# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models

# Create your models here.

class Search(models.Model):
	site_name = models.CharField(unique=True, max_length=300)
	site_url = models.CharField(max_length=2000)
	site_weight = models.CharField(max_length=10, blank=True, null=True)
	site_status = models.CharField(max_length=200, blank=True, null=True)


