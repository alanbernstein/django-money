from __future__ import unicode_literals

import os
import datetime

from django.db import models
from django.db.models import Sum, Count, Q
from django.template.defaultfilters import slugify
from regex_field import RegexField
from taggit.managers import TaggableManager  # ??
from django.utils.html import format_html
import django_tables2 as tables
from taggit.models import Tag


__all__ = ['User', 'Account', 'Merchant', 'Statement', 'Transaction']


class User(models.Model):
    name = models.CharField(max_length=300)

    def __str__(self):
        return self.name


# class TestIdea(models.Model):
#     make_types(['type_name1', 'type_name2', 'bar'])
# wonder if there is a way to have this automatically define all:
# - member variables
# - list of tuples for the types variable
# - type field

statement_root = os.getenv('STATEMENTS')


class Account(models.Model):
    CHECKING, CREDIT, SAVING, INVESTMENT, BILL = range(5)
    ACCOUNT_TYPES = ((CHECKING, 'checking'), (CREDIT, 'credit'), (SAVING, 'saving'), (INVESTMENT, 'investment'))
    type = models.SmallIntegerField(choices=ACCOUNT_TYPES)
    name = models.CharField(max_length=300)
    user = models.ForeignKey(User)
    slug = models.SlugField()
    statements_directory = models.CharField(max_length=300)

    def __str__(self):
        return "%s's %s" % (self.user.name, self.name)

    def save(self, *args, **kwargs):
        # set derived stuff if new
        # TODO this is probably wrong
        if not self.id:
            self.slug = slugify('%s %s' % (self.user, self.name))
            self.statements_directory = statement_root + self.slug + os.path.sep

        super(Account, self).save(*args, **kwargs)

    def as_link(self, self_link=False):
        if self_link:
            return format_html('<a href="/accounts/%s">%s</a>' % (self.id, self.id))
        else:
            return format_html('<a href="/accounts/%s">%s</a>' % (self.id, self.name))

    def get_statements_directory(self):
        # TODO when i need it working on both desktop and laptop
        pass

    def get_statements_count(self):
        # TODO why doesnt this work?
        # s = Statement.objects.filter(account_id==self.id)
        # c = s.count()
        # return c
        return 0


class Location(models.Model):
    pass


class Merchant(models.Model):
    name = models.CharField(max_length=300)
    pattern = RegexField(max_length=1000)
    tags = TaggableManager()

    def __str__(self):
        m = self.name
        tags = self.tags.all()
        # debug()
        if tags:
            tagnames = [t.name for t in tags]
            m = '%s (%s)' % (m, ', '.join(tagnames))
        return m

    def get_tags_as_links(self):
        link_list = []
        for tag in self.tags.all():
            link_list.append('<a href="/tags/%s">%s</a>' % (tag.id, tag.name))
        link_str = ', '.join(link_list)
        return format_html(link_str)

    def as_link(self, self_link=False):
        if self_link:
            return format_html('<a href="/merchants/%s">%s</a>' % (self.id, self.id))
        else:
            return format_html('<a href="/merchants/%s">%s</a>' % (self.id, self.name))

    def get_summary(self):
        tx = Transaction.objects.filter(merchant_id=self.id)
        count = tx.count()
        key = 'debit_amount'
        amount = tx.aggregate(Sum(key))[key + '__sum']

        return format_html('$%.2f, %d transactions<br>%s' % (amount, count, self.pattern.pattern))


