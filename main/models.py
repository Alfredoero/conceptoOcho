# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models
import datetime

# Create your models here.

class Search(models.Model):
	site_name = models.CharField(max_length=300)
	site_url = models.CharField(max_length=2000)
	site_weight = models.CharField(max_length=10, blank=True, null=True)
	site_status = models.CharField(max_length=200, blank=True, null=True)

	def __str__(self):
		return self.site_name


class Phone(models.Model):
	phone = models.CharField(max_length=20)

	def __str__(self):
		return self.phone


class Keyword(models.Model):
	keyword = models.CharField(max_length=300)

	def __str__(self):
		return self.keyword


class InfoSearch(models.Model):
	site_name = models.CharField(max_length=300, blank=True, null=True)
	site_url = models.CharField(max_length=2000, unique=True)
	site_phones = models.ManyToManyField(Phone, blank=True)
	site_keywords = models.ManyToManyField(Keyword, blank=True)
	site_email = models.CharField(max_length=300, blank=True, null=True)
	site_address = models.CharField(max_length=500, blank=True, null=True)
	site_contact_url = models.CharField(max_length=2000, blank=True, null=True)
	related_search = models.CharField(max_length=500, blank=True, null=True)
	search_date = models.DateField(auto_now_add=True, blank=True)
	average_ranking = models.CharField(max_length=10, blank=True, null=True)
	top_ranking = models.CharField(max_length=5, blank=True, null=True)
	search_nums = models.CharField(max_length=5, blank=True, null=True)
	click_cost = models.DecimalField(decimal_places=2, max_digits=10, blank=True, null=True)
	click_aditional = models.DecimalField(decimal_places=2, max_digits=10, blank=True, null=True)

	def __str__(self):
		return self.site_name


class InfoYellow(models.Model):
	site_name = models.CharField(max_length=300, unique=True)
	site_url = models.CharField(max_length=2000, blank=True, null=True)
	site_phone = models.ManyToManyField(Phone, blank=True)
	site_email = models.CharField(max_length=300, blank=True, null=True)
	site_address = models.CharField(max_length=500, blank=True, null=True)
	related_search = models.CharField(max_length=500, blank=True, null=True)
	search_date = models.DateField(auto_now_add=True, blank=True)

	def __str__(self):
		return self.site_name
