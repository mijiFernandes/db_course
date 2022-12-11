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
        db.close()
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
    del request.session['host']
    del request.session['user']
    del request.session['passwd']
    del request.session['db']

    return render(request, "undb.html")


def csv(request):
    if request.method == "POST":
        db = MySQLdb.connect(host=request.session.get('host'),
                             user=request.session.get('user'),
                             passwd=request.session.get('passwd'),
                             db=request.session.get('db'))

        cur = db.cursor()
        data = pd.read_csv(request.FILES['csv_file'], sep=',', header=None)
        sql = "INSERT INTO `"
        sql += str(request.FILES['csv_file'])[0:-4] + "` ("

        temp = data.values
        for i in temp[0]:
            sql += f"`{i}`, "
        sql = sql[:-2] + ") VALUES "
        for i in range(1, len(temp)):
            sql += "("
            for j in temp[i]:
                sql += f"'{j}', "
            sql = sql[:-2] + "), "
        sql = sql[:-2] + ";"
        # print(sql)
        # cur.execute("""INSERT INTO `1_fitness_measurement`
        # (`PHONE_NUM`, `MAIL_ADDR`, `TEST_CNT`, `CENTER_NM`, `AGE_GBN`, `TEST_GBN`,
        # `TEST_AGE`, `INPUT_GBN`, `CERT_GBN`, `TEST_YMD`, `TEST_SEX`) VALUES
        # ('015-0019-9010', '04e8jlwv1qa6mxqrz2a@comcast.com', '2', 'KSPO송파', '성인', '일반', '29', '없음', '3등급', '20210908', 'M');""")
        cur.execute(sql)
        db.commit()
        db.close()
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
        db.commit()
        db.close()
    return render(request, "schema.html")
