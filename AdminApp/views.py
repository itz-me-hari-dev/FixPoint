from django.shortcuts import render , redirect ,get_object_or_404
from django.http import HttpResponseForbidden
from django.utils.datastructures import MultiValueDictKeyError
from django.core.files.storage import FileSystemStorage
from AdminApp.models import *
from django.contrib import messages
from UserApp.models import ServiceProviderProfileDb
from django.contrib.auth import authenticate, login
from django.contrib.auth import logout

# Create your views here.

def dashboard(request):
    return render(request,"dashboard.html")

def admin_login(request):

    if request.method == "POST":

        username = request.POST.get("admin_username")
        password = request.POST.get("admin_password")

        user = authenticate(request, username=username, password=password)

        if user is not None and user.is_superuser:
            login(request, user)
            return redirect('dashboard')  # your admin dashboard
        else:
            messages.error(request, "Invalid Admin Credentials")

    return render(request, "admin-login.html")

def admin_logout(request):
    logout(request)
    return redirect('admin_login')

# Category-View-Start

def add_service_category_form_page(request):
    return render(request,"add-service-category-page.html")

def save_service_category(request):

    if request.method == 'POST':
        category_name = request.POST.get("category_name")
        category_description = request.POST.get("category_description")
        category_image = request.FILES.get("category_image")
        is_active = bool(request.POST.get('is_active'))

        ServiceCategoryDb(
            category_name = category_name,
            category_description = category_description,
            category_image = category_image,
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

        try :
            category_image = request.FILES["category_image"]
            fs = FileSystemStorage()
            file = fs.save(f'category_image/{category_image.name}',category_image)

        except MultiValueDictKeyError :

            file = ServiceCategoryDb.objects.get(id=category_id).category_image

        ServiceCategoryDb.objects.filter(id=category_id).update(
            category_name = category_name,
            category_description = category_description,
            category_image = file,
            is_active = is_active

        )

        return redirect(display_service_categories_page)

def delete_service_category(request,category_id):
    ServiceCategoryDb.objects.filter(id=category_id).delete()
    return redirect(display_service_categories_page)


# Category-View-Ends


# Service Provider Approve/Reject code start

def display_service_providers_page(request):

    # Check login
    if not request.user.is_authenticated:
        return redirect(admin_login)

    # Check superuser
    if not request.user.is_superuser:
        return HttpResponseForbidden("Not allowed")

    providers = ServiceProviderProfileDb.objects.select_related('user')\
        .all().order_by('-created_at')

    return render(request, 'display_service_providers.html', {
        'providers': providers
    })


def approve_provider(request, provider_id):

    # Check login
    if not request.user.is_authenticated:
        return redirect(admin_login)

    # Check superuser
    if not request.user.is_superuser:
        return HttpResponseForbidden("Not allowed")

    provider = get_object_or_404(ServiceProviderProfileDb, id=provider_id)

    provider.approval_status = 'APPROVED'
    provider.rejection_reason = ""
    provider.save()

    messages.success(request, "Service Provider Approved Successfully!")

    return redirect(display_service_providers_page)


def reject_provider(request, provider_id):

    # Check login
    if not request.user.is_authenticated:
        return redirect(admin_login)

    # Check superuser
    if not request.user.is_superuser:
        return HttpResponseForbidden("Not allowed")

    provider = get_object_or_404(ServiceProviderProfileDb, id=provider_id)

    provider.approval_status = 'REJECTED'
    provider.rejection_reason = "Rejected by admin"
    provider.save()

    messages.warning(request, "Service Provider Rejected!")

    return redirect(display_service_providers_page)

# Service Provider Approve/Reject code End