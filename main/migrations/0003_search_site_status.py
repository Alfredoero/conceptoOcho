# -*- coding: utf-8 -*-
# Generated by Django 1.11.5 on 2017-09-08 00:09
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0002_search_site_weight'),
    ]

    operations = [
        migrations.AddField(
            model_name='search',
            name='site_status',
            field=models.CharField(blank=True, max_length=200, null=True),
        ),
    ]
