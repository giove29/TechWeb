"""
URL configuration for modena_eventi project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include, re_path
from django.conf.urls import handler403, handler404
from .views import *

urlpatterns = [
    path('admin/', admin.site.urls, name="adminpage"),
    path('core/', include('core.urls')),
    path('users/', include('utenti.urls')),
    re_path(r'^$|^/$|^home/$', home_page, name='homepage'),
    re_path(r'^.*', resource_not_found_view, name='notfound'),
]
