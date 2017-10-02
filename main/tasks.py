from huey.contrib.djhuey import task


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

@task()
def placesearch_task(search, city):
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
				
		# print(res["name"])
	return detail_places


@task()
def yellowsearch_task(search, city):
	yellow_search = requests.get('http://api2.yp.com/listings/v1/search?searchloc=%s&term=%s&format=json&sort=name&listingcount=20&key=5t4k08tttp' %(city, search))
	return yellow_search.json()