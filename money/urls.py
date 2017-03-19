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
import accounts.vws
from accounts.views import transactions

urlpatterns = [
    url(r'^api/', include('api.v1.urls')),  # not sure about this
    url(r'^admin/', admin.site.urls),
    url(r'^$', accounts.vws.index, name='index'),
    url(r'^tags$', accounts.vws.tag_list, name='tag-list'),
    url(r'^tags/(?P<tag_id>[0-9]+)$', accounts.vws.tag_detail, name='tag-detail'),
    url(r'^transactions$', transactions.transaction_list, name='transaction-list'),
    url(r'^transactions/(?P<transaction_id>[0-9]+)$', accounts.views.transactions.transaction_detail, name='transaction-detail'),
    url(r'^transactions/untagged$', accounts.views.transactions.transactions_untagged, name='transactions-untagged'),
    url(r'^transactions/unnamed$', transactions.transactions_unnamed, name='transactions-unnamed'),
    url(r'^transactions/compare/(?P<tags>.*)$', accounts.views.transactions.transactions_compare, name='transactions-compare'),
    url(r'^transactions/subdivide/(?P<tags>.*)$', accounts.views.transactions.transactions_subdivide, name='transactions-subdivide'),
    url(r'^merchants$', accounts.vws.merchant_list, name='merchant-list'),
    url(r'^merchants/(?P<merchant_id>[0-9]+)$', accounts.vws.merchant_detail, name='merchant-detail'),
    url(r'^merchants/untagged$', accounts.vws.merchants_untagged, name='merchants-untagged'),
    url(r'^merchants/unnamed$', accounts.vws.merchants_unnamed, name='merchants-unnamed'),
    url(r'^timeseries$', accounts.vws.timeseries, name='timeseries'),
    # url(r'^trends', accounts.vws.trends, name='trends'),
    url(r'^accounts$', accounts.vws.account_list, name='account-list'),
    url(r'^accounts/(?P<account_id>[0-9]+)$', accounts.vws.account_detail, name='account-detail'),
    url(r'^statements$', accounts.vws.statement_list, name='statement-list'),
    url(r'^statements/(?P<statement_id>[0-9]+)$', accounts.vws.statement_detail, name='statement-detail'),

]

# (?P<question_id>[0-9]+)
r'^(?P<question_id>[0-9]+)/vote/$'
