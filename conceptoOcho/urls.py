"""conceptoOcho URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.11/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import url
from django.contrib import admin
from main import views

urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(r'^$', views.index, name='index'),    
    url(r'^check/$', views.check, name='check'),   
    url(r'^filter/$', views.filter, name='filter'),   
    url(r'^places/$', views.place_status, name='places'),   
    url(r'^yellow/$', views.yellow_status, name='yellow'),   
    url(r'^ajax_yellow/$', views.yellow_ajax, name='yellow_ajax'),
    url(r'^ajax_filter/$', views.filter_ajax, name='filter_ajax'),
    url(r'^ajax_get_info/$', views.get_info, name='get_info_ajax'),
    url(r'^ajax_excel/$', views.make_excel, name='excel_ajax'),
    url(r'^files/(?P<filename>)', views.excel_download),
]
