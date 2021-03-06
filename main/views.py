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
				service = build("customsearch", "v1", developerKey="AIzaSyBfsEcEcNt4wtZq7iM5LV2gWfwnSQAD0cA")  # enriquea.rodriguezr
				res = service.cse().list(q="%s -filetype:pdf" % data, cx='011980423541542895616:ug0kbjbf6vm', hq="near=%s" % search_city, cr=search_country, hl=language, filter="1", ).execute()  # enriquea.rodriguezr
				# service = build("customsearch", "v1", developerKey="AIzaSyCkyySNSaqmDEt-1QaTzCiSUwWLN4aqhr8")  # arodriguez@ateravisiontech.com
				# res = service.cse().list(q="%s -filetype:pdf" % data, cx='013210873390130240871:lnlmh1y0yyg', hq="near=%s" % search_city, cr=search_country, hl=language, filter="1", ).execute()  # arodriguez@teravisiontech.com
				# service = build("customsearch", "v1", developerKey="AIzaSyApeEnuK8qB9oELABnVcMGVZlB6wZWYCrw")  # aerodriguezr1712@gmail.com
				# res = service.cse().list(q="%s -filetype:pdf" % data, cx='006779655238496411723:t_5t0k_hst0', hq="near=%s" % search_city, cr=search_country, hl=language, filter="1", ).execute()  # aerodriguezr1712@gmail.com
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
						infoSearch.related_search = data
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
		return render(request, 'main/index.html', {'form': form})


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
	yellow_search = requests.get('http://api2.yp.com/listings/v1/search?searchloc=%s&term=%s&format=json&sort=name&listingcount=20&key=gxs0rc3yx0' %(city, search))
	res = yellow_search.json()
	if res["searchResult"]["metaProperties"]["message"] == "":
		yellow = res["searchResult"]["searchListings"]["searchListing"]
	for item in yellow:
		try:
			yellow_save = InfoYellow.objects.get(site_name=item["businessName"])
			# print("Found %s" % yellow_save.site_name)
		except InfoYellow.DoesNotExist:
			yellow_save = InfoYellow()
			yellow_save.site_name = item["businessName"]
			yellow_save.site_url = item["websiteURL"]
			yellow_save.site_email = item["email"]
			yellow_save.site_address = "%s %s" %(item["street"], item["state"])
			yellow_save.related_search = search

			yellow_save.save()
			if(item["phone"] != ""):
				phone = Phone(phone=item["phone"])	
				phone.save()		
				yellow_save.site_phone.add(phone)

	return JsonResponse(yellow, safe=False)	


# no use
def yellowsearch(search, city):
	#yellow_search = requests.get('http://api2.yp.com/listings/v1/search?searchloc=%s&term=%s&format=json&sort=name&listingcount=20&key=zpddvzj9cy' %(city, search))
	yellow_search = requests.get('http://api2.yp.com/listings/v1/search?searchloc=%s&term=%s&format=json&sort=name&listingcount=20&key=5t4k08tttp' %(city, search))
	return yellow_search.json()


# in use
def filter_ajax(request):
	keys = request.GET.get('keys', None)
	keys_list = keys.split(",")
	do_search = request.GET.get('search_str', None)
	search_city = request.GET.get('search_city', None)
	search_country = request.GET.get('search_country', None)
	language = request.GET.get('language', None)		
	keys_string = ' '.join(keys_list)
	service = build("customsearch", "v1", developerKey="AIzaSyBfsEcEcNt4wtZq7iM5LV2gWfwnSQAD0cA")  # enriquea.rodriguezr
	# service = build("customsearch", "v1", developerKey="AIzaSyCkyySNSaqmDEt-1QaTzCiSUwWLN4aqhr8")  # arodriguez@ateravisiontech.com
	# service = build("customsearch", "v1", developerKey="AIzaSyApeEnuK8qB9oELABnVcMGVZlB6wZWYCrw")  # arodriguez@ateravisiontech.com
	if len(keys_list) > 0:
		res = service.cse().list(q="%s %s -filetype:pdf" % (do_search, keys_string), cx='011980423541542895616:ug0kbjbf6vm', hq="near=%s" % search_city, cr=search_country, hl=language,  filter="1", ).execute()  # enriquea.rodriguezr
		# res = service.cse().list(q="%s %s -filetype:pdf" % (do_search, keys_string), cx='013210873390130240871:lnlmh1y0yyg', hq="near=%s" % search_city, cr=search_country, hl=language, filter="1", ).execute()  # arodriguez@teravisiontech.com
		# res = service.cse().list(q="%s %s -filetype:pdf" % (do_search, keys_string), cx='006779655238496411723:t_5t0k_hst0', hq="near=%s" % search_city, cr=search_country, hl=language, filter="1", ).execute()  # aerodriguezr1712@gmail.com
	else:
		res = service.cse().list(q="%s -filetype:pdf" % do_search, cx='011980423541542895616:ug0kbjbf6vm', hq="near=%s" % search_city, cr=search_country, hl=language,  filter="1", ).execute()  # enriquea.rodriguezr
		# res = service.cse().list(q="%s -filetype:pdf" % do_search, cx='013210873390130240871:lnlmh1y0yyg', hq="near=%s" % search_city, cr=search_country, hl=language,  filter="1", ).execute()  # arodriguez@teravisiontech.com
		# res = service.cse().list(q="%s -filetype:pdf" % do_search, cx='006779655238496411723:t_5t0k_hst0', hq="near=%s" % search_city, cr=search_country, hl=language,  filter="1", ).execute()  # aerodriguezr1712@gmail.com
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
			search_inf = InfoSearch(site_url=item["link"], site_name=item["title"], related_search=do_search)
			search_inf.save()
	for page in Search.objects.all():
		contact.append({'url': page.site_url})
	return JsonResponse(contact, safe=False)


