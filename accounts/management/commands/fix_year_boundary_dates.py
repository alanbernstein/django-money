import re
import datetime
from itertools import groupby
from django.core.management.base import BaseCommand
from django.db.models import Sum
from accounts.models import Transaction, Merchant
from accounts.base import get_account

from panda.debug import pp, debug, pm


class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument('--account', '-a', default='', help='specify account to use')

    def handle(self, *args, **options):

        account = get_account(options['account'], self.stdout)
        fix_dates(account)


def fix_dates(account):
    tt = Transaction.objects.all()
    for t in tt:
        if t.transaction_date > t.statement.end_date:
            date = t.transaction_date
            new_date = date.replace(year = date.year - 1)
            t.transaction_date = new_date
            t.save()
            print(t.statement, date, new_date)
