import os
import re


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
