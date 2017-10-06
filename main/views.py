#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
import urllib.request
from .forms import PostForm
from .models import Search
from bs4 import BeautifulSoup
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from django.core.validators import URLValidator
from django.core.exceptions import ValidationError
from xlsxwriter.workbook import Workbook
from wsgiref.util import FileWrapper
from conceptoOcho.settings import PROJECT_ROOT
#from .tasks import placesearch_task, yellowsearch_task
import requests
import pprint
import json
import re
import os


# Create your views here.
def index(request):
	form = PostForm()
	Search.objects.all().delete()
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
										if(key.strip() != "" and key.strip() != " "):
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
		contact = []
		return {"url": url, "links": contact , "error": "No response %s" % url}


def valid_url(url):
	val = URLValidator()
	try:
		val(url)
	except ValidationError as e:
		return False	
	return True


def get_info(request):	
	info_all = []
	try:
		url = request.GET.get('url')
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
						#info += soup.findAll(text=re.compile('(\d{3}[-\.\s]??\d{3}[-\.\s]??\d{4}|\(\d{3}\)\s*\d{3}[-\.\s]??\d{4}|\d{3}[-\.\s]??\d{4})'))
						info_list = [re.sub("[^0-9()-]","", x) for x in info]
						email = soup.findAll(text=re.compile('(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)'))
						info_all.append({"url": contacto["url"], "info": info_list, 'email': email, "found": url_contact})
						return JsonResponse(info_all, safe=False)
					else:
						info_all.append({"url": contacto["links"], "info": "No Valid URL on links %s" % url_contact, "email": "No Valid URL on links %s" % url_contact})
						return JsonResponse(info, safe=False)
			else:
				html_doc = urllib.request.urlopen(new_url)
				soup = BeautifulSoup(html_doc, 'html.parser')
				info = soup.findAll(text=re.compile('^(?:(?:\+?1\s*(?:[.-]\s*)?)?(?:\(\s*([2-9]1[02-9]|[2-9][02-8]1|[2-9][02-8][02-9])\s*\)|([2-9]1[02-9]|[2-9][02-8]1|[2-9][02-8][02-9]))\s*(?:[.-]\s*)?)?([2-9]1[02-9]|[2-9][02-9]1|[2-9][02-9]{2})\s*(?:[.-]\s*)?([0-9]{4})(?:\s*(?:#|x\.?|ext\.?|extension)\s*(\d+))?$'))
				#info += soup.findAll(text=re.compile('.*?(\(?\d{3}\D{0,3}\d{3}\D{0,3}\d{4}).*?'))
				info_list = [re.sub("[^0-9()-]","", x) for x in info]
				email = soup.findAll(text=re.compile('(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)'))
				info_all.append({"url": contacto["url"], "info": info_list, 'email': email, "found": "No Contact URLs found"})
				return JsonResponse(info_all, safe=False)
		else:
			info_all.append({"url": contacto["url"], "info": "Error %s" % contacto["error"], 'email': "Error %s" % contacto["error"]})
			return JsonResponse(info_all, safe=False)
	except urllib.request.HTTPError as error:
		info_all.append({"url": new_url, "info": "No Response from server", "email": "No Response from server"})
		return JsonResponse(info_all, safe=False)
	except urllib.request.URLError as UrlError:
		info_all.append({"url": new_url, "info": "No Valid URL on contact", "email": "No Valid URL on contact"})
		return JsonResponse(info_all, safe=False)
	return


def yellow_status(request):
	return None


def yellow_ajax(request):
	search = request.GET.get("search_str", None)
	city = request.GET.get("search_city", None)
	yellow = []
	yellow_search = requests.get('http://api2.yp.com/listings/v1/search?searchloc=%s&term=%s&format=json&sort=name&listingcount=20&key=zpddvzj9cy' %(city, search))
	res = yellow_search.json()
	if res["searchResult"]["metaProperties"]["message"] == "":
		yellow = res["searchResult"]["searchListings"]["searchListing"]
	
	return JsonResponse(yellow, safe=False)	


def yellowsearch(search, city):
	yellow_search = requests.get('http://api2.yp.com/listings/v1/search?searchloc=%s&term=%s&format=json&sort=name&listingcount=20&key=zpddvzj9cy' %(city, search))
	#yellow_search = requests.get('http://api2.yp.com/listings/v1/search?searchloc=%s&term=%s&format=json&sort=name&listingcount=20&key=5t4k08tttp' %(city, search))
	return yellow_search.json()


def place_detail(request):
	place_id = request.GET.get('place_id', None)
	url_detail= "https://maps.googleapis.com/maps/api/place/details/json?placeid=%s&key=AIzaSyCCw6wXXZqy0XpYQi17xjU66yhoto1XiVw" % place_id
	google_detail = requests.get(url_detail)
	sch_detail = google_detail.json()
	data = {}
	if(sch_detail["status"] == "OK"):
		data = {"address": sch_detail["result"]["formatted_address"], "number": sch_detail["result"]["international_phone_number"], "name": sch_detail["result"]["name"], "url": sch_detail["result"]["website"]}
		return JsonResponse(data)
	else:
		return None


