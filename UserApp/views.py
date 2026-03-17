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
from django.contrib.auth.models import User
from django.contrib.auth import login , authenticate , logout
from django.contrib.auth.decorators import login_required
from UserApp.notifications import *


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

        if request.user.is_authenticated:
            user = get_object_or_404(UserDb, user=request.user)
        else:
            user = None

        if form_type == "customer":
            CustomerContactDb.objects.create(
                user=user,
                full_name=request.POST.get("cust_name"),
                email=request.POST.get("cust_email"),
                message=request.POST.get("cust_message"),
            )
            notify_contact_message(
                form_type="customer",
                full_name=request.POST.get("cust_name"),
                email=request.POST.get("cust_email"),
                message=request.POST.get("cust_message"),
            )
            messages.success(request, "Message sent successfully.")

        elif form_type == "provider":
            ServiceProviderContactDb.objects.create(
                user=user,
                full_name=request.POST.get("provider_name"),
                email=request.POST.get("provider_email"),
                message=request.POST.get("provider_message"),
            )
            notify_contact_message(
                form_type="service provider",
                full_name=request.POST.get("provider_name"),
                email=request.POST.get("provider_email"),
                message=request.POST.get("provider_message"),
            )
            messages.success(request, "Message sent successfully.")

    return redirect("contact_page")

def user_authentication(request):
    return render(request,"user-authentication.html")

def user_sign_up(request):

    if request.method == 'POST':

        username = request.POST.get("username")
        email = request.POST.get("email")
        password = request.POST.get("password")
        confirm_password = request.POST.get("confirm_password")
        user_role = request.POST.get("user_role")

        # Empty field validation
        if not username or not email or not password or not confirm_password or not user_role:
            messages.error(request, "All fields are required.")
            return redirect("user_authentication")

        # Check existing username/email in Django User
        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists.")
            return redirect("user_authentication")

        if User.objects.filter(email=email).exists():
            messages.error(request, "Email already exists.")
            return redirect("user_authentication")

        if password != confirm_password:
            messages.error(request, "Passwords do not match.")
            return redirect("user_authentication")

        # Create Django User (password automatically hashed)
        django_user = User.objects.create_user(
            username=username,
            email=email,
            password=password
        )

        # Create your custom profile
        UserDb.objects.create(
            user=django_user,
            user_role=user_role,
            is_approved=True if user_role == "CUSTOMER" else False
        )

        login(request, django_user)  # auto login after signup

        messages.success(request, "Registration successful.")

        return redirect("home")

    return redirect("user_authentication")

def user_sign_in(request):

    if request.method == 'POST':

        email_or_username = request.POST.get("email_or_username")
        password = request.POST.get("password")

        if not email_or_username or not password:
            messages.error(request, "All fields are required.")
            return redirect("user_authentication")

        # Try username login first
        user = authenticate(request, username=email_or_username, password=password)

        # If not found, try email login
        if user is None:
            try:
                user_obj = User.objects.get(email=email_or_username)
                user = authenticate(request, username=user_obj.username, password=password)
            except User.DoesNotExist:
                user = None

        if user is not None:

            login(request, user)

            user_profile = UserDb.objects.get(user=user)

            if request.user.profile.user_role == "SERVICE_PROVIDER":
                return redirect("service_provider_dashboard")
            else:
                return redirect("home")

        else:
            messages.error(request, "Invalid username/email or password.")
            return redirect("user_authentication")

    return redirect("user_authentication")

@login_required(login_url="user_authentication")
def user_logout(request):
    logout(request)
    return redirect("home")

@login_required(login_url="user_authentication")
def service_provider_dashboard(request):

    user_profile = get_object_or_404(UserDb, user=request.user)

    if request.user.profile.user_role != "SERVICE_PROVIDER":
        messages.error(request, "Unauthorized access.")
        return redirect("home")

    profile = ServiceProviderProfileDb.objects.filter(
        user=user_profile
    ).first()

    if not profile:
        messages.info(request, "Please complete your profile first.")
        return redirect("manage_service_provider_profile")

    bookings = ServiceBookingDb.objects.filter(
        service_provider=profile
    ).select_related("customer", "payment").order_by("-booking_date")

    active_job = bookings.filter(status="IN_PROGRESS").first()

    today = timezone.now().date()
    current_month = today.month
    current_year = today.year

    today_earnings = bookings.filter(
        status="COMPLETED",
        payment__payment_status="SUCCESS",
        booking_date__date=today
    ).aggregate(total=Sum("total_amount"))["total"] or 0

    monthly_earnings = bookings.filter(
        status="COMPLETED",
        payment__payment_status="SUCCESS",
        booking_date__month=current_month,
        booking_date__year=current_year
    ).aggregate(total=Sum("total_amount"))["total"] or 0

    total_earnings = bookings.filter(
        status="COMPLETED",
        payment__payment_status="SUCCESS"
    ).aggregate(total=Sum("total_amount"))["total"] or 0

    total_jobs = bookings.filter(status="COMPLETED").count()

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