class Statement(models.Model):
    account = models.ForeignKey(Account)
    statement_date = models.DateField(null=True, blank=True)
    due_date = models.DateField(null=True, blank=True)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    file_path = models.CharField(max_length=300, default='', blank=True)
    file_name = models.CharField(max_length=50, default='', blank=True)
    file_hash = models.CharField(max_length=32, default='', blank=True)
    downloaded = models.BooleanField(default=False)
    parsed = models.BooleanField(default=False)  # TODO: change this to 'parsed'

    def __str__(self):
        if self.parsed and self.end_date:
            return '%s ending %s' % (self.account.name,
                                     datetime.datetime.strftime(self.end_date, '%Y-%m-%d'))
        else:
            return '%s - unparsed' % self.file_name

    def get_filename(self):
        return '%s/%s' % (self.file_path, self.file_name)

    def as_link(self, self_link=False):
        consolidated_views = True
        if consolidated_views:
            # use the transactions view with a statement filter
            href = '/transactions?statement_id=%s' % self.id
        else:
            # use the dedicated statements view
            href = '/statements/%s' % self.id

        if self_link:
            # used for the statement-list view,
            # because there should be at least onse place for user to be
            # able to identify statements by ID
            text = self.id
        else:
            # used everywhere else, because usually the end-date of the
            # statement is enough information
            text = self.end_date

        return format_html('<a href="%s">%s</a>' % (href, text))

    def get_count(self, debit_only=True):
        # TODO debit only
        # TODO is there a more django-y way to do this?
        tx = Transaction.objects.filter(statement_id=self.id)
        return tx.count()

    def get_total(self, debit_only=True):
        # TODO debit only
        # TODO is there a more django-y way to do this?
        tx = Transaction.objects.filter(statement_id=self.id)
        key = 'debit_amount'
        total = tx.aggregate(Sum(key))[key + '__sum']
        if not total:
            # TODO this shouldnt happen
            total = 0

        return total

    def __self__(self):
        if self.end_date:
            return '%s - %s' % (self.account.__str__(), self.end_date)
        else:
            return '%s (unparsed)' % self.account.__str__()


class Transaction(models.Model):
    account = models.ForeignKey(Account)
    merchant = models.ForeignKey(Merchant, null=True, blank=True)
    statement = models.ForeignKey(Statement, null=True, blank=True)
    transaction_date = models.DateField()
    post_date = models.DateField(null=True, blank=True)
    debit_amount = models.DecimalField(decimal_places=2, max_digits=10, null=True, blank=True)
    credit_amount = models.DecimalField(decimal_places=2, max_digits=10, null=True, blank=True)
    description_raw = models.CharField(max_length=300)
    description = models.CharField(max_length=300, default='', blank=True)
    notes = models.TextField(default='', blank=True)
    tags = TaggableManager()
    # all_tags = TaggableManager()
    # location - figure out a good way to do that

    # not sure if this should be an enum, or just a string...
    TRANSACTION_TYPES = ()
    SALE = 0
    type = models.SmallIntegerField(choices=TRANSACTION_TYPES, default=SALE)

    def __str__(self):
        if self.merchant:
            desc = self.merchant.name
        elif self.description:
            desc = self.description
        else:
            desc = '(no description)'

        if self.debit_amount is not None:
            amount = self.debit_amount
        elif self.credit_amount is not None:
            amount = -self.credit_amount
        else:
            amount = 0

        res = '%5s %s  $%10.2f  %s' % (self.id, self.transaction_date, amount, desc)
        return res

    def get_summary(self):
        if self.merchant:
            desc = self.merchant.name
        elif self.description:
            desc = self.description
        else:
            desc = '(no description)'

        return format_html('$%.2f on %s at %s' % (self.debit_amount, self.transaction_date, desc))

    def get_tags(self):
        """tags are defined for both merchants and transactions.
        call this getter to see the full list"""
        tags = set(self.tags.all())
        if self.merchant:
            tags = tags.union(self.merchant.tags.all())
        return tags

    def get_tags_as_strings(self):
        # TODO kludge until i can figure out how to use ORM properly
        tags = set(self.tags.all())
        if self.merchant:
            tags = tags.union(self.merchant.tags.all())
        return map(lambda x: x.name, tags)

    def get_tags_as_links(self):
        link_list = []
        for tag in self.get_tags():
            link_list.append('<a href="/tags/%s">%s</a>' % (tag.id, tag.name))
        link_str = ', '.join(link_list)
        return format_html(link_str)

    def as_link(self, self_link=False):
        if self_link:
            return format_html('<a href="/transactions/%s">%s</a>' % (self.id, self.id))
        else:
            return format_html('<a href="/transactions/%s">%s</a>' % (self.id, self))


