import re
import datetime
from itertools import groupby
from django.core.management.base import BaseCommand
from django.db.models import Sum
from accounts.models import Transaction, Merchant
from accounts.base import get_account

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


def help():
    print('--\nusage')
    print('  help()')
    print('  add_merchant(name, pattern, tags)')
    print('  add_merchant_pattern(merchant_id, pattern)')
    print('  add_tx_tags(transaction_id, tags)')
    print('  search(string)')
    print("  list_tx(account, 'recent')")
    print("  list_tx(account, 'recent-amount')")
    print("  list_tx(account, 'amount')")
    print("  list_tx(account, 'group-count')")
    print("  list_tx(account, 'group-total')")
    print("  assign_merchants_auto(account)")


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


def add_merchant_pattern(merchant_id, pattern):
    merchant = Merchant.objects.get(id=merchant_id)
    old_pattern = merchant.pattern.pattern
    new_pattern = '|'.join([old_pattern, pattern])
    merchant.pattern = new_pattern
    merchant.save()
    print('old pattern      - %s' % old_pattern)
    print('combined pattern - %s' % new_pattern)


def add_transaction_tags(transaction_ids, tags, notes=None):
    if not type(tags) == list:
        tags = [tags]

    if not type(transaction_ids) == list:
        transaction_ids = [transaction_ids]

    for tid in transaction_ids:
        tt = Transaction.objects.get(id=tid)
        tt.tags.add(*tags)
        if notes:
            tt.notes = notes
        tt.save()


add_tx_tags = add_transaction_tags


def search_merchants(s):
    res = Merchant.objects.filter(name__icontains=s)
    for m in res:
        print('%d. %s - %s' % (m.id, m.name, m.pattern.pattern))


def search_transactions(s):
    res = Transaction.objects.filter(description__icontains=s)
    for t in res:
        mid = ''
        if t.merchant:
            mid = t.merchant.id
        print('%d. %s (%s %s) - %s' % (t.id, t.description, t.transaction_date, t.debit_amount, mid))


def search(s):
    print('merchants:')
    search_merchants(s)
    print('transactions')
    search_transactions(s)


def list_transactions(account, mode='recent'):
    # find a good set of transactions to focus on...
    # recent_days = 3 * 30
    N = 20
    tx0 = Transaction.objects.filter(account_id=account.id, merchant=None, tags=None)
    total = tx0.aggregate(Sum('debit_amount')).values()[0]
    num_tx = len(tx0)

    # sort by amount
    by_amount = tx0.order_by('-debit_amount')

    # sort by recent/amount
    # min_date = datetime.datetime.today() - datetime.timedelta(days=recent_days)
    # recent = tx0.filter(transaction_date__gte=min_date)
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

    #if mode == 'recent-amount':
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

    if mode == 'group-total':
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


def normalize_descriptions(account):
    # TODO: break this up by account?
    # tx = Transaction.objects.filter(account_id=account.id)
    unnormalized = Transaction.objects.filter(account_id=account.id, description=None)

    for t in unnormalized:
        desc_short = t.description_raw
        desc_short = re.sub('[0-9]{23}', ' ', desc_short)                    # chase credit, transaction ID numbers
        desc_short = re.sub('[^a-zA-Z][0-9]{5,}[^a-zA-Z]', ' ', desc_short)  # other extraneous long ID numbers
        desc_short = re.sub('#[0-9]{3,}', ' ', desc_short)                   # other id numbers starting with '#'
        desc_short = re.sub('[0-9][0-9]/[0-9][0-9]', '', desc_short)         # mm/yy
        desc_short = re.sub('^SQ *', '', desc_short)                         # square prefix
        for s in LOCATION_STRINGS:
            desc_short = re.sub(' %s$' % s, '', desc_short, re.IGNORECASE)   # location strings
        desc_short = re.sub('[0-9]{3}-[0-9]{3}-[0-9]{4}', '', desc_short)    # phone numbers
        desc_short = re.sub(' +', ' ', desc_short)                           # collapse spaces
        t.description = desc_short.strip()
        print(t.description_raw)
        print(' -> %s' % t.description)
        t.save()

    print('done normalizing descriptions (checked %d transactions)' % unnormalized.count())
