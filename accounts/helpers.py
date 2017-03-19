import datetime
from datetime import datetime as dt
from dateutil.relativedelta import relativedelta
from collections import defaultdict
import logging

from django.utils.html import format_html
from django.db.models import Sum, Q
from taggit.models import Tag

from accounts.models import (Account,
                             Statement,
                             Transaction,
                             Merchant,
                             )


logger = logging.getLogger(__name__)


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
        row['id'] = m.id
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


def get_account_info(accounts=None):
    if not hasattr(accounts, '__iter__'):
        # convert single instance to list
        accounts = [accounts]

    if isinstance(accounts[0], int):
        # get transactions from ids
        ids = accounts
        accounts = Account.objects.filter(id__in=ids)

    rows = []
    for a in accounts:
        row = {}
        row['id'] = a.as_link(self_link=True)


def get_statement_info(statements=None):
    if not hasattr(statements, '__iter__'):
        # convert single instance to list
        statements = [statements]

    if isinstance(statements[0], int):
        # get transactions from ids
        ids = statements
        statements = Statement.objects.filter(id__in=ids)

    rows = []
    for s in statements:
        row = {}
        row['id'] = s.as_link(self_link=True)
        row['account'] = s.account
        row['end_date'] = s.end_date
        row['count'] = s.get_count()
        row['total'] = s.get_total()
        rows.append(row)

    return rows


def get_transactions_by_tag(tag, merchants=True):
    tag_merchants = Merchant.objects.filter(tags__name__in=[tag.name])
    merchant_ids = [m.id for m in tag_merchants]

    tag_tx = Transaction.objects.filter(Q(tags__name__in=[tag.name]) | Q(merchant_id__in=merchant_ids))

    return tag_tx


def get_tag_info():
    # return Tag.objects.all()

    rows = []
    tags = Tag.objects.all()

    for tag in tags:
        row = {}
        row['id'] = tag.id
        row['name'] = format_html('<a href="tags/%s">%s</a>' % (tag.id, tag.name))
        tag_tx = get_transactions_by_tag(tag)
        row['total_transactions'] = len(tag_tx)
        row['total_amount'] = sum([t.debit_amount for t in tag_tx])
        rows.append(row)

    return rows


def month_range(start, end):
    """get a list of datetimes incremented by exactly one month"""
    # print [min_date + relativedelta(months=i) for i in range(48)]
    date_vec = [start]
    while date_vec[-1] < end:
        date_vec.append(date_vec[-1] + relativedelta(months=1))
    return date_vec


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
