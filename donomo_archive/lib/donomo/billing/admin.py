#!/usr/bin/env python
# -*- coding: utf-8 -*-
from django.contrib import admin

from donomo.billing.models import *

class InvoiceAdmin(admin.ModelAdmin):
    list_display = ("owner",)
admin.site.register(Invoice, InvoiceAdmin)

class AccountAdmin(admin.ModelAdmin):
    list_display = ("user", "balance",)
admin.site.register(Account, AccountAdmin)
