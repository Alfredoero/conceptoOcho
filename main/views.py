#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
import urllib.request
from .forms import PostForm
from .models import Search, Keyword, Phone, InfoSearch, InfoYellow
from bs4 import BeautifulSoup
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from django.core.validators import URLValidator
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from xlsxwriter.workbook import Workbook
from wsgiref.util import FileWrapper
from conceptoOcho.settings import PROJECT_ROOT
#from .tasks import placesearch_task, yellowsearch_task
from datetime import datetime
import requests
import chardet
import pprint
import json
import re
import os


# Create your views here.
def index(request):
	form = PostForm()
	Search.objects.all().delete()
	return render(request, 'main/index.html', {'form': form})


# in use
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
				res = service.cse().list(q="%s -filetype:pdf" % data, cx='011980423541542895616:ug0kbjbf6vm', hq="near=%s" % search_city, cr=search_country, hl=language, filter="1", ).execute()
				all_links = []

				for item in res["items"]:
					try:
						allow = True
						all_links.append(item["link"])
						metas = []
						soup = ""
						infoSearch = InfoSearch(site_url=item["link"])
						try:
							html_doc = urllib.request.urlopen(item["link"])
							soup = BeautifulSoup(html_doc, 'html.parser')
							for met in soup.findAll(attrs={"name": "keywords"}):
								try:
									contenido = met["content"]
									content_list = contenido.split(",")
									for key in content_list:
										if key.strip() != "" and key.strip() != " ":
											keywords.append(key.strip())
											metas.append(key.strip())
											try:
												keyw = Keyword.objects.get(keyword=key.strip())
											except Keyword.DoesNotExist:
												keyw = Keyword()
												keyw.keyword = key.strip()
												keyw.save()
								except KeyError:
									pass

						except urllib.request.HTTPError as error:
							allow = False
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
						infoSearch.site_name = item["title"]
						infoSearch.save()
						for meta in metas:
							keyw_l = Keyword.objects.get(keyword=meta)
							infoSearch.site_keywords.add(keyw_l)
						# for x in xrange(1, 10):
						#   n_total.append(x)
						#   res2 = service.cse().list( q=data, cx='011980423541542895616:ug0kbjbf6vm', gl='us', start=(x*10)+1, ).execute()
						#   for item in res2["items"]:
						#       all_links.append(item["link"])

						# print "Forbidden %s" %(error.code)
					# pprint.pprint(all_metas)
					except KeyError as e:
						form = PostForm()
						return render(request, 'main/index.html', {'noitems': "No results %s" % e, 'form': form})
					except IntegrityError:
						pass
				return render(request, 'main/check.html',
							  {'page': page, 'data': sorted(list(set(keywords))), 'do_search': data,
							   'search_city': search_city, 'search_country': search_country, "language": language})
			except HttpError as error:
				form = PostForm()
				return render(request, 'main/index.html', {'limitreached': "You have reached the daily quota for your free plan. Please upgrade your plan. %s" % error, 'form': form})
	else:
		form = PostForm()
		return render(request, 'main/index.html', { 'form': form})


# in use
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
		return {"url": url, "links": contact, "error": "No response %s" % url}


# in use
def valid_url(url):
	val = URLValidator()
	try:
		val(url)
	except ValidationError as e:
		return False	
	return True


