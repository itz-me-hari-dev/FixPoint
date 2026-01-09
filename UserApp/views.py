from django.shortcuts import render ,redirect
from django.template.context_processors import request
from django.utils.datastructures import MultiValueDictKeyError
from django.core.files.storage import FileSystemStorage
from UserApp.models import UserDb

# Create your views here.

def index(request):
    return render(request,"index.html")

def user_authentication(request):
    return render(request,"user-authentication.html")

def user_sign_up(request):

    if request.method == 'POST':

        username =  request.POST.get("username")
        email = request.POST.get("email")
        password = request.POST.get("password")
        confirm_password = request.POST.get("confirm_password")
        user_role = request.POST.get("user_role")

        if UserDb.objects.filter(username=username).exists():
            return redirect(user_authentication)

        elif UserDb.objects.filter(email=email).exists():
            return redirect(user_authentication)

        elif password != confirm_password:
            return redirect(user_authentication)

        else :

            UserDb(username=username,
                   email=email,
                   password=password,
                   confirm_password=confirm_password,
                   user_role=user_role

                   ).save()

            return redirect(index)





