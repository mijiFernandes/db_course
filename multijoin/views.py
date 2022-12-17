from django.shortcuts import render
from board.models import Table
import MySQLdb
# Create your views here.

def multijoin_main(request):
    db = MySQLdb.connect(host=request.session.get('host'),
                            user=request.session.get('user'),
                            passwd=request.session.get('passwd'),
                            db=request.session.get('db'))

    cur = db.cursor()
    cur.execute(f"SHOW TABLES")
    db.close()
    return render(request, 'multijoin/main.html', {"total_tables":cur.fetchall(),})

def multijoin(request):
    table_name= "None"
    if request.method == "POST":
        table_name = request.POST.get('tables')
    return render(request, 'multijoin/join.html', {"tablename":table_name,})