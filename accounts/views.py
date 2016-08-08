from datetime import datetime

from django.shortcuts import render
from django.http import HttpResponse
from django.core.urlresolvers import resolve
from django.shortcuts import render
from django.utils.html import format_html
from django.db.models import Sum, Count

from accounts.models import Account, Statement, Transaction, Merchant, User, TagTable, MerchantTable, TransactionTable
from taggit.models import Tag



"""
TODO: view tag breakdown, but also view subtag breakdown
- that is, i should be able to view something like a chart of rent/bills/food/entertainment/...
- but also, a chart of all transactions matching a single tag, split up by other tags they also have. eg:
  - food: groceries/meal/date
  - travel: airfare/lodging/food
  - etc

options for decent charts:
https://www.djangopackages.com/grids/g/charts/

- django-nvd3
  - depends on python-nvd3, nvd3, bower - might be the best looking/most mature (https://pypi.python.org/pypi/django-nvd3)



options for tag inputs:
https://github.com/ludwiktrammer/django-tagging-autocomplete

https://github.com/Jaza/django-taggit-autocomplete - works with taggit - no longer maintained

other similar
https://github.com/nemesisdesign/django-tagging-autocomplete-tag-it
https://github.com/rasca/django-taggit-jquery-tag-it

https://django-bootstrap-ui.readthedocs.io/en/stable/

https://pypi.python.org/pypi/django-tags-input


"""


def index(request):
    resp = ''
    resp += '<a href="tags">tags</a><br>\n'
    resp += '<a href="accounts">accounts</a><br>\n'
    resp += '<a href="statements">statements</a><br>\n'
    resp += '<a href="merchants">merchants</a> - <a href="merchants/untagged">untagged</a> - <a href="merchants/unnamed">unnamed</a><br>\n'
    resp += '<a href="transactions">transactions</a> - <a href="transactions/untagged">untagged</a> - <a href="transactions/unnamed">unnamed</a><br>\n'
    return HttpResponse(resp)


def transaction_list_table(request):
    all_tx = Transaction.objects.all()
    Nt = len(all_tx)
    tx = all_tx[Nt - 30:Nt - 1]

    rows = get_transaction_info(tx)
    table = TransactionTable(rows)
    return render(request, 'datatable-basic.html', {'table': table})


def get_merchant_info(merchants=None):
    """
    input merchants should be a list of merchants or merchant ids
    """

    if not hasattr(merchants, '__iter__'):
        # convert single instance to list
        merchants = [merchants]

    if isinstance(merchants[0], int):
        # get transactions from ids
        ids = merchants
        merchants = Merchant.objects.filter(id__in=ids)

    rows = []
    for m in merchants:
        m_tx = Transaction.objects.filter(merchant_id=m.id)
        row = {}
        row['name'] = m.as_link()
        row['pattern'] = m.pattern.pattern
        row['tags'] = m.get_tags_as_links()
        row['total_transactions'] = m_tx.count()
        key = 'debit_amount'
        row['total_amount'] = m_tx.aggregate(Sum(key))[key + '__sum']
        rows.append(row)

    return rows


def get_transaction_info(tx=None):
    """
    input tx should be a list of transactions or transaction ids
    """

    if not hasattr(tx, '__iter__'):
        # convert single instance to list
        tx = [tx]

    if isinstance(tx[0], int):
        # get transactions from ids
        ids = tx
        tx = Transaction.objects.filter(id__in=ids)

    rows = []
    for t in tx:
        row = {}
        row['id'] = t.as_link(self_link=True)
        if t.merchant:
            row['merchant'] = t.merchant.as_link()
        row['transaction_date'] = t.transaction_date
        row['amount'] = t.debit_amount
        row['description'] = t.description
        row['account'] = t.account.as_link()
        row['statement'] = t.statement.as_link()
        row['tags'] = t.get_tags_as_links()

        rows.append(row)

    return rows


def transaction_list_simple(request):
    resp = ''

    resp += '<h2>all transactions</h2>'
    for t in Transaction.objects.all():
        resp += t.as_link()

    return HttpResponse(resp)


transaction_list = transaction_list_table


def transaction_detail(request, *args, **kwargs):
    tid = kwargs['transaction_id']
    # t = Transaction.objects.get(id=tid)

    resp = ''
    resp += '<h2>transaction detail</h2>'
    for k, v in get_transaction_info([int(tid)])[0].items():
        resp += '%s: %s<br>' % (k, v)

    resp += '<h3>same merchant</h3>'
    resp += '<h3>same tags</h3>'
    return HttpResponse(resp)


def merchants_untagged(request, sort=False):
    # TODO: sort by frequency
    merchants = Merchant.objects.filter(tags__isnull=True)
    rows = get_merchant_info(merchants)
    table = MerchantTable(rows)
    return render(request, 'datatable-basic.html', {'table': table})


