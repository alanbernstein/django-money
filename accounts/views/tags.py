import logging

from django.shortcuts import render
from django.http import HttpResponse
from taggit.models import Tag

from accounts.models import Merchant, TagTable
from accounts.helpers import get_tag_info, get_transactions_by_tag

from panda.debug import debug


logger = logging.getLogger(__name__)


def tag_detail(request, *args, **kwargs):
    # TODO use template
    tag_id = kwargs['tag_id']
    tag = Tag.objects.get(id=tag_id)

    resp = ''
    resp += '<h2>%s</h2>' % tag.name

    resp += '<h3>related tags</h3>'
    resp += '(todo)'

    resp += '<h3>merchants</h3>'
    for merchant in Merchant.objects.filter(tags__id__in=[tag_id]):
        resp += merchant.as_link() + '<br>'

    resp += '<h3>transactions</h3>'
    for t in get_transactions_by_tag(tag):
        resp += t.as_link() + '<br>'

    return HttpResponse(resp)


tag_priority = ['bills', 'grocery', 'meal', 'car', 'bike']


def tag_list_table(request):
    # table columns:
    # - total transactions
    # - total amount
    # - exclusive transactions
    # - exclusive amount

    # 'exclusive' = generating mutually-exclusive categories from unconstrained tags, by using a priority list

    rows = get_tag_info()
    table = TagTable(rows)
    return render(request, 'datatable.html',
                  {'table': table, 'resource': 'tag'})


def tag_list_simple(request):
    resp = ''

    resp += '<h2>all tags</h2>'
    for tag in Tag.objects.all():
        resp += '<a href="tags/%s">%s</a>\n' % (tag.id, tag.name)

    return HttpResponse(resp)


tag_list = tag_list_table
