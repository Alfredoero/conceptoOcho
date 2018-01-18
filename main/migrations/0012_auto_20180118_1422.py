# -*- coding: utf-8 -*-
# Generated by Django 1.11.5 on 2018-01-18 14:22
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0011_infosearch_average_ranking'),
    ]

    operations = [
        migrations.AddField(
            model_name='infosearch',
            name='click_aditional',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True),
        ),
        migrations.AddField(
            model_name='infosearch',
            name='click_cost',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True),
        ),
        migrations.AddField(
            model_name='infosearch',
            name='top_ranking',
            field=models.CharField(blank=True, max_length=5, null=True),
        ),
    ]