from django.shortcuts import render
from mysite.common_assets import STANDARD_KEYS, REPRESENTATIVE_PROPS
import MySQLdb
from board.views import undb
import json
import numpy as np
import pandas as pd

# Create your views here.

def singlejoin_main(request):
    try:
        db = MySQLdb.connect(host=request.session.get('host'),
                             user=request.session.get('user'),
                             passwd=request.session.get('passwd'),
                             db=request.session.get('db'),
                             port=request.session.get('port'), )

        cur = db.cursor()

        # DELETED deprecated python implementation

        # Representative property should be chosen before join
        # dict_s = json.dumps({"전화번호":"PHONE_NUM", "이메일주소":"MAIL_ADDR"}, ensure_ascii=False)
        # cur.execute(f"""CREATE TABLE IF NOT EXISTS REPRESENTATIVE_KEY AS
        #             select distinct c.table_name, '{dict_s}' as RKEY from information_schema.columns as c
        #             where table_schema='{request.session.get('db')}' and
        #                 c.table_name not in ('REPRESENTATIVE_PROP', 'REPRESENTATIVE_KEY', 'TABLE_COUNTS')
        #             """)

        # # PK should be chosen before join
        # cur.execute(f"""CREATE TABLE IF NOT EXISTS REPRESENTATIVE_PROP AS
        #                 select distinct c.table_name, "금융정보" as RPROP from information_schema.columns as c where table_schema='{request.session.get('db')}' and
        #                 c.table_name not in ('REPRESENTATIVE_PROP', 'REPRESENTATIVE_KEY', 'TABLE_COUNTS')
        #             """)
        # # Records count should be done in real-time before join
        # cur.execute(f"""CREATE TABLE IF NOT EXISTS TABLE_COUNTS AS
        #             select table_name, table_rows as counts from
        #             information_schema.tables where table_schema='{request.session.get('db')}'
        #             """)

        cur.execute("""CREATE VIEW IF NOT EXISTS JOINABLE_TABLES AS
                       SELECT  TABLE_NAME, COUNTS as NUM_RECORDS, REPRESENTATIVES AS RPROP, REPRESENTATIVE_KEY AS RKEY 
                       FROM TABLE_COUNTS
                       WHERE SCAN=1
                    """)
        db.commit()
        cur.execute("SELECT * FROM JOINABLE_TABLES")
        prev_joinables = list(cur.fetchall())
        dropped_joinables = []

        for i, tuple_ in enumerate(prev_joinables):
            tuple_ = list(tuple_)
            prop_dict = json.loads(tuple_[2].replace("'", '"'))
            key_dict = json.loads(tuple_[3].replace("'", '"'))

            # RPROP check
            drop = True
            for prop in prop_dict.values():
                if prop is not None and prop != '' and prop != '-':
                    drop = False
                    break
            if drop:
                dropped_joinables.append(tuple_[0])
                continue
            # RKEY check
            drop = True
            for prop in key_dict.values():
                if prop is not None and prop != '' and prop != '-':
                    drop = False
                    break
            if drop:
                dropped_joinables.append(tuple_[0])
                continue
        cur.execute("DROP TABLE IF EXISTS FILTERED_TABLE")
        cur.execute("""CREATE TABLE FILTERED_TABLE AS 
                       SELECT * FROM JOINABLE_TABLES""")
        for dropped in dropped_joinables:
            cur.execute(f"""DELETE FROM FILTERED_TABLE
                            WHERE TABLE_NAME='{dropped}'""")
        db.commit()
        if request.method == 'POST':
            table_name = request.POST.get('table_name')
            standard_key = request.POST.get('standard_key')
            # print("-"*20, standard_key)
            rprop = request.POST.get('rprop')
            prop_name = request.POST.get('prop_name')
            cur.execute(f"SELECT table_name from JOINABLE_TABLES where table_name LIKE '%{table_name}%'")
            table_names = cur.fetchall()
            tables = []
            # search table which has property like 'prop_name'
            for table in table_names:
                table = table[0]
                cur.execute(f"desc {table}")
                desc = cur.fetchall()
                for row in desc:

                    if str(prop_name).lower() in str(row[0]).lower():
                        tables.append("'" + table + "'")
                        break
            if len(tables) == 0:
                tables.append("'1nNoNaMeSMaTcHeDn1'")

            str_tables = '(' + ','.join(tables) + ')'
            cur.execute(f"""SELECT * from FILTERED_TABLE where 
                            (table_name LIKE '%{table_name}%' and table_name in {str_tables})
                            """)
        # total_tables = list(zip(tables, counts, properties, pks))
        else:
            standard_key = ""
            rprop = ""
            cur.execute("SELECT * from FILTERED_TABLE")
        total_tables = list(cur.fetchall())
        filtered_tables = []
        for i in range(len(total_tables)):
            # total_tables[i][3] : 'attributes' from REPRESENTATIVE_KEYS table
            # is a dictionary which has representative key name as a key, and
            # a corresponding attribute as a value
            total_tables[i] = list(total_tables[i])

            prop_dict = json.loads(total_tables[i][2].replace("'", '"'))
            key_dict = json.loads(total_tables[i][3].replace("'", '"'))

            if rprop == "" or rprop == "대표 속성":
                occupied_rprop = [prop_dict[rkey] for rkey in prop_dict.keys() if
                                  prop_dict[rkey] != None and prop_dict[rkey] != '' and prop_dict[rkey] != '-']
            else:
                occupied_rprop = [prop_dict[rkey] for rkey in prop_dict.keys() if
                                  prop_dict[rkey] != None and prop_dict[rkey] != '' and prop_dict[rkey] != '-' and
                                  prop_dict[rkey] == rprop]
            if standard_key == "" or standard_key == "표준 결합키":
                occupied_rkey = [key_dict[rkey] for rkey in key_dict.keys() if
                                 key_dict[rkey] != None and key_dict[rkey] != '' and key_dict[rkey] != '-']
            else:
                occupied_rkey = [key_dict[rkey] for rkey in key_dict.keys() if
                                 key_dict[rkey] != None and key_dict[rkey] != '' and key_dict[rkey] != '-' and key_dict[
                                     rkey] == standard_key]
            if len(occupied_rkey) == 0 or len(occupied_rprop) == 0:
                continue
            total_tables[i][2] = list(set(occupied_rprop))
            total_tables[i][3] = occupied_rkey
            filtered_tables.append(total_tables[i])

        db.close()
        return render(request, 'singlejoin/main.html',
                      {"total_tables": filtered_tables, "is_db": request.session.get('host'),
                       "user": request.session.get('user'),
                       "passwd": request.session.get('passwd'),
                       "db": request.session.get('db'),
                       "login": request.session.get('login'),
                       "port": request.session.get('port'),
                       "standard_keys": STANDARD_KEYS,
                       "representative_props": REPRESENTATIVE_PROPS, })
    except TypeError:
        return undb(request)


