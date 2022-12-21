from django.shortcuts import render, redirect
import pandas as pd
import MySQLdb
import json
import re


def main(request):
    return render(request, "main.html", {"is_db": request.session.get('host')})


def search(request):
    if request.method == "POST":
        table_name = request.POST.get('table')
        db = MySQLdb.connect(host=request.POST.get('host'),
                             user=request.POST.get('user'),
                             passwd=request.POST.get('passwd'),
                             db=request.POST.get('db'),
                             port=request.POST.get('port'))

        cur = db.cursor()
        if cur.execute(f"SHOW TABLES LIKE '{table_name}';") == 0:
            return render(request, "search.html", {"data_set": [f"Table '{table_name}' doesn't exist"]})
        cur.execute(f"SELECT * FROM {table_name}")
        db.close()
        return render(request, "search.html", {"data_set": cur.fetchall(), "is_db": request.session.get('host')})
    else:
        return render(request, "search.html", {"is_db": request.session.get('host')})


def db(request):
    if request.method == "POST":
        request.session['host'] = request.POST.get('host')
        request.session['user'] = request.POST.get('user')
        request.session['passwd'] = request.POST.get('passwd')
        request.session['db'] = request.POST.get('db')
        request.session['port'] = int(request.POST.get('port'))

        db = MySQLdb.connect(host=request.POST.get('host'),
                             user=request.POST.get('user'),
                             passwd=request.POST.get('passwd'),
                             db=request.POST.get('db'),
                             port=int(request.POST.get('port')))

        cur = db.cursor()
        cur.execute("""CREATE TABLE IF NOT EXISTS `TABLE_COUNTS` (
        `ID` INT PRIMARY KEY auto_increment NOT NULL,
        `TABLE_NAME` text COLLATE utf8_bin DEFAULT NULL,
        `COUNTS` int(11) DEFAULT NULL,
        `SCAN` boolean DEFAULT FALSE,
        `KEY_LIST` text COLLATE utf8_bin DEFAULT NULL,
        `ATTRIBUTES` text COLLATE utf8_bin DEFAULT NULL,
        `REPRESENTATIVES` text COLLATE utf8_bin DEFAULT NULL,
        `REPRESENTATIVE_KEY` text COLLATE utf8_bin DEFAULT NULL
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_bin;""")

        db.commit()
    return render(request, "db.html", {"is_db": request.session.get('host')})


def undb(request):
    del request.session['host']
    del request.session['user']
    del request.session['passwd']
    del request.session['db']
    del request.session['port']

    return render(request, "undb.html", {"is_db": request.session.get('host')})


def csv(request):
    if request.method == "POST":
        db = MySQLdb.connect(host=request.session.get('host'),
                             user=request.session.get('user'),
                             passwd=request.session.get('passwd'),
                             db=request.session.get('db'),
                             port=request.session.get('port'))

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

        representatives = {}
        representative_key = {}
        cur.execute(f"DESC {table_name}")
        for i in cur.fetchall():
            attributes.append(i[0])
            representatives[i[0]] = None
            representative_key[i[0]] = None

        sql = f"""INSERT INTO `TABLE_COUNTS` (`TABLE_NAME`, `COUNTS`, `SCAN`, `KEY_LIST`, `ATTRIBUTES`, 
        `REPRESENTATIVES`, `REPRESENTATIVE_KEY`) VALUES (
        '{table_name}', {cur.execute(f"SELECT * FROM {table_name}")}, '0', 
        '{json.dumps(key_list)}', '{json.dumps(attributes)}',
        '{json.dumps(representatives)}', '{json.dumps(representative_key)}');"""
        cur.execute(sql)
        db.commit()
        db.close()

    return render(request, "csv.html", {"is_db": request.session.get('host')})


def list_to_scan(request):
    db = MySQLdb.connect(host=request.session.get('host'),
                         user=request.session.get('user'),
                         passwd=request.session.get('passwd'),
                         db=request.session.get('db'),
                         port=int(request.session.get('port')))

    cur = db.cursor()
    sql = """SELECT * FROM `TABLE_COUNTS`"""
    cur.execute(sql)
    table_list = []
    tables = cur.fetchall()
    for table in tables:
        table_list.append({"id": table[0],
         "table_name": table[1],
         "records": table[2],
         "scan": table[3],
         "key_list": table[4],
         "attributes": table[5]})
    context = {"table_list": table_list, "is_db": request.session.get('host')}
    return render(request, "scan_list.html", context)


