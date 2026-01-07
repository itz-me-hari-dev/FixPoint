from django.shortcuts import render ,redirect
from django.utils.datastructures import MultiValueDictKeyError
from django.core.files.storage import FileSystemStorage

# Create your views here.

def index(request):
    return render(request,"index.html")