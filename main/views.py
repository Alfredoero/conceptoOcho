#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.http import HttpResponse
from django.shortcuts import render
import urllib2
from .forms import PostForm
from bs4 import BeautifulSoup
from googleapiclient.discovery import build
import pprint
import json

# Create your views here.
def run_script(url):

	return
	
def index(request):
	if request.method == 'POST':
		form = PostForm(request.POST)
		if form.is_valid():
			data = form.cleaned_data['do_search']
			page = request.POST.get("page")
			print page
			service = build("customsearch", "v1", developerKey="AIzaSyBfsEcEcNt4wtZq7iM5LV2gWfwnSQAD0cA")
		  	res = service.cse().list( q=data, cx='011980423541542895616:ug0kbjbf6vm', gl='us', ).execute()
		  	total = res["searchInformation"]["totalResults"]
		  	all_links = []
		  	n_total = []
		  	all_metas = []
		  	for item in res["items"]:
		  		all_links.append(item["link"])		  		
	
		  	#for x in xrange(1, 10):
		  	#	n_total.append(x)
		  	#	res2 = service.cse().list( q=data, cx='011980423541542895616:ug0kbjbf6vm', gl='us', start=(x*10)+1, ).execute()
		  	#	for item in res2["items"]:
		  	#		all_links.append(item["link"])

		  	for link in all_links:
		  		metas = []
		  		try:
			  		html_doc = urllib2.urlopen(link)
			  		soup = BeautifulSoup(html_doc, 'html.parser')			  		
			  		for met in soup.findAll(attrs={"name":"keywords"}):
			  			print met
			  			metas.append(met.encode("utf-8"))
			  		all_metas.append({"link": link , "meta": metas})
			  	except urllib2.HTTPError as error:
			  		all_metas.append({"link": link , "meta": "Forbidden %s" % error.code})
			  		print "Forbidden %s" %(error.code)
			pprint.pprint(all_metas)
			return render(request, 'main/index.html', {'page': page, 'data': all_metas, 'form': form})
	else:
		page = 0
		form = PostForm()
	return render(request, 'main/index.html', {'page': page, 'form': form})
	