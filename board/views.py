from django.shortcuts import render
import pandas as pd
import MySQLdb


def main(request):
    return render(request, "main.html", {"is_db": request.session.get('host')})


def search(request):
    if request.method == "POST":
        table_name = request.POST.get('table')
        # db = MySQLdb.connect(host=request.session.get('host'),
        #                      user=request.session.get('user'),
        #                      passwd=request.session.get('passwd'),
        #                      db=request.session.get('db'))
        db = MySQLdb.connect(host='localhost',
                             user='root',
                             passwd='yewon1108!',
                             db='db_final')

        cur = db.cursor()
        if cur.execute(f"SHOW TABLES LIKE '{table_name}'") == 0:
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
    return render(request, "csv.html", {"is_db": request.session.get('host')})


def schema(request):
    if request.method == "POST":
        table_schema = request.POST.get("schema")
        db = MySQLdb.connect(host=request.session.get('host'),
                             user=request.session.get('user'),
                             passwd=request.session.get('passwd'),
                             db='db_final')
        #                     # At first, there's no explicit db name.
        # dbname = request.session.get('db')
        cur = db.cursor()
        # cur.execute(f"CREATE DATABASE {dbname}")
        cur.execute(f"{table_schema}")
        # db.commit()
        db.close()
    return render(request, "schema.html", {"is_db": request.session.get('host')})
