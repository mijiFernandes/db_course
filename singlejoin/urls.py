from django.urls import path
from . import views

urlpatterns = [
    path('', views.singlejoin_main, name='singlejoin_main'),
    path('process/', views.join, name='join_process'),
    path('search/', views.singlejoin, name='singlejoin'),
    path('joinresult/', views.do_join, name='join_result')
]