# in use
def get_info(request):	
	info_all = []
	new_url = ""
	try:
		url = request.GET.get('url')
		save_info = InfoSearch.objects.get(site_url=url)
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
						save_info.site_contact_url = url_contact
						save_info.site_email = email
						for num in info_list:
							phone_num = Phone(phone=num)
							phone_num.save()
							save_info.site_phones.add(phone_num)
						save_info.save()
						return JsonResponse(info_all, safe=False)
					else:
						info_all.append({"url": contacto["links"], "info": "No Valid URL on links %s" % url_contact, "email": "No Valid URL on links %s" % url_contact})
						return JsonResponse(info_all, safe=False)
			else:
				html_doc = urllib.request.urlopen(new_url)
				soup = BeautifulSoup(html_doc, 'html.parser')
				info = soup.findAll(text=re.compile('^(?:(?:\+?1\s*(?:[.-]\s*)?)?(?:\(\s*([2-9]1[02-9]|[2-9][02-8]1|[2-9][02-8][02-9])\s*\)|([2-9]1[02-9]|[2-9][02-8]1|[2-9][02-8][02-9]))\s*(?:[.-]\s*)?)?([2-9]1[02-9]|[2-9][02-9]1|[2-9][02-9]{2})\s*(?:[.-]\s*)?([0-9]{4})(?:\s*(?:#|x\.?|ext\.?|extension)\s*(\d+))?$'))
				#info += soup.findAll(text=re.compile('.*?(\(?\d{3}\D{0,3}\d{3}\D{0,3}\d{4}).*?'))
				info_list = [re.sub("[^0-9()-]","", x) for x in info]
				email = soup.findAll(text=re.compile('(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)'))
				info_all.append({"url": contacto["url"], "info": info_list, 'email': email, "found": "No Contact URLs found"})
				save_info.site_contact_url = "Not Found"
				save_info.site_email = email
				for num in info_list:
					phone_num = Phone(phone=num)
					phone_num.save()
					save_info.site_phones.add(phone_num)
				save_info.save()
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


# no use
def yellow_status(request):
	return None


# in use
def yellow_ajax(request):
	search = request.GET.get("search_str", None)
	city = request.GET.get("search_city", None)
	yellow = []
	yellow_search = requests.get('http://api2.yp.com/listings/v1/search?searchloc=%s&term=%s&format=json&sort=name&listingcount=20&key=zpddvzj9cy' %(city, search))
	res = yellow_search.json()
	if res["searchResult"]["metaProperties"]["message"] == "":
		yellow = res["searchResult"]["searchListings"]["searchListing"]
	for item in yellow:
		try:
			yellow_save = InfoYellow.objects.get(site_name=item["businessName"])
			print("Found %s" % yellow_save.site_name)
		except InfoYellow.DoesNotExist:
			yellow_save = InfoYellow()
			yellow_save.site_name = item["businessName"]
			yellow_save.site_url = item["websiteURL"]
			yellow_save.site_email = item["email"]
			phone = Phone(phone=item["phone"])			
			yellow_save.site_address = "%s %s" %(item["street"], item["state"])
			yellow_save.save()
			yellow_save.site_phone.add(phone)

	return JsonResponse(yellow, safe=False)	


# no use
def yellowsearch(search, city):
	#yellow_search = requests.get('http://api2.yp.com/listings/v1/search?searchloc=%s&term=%s&format=json&sort=name&listingcount=20&key=zpddvzj9cy' %(city, search))
	yellow_search = requests.get('http://api2.yp.com/listings/v1/search?searchloc=%s&term=%s&format=json&sort=name&listingcount=20&key=5t4k08tttp' %(city, search))
	return yellow_search.json()


# no use
def place_detail(request):
	place_id = request.GET.get('place_id', None)
	url_detail= "https://maps.googleapis.com/maps/api/place/details/json?placeid=%s&key=AIzaSyCCw6wXXZqy0XpYQi17xjU66yhoto1XiVw" % place_id
	google_detail = requests.get(url_detail)
	sch_detail = google_detail.json()
	data = {}
	if sch_detail["status"] == "OK" :
		data = {"address": sch_detail["result"]["formatted_address"], "number": sch_detail["result"]["international_phone_number"], "name": sch_detail["result"]["name"], "url": sch_detail["result"]["website"]}
		return JsonResponse(data)
	else:
		return None


