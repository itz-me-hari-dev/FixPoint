from django.shortcuts import render,redirect, get_object_or_404
from django.utils.datastructures import MultiValueDictKeyError
from django.core.files.storage import FileSystemStorage
from UserApp.models import UserDb,ServiceProviderProfileDb,CustomerProfileDb,ServiceBookingDb
from AdminApp.models import ServiceCategoryDb
from django.utils import timezone
from django.contrib import messages
from decimal import Decimal
import math


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

        is_approved = True if user_role == "CUSTOMER" else False

        UserDb.objects.create(
            username=username,
            email=email,
            password=password,
            user_role=user_role,
            is_approved=is_approved
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

def service_provider_dashboard(request):

    if not request.session.get("username"):
        return redirect("user_authentication")

    user = UserDb.objects.get(username=request.session["username"])

    try:
        profile = ServiceProviderProfileDb.objects.get(user=user)
    except ServiceProviderProfileDb.DoesNotExist:
        profile = None

    bookings = ServiceBookingDb.objects.filter(
        service_provider=profile
    ).order_by("-booking_date")

    service_categories = ServiceCategoryDb.objects.all()

    context = {
        "profile": profile,
        "service_categories": service_categories,
        "bookings": bookings
    }

    return render(request, "service-provider-dashboard.html", context)


def manage_service_provider_profile(request):

    if not request.session.get("username"):
        return redirect("user_login")

    if request.method == "POST":

        user = UserDb.objects.get(username=request.session["username"])

        # try:
        #     profile = ServiceProviderProfileDb.objects.get(user=user)
        #     created = False
        # except ServiceProviderProfileDb.DoesNotExist:
        #     profile = ServiceProviderProfileDb(user=user)
        #     created = True

        profile , created = ServiceProviderProfileDb.objects.get_or_create(
            user=user
        )

        profile.full_name = request.POST.get("full_name")
        profile.phone_number = request.POST.get("phone_number")
        profile.service_type = request.POST.get("service_type")

        experience_raw = request.POST.get("experience")
        profile.experience = int(experience_raw) if experience_raw else 0

        profile.location = request.POST.get("location")

        hourly_rate_raw = request.POST.get("hourly_rate")
        profile.hourly_rate = Decimal(hourly_rate_raw) if hourly_rate_raw else Decimal("0.00")

        latitude_raw = request.POST.get("latitude")
        longitude_raw = request.POST.get("longitude")

        profile.latitude = Decimal(latitude_raw) if latitude_raw else None
        profile.longitude = Decimal(longitude_raw) if longitude_raw else None

        profile_photo = request.FILES.get("profile_photo")
        if profile_photo:
            profile.profile_photo = profile_photo

        # Reset approval only when updating
        if not created:
            profile.approval_status = "PENDING"
            profile.rejection_reason = None

        profile.save()

        return redirect("service_provider_dashboard")

    return redirect("service_provider_dashboard")

def toggle_availability(request):

    if not request.session.get("username"):
        return redirect("user_login")

    user = UserDb.objects.get(username=request.session["username"])

    try:
        profile = ServiceProviderProfileDb.objects.get(user=user)

        profile.is_available = not profile.is_available
        profile.save()

    except ServiceProviderProfileDb.DoesNotExist:
        pass

    return redirect("service_provider_dashboard")

def customer_dashboard(request):

    if not request.session.get("username"):
        return redirect("user_login")

    user = UserDb.objects.get(username=request.session["username"])

    try:
        profile = CustomerProfileDb.objects.get(user=user)
    except CustomerProfileDb.DoesNotExist:
        profile = None

    context = {
        "profile": profile,
        "user":user
    }

    return render(request, "customer-dashboard.html", context)

def manage_customer_profile(request):

    if not request.session.get("username"):
        return redirect("user_authentication")

    user = UserDb.objects.get(username=request.session["username"])

    profile, created = CustomerProfileDb.objects.get_or_create(
        user=user
    )

    if request.method == "POST":

        profile.full_name = request.POST.get("full_name")
        profile.phone_number = request.POST.get("phone_number")
        profile.location = request.POST.get("location")

        latitude = request.POST.get("latitude")
        longitude = request.POST.get("longitude")

        profile.latitude = latitude or None
        profile.longitude = longitude or None

        profile.save()

        if not user.is_approved:
            user.is_approved = True
            user.save(update_fields=["is_approved"])

        return redirect("customer_dashboard")

    return redirect("customer_dashboard")

def calculate_distance(lat1, lon1, lat2, lon2):
    R = 6371
    d_lat = math.radians(lat2 - lat1)
    d_lon = math.radians(lon2 - lon1)

    a = (math.sin(d_lat/2) ** 2 +
         math.cos(math.radians(lat1)) *
         math.cos(math.radians(lat2)) *
         math.sin(d_lon/2) ** 2)

    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return round(R * c, 2)

def customer_service_post_page(request):

    if not request.session.get("username"):
        return redirect("user_authentication")

    user = UserDb.objects.get(username=request.session["username"])
    customer_profile = CustomerProfileDb.objects.get(user=user)

    service_categories = ServiceCategoryDb.objects.all()
    service_post = ServiceProviderProfileDb.objects.filter(is_available=True)

    # Calculate distance
    for provider in service_post:
        if (provider.latitude and provider.longitude and
            customer_profile.latitude and customer_profile.longitude):

            provider.distance = calculate_distance(
                float(customer_profile.latitude),
                float(customer_profile.longitude),
                float(provider.latitude),
                float(provider.longitude)
            )
        else:
            provider.distance = None

    context = {
        "service_categories": service_categories,
        "service_post": service_post,
    }

    return render(request, "customer-service-post-page.html", context)

def provider_profile_view(request, provider_id):

    if not request.session.get("username"):
        return redirect("user_authentication")

    user = UserDb.objects.get(username=request.session["username"])
    customer_profile = CustomerProfileDb.objects.get(user=user)

    provider = get_object_or_404(ServiceProviderProfileDb, id=provider_id)

    distance = None

    if (provider.latitude and provider.longitude and
        customer_profile.latitude and customer_profile.longitude):

        distance = calculate_distance(
            float(customer_profile.latitude),
            float(customer_profile.longitude),
            float(provider.latitude),
            float(provider.longitude)
        )

    context = {
        "provider": provider,
        "distance": distance
    }

    return render(request, "provider-profile-view.html", context)

def provider_start_job(request, booking_id):

    if not request.session.get("username"):
        return redirect("user_authentication")

    user = UserDb.objects.get(username=request.session["username"])
    provider_profile = get_object_or_404(ServiceProviderProfileDb, user=user)

    booking = get_object_or_404(
        ServiceBookingDb,
        id=booking_id,
        service_provider=provider_profile
    )

    # Prevent double start
    if booking.status != "ACCEPTED":
        messages.error(request, "Job cannot be started.")
        return redirect("service_provider_dashboard")

    booking.start_time = timezone.now()
    booking.status = "IN_PROGRESS"
    booking.save()

    messages.success(request, "Job started successfully.")

    return redirect("service_provider_dashboard")

def provider_stop_job(request, booking_id):

    if not request.session.get("username"):
        return redirect("user_authentication")

    user = UserDb.objects.get(username=request.session["username"])
    provider_profile = get_object_or_404(ServiceProviderProfileDb, user=user)

    booking = get_object_or_404(
        ServiceBookingDb,
        id=booking_id,
        service_provider=provider_profile
    )

    # Prevent stopping wrong status
    if booking.status != "IN_PROGRESS":
        messages.error(request, "Job is not in progress.")
        return redirect("service_provider_dashboard")

    if not booking.start_time:
        messages.error(request, "Start time not found.")
        return redirect("service_provider_dashboard")

    booking.end_time = timezone.now()

    duration = booking.end_time - booking.start_time
    total_hours = Decimal(duration.total_seconds()) / Decimal(3600)

    booking.total_time = round(float(total_hours), 2)

    booking.total_amount = (
        total_hours * booking.service_provider.hourly_rate
    ).quantize(Decimal("0.01"))

    booking.status = "COMPLETED"
    booking.save()

    messages.success(request, "Job completed successfully.")

    return redirect("service_provider_dashboard")

def create_booking(request, provider_id):

    if not request.session.get("username"):
        return redirect("user_authentication")

    user = UserDb.objects.get(username=request.session["username"])
    customer_profile = CustomerProfileDb.objects.get(user=user)

    provider = get_object_or_404(ServiceProviderProfileDb, id=provider_id)

    ServiceBookingDb.objects.create(
        customer=customer_profile,
        service_provider=provider,
        service_type=provider.service_type,
        status="PENDING"
    )

    messages.success(request, "Booking request sent successfully.")
    return redirect("customer_dashboard")

def accept_booking(request, booking_id):
    booking = get_object_or_404(ServiceBookingDb, id=booking_id)
    booking.status = "ACCEPTED"
    booking.save()
    return redirect("service_provider_dashboard")

def reject_booking(request, booking_id):
    booking = get_object_or_404(ServiceBookingDb, id=booking_id)
    booking.status = "CANCELLED"
    booking.save()
    return redirect("service_provider_dashboard")






