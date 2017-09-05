#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.http import HttpResponse
from django.shortcuts import render
import urllib2
from .forms import PostForm
from bs4 import BeautifulSoup
from googleapiclient.discovery import build

# Create your views here.
def run_script(url):

	return
	
def index(request):
	if request.method == 'POST':
		form = PostForm(request.POST)
		if form.is_valid():
			data = form.cleaned_data['do_search']
			service = build("customsearch", "v1", developerKey="AIzaSyBfsEcEcNt4wtZq7iM5LV2gWfwnSQAD0cA")
		  	res = service.cse().list( q=data, cx='011980423541542895616:ug0kbjbf6vm', gl='us',).execute()
						
			return render(request, 'main/index.html', {'data': res, 'form': form})
	else:
		form = PostForm()
	return render(request, 'main/index.html', {'form': form})
	