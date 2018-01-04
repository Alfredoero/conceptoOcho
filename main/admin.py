# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin
from main.models import Search, Phone, Keyword, InfoSearch, InfoYellow
# Register your models here.


class SearchAdmin(admin.ModelAdmin):
    list_display = ('site_name', 'site_url', 'site_weight')


class PhoneAdmin(admin.ModelAdmin):
    list_display = ('phone',)


class KeywordAdmin(admin.ModelAdmin):
    list_display = ('keyword', )


class InfoSearchAdmin(admin.ModelAdmin):
    list_display = ('site_name', 'site_url', 'site_email', 'site_address', 'search_date', 'related_search', 'average_ranking')


class InfoYellowAdmin(admin.ModelAdmin):
    list_display = ('site_name', 'site_url', 'site_email', 'site_address', 'search_date', 'related_search')

admin.site.register(Search, SearchAdmin)
admin.site.register(Phone, PhoneAdmin)
admin.site.register(Keyword, KeywordAdmin)
admin.site.register(InfoSearch, InfoSearchAdmin)
admin.site.register(InfoYellow, InfoYellowAdmin)
