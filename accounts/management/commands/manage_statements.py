import glob
import os
import re
import dateparser
from collections import Counter
from django.core.management.base import BaseCommand
from accounts.models import Transaction, Merchant, Statement, Account

from panda.debug import pp, debug, pm


class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument('--populate', action='store_true', default=False, help='read PDF statements into statement objects (no parsing)')
        parser.add_argument('--remove-unparsed', action='store_true', default=False, help="poor man's deduplicate - remove unparsed statements")
        parser.add_argument('--deduplicate', action='store_true', default=False, help="real deduplicate, based on statement dates")

    def handle(self, *args, **options):
        if options['populate']:
            populate_chase_credit_statements()
        if options['remove_unparsed']:
            remove_unparsed_statements()
        if options['deduplicate']:
            remove_duplicate_statements_and_transactions()


def remove_duplicate_statements_and_transactions():
    # TODO: use this to deal with the 2015-05 double statement problem
    ss = Statement.objects.all()
    dates = [s.end_date for s in ss]

    date_counter = Counter(dates)
    duplicates = {k: v for k, v in date_counter.items() if v > 1}

    if duplicates:
        print('%d duplicate sets...' % len(duplicates))
        for date, count in duplicates.items():
            st = Statement.objects.filter(end_date=date)
            print(st)
            for s in st:
                tx = Transaction.objects.filter(statement=s)
                for n, t in enumerate(tx):
                    print(n, t)

                print(' ')

def rename_chase_credit_statements():
    pass


def remove_unparsed_statements():
    # difficult to actually dedupe; if you end up with multiple instances of
    # the same statement, then you can do this to remove the new one only
    # if you do it before parsing it
    Statement.objects.filter(parsed=False).delete()


def populate_chase_credit_statements():
    """reads statements in download directory, and adds them to database (without parsing)"""
    account, new = Account.objects.get_or_create(slug='alan-chase-credit')
    glob_pattern = account.statements_directory + '/chase-credit-20*.pdf'
    # TODO: move elsewhere and generalize
    # TODO: set up better organization of files

    filenames = glob.glob(glob_pattern)
    filenames.sort()
    created_count = 0
    for f in filenames:
        # don't need this stuff, parse date from contents, not filename
        # m = re.search('[0-9]{4}-[0-9]{2}(-[0-9]{2})?', f)
        # date_str = m.group()
        # filename_date = dateparser.parse(date_str).date()
        file_path, file_name = os.path.split(f)

        if False:
            matches = Statement.objects.filter(account_id=account.id, file_name=file_name)
            exists = len(matches) > 0
            print(account, file_name, exists)
            debug()
            continue
        statement, new = Statement.objects.get_or_create(account_id=account.id,
                                                         # end_date=filename_date,
                                                         file_path=file_path,
                                                         file_name=file_name)  # need to migrate before this will work

        created_count += new
        statement.downloaded = True
        statement.save()
        if new:
            print(statement)

    print('done populating (checked %d PDF files, found %d new statements)' % (len(filenames), created_count))
