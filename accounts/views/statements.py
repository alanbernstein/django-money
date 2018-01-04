from django.shortcuts import render
from django.views.generic import View

from accounts.models import (Statement,
                             StatementTable,
                             )
from accounts.helpers import get_statement_info
from accounts.tags import get_tag_totals, get_tag_exclusive_totals_by_size


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


statement_list = StatementListView.as_view()
