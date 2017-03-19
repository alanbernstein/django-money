from django.shortcuts import render_to_response
from django.views.generic import TemplateView


def index_func(request):
    return render_to_response('index.html')


class IndexView(TemplateView):
    template_name = "index.html"


index = IndexView.as_view()
