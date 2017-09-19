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
from googleapiclient.errors import HttpError
from django.core.validators import URLValidator
from django.core.exceptions import ValidationError
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
			Search.objects.all().delete()
			keywords = []
			data = form.cleaned_data['do_search']			
			search_city = form.cleaned_data['search_city']
			search_country = form.cleaned_data['search_country'] 
			language = form.cleaned_data['language'] 
			page = request.POST.get("page")
			try:
				service = build("customsearch", "v1", developerKey="AIzaSyBfsEcEcNt4wtZq7iM5LV2gWfwnSQAD0cA")
				res = service.cse().list( q="%s -filetype:pdf" % data, cx='011980423541542895616:ug0kbjbf6vm', hq="near=%s" % search_city, cr=search_country, hl=language, filter="1", ).execute()
				total = res["searchInformation"]["totalResults"]
				#print(res["queries"])
				all_links = []
				n_total = []
				all_metas = []
				try:
					for item in res["items"]:
						allow = True
						all_links.append(item["link"])
						metas = []
						soup = ""
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
							allow = False
							all_metas.append({"link": item["link"] , "meta": "Forbidden %s" % error.code})
						except urllib.request.URLError as error:
							allow = False
						try:
							search = Search.objects.get(site_url=item["link"])					
						except Search.DoesNotExist as e:					
							search = Search(site_name=item["title"], site_url=item["link"])
							if allow: 
								keys_count = len(soup.findAll(attrs={"name": "keywords"}))
								total_weight = 0
								if keys_count == 0:
									first_keys = data.split(" ")							
									for key in first_keys:							
										total_weight += len(soup.findAll(text=re.compile("%s" % key.upper())))						
										total_weight += len(soup.findAll(text=re.compile("%s" % key.lower())))						
										total_weight += len(soup.findAll(text=re.compile("%s" % key.capitalize())))
								search.site_weight = total_weight
							search.save()
					#for x in xrange(1, 10):
					#   n_total.append(x)
					#   res2 = service.cse().list( q=data, cx='011980423541542895616:ug0kbjbf6vm', gl='us', start=(x*10)+1, ).execute()
					#   for item in res2["items"]:
					#       all_links.append(item["link"])			
						
							#print "Forbidden %s" %(error.code)
					#pprint.pprint(all_metas)
					return render(request, 'main/check.html', {'page': page, 'data': sorted(list(set(keywords))), 'do_search': data , 'search_city': search_city, 'search_country': search_country, "language": language, "metas": all_metas })
				except KeyError as e:
					form = PostForm()
					return render(request, 'main/index.html', {'noitems': "No results %s" % e, 'form': form })
			except HttpError as e:
				form = PostForm()
				return render(request, 'main/index.html', {'limitreached': "You have reached the daily quota for your free plan. Please upgrade your plan.", 'form': form })
			
			
	else:
		form = PostForm()
		return render(request, 'main/index.html', { 'form': form})

def get_links(url):
	try:		
		page = urllib.request.urlopen(url)
		soup_links = BeautifulSoup(page, 'html.parser')		   
		links = [item['href'] for item in soup_links.findAll('a', href=True)]
		contact = [x for x in links if "contact" or "Contact" or "CONTACT" in x]
		return {"url": url, "links": contact, "error": ""}
	except urllib.request.HTTPError as error:
		return {"url": url, "links": "No response", "error": "No response"}
def valid_url(url):
	val = URLValidator()
	try:
		val(url)
	except ValidationError as e:
		return False
	return True

def get_info(url):
	try:
		splited_url = url.split("/")
		new_url = "%s//%s/" % (splited_url[0], splited_url[2])
		contact = get_links(new_url)
		if contact["error"] != "No response":
			for cont in list(set(contact)):
				if valid_url(cont):
					html_doc = urllib.request.urlopen(cont)
					soup = BeautifulSoup(html_doc, 'html.parser')
					info = soup.findAll(text=re.compile('^(?:(?:\+?1\s*(?:[.-]\s*)?)?(?:\(\s*([2-9]1[02-9]|[2-9][02-8]1|[2-9][02-8][02-9])\s*\)|([2-9]1[02-9]|[2-9][02-8]1|[2-9][02-8][02-9]))\s*(?:[.-]\s*)?)?([2-9]1[02-9]|[2-9][02-9]1|[2-9][02-9]{2})\s*(?:[.-]\s*)?([0-9]{4})(?:\s*(?:#|x\.?|ext\.?|extension)\s*(\d+))?$'))
					email = soup.findAll(text=re.compile('(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)'))
					return {"url": contact["url"], "info": info, 'email': email}
				elif cont == "":
					return {"url": contact["url"], "info": "No Valid or empty", "email": "No Valid or empty URL"}
				else:
					return {"url": cont, "info": "No Valid URL", "email": "No Valid URL"}
		else:
			return {"url": contact["url"], "info": "No Response", 'email': "No Response"}
	except urllib.request.HTTPError as error:
		return {"url": new_url, "info": "No Response", "email": "No Response from server"}
	except urllib.request.URLError as UrlError:
		return {"url": new_url, "info": "No Valid URL", "email": "No Valid URL"}
	return 


def filter(request):
	if request.method == 'POST':
		keys = request.POST.getlist('keys')
		do_search = request.POST.get('do_search')
		search_city = request.POST.get('search_city')
		search_country = request.POST.get('search_country')
		language = request.POST.get('language')
		keys_string = ' '.join(keys)
		service = build("customsearch", "v1", developerKey="AIzaSyBfsEcEcNt4wtZq7iM5LV2gWfwnSQAD0cA")
		res = service.cse().list( q="%s %s -filetype:pdf" % (do_search, keys_string), cx='011980423541542895616:ug0kbjbf6vm', hq="near=%s" % search_city, cr=search_country, hl=language,  filter="1", ).execute()
		contact = []
		for item in res["items"]:
			try:
				search = Search.objects.get(site_url=item["link"])
			except Search.DoesNotExist as e:
				search = Search(site_name=item["title"], site_url=item["link"])
				search.save()
		for page in Search.objects.all():
			contact.append(get_info(page.site_url))
			
		return render(request, 'main/filter.html', {'contact': contact })
	else:
		form = PostForm()
		return render(request, 'main/index.html', {'form': form})
	