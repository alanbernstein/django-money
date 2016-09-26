import datetime
from datetime import datetime as dt
from dateutil.relativedelta import relativedelta
from itertools import groupby
from collections import defaultdict
import logging

from django.shortcuts import render, render_to_response
from django.http import HttpResponse
from django.core.urlresolvers import resolve
from django.shortcuts import render
from django.utils.html import format_html
from django.db.models import Sum, Count, Q
from taggit.models import Tag

from accounts.models import (Account,
                             Statement,
                             Transaction,
                             Merchant,
                             User,
                             TagTable,
                             MerchantTable,
                             TransactionTable
                             )

from panda.debug import debug

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

logger = logging.getLogger(__name__)


def index(request):
    return render_to_response('index.html')


def transaction_list_table(request):
    all_tx = Transaction.objects.all()
    Nt = len(all_tx)
    tx = all_tx[Nt - 30:Nt - 1]

    rows = get_transaction_info(tx)
    print(rows[0])
    table = TransactionTable(rows)
    # return render(request, 'datatable-basic.html', {'table': table})
    return render(request, 'datatable.html',
                  {'table': table, 'resource': 'transaction'})


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
        total = m_tx.aggregate(Sum(key))[key + '__sum']
        total = total or 0
        row['total_amount'] = float(total)
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
    return render(request, 'datatable.html',
                  {'table': table, 'resource': 'merchant'})



def transactions_untagged(request, sort=False):
    # TODO: sort by frequency
    # sorted_items = profile.ItemList.annotate(itemcount=Count('name'))
    # sorted_items = sorted_items.order_by('-itemcount')

    tx = Transaction.objects.filter(tags__isnull=True, merchant__tags__isnull=True)
    rows = get_transaction_info(tx)
    rows2 = [row for row in rows if not row['tags']]  # TODO: why is this necessary
    table = TransactionTable(rows2)
    #return render(request, 'datatable-basic.html', {'table': table})
    return render(request, 'datatable.html',
                  {'table': table, 'resource': 'transaction'})



def merchants_unnamed(request, sort=True):
    # TODO: try to use this to fix the header images
    # http://django-datatable-view.appspot.com/specific-columns/
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
    return render(request, 'datatable.html',
                  {'table': table, 'resource': 'merchant'})


def merchant_list_table(request):
    # total tran
    merchants = Merchant.objects.all()
    rows = get_merchant_info(merchants)
    table = MerchantTable(rows)
    print(rows[0])
    return render(request, 'datatable.html',
                  {'table': table, 'resource': 'merchant'})


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
    return render(request, 'datatable.html',
                  {'table': table, 'resource': 'tag'})


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


def get_compare_data(merchants=None, tags=None, start=None, end=None):
    """inputs:
    merchants = [merchant_name1, ...]
      OR 
    tags = [tag_name1, ...]

    start = 'YYYY-MM-DD'
    end = 'YYYY-MM-DD'

    """
    # TODO: there might be a way to simplify the second half of this function
    # to a single django query.
    # it appears to be cleaner in 1.10: http://stackoverflow.com/questions/8746014/django-group-by-date-day-month-year
    # but for now this is stuck in 1.8 because of regex_field.
    # might need to munge the data anyway to get the months with 0 transactions
    #
    # TODO: support different time bins? could generalize this approach with something like
    #       <year>/<month mod 3> for quarters
    #       <year>/<julian day mod 7> for weeks
    #       also don't see myself being interested in anything except maybe years

    if tags and merchants:
        # not sure if there is any way to do this
        logger.error('get_compare_data: both merchants and tags')
        return {}

    if not tags and not merchants:
        # no query requested
        logger.error('get_compare_data: no merchants or tags')
        return {}

    # generate appropriate query
    qs = {}
    if tags:
        for tag in tags:
            # TODO: not sure if this query works properly
            qs[tag] = Transaction.objects.filter(Q(tag__name=tag) | Q(merchant__tag__name=tag))

    if merchants:
        for merchant in merchants:
            qs[merchant] = Transaction.objects.filter(merchant__name=merchant)

    if start:
        if len(start) == 7:
            start += '-01'  # day required
        for k in qs:
            qs[k] = qs[k].filter(transaction_date__gte=start)

    if end:
        if len(end) == 7:
            end += '-01'  # day required
        for k in qs:
            qs[k] = qs[k].filter(transaction_date__lte=end)

    # execute query, collate data into simple format, track max and min dates
    # month_totals[key][month] = total
    # key could be merchant, tag, ...
    month_totals = {}
    start_date = dt.today().date()
    end_date = datetime.date(1970, 1, 1)
    for key, txs in qs.items():
        groups = defaultdict(float)
        for tx in txs:
            start_date = min(start_date, tx.transaction_date)
            end_date = max(end_date, tx.transaction_date)
            month = dt.strftime(tx.transaction_date, '%Y/%m')
            groups[month] += float(tx.debit_amount)
        month_totals[key] = groups

    # collate into graphable data
    # {'x': [datetime, ...],  # len = N
    #  'key1': [float, ...],  # len = N
    #  'key2': [float, ...]}  # len = N
    x = month_range(start_date, end_date)
    chartdata = {'x': [dt.strftime(date, '%Y/%m') for date in x]}
    for key, totals in month_totals.items():
        chartdata[key] = [totals[month] for month in chartdata['x']]

    """
    django-nvd3 wants something like this:
    chartdata = {'x': xdata,
                 'name1': 'series 1', 'y1': ydata, 'extra1': extra_serie,
                 'name2': 'series 2', 'y2': ydata2, 'extra2': extra_serie}
    """
    return chartdata


def month_range(start, end):
    """get a list of datetimes incremented by exactly one month"""
    # print [min_date + relativedelta(months=i) for i in range(48)]
    date_vec = [start]
    while date_vec[-1] < end:
        date_vec.append(date_vec[-1] + relativedelta(months=1))
    return date_vec


def get_subdivide_data(tags):
    return []
    

def transactions_compare(request, tags):
    # TODO: this should render a template which hits an api for data
    taglist = tags.split('+')
    data = ''
    data += 'tags: %s' % ', '.join(taglist)
    chart_data = get_compare_data(taglist)
    return HttpResponse(data)


def transactions_subdivide(request, tags):
    # TODO: this should render a template which hits an api for data
    taglist = tags.split('+')
    data = ''
    data += 'tags: %s' % ', '.join(taglist)
    chart_data = get_subdivide_data(taglist)
    return HttpResponse(data)


def timeseries(request):
    resp = ''

    return HttpResponse(resp)
