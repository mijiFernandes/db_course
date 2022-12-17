"""mysite URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.1/topics/http/urls/
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
from django.urls import path, include

from board.views import *

urlpatterns = [
    path('', main, name='main'),
    path('search/', search, name='search'),
    path('db/', db, name='db'),
    path('undb/', undb, name='undb'),
    path('csv/', csv, name='csv'),
    path('schema/', schema, name='schema'),
    path('table_list/',list_to_scan, name='scan'),
    path('table_list_modify/',list_to_modify, name='modify'),
    path('table_list/<int:table_id>/', detail),
    path('admin/', admin.site.urls),
    path('multijoin/', include('multijoin.urls')),
]
