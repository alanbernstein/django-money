from django.contrib import admin
from .models import Transaction, Account, Statement, Merchant

# Register your models here.

admin.site.register(Transaction)
admin.site.register(Account)
admin.site.register(Statement)
admin.site.register(Merchant)
