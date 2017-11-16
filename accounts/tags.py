import os
import re
from django.db.models import Q


# TODO redo this logic inside python if it's too slow
"""
given a list of transaction objects like this:
[([tag1, tag2, ...], amount), ...]
do the same work that's done in get_tag_totals, etc, but without doing any additional SQL queries
"""


def get_tag_totals(tx):
    """
    given a queryset of transactions, create a list of tuples like:
    [(tag, count, debit_total), ...]
    sorted in decreasing order of debit_total.
    transactions are counted in each of the tags in which they appear
    """
    tagsets = [t.get_tags() for t in tx]
    tags = list(set.union(*tagsets))
    tag_stuff = []
    for tag in tags:
        tagtx = tx.filter(Q(tags__name__in=[tag]) | Q(merchant__tags__name__in=[tag])).distinct()
        count = len(tagtx)
        total_debit = sum([t.debit_amount for t in tagtx])
        tag_stuff.append((tag, count, total_debit))
    tag_stuff.sort(key=lambda x: -x[2])
    return tag_stuff


def get_tag_exclusive_totals_by_size(tx):
    """
    given a queryset of transactions, create a list of tuples like:
    [(tag, count, debit_total), ...]
    sorted in decreasing order of debit_total.
    each transaction is counted only once.
    tags are sorted by debit_total, and all transactions in the highest-total tag
    are counted in that tag.
    this is "debit_total priority order"
    """
    tag_exclusive = []
    while True:
        tag_stuff = get_tag_totals(tx)
        if not tag_stuff:
            break
        tag = tag_stuff[0][0]
        tagtx = tx.filter(Q(tags__name__in=[tag]) | Q(merchant__tags__name__in=[tag])).distinct()
        count = len(tagtx)
        total_debit = sum([t.debit_amount for t in tagtx])
        tag_exclusive.append((tag.name, count, total_debit))

        tx = tx.exclude(Q(tags__name__in=[tag]) | Q(merchant__tags__name__in=[tag])).distinct()

        # TODO: better break condition
        if len(tx) < 5:
            break
    tag_exclusive.append(('(other)', len(tx), sum([t.debit_amount for t in tx])))

    return tag_exclusive


def get_tag_exclusive_by_priority(tx):
    """
    given a queryset of transactions, create a list of tuples like:
    [(tag, count, debit_total), ...]
    sorted in decreasing order of debit_total.
    each transaction is counted only once.
    tags are sorted by manually-defined priority, and all transactions in the highest-priority tag
    are counted in that tag.
    this is "manual priority order"
    """
    tag_exclusive = []

    return tag_exclusive



# length of first captured group determines depth
# second captured group is the relevant text
ORG_HEADER_PREFIX = '^(\**) (.*)'  # depth 1: '* xxx', depth 2: '** xxx', depth 3: '*** xxx'
ORG_LIST_PREFIX = '^(  )*- (.*)'   # depth 1: '- xxx', depth 2: '  - xxx', depth 3: '    - xxx'


def get_tag_hierarchy():
    fname = os.getenv('PY') + '/django/money/tag-structure.txt'
    return parse_tag_tree(fname, ORG_HEADER_PREFIX)


def parse_tag_tree(fname, prefix_re):
    """
    reads a text file containing a tag hierarchy
    returns a flat list of hierarchical tags. each element resembles, for example:
    ['root', 'grandparent', 'parent', 'child']
    """
    with open(fname, 'r') as f:
        lines = f.read().strip().split('\n')

    tagstack = []
    tagsets = []

    for line in lines:
        # capture groups
        match = re.match(prefix_re, line)
        if not match:
            continue
        depth = len(match.groups()[0])  # TODO need to divide here, for other prefix_re values
        text = match.groups()[1]

        if depth <= len(tagstack):
            # depth decreased, go back up the tree
            tagstack = tagstack[0:depth-1]  # pop len(tagstack)-depth

        tagstack.append(text)
        tagsets.append(list(tagstack))

    return tagsets


def match_tag_prefix(tagsets, prefix, maxdepth=1000):
    # prefix is a list, like ['root', 'grandparent']
    # optional depth limits max depth (to retrieve all L2 tags, for example)
    return [ts for ts in tagsets if ts[:len(prefix)] == prefix and len(ts) <= maxdepth]
