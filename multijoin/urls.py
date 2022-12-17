from django.urls import path

from . import views

urlpatterns = [
    path('', views.multijoin, name='multijoin_main'),
]