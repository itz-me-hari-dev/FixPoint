from django.shortcuts import render , redirect ,get_object_or_404
from django.utils.datastructures import MultiValueDictKeyError
from django.core.files.storage import FileSystemStorage
from AdminApp.models import *
from django.contrib import messages
from UserApp.models import UserDb,CustomerProfileDb,ServiceProviderProfileDb
from django.contrib.auth import authenticate, login
from django.contrib.auth import logout
from UserApp.notifications import notify_provider_approval
from functools import wraps

# Create your views here.

def admin_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect("admin_login")
        if not request.user.is_superuser:
            messages.error(request, "Please log in with an admin account.")
            return redirect("admin_login")
        return view_func(request, *args, **kwargs)
    return _wrapped_view

@admin_required
def dashboard(request):

    total_customers = UserDb.objects.filter(user_role="CUSTOMER").count()
    total_providers = UserDb.objects.filter(user_role="SERVICE_PROVIDER").count()
    total_categories = ServiceCategoryDb.objects.count()

    total_customer_messages = CustomerContactDb.objects.count()
    total_provider_messages = ServiceProviderContactDb.objects.count()

    recent_customer_messages = CustomerContactDb.objects.order_by("-created_at")[:5]
    recent_provider_messages = ServiceProviderContactDb.objects.order_by("-created_at")[:5]

    context = {
        "total_customers": total_customers,
        "total_providers": total_providers,
        "total_categories": total_categories,
        "total_customer_messages": total_customer_messages,
        "total_provider_messages": total_provider_messages,
        "recent_customer_messages": recent_customer_messages,
        "recent_provider_messages": recent_provider_messages,
    }

    return render(request, "dashboard.html", context)

def admin_login(request):

    if request.user.is_authenticated and request.user.is_superuser:
        return redirect('dashboard')

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

@admin_required
def add_service_category_form_page(request):
    return render(request,"add-service-category-page.html")

@admin_required
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

@admin_required
def display_service_categories_page(request):
    service_categories = ServiceCategoryDb.objects.all()
    context ={
        "service_categories": service_categories
    }
    return render(request,"display-service-categories-page.html",context)

@admin_required
def edit_service_category_page(request,category_id):
    category = ServiceCategoryDb.objects.get(id=category_id)
    return render(request,"edit-service-category-page.html",{"category":category})

@admin_required
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

@admin_required
def delete_service_category(request,category_id):
    ServiceCategoryDb.objects.filter(id=category_id).delete()
    return redirect(display_service_categories_page)


# Category-View-Ends


# Service Provider Approve/Reject code start

@admin_required
def display_service_providers_for_approval_page(request):
    providers = ServiceProviderProfileDb.objects.select_related('user')\
        .all().order_by('-created_at')

    return render(request, 'display_service_providers._approval_request.html', {
        'providers': providers
    })


@admin_required
def approve_provider(request, provider_id):
    provider = get_object_or_404(ServiceProviderProfileDb, id=provider_id)

    provider.approval_status = 'APPROVED'
    provider.rejection_reason = ""
    provider.save()
    notify_provider_approval(provider, is_approved=True)

    messages.success(request, "Service Provider Approved Successfully!")

    return redirect("display_service_providers_for_approval_page")


@admin_required
def reject_provider(request, provider_id):
    provider = get_object_or_404(ServiceProviderProfileDb, id=provider_id)

    provider.approval_status = 'REJECTED'
    provider.rejection_reason = "Rejected by admin"
    provider.save()
    notify_provider_approval(provider, is_approved=False)

    messages.warning(request, "Service Provider Rejected!")

    return redirect("display_service_providers_for_approval_page")

# Service Provider Approve/Reject code End


# user contact start
@admin_required
def admin_contact_messages(request):

    customer_messages = CustomerContactDb.objects.all().order_by("-created_at")
    provider_messages = ServiceProviderContactDb.objects.all().order_by("-created_at")

    context = {
        "customer_messages": customer_messages,
        "provider_messages": provider_messages,
    }

    return render(request, "admin_contact_messages.html", context)

@admin_required
def delete_customer_message(request, message_id):
    CustomerContactDb.objects.filter(id=message_id).delete()
    return redirect("admin_contact_messages")

@admin_required
def delete_service_provider_message(request, message_id):
    ServiceProviderContactDb.objects.filter(id=message_id).delete()
    return redirect("admin_contact_messages")

@admin_required
def customers_details(request):

    customers = UserDb.objects.filter(
        user_role='CUSTOMER'
    ).select_related('customerprofiledb')

    context = {
        "customers": customers
    }

    return render(request, "customers-details.html",context )

@admin_required
def service_providers_details(request):

    providers = UserDb.objects.filter(
        user_role='SERVICE_PROVIDER'
    ).select_related('serviceproviderprofiledb')

    context = {
        "providers": providers
    }

    return render(request, "service-providers-details.html", context)

@admin_required
def delete_user(request, user_id):
    user = get_object_or_404(UserDb, id=user_id)
    user.delete()

    return redirect(request.META.get('HTTP_REFERER', 'dashboard'))

# user contact end
