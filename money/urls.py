"""money URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.9/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import url, include
from django.contrib import admin
import accounts.views

urlpatterns = [
    url(r'^api/', include('api.urls')),  # not sure about this
    url(r'^admin/', admin.site.urls),
    url(r'^$', accounts.views.index, name='index'),
    url(r'^tags$', accounts.views.tag_list, name='tag-list'),
    url(r'^tags/(?P<tag_id>[0-9]+)$', accounts.views.tag_detail, name='tag-detail'),
    url(r'^transactions$', accounts.views.transaction_list, name='transaction-list'),
    url(r'^transactions/(?P<transaction_id>[0-9]+)$', accounts.views.transaction_detail, name='transaction-detail'),
    url(r'^transactions/untagged$', accounts.views.transactions_untagged, name='transactions-untagged'),
    url(r'^transactions/unnamed$', accounts.views.merchants_unnamed, name='transactions-unnamed'),
    url(r'^transactions/compare/(?P<tags>.*)$', accounts.views.transactions_compare, name='transactions-compare'),
    url(r'^transactions/subdivide/(?P<tags>.*)$', accounts.views.transactions_subdivide, name='transactions-subdivide'),
    url(r'^merchants$', accounts.views.merchant_list, name='merchant-list'),
    url(r'^merchants/(?P<merchant_id>[0-9]+)$', accounts.views.merchant_detail, name='merchant-detail'),
    url(r'^merchants/untagged$', accounts.views.merchants_untagged, name='merchants-untagged'),
    url(r'^merchants/unnamed$', accounts.views.merchants_unnamed, name='merchants-unnamed'),
    url(r'^timeseries$', accounts.views.timeseries, name='timeseries'),
    # url(r'^trends', accounts.views.trends, name='trends'),
    url(r'^accounts$', accounts.views.account_list, name='account-list'),
    url(r'^accounts/(?P<account_id>[0-9]+)$', accounts.views.account_detail, name='account-detail'),
    url(r'^statements$', accounts.views.statement_list, name='statement-list'),
    url(r'^statements/(?P<statement_id>[0-9]+)$', accounts.views.statement_detail, name='statement-detail'),

]

# (?P<question_id>[0-9]+)
r'^(?P<question_id>[0-9]+)/vote/$'
