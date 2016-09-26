import datetime
from accounts.models import Transaction
from accounts.views import get_compare_data
from test_accounts import AccountTest


class TimeseriesTest(AccountTest):
    def setUp(self):
        super(TimeseriesTest, self).setUp()
        self.num_transactions = 10
        for n in range(1, self.num_transactions+1):
            d1 = datetime.date(2016, 1 + int(n * .6), 1)
            d2 = datetime.date(2016, 3 + int(n * .4), 1)
            Transaction.objects.create(debit_amount=n, transaction_date=d1,
                                       merchant=self.m1, account=self.a1)
            Transaction.objects.create(debit_amount=n * 2, transaction_date=d2,
                                       merchant=self.m2, account=self.a1)

    def test_compare_data(self):
        kwargs = {'merchants': ['m1', 'm2']}
        data = get_compare_data(**kwargs)

        self.assertEqual(data.keys(), ['x', 'm1', 'm2'])
        self.assertEqual(len(data['m1']), 7)
