#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.http import HttpResponse
from django.shortcuts import render
import urllib.request
from .forms import PostForm
from .models import Search
from bs4 import BeautifulSoup
from googleapiclient.discovery import build
import pprint
import json
import re

# Create your views here.

def run_script(url):

	return
	
def index(request):	
	form = PostForm()
	return render(request, 'main/index.html', {'form': form})

def check(request):
	page = 0
	if request.method == 'POST':
		form = PostForm(request.POST)
		if form.is_valid():
			keywords = []
			data = form.cleaned_data['do_search']			
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

				metas = []
				try:
					html_doc = urllib.request.urlopen(item["link"])
					soup = BeautifulSoup(html_doc, 'html.parser')
					for met in soup.findAll(attrs={"name":"keywords"}):
						try:
							contenido = met["content"]
							content_list = contenido.split(",")
							for key in content_list:
								keywords.append(key.strip())
						except KeyError:
							pass							
						metas.append(met.encode("utf-8"))
					
					all_metas.append({"link": item["link"] , "meta": metas})
				except urllib.request.HTTPError as error:
					all_metas.append({"link": item["link"] , "meta": "Forbidden %s" % error.code})
				try:
					search = Search.objects.get(site_name=item["link"])					
				except Search.DoesNotExist as e:					
					search = Search()
					search.site_name = item["title"]
					search.site_url = item["link"]
					search.save()
				keys_count = len(soup.findAll(attrs={"name": "keywords"}))
				total_weight = 0
				if keys_count == 0:
					first_keys = data.split(" ")							
					for key in first_keys:							
						total_weight += len(soup.body.findAll(text=re.compile("%s" % key.upper())))						
						total_weight += len(soup.body.findAll(text=re.compile("%s" % key.lower())))						
						total_weight += len(soup.body.findAll(text=re.compile("%s" % key.capitalize())))
				search.site_weight = total_weight
				search.save()
			#for x in xrange(1, 10):
			#   n_total.append(x)
			#   res2 = service.cse().list( q=data, cx='011980423541542895616:ug0kbjbf6vm', gl='us', start=(x*10)+1, ).execute()
			#   for item in res2["items"]:
			#       all_links.append(item["link"])
			
			
				
					#print "Forbidden %s" %(error.code)
			#pprint.pprint(all_metas)
			return render(request, 'main/check.html', {'page': page, 'data': list(set(keywords)), 'do_search': data , 'search_city': search_city, 'search_country': search_country, "metas": all_metas })
	else:
		form = PostForm()
		return render(request, 'main/index.html', { 'form': form})

def filter(request):
	if request.method == 'POST':
		keys = request.POST.getlist('keys')
		do_search = request.POST.get('do_search')
		search_city = request.POST.get('search_city')
		search_country = request.POST.get('search_country')
		keys_string = ' '.join(keys)
		service = build("customsearch", "v1", developerKey="AIzaSyBfsEcEcNt4wtZq7iM5LV2gWfwnSQAD0cA")
		res = service.cse().list( q=data, cx='011980423541542895616:ug0kbjbf6vm', gl=search_country, hq="near=%s" % search_city, cr=search_country, hl=search_country, filter="1", orTerms=keys_string, ).execute()
		contact = []
		for item in res["items"]:
			try:
				search = Search.objects.get(site_name=item["title"])
			except Search.DoesNotExist as e:
				search = Search(site_name=item["title"], site_url=item["link"])
				search.save()
		for page in Search.objects.all():		
			html_doc = urllib.request.urlopen(page.site_url)
			soup = BeautifulSoup(html_doc, 'html.parser')
			info = soup.body.find(text=re.compile('^(?:(?:\+?1\s*(?:[.-]\s*)?)?(?:\(\s*([2-9]1[02-9]|[2-9][02-8]1|[2-9][02-8][02-9])\s*\)|([2-9]1[02-9]|[2-9][02-8]1|[2-9][02-8][02-9]))\s*(?:[.-]\s*)?)?([2-9]1[02-9]|[2-9][02-9]1|[2-9][02-9]{2})\s*(?:[.-]\s*)?([0-9]{4})(?:\s*(?:#|x\.?|ext\.?|extension)\s*(\d+))?$'))
			contact.append({"url": page.site_url, "info": info })

		return render(request, 'main/filter.html', {'contact': contact })
	else:
		form = PostForm()
		return render(request, 'main/index.html', {'form': form})
	