@login_required(login_url="user_authentication")
def manage_service_provider_profile(request):

    user_profile = get_object_or_404(UserDb, user=request.user)
    service_categories = ServiceCategoryDb.objects.filter(is_active=True)

    if request.user.profile.user_role != "SERVICE_PROVIDER":
        messages.error(request, "Unauthorized access.")
        return redirect("home")

    profile = ServiceProviderProfileDb.objects.filter(
        user=user_profile
    ).first()

    if request.method == "POST":

        if not profile:
            profile = ServiceProviderProfileDb(user=user_profile)

        new_email = request.POST.get("email")

        if new_email and new_email != request.user.email:
            from django.contrib.auth.models import User

            if User.objects.filter(email=new_email).exclude(id=request.user.id).exists():
                messages.error(request, "Email already exists.")
                return redirect("manage_service_provider_profile")

            request.user.email = new_email
            request.user.save(update_fields=["email"])

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

        if profile.pk:
            profile.approval_status = "PENDING"
            profile.rejection_reason = None

        profile.save()

        messages.success(request, "Profile saved successfully.")
        return redirect("service_provider_dashboard")

    return render(request, "service-provider-dashboard.html", {
        "profile": profile,
        "service_categories": service_categories,
    })

@login_required(login_url="user_authentication")
def toggle_availability(request):

    user_profile = get_object_or_404(UserDb, user=request.user)

    # Role protection
    if request.user.profile.user_role != "SERVICE_PROVIDER":
        messages.error(request, "Unauthorized access.")
        return redirect("home")

    try:
        profile = ServiceProviderProfileDb.objects.get(user=user_profile)

        profile.is_available = not profile.is_available
        profile.save()

        if profile.is_available:
            messages.success(request, "You are now marked as Available.")
        else:
            messages.warning(request, "You are now marked as Unavailable.")

    except ServiceProviderProfileDb.DoesNotExist:
        messages.error(request, "Profile not found.")

    return redirect("service_provider_dashboard")

@login_required(login_url="user_authentication")
def customer_dashboard(request):

    # Get your custom user profile
    user_profile = get_object_or_404(UserDb, user=request.user)

    # Role protection
    if request.user.profile.user_role != "CUSTOMER":
        return redirect("home")

    try:
        profile = CustomerProfileDb.objects.get(user=user_profile)
    except CustomerProfileDb.DoesNotExist:
        profile = None

    total_bookings = 0
    total_spent = 0
    bookings = []

    if profile:
        total_bookings = ServiceBookingDb.objects.filter(
            customer=profile
        ).count()

        # Only successful payments
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
        "total_bookings": total_bookings,
        "total_spent": total_spent,
        "bookings": bookings,
    }

    return render(request, "customer-dashboard.html", context)

@login_required(login_url="user_authentication")
def manage_customer_profile(request):

    user_profile = get_object_or_404(UserDb, user=request.user)

    if request.user.profile.user_role != "CUSTOMER":
        messages.error(request, "Unauthorized access.")
        return redirect("home")

    profile, created = CustomerProfileDb.objects.get_or_create(
        user=user_profile
    )

    if request.method == "POST":

        new_email = request.POST.get("email")

        if new_email and new_email != request.user.email:
            from django.contrib.auth.models import User

            if User.objects.filter(email=new_email).exclude(id=request.user.id).exists():
                messages.error(request, "Email already exists.")
                return redirect("manage_customer_profile")

            request.user.email = new_email
            request.user.save(update_fields=["email"])

        profile.full_name = request.POST.get("full_name")
        profile.phone_number = request.POST.get("phone_number")
        profile.location = request.POST.get("location")

        latitude = request.POST.get("latitude")
        longitude = request.POST.get("longitude")

        profile.latitude = latitude or None
        profile.longitude = longitude or None

        profile.save()

        if not user_profile.is_approved:
            user_profile.is_approved = True
            user_profile.save(update_fields=["is_approved"])

        messages.success(request, "Profile updated successfully.")
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