def list_to_modify(request):
    db = MySQLdb.connect(host=request.session.get('host'),
                         user=request.session.get('user'),
                         passwd=request.session.get('passwd'),
                         db=request.session.get('db'),
                         port=request.session.get('port'))

    cur = db.cursor()
    sql = """SELECT * FROM `TABLE_COUNTS`"""
    cur.execute(sql)
    table_list = []
    tables = cur.fetchall()
    for table in tables:
        table_list.append({"id": table[0],
                           "table_name": table[1],
                           "records": table[2],
                           "scan": table[3],
                           "key_list": table[4],
                           "attributes": table[5]})
    context = {"table_list": table_list, "is_db": request.session.get('host')}
    return render(request, "modify_list.html", context)


def table_delete(request, table_id):
    db = MySQLdb.connect(host=request.session.get('host'),
                         user=request.session.get('user'),
                         passwd=request.session.get('passwd'),
                         db=request.session.get('db'),
                         port=request.session.get('port'))

    cur = db.cursor()
    cur.execute(f"""SELECT * FROM TABLE_COUNTS 
                    WHERE id={table_id}""")
    temp = cur.fetchone()
    table = {"id": temp[0],
         "table_name": temp[1],
         "records": temp[2],
         "scan": temp[3],
         "key_list": temp[4],
         "attributes": temp[5]}
    cur.execute(f"DROP TABLE {table['table_name']};")
    cur.execute(f"DELETE FROM TABLE_COUNTS WHERE `id`={table_id};")
    db.commit()
    db.close()

    return redirect('modify')