# in use
def make_excel(request):
	PATH_FULL = os.path.dirname(os.path.abspath(__file__))
	file_path = os.path.join(PATH_FULL, 'assets/unicode_name.xlsx')
	workbook = Workbook(file_path)
	worksheet = workbook.add_worksheet("Google Search")
	worksheet2 = workbook.add_worksheet("Yellow Pages")
	today = datetime.today()
	info = InfoSearch.objects.filter(search_date__year=today.year, search_date__month=today.month, search_date__day=today.day).order_by('related_search')
	count = 2
	worksheet.write('A1', "Sitio")
	worksheet.write('B1', "Url")
	worksheet.write('C1', "Telefonos")
	worksheet.write('D1', "Email")
	worksheet.write('E1', "Pagina Contacto")
	worksheet.write('F1', "Ranking Promedio")
	worksheet.write('G1', "Oppotunity")
	worksheet.write('H1', "Search Date")
	related = ""
	for item in info:
		if related == "":
			related = item.related_search
			worksheet.write('A%d' % count, 'busqueda relacionada = %s' % item.related_search)
			count += 1
		elif item.related_search != related:
			related = item.related_search
			worksheet.write('A%d' % count, 'busqueda relacionada = %s' % item.related_search)
			count += 1

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
		worksheet.write('F%d' % count, "%s" % item.average_ranking)
		worksheet.write('G%d' % count, "You currently rank somewhere in the top %s on %s search phrases on Google. If you could land number one spot for all those searches, you'd get about %s additional clicks per month. That would cost you more than $%s in equivalent PPC dollars." % (item.top_ranking, item.search_nums, item.click_aditional, item.click_cost))
		date = item.search_date
		worksheet.write('H%d' % count, "%s" % date)

		count += 1

	worksheet2.write('A1', "Sitio")
	worksheet2.write('B1', "Url")
	worksheet2.write('C1', "Telefonos")
	worksheet2.write('D1', "Email")
	worksheet2.write('E1', "Direccion")
	yellow = InfoYellow.objects.filter(search_date__year=today.year, search_date__month=today.month, search_date__day=today.day).order_by("related_search")
	count = 2
	related_yellow = ""
	for yell in yellow:
		if related_yellow == "":
			related_yellow = yell.related_search
			worksheet2.write('A%d' % count, 'busqueda relacionada= %s' %yell.related_search)
			count += 1
		elif related_yellow != yell.related_search:
			related_yellow = yell.related_search
			worksheet2.write('A%d' % count, 'busqueda relacionada= %s' %yell.related_search)
			count += 1

		worksheet2.write('A%d' % count, yell.site_name)
		worksheet2.write('B%d' % count, yell.site_url)
		phones = ""
		num = 0
		for phon in yell.site_phone.all():
			if num == 0:
				phones += "%s" % phon.phone
			else:
				phones += ", %s " % phon.phone
			num += 1
		worksheet2.write('C%d' % count, phones)
		worksheet2.write('D%d' % count, yell.site_email)
		worksheet2.write('E%d' % count, yell.site_address)
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
		keys = request.POST.getlist('keys[]')
		do_search = request.POST.get('do_search')
		search_city = request.POST.get('search_city')
		search_country = request.POST.get('search_country')
		language = request.POST.get('language')
		keys_string = ','.join(keys)
		print(keys_string)
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


