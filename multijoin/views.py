from django.shortcuts import render
import MySQLdb
# Create your views here.

def multijoin(request):
    if request.method == "POST":
        table_name = request.POST.get('tablename')
        db = MySQLdb.connect(host='localhost',
                             user='root',
                             passwd='yewon1108!',
                             db='db_final')

        cur = db.cursor()
        cur.execute(f"SHOW TABLES LIKE '{table_name}%'")
        db.close()
        return render(request, 'multijoin/main.html', {"data_set":cur.fetchall(), "is_db": request.session.get('host')})
    else:
        return render(request, 'multijoin/main.html', {"is_db": request.session.get('host')})