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

    ignore_merchant = 152

    def get(self, request, *args, **kwargs):
        # TODO
        # factor out the filtering logic here and use that in places
        # where transactions are filtered internally
        # (IndexView._get_transactions_by_month)
        """
        show an arbitrary list of transactions, filtered in different ways,
        according to a search bar:
         start:2017-01                # limit transaction date by month
         start:2017-01-01
         end:2017-12
         statement:985                # select a transaction
         account:alan-chase-credit    # select an account
         account:1                    # select an account
         greater:100                  # filter by transaction amount
         less:100

        tags (this needs more thought and experimentation):
         tags:food                    # include single tag
         tags:food+bike               # include anything with food AND bike
         tags:food,bike               # include anything with food OR bike
         tags:-reimbursed             # exclude reimbursed


        the purpose of this is to consolidate all transaction-list views
        into one endpoint, so:
        1. all the aggregation logic and plotting code can be done in one place
        2. this stuff can be used as an API endpoint instead of a UI view, for a more dynamic page
        """

        filter_kwargs = self.get_filter_kwargs(request.GET)
        print('filter_kwargs:', filter_kwargs)

        # all transactions except credit card payments
        tx = Transaction.objects.filter(**filter_kwargs).exclude(merchant_id=self.ignore_merchant).order_by('-transaction_date')
        if len(tx) == 0:
            print('no results!')
        #Nt = len(tx)
        #tx = tx[Nt - 100:Nt - 1]
        print('transactoin count: %s' % len(tx))
        rows = get_transaction_info(tx)
        table = TransactionTable(rows)
        graph = self.get_graph(tx)
        print('should see a graph...')
        return render(request, 'datatable-dynamic.html',
                      {'table': table, 'resource': 'transaction', 'graph': graph})

    def get_filter_kwargs(self, kwargs):
        """
        given all url query parameters, translate into a dict that can
        be supplied directly to django filter() call
        """
        filter_kwargs = {}
        if not kwargs:
            # default, limit to last 3 months
            filter_kwargs['transaction_date__gte'] = add_months(n=-3)
        elif 'filter_string' in kwargs:
            # textbox filter search, must be parsed
            """
            given a string like
            'start:2017-01 greater:100 tags:food,meal', split into a dict like
            {
                'start': '2017-01',
                'greater': '100',
                'tags': 'food,meal',
            }
            """
            # filter_kwargs = {k: v for k, v in map(lambda x: x.split(':'), kwargs['filter_string'].split())}
            kv_list = kwargs['filter_string'].split()
            filter_kwargs = {}
            for kv in kv_list:
                k, v = kv.split(':')
                filter_kwargs[k] = v
        else:
            # copy directly from query params
            filter_kwargs = kwargs

        # normalize keys and value types
        return self.normalize_filter_kwargs(filter_kwargs)

    def normalize_filter_kwargs(self, kwargs):
        """
        given a dict of options, normalize the keys, and correctly cast the values
        """
        filter_dict = {}
        for k, v in kwargs.items():
            if k in ['statement', 'statement_id']:
                filter_dict['statement_id'] = int(v)
            elif k in ['account', 'account_id']:
                filter_dict['account_id'] = int(v)
            elif k in ['greater']:
                # 'greater:100' limits to transactions >= $100
                filter_dict['debit_amount__gte'] = float(v)
            elif k in ['less']:
                # 'less:100' limits to transactions <= $100
                filter_dict['debit_amount__lte'] = float(v)
            elif k in ['start']:
                # 'start:2017-10-15' limits to after 2017-10-15 (inclusive)
                # 'start:2017-10'    limits to after 2017-10-01 (inclusive)
                # 'start:2017'       limits to after 2017-01-01 (inclusive)
                filter_dict['transaction_date__gte'] = parse_start_date(v)
            elif k in ['end']:
                # 'end:2017-10-15' limits to before 2017-10-15 (inclusive)
                # 'end:2017-10'    limits to before 2017-10-31 (inclusive)
                # 'end:2017'       limits to before 2017-12-31 (inclusive)
                filter_dict['transaction_date__lte'] = parse_end_date(v)
            elif k in ['month']:
                # 'month:2017-10' limits to transaction_date in that month
                start = datetime.datetime.strptime(v, '%Y-%m')
                end = add_months(start, n=1) - datetime.timedelta(days=1)
                filter_dict['transaction_date__gte'] = start
                filter_dict['transaction_date__lte'] = end
            elif k in ['months']:
                # 'months:3' limits to last 3 months from today
                start = add_months(n=-int(v))
                filter_dict['transaction_date__gte'] = start
            elif k in ['days']:
                # 'days:60' limits to last 60 days
                start = datetime.datetime.now() - datetime.timedelta(days=int(v))
                filter_dict['transaction_date__gte'] = start
            elif k in ['tags']:
                filter_dict[k] = v.split(',')  # TODO
            elif k in ['transactions']:
                # TODO: limit to last N transactions
                # this won't go into django filter
                # not sure how best to solve...
                pass
            else:
                print('normalize_filter_kwargs: %s, %s' % (k, v))
                filter_dict[k] = v
        return filter_dict

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
