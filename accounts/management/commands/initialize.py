import glob
import re
import os
import json
from itertools import groupby
import dateparser

from django.core.management.base import BaseCommand, CommandError
from django.db.models import Sum

from accounts.models import Account, Statement, Transaction, Merchant, User
from taggit.models import Tag

from accounts.base import get_account

#from finance.parse_statements import parse_chase_credit_statement
from panda.progressbar import ProgressBar
from panda.debug import pp, debug, pm
from panda.debug import annotate_time_indent as annotate


class Command(BaseCommand):
    """one-off scripts for bootstrapping database
    initialize -a 'chase credit' -u alan  # initialize account'
    initialize -a 'chase-credit' -s       # initialize statements for account
    initialize -a 'chase-credit' -t       # initialize tags for account
    initialize -a alan-chase-credit -p -f ../../finance/merchant_patterns.json  # initialize merchants from file
    initialize -a alan-chase-credit -t -f ../../finance/merchant_tags.json      # import merchant tags from file
    initialize -a alan-chase-credit --assign                                    # assign merchants to transactions
    """

    def add_arguments(self, parser):
        parser.add_argument('--account', '-a', default='', help='specify account to use')
        parser.add_argument('--user', '-u', default='', help='specify user for account init')
        parser.add_argument('--filename', '-f', default='', help='supply a filename')
        parser.add_argument('--tags', '-t', action='store_true', default=False, help='import merchant tags')
        parser.add_argument('--patterns', '-p', action='store_true', default=False, help='import merchant patterns')

    def handle(self, *args, **options):
        account = get_account(options['account'], stdout=self.stdout)
        if not account:
            return

        # run stuff
        if options['user']:
            initialize_account('Alan', 'Chase Credit', Account.CREDIT)

        if options['patterns'] and options['filename']:
            initialize_merchant_patterns(account, options['filename'])

        if options['tags'] and options['filename']:
            initialize_merchant_tags(account, options['filename'])


def initialize_merchant_tags(account, filename):
    with open(filename, 'r') as f:
        data = json.load(f)

    for name, tags in data.items():
        merchant = Merchant.objects.get(name=name)
        merchant.tags.add(*tags)
        merchant.save()

    debug()


def initialize_merchant_patterns(account, filename):
    with open(filename, 'r') as f:
        data = json.load(f)

    for name, patterns in data.items():
        if len(patterns) > 1:
            print(name, patterns)
        else:
            merchant, new = Merchant.objects.get_or_create(name=name, pattern=patterns[0])
            merchant.save()

    debug()


def initialize_account(user, account_name, account_type):
    if type(user) is str:
        user, new = User.objects.get_or_create(name=user)
        user.save()

    account, new = Account.objects.get_or_create(name=account_name,
                                                 user_id=user.id,
                                                 type=account_type)
    account.save()  # sets slug


