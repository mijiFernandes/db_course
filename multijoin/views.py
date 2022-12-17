from django.shortcuts import render

# Create your views here.

def multijoin(request):
    return render(request, 'multijoin/main.html')