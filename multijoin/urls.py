from django.urls import path

from . import views

urlpatterns = [
    path('', views.multijoin_main, name='multijoin_main'),
    path('search/', views.multijoin, name='multijoin'),
    path('process/', views.join, name='multijoin_start'),
]