def singlejoin(request):
    if request.session.get('login') != -1:
        db = MySQLdb.connect(host=request.session.get('host'),
                             user=request.session.get('user'),
                             passwd=request.session.get('passwd'),
                             db=request.session.get('db'),
                             port=request.session.get('port'), )
        table_name = "Not selected"
        rkey = "No key"
        rprop = "No prop"
        if request.method == 'POST':
            table_name = request.POST.get('table_name')
            rkey = request.POST.get('rkey')
            rprop = request.POST.get('rprop')

        cur = db.cursor()
        cur.execute(f"SELECT * FROM FILTERED_TABLE WHERE table_name='{table_name}'")

        chosen_tables = list(cur.fetchall())
        chosen_tables[0] = list(chosen_tables[0])
        prop_dict = json.loads(chosen_tables[0][2].replace("'", '"'))

        occupied_rprop = [prop_dict[rkey] for rkey in prop_dict.keys() if
                          prop_dict[rkey] != None and prop_dict[rkey] != '' and prop_dict[rkey] != '-']
        chosen_tables[0][2] = list(set(occupied_rprop))

        cur.execute(f"SELECT * FROM FILTERED_TABLE WHERE table_name != '{table_name}'")
        total_tables = list(cur.fetchall())
        filtered_tables = []
        for i in range(len(total_tables)):
            # total_tables[i][3] : 'attributes' from REPRESENTATIVE_KEYS table
            # is a dictionary which has representative key name as a key, and
            # a corresponding attribute as a value
            total_tables[i] = list(total_tables[i])
            strs = total_tables[i][3].replace("'", '"')
            prop_dict = json.loads(total_tables[i][2].replace("'", '"'))
            key_dict = json.loads(strs)
            if rkey not in key_dict.values():
                continue
            occupied_rprop = [prop_dict[rkey] for rkey in prop_dict.keys() if
                              prop_dict[rkey] != None and prop_dict[rkey] != '' and prop_dict[rkey] != '-']
            total_tables[i][3] = rkey
            total_tables[i][2] = list(set(occupied_rprop))
            filtered_tables.append(total_tables[i])
        db.close()

    return render(request, 'singlejoin/join.html',
                  {"tablename": table_name, "total_tables": filtered_tables, "is_db": request.session.get('host'),
                   "user": request.session.get('user'),
                   "passwd": request.session.get('passwd'),
                   "db": request.session.get('db'),
                   "login": request.session.get('login'),
                   "port": request.session.get('port'),

                   "chosen_tables": chosen_tables,
                   "rkey": rkey,
                   "rprop": rprop,
                   })


