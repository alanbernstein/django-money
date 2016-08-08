import sys
import re
import subprocess
import glob
import os
from datetime import datetime as dt
from optparse import make_option

from django.core.management.base import BaseCommand, CommandError

from money.accounts.models import Account, Statement, Transaction, Merchant

from panda.progressbar import ProgressBar
from panda.debug import pp, debug
from panda.debug import annotate_time_indent as annotate


    

class Command(BaseCommand):
    help="todo"

    def add_arguments(self, parser):
        parser.add_argument('file_glob', nargs='+', type=str)


    def handle(self, *args, **options):
        """todo"""

        
