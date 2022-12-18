from django.shortcuts import render
import pandas as pd
import MySQLdb
from .models import Table



def search(request):
    if request.method == "POST":
        table_name = request.POST.get('table')
        db = MySQLdb.connect(host=request.session.get('host'),
                                user=request.session.get('user'),
                                passwd=request.session.get('passwd'),
                                db=request.session.get('db'),
                                port=request.session.get('port'),)
        
        cur = db.cursor()
        if cur.execute(f"SHOW TABLES LIKE '{table_name}'") == 0:
            return render(request, "search.html", {"data_set": [f"Table '{table_name}' doesn't exist"]})
        cur.execute(f"SELECT * FROM {table_name}")
        db.close()
        return render(request, "search.html", {"data_set": cur.fetchall(), "is_db": request.session.get('host')})
    else:
        return render(request, "search.html", {"is_db": request.session.get('host')})


def main(request):
    return render(request, "index.html", 
                  {"is_db": request.session.get('host'),
                    "user": request.session.get('user'),
                    "passwd":request.session.get('passwd'),
                    "db":request.session.get('db'),
                    "login":request.session.get('login'),
                    "port":request.session.get('port'),})


def db(request):
    if (request.session.get('login')==1):
        return render(request, "db.html", {"is_db": request.session.get('host'),
                    "user": request.session.get('user'),
                    "passwd":request.session.get('passwd'),
                    "db":request.session.get('db'),
                    "login":request.session.get('login'),
                    "port":request.session.get('port'),})
    request.session['host'] = request.POST.get('host')
    request.session['user'] = request.POST.get('user')
    request.session['passwd'] = request.POST.get('passwd')
    request.session['db'] = request.POST.get('db')
    request.session['port'] = int(request.POST.get('port')) if request.POST.get('port') is not None else None
    request.session['login'] = 0
    try:
        if request.method == "POST":
            db = MySQLdb.connect(host=request.session.get('host'),
                                user=request.session.get('user'),
                                passwd=request.session.get('passwd'),
                                db=request.session.get('db'),
                                port=request.session.get('port'),)
            request.session['login'] = 1
            if (not request.session.get('host') or \
                not request.session.get('user') or \
                not request.session.get('passwd') or \
                not request.session.get('db') or \
                not request.session.get('port')):
                request.session['login'] = -1
            db.close()  
    except MySQLdb.Error as e:
        request.session['login'] = -1
    except TypeError as e:
        request.session['login'] = -1

    return render(request, "db.html", {"is_db": request.session.get('host'),
                    "user": request.session.get('user'),
                    "passwd":request.session.get('passwd'),
                    "db":request.session.get('db'),
                    "login":request.session.get('login'),
                    "port":request.session.get('port'),})


def undb(request):
    del request.session['host']
    del request.session['user']
    del request.session['passwd']
    del request.session['db']
    del request.session['login']
    del request.session['port']
    return render(request, "undb.html", {"login":0})


def csv(request):
    if request.method == "POST":
        db = MySQLdb.connect(host=request.session.get('host'),
                                user=request.session.get('user'),
                                passwd=request.session.get('passwd'),
                                db=request.session.get('db'),
                                port=request.session.get('port'),)
        cur = db.cursor()
        data = pd.read_csv(request.FILES['csv_file'], sep=',', header=None, keep_default_na=False)
        sql = "INSERT INTO `"
        sql += str(request.FILES['csv_file'])[0:-4] + "` ("

        temp = data.values
        for i in temp[0]:
            sql += f"`{i}`, "
        sql = sql[:-2] + ") VALUES "
        for i in range(1, len(temp)):
            sql += "("
            for j in temp[i]:
                if j == "":
                    sql += f"NULL, "
                else:
                    sql += f"'{j}', "
            sql = sql[:-2] + "), "
        sql = sql[:-2] + ";"
        cur.execute(sql)
        db.commit()
        db.close()
    return render(request, "csv.html", {"is_db": request.session.get('host'),
                    "user": request.session.get('user'),
                    "passwd":request.session.get('passwd'),
                    "db":request.session.get('db'),
                    "login":request.session.get('login'),
                    "port":request.session.get('port'),})


def list_to_scan(request):
    table_list = Table.objects.order_by('table_name')
    context = {"table_list": table_list, "is_db": request.session.get('host')}
    return render(request, "scan_list.html", context)


def list_to_modify(request):
    table_list = Table.objects.order_by('table_name')
    context = {"table_list": table_list, "is_db": request.session.get('host')}
    return render(request, "modify_list.html", context)


def detail(request, table_id):
    table = Table.objects.get(id=table_id)
    if request.method == "POST":
        db = MySQLdb.connect(host=request.session.get('host'),
                                user=request.session.get('user'),
                                passwd=request.session.get('passwd'),
                                db=request.session.get('db'),
                                port=request.session.get('port'),)

        cur = db.cursor()
        cur.execute(f"desc {table.table_name};")

        table.scan = True
        table.save()

        context = {'table': table, "is_db": request.session.get('host'), "structure": cur.fetchall()}
        db.close()
    else:
        context = {'table': table, "is_db": request.session.get('host'), "structure": ""}

    return render(request, 'table_detail.html', context)


def schema(request):
    if request.method == "POST":
        table_schema = request.POST.get("schema")
        table_name = request.POST.get("table_name")

        t = Table(table_name=table_name)
        t.save()

        db = MySQLdb.connect(host=request.session.get('host'),
                                user=request.session.get('user'),
                                passwd=request.session.get('passwd'),
                                db=request.session.get('db'),
                                port=request.session.get('port'),)

        cur = db.cursor()
        cur.execute(f"{table_schema}")
        db.close()
    return render(request, "schema.html", {"is_db": request.session.get('host')})