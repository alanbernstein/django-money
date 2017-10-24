import json
import time
import datetime

from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from django.views.generic import ListView
from django.views.generic.base import TemplateView
from taggit.models import Tag
from django.db import connection
from django.db.models import Sum, Count

from accounts.models import Transaction
from accounts.helpers import get_tag_info, get_transactions_by_tag

import plotly.plotly as py
import plotly.graph_objs as go
import plotly.offline as opy

from panda.debug import debug


class PlotView(TemplateView):
    template_name = 'plot.html'

    def get(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        return self.render_to_response(context)

    def get_context_data(self, **kwargs):
        context = super(PlotView, self).get_context_data(**kwargs)

        fig = self.get_graph()
        div = opy.plot(fig, auto_open=False, output_type='div')
        context['title'] = 'budget plots'
        context['graph'] = div

        return context

    def get_graph(self):
        traces = [go.Scatter(
            x=[1, 2, 3],
            y=[2, 5, 3],
        )]
        layout = {}

        return go.Figure(data=traces, layout=layout)


def overview(request, *args, **kwargs):
    # TODO: start, end, period
    tdate = connection.ops.date_trunc_sql('month', 'transaction_date')
    qs = Transaction.objects.extra({'day': tdate})
    rows = qs.values('day').annotate(
        amount=Sum('debit_amount'), count=Count('pk')
    ).order_by('day')
    data = {
        'day': [r['day'] for r in rows],
        'count': [int(r['count']) for r in rows],
        'amount': [float(r['amount']) for r in rows],
    }
    return JsonResponse(data)


def compare(request, *args, **kwargs):
    # TODO: start, end, period
    # TODO: use merchant tags as well
    # TODO: ignore transactions with 'payment' tag
    end = datetime.datetime.today()
    start = end - datetime.timedelta(days=180)
    period = 'month'

    taglist = kwargs['tags'].split('+')
    r = ''
    r += 'args: %s<br>' % (args,)
    r += 'kwargs: %s <br>' % (kwargs,)
    r += 'tags: %s <br>' % (', '.join(taglist))

    data = {}
    for tag in taglist:
        tdate = connection.ops.date_trunc_sql('month', 'transaction_date')
        qs = Transaction.objects.filter(tags__name__in=[tag]).extra({'month': tdate})
        rows = qs.values('month').annotate(amount=Sum('debit_amount'), count=Count('pk')).order_by('month')

        # TODO can django do this?
        data[tag] = {
            'day': [r['day'] for r in rows],
            'count': [int(r['count']) for r in rows],
            'amount': [float(r['amount']) for r in rows],
        }

    return JsonResponse(data)


def segment_by_tag(tag_priority=None):
    # generates a dict of lists of mutually exclusive transaction ids
    # this is a "category" action, but we only have tags, so
    # use tags to try to do it

    t0 = time.time()
    tag_info = get_tag_info()
    if tag_priority == 'total':
        tag_info.sort(key='total_amount', reverse=True)

    elif tag_priority == 'count':
        tag_info.sort(key='total_transactions', reverse=True)

    elif hasattr(tag_priority, '__iter__'):
        # not well-defined?
        pass

    all_tx_ids = set([t.id for t in Transaction.objects.all()])
    priority_ids = [t['id'] for t in tag_info]

    segments = {}
    for idx in priority_ids:
        tag = Tag.objects.get(id=idx)
        txtag_ids = set([t.id for t in get_transactions_by_tag(tag)])

        # add unseen transactions to this segment
        segments[idx] = txtag_ids.intersection(all_tx_ids)
        # these tags are now seen, remove from full list
        all_tx_ids = all_tx_ids.difference(txtag_ids)

    print('%f sec' % (time.time() - t0))
    return segments
