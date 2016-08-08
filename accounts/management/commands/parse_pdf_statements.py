from optparse import make_option
import re
import subprocess
from datetime import datetime as dt

from django.core.management.base import BaseCommand, CommandError

from accounts.models import Account, Statement, Transaction, Merchant
from accounts.management.commands.initialize import populate_chase_credit_statements

# from finance.parse_statements import parse_chase_credit_statement
from panda.progressbar import ProgressBar
from panda.debug import pp, debug, pm
from panda.debug import annotate_time_indent as annotate


# NOTE: formerly known as import_pdf_statements
class Command(BaseCommand):
    help="todo"

    def add_arguments(self, parser):
        # TODO: allow specifying account / date range / whatever
        #parser.add_argument('file_glob', nargs='+', type=str)
        pass

    @pm
    def handle(self, *args, **options):
        """find all un-parsed statements, get correct parser, parse"""

        # statements = Statement.objects.all()
        # for statement in statements:
        #     self.stdout.write('%s' % statement, ending='')
        #     if not statement.downloaded:
        #         self.stdout.write(' - need to download\n')
        #         continue
        #     if statement.parsed:
        #         self.stdout.write(' - already parsed\n')
        #         continue

        populate_chase_credit_statements()

        unparsed = Statement.objects.filter(downloaded=True, parsed=False)
        for statement in unparsed:
            Parser = parser_map[statement.account.name]
            parser = Parser(statement)
            parser.parse()
        print('done parsing %d statements' % unparsed.count())


# TODO: move this stuff to a parsers folder

DATE_PRINT_FORMAT = '%Y/%m/%d'
DATE_PARSE_FORMAT = '%m/%d/%y'
MDY_REGEX = '[0-9][0-9]/[0-9][0-9]/[0-9][0-9]'


class PdfStatementParser(object):
    def __init__(self, statement):
        self.statement = statement


class ChaseCreditParser(PdfStatementParser):
    def parse(self):
        self.get_statement_dates()
        self.get_transaction_details()

    def get_statement_dates(self):
        """parse start date, end date, due date"""
        start_date, end_date, due_date = None, None, None
        dates_command = 'pdftotext -layout %s - | grep "%s"' % (self.statement.get_filename(), MDY_REGEX)
        raw_output = subprocess.check_output(dates_command, shell=True)
        lines = str(raw_output).strip().split('\n')

        for line in lines:
            m1 = re.search('Opening/Closing.*(%s) - (%s)' % (MDY_REGEX, MDY_REGEX), line)
            if m1:
                start_date = dt.strptime(m1.groups()[0], DATE_PARSE_FORMAT)
                end_date = dt.strptime(m1.groups()[1], DATE_PARSE_FORMAT)
            if not start_date or not end_date:
                m1 = re.search('Statement Date.*(%s) - (%s)' % (MDY_REGEX, MDY_REGEX), line)
                if m1:
                    start_date = dt.strptime(m1.groups()[0], DATE_PARSE_FORMAT)
                    end_date = dt.strptime(m1.groups()[1], DATE_PARSE_FORMAT)

            m2 = re.search('Due Date.*(%s)' % MDY_REGEX, line)
            if m2:
                due_date = dt.strptime(m2.groups()[0], DATE_PARSE_FORMAT)

        if not all([start_date, end_date, due_date]):
            pp(lines)
            debug()

        self.statement.due_date = due_date
        self.statement.start_date = start_date
        self.statement.end_date = end_date
        self.statement.save()

    def get_transaction_details(self):
        # merchant, post_date
        # credit_amount, notes

        transactions_command = 'pdftotext -layout %s - | grep "^ *[01][0-9]/"' % self.statement.get_filename()
        raw_output = subprocess.check_output(transactions_command, shell=True)
        lines = str(raw_output).strip().split('\n')

        print('  %d lines' % len(lines))
        for line in lines:
            # TODO: this misses a few lines..
            m = re.search('([0-1][0-9]/[0-9][0-9])(.*)([ -][0-9,]+\.[0-9][0-9])', line)
            if not m:
                print(line)
                continue

            date_str = m.groups()[0].strip()
            year = self.statement.due_date.year
            if self.statement.due_date.month == 1 and date_str.startswith('12'):
                # TODO: this is failing for some reason 
                year -= 1
            timestamp = dt.strptime('%s/%02d' % (date_str, year % 100), DATE_PARSE_FORMAT)

            desc_str = m.groups()[1].strip()
            dollars_str = m.groups()[2].strip()
            dollars_float = float(dollars_str.replace(',', ''))

            tx, new = Transaction.objects.get_or_create(account=self.statement.account,
                                                        transaction_date=timestamp,
                                                        debit_amount=dollars_float,
                                                        statement_id=self.statement.id,
                                                        description_raw=desc_str)

        self.statement.parsed = True
        self.statement.save()


parser_map = {'Chase Credit': ChaseCreditParser}