def place_status(request):

	detail_places = []
	for res in search["results"]:
		plc_id = res["place_id"]
		url_detail= "https://maps.googleapis.com/maps/api/place/details/json?placeid=%s&key=AIzaSyCCw6wXXZqy0XpYQi17xjU66yhoto1XiVw" % plc_id
		google_detail = requests.get(url_detail)
		sch_detail = google_detail.json()
		if(sch_detail["status"] == "OK"):
			try: 
				address = sch_detail["result"]["formatted_address"]
				number = sch_detail["result"]["international_phone_number"]
				name = sch_detail["result"]["name"]
				url = sch_detail["result"]["website"]
				detail_places.append({"address": address, "number": number, "name": name, "url": url})
			except KeyError as e:
				if e == "website":
					detail_places.append({"address": address, "number": number, "name": name, "url": "Not found"})
				elif e == "international_phone_number":
					detail_places.append({"address": address, "number": "Not found", "name": name, "url": url})
				
		# print(res["name"])
	return detail_places
	 

def placesearch(search, city):
	sch = search.replace(' ', '+')
	cty = city.replace(' ', '+')
	url = "https://maps.googleapis.com/maps/api/place/textsearch/json?query=%s+in+%s&key=AIzaSyCCw6wXXZqy0XpYQi17xjU66yhoto1XiVw" % (sch, cty)
	google_places = requests.get(url)
	search = google_places.json()
	detail_places = []
	for res in search["results"]:
		plc_id = res["place_id"]
		url_detail= "https://maps.googleapis.com/maps/api/place/details/json?placeid=%s&key=AIzaSyCCw6wXXZqy0XpYQi17xjU66yhoto1XiVw" % plc_id
		google_detail = requests.get(url_detail)
		sch_detail = google_detail.json()
		if(sch_detail["status"] == "OK"):
			try: 
				address = sch_detail["result"]["formatted_address"]
				number = sch_detail["result"]["international_phone_number"]
				name = sch_detail["result"]["name"]
				url = sch_detail["result"]["website"]
				detail_places.append({"address": address, "number": number, "name": name, "url": url})
			except KeyError as e:
				if e == "website":
					detail_places.append({"address": address, "number": number, "name": name, "url": "Not found"})
				elif e == "international_phone_number":
					detail_places.append({"address": address, "number": "Not found", "name": name, "url": url})
				
	return detail_places


def filter_ajax(request):
	keys = request.GET.get('keys', None)
	keys_list = keys.split(",")
	do_search = request.GET.get('search_str', None)
	search_city = request.GET.get('search_city', None)
	search_country = request.GET.get('search_country', None)
	language = request.GET.get('language', None)		
	keys_string = ' '.join(keys_list)
	service = build("customsearch", "v1", developerKey="AIzaSyBfsEcEcNt4wtZq7iM5LV2gWfwnSQAD0cA")
	if len(keys_list) > 0:
		res = service.cse().list(q="%s %s -filetype:pdf" % (do_search, keys_string), cx='011980423541542895616:ug0kbjbf6vm', hq="near=%s" % search_city, cr=search_country, hl=language,  filter="1", ).execute()
	else:
		res = service.cse().list(q="%s -filetype:pdf" % do_search, cx='011980423541542895616:ug0kbjbf6vm', hq="near=%s" % search_city, cr=search_country, hl=language,  filter="1", ).execute()
	contact = []
	for item in res["items"]:
		try:
			search = Search.objects.get(site_url=item["link"])
		except Search.DoesNotExist as e:
			search = Search(site_name=item["title"], site_url=item["link"])
			search.save()
	for page in Search.objects.all():
		contact.append({'url': page.site_url})
	return JsonResponse(contact, safe=False)


def make_excel(request):
	PATH_FULL = os.path.dirname(os.path.abspath(__file__))
	file_path = os.path.join(PATH_FULL,'assets/name.xlsx')
	workbook = Workbook(file_path)
	worksheet = workbook.add_worksheet()
	worksheet.write('A1', "Zup nigga")
	worksheet.write('A2', "Zup Bro")
	workbook.close()
	data = {'status': "ok", "file_name": "name.xlsx"}
	return JsonResponse(data, safe=False)


def excel_download(request, filename):
	PATH_FULL = os.path.dirname(os.path.abspath(__file__))
	path = os.path.join(PATH_FULL, 'assets')
	print(filename)
	f = open(path+"/name.xlsx", "r")
	response = HttpResponse(FileWrapper(f), content_type='text/csv')
	response['Content-Disposition'] = 'attachment; filename=excel.xlsx'
	f.close()
	return response


def filter(request):
	if request.method == 'POST':
		keys = request.POST.getlist('keys')
		do_search = request.POST.get('do_search')
		search_city = request.POST.get('search_city')
		search_country = request.POST.get('search_country')
		language = request.POST.get('language')
		keys_string = ','.join(keys)
		return render(request, 'main/filter.html', 
			{	'search': do_search, 
				'city': search_city,
				'keys': keys,
				'country': search_country,
				'language': language
			})
	else:
		form = PostForm()
		return render(request, 'main/index.html', {'form': form})



