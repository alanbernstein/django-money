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
from accounts.helpers import get_transaction_info, get_merchant_info

from panda.debug import debug


def merchant_detail(request, *args, **kwargs):
    # TODO: unique matches
    mid = kwargs['merchant_id']
    merchant = Merchant.objects.get(id=mid)
    tx = Transaction.objects.filter(merchant_id=mid)

    rows = get_transaction_info(tx)
    table = TransactionTable(rows)
    return render(request, 'merchant-detail.html', {'table': table,
                                                    'merchant_name': merchant.name,
                                                    'merchant_summary': merchant.get_summary()})



def get_merchants_with_similar_tags(tags):
    # TODO
    return []


def merchants_untagged(request, sort=False):
    # TODO: sort by frequency
    merchants = Merchant.objects.filter(tags__isnull=True)
    rows = get_merchant_info(merchants)
    table = MerchantTable(rows)
    return render(request, 'datatable.html',
                  {'table': table, 'resource': 'merchant'})


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
