from django.urls import path

from . import views

urlpatterns = [
    path('', views.multijoin_main, name='multijoin_main'),
    path('<str:table_name>', views.multijoin, name='multijoin'),
]