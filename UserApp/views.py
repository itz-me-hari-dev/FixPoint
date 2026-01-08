from django.shortcuts import render ,redirect
from django.template.context_processors import request
from django.utils.datastructures import MultiValueDictKeyError
from django.core.files.storage import FileSystemStorage

# Create your views here.

def index(request):
    return render(request,"index.html")

def user_authentication(request):
    return render(request,"user-authentication.html")

# def user_sign_up(request):

