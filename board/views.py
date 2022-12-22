from django.shortcuts import render, redirect
import pandas as pd
import MySQLdb
import json
import re
from mysite.common_assets import STANDARD_KEYS
from django.http import HttpResponse
import csv

regEx = "[^a-zA-Z0-9\u3130-\u318F\uAC00-\uD7AF\s]"
regEx2 = "[^0-9]"



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
    request.session['login'] = 0
    try:
        if request.method == "POST":
            request.session['host'] = request.POST.get('host')
            request.session['user'] = request.POST.get('user')
            request.session['passwd'] = request.POST.get('passwd')
            request.session['db'] = request.POST.get('db')
            request.session['port'] = int(request.POST.get('port')) if request.POST.get('port') is not None and request.POST.get('port') != '' else None

            db = MySQLdb.connect(host=request.POST.get('host'),
                                user=request.POST.get('user'),
                                passwd=request.POST.get('passwd'),
                                db=request.POST.get('db'),
                                port=int(request.POST.get('port')))
            request.session['login'] = 1
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

            cur.execute("""CREATE TABLE IF NOT EXISTS `REPRESENTATIVE_KEYS` (
                   `ID` INT PRIMARY KEY AUTO_INCREMENT NOT NULL,
                   `TABLE_NAME` TEXT COLLATE UTF8_BIN DEFAULT NULL,
                    `REPRESENTATIVE_KEY` TEXT COLLATE UTF8_BIN DEFAULT NULL
                    ) ENGINE=INNODB DEFAULT CHARSET=UTF8 COLLATE=UTF8_BIN;""")
            db.commit()

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
    if request.session['login'] == 1:
        del request.session['host']
        del request.session['user']
        del request.session['passwd']
        del request.session['db']
        request.session['login'] = 0
        del request.session['port']
    return render(request, "undb.html", {"login":0})
   

def final_result(request):
    return render(request, "final_result.html", {"is_db": request.session.get('host'),
                    "user": request.session.get('user'),
                    "passwd":request.session.get('passwd'),
                    "db":request.session.get('db'),
                    "login":request.session.get('login'),
                    "port":request.session.get('port'),})


def csv_register(request):
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
        
        # Representative key names(STANDARD_KEYS) have to be tracked
        key_list = STANDARD_KEYS
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

        sql = f"""INSERT INTO TABLE_COUNTS (`TABLE_NAME`, `COUNTS`, `SCAN`, `KEY_LIST`, `ATTRIBUTES`, 
        `REPRESENTATIVES`, `REPRESENTATIVE_KEY`) VALUES (
        '{table_name}', {cur.execute(f"SELECT * FROM {table_name}")}, '0', 
        '{json.dumps(key_list, ensure_ascii=False)}', '{json.dumps(attributes, ensure_ascii=False)}',
        '{json.dumps(representatives, ensure_ascii=False)}', '{json.dumps(representative_key, ensure_ascii=False)}');"""
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
    try:
        db = MySQLdb.connect(host=request.session.get('host'),
                            user=request.session.get('user'),
                            passwd=request.session.get('passwd'),
                            db=request.session.get('db'),
                            port=int(request.session.get('port')))

        cur = db.cursor()
        sql = """SELECT * FROM TABLE_COUNTS"""
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
        context = {"table_list": table_list, "is_db": request.session.get('host'),
                        "user": request.session.get('user'),
                        "passwd":request.session.get('passwd'),
                        "db":request.session.get('db'),
                        "login":request.session.get('login'),
                        "port":request.session.get('port'),}
    except:
        context = {"table_list": None, "is_db": request.session.get('host'),
                        "user": request.session.get('user'),
                        "passwd":request.session.get('passwd'),
                        "db":request.session.get('db'),
                        "login":request.session.get('login'),
                        "port":request.session.get('port'),}
    return render(request, "scan_list.html", context)


def list_to_modify(request):
    try:
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
        context = {"table_list": table_list, "is_db": request.session.get('host'),
                        "user": request.session.get('user'),
                        "passwd":request.session.get('passwd'),
                        "db":request.session.get('db'),
                        "login":request.session.get('login'),
                        "port":request.session.get('port'),}
    except:
        context = {"table_list": None, "is_db": request.session.get('host'),
                        "user": request.session.get('user'),
                        "passwd":request.session.get('passwd'),
                        "db":request.session.get('db'),
                        "login":request.session.get('login'),
                        "port":request.session.get('port'),}
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
    cur.execute(f"DELETE FROM representative_keys WHERE `TABLE_NAME` = '{table['table_name']}';")
    db.commit()
    db.close()

    return redirect('modify')


