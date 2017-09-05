# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models

# Create your models here.

class Search(models.Model):
	site_name = models.CharField(max_length=300)
	site_url = models.CharField(max_length=2000)



