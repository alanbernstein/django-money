import datetime
from collections import defaultdict
from django.shortcuts import render_to_response
from django.views.generic import TemplateView

import plotly.graph_objs as go
import plotly.offline as opy

from accounts.models import Transaction
from accounts.helpers import get_transactions_by_month, get_nth_month
from plot_tools import get_layout


def index_func(request):
    return render_to_response('index.html')


class IndexView(TemplateView):
    template_name = "index.html"
    plot_args = dict(
        auto_open=False,
        output_type='div',
        show_link=False,
        config={'displayModeBar': False}
    )

    def get(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        return self.render_to_response(context)

    def get_context_data(self, **kwargs):
        context = super(IndexView, self).get_context_data(**kwargs)
        context['overview_graph'] = self.get_overview_graph(months=24)
        context['second_graph'] = self.get_second_graph(months=24)
        return context

    def _get_transactions_by_month(self, months):
        # return a dict of {datetime: queryset}
        # where each KV pair represents a single month
        month_groups = {}
        for n in range(months):
            date = get_nth_month(n)
            month_groups[date] = get_transactions_by_month(date)

        return month_groups

    def _get_transactions_by_month_old(self, days):
        # get all in time window
        newest = datetime.datetime.now()
        oldest = newest - datetime.timedelta(days=days)
        oldest_round = datetime.datetime(oldest.year, oldest.month, 1)  # ensure full month
        tt = Transaction.objects.filter(
            transaction_date__gt=oldest_round,
            transaction_date__lt=newest,
            debit_amount__gt=0,
        ).order_by('transaction_date')

        # TODO make the values querysets, not lists, so can still use ORM
        # group by month
        month_groups = defaultdict(list)
        for t in tt:
            month = datetime.datetime(t.transaction_date.year, t.transaction_date.month, 1)
            month_groups[month].append(t)

        return month_groups

    def _get_figure(self, data, layout, **kwargs):
        fig = go.Figure(data=data, layout=layout)
        return opy.plot(fig, **kwargs)

    def get_overview_graph_new(self, months):
        pass

    def get_overview_graph(self, months):
        month_groups = self._get_transactions_by_month(months)

        # compute total spent for each month
        # compute total spent on each tag, exclusively, for each month
        months = month_groups.keys()
        months.sort()
        x, y_total = [], []
        tag_names = ['travel', 'grocery', 'meal', 'car', 'bike']
        y_tags = {t: [] for t in tag_names}
        for month in months:
            x.append(month)
            tx = month_groups[month]
            total = 0
            y_tag_totals = {t: 0 for t in tag_names}
            for t in tx:
                total += t.debit_amount
                tags = t.get_tags_as_strings()
                for tag in y_tags:
                    if tag in tags:
                        y_tag_totals[tag] += t.debit_amount
                        # only add the first one
                        break

            y_total.append(total)
            for tag in tag_names:
                y_tags[tag].append(y_tag_totals[tag])

        traces = [
            go.Scatter(x=x, y=y_total, name='total'),
        ]
        for tag_name, y in y_tags.items():
            traces.append(go.Scatter(x=x, y=y, name=tag_name))

        layout = get_layout(title='CC purchases: amount')
        return self._get_figure(traces, layout, **self.plot_args)

    def get_second_graph(self, months):
        month_groups = self._get_transactions_by_month(months)

        months = month_groups.keys()
        months.sort()
        x, y = [], []
        for month in months:
            x.append(month)
            y.append(len(month_groups[month]))

        traces = [
            go.Scatter(x=x, y=y, name='total purchases'),
        ]

        layout = get_layout(title='CC purchases: count')
        return self._get_figure(traces, layout, **self.plot_args)


index = IndexView.as_view()