def download_num(request, table_id):
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
         "attributes": temp[5],
         "representatives": temp[6],
         "representative_key": temp[7]}
    response = HttpResponse(content_type='text/csv',
                            headers={'Content-Disposition': f'attachment; filename="numeric_data_of_{table["table_name"]}.csv"'})
    response.write(u''.encode('utf-8-sig'))
    writer = csv.writer(response)
    writer.writerow(['속성명', '데이터 타입', 'Null 레코드 수', 'Null 레코드 비율', '상이 수치값',
                       '최댓값', '최솟값', '0 레코드 수', '0 레코드 비율', '대표 속성', '결합키 후보', '대표 결합키'])

    rows = []

    cur.execute(f"DESC {table['table_name']}")
    for i in cur.fetchall():
        cur.execute(f"SELECT COUNT(`{i[0]}`) FROM {table['table_name']}")
        no_null = cur.fetchone()
        row = [i[0], i[1], table['records'] - no_null[0],
               float(round((table['records'] - no_null[0]) / table['records'], 8))]

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

    for row in rows:
        if "int" in row[1].lower():
            writer.writerow(row)

    db.close()

    return response


def download_cat(request, table_id):
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
         "attributes": temp[5],
         "representatives": temp[6],
         "representative_key": temp[7]}
    response = HttpResponse(content_type='text/csv',
                            headers={'Content-Disposition': f'attachment; filename="categorical_data_of_{table["table_name"]}.csv"'})
    response.write(u''.encode('utf-8-sig'))
    writer = csv.writer(response)
    writer.writerow(['속성명', '데이터 타입', 'Null 레코드 수', 'Null 레코드 비율', '상이 범주값',
                       '특수문자 포함 레코드 수', '특수문자 포함 레코드 비율', '대표 속성', '결합키 후보', '대표 결합키'])

    rows = []

    cur.execute(f"DESC {table['table_name']}")
    for i in cur.fetchall():
        cur.execute(f"SELECT COUNT(`{i[0]}`) FROM {table['table_name']}")
        no_null = cur.fetchone()
        row = [i[0], i[1], table['records'] - no_null[0],
               float(round((table['records'] - no_null[0]) / table['records'], 8))]

        cur.execute(f"SELECT COUNT(DISTINCT `{i[0]}`) FROM {table['table_name']}")

        distinct = cur.fetchone()[0]
        row.append(distinct)

        if "int" in row[1].lower():
            continue
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

    categorical = []

    for row in rows:
        if "int" in row[1].lower():
            continue
        else:
            categorical.append(row)
            writer.writerow(row)

    db.close()

    return response

