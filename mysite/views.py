from django.shortcuts import render
import pandas as pd


def main(request):
    return render(request, "main.html")


def search(request):
    return render(request, "search.html")


def db(request):
    return render(request, "db.html")


def undb(request):
    return render(request, "undb.html")


def csv(request):
    return render(request, "csv.html")


def schema(request):
    return render(request, "schema.html")