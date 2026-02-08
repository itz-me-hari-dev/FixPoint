from django.shortcuts import render,redirect
from django.template.context_processors import request
from django.utils.datastructures import MultiValueDictKeyError
from django.core.files.storage import FileSystemStorage
from UserApp.models import UserDb, ServiceProviderProfileDb
from AdminApp.models import ServiceCategoryDb
from django.contrib import messages


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
    return render(request,"customer-dashboard.html")

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
        hourly_rate = request.POST.get("hourly_rate") or None
        location = request.POST.get("location")

        latitude = request.POST.get("latitude") or None
        longitude = request.POST.get("longitude") or None

        profile_photo = request.FILES.get("profile_photo")

        # 🔹 Try updating first
        try:
            profile = ServiceProviderProfileDb.objects.get(user=user)

            profile.full_name = full_name
            profile.service_type = service_type
            profile.experience = experience
            profile.hourly_rate = hourly_rate
            profile.location = location
            profile.latitude = latitude
            profile.longitude = longitude

            # reset approval on update
            profile.approval_status = "PENDING"
            profile.rejection_reason = None

        except ServiceProviderProfileDb.DoesNotExist:
            # 🔹 Create only if not exists
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

        # 🔹 Handle photo for both cases
        if profile_photo:
            profile.profile_photo = profile_photo

        profile.save()

        return redirect("service_provider_dashboard")

    return redirect("service_provider_dashboard")
















