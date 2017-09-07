#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.http import HttpResponse
from django.shortcuts import render
import urllib.request
from .forms import PostForm
from bs4 import BeautifulSoup
from googleapiclient.discovery import build
import pprint
import json

# Create your views here.
def get_keywords(meta):
	try:
		print(meta["content"])
	except keyError as error:
		pass
	return
def run_script(url):

	return
	
def index(request):	
	return render(request, 'main/index.html', {'page': page, 'form': form})

def check1(request):
	page = 0
	if request.method == 'POST':
		form = PostForm(request.POST)
		if form.is_valid():
			data = form.cleaned_data['do_search']
			#num_results = form.cleaned_data['num_results']
			search_city = form.cleaned_data['search_city']
			search_country = form.cleaned_data['search_country'] 
			page = request.POST.get("page")
			service = build("customsearch", "v1", developerKey="AIzaSyBfsEcEcNt4wtZq7iM5LV2gWfwnSQAD0cA")
			res = service.cse().list( q=data, cx='011980423541542895616:ug0kbjbf6vm', gl=search_country, hq="near=%s" % search_city, cr=search_country, hl=search_country, filter="1", ).execute()
			total = res["searchInformation"]["totalResults"]
			#pprint.pprint(res)
			all_links = []
			n_total = []
			all_metas = []
			for item in res["items"]:
				all_links.append(item["link"])              
	
			#for x in xrange(1, 10):
			#   n_total.append(x)
			#   res2 = service.cse().list( q=data, cx='011980423541542895616:ug0kbjbf6vm', gl='us', start=(x*10)+1, ).execute()
			#   for item in res2["items"]:
			#       all_links.append(item["link"])
			keywords = []
			for link in all_links:
				metas = []

				try:
					html_doc = urllib.request.urlopen(link)
					soup = BeautifulSoup(html_doc, 'html.parser')                   
					for met in soup.findAll(attrs={"name":"keywords"}):
						#get_keywords(met)
						try:
							contenido = met["content"]
							content_list = contenido.split(",")
							for key in content_list:
								keywords.append(key)
						except keyError:
							pass
						metas.append(met.encode("utf-8"))


					all_metas.append({"link": link , "meta": metas})
				except urllib.request.HTTPError as error:
					all_metas.append({"link": link , "meta": "Forbidden %s" % error.code})
					#print "Forbidden %s" %(error.code)
			#pprint.pprint(all_metas)
			return render(request, 'main/check1.html', {'page': page, 'data': keywords})
	else:
		form = PostForm()
		return render(request, 'main/index.html', { 'form': form})
	return render(request, 'main/check1.html', {})
	