def transactions_untagged(request, sort=False):
    # TODO: sort by frequency
    # sorted_items = profile.ItemList.annotate(itemcount=Count('name'))
    # sorted_items = sorted_items.order_by('-itemcount')

    tx = Transaction.objects.filter(tags__isnull=True)
    rows = get_transaction_info(tx)
    rows2 = [row for row in rows if not row['tags']]  # TODO: why is this necessary
    table = TransactionTable(rows2)
    return render(request, 'datatable-basic.html', {'table': table})


def merchants_unnamed(request, sort=True):
    tx = Transaction.objects.filter(merchant__isnull=True)
    key = 'description'
    if sort:
        tx_counts_sums = tx.values(key).annotate(count=Count(key)).annotate(sum=Sum('debit_amount')).order_by('-count')
        rows = []
        for t in tx_counts_sums:
            row = {}
            row['name'] = t['description']
            row['pattern'] = '?'
            row['total_transactions'] = t['count']
            row['total_amount'] = t['sum']
            rows.append(row)
    else:
        rows = get_transaction_info(tx)

    table = MerchantTable(rows)
    return render(request, 'datatable-basic.html', {'table': table})


def merchant_list_table(request):
    # total tran
    merchants = Merchant.objects.all()
    rows = get_merchant_info(merchants)
    table = MerchantTable(rows)
    return render(request, 'datatable-basic.html', {'table': table})


def merchant_list_simple(request):
    resp = ''

    resp += '<h2>all merchants</h2>'
    for merchant in Merchant.objects.all():
        resp += merchant.as_link()

    return HttpResponse(resp)


merchant_list = merchant_list_table


def account_detail(request, *args, **kwargs):
    resp = ''
    resp += '<h2>account detail</h2>'

    return HttpResponse(resp)


def statement_detail(request, *args, **kwargs):
    resp = ''
    resp += '<h2>statement detail</h2>'

    return HttpResponse(resp)


def merchant_detail(request, *args, **kwargs):
    # TODO: unique matches
    mid = kwargs['merchant_id']
    merchant = Merchant.objects.get(id=mid)
    tx = Transaction.objects.filter(merchant_id=mid)
    count = tx.count()
    key = 'debit_amount'
    amount = tx.aggregate(Sum(key))[key + '__sum']

    merchant_summary = format_html('$%.2f, %d transactions<br>%s' % (amount, count, merchant.pattern.pattern))

    rows = get_transaction_info(tx)
    table = TransactionTable(rows)
    return render(request, 'merchant-detail.html', {'table': table,
                                                    'merchant_name': merchant.name,
                                                    'merchant_summary': merchant_summary})


def account_list(request, *args, **kwargs):
    resp = ''
    resp += '<h2>account list</h2>'

    return HttpResponse(resp)


def statement_list(request, *args, **kwargs):
    resp = ''
    resp += '<h2>statement list</h2>'

    return HttpResponse(resp)


def tag_detail(request, *args, **kwargs):
    tag_id = kwargs['tag_id']
    tag = Tag.objects.get(id=tag_id)

    resp = ''
    resp += '<h2>%s</h2>' % tag.name

    resp += '<h3>merchants</h3>'
    for merchant in Merchant.objects.filter(tags__id__in=[tag_id]):
        resp += merchant.as_link() + '<br>'

    resp += '<h3>transactions</h3>'
    for t in Transaction.objects.filter(tags__id__in=[tag_id]):
        resp += t.as_link() + '<br>'

    return HttpResponse(resp)


tag_priority = ['bills', 'grocery', 'meal', 'car', 'bike']
def tag_list_table(request):
    # table columns:
    # - total transactions
    # - total amount
    # - exclusive transactions
    # - exclusive amount

    # 'exclusive' = generating mutually-exclusive categories from unconstrained tags, by using a priority list

    rows = get_tag_info()
    table = TagTable(rows)
    return render(request, 'datatable-basic.html', {'table': table})


def get_tag_info():
    # return Tag.objects.all()

    rows = []
    tags = Tag.objects.all()

    for tag in tags:
        row = {}
        row['name'] = format_html('<a href="tags/%s">%s</a>' % (tag.id, tag.name))
        tag_tx = Transaction.objects.filter(tags__name__in=[tag.name])
        row['total_transactions'] = len(tag_tx)
        row['total_amount'] = sum([t.debit_amount for t in tag_tx])
        rows.append(row)

    return rows


def tag_list_simple(request):
    resp = ''

    resp += '<h2>all tags</h2>'
    for tag in Tag.objects.all():
        resp += '<a href="tags/%s">%s</a>\n' % (tag.id, tag.name)

    return HttpResponse(resp)


tag_list = tag_list_table


def timeseries(request):
    resp = ''

    return HttpResponse(resp)
