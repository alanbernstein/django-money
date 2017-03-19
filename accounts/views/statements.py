from django.shortcuts import render
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
    statement_summary = format_html('$%.2f, %d transactions' % (s.get_total(), s.get_count()))

    tx = Transaction.objects.filter(statement_id=s.id)
    rows = get_transaction_info(tx)
    table = TransactionTable(rows)
    return render(request, 'statement-detail.html', {'table': table,
                                                     'statement_description': s.__str__(),
                                                     'statement_summary': statement_summary})


def statement_list(request, *args, **kwargs):
    statements = Statement.objects.all()
    rows = get_statement_info(statements)
    table = StatementTable(rows)
    return render(request, 'datatable.html',
                  {'table': table, 'resource': 'statement'})
