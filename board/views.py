from django.shortcuts import render
import pandas as pd
import MySQLdb


def main(request):
    return render(request, "main.html")


def search(request):
    if request.method == "POST":
        table_name = request.POST.get('table')
        db = MySQLdb.connect(host=request.session.get('host'),
                             user=request.session.get('user'),
                             passwd=request.session.get('passwd'),
                             db=request.session.get('db'))

        cur = db.cursor()
        if cur.execute(f"SHOW TABLES LIKE '{table_name}';") == 0:
            return render(request, "search.html", {"data_set": [f"Table '{table_name}' doesn't exist"]})
        cur.execute(f"SELECT * FROM {table_name}")
        return render(request, "search.html", {"data_set": cur.fetchall()})
    else:
        return render(request, "search.html")


def db(request):
    request.session['host'] = request.POST.get('host')
    request.session['user'] = request.POST.get('user')
    request.session['passwd'] = request.POST.get('passwd')
    request.session['db'] = request.POST.get('db')

    return render(request, "db.html")


def undb(request):

    # print(request.session.get('host'))
    # print(request.session.get('user'))
    # print(request.session.get('passwd'))
    # print(request.session.get('db'))
    del request.session['host']
    del request.session['user']
    del request.session['passwd']
    del request.session['db']

    return render(request, "undb.html")


def csv(request):
    return render(request, "csv.html")


def schema(request):
    if request.method == "POST":
        table_schema = request.POST.get("schema")
        db = MySQLdb.connect(host=request.session.get('host'),
                             user=request.session.get('user'),
                             passwd=request.session.get('passwd'),
                             db=request.session.get('db'))

        cur = db.cursor()
        cur.execute(f"{table_schema}")
    return render(request, "schema.html")
