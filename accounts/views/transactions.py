import datetime

from django.shortcuts import render
from django.views.generic import View
from django.http import HttpResponse
from django_tables2 import MultiTableMixin
from django.views.generic.base import TemplateView

from accounts.models import (Transaction,
                             MerchantTable,
                             Statement,
                             TransactionTable,
                             filter_transactions,
                             )

from accounts.helpers import (get_transaction_info,
                              get_merchant_info,
                              get_compare_data,
                              )

from accounts.tags import get_tag_totals, get_tag_exclusive_totals_by_size
from accounts.helpers import parse_start_date, parse_end_date, add_months

import plotly.graph_objs as go
import plotly.offline as opy
from plot_tools import get_layout

from panda.debug import debug


def transaction_list_table(request):
    all_tx = Transaction.objects.all()
    Nt = len(all_tx)
    tx = all_tx[Nt - 100:Nt - 1]

    rows = get_transaction_info(tx)
    print(rows[0])
    table = TransactionTable(rows)
    # return render(request, 'datatable-basic.html', {'table': table})
    return render(request, 'datatable.html',
                  {'table': table, 'resource': 'transaction'})


def transaction_list_simple(request):
    resp = ''

    resp += '<h2>all transactions</h2>'
    for t in Transaction.objects.all():
        resp += t.as_link()

    return HttpResponse(resp)


class TransactionListView(View):
    plot_args = dict(
        auto_open=False,
        output_type='div',
        show_link=False,
        config={'displayModeBar': False}
    )

    def get(self, request, *args, **kwargs):
        filter_fields = request.GET
        tx = filter_transactions(filter_fields)
        rows = get_transaction_info(tx)
        table = TransactionTable(rows)
        graph = self.get_graph(tx)
        print('should see a graph...')
        return render(request, 'datatable-dynamic.html',
                      {'table': table, 'resource': 'transaction', 'graph': graph})

    def get_graph(self, tx):
        # tag_amounts = get_tag_totals(tx)
        tag_amounts = get_tag_exclusive_totals_by_size(tx)
        tags = [t[0] for t in tag_amounts[::-1]]
        debit_totals = [t[2] for t in tag_amounts[::-1]]
        data = [
            go.Bar(y=tags, x=debit_totals, orientation='h', name='stuff'),
            dict(y=tags, x=debit_totals, text=map(str, debit_totals), mode='text', textposition='right'),
        ]
        layout = get_layout(title='Expenditures by tag', xtitle='$', ytitle='Tag', showlegend=False)
        fig = go.Figure(data=data, layout=layout)
        return opy.plot(fig, **self.plot_args)


# transaction_list = transaction_list_table
transaction_list = TransactionListView.as_view()


class TransactionDetailView(View):
    def get(self, request, *args, **kwargs):
        tid = kwargs['transaction_id']

        t = Transaction.objects.get(id=tid)

        m = t.merchant
        if m:
            tx = Transaction.objects.filter(merchant_id=m.id)
            merchant_summary = m.get_summary()
            transaction_summary = t.get_summary()
        else:
            tx = []
            merchant_summary = '(no merchant)'
            transaction_summary = '(no transaction)'
        rows = get_transaction_info(tx)
        table1 = TransactionTable(rows)

        # m = get_merchants_with_similar_tags(t.tags.all())
        rows = get_merchant_info(t.merchant)
        table2 = MerchantTable(rows)

        return render(request, 'transaction-detail.html', {
            'merchant_summary': merchant_summary,
            'transaction_summary': transaction_summary,
            'table1': table1,
            'table2': table2,
        })


def transaction_detail_func(request, *args, **kwargs):
    tid = kwargs['transaction_id']

    t = Transaction.objects.get(id=tid)
    row = get_transaction_info(t)
    table0 = TransactionTable(row)

    mid = t.merchant.id
    if mid:
        tx = Transaction.objects.filter(merchant_id=mid)
    else:
        tx = []
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


# transaction_detail = transaction_detail_func
transaction_detail = TransactionDetailView.as_view()


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


def transactions_compare(request, tags):
    # TODO: this should render a template which hits an api for data
    taglist = tags.split('+')
    data = ''
    data += 'tags: %s' % ', '.join(taglist)
    # chart_data = get_compare_data(taglist)
    return HttpResponse(data)


def transactions_subdivide(request, tags):
    # TODO: this should render a template which hits an api for data
    taglist = tags.split('+')
    data = ''
    data += 'tags: %s' % ', '.join(taglist)
    # chart_data = get_subdivide_data(taglist)
    return HttpResponse(data)
