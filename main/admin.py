# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin
from main.models import Search
# Register your models here.

class SearchAdmin(admin.ModelAdmin):
    list_display = ('site_title')

admin.site.register(Search, SearchAdmin)
