from django.shortcuts import render
from django.utils.html import format_html

from accounts.models import (Account,
                             Statement,
                             AccountTable,
                             StatementTable,
                             )
from accounts.helpers import get_statement_info


def account_list(request, *args, **kwargs):
    accounts = Account.objects.all()
    rows = get_account_info(accounts)
    table = AccountTable(rows)
    return render(request, 'datatable.html',
                  {'table': table, 'resource': 'account'})


def account_detail(request, *args, **kwargs):
    aid = kwargs['account_id']
    a = Account.objects.get(id=aid)
    statements = Statement.objects.filter(account_id=aid)
    account_summary = format_html('%d statements' % len(statements))
    rows = get_statement_info(statements)
    table = StatementTable(rows)
    return render(request, 'account-detail.html', {'table': table,
                                                   'account_description': a.__str__(),
                                                   'account_summary': account_summary})


def get_account_info(accounts=None):
    if not hasattr(accounts, '__iter__'):
        # convert single instance to list
        accounts = [accounts]

    if isinstance(accounts[0], int):
        # get transactions from ids
        ids = accounts
        accounts = Account.objects.filter(id__in=ids)

    rows = []
    for a in accounts:
        row = {}
        row['id'] = a.as_link(self_link=True)
        row['name'] = a.name
        row['user'] = a.user
        row['type'] = Account.ACCOUNT_TYPES[a.type][1]
        rows.append(row)

    return rows
