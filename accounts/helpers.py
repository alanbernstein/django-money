from django.db.models import Sum, Count, Q
from django.utils.html import format_html
from accounts.models import (Account,
                             Statement,
                             Transaction,
                             Merchant,
                             User,
                             Tag,
                             TagTable,
                             MerchantTable,
                             TransactionTable,
                             AccountTable,
                             StatementTable,
                             )

def get_transaction_info(tx=None):
    """
    input tx should be a list of transactions or transaction ids
    """

    if not hasattr(tx, '__iter__'):
        # convert single instance to list
        tx = [tx]

    if isinstance(tx[0], int):
        # get transactions from ids
        ids = tx
        tx = Transaction.objects.filter(id__in=ids)

    rows = []
    for t in tx:
        row = {}
        row['id'] = t.as_link(self_link=True)
        if t.merchant:
            row['merchant'] = t.merchant.as_link()
        row['transaction_date'] = t.transaction_date
        row['amount'] = t.debit_amount
        row['description'] = t.description
        row['account'] = t.account.as_link()
        row['statement'] = t.statement.as_link()
        row['tags'] = t.get_tags_as_links()

        rows.append(row)

    return rows


def get_merchant_info(merchants=None):
    """
    input merchants should be a list of merchants or merchant ids
    """

    if not hasattr(merchants, '__iter__'):
        # convert single instance to list
        merchants = [merchants]

    if isinstance(merchants[0], int):
        # get transactions from ids
        ids = merchants
        merchants = Merchant.objects.filter(id__in=ids)

    rows = []
    for m in merchants:
        m_tx = Transaction.objects.filter(merchant_id=m.id)
        row = {}
        row['id'] = m.id
        row['name'] = m.as_link()
        row['pattern'] = m.pattern.pattern
        row['tags'] = m.get_tags_as_links()
        row['total_transactions'] = m_tx.count()
        key = 'debit_amount'
        total = m_tx.aggregate(Sum(key))[key + '__sum']
        total = total or 0
        row['total_amount'] = float(total)
        rows.append(row)

    return rows


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


def get_statement_info(statements=None):
    if not hasattr(statements, '__iter__'):
        # convert single instance to list
        statements = [statements]

    if isinstance(statements[0], int):
        # get transactions from ids
        ids = statements
        statements = Statement.objects.filter(id__in=ids)

    rows = []
    for s in statements:
        row = {}
        row['id'] = s.as_link(self_link=True)
        row['account'] = s.account
        row['end_date'] = s.end_date
        row['count'] = s.get_count()
        row['total'] = s.get_total()
        rows.append(row)

    return rows


def get_transactions_by_tag(tag, merchants=True):
    tag_merchants = Merchant.objects.filter(tags__name__in=[tag.name])
    merchant_ids = [m.id for m in tag_merchants]

    tag_tx = Transaction.objects.filter(Q(tags__name__in=[tag.name]) | Q(merchant_id__in=merchant_ids))

    return tag_tx


def get_tag_info():
    # return Tag.objects.all()

    rows = []
    tags = Tag.objects.all()

    for tag in tags:
        row = {}
        row['id'] = tag.id
        row['name'] = format_html('<a href="tags/%s">%s</a>' % (tag.id, tag.name))
        tag_tx = get_transactions_by_tag(tag)
        row['total_transactions'] = len(tag_tx)
        row['total_amount'] = sum([t.debit_amount for t in tag_tx])
        rows.append(row)

    return rows
