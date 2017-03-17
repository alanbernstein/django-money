import re
import os
from collections import Counter, defaultdict
import datetime
from itertools import groupby
from django.core.management.base import BaseCommand
from django.db.models import Sum
from django.db.models import Q
from taggit.models import Tag
from accounts.models import Transaction, Merchant
from accounts.base import get_account
from accounts.search import print_search_results as search

from panda.debug import pp, debug, pm


class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument('--account', '-a', default='', help='specify account to use')
        parser.add_argument('--clean-descriptions', action='store_true', default=False, help='attempt to canonicalize descriptions')
        parser.add_argument('--assign-interactive', action='store_true', default=False, help='')
        parser.add_argument('--auto-add-merchants', action='store_true', default=False, help='')

    def handle(self, *args, **options):

        account = get_account(options['account'])

        if options['clean_descriptions']:
            normalize_descriptions(account)
        if options['assign_interactive']:
            assign_interactive(account)
        if options['auto_add_merchants']:
            assign_merchants_auto(account)


# pm manage_transactions -a alan-chase-credit --assign-interactive
def help():
    print('--\nusage')
    print('  help()')
    print('  add_merchant(name, pattern, tags)')
    print('  add_merchant_pattern(merchant_id, pattern)')
    print('  add_merchant_tags(merchant_id, tags, notes)')
    print('  add_tx_tags(transaction_id, tags, notes)')
    print('  get_tx(ids_or_strings)')
    print('  get_tx_context(id)')
    print('  search(string[, tags=False, merchants=False, transactions=False])')
    print("  list_tx(account, 'recent')")
    print("  list_tx(account, 'recent-amount')")
    print("  list_tx(account, 'amount')")
    print("  list_tx(account, 'group-count')")
    print("  list_tx(account, 'group-total')")
    print("  assign_merchants_auto(account)")
    print("  list_tags()")


def assign_interactive(account):
    act = account
    list_transactions(account)
    help()
    debug()


def add_merchant(name, pattern, tags):
    if not type(tags) == list:
        tags = [tags]

    mm = Merchant.objects.create(name=name,
                                 pattern=pattern)
    mm.tags.add(*tags)
    mm.save()
    print(mm)


def add_merchant_pattern(merchant_id, pattern):
    merchant = Merchant.objects.get(id=merchant_id)
    old_pattern = merchant.pattern.pattern
    new_pattern = '|'.join([old_pattern, pattern])
    merchant.pattern = new_pattern
    merchant.save()
    print('old pattern      - %s' % old_pattern)
    print('combined pattern - %s' % new_pattern)


def add_transaction_tags(transaction_ids, tags=None, notes=None):
    if tags and not type(tags) == list:
        tags = [tags]

    if not type(transaction_ids) == list:
        transaction_ids = [transaction_ids]

    for tid in transaction_ids:
        tt = Transaction.objects.get(id=tid)
        if tags:
            tt.tags.add(*tags)
        if notes:
            if tt.notes == '' or tt.notes is None:
                tt.notes = notes
            else:
                print('%d already has a `notes`: %s' % (tid, tt.notes))
        tt.save()


add_tx_tags = add_transaction_tags


def add_merchant_tags(merchant_ids, tags=None, notes=None):
    if tags and not type(tags) == list:
        tags = [tags]

    if not type(merchant_ids) == list:
        merchant_ids = [merchant_ids]

    for mid in merchant_ids:
        mm = Merchant.objects.get(id=mid)
        if tags:
            mm.tags.add(*tags)
        if notes:
            if mm.notes == '' or mm.notes is None:
                mm.notes = notes
            else:
                print('%d already has a `notes`: %s' % (mid, mm.notes))
        mm.save()


def get_tx_context(tid, context=5):
    tt = Transaction.objects.filter(id__in=range(tid-context, tid+context))
    for t in tt:
        print('%6d %s' % (t.id, t))


def get_tx(qlist):
    if type(qlist) != list:
        qlist = [qlist]

    tx = []
    for query in qlist:
        if type(query) == str:
            pass
        if type(query) == int:
            tx.append(Transaction.objects.get(id=query))

    if len(tx) == 1:
        tx = tx[0]
    return tx


export_fname = os.getenv('HOME') + '/untagged-transactions.org'


def export_untagged_to_org(account):
    tx0 = Transaction.objects.filter(account_id=account.id, merchant=None, tags=None)

    with open(export_fname, 'w') as f:
        f.write('| id | description | amount | date | tags | notes |\n')
        f.write('|-+-+-+-+-+-|\n')
        for t in tx0:
            f.write('| %d | %s | %s | %s | | |\n' % (t.id, t.description_raw, t.debit_amount, t.transaction_date))

    print('wrote %d transactions to %s' % (tx0.count(), export_fname))