# def place_status(request):
#
# 	detail_places = []
# 	for res in search["results"]:
# 		plc_id = res["place_id"]
# 		url_detail= "https://maps.googleapis.com/maps/api/place/details/json?placeid=%s&key=AIzaSyCCw6wXXZqy0XpYQi17xjU66yhoto1XiVw" % plc_id
# 		google_detail = requests.get(url_detail)
# 		sch_detail = google_detail.json()
# 		if(sch_detail["status"] == "OK"):
# 			try:
# 				address = sch_detail["result"]["formatted_address"]
# 				number = sch_detail["result"]["international_phone_number"]
# 				name = sch_detail["result"]["name"]
# 				url = sch_detail["result"]["website"]
# 				detail_places.append({"address": address, "number": number, "name": name, "url": url})
# 			except KeyError as e:
# 				if e == "website":
# 					detail_places.append({"address": address, "number": number, "name": name, "url": "Not found"})
# 				elif e == "international_phone_number":
# 					detail_places.append({"address": address, "number": "Not found", "name": name, "url": url})
#
# 		# print(res["name"])
# 	return detail_places


# no use
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


# in use
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
		try:
			search_inf = InfoSearch.objects.get(site_url=item["link"])
		except InfoSearch.DoesNotExist as e:
			search_inf = InfoSearch(site_url=item["link"])
			search_inf.save()
	for page in Search.objects.all():
		contact.append({'url': page.site_url})
	return JsonResponse(contact, safe=False)


# in use
def make_excel(request):
	PATH_FULL = os.path.dirname(os.path.abspath(__file__))
	file_path = os.path.join(PATH_FULL,'assets/unicode_name.xlsx')
	workbook = Workbook(file_path)
	worksheet = workbook.add_worksheet("Google Search")
	worksheet2 = workbook.add_worksheet("Yellow Pages")
	today = datetime.today()	
	info = InfoSearch.objects.filter(search_date__year=today.year, search_date__month=today.month, search_date__day=today.day)
	count = 2
	worksheet.write('A1', "Sitio")
	worksheet.write('B1', "Url")
	worksheet.write('C1', "Telefonos")
	worksheet.write('D1', "Email")
	worksheet.write('E1', "Pagina Contacto")
	for item in info:
		worksheet.write('A%d' % count, item.site_name)
		worksheet.write('B%d' % count, item.site_url)
		phones = ""
		num = 0
		for phon in item.site_phones.all():
			if num == 0:
				phones += "%s" % phon.phone
			else:
				phones += ", %s " % phon.phone
			num += 1
		worksheet.write('C%d' % count, phones)
		worksheet.write('D%d' % count, item.site_email)
		worksheet.write('E%d' % count, item.site_contact_url)
		count += 1

	worksheet2.write('A1', "Sitio")
	worksheet2.write('B1', "Url")
	worksheet2.write('C1', "Telefonos")
	worksheet2.write('D1', "Email")
	worksheet2.write('E1', "Direccion")
	yellow = YellowSearch.objects.filter(search_date__year=today.year, search_date__month=today.month, search_date__day=today.day)
	for yell in yellow:
		worksheet.write('A%d' % count, yell.site_name)
		worksheet.write('B%d' % count, yell.site_url)
		phones = ""
		num = 0
		for phon in yell.site_phones.all():
			if num == 0:
				phones += "%s" % phon.phone
			else:
				phones += ", %s " % phon.phone
			num += 1
		worksheet.write('C%d' % count, phones)
		worksheet.write('D%d' % count, yell.site_email)
		worksheet.write('E%d' % count, yell.site_address)
		count += 1
	#worksheet.write('A2', var2)
	workbook.close()
	data = {'status': "ok", "file_name": "name.xlsx"}
	return JsonResponse(data, safe=False)


# in use
def excel_download(request):
	PATH_FULL = os.path.dirname(os.path.abspath(__file__))
	path = os.path.join(PATH_FULL, 'assets')
	file = open(os.path.join(path,"unicode_name.xlsx"), 'rb')
	response = HttpResponse(FileWrapper(file), content_type='application/vnd.ms-excel') 
	response['Content-Disposition'] = 'attachment; filename=excel.xlsx'
	file.close()
	return response


# in use
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



