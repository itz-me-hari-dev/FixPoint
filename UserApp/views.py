from django.shortcuts import render,redirect, get_object_or_404
from django.utils.datastructures import MultiValueDictKeyError
from django.core.files.storage import FileSystemStorage
from UserApp.models import UserDb,ServiceProviderProfileDb,CustomerProfileDb
from AdminApp.models import ServiceCategoryDb
from django.contrib import messages
from decimal import Decimal


# Create your views here.

def home(request):
    categories = ServiceCategoryDb.objects.all()
    return render(request,"index.html",{"categories":categories})

def user_authentication(request):
    return render(request,"user-authentication.html")

def user_sign_up(request):

    if request.method == 'POST':

        username =  request.POST.get("username")
        email = request.POST.get("email")
        password = request.POST.get("password")
        confirm_password = request.POST.get("confirm_password")
        user_role = request.POST.get("user_role")

        # empty field check
        if not username or not email or not password or not confirm_password or not user_role:
            return redirect(user_authentication)

        if UserDb.objects.filter(username=username).exists():
            return redirect(user_authentication)

        if UserDb.objects.filter(email=email).exists():
            return redirect(user_authentication)

        if password != confirm_password:
            return redirect(user_authentication)



        UserDb.objects.create(
            username=username,
            email=email,
            password=password,
            user_role=user_role
        )

        return redirect(user_authentication)

    return redirect(user_authentication)

def user_sign_in(request):

    if request.method == 'POST':

        email_or_username = request.POST.get("email_or_username")
        password = request.POST.get("password")

        if not email_or_username or not password :
            return redirect(user_authentication)

        user = UserDb.objects.filter(username=email_or_username).first()

        if not user:
            user = UserDb.objects.filter(email=email_or_username).first()

        if not user:
            return redirect(user_authentication)

        if user.password != password:
            return redirect(user_authentication)

        request.session["username"] = user.username
        request.session["user_id"] = user.id
        request.session["user_role"] = user.user_role

        if request.session["user_role"] == 'SERVICE_PROVIDER':
            return redirect(service_provider_dashboard)

        elif request.session["user_role"] == 'CUSTOMER':
            return redirect(home)


    return redirect(user_authentication)

def user_logout(request):

    del request.session["username"]
    del request.session["user_id"]
    del request.session["user_role"]

    return redirect(home)


def customer_dashboard(request):

    if not request.session.get("username"):
        return redirect("user_authentication")

    user = UserDb.objects.get(username=request.session["username"])

    profile = CustomerProfileDb.objects.filter(user=user).first()

    # If profile not exists → go to create page
    if not profile:
        return redirect("create_customer_profile")  # URL NAME

    # Update profile
    if request.method == "POST":
        profile.full_name = request.POST.get("full_name")
        profile.phone_number = request.POST.get("phone_number")
        profile.location = request.POST.get("location")
        profile.latitude = request.POST.get("latitude") or None
        profile.longitude = request.POST.get("longitude") or None
        profile.save()

        messages.success(request, "Profile updated successfully.")
        return redirect("customer_dashboard")

    return render(request, "customer-dashboard.html", {"profile": profile})




def service_provider_dashboard(request):

    if not request.session.get("username"):
        return redirect("user_login")

    user = UserDb.objects.get(username=request.session["username"])

    try:
        profile = ServiceProviderProfileDb.objects.get(user=user)
    except ServiceProviderProfileDb.DoesNotExist:
        profile = None

    context = {
        "profile": profile
    }

    return render(request, "service-provider-dashboard.html", context)


def create_service_provider_profile(request):

    if not request.session.get("username"):
        return redirect("user_login")

    if request.method == "POST":

        user = UserDb.objects.get(username=request.session["username"])

        full_name = request.POST.get("full_name")
        service_type = request.POST.get("service_type")
        experience = request.POST.get("experience")
        location = request.POST.get("location")

        hourly_rate_raw = request.POST.get("hourly_rate")
        latitude_raw = request.POST.get("latitude")
        longitude_raw = request.POST.get("longitude")

        hourly_rate = Decimal(hourly_rate_raw) if hourly_rate_raw else None
        latitude = Decimal(latitude_raw) if latitude_raw else None
        longitude = Decimal(longitude_raw) if longitude_raw else None

        profile_photo = request.FILES.get("profile_photo")

        try:
            profile = ServiceProviderProfileDb.objects.get(user=user)

            profile.full_name = full_name
            profile.service_type = service_type
            profile.experience = experience
            profile.hourly_rate = hourly_rate
            profile.location = location
            profile.latitude = latitude
            profile.longitude = longitude

            profile.approval_status = "PENDING"
            profile.rejection_reason = None

        except ServiceProviderProfileDb.DoesNotExist:
            profile = ServiceProviderProfileDb(
                user=user,
                full_name=full_name,
                service_type=service_type,
                experience=experience,
                hourly_rate=hourly_rate,
                location=location,
                latitude=latitude,
                longitude=longitude,
            )

        if profile_photo:
            profile.profile_photo = profile_photo

        profile.save()

        return redirect("service_provider_dashboard")

    return redirect("service_provider_dashboard")


def create_customer_profile(request):

    if not request.session.get("username"):
        return redirect("user_authentication")

    user = UserDb.objects.get(username=request.session["username"])

    # If already exists → go dashboard (prevents loop)
    if CustomerProfileDb.objects.filter(user=user).exists():
        return redirect("customer_dashboard")

    if request.method == "POST":

        full_name = request.POST.get("full_name")
        phone_number = request.POST.get("phone_number")
        location = request.POST.get("location")
        latitude = request.POST.get("latitude")
        longitude = request.POST.get("longitude")

        CustomerProfileDb.objects.create(
            user=user,
            full_name=full_name,
            phone_number=phone_number,
            location=location,
            latitude=latitude or None,
            longitude=longitude or None,
        )

        return redirect("customer_dashboard")

    return redirect("customer_dashboard")