def filter_transactions(filter_fields, limit=None):
    # TODO: what is the appropriate way to make this a method
    #       on the Transaction model?
    """
    get an arbitrary list of transactions, filtered in different ways,
    according to various filter parameters. several ways to do this:
    1. provide {'filter_string': 'kv1, kv2, ...'}, where kvN is something like these:
     start:2017-01                # limit transaction date by month
     start:2017-01-01
     end:2017-12
     statement:985                # select a transaction
     account:alan-chase-credit    # select an account
     account:1                    # select an account
     greater:100                  # filter by transaction amount
     less:100
    (this is intended for parsing a text search field from the UI)

    tags (this needs more thought and experimentation):
     tags:food                    # include single tag
     tags:food+bike               # include anything with food AND bike
     tags:food,bike               # include anything with food OR bike
     tags:-reimbursed             # exclude reimbursed

    2. provide {'nickname1': val1, 'nickname2': val2, ...}
    where nicknames are the same as above
    (this could be a shorthand way to handle transaction filters,
    for command line or internal usage)

    3. provide {'name1': val1, 'name2': val2, ...}
    where names are the literal django filter argument names, like
      statement_id
      debit_amount__gte
      transaction_date__lte
    (this is a side effect, not much reason to do this vs a django filter

    the purpose of this is to allow consolidating all transaction-list views
    into one endpoint, so:
    1. all the aggregation logic and plotting code can be done in one place
    2. this stuff can be used as an API endpoint instead of a UI view, for a more dynamic page
    """

    # TODO: filter out dumb stuff here: reimbursements, payments, etc
    ignore_merchant = 152
    filter_kwargs = get_filter_kwargs(filter_fields)

    # all transactions except credit card payments
    tx = Transaction.objects.filter(**filter_kwargs).exclude(merchant_id=ignore_merchant).order_by('-transaction_date')
    if len(tx) == 0:
        print('no results!')
    if limit:
        Nt = len(tx)
        tx = tx[Nt - 100:Nt - 1]
    return tx


def get_filter_kwargs(kwargs):
    """
    given all url query parameters, translate into a dict that can
    be supplied directly to django filter() call
    """
    from accounts.helpers import add_months  # TODO fix this
    filter_kwargs = {}
    if not kwargs:
        # default, limit to last 3 months
        filter_kwargs['transaction_date__gte'] = add_months(n=-3)
    elif 'filter_string' in kwargs:
        # textbox filter search, must be parsed
        """
        given a string like
        'start:2017-01 greater:100 tags:food,meal', split into a dict like
        {
            'start': '2017-01',
            'greater': '100',
            'tags': 'food,meal',
        }
        """
        # filter_kwargs = {k: v for k, v in map(lambda x: x.split(':'), kwargs['filter_string'].split())}
        kv_list = kwargs['filter_string'].split()
        filter_kwargs = {}
        for kv in kv_list:
            k, v = kv.split(':')
            filter_kwargs[k] = v
    else:
        # copy directly from query params
        filter_kwargs = kwargs

    # normalize keys and value types
    return normalize_filter_kwargs(filter_kwargs)


