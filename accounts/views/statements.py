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
from accounts.helpers import get_transaction_info, get_statement_info

from panda.debug import debug


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
