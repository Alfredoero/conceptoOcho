# -*- coding: utf-8 -*-
# Generated by Django 1.11.5 on 2017-12-27 20:15
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0009_auto_20171009_0602'),
    ]

    operations = [
        migrations.AddField(
            model_name='infosearch',
            name='related_search',
            field=models.CharField(blank=True, max_length=500, null=True),
        ),
        migrations.AddField(
            model_name='infoyellow',
            name='related_search',
            field=models.CharField(blank=True, max_length=500, null=True),
        ),
    ]
