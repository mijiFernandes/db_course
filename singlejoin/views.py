from django.shortcuts import render
from mysite.common_assets import STANDARD_KEYS, REPRESENTATIVE_PROPS
import MySQLdb
from board.views import undb

# Create your views here.

chosen_table_list = []
def singlejoin_main(request):
    try:
        db = MySQLdb.connect(host=request.session.get('host'),
                            user=request.session.get('user'),
                            passwd=request.session.get('passwd'),
                            db=request.session.get('db'),
                            port=request.session.get('port'), )

        cur = db.cursor()

        cur.execute(f"""CREATE TABLE IF NOT EXISTS REPRESENTATIVE_KEY AS
                    select distinct c.table_name, "대표 속성" as RKEY from information_schema.columns as c  
                    where table_schema='{request.session.get('db')}' and 
                        c.table_name not in ('REPRESENTATIVE_PROP', 'REPRESENTATIVE_KEY', 'TABLE_COUNTS')
                    """)


        cur.execute(f"""CREATE TABLE IF NOT EXISTS REPRESENTATIVE_PROP AS
                        select distinct c.table_name, "결합키" as RPROP from information_schema.columns as c where table_schema='{request.session.get('db')}' and 
                        c.table_name not in ('REPRESENTATIVE_PROP', 'REPRESENTATIVE_KEY', 'TABLE_COUNTS')
                    """)

        cur.execute(f"""CREATE TABLE IF NOT EXISTS TABLE_COUNTS AS
                    select table_name, table_rows as counts from 
                    information_schema.tables where table_schema='{request.session.get('db')}'
                    """)

        cur.execute("""CREATE VIEW IF NOT EXISTS JOINABLE_TABLES AS
                        SELECT  RP.table_name, TC.counts as NUM_RECORDS, RP.RPROP, RK.RKEY FROM
                        REPRESENTATIVE_PROP as RP 
                        INNER JOIN REPRESENTATIVE_KEY AS RK
                        ON RP.table_name=RK.table_name 
                        INNER JOIN TABLE_COUNTS as TC
                        ON RP.table_name=TC.table_name
                    """)

        if request.method == 'POST':
            table_name = request.POST.get('table_name')
            standard_key = request.POST.get('standard_key')
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
            cur.execute(f"""SELECT * from JOINABLE_TABLES where 
                            (table_name LIKE '%{table_name}%' and table_name in {str_tables})
                            or rkey LIKE '{standard_key}' 
                            or rprop LIKE '{rprop}'
                            """)
        else:
            cur.execute("SELECT * from JOINABLE_TABLES")
        total_tables = cur.fetchall()

        db.close()
        return render(request, 'singlejoin/main.html', {"total_tables": total_tables, "is_db": request.session.get('host'),
                                                    "user": request.session.get('user'),
                                                    "passwd": request.session.get('passwd'),
                                                    "db": request.session.get('db'),
                                                    "login": request.session.get('login'),
                                                    "port": request.session.get('port'),
                                                    "standard_keys": STANDARD_KEYS,
                                                    "representative_props": REPRESENTATIVE_PROPS, })
    except TypeError:
        return undb(request)

def singlejoin(request, table_name, chosen_table_list=chosen_table_list):
    db = MySQLdb.connect(host=request.session.get('host'),
                         user=request.session.get('user'),
                         passwd=request.session.get('passwd'),
                         db=request.session.get('db'),
                         port=request.session.get('port'), )

    is_full = False
    cur = db.cursor()
    cur.execute(f"SELECT * FROM JOINABLE_TABLES WHERE table_name='{table_name}'")

    chosen_tables = cur.fetchall()
    if len(chosen_table_list) < 2:
        chosen_table_list.append(chosen_tables)
    else:
        is_full = True
        chosen_table_list.clear()

    cur.execute(f"SELECT * FROM JOINABLE_TABLES WHERE RKEY='{chosen_tables[0][3]}'")
    total_tables = cur.fetchall()
    db.close()
    return render(request, 'singlejoin/join.html',
                  {"tablename": table_name, "total_tables": total_tables, "is_db": request.session.get('host'),
                   "user": request.session.get('user'),
                   "passwd": request.session.get('passwd'),
                   "db": request.session.get('db'),
                   "login": request.session.get('login'),
                   "port": request.session.get('port'),
                   "standard_keys": STANDARD_KEYS,
                   "chosen_tables": chosen_tables,
                   "representative_props": REPRESENTATIVE_PROPS,
                   "chosen_table_list": chosen_table_list,
                   "is_full": is_full})


def join(request, rkey, chosen_table_list=chosen_table_list):
    if request.session.get('login') != -1:
        db = MySQLdb.connect(host=request.session.get('host'),
                            user=request.session.get('user'),
                            passwd=request.session.get('passwd'),
                            db=request.session.get('db'),
                            port=request.session.get('port'),)

        cur = db.cursor()
        table_name1 = chosen_table_list[0]
        table_name2 = chosen_table_list[1]
        cur.execute(f"SELECT attributes FROM REPRESENTATIVE_KEY WHERE table_name='{table_name1[0]}'")
        prop1 = cur.fetchone()[0][rkey]

        cur.execute(f"SELECT attributes FROM REPRESENTATIVE_KEY WHERE table_name='{table_name2[0]}'")
        prop2 = cur.fetchone()[0][rkey]

        # Inner Join
        cur.execute(f"""CREATE TABLE {table_name1}_{table_name2} AS 
                        SELECT * FROM {table_name1} AS T1
                        INNER JOIN ON {table_name2} AS T2
                        WHERE T1.{prop1}=T2.{prop2}
        """)
        cur.execute(f"SELECT * FROM {table_name1}_{table_name2}")
        joined_table = cur.fetchall()
    else:
        joined_table = None

    return render(request, 'singlejoin/joinresult.html', {"table_1":table_name1, "table_2":table_name2, "is_db": request.session.get('host'),
                    "user": request.session.get('user'),
                    "passwd":request.session.get('passwd'),
                    "db":request.session.get('db'),
                    "login":request.session.get('login'),
                    "port":request.session.get('port'),
                    "standard_keys":STANDARD_KEYS,
                    "joined_table":joined_table,
                    "representative_props":REPRESENTATIVE_PROPS})


