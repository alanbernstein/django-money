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
                             TransactionTable,
                             AccountTable,
                             StatementTable,
                             )

from panda.debug import debug

"""
TODO: view tag breakdown, but also view subtag breakdown
- that is, i should be able to view something like a chart of rent/bills/food/entertainment/...
- but also, a chart of all transactions matching a single tag, split up by other tags they also have. eg:
  - food: groceries/meal/date
  - travel: airfare/lodging/food
- etc

IDEA: label some tags as "top-level", that is, tags in that set will never be used together
- bills
- food
- transportation
IDEA: figure out this set automatically

options for decent charts:
http://chartit.shutupandship.com/
https://www.djangopackages.com/grids/g/charts/

- django-nvd3
  - depends on python-nvd3, nvd3, bower - might be the best looking/most mature (https://pypi.python.org/pypi/django-nvd3)


http://nvd3.org/examples/


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


def timeseries(request):
    resp = ''

    return HttpResponse(resp)