def join(request):
    if request.method == 'POST':
        db = MySQLdb.connect(host=request.session.get('host'),
                             user=request.session.get('user'),
                             passwd=request.session.get('passwd'),
                             db=request.session.get('db'),
                             port=request.session.get('port'), )

        cur = db.cursor()

        table_list = request.POST.getlist('selected')
        table_name = request.POST.get('table_name')
        rkey = request.POST.get('rkey')

        cur.execute(f"SELECT * FROM FILTERED_TABLE WHERE table_name='{table_name}'")
        basetable = list(cur.fetchall()[0])
        success = True

        # Join result table
        cur.execute(f"""CREATE TABLE IF NOT EXISTS SINGLE_JOIN_RESULTS 
                        (BASE_TABLE_NAME text,
                         BASE_TABLE_N_RECORDS int(11),
                         BASE_KEY_PROP text,
                        
                         JOIN_TABLE_NAME text,
                         JOIN_TABLE_N_RECORDS int(11),
                         JOIN_KEY_PROP text,
                        
                         RKEY text,
                         JOINED_N_RECORDS int(11),
                         W1 double,
                         W2 double,
                         STATUS text,
                         JOINED_NAME text
                        )
        """)
        db.commit()
        for join_table_name in table_list:
            key_dict = json.loads(basetable[3].replace("'", '"'))
            base_key_prop = ''
            for key in key_dict.keys():
                if key_dict[key] == rkey:
                    base_key_prop = key
            if base_key_prop == '':
                raise ValueError("Base key property should not be None")
            cur.execute(f"SELECT * FROM FILTERED_TABLE WHERE table_name='{join_table_name}'")
            jointable = list(cur.fetchall()[0])
            join_key_dict = json.loads(jointable[3].replace("'", '"'))
            join_key_prop = ''
            for key in join_key_dict.keys():
                if join_key_dict[key] == rkey:
                    join_key_prop = key
            if join_key_prop == '':
                raise ValueError("Join key property should not be None")
            # Inner Join
            try:
                msg = f"T1 prop: {base_key_prop} T2 prop: {join_key_prop}\n"
                cur.execute(f"DESC {table_name}")
                base_columns = [f"T1.{col} AS base_{col}" for col in list(np.array(cur.fetchall())[:, 0])]
                base_columns_sql = ','.join(base_columns)

                cur.execute(f"DESC {join_table_name}")
                join_columns = [f"T2.{col} AS join_{col}" for col in list(np.array(cur.fetchall())[:, 0])]
                join_columns_sql = ','.join(join_columns)

                cur.execute(f"DROP TABLE IF EXISTS {table_name[:7]}_{join_table_name[:7]}")
                cur.execute(f"""CREATE TABLE {table_name[:7]}_{join_table_name[:7]} AS 
                                SELECT {base_columns_sql}, {join_columns_sql} FROM {table_name} AS T1
                                INNER JOIN {join_table_name} AS T2
                                ON T1.{base_key_prop}=T2.{join_key_prop}
                """)
                db.commit()
                cur.execute(f"SELECT COUNT(*) FROM {table_name[:7]}_{join_table_name[:7]}")
                join_result_count = int(cur.fetchone()[0])

                cur.execute(f"SELECT COUNTS FROM TABLE_COUNTS WHERE table_name='{table_name}'")
                base_count = int(cur.fetchone()[0])

                cur.execute(f"SELECT COUNTS FROM TABLE_COUNTS WHERE table_name='{join_table_name}'")
                join_count = int(cur.fetchone()[0])
                cur.execute(f"""INSERT INTO SINGLE_JOIN_RESULTS (
                                    BASE_TABLE_NAME,
                                    BASE_TABLE_N_RECORDS,
                                    BASE_KEY_PROP,
                                    JOIN_TABLE_NAME,
                                    JOIN_TABLE_N_RECORDS,
                                    JOIN_KEY_PROP,
                                    RKEY,
                                    JOINED_N_RECORDS,
                                    W1,
                                    W2,
                                    STATUS,
                                    JOINED_NAME
                                )
                                VALUES (
                                    '{table_name}',
                                    '{base_count}',
                                    '{base_key_prop}',
                                    '{join_table_name}',
                                    '{join_count}',
                                    '{join_key_prop}',
                                    '{rkey}',
                                    '{join_result_count}',
                                    '{join_result_count/base_count}',
                                    '{join_result_count/join_count}',
                                    "결합완료",
                                    '{table_name[:7]}_{join_table_name[:7]}'
                                )
                """)
                db.commit()
            except MySQLdb.Error as e:
                success = False
                base_count = 1
                join_result_count = 1
                join_count = 1
                msg += str(e)

    return render(request, 'singlejoin/joinresult.html', {"tablename": table_name, "is_db": request.session.get('host'),
                                                          "user": request.session.get('user'),
                                                          "passwd": request.session.get('passwd'),
                                                          "db": request.session.get('db'),
                                                          "login": request.session.get('login'),
                                                          "port": request.session.get('port'),
                                                          "success": success,
                                                          "msg": msg,
                                                          "base_count": base_count,
                                                          "base_key_prop": base_key_prop,
                                                          "join_table_name": join_table_name,
                                                          "join_count": join_count,
                                                          "join_key_prop": join_key_prop,
                                                          "rkey": rkey,
                                                          "join_result_count": join_result_count,
                                                          "W1": join_result_count / base_count,
                                                          "W2": join_result_count / join_count,
                                                          "result": '결합완료',
                                                          "result_table_name": table_name[:5] + '_' + join_table_name[:5]
                                                          })

