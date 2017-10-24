from __future__ import unicode_literals

import os
from datetime import datetime

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
    name = models.CharField(max_length=300)
    user = models.ForeignKey(User)
    slug = models.SlugField()
    CHECKING, CREDIT, SAVING, INVESTMENT, BILL = range(5)
    ACCOUNT_TYPES = ((CHECKING, 'checking'), (CREDIT, 'credit'), (SAVING, 'saving'), (INVESTMENT, 'investment'))
    type = models.SmallIntegerField(choices=ACCOUNT_TYPES)
    statements_directory = models.CharField(max_length=300)

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

    def save(self, *args, **kwargs):
        # set derived stuff if new
        if not self.id:
            self.slug = slugify('%s %s' % (self.user, self.name))
            self.statements_directory = statement_root + self.slug + os.path.sep

        super(Account, self).save(*args, **kwargs)

    def __str__(self):
        return "%s's %s" % (self.user.name, self.name)


class Location(models.Model):
    pass


class Merchant(models.Model):
    name = models.CharField(max_length=300)
    pattern = RegexField(max_length=1000)
    tags = TaggableManager()

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

    def __str__(self):
        m = self.name
        tags = self.tags.all()
        # debug()
        if tags:
            tagnames = [t.name for t in tags]
            m = '%s (%s)' % (m, ', '.join(tagnames))
        return m


class Statement(models.Model):
    account = models.ForeignKey(Account)
    statement_date = models.DateField(null=True, blank=True)
    due_date = models.DateField(null=True, blank=True)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    file_path = models.CharField(max_length=300, null=True, blank=True)
    file_name = models.CharField(max_length=50, null=True, blank=True)
    file_hash = models.CharField(max_length=32, null=True, blank=True)
    downloaded = models.BooleanField(default=False)
    parsed = models.BooleanField(default=False)  # TODO: change this to 'parsed'

    def get_filename(self):
        return '%s/%s' % (self.file_path, self.file_name)

    def as_link(self, self_link=False):
        if self_link:
            return format_html('<a href="/statements/%s">%s</a>' % (self.id, self.id))
        else:
            return format_html('<a href="/statements/%s">%s</a>' % (self.id, self.end_date))

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

    def __str__(self):
        if self.end_date:
            return '%s ending %s' % (self.account.name,
                                     datetime.strftime(self.end_date, '%Y-%m-%d'))
        else:
            return '%s - unparsed' % self.file_name

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
    description = models.CharField(max_length=300, null=True, blank=True)
    notes = models.TextField(null=True, blank=True)
    tags = TaggableManager()
    # all_tags = TaggableManager()
    # location - figure out a good way to do that

    # not sure if this should be an enum, or just a string...
    TRANSACTION_TYPES = ()
    SALE = 0
    type = models.SmallIntegerField(choices=TRANSACTION_TYPES, default=SALE)

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

    class Meta:
        attrs = {'class': 'display', 'id': 'transactiontable'}
        orderable = False
        sequence = ('id', 'transaction_date', 'merchant', 'amount', 'description', 'tags', 'account', 'statement')


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
