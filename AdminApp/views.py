from django.shortcuts import render
from django.utils.datastructures import MultiValueDictKeyError
from django.core.files.storage import FileSystemStorage

# Create your views here.

def dashboard(request):
    return render(request,"dashboard.html")