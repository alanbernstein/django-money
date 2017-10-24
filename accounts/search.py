from taggit.models import Tag
from accounts.models import Transaction, Merchant


def search_merchants(s):
    return Merchant.objects.filter(name__icontains=s)


def search_transactions(s):
    return Transaction.objects.filter(description__icontains=s)


def search_notes(s):
    return Tag.objects.filter(notes__icontains=s)


def search_tags(s):
    return Tag.objects.filter(name__icontains=s)


def print_search_results(keyword, tags=True, merchants=True, transactions=True, notes=True):
    first = True

    if tags:
        tag_output = search_tags(keyword)
        if tag_output:

            if not first:
                print('')
            first = False

            print('tags:')
            for t in tag_output:
                print('%d. %s' % (t.id, t.name))

    if merchants:
        merchant_output = search_merchants(keyword)
        if merchant_output:

            if not first:
                print('')
            first = False

            print('merchants:')
            for m in merchant_output:
                print('%d. %s - %s' % (m.id, m.name, m.pattern.pattern))

    if transactions:
        tx_output = search_transactions(keyword)
        if tx_output:

            if not first:
                print('')
            first = False

            print('transactions:')
            for t in tx_output:
                mid = ''
                if t.merchant:
                    mid = t.merchant.id
                print('%d. %s (%s %s) - %s' % (t.id, t.description,
                                               t.transaction_date, t.debit_amount, mid))

    if notes:
        notes_output = search_notes(keyword)
        if notes_output:

            if not first:
                print('')
            first = False

            print('notes:')
            for t in notes_output:
                print('%d. %s (%s %s) - %s' % (t.id, t.description,
                                               t.transaction_date, t.debit_amount, t.notes))

    if first:
        print('no results!')