def detail(request, table_id):
    db = MySQLdb.connect(host=request.session.get('host'),
                         user=request.session.get('user'),
                         passwd=request.session.get('passwd'),
                         db=request.session.get('db'),
                         port=request.session.get('port'))

    cur = db.cursor()
    regEx = "[^a-zA-Z0-9\u3130-\u318F\uAC00-\uD7AF\s]"
    cur.execute(f"""SELECT * FROM TABLE_COUNTS 
                    WHERE id={table_id}""")
    temp = cur.fetchone()

    table = {"id": temp[0],
         "table_name": temp[1],
         "records": temp[2],
         "scan": temp[3],
         "key_list": temp[4],
         "attributes": temp[5],
         "representatives": temp[6],
         "representative_key": temp[7]}
    key_list = json.decoder.JSONDecoder().decode(table['key_list'])
    if request.method == "POST":
        rows = []

        cur.execute(f"DESC {table['table_name']}")
        for i in cur.fetchall():
            cur.execute(f"SELECT COUNT(`{i[0]}`) FROM {table['table_name']}")
            no_null = cur.fetchone()
            row = [i[0], i[1], table['records'] - no_null[0],
                   float(round((table['records'] - no_null[0]) / table['records'], 8))]

            # float(round((table['records'] - no_null[0] / table['records']), 8))

            cur.execute(f"SELECT COUNT(DISTINCT `{i[0]}`) FROM {table['table_name']}")

            distinct = cur.fetchone()[0]
            row.append(distinct)

            if "int" in row[1].lower():
                cur.execute(f"SELECT MAX({i[0]}) AS maximum, MIN({i[0]}) AS minimum FROM {table['table_name']};")
                maxMin = cur.fetchall()

                # Append max and min values
                row.append(maxMin[0][0])
                row.append(maxMin[0][1])

                cur.execute(f"SELECT COUNT(*) FROM {table['table_name']} WHERE {i[0]} = 0;")
                zeroValue = cur.fetchall()

                # Append zero value count
                row.append(zeroValue[0][0])
                row.append(float(round(zeroValue[0][0] / table['records'], 8)))

            else:
                count = 0
                # Converts record to string. This is to ensure null values and numbers are parsed as strings
                cur.execute(f"SELECT {i[0]} FROM {table['table_name']};")
                colVal = list(cur.fetchall())
                for j in colVal:
                    # Converts record to string. This is to ensure null values and numbers are parsed as strings
                    string = str(j[0])

                    # Compare with regular expression
                    result = re.search(regEx, string)

                    # If found special character, increase count
                    if result:
                        count += 1
                row.append(count)
                row.append(float(round(count / table['records'], 8)))

            representatives = dict(json.decoder.JSONDecoder().decode(table['representatives']))

            if not representatives[f"{i[0]}"]:
                row.append("-")
            else:
                row.append(representatives[f"{i[0]}"])

            if distinct / table['records'] >= 0.9:
                row.append("O")
            else:
                row.append("X")
            rows.append(row)

            representative_key = dict(json.decoder.JSONDecoder().decode(table['representative_key']))

            if not representative_key[f"{i[0]}"]:
                row.append("-")
            else:
                row.append(representative_key[f"{i[0]}"])


        cur.execute(f"""UPDATE TABLE_COUNTS SET `scan`='1' WHERE `id` = {table_id};""")
        db.commit()

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
    db = MySQLdb.connect(host=request.session.get('host'),
                         user=request.session.get('user'),
                         passwd=request.session.get('passwd'),
                         db=request.session.get('db'),
                         port=request.session.get('port'))

    cur = db.cursor()
    cur.execute(f"""SELECT * FROM TABLE_COUNTS 
                    WHERE id={table_id}""")

    regEx = "[^a-zA-Z0-9\u3130-\u318F\uAC00-\uD7AF\s]"
    temp = cur.fetchone()
    table = {"id": temp[0],
             "table_name": temp[1],
             "records": temp[2],
             "scan": temp[3],
             "key_list": temp[4],
             "attributes": temp[5],
             "representatives": temp[6],
             "representative_key": temp[7]}
    key_list = json.decoder.JSONDecoder().decode(table['key_list'])
    rows = []

    if request.method == "POST":
        cur.execute(f"ALTER TABLE {table['table_name']} DROP COLUMN {request.POST.get('attribute')}")
        temp = list(json.decoder.JSONDecoder().decode(table["attributes"]))
        for attr in temp:
            if attr == request.POST.get('attribute'):
                temp.remove(request.POST.get('attribute'))
                cur.execute(f"""UPDATE TABLE_COUNTS SET ATTRIBUTES = '{json.dumps(temp)}' WHERE id = {table["id"]};""")
                db.commit()
                break

    cur.execute(f"DESC {table['table_name']}")
    for i in cur.fetchall():
        cur.execute(f"SELECT COUNT(`{i[0]}`) FROM {table['table_name']}")
        no_null = cur.fetchone()
        row = [i[0], i[1], table['records'] - no_null[0],
               (table['records'] - no_null[0]) / table['records']]
        cur.execute(f"SELECT COUNT(DISTINCT `{i[0]}`) FROM {table['table_name']}")
        distinct = cur.fetchone()[0]
        row.append(distinct)

        if "int" in row[1].lower():
            cur.execute(f"SELECT MAX({i[0]}) AS maximum, MIN({i[0]}) AS minimum FROM {table['table_name']};")
            maxMin = cur.fetchall()

            # Append max and min values
            row.append(maxMin[0][0])
            row.append(maxMin[0][1])

            cur.execute(f"SELECT COUNT(*) FROM {table['table_name']} WHERE {i[0]} = 0;")
            zeroValue = cur.fetchall()

            # Append zero value count
            row.append(zeroValue[0][0])
            row.append(float(round(zeroValue[0][0] / table['records'], 8)))

        else:
            count = 0
            # Converts record to string. This is to ensure null values and numbers are parsed as strings
            cur.execute(f"SELECT {i[0]} FROM {table['table_name']};")
            colVal = list(cur.fetchall())
            for j in colVal:
                # Converts record to string. This is to ensure null values and numbers are parsed as strings
                string = str(j[0])

                # Compare with regular expression
                result = re.search(regEx, string)

                # If found special character, increase count
                if result:
                    count += 1
            row.append(count)
            row.append(float(round(count / table['records'], 8)))

        representatives = dict(json.decoder.JSONDecoder().decode(table['representatives']))

        if not representatives[f"{i[0]}"]:
            row.append("-")
        else:
            row.append(representatives[f"{i[0]}"])

        if distinct / table['records'] >= 0.9:
            row.append("O")
        else:
            row.append("X")
        rows.append(row)

        representative_key = dict(json.decoder.JSONDecoder().decode(table['representative_key']))

        if not representative_key[f"{i[0]}"]:
            row.append("-")
        else:
            row.append(representative_key[f"{i[0]}"])

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


