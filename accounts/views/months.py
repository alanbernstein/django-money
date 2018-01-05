from django.shortcuts import render
from django.views.generic import View

from accounts.models import (Statement,
                             Transaction,
                             StatementTable,
                             )
from accounts.helpers import get_statement_info

import datetime


class MonthListView(View):
    def get(self, request, *args, **kwargs):
        # TODO create Month and MonthTable models
        # (right now this is just using statements...)
        start = Transaction.objects.earliest('transaction_date').transaction_date
        end = datetime.datetime.now()

        statements = Statement.objects.all()
        rows = get_statement_info(statements)
        table = StatementTable(rows)
        return render(request, 'datatable.html',
                      {
                          'table': table,
                          'resource': 'statement',
                          'datatable_kwargs': {"order": [[2, 'desc']]},
                      })


month_list = MonthListView.as_view()
