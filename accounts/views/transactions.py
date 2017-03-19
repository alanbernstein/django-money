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

    t = Transaction.objects.get(id=tid)
    row = get_transaction_info(t)
    table0 = TransactionTable(row)

    tx = Transaction.objects.filter(merchant_id=t.merchant.id)
    rows = get_transaction_info(tx)
    table1 = TransactionTable(rows)

    # m = get_merchants_with_similar_tags(t.tags.all())
    m = [t.merchant]
    rows = get_merchant_info(m)
    table2 = MerchantTable(rows)

    return render(request, 'transaction-detail.html', {
        'merchant_summary': t.merchant.get_summary(),
        'table0': table0,
        'table1': table1,
        'table2': table2,
    })


def transactions_untagged(request, sort=False):
    # TODO: sort by frequency
    # sorted_items = profile.ItemList.annotate(itemcount=Count('name'))
    # sorted_items = sorted_items.order_by('-itemcount')

    tx = Transaction.objects.filter(tags__isnull=True, merchant__tags__isnull=True)
    rows = get_transaction_info(tx)
    rows2 = [row for row in rows if not row['tags']]  # TODO: why is this necessary
    table = TransactionTable(rows2)
    # return render(request, 'datatable-basic.html', {'table': table})
    return render(request, 'datatable.html',
                  {'table': table, 'resource': 'transaction'})

def transactions_unnamed(request, *args, **kwargs):
    # this doesnt make sense right?
    return ''

def get_transactions_by_tag(tag, merchants=True):
    tag_merchants = Merchant.objects.filter(tags__name__in=[tag.name])
    merchant_ids = [m.id for m in tag_merchants]

    tag_tx = Transaction.objects.filter(Q(tags__name__in=[tag.name]) | Q(merchant_id__in=merchant_ids))

    return tag_tx

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
