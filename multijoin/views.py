from django.shortcuts import render
from mysite.common_assets import STANDARD_KEYS, REPRESENTATIVE_PROPS
import MySQLdb
# Create your views here.

def multijoin_main(request):
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
    cur.execute(f"""CREATE TABLE IF NOT EXISTS REPRESENTATIVE_KEY AS
                   select distinct c.table_name, "전화번호" as RKEY from information_schema.columns as c  
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

        cur.execute(f"""SELECT * from JOINABLE_TABLES where table_name LIKE '%{table_name}%'
                         and rkey LIKE '{standard_key}' 
                         and rprop LIKE '{rprop}'""")
    # total_tables = list(zip(tables, counts, properties, pks))
    else:
        cur.execute("SELECT * from JOINABLE_TABLES")
    total_tables = cur.fetchall()

    db.close()
    return render(request, 'multijoin/main.html', {"total_tables":total_tables,"is_db": request.session.get('host'),
                    "user": request.session.get('user'),
                    "passwd":request.session.get('passwd'),
                    "db":request.session.get('db'),
                    "login":request.session.get('login'),
                    "port":request.session.get('port'),
                    "standard_keys":STANDARD_KEYS,
                    "representative_props":REPRESENTATIVE_PROPS,})

def multijoin(request):
    table_name= "None"
    if request.method == "POST":
        table_name = request.POST.get('tables')
    return render(request, 'multijoin/join.html', {"tablename":table_name,})