def normalize_filter_kwargs(kwargs):
    """
    given a dict of options, normalize the keys, and correctly cast the values
    """
    from accounts.helpers import parse_start_date, parse_end_date, add_months

    filter_dict = {}
    for k, v in kwargs.items():
        if k in ['statement', 'statement_id']:
            filter_dict['statement_id'] = int(v)
        elif k in ['account', 'account_id']:
            filter_dict['account_id'] = int(v)
        elif k in ['greater']:
            # 'greater:100' limits to transactions >= $100
            filter_dict['debit_amount__gte'] = float(v)
        elif k in ['less']:
            # 'less:100' limits to transactions <= $100
            filter_dict['debit_amount__lte'] = float(v)
        elif k in ['start']:
            # 'start:2017-10-15' limits to after 2017-10-15 (inclusive)
            # 'start:2017-10'    limits to after 2017-10-01 (inclusive)
            # 'start:2017'       limits to after 2017-01-01 (inclusive)
            filter_dict['transaction_date__gte'] = parse_start_date(v)
        elif k in ['end']:
            # 'end:2017-10-15' limits to before 2017-10-15 (inclusive)
            # 'end:2017-10'    limits to before 2017-10-31 (inclusive)
            # 'end:2017'       limits to before 2017-12-31 (inclusive)
            filter_dict['transaction_date__lte'] = parse_end_date(v)
        elif k in ['month']:
            # 'month:2017-10' limits to transaction_date in that month
            start = datetime.datetime.strptime(v, '%Y-%m')
            end = add_months(start, n=1) - datetime.timedelta(days=1)
            filter_dict['transaction_date__gte'] = start
            filter_dict['transaction_date__lte'] = end
        elif k in ['months']:
            # 'months:3' limits to last 3 months from today
            start = add_months(n=-int(v))
            filter_dict['transaction_date__gte'] = start
        elif k in ['days']:
            # 'days:60' limits to last 60 days
            start = datetime.datetime.now() - datetime.timedelta(days=int(v))
            filter_dict['transaction_date__gte'] = start
        elif k in ['tags']:
            filter_dict[k] = v.split(',')  # TODO
        elif k in ['transactions']:
            # TODO: limit to last N transactions
            # this won't go into django filter
            # not sure how best to solve...
            pass
        else:
            print('normalize_filter_kwargs: %s, %s' % (k, v))
            filter_dict[k] = v
    return filter_dict


class TagTable(tables.Table):
    name = tables.Column()
    total_transactions = tables.Column()
    total_amount = tables.Column()
    priority_transactions = tables.Column()
    priority_amount = tables.Column()

    class Meta:
        model = Tag
        attrs = {'class': 'display', 'id': 'tagtable'}
        orderable = False


class MerchantTable(tables.Table):
    id = tables.Column()
    name = tables.Column()
    pattern = tables.Column()
    tags = tables.Column()
    total_transactions = tables.Column()
    total_amount = tables.Column()

    class Meta:
        # html table attributes
        attrs = {'class': 'display', 'id': 'merchanttable'}
        orderable = False  # disable django-table2's sorting links (using datatables in js instead)
        sequence = ('id', 'name', 'tags', 'total_transactions', 'total_amount', 'pattern')


class TransactionTable(tables.Table):
    id = tables.Column()
    account = tables.Column()
    merchant = tables.Column()
    transaction_date = tables.Column()
    amount = tables.Column()
    description = tables.Column()
    statement = tables.Column()
    tags = tables.Column()
    notes = tables.Column()

    class Meta:
        attrs = {'class': 'display', 'id': 'transactiontable'}
        orderable = False
        sequence = ('id', 'transaction_date', 'merchant', 'amount', 'description', 'tags', 'account', 'statement', 'notes')


class StatementTable(tables.Table):
    id = tables.Column()
    account = tables.Column()
    count = tables.Column()
    total = tables.Column()
    end_date = tables.Column()
    # TODO common tags? notes?

    class Meta:
        attrs = {'class': 'display', 'id': 'statementtable'}
        orderable = False
        sequence = ('id', 'account', 'end_date', 'count', 'total')


class AccountTable(tables.Table):
    id = tables.Column()
    name = tables.Column()
    user = tables.Column()
    type = tables.Column()

    class Meta:
        attrs = {'class': 'display', 'id': 'accounttable'}
        orderable = False
        sequence = ('id', 'name', 'user', 'type')
