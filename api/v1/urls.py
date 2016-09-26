from django.conf.urls import url
from django.contrib import admin
import accounts.views
import api.views

urlpatterns = [
    url(r'^trends$', api.views.trends, name='trends'),
]
