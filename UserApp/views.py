from django.shortcuts import render,redirect, get_object_or_404
from django.utils.datastructures import MultiValueDictKeyError
from django.core.files.storage import FileSystemStorage
from UserApp.models import *
from AdminApp.models import *
from django.contrib import messages
from decimal import Decimal
import math
from django.utils import timezone
from django.db.models import Sum , Count
import razorpay
from django.conf import settings


# Create your views here.

def home(request):
    categories = ServiceCategoryDb.objects.all()
    return render(request,"index.html",{"categories":categories})

def about_page(request):
    return render(request,"about-page.html")

def services_page(request):
    categories = ServiceCategoryDb.objects.filter(is_active=True)
    context = {
        "categories": categories
    }
    return render(request, "services-page.html", context)

def contact_page(request):
    return render(request, "contact-page.html")

def user_message_save(request):

    if request.method == "POST":
        form_type = request.POST.get("form_type")

        if request.session.get("username"):
            user = UserDb.objects.get(username=request.session["username"])
        else:
            user = None

        if form_type == "customer":
            CustomerContactDb.objects.create(
                user=user,
                full_name=request.POST.get("cust_name"),
                email=request.POST.get("cust_email"),
                message=request.POST.get("cust_message"),
            )

        elif form_type == "provider":
            ServiceProviderContactDb.objects.create(
                user=user,
                full_name=request.POST.get("provider_name"),
                email=request.POST.get("provider_email"),
                message=request.POST.get("provider_message"),
            )

    return redirect("contact_page")

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
    ).select_related("customer", "payment").order_by("-booking_date")

    active_job = bookings.filter(status="IN_PROGRESS").first()

    today = timezone.now().date()
    current_month = today.month
    current_year = today.year

    # Today Earnings (only paid jobs)
    today_earnings = bookings.filter(
        status="COMPLETED",
        payment__payment_status="SUCCESS",
        booking_date__date=today
    ).aggregate(total=Sum("total_amount"))["total"] or 0

    # Monthly Earnings
    monthly_earnings = bookings.filter(
        status="COMPLETED",
        payment__payment_status="SUCCESS",
        booking_date__month=current_month,
        booking_date__year=current_year
    ).aggregate(total=Sum("total_amount"))["total"] or 0

    # Total Earnings (all time)
    total_earnings = bookings.filter(
        status="COMPLETED",
        payment__payment_status="SUCCESS"
    ).aggregate(total=Sum("total_amount"))["total"] or 0

    # Total Jobs
    total_jobs = bookings.filter(status="COMPLETED").count()

    # Total Hours Today
    total_hours_today = bookings.filter(
        status="COMPLETED",
        booking_date__date=today
    ).aggregate(total=Sum("total_time"))["total"] or 0

    last_job = bookings.filter(status="COMPLETED").first()

    service_categories = ServiceCategoryDb.objects.all()

    context = {
        "profile": profile,
        "bookings": bookings,
        "active_job": active_job,
        "today_earnings": today_earnings,
        "monthly_earnings": monthly_earnings,
        "total_earnings": total_earnings,
        "total_jobs": total_jobs,
        "last_job": last_job,
        "total_hours_today": total_hours_today,
        "service_categories": service_categories,
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

    total_bookings = 0
    total_spent = 0
    bookings = []

    if profile:
        total_bookings = ServiceBookingDb.objects.filter(
            customer=profile
        ).count()

        # Only count successful payments
        total_spent = PaymentDb.objects.filter(
            booking__customer=profile,
            payment_status="SUCCESS"
        ).aggregate(
            total=Sum("amount")
        )["total"] or 0

        bookings = ServiceBookingDb.objects.filter(
            customer=profile
        ).select_related(
            "service_provider",
            "payment"
        ).order_by("-booking_date")

    context = {
        "profile": profile,
        "user": user,
        "total_bookings": total_bookings,
        "total_spent": total_spent,
        "bookings": bookings,
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

    # Base queryset
    service_post = ServiceProviderProfileDb.objects.filter(
        is_available=True,
        approval_status="APPROVED"
    )

    #Get selected category from GET
    selected_category = request.GET.get("category")

    if selected_category:
        # Because your service_type is stored as string
        category_obj = ServiceCategoryDb.objects.filter(id=selected_category).first()
        if category_obj:
            service_post = service_post.filter(
                service_type=category_obj.category_name
            )

    #Calculate distance
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
        "selected_category": selected_category,
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

    if booking.status != "ACCEPTED":
        messages.error(request, "Job cannot be started.")
        return redirect("service_provider_dashboard")

    # Calculate travel distance here
    if (
        provider_profile.latitude and provider_profile.longitude and
        booking.customer.latitude and booking.customer.longitude
    ):

        distance = calculate_distance(
            float(provider_profile.latitude),
            float(provider_profile.longitude),
            float(booking.customer.latitude),
            float(booking.customer.longitude)
        )

        booking.travel_distance = Decimal(str(distance))

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

    if booking.status != "IN_PROGRESS":
        messages.error(request, "Job is not in progress.")
        return redirect("service_provider_dashboard")

    if not booking.start_time:
        messages.error(request, "Start time not found.")
        return redirect("service_provider_dashboard")

    booking.end_time = timezone.now()

    # Calculate working hours
    duration = booking.end_time - booking.start_time
    total_hours = Decimal(duration.total_seconds()) / Decimal(3600)

    # Round to 2 decimal places
    total_hours = total_hours.quantize(Decimal("0.01"))
    booking.total_time = total_hours

    # Work charge
    work_charge = (
        total_hours * booking.service_provider.hourly_rate
    ).quantize(Decimal("0.01"))

    # Travel charge
    travel_charge = Decimal("0.00")

    if booking.travel_distance:
        travel_charge = (
            booking.travel_distance * Decimal("10")
        ).quantize(Decimal("0.01"))

    # Final total
    booking.total_amount = (
        work_charge + travel_charge
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

def create_payment(request, booking_id):

    if not request.session.get("username"):
        return redirect("user_authentication")

    booking = get_object_or_404(ServiceBookingDb, id=booking_id)

    # Allow only completed jobs
    if booking.status != "COMPLETED":
        messages.error(request, "Payment not allowed.")
        return redirect("customer_dashboard")

    # Check existing payment
    existing_payment = PaymentDb.objects.filter(booking=booking).first()

    # If already paid → block
    if existing_payment and existing_payment.payment_status == "SUCCESS":
        messages.error(request, "Payment already completed.")
        return redirect("customer_dashboard")

    # If pending → delete and recreate
    if existing_payment and existing_payment.payment_status == "PENDING":
        existing_payment.delete()

    # -----------------------------
    # Billing Breakdown Calculation
    # -----------------------------

    # Convert total_time safely to Decimal
    total_time_decimal = Decimal(str(booking.total_time))

    # Work charge
    work_charge = (
        total_time_decimal *
        booking.service_provider.hourly_rate
    ).quantize(Decimal("0.01"))

    # Travel charge
    travel_charge = Decimal("0.00")

    if booking.travel_distance:
        travel_charge = (
            Decimal(str(booking.travel_distance)) *
            Decimal("10")
        ).quantize(Decimal("0.01"))

    # Final amount
    final_amount = (work_charge + travel_charge).quantize(Decimal("0.01"))

    # -----------------------------
    # Razorpay Order Creation
    # -----------------------------

    client = razorpay.Client(
        auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
    )

    amount_paise = int(final_amount * 100)

    order = client.order.create({
        "amount": amount_paise,
        "currency": "INR",
        "payment_capture": 1
    })

    # Save payment record
    PaymentDb.objects.create(
        booking=booking,
        razorpay_order_id=order["id"],
        amount=final_amount,
        payment_status="PENDING"
    )

    context = {
        "booking": booking,
        "order": order,
        "razorpay_key": settings.RAZORPAY_KEY_ID,
        "work_charge": work_charge,
        "travel_charge": travel_charge,
        "final_amount": final_amount,
    }

    return render(request, "payment-page.html", context)

def payment_success(request):

    payment_id = request.GET.get("payment_id")
    order_id = request.GET.get("order_id")
    signature = request.GET.get("signature")

    payment = PaymentDb.objects.get(razorpay_order_id=order_id)

    payment.razorpay_payment_id = payment_id
    payment.razorpay_signature = signature
    payment.payment_status = "SUCCESS"
    payment.save()

    messages.success(request, "Payment Successful!")

    return redirect("customer_dashboard")