def detail(request, table_id):
    db = MySQLdb.connect(host=request.session.get('host'),
                        user=request.session.get('user'),
                        passwd=request.session.get('passwd'),
                        db=request.session.get('db'),
                        port=request.session.get('port'),)
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
    if request.method == "POST" or table["scan"]:
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

        if request.method == "POST":
            representative_key = dict(json.decoder.JSONDecoder().decode(table['representative_key']))
            representative_key_str = '"' + str(representative_key) + '"'

            sqlQuery = "INSERT INTO representative_keys VALUES (" + str(table["id"]) + ", '" + str(
                table["table_name"]) + "', " + representative_key_str + ");"

            cur.execute(sqlQuery)

            cur.execute(f"""UPDATE TABLE_COUNTS SET `scan`='1' WHERE `id` = {table_id};""")
            db.commit()
            table["scan"] = True

        numeric = []
        categorical = []

        for row in rows:
            if "int" in row[1].lower():
                numeric.append(row)
            else:
                categorical.append(row)
        context = {'table': table, "is_db": request.session.get('host'),
                    "user": request.session.get('user'),
                    "passwd":request.session.get('passwd'),
                    "db":request.session.get('db'),
                    "login":request.session.get('login'),
                    "port":request.session.get('port'),
                   "key_list": key_list, "numeric": numeric, "categorical": categorical}
        db.close()
    else:

        context = {'table': table, "is_db": request.session.get('host'),
                    "user": request.session.get('user'),
                    "passwd":request.session.get('passwd'),
                    "db":request.session.get('db'),
                    "login":request.session.get('login'),
                    "port":request.session.get('port'), "structure": "", "key_list": key_list}

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

    if request.method == "POST" and request.POST.get('delete'):
        cur.execute(f"ALTER TABLE {table['table_name']} DROP COLUMN {request.POST.get('delete')}")
        attrs = list(json.decoder.JSONDecoder().decode(table["attributes"]))
        for attr in attrs:
            if attr == request.POST.get('delete'):
                attrs.remove(request.POST.get('delete'))
                cur.execute(f"""UPDATE TABLE_COUNTS 
                SET ATTRIBUTES = '{json.dumps(attrs, ensure_ascii=False)}' WHERE id = {table["id"]};""")
                db.commit()
                break

        attrs = dict(json.decoder.JSONDecoder().decode(table["representatives"]))

        for attr in attrs:
            if attr == request.POST.get('delete'):
                del attrs[attr]
                cur.execute(f"""UPDATE TABLE_COUNTS
                SET representatives = '{json.dumps(attrs, ensure_ascii=False)}' WHERE id = {table["id"]};""")
                db.commit()
                break

        attrs = dict(json.decoder.JSONDecoder().decode(table["representative_key"]))
        for attr in attrs:
            if attr == request.POST.get('delete'):
                del attrs[attr]
                cur.execute(f"""UPDATE TABLE_COUNTS
                SET representative_key = '{json.dumps(attrs, ensure_ascii=False)}' WHERE id = {table["id"]};""")
                cur.execute(f"""UPDATE representative_keys
                SET representative_key = '{json.dumps(attrs, ensure_ascii=False)}' WHERE id = {table["id"]};""")
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

        representative_key = dict(json.decoder.JSONDecoder().decode(table['representative_key']))

        if distinct / table['records'] >= 0.9:
            if not representative_key[f"{i[0]}"]:
                row.append({"candidate": "O", "key": "-"})
            else:
                row.append({"candidate": "O", "key": representative_key[f"{i[0]}"]})
        else:
            row.append({"candidate": "X", "key": None})
        rows.append(row)

    numeric = []
    categorical = []

    for row in rows:
        if "int" in row[1].lower():
            numeric.append(row)
        else:
            categorical.append(row)

    if request.method == "POST" and request.POST.get('num_edit'):
        representatives = dict(json.decoder.JSONDecoder().decode(table["representatives"]))
        representative_key = dict(json.decoder.JSONDecoder().decode(table["representative_key"]))

        for i in range(0, len(numeric)):
            if not request.POST.get(str(i)):
                representatives[numeric[i][0]] = "-"
            else:
                representatives[numeric[i][0]] = request.POST.get(str(i))

            representative_key[numeric[i][0]] = request.POST.get(f"representative_key{i}")

            cur.execute(f"""UPDATE TABLE_COUNTS 
            SET representatives = '{json.dumps(representatives, ensure_ascii=False)}' WHERE id = {table["id"]};""")
            cur.execute(f"""UPDATE TABLE_COUNTS 
            SET representative_key = '{json.dumps(representative_key, ensure_ascii=False)}' WHERE id = {table["id"]};""")
            cur.execute(f"""UPDATE representative_keys 
            SET REPRESENTATIVE_KEY = '{json.dumps(representative_key, ensure_ascii=False)}' WHERE id = {table["id"]};""")

            if request.POST.get(f"type{i}") == "change":
                try:
                    cur.execute(f"ALTER TABLE {table['table_name']} MODIFY {numeric[i][0]} TEXT;")
                    db.commit()
                except:
                    pass

            db.commit()
        return redirect('modify')

    if request.method == "POST" and request.POST.get('cat_edit'):
        representatives = dict(json.decoder.JSONDecoder().decode(table["representatives"]))
        representative_key = dict(json.decoder.JSONDecoder().decode(table["representative_key"]))

        for i in range(0, len(categorical)):
            if not request.POST.get(str(i)):
                representatives[categorical[i][0]] = "-"
            else:
                representatives[categorical[i][0]] = request.POST.get(str(i))

            representative_key[categorical[i][0]] = request.POST.get(f"representative_key{i}")

            cur.execute(f"""UPDATE TABLE_COUNTS 
            SET representatives = '{json.dumps(representatives, ensure_ascii=False)}' WHERE id = {table["id"]};""")
            cur.execute(f"""UPDATE TABLE_COUNTS 
            SET representative_key = '{json.dumps(representative_key, ensure_ascii=False)}' WHERE id = {table["id"]};""")
            cur.execute(f"""UPDATE representative_keys 
            SET REPRESENTATIVE_KEY = '{json.dumps(representative_key, ensure_ascii=False)}' WHERE id = {table["id"]};""")
            db.commit()

            count = 0
            if request.POST.get(f"type{i}") == "change":
                try:
                    cur.execute(f"SELECT {categorical[i][0]} FROM {table['table_name']}")
                    data = cur.fetchall()
                    for j in data:
                        if not re.search(regEx2, j[0]):
                            count += 1
                    if count == len(data):
                        cur.execute(f"ALTER TABLE {table['table_name']} MODIFY {categorical[i][0]} INT;")
                        db.commit()
                except:
                    pass
            db.commit()
        return redirect('modify')

    context = {'table': table, "is_db": request.session.get('host'),
                    "user": request.session.get('user'),
                    "passwd":request.session.get('passwd'),
                    "db":request.session.get('db'),
                    "login":request.session.get('login'),
                    "port":request.session.get('port'),
               "key_list": key_list, "numeric": numeric, "categorical": categorical}
    db.close()
    return render(request, 'table_modify.html', context)