@login_required(login_url="user_authentication")
def customer_service_post_page(request):

    # Get custom user profile
    user_profile = get_object_or_404(UserDb, user=request.user)

    # Role protection
    if request.user.profile.user_role != "CUSTOMER":
        messages.error(request, "Unauthorized access.")
        return redirect("home")

    try:
        customer_profile = CustomerProfileDb.objects.get(user=user_profile)
    except CustomerProfileDb.DoesNotExist:
        messages.warning(request, "Please complete your profile first.")
        return redirect("customer_dashboard")

    service_categories = ServiceCategoryDb.objects.all()

    # Base queryset
    service_post = ServiceProviderProfileDb.objects.filter(
        is_available=True,
        approval_status="APPROVED"
    )

    # Get selected category
    selected_category = request.GET.get("category")

    if selected_category:
        category_obj = ServiceCategoryDb.objects.filter(id=selected_category).first()
        if category_obj:
            service_post = service_post.filter(
                service_type=category_obj.category_name
            )

    # Calculate distance
    for provider in service_post:
        if (
            provider.latitude and provider.longitude and
            customer_profile.latitude and customer_profile.longitude
        ):
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

@login_required(login_url="user_authentication")
def provider_profile_view(request, provider_id):

    # Get custom user profile
    user_profile = get_object_or_404(UserDb, user=request.user)

    # Only customers can view provider details
    if request.user.profile.user_role != "CUSTOMER":
        messages.error(request, "Unauthorized access.")
        return redirect("home")

    try:
        customer_profile = CustomerProfileDb.objects.get(user=user_profile)
    except CustomerProfileDb.DoesNotExist:
        messages.warning(request, "Please complete your profile first.")
        return redirect("customer_dashboard")

    provider = get_object_or_404(ServiceProviderProfileDb, id=provider_id)

    distance = None

    if (
        provider.latitude and provider.longitude and
        customer_profile.latitude and customer_profile.longitude
    ):
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

@login_required(login_url="user_authentication")
def provider_start_job(request, booking_id):

    # Get custom user profile
    user_profile = get_object_or_404(UserDb, user=request.user)

    # Role protection
    if request.user.profile.user_role != "SERVICE_PROVIDER":
        messages.error(request, "Unauthorized access.")
        return redirect("home")

    provider_profile = get_object_or_404(
        ServiceProviderProfileDb,
        user=user_profile
    )

    booking = get_object_or_404(
        ServiceBookingDb,
        id=booking_id,
        service_provider=provider_profile
    )

    if booking.status != "ACCEPTED":
        messages.error(request, "Job cannot be started.")
        return redirect("service_provider_dashboard")

    # Calculate travel distance
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

@login_required(login_url="user_authentication")
def provider_stop_job(request, booking_id):

    # Get custom user profile
    user_profile = get_object_or_404(UserDb, user=request.user)

    # Role protection
    if request.user.profile.user_role != "SERVICE_PROVIDER":
        messages.error(request, "Unauthorized access.")
        return redirect("home")

    provider_profile = get_object_or_404(
        ServiceProviderProfileDb,
        user=user_profile
    )

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
    notify_job_completed(booking)

    messages.success(request, "Job completed successfully.")

    return redirect("service_provider_dashboard")

@login_required(login_url="user_authentication")
def create_booking(request, provider_id):

    # Get custom user profile
    user_profile = get_object_or_404(UserDb, user=request.user)

    # Role protection
    if request.user.profile.user_role != "CUSTOMER":
        messages.error(request, "Unauthorized access.")
        return redirect("home")

    try:
        customer_profile = CustomerProfileDb.objects.get(user=user_profile)
    except CustomerProfileDb.DoesNotExist:
        messages.warning(request, "Please complete your profile first.")
        return redirect("customer_dashboard")

    provider = get_object_or_404(ServiceProviderProfileDb, id=provider_id)

    # Optional: Prevent duplicate pending booking
    existing_booking = ServiceBookingDb.objects.filter(
        customer=customer_profile,
        service_provider=provider,
        status="PENDING"
    ).exists()

    if existing_booking:
        messages.warning(request, "You already have a pending booking with this provider.")
        return redirect("customer_dashboard")

    booking = ServiceBookingDb.objects.create(
        customer=customer_profile,
        service_provider=provider,
        service_type=provider.service_type,
        status="PENDING"
    )
    notify_booking_created(booking)

    messages.success(request, "Booking request sent successfully.")
    return redirect("customer_dashboard")

