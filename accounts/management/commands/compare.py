import re
import os
from collections import Counter
import datetime
from itertools import groupby
import matplotlib.pyplot as plt
from django.core.management.base import BaseCommand
from django.db.models import Sum
from taggit.models import Tag
from accounts.models import Transaction, Merchant
from accounts.base import get_account
from accounts.views import get_compare_data

from panda.debug import pp, debug, pm, jprint


class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument('--account', '-a', default='', help='specify account to use')
        parser.add_argument('--tags', '-t', default='', help='tags')

    def handle(self, *args, **options):

        if options['account']:
            account = get_account(options['account'])

        tags = options['tags']
        data = get_compare_data(tags)
        print('%s, %s, %s' % ('x', 'y1', 'y2'))
        for row in zip(data['x'], data['y1'], data['y2']):
            print('%s, %s, %s' % row)
        plot_compare_data(data)


def plot_compare_data(data):
    plt.plot(data['x'], data['y1'], 'r')
    plt.plot(data['x'], data['y2'], 'b')
    plt.show()
    pass


def get_compare_data(tags):
    data = {'x': [0, 1, 2],
            'y1': [0, 1, 4],
            'y2': [0, 1, 2],
            }
    return  data
