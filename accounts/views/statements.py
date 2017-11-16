from django.shortcuts import render
from django.views.generic import View
from django.utils.html import format_html

from accounts.models import (Statement,
                             Transaction,
                             TransactionTable,
                             StatementTable,
                             )
from accounts.helpers import get_transaction_info, get_statement_info


def statement_detail(request, *args, **kwargs):
    sid = kwargs['statement_id']
    s = Statement.objects.get(id=sid)
    tx = Transaction.objects.filter(statement_id=s.id)
    rows = get_transaction_info(tx)
    table = TransactionTable(rows)
    return render(request, 'datatable.html',
                  {'table': table, 'resource': 'transaction'})


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
