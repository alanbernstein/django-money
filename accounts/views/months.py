import logging

from django.shortcuts import render
from django.http import HttpResponse
from django.views.generic import ListView
from taggit.models import Tag

from accounts.models import Merchant, TagTable
from accounts.helpers import get_tag_info, get_transactions_by_tag

from panda.debug import debug



def month_detail(request, *args, **kwargs):
    resp = []
    return HttpResponse(resp)


def month_list_simple(request):
    resp = []
    return HttpResponse(resp)


month_list = month_list_simple