def check_result(request):
    try:
        db = MySQLdb.connect(host=request.session.get('host'),
                            user=request.session.get('user'),
                            passwd=request.session.get('passwd'),
                            db=request.session.get('db'),
                            port=request.session.get('port'),)

        cur = db.cursor()
        cur.execute("SELECT * FROM SINGLE_JOIN_RESULTS")
        result = cur.fetchall()
    
        return render(request, 'singlejoin/joinresult_table.html', {"is_db": request.session.get('host'),
                        "user": request.session.get('user'),
                        "passwd":request.session.get('passwd'),
                        "db":request.session.get('db'),
                        "login":request.session.get('login'),
                        "port":request.session.get('port'),
                        "result":result,
                        })
    except:
        return render(request, 'singlejoin/joinresult_table.html', {"is_db": request.session.get('host'),
                        "user": request.session.get('user'),
                        "passwd":request.session.get('passwd'),
                        "db":request.session.get('db'),
                        "login":request.session.get('login'),
                        "port":request.session.get('port'),
                        "result":None,
                        })
def download_view(request):
    db = MySQLdb.connect(host=request.session.get('host'),
                        user=request.session.get('user'),
                        passwd=request.session.get('passwd'),
                        db=request.session.get('db'),
                        port=request.session.get('port'),)

    cur = db.cursor()
    table_name = request.POST.get('table_name')

    cur.execute("DESC SINGLE_JOIN_RESULTS")
    headers = np.array(cur.fetchall())[:, 0]
    cur.execute(f"""SELECT * FROM SINGLE_JOIN_RESULTS 
                    WHERE JOINED_NAME='{table_name}'""")
    results = np.array(cur.fetchall())
    data = {header:results[:, i] for i, header in enumerate(headers)}
    outcsv = pd.DataFrame(data)
    outcsv.to_csv(f'SINGLEJOIN_{table_name}_view.csv')

    cur.execute(f"DESC {table_name}")
    headers = np.array(cur.fetchall())[:, 0]
    cur.execute(f"""SELECT * FROM {table_name}""")
    results = np.array(cur.fetchall())
    data = {header:results[:, i] for i, header in enumerate(headers)}
    outcsv = pd.DataFrame(data)
    outcsv.to_csv(f'SINGLEJOIN_{table_name}_result.csv', index=False)

    return check_result(request)
