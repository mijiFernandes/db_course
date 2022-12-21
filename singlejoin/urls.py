from django.urls import path
from . import views

urlpatterns = [
    path('', views.singlejoin_main, name='singlejoin_main'),
    path('joinresult/', views.join, name='singlejoin_result'),
    path('<str:table_name>', views.singlejoin, name='singlejoin'),

]
