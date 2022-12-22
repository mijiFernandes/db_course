from django.urls import path
from . import views

urlpatterns = [
    path('', views.singlejoin_main, name='singlejoin_main'),
    path('search/', views.singlejoin, name='singlejoin'),
    path('process/', views.join, name='singlejoin_start'),
    path('result/', views.check_result, name='single_result_table'),
    path('download/', views.download_view, name='single_download'),
    
]
