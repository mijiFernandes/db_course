from django.shortcuts import render, redirect
import pandas as pd
import MySQLdb
from .models import Table
import json


def main(request):
    return render(request, "main.html", {"is_db": request.session.get('host')})


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
        db.close()
        return render(request, "search.html", {"data_set": cur.fetchall(), "is_db": request.session.get('host')})
    else:
        return render(request, "search.html", {"is_db": request.session.get('host')})


def db(request):
    request.session['host'] = request.POST.get('host')
    request.session['user'] = request.POST.get('user')
    request.session['passwd'] = request.POST.get('passwd')
    request.session['db'] = request.POST.get('db')

    return render(request, "db.html", {"is_db": request.session.get('host')})


def undb(request):
    del request.session['host']
    del request.session['user']
    del request.session['passwd']
    del request.session['db']

    return render(request, "undb.html", {"is_db": request.session.get('host')})


def csv(request):
    if request.method == "POST":
        db = MySQLdb.connect(host=request.session.get('host'),
                             user=request.session.get('user'),
                             passwd=request.session.get('passwd'),
                             db=request.session.get('db'))

        cur = db.cursor()
        data = pd.read_csv(request.FILES['csv_file'], sep=',', header=None, keep_default_na=False)

        temp = data.values

        table_name = str(request.FILES['csv_file'])[0:-4]
        sql = "CREATE TABLE IF NOT EXISTS `"
        sql += table_name + "` ("

        key_list = ["전화번호", "이메일주소", "IP주소", "차량번호", "주민등록번호"]
        attributes = []

        for i in range(0, len(temp[0])):
            j = 1
            while not temp[j][i]:
                j += 1
            try:
                int(temp[j][i])
                sql += f"`{temp[0][i]}`int(11) DEFAULT NULL, "
            except:
                sql += f"`{temp[0][i]}`text COLLATE utf8_bin DEFAULT NULL, "
        sql = sql[:-2] + ") ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_bin;"
        cur.execute(sql)
        db.commit()

        sql = "INSERT INTO `"
        sql += table_name + "` ("

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

        cur.execute(f"DESC {table_name}")
        for i in cur.fetchall():
            attributes.append(i[0])

        t = Table(table_name=table_name, key_list=json.dumps(key_list),
                  records=cur.execute(f"SELECT * FROM {table_name}"),
                  attributes=attributes)
        t.save()
        db.close()

    return render(request, "csv.html", {"is_db": request.session.get('host')})


def list_to_scan(request):
    table_list = Table.objects.order_by('table_name')
    context = {"table_list": table_list, "is_db": request.session.get('host')}
    return render(request, "scan_list.html", context)


def list_to_modify(request):
    table_list = Table.objects.order_by('table_name')
    context = {"table_list": table_list, "is_db": request.session.get('host')}
    return render(request, "modify_list.html", context)


def table_delete(request, table_id):
    table = Table.objects.get(id=table_id)

    db = MySQLdb.connect(host=request.session.get('host'),
                         user=request.session.get('user'),
                         passwd=request.session.get('passwd'),
                         db=request.session.get('db'))

    cur = db.cursor()
    cur.execute(f"DROP TABLE {table.table_name}")
    db.close()
    table.delete()

    return redirect('modify')


def detail(request, table_id):
    table = Table.objects.get(id=table_id)
    key_list = json.decoder.JSONDecoder().decode(table.key_list)
    if request.method == "POST":
        rows = []

        db = MySQLdb.connect(host=request.session.get('host'),
                             user=request.session.get('user'),
                             passwd=request.session.get('passwd'),
                             db=request.session.get('db'))

        cur = db.cursor()
        cur.execute(f"DESC {table.table_name}")
        for i in cur.fetchall():
            cur.execute(f"SELECT COUNT(`{i[0]}`) FROM {table.table_name}")
            no_null = cur.fetchone()
            row = [i[0], i[1], table.records - no_null[0],
                   (table.records - no_null[0]) / table.records]
            cur.execute(f"SELECT COUNT(DISTINCT `{i[0]}`) FROM {table.table_name}")
            distinct = cur.fetchone()[0]
            if distinct / table.records >= 0.9:
                row.append("O")
            else:
                row.append("X")
            rows.append(row)

        table.scan = True
        table.save()

        numeric = []
        categorical = []

        for row in rows:
            if "int" in row[1].lower():
                numeric.append(row)
            else:
                categorical.append(row)

        temp = cur.fetchall()

        context = {'table': table, "is_db": request.session.get('host'), "structure": temp,
                   "key_list": key_list, "numeric": numeric, "categorical": categorical}
        db.close()
    else:
        context = {'table': table, "is_db": request.session.get('host'), "structure": "", "key_list": key_list}

    return render(request, 'table_detail.html', context)


def modify(request, table_id):
    table = Table.objects.get(id=table_id)
    key_list = json.decoder.JSONDecoder().decode(table.key_list)
    rows = []

    db = MySQLdb.connect(host=request.session.get('host'),
                         user=request.session.get('user'),
                         passwd=request.session.get('passwd'),
                         db=request.session.get('db'))

    cur = db.cursor()

    if request.method == "POST":
        cur.execute(f"ALTER TABLE {table.table_name} DROP COLUMN {request.POST.get('attribute')}")

    cur.execute(f"DESC {table.table_name}")
    for i in cur.fetchall():
        cur.execute(f"SELECT COUNT(`{i[0]}`) FROM {table.table_name}")
        no_null = cur.fetchone()
        row = [i[0], i[1], table.records - no_null[0],
               (table.records - no_null[0]) / table.records]
        cur.execute(f"SELECT COUNT(DISTINCT `{i[0]}`) FROM {table.table_name}")
        distinct = cur.fetchone()[0]
        if distinct / table.records >= 0.9:
            row.append("O")
        else:
            row.append("X")
        rows.append(row)

    table.scan = True
    table.save()

    numeric = []
    categorical = []

    for row in rows:
        if "int" in row[1].lower():
            numeric.append(row)
        else:
            categorical.append(row)

    temp = cur.fetchall()

    context = {'table': table, "is_db": request.session.get('host'), "structure": temp,
               "key_list": key_list, "numeric": numeric, "categorical": categorical}
    db.close()
    return render(request, 'table_modify.html', context)