def get_position(request):
	keys = request.GET.get('keys', None)
	keys_list = keys.split(",")
	link_src = request.GET.get('url', None)
	do_search = request.GET.get('search_str', None)
	search_city = request.GET.get('search_city', None)
	search_country = request.GET.get('search_country', None)
	language = request.GET.get('language', None)
	contact = []
	try:
		info = InfoSearch.objects.get(site_url="%s/" % link_src)
	except InfoSearch.DoesNotExist:
		info = InfoSearch(site_url="%s/" % link_src)
	service = build("customsearch", "v1", developerKey="AIzaSyBfsEcEcNt4wtZq7iM5LV2gWfwnSQAD0cA")  # enriquea.rodriguezr
	# service = build("customsearch", "v1", developerKey="AIzaSyCkyySNSaqmDEt-1QaTzCiSUwWLN4aqhr8")  # arodriguez@teravisiontech.com
	# service = build("customsearch", "v1", developerKey="AIzaSyApeEnuK8qB9oELABnVcMGVZlB6wZWYCrw")  # aerodriguezr1712@gmail.com
	if len(keys_list) > 0:
		sumrise = 0
		count = 0
		for key in keys_list:
			if count <= 2:
				res = service.cse().list(q="%s -filetype:pdf" % (key), cx='011980423541542895616:ug0kbjbf6vm', hq="near=%s" % search_city, cr=search_country, hl=language, filter="1", ).execute()  # enriquea.rodriguezr
				# res = service.cse().list(q="%s -filetype:pdf" % (key), cx='013210873390130240871:lnlmh1y0yyg', hq="near=%s" % search_city, cr=search_country, hl=language, filter="1", ).execute()  # arodriguez@teravisiontech.com
				# res = service.cse().list(q="%s -filetype:pdf" % (key), cx='006779655238496411723:t_5t0k_hst0', hq="near=%s" % search_city, cr=search_country, hl=language, filter="1", ).execute()  # aerodriguezr1712@gmail.com
				posi_num = 0
				for item in res["items"]:
					posi_num += 1
					if item["link"] == link_src:
						break
				if posi_num == 0:
					sumrise += 10
				else:
					sumrise += posi_num
				count += 1
			else:
				pass
		posi = sumrise/count
		info.average_ranking = posi
		info.save()
	else:
		res = service.cse().list(q="%s -filetype:pdf" % do_search, cx='011980423541542895616:ug0kbjbf6vm', hq="near=%s" % search_city, cr=search_country, hl=language, filter="1", ).execute()  # enriquea.rodriguezr
		# res = service.cse().list(q="%s -filetype:pdf" % do_search, cx='013210873390130240871:lnlmh1y0yyg', hq="near=%s" % search_city, cr=search_country, hl=language, filter="1", ).execute()  # arodriguez@ateravisiontech.com
		# res = service.cse().list(q="%s -filetype:pdf" % do_search, cx='006779655238496411723:t_5t0k_hst0', hq="near=%s" % search_city, cr=search_country, hl=language, filter="1", ).execute()  # aerodriguezr1712@teravisiontech.com
		posi_num = 0
		posi = 0
		for item in res["items"]:
			posi_num += 1
			if item["link"] == link_src:
				break
		if posi_num == 0:
			posi += 10
		else:
			posi += posi_num
		info.average_ranking = posi
		info.save()
		count = 1

	contact.append({'position': posi, 'key_count': count})
	return JsonResponse(contact, safe=False)


def get_spyfu_data(request):
	keys = request.GET.get('keys', None)
	link_src = request.GET.get('url', None)
	try:
		info = InfoSearch.objects.get(site_url="%s/" % link_src)
	except InfoSearch.DoesNotExist:
		info = InfoSearch(site_url="%s/" % link_src)
	contact = []

	# Posicion del dominio dentro del top
	ranking = request.GET.get('position', None)
	info.average_ranking = ranking

	# numero de keywords en los que se busco el dominio
	phrase_num = request.GET.get('key_count', None)
	info.search_nums = phrase_num
	phrases = keys.split(",")

	# depende de la profundidad en la cual se busca el dominio, ej: si se busco en las primeras 5 paginas de la
	# busqueda de google seria el top 50 contando con que cada pagina son 10 pocisiones
	top = int(phrase_num) * 10
	info.top_ranking = top

	# numero de click adicionales en caso de lograr el primer lugar en cada keyword buscado
	api_key = "TTUH1QJH"
	count_click = 0

	# costo del total de clicks pagos adicionales
	paid_click_cost = 0

	for key in phrases:
		key = key.replace("[", "")
		key = key.replace("'", "")
		key = key.replace("]", "")
		if key != "":
			api_req = "https://www.spyfu.com/apis/core_api/get_term_ranking_urls_us?term=%s&api_key=%s" % (key, api_key)
			req_raw = requests.get(api_req)
			try:
				req_json = req_raw.json()
				count_click += float(req_json["organicGrid"][0]["rawEstimatedOrganicMonthlyClicks"])
			except ValueError:
				pass
			api_req_cost = "https://www.spyfu.com/apis/core_api/get_term_metrics_us?term=%s&api_key=%s" % (key, api_key)
			req_raw_cost = requests.get(api_req_cost)
			try:
				req_json_cost = req_raw_cost.json()
				paid_click_cost += float(req_json_cost["rawPhraseCostPerMonth"])
			except ValueError:
				pass

	info.click_aditional = count_click
	info.click_cost = paid_click_cost
	info.save()
	contact.append({'countClicks': count_click, 'clickCost': paid_click_cost, 'top': top, 'ranking': ranking, 'phraseNumber': phrase_num})
	return JsonResponse(contact, safe=False)



