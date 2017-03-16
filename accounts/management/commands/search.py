from django.core.management.base import BaseCommand
from accounts.search import print_search_results


class Command(BaseCommand):
    """
    quick search over everything
    search keyword     # search all tags+merchants+transactions by keyword
    search -m keyword  # search only merchants by keyword
    search -t keyword  # search only tags by keyword
    search -T keyword  # search only transactions by keyword
    """

    def add_arguments(self, parser):
        parser.add_argument('keyword', help='search for keyword. if -t, -m -T are not supplied, search over all three')  # positional argument, without flag
        parser.add_argument('--tags', '-T', action='store_true', default=False,
                            help='search tags')
        parser.add_argument('--merchants', '-m', action='store_true', default=False,
                            help='search merchants')
        parser.add_argument('--transactions', '-t', action='store_true', default=False,
                            help='search transactions')

    def handle(self, *args, **options):
        if not options['tags'] and not options['merchants'] and not options['transactions']:
            options['tags'] = True
            options['merchants'] = True
            options['transactions'] = True

        print_search_results(options['keyword'],
                             tags=options['tags'],
                             merchants=options['merchants'],
                             transactions=options['transactions'])
