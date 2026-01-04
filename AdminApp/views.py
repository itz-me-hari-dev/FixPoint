from django.shortcuts import render , redirect
from django.utils.datastructures import MultiValueDictKeyError
from django.core.files.storage import FileSystemStorage
from AdminApp.models import *

# Create your views here.

def dashboard(request):
    return render(request,"dashboard.html")

# Category-View-Start

def add_service_category_form_page(request):
    return render(request,"add-service-category-page.html")

def save_service_category(request):

    if request.method == 'POST':
        category_name = request.POST.get("category_name")
        category_description = request.POST.get("category_description")
        is_active = bool(request.POST.get('is_active'))

        ServiceCategoryDb(
            category_name = category_name,
            category_description = category_description,
            is_active = is_active

        ).save()

        return redirect(add_service_category_form_page)


def display_service_categories_page(request):
    service_categories = ServiceCategoryDb.objects.all()
    return render(request,"display-service-categories-page.html",{"service_categories":service_categories})

def edit_service_category_page(request,category_id):
    category = ServiceCategoryDb.objects.get(id=category_id)
    return render(request,"edit-service-category-page.html",{"category":category})

def update_service_category(request,category_id):

    if request.method == 'POST':
        category_name = request.POST.get("category_name")
        category_description = request.POST.get("category_description")
        is_active = bool(request.POST.get('is_active'))

        ServiceCategoryDb.objects.filter(id=category_id).update(
            category_name = category_name,
            category_description = category_description,
            is_active = is_active

        )

        return redirect(display_service_categories_page)


def delete_service_category(request,category_id):
    ServiceCategoryDb.objects.filter(id=category_id).delete()
    return redirect(display_service_categories_page)


# Category-View-Ends

# Admin-View-Start

def admin_login(request):
    return render(request,"admin-login.html")

# Admin-View-End