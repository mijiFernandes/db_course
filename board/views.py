from django.shortcuts import render
from django.http import HttpResponse
from .models import Entity
import pandas as pd
import requests


def index(request):
    entity = Entity.objects.raw("SELECT * FROM board_entity WHERE id=1")

    url = entity[0].table.__str__()
    s = requests.get(url).content
    c = pd.read_csv(s)

    return HttpResponse(c)
