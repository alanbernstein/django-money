import re
from collections import Counter
from django.core.management.base import BaseCommand
from django.db.models import Sum
from taggit.models import Tag
from accounts.base import get_account
from accounts.models import Transaction, Merchant

from panda.debug import pp, debug, pm


class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument('--account', '-a', default='', help='specify account to use')

        parser.add_argument('--deduplicate', action='store_true', default=False, help='deduplicate merchants by name')
        parser.add_argument('--combine', default='', help='combine multiple merchants by id')
        parser.add_argument('--describe', '-d', nargs='*', default=None, help='describe merchants by tags tags supplied in list')

    def handle(self, *args, **options):
        account = get_account(options['account'])

        if options['deduplicate']:
            deduplicate_merchants_by_name()
        if options['combine']:
            combine_merchants_by_id()
        if options['describe'] is not None:
            describe_tags(account, options['describe'])


def describe_tags(account, taglist):
    if taglist:
        merchants = Merchant.objects.filter(tags__name__in=taglist)

        filters = {}
        if account:
            filters = {'account_id': account.id}

        print('%d merchants in tag list: %s' % (len(merchants), taglist))
        for m in merchants:
            filters.update({'merchant_id': m.id})
            tx0 = Transaction.objects.filter(**filters)
            if tx0:
                total = tx0.aggregate(Sum('debit_amount')).values()[0]
                print('%40s  $%9.2f  %d' % (m.name, total, len(tx0)))
            else:
                # TODO: figure this out
                print('%40s  ?' % m.name)
                debug()

    tags = Tag.objects.all()
    tagnames = [tag.name for tag in tags]
    print('all tags:')
    print(', '.join(tagnames))


def deduplicate_merchants_by_name():
    all_merchants = Merchant.objects.all()
    name_list = [m.name.lower() for m in all_merchants]
    name_counter = Counter(name_list)
    duplicates = {k: v for k, v in name_counter.items() if v > 1}

    if duplicates:
        print('%d duplicate sets...' % len(duplicates))
        for lower_name, count in duplicates.items():
            merchants = Merchant.objects.filter(name__iexact=lower_name)
            print(merchants)

            for merchant in merchants[1:]:
                combine_merchants_by_id(merchants[0].id, merchant.id)


@pm
def combine_merchants_by_id(winner_id, loser_id):
    # add tags from loser to winner
    # add patterns from loser to winner
    # move transactions from loser to winner

    winner = Merchant.objects.get(id=winner_id)
    loser = Merchant.objects.get(id=loser_id)

    winner_tx = Transaction.objects.filter(merchant__id=winner_id)
    loser_tx = Transaction.objects.filter(merchant__id=loser_id)
    winner_total = sum([t.debit_amount for t in winner_tx])
    loser_total = sum([t.debit_amount for t in loser_tx])

    print('winner:')
    print(' pattern: %s' % winner.pattern.pattern)
    print(' tags: %s' % winner.tags.all())
    print(' %d transactions, $%.2f' % (winner_tx.count(), winner_total))

    print('loser:')
    print(' pattern: %s' % loser.pattern.pattern)
    print(' tags: %s' % loser.tags.all())
    print(' %d transactions, $%.2f' % (loser_tx.count(), loser_total))

    print('its time to test this!')
    debug()

    # not tested yet
    winner.tags.add(loser.tags.all())
    winner.pattern += '|' + loser.pattern
    #winner.save()

    for t in loser_tx:
        t.merchant = winner
        #t.save()