@login_required(login_url="user_authentication")
def accept_booking(request, booking_id):

    user_profile = get_object_or_404(UserDb, user=request.user)

    # Role protection
    if request.user.profile.user_role != "SERVICE_PROVIDER":
        messages.error(request, "Unauthorized access.")
        return redirect("home")

    provider_profile = get_object_or_404(
        ServiceProviderProfileDb,
        user=user_profile
    )

    booking = get_object_or_404(
        ServiceBookingDb,
        id=booking_id,
        service_provider=provider_profile
    )

    if booking.status != "PENDING":
        messages.warning(request, "Booking cannot be accepted.")
        return redirect("service_provider_dashboard")

    booking.status = "ACCEPTED"
    booking.save()
    notify_booking_status_updated(booking)

    messages.success(request, "Booking accepted successfully.")

    return redirect("service_provider_dashboard")

@login_required(login_url="user_authentication")
def reject_booking(request, booking_id):

    user_profile = get_object_or_404(UserDb, user=request.user)

    # Role protection
    if request.user.profile.user_role != "SERVICE_PROVIDER":
        messages.error(request, "Unauthorized access.")
        return redirect("home")

    provider_profile = get_object_or_404(
        ServiceProviderProfileDb,
        user=user_profile
    )

    booking = get_object_or_404(
        ServiceBookingDb,
        id=booking_id,
        service_provider=provider_profile
    )

    if booking.status != "PENDING":
        messages.warning(request, "Booking cannot be rejected.")
        return redirect("service_provider_dashboard")

    booking.status = "CANCELLED"
    booking.save()
    notify_booking_status_updated(booking)

    messages.success(request, "Booking rejected successfully.")

    return redirect("service_provider_dashboard")

@login_required(login_url="user_authentication")
def create_payment(request, booking_id):

    user_profile = get_object_or_404(UserDb, user=request.user)

    # Role protection
    if request.user.profile.user_role != "CUSTOMER":
        messages.error(request, "Unauthorized access.")
        return redirect("home")

    # Get customer profile
    try:
        customer_profile = CustomerProfileDb.objects.get(user=user_profile)
    except CustomerProfileDb.DoesNotExist:
        messages.warning(request, "Please complete your profile first.")
        return redirect("customer_dashboard")

    # Ensure booking belongs to this customer
    booking = get_object_or_404(
        ServiceBookingDb,
        id=booking_id,
        customer=customer_profile
    )

    # Allow only completed jobs
    if booking.status != "COMPLETED":
        messages.error(request, "Payment not allowed.")
        return redirect("customer_dashboard")

    # Check existing payment
    existing_payment = PaymentDb.objects.filter(booking=booking).first()

    if existing_payment and existing_payment.payment_status == "SUCCESS":
        messages.error(request, "Payment already completed.")
        return redirect("customer_dashboard")

    if existing_payment and existing_payment.payment_status == "PENDING":
        existing_payment.delete()

    # -----------------------------
    # Billing Calculation
    # -----------------------------

    total_time_decimal = Decimal(str(booking.total_time))

    work_charge = (
        total_time_decimal *
        booking.service_provider.hourly_rate
    ).quantize(Decimal("0.01"))

    travel_charge = Decimal("0.00")

    if booking.travel_distance:
        travel_charge = (
            Decimal(str(booking.travel_distance)) *
            Decimal("10")
        ).quantize(Decimal("0.01"))

    final_amount = (work_charge + travel_charge).quantize(Decimal("0.01"))

    # -----------------------------
    # Razorpay Order
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

@login_required(login_url="user_authentication")
def payment_success(request):

    user_profile = get_object_or_404(UserDb, user=request.user)

    # Only customers can access
    if request.user.profile.user_role != "CUSTOMER":
        messages.error(request, "Unauthorized access.")
        return redirect("home")

    payment_id = request.GET.get("payment_id")
    order_id = request.GET.get("order_id")
    signature = request.GET.get("signature")

    # Safety validation
    if not payment_id or not order_id or not signature:
        messages.error(request, "Invalid payment response.")
        return redirect("customer_dashboard")

    payment = get_object_or_404(
        PaymentDb,
        razorpay_order_id=order_id,
        booking__customer__user=user_profile
    )

    # Prevent double success update
    if payment.payment_status == "SUCCESS":
        messages.info(request, "Payment already verified.")
        return redirect("customer_dashboard")

    client = razorpay.Client(
        auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
    )

    try:
        client.utility.verify_payment_signature({
            "razorpay_order_id": order_id,
            "razorpay_payment_id": payment_id,
            "razorpay_signature": signature
        })

        payment.razorpay_payment_id = payment_id
        payment.razorpay_signature = signature
        payment.payment_status = "SUCCESS"
        payment.save()
        notify_payment_success(payment)

        messages.success(request, "Payment Successful!")

    except razorpay.errors.SignatureVerificationError:
        payment.payment_status = "FAILED"
        payment.save()
        messages.error(request, "Payment verification failed.")

    return redirect("customer_dashboard")
