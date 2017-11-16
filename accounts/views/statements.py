from django.shortcuts import render
from django.views.generic import View
from django.utils.html import format_html

from accounts.models import (Statement,
                             Transaction,
                             TransactionTable,
                             StatementTable,
                             )
from accounts.helpers import get_transaction_info, get_statement_info

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
            tx = Transaction.objects.filter(statement_id=s.id)
            rows = get_transaction_info(tx)
            table = TransactionTable(rows)
            return render(request, 'datatable.html',
                          {'table': table, 'resource': 'transaction', 'graph': self.get_graph()})

    def get_graph(self):
        data = [go.Bar(x=['food', 'bike'], y=[400, 300], name='stuff')]
        layout = get_layout(title='Expenditures by tag (fake)')
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
