from django.shortcuts import render
from mysite.common_assets import STANDARD_KEYS, REPRESENTATIVE_PROPS
import MySQLdb
from board.views import undb
import json
# Create your views here.

def multijoin_main(request):
    try:
        db = MySQLdb.connect(host=request.session.get('host'),
                            user=request.session.get('user'),
                            passwd=request.session.get('passwd'),
                            db=request.session.get('db'),
                            port=request.session.get('port'),)

        cur = db.cursor()
        
        # cur.execute(f"SHOW TABLES")
        # total_tables = cur.fetchall()

        # counts = []
        # tables = []
        # properties = []
        # pks = []
        # for i, table_tuple in enumerate(total_tables):
        #     table_name = table_tuple[0]
        #     cur.execute(f"select * from {table_name} limit 1")
        #     # PK should be chosen before join
        #     features = cur.description[0]
        #     feature = features[0]
            
        #     tables.append(table_name)

        #     cur.execute(f"select count(*) from {table_name}")
        #     count = cur.fetchone()[0]
        #     counts.append(count)

        #     # Representative property should be chosen before join
        #     properties.append("금융정보")
        #     pks.append(feature)
        
        # Representative property should be chosen before join
        dict_s = json.dumps({"전화번호":"PHONE_NUM", "이메일주소":"MAIL_ADDR"}, ensure_ascii=False)
        cur.execute(f"""CREATE TABLE IF NOT EXISTS REPRESENTATIVE_KEY AS
                    select distinct c.table_name, '{dict_s}' as RKEY from information_schema.columns as c  
                    where table_schema='{request.session.get('db')}' and 
                        c.table_name not in ('REPRESENTATIVE_PROP', 'REPRESENTATIVE_KEY', 'TABLE_COUNTS')
                    """)

        # PK should be chosen before join
        cur.execute(f"""CREATE TABLE IF NOT EXISTS REPRESENTATIVE_PROP AS
                        select distinct c.table_name, "금융정보" as RPROP from information_schema.columns as c where table_schema='{request.session.get('db')}' and 
                        c.table_name not in ('REPRESENTATIVE_PROP', 'REPRESENTATIVE_KEY', 'TABLE_COUNTS')
                    """)
        # Records count should be done in real-time before join
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
                        tables.append("'"+table+"'")
                        break
            if len(tables) == 0:
                tables.append("'1nNoNaMeSMaTcHeDn1'")

            str_tables = '('+','.join(tables)+')'
            cur.execute(f"""SELECT * from JOINABLE_TABLES where 
                            (table_name LIKE '%{table_name}%' and table_name in {str_tables})
                            or rkey LIKE '{standard_key}' 
                            or rprop LIKE '{rprop}'
                            """)
        # total_tables = list(zip(tables, counts, properties, pks))
        else:
            cur.execute("SELECT * from JOINABLE_TABLES")
        total_tables = list(cur.fetchall())
        for i in range(len(total_tables)):
            # total_tables[i][3] : 'attributes' from REPRESENTATIVE_KEYS table
            # is a dictionary which has representative key name as a key, and 
            # a corresponding attribute as a value
            total_tables[i] = list(total_tables[i])
            strs = total_tables[i][3].replace("'", '"')
           
            out_dict = json.loads(strs)
            
            total_tables[i][3] = list(out_dict.keys())
            
        db.close()
        return render(request, 'multijoin/main.html', {"total_tables":total_tables,"is_db": request.session.get('host'),
                        "user": request.session.get('user'),
                        "passwd":request.session.get('passwd'),
                        "db":request.session.get('db'),
                        "login":request.session.get('login'),
                        "port":request.session.get('port'),
                        "standard_keys":STANDARD_KEYS,
                        "representative_props":REPRESENTATIVE_PROPS,})
    except TypeError:
        # return undb(request)
        pass

def multijoin(request):
    if request.session.get('login') != -1:
        db = MySQLdb.connect(host=request.session.get('host'),
                            user=request.session.get('user'),
                            passwd=request.session.get('passwd'),
                            db=request.session.get('db'),
                            port=request.session.get('port'),)
        table_name="Not selected"
        rkey = "No key"
        if request.method == 'POST':
            table_name = request.POST.get('table_name')
            rkey = request.POST.get('rkey')
            
        cur = db.cursor()
        cur.execute(f"SELECT * FROM JOINABLE_TABLES WHERE table_name='{table_name}'")
        
        chosen_tables = cur.fetchall()
        cur.execute(f"SELECT * FROM JOINABLE_TABLES WHERE RKEY='{chosen_tables[0][3]}' and table_name != '{table_name}'")
        total_tables = list(cur.fetchall())
        filtered_tables = []
        for i in range(len(total_tables)):
            # total_tables[i][3] : 'attributes' from REPRESENTATIVE_KEYS table
            # is a dictionary which has representative key name as a key, and 
            # a corresponding attribute as a value
            total_tables[i] = list(total_tables[i])
            strs = total_tables[i][3].replace("'", '"')
           
            out_dict = json.loads(strs)
            if rkey not in out_dict.keys():
                continue
            total_tables[i][3] = rkey
            total_tables[i].insert(0, 0)
            filtered_tables.append(total_tables[i])
        db.close()

    return render(request, 'multijoin/join.html', {"tablename":table_name,"total_tables":filtered_tables,"is_db": request.session.get('host'),
                    "user": request.session.get('user'),
                    "passwd":request.session.get('passwd'),
                    "db":request.session.get('db'),
                    "login":request.session.get('login'),
                    "port":request.session.get('port'),
                    
                    "chosen_tables":chosen_tables,
                    "rkey":rkey,
                    })


def join(request):
    return render(request, '404.html')
    # if request.session.get('login') != -1:
    #     db = MySQLdb.connect(host=request.session.get('host'),
    #                         user=request.session.get('user'),
    #                         passwd=request.session.get('passwd'),
    #                         db=request.session.get('db'),
    #                         port=request.session.get('port'),)

    #     cur = db.cursor()
    #     cur.execute(f"SELECT attributes FROM REPRESENTATIVE_KEY WHERE table_name='{table_name1}'")
    #     prop1 = cur.fetchone()[0][rkey]

    #     cur.execute(f"SELECT attributes FROM REPRESENTATIVE_KEY WHERE table_name='{table_name2}'")
    #     prop2 = cur.fetchone()[0][rkey]

    #     # Inner Join
    #     cur.execute(f"""CREATE TABLE {table_name1}_{table_name2} AS 
    #                     SELECT * FROM {table_name1} AS T1
    #                     INNER JOIN ON {table_name2} AS T2
    #                     WHERE T1.{prop1}=T2.{prop2}
    #     """)
    #     cur.execute(f"SELECT * FROM {table_name1}_{table_name2}")
    #     joined_table = cur.fetchall()
    # else:
    #     joined_table = None
    # return render(request, 'multijoin/join.html', {"table_1":table_name1, "table_2":table_name2, "is_db": request.session.get('host'),
    #                 "user": request.session.get('user'),
    #                 "passwd":request.session.get('passwd'),
    #                 "db":request.session.get('db'),
    #                 "login":request.session.get('login'),
    #                 "port":request.session.get('port'),
    #                 "standard_keys":STANDARD_KEYS,
    #                 "joined_table":joined_table,
    #                 "representative_props":REPRESENTATIVE_PROPS,})