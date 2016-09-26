import datetime
from django.test import TestCase
from accounts.models import Transaction, Merchant, Account, User


class AccountTest(TestCase):
    def setUp(self):
        """bare minimum necessary to create transactions"""
        self.user = User.objects.create()
        self.a1 = Account.objects.create(type=Account.CHECKING, user=self.user)
        self.m1 = Merchant.objects.create(name='m1')
        self.m2 = Merchant.objects.create(name='m2')
        Transaction.objects.create(debit_amount=1, transaction_date=datetime.datetime.today(),
                                   merchant=self.m1, account=self.a1)
