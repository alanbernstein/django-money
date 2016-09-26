import json
# import matplotlib.pyplot as plt
from django.core.management.base import BaseCommand
from accounts.base import get_account
from accounts.views import get_compare_data

from panda.debug import pp, debug, pm, jprint


class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument('--account', '-a', default='', help='specify account to use')
        parser.add_argument('--tags', '-t', default='', help='tags')
        parser.add_argument('--merchants', '-m', default='', help='merchants')

    def handle(self, *args, **options):
        if options['account']:
            account = get_account(options['account'])

        # get inputs
        if options['merchants']:
            merchants = [x.strip() for x in options['merchants'].split(',')]
            data = get_compare_data(merchants=merchants)
        if options['tags']:
            tags = [x.strip() for x in options['tags'].split(',')]
            data = get_compare_data(tags=tags)

        print(json.dumps(data))

        """
        # collate and print
        keys = data.keys()
        header = ', '.join(keys)
        print(header)
        for n in range(len(data[keys[0]])):
            m = []
            for key in keys:
                m.append(str(data[key][n]))
            print(', '.join(m))
        """
