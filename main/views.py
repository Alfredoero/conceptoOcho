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
import requests
import pprint
import json
import re


# Create your views here.
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
				# print(res["queries"])
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
						# for x in xrange(1, 10):
						#   n_total.append(x)
						#   res2 = service.cse().list( q=data, cx='011980423541542895616:ug0kbjbf6vm', gl='us', start=(x*10)+1, ).execute()
						#   for item in res2["items"]:
						#       all_links.append(item["link"])

						# print "Forbidden %s" %(error.code)
					# pprint.pprint(all_metas)
					return render(request, 'main/check.html', {'page': page, 'data': sorted(list(set(keywords))), 'do_search': data , 'search_city': search_city, 'search_country': search_country, "language": language, "metas": all_metas })
				except KeyError as e:
					form = PostForm()
					return render(request, 'main/index.html', {'noitems': "No results %s" % e, 'form': form })
			except HttpError as error:
				form = PostForm()
				return render(request, 'main/index.html', {'limitreached': "You have reached the daily quota for your free plan. Please upgrade your plan. %s" % error , 'form': form })
	else:
		form = PostForm()
		return render(request, 'main/index.html', { 'form': form})


def get_links(url):
	try:
		page = urllib.request.urlopen(url)
		soup_links = BeautifulSoup(page, 'html.parser')
		links = [item['href'] for item in soup_links.findAll('a', href=True)]
		contact = [x for x in links if "contact" in x]
		contact += [x for x in links if "Contact" in x]
		contact += [x for x in links if "CONTACT" in x]
		return {"url": url, "links": contact, "error": ""}
	except urllib.request.HTTPError as error:
		return {"url": url, "links": "No response %s" % url, "error": "No response %s" % url}


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
		new_url = "%s//%s" % (splited_url[0], splited_url[2])
		contacto = get_links(new_url)
		if contacto["error"] == "":
			if len(contacto["links"]) > 0:
				for cont in list(set(contacto['links'])):
					if "http" in cont:
						url_contact = cont
					else:
						if "/" in cont:
							url_contact = "%s%s" % (new_url, cont)
						else:
							url_contact = "%s/%s" % (new_url, cont)

					if valid_url(url_contact):
						html_doc = urllib.request.urlopen(url_contact)
						soup = BeautifulSoup(html_doc, 'html.parser')
						info = soup.findAll(text=re.compile('^(?:(?:\+?1\s*(?:[.-]\s*)?)?(?:\(\s*([2-9]1[02-9]|[2-9][02-8]1|[2-9][02-8][02-9])\s*\)|([2-9]1[02-9]|[2-9][02-8]1|[2-9][02-8][02-9]))\s*(?:[.-]\s*)?)?([2-9]1[02-9]|[2-9][02-9]1|[2-9][02-9]{2})\s*(?:[.-]\s*)?([0-9]{4})(?:\s*(?:#|x\.?|ext\.?|extension)\s*(\d+))?$'))
						info += soup.findAll(text=re.compile('(\d{3}[-\.\s]??\d{3}[-\.\s]??\d{4}|\(\d{3}\)\s*\d{3}[-\.\s]??\d{4}|\d{3}[-\.\s]??\d{4})'))
						info_list = [re.sub("[^0-9()-]","", x) for x in info]
						email = soup.findAll(text=re.compile('(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)'))
						return {"url": contacto["url"], "info": info_list, 'email': email, "found": url_contact}
					else:
						return {"url": contacto["links"], "info": "No Valid URL on links %s" % url_contact, "email": "No Valid URL on links %s" % url_contact}
			else:
				html_doc = urllib.request.urlopen(new_url)
				soup = BeautifulSoup(html_doc, 'html.parser')
				info = soup.findAll(text=re.compile('^(?:(?:\+?1\s*(?:[.-]\s*)?)?(?:\(\s*([2-9]1[02-9]|[2-9][02-8]1|[2-9][02-8][02-9])\s*\)|([2-9]1[02-9]|[2-9][02-8]1|[2-9][02-8][02-9]))\s*(?:[.-]\s*)?)?([2-9]1[02-9]|[2-9][02-9]1|[2-9][02-9]{2})\s*(?:[.-]\s*)?([0-9]{4})(?:\s*(?:#|x\.?|ext\.?|extension)\s*(\d+))?$'))
				info += soup.findAll(text=re.compile('.*?(\(?\d{3}\D{0,3}\d{3}\D{0,3}\d{4}).*?'))
				info_list = [re.sub("[^0-9()-]","", x) for x in info]
				email = soup.findAll(text=re.compile('(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)'))
				return {"url": contacto["url"], "info": info_list, 'email': email, "found": "No Contact URLs found"}
		else:
			return {"url": contacto["url"], "info": "Error %s" % contacto["error"], 'email': "Error %s" % contacto["error"]}
	except urllib.request.HTTPError as error:
		return {"url": new_url, "info": "No Response from server", "email": "No Response from server"}
	except urllib.request.URLError as UrlError:
		return {"url": new_url, "info": "No Valid URL on contact", "email": "No Valid URL on contact"}
	return


def yellowsearch(search, city):
	yellow_search = requests.get('http://api2.yp.com/listings/v1/search?searchloc=%s&term=%s&format=json&sort=name&listingcount=20&key=5t4k08tttp' %(city, search))
	return yellow_search.json()


def filter(request):
	if request.method == 'POST':
		keys = request.POST.getlist('keys')
		do_search = request.POST.get('do_search')
		search_city = request.POST.get('search_city')
		search_country = request.POST.get('search_country')
		language = request.POST.get('language')
		keys_string = ' '.join(keys)
		service = build("customsearch", "v1", developerKey="AIzaSyBfsEcEcNt4wtZq7iM5LV2gWfwnSQAD0cA")
		res = service.cse().list(q="%s %s -filetype:pdf" % (do_search, keys_string), cx='011980423541542895616:ug0kbjbf6vm', hq="near=%s" % search_city, cr=search_country, hl=language,  filter="1", ).execute()
		contact = []
		for item in res["items"]:
			try:
				search = Search.objects.get(site_url=item["link"])
			except Search.DoesNotExist as e:
				search = Search(site_name=item["title"], site_url=item["link"])
				search.save()
		for page in Search.objects.all():
			contact.append(get_info(page.site_url))
		more_search = yellowsearch("%s" % do_search, search_city)
		yellow = []
		if more_search["searchResult"]["metaProperties"]["message"] == "":
			yellow = more_search["searchResult"]["searchListings"]["searchListing"]
		return render(request, 'main/filter.html', {'contact': contact, "yellow": yellow, "yellowmessage": more_search["searchResult"]["metaProperties"]["message"]})
	else:
		form = PostForm()
		return render(request, 'main/index.html', {'form': form})