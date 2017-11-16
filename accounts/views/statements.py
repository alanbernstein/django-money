from django.shortcuts import render
from django.views.generic import View
from django.utils.html import format_html

from accounts.models import (Statement,
                             Transaction,
                             TransactionTable,
                             StatementTable,
                             )
from accounts.helpers import get_transaction_info, get_statement_info
from accounts.tags import get_tag_totals, get_tag_exclusive_totals_by_size

import plotly.graph_objs as go
import plotly.offline as opy
from plot_tools import get_layout


def statement_detail_table(request, *args, **kwargs):
    sid = kwargs['statement_id']
    s = Statement.objects.get(id=sid)
    tx = Transaction.objects.filter(statement_id=s.id)
    rows = get_transaction_info(tx)
    table = TransactionTable(rows)
    return render(request, 'datatable.html',
                  {'table': table, 'resource': 'transaction'})


class StatementDetailView(View):
    plot_args = dict(
        auto_open=False,
        output_type='div',
        show_link=False,
        config={'displayModeBar': False}
    )

    def get(self, request, *args, **kwargs):
            sid = kwargs['statement_id']
            s = Statement.objects.get(id=sid)
            # all transactions except credit card payments
            tx = Transaction.objects.filter(statement_id=s.id).exclude(merchant_id=152)
            rows = get_transaction_info(tx)
            table = TransactionTable(rows)
            return render(request, 'datatable.html',
                          {'table': table, 'resource': 'transaction', 'graph': self.get_graph(tx)})

    def get_graph(self, tx):
        # tag_amounts = get_tag_totals(tx)
        tag_amounts = get_tag_exclusive_totals_by_size(tx)
        tags = [t[0] for t in tag_amounts[::-1]]
        debit_totals = [t[2] for t in tag_amounts[::-1]]
        x_text = [x+10 for x in debit_totals]
        data = [
            go.Bar(y=tags, x=debit_totals, orientation='h', name='stuff'),
            dict(y=tags, x=x_text, text=map(str, debit_totals), mode='text'),
        ]
        layout = get_layout(title='Expenditures by tag', xtitle='$', ytitle='Tag', showlegend=False)
        fig = go.Figure(data=data, layout=layout)
        return opy.plot(fig, **self.plot_args)


statement_detail = StatementDetailView.as_view()


def statement_list_table(request, *args, **kwargs):
    statements = Statement.objects.all()
    rows = get_statement_info(statements)
    table = StatementTable(rows)
    return render(request, 'datatable.html',
                  {'table': table, 'resource': 'statement'})


class StatementListView(View):
    def get(self, request, *args, **kwargs):
        statements = Statement.objects.all()
        rows = get_statement_info(statements)
        table = StatementTable(rows)
        return render(request, 'datatable.html',
                      {
                          'table': table,
                          'resource': 'statement',
                          'datatable_kwargs': {"order": [[2, 'desc']]},
                      })


# statement_list = statement_list_table
statement_list = StatementListView.as_view()