def import_tags_from_org(account, fname=None, tags=None):
    fname = fname or export_fname
    with open(fname, 'r') as f:
        lines = f.read().splitlines()

    lines = lines[2:]
    print('read %d transactions' % len(lines))
    added_tags = 0
    added_notes = 0

    if tags is None:
        # import free-form text
        for line in lines:
            trash, id, desc, amount, date, tagstr, notes, trash = [x.strip() for x in line.split('|')]

            debug()
            t = Transaction.objects.get(id=int(id))
            if tagstr:
                tags = [x.strip() for x in tagstr.split(',')]
                t.tags.add(*tags)
                added_tags += 1

            if notes:
                t.notes = notes
                added_notes += 1

            if tagstr or notes:
                print(t, t.tags.all())
            t.save()
    else:
        # add tags from input list to all lines in the file
        for line in lines:
            id, desc, amount, date, tagstr, notes = [x.strip() for x in line.split('|')]
            t = Transaction.objects.get(id=int(id))
            t.tags.add(*tags)
            added_tags += 1
            print(t)
            t.save()

    print('added tags to %d transactions' % added_tags)
    if added_notes:
        print('added notes to %d transactions' % added_notes)


def list_tags(account, mode='count', N=50):
    # TODO: use raw sql to improve this
    # content types:
    # 12: merchants
    # 14: transactions
    tags = Tag.objects.all()

    tag_tx_counts = {}
    tag_tx_sums = {}
    for tag in tags:
        # t_count = Transaction.objects.filter(tags__name__in=[tag.name]).count(),
        # mt_count = Transaction.objects.filter(merchant_id__in=merchant_ids)

        # TODO consolidate this with views.get_transactions_by_tag
        merchant_ids = [m.id for m in Merchant.objects.filter(tags__name__in=[tag.name])]
        txs = Transaction.objects.filter(Q(tags__name__in=[tag.name]) | Q(merchant_id__in=merchant_ids))

        tag_tx_counts[tag.name] = (txs.count())
        tag_tx_sums[tag.name] = float(sum([t.debit_amount for t in txs]))

    if mode == 'count':
        name_count = [(v, k) for k, v in tag_tx_counts.items()]
        name_count.sort(key=lambda x: -x[0])
        for nc in name_count[:N]:
            print('%5d  %s' % nc)

    elif mode == 'amount':
        name_amount = [(v, k) for k, v in tag_tx_sums.items()]
        name_amount.sort(key=lambda x: -x[0])
        for na in name_amount[:N]:
            print('$%9.2f  %s' % na)

    elif mode == 'count-exclusive':
        pass

    elif mode == 'amount-exclusive':
        pass


def list_transactions(account, mode='recent', N=20):
    # find a good set of transactions to focus on...
    # recent_days = 3 * 30
    #
    # this can be a little confusing, e.g., the clipper grouping weirdness
    # this is because i'm filtering out anything with a merchant or any tags
    # might want to allow other modes that filter the transactions differently or not at all
    tx0 = Transaction.objects.filter(account_id=account.id, merchant=None, tags=None)
    # total = tx0.aggregate(Sum('debit_amount')).values()[0]  # breaks in python3
    total = float(sum([t.debit_amount for t in tx0]))
    num_tx = len(tx0)

    # sort by amount
    by_amount = tx0.order_by('-debit_amount')

    # sort by recent/amount
    # min_date = datetime.datetime.today() - datetime.timedelta(days=recent_days)
    # recent = tx0.filter(transaction_date__gte=min_date)
    N = min(N, num_tx)
    recent = tx0[num_tx-N-1:num_tx-1]
    # recent_by_amount = recent.order_by('-debit_amount')

    # group by description
    tx = tx0.order_by('description')
    group_dict = {}
    group_list = []
    for k, v in groupby(tx, lambda x: x.description):
        amount_list = [float(x.debit_amount) for x in v]
        group_dict[k] = amount_list
        group_list.append((k, amount_list))

    # sort by count/total
    grouped_by_count = sorted(group_list, key=lambda x: len(x[1]), reverse=True)
    grouped_by_total = sorted(group_list, key=lambda x: abs(sum([y for y in x[1]])), reverse=True)

    # show results
    print('%d transactions without merchants or tags ($%8.2f)' % (tx0.count(), total))

    if mode == 'amount':
        print('--\ntop %d transactions by amount:' % N)
        for t in by_amount[0:N]:
            print('%6d %s' % (t.id, t))

    # if mode == 'recent-amount':
    #    print('--\ntop %d recent transactions by amount:' % N)
    #    for t in recent_by_amount[0:N]:
    #        print('%6d %s' % (t.id, t))

    if mode == 'recent':
        print('--\n%d recent transactions' % N)
        for t in recent:
            print('%6d %s' % (t.id, t))

    if mode == 'group-count':
        print('--\ntop %d description-groups by count' % N)
        for entry in grouped_by_count[0:N]:
            print('%40s (%d, $%6.2f)' % (entry[0], len(entry[1]), abs(sum([y for y in entry[1]]))))

    if mode in ['group-total', 'group-amount']:
        print('--\ntop %d description-groups by absolute total' % N)
        for entry in grouped_by_total[0:N]:
            print('%40s (%d, $%6.2f)' % (entry[0], len(entry[1]), abs(sum([y for y in entry[1]]))))

    # TODO: return the above thing as a list


