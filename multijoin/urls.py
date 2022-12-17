from django.urls import path

from . import views

urlpatterns = [
    path('', views.multijoin_main, name='multijoin_main'),
    path('join/', views.multijoin, name='multijoin'),
]