list_tx = list_transactions


def assign_merchants_auto(account, only_non_linked=True, test=False):
    # for each transaction in account without a merchant, check all merchant patterns for match

    if only_non_linked:
        tx = Transaction.objects.filter(account_id=account.id, merchant=None)
    else:
        tx = Transaction.objects.filter(account_id=account.id)

    merchants = Merchant.objects.all()
    num_assigned = 0
    if test:
        print('TEST RUN')
    for m in merchants:
        pattern = re.compile(m.pattern)
        #print('%s - %s' % (m.name, m.pattern))
        for t in tx:
            if pattern.search(t.description_raw):
                #print('  %s' % t.description)
                if t.merchant and t.merchant != m:
                    print('multiple match:', t.merchant, m)
                    continue
                t.merchant = m
                print(m, t)
                num_assigned += 1
                if not test:
                    t.save()
    print('total transactions checked: %d' % len(tx))
    print('assigned: %d' % num_assigned)
    print('with merchants: %d' % Transaction.objects.filter(merchant__isnull=False).count())
    print('without merchants: %d' % Transaction.objects.filter(merchant=None).count())
    debug()


def get_tx_groups_by_frequency(tx, field=None, sortby=None):

    field = field or 'description'

    # create dict of lists of transactions with same description
    tx_groups_dict = {}
    for t in tx:
        if t[field] in tx_groups_dict:
            tx_groups_dict[t[field]].append(t)
        else:
            tx_groups_dict[t[field]] = [t]

    # create list of lists of transactions, sorted by length or total
    tx_groups_list = [v for k, v in tx_groups_dict.items()]
    if sortby is None or sortby == 'length':
        tx_groups_list.sort(key=lambda x: -len(x))
    elif sortby == 'absolute_total':
        tx_groups_list.sort(key=lambda x: -abs(sum([y['cents'] for y in x])))
    elif sortby == 'total':
        tx_groups_list.sort(key=lambda x: -sum([y['cents'] for y in x]))

    return tx_groups_list


LOCATION_STRINGS = ['AUSTIN TX',
                    'DALLAS TX',
                    'CHICAGO IL',
                    'OAK PARK IL',
                    'SAN FRANCISCO CA',
                    'PALO ALTO CA']


def get_common_suffixes(account):
    tx = Transaction.objects.all()
    suffix_ngrams1 = [t.description_raw.lower().split()[-1] for t in tx]
    suffix_ngrams2 = [' '.join(t.description_raw.lower().split()[-2:]) for t in tx]
    ngram1_groups = Counter(suffix_ngrams1)
    ngram2_groups = Counter(suffix_ngrams2)
    for t in ngram2_groups.most_common()[0:10]:
        print(t)
    


def normalize_descriptions(account=None):
    # TODO: break this up by account?
    # tx = Transaction.objects.filter(account_id=account.id)
    if account:
        unnormalized = Transaction.objects.filter(account_id=account.id, description=None)
    else:
        unnormalized = Transaction.objects.filter(description=None)

    for t in unnormalized:
        desc_short = t.description_raw
        desc_short = re.sub('[0-9]{23}', ' ', desc_short)                    # chase credit, transaction ID numbers
        desc_short = re.sub('[^a-zA-Z][0-9]{5,}[^a-zA-Z]', ' ', desc_short)  # other extraneous long ID numbers
        desc_short = re.sub('#[0-9]{3,}', ' ', desc_short)                   # other id numbers starting with '#'
        desc_short = re.sub('[0-9][0-9]/[0-9][0-9]', '', desc_short)         # mm/yy
        desc_short = re.sub('^SQ *', '', desc_short)                         # square prefix
        # TODO: save location string, use to suggest 'travel'
        # TODO: detect common suffixes as location strings
        for s in LOCATION_STRINGS:
            desc_short = re.sub(' %s$' % s, '', desc_short, re.IGNORECASE)   # location strings
        desc_short = re.sub('[0-9]{3}-[0-9]{3}-[0-9]{4}', '', desc_short)    # phone numbers
        desc_short = re.sub(' +', ' ', desc_short)                           # collapse spaces
        t.description = desc_short.strip()
        print(t.description_raw)
        print(' -> %s' % t.description)
        t.save()

    print('done normalizing descriptions (checked %d transactions)' % unnormalized.count())
