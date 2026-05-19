from django.db import models
from django.contrib.auth.models import User
# Create your models here.


class UserDb(models.Model):

    ROLE_CHOICES = (
        ('SERVICE_PROVIDER', 'Service Provider'),
        ('CUSTOMER', 'Customer'),
    )

    # Link to Django User (NO null anymore after migration)
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="profile"
    )

    user_role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES
    )

    is_approved = models.BooleanField(default=False)

    def __str__(self):
        return self.user.username

class ServiceProviderProfileDb(models.Model):

    APPROVAL_STATUS = (
        ('PENDING', 'Pending Approval'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
    )

    user = models.OneToOneField(UserDb, on_delete=models.CASCADE)

    full_name = models.CharField(max_length=150)
    phone_number = models.CharField(max_length=15, null=True, blank=True)

    service_type = models.CharField(max_length=100)
    experience = models.PositiveIntegerField(default=0)
    hourly_rate = models.DecimalField(
        max_digits=8,
        decimal_places=2
    )

    location = models.CharField(max_length=150)
    latitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True
    )
    longitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True
    )

    is_available = models.BooleanField(default=True)

    approval_status = models.CharField(
        max_length=10,
        choices=APPROVAL_STATUS,
        default='PENDING'
    )

    profile_photo = models.ImageField(
        upload_to="provider_photos/",
        null=True,
        blank=True
    )

    rejection_reason = models.TextField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.full_name} (ServiceProvider)"

class CustomerProfileDb(models.Model):

    user = models.OneToOneField(UserDb, on_delete=models.CASCADE)

    full_name = models.CharField(max_length=150)
    phone_number = models.CharField(max_length=15, null=True, blank=True)
    location = models.CharField(max_length=150)

    latitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True
    )

    longitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True
    )

    created_at = models.DateTimeField(auto_now_add=True)

    rejection_reason = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.full_name} (Customer)"




class ServiceBookingDb(models.Model):

    STATUS_CHOICES = (
        ('PENDING', 'Pending'),
        ('ACCEPTED', 'Accepted'),
        ('IN_PROGRESS', 'In Progress'),
        ('COMPLETED', 'Completed'),
        ('CANCELLED', 'Cancelled'),
    )

    customer = models.ForeignKey(
        CustomerProfileDb,
        on_delete=models.CASCADE,
        related_name="customer_bookings"
    )

    service_provider = models.ForeignKey(
        ServiceProviderProfileDb,
        on_delete=models.CASCADE,
        related_name="provider_bookings"
    )

    service_type = models.CharField(max_length=100)

    booking_date = models.DateTimeField(auto_now_add=True)

    start_time = models.DateTimeField(null=True, blank=True)
    end_time = models.DateTimeField(null=True, blank=True)

    total_time = models.FloatField(null=True, blank=True)
    total_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='PENDING'
    )

    travel_distance = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        null=True,
        blank=True
    )

    def __str__(self):
        return f"{self.customer.full_name} → {self.service_provider.full_name}"

class PaymentDb(models.Model):

    PAYMENT_STATUS = (
        ('PENDING', 'Pending'),
        ('SUCCESS', 'Success'),
        ('FAILED', 'Failed'),
    )

    booking = models.OneToOneField(
        ServiceBookingDb,
        on_delete=models.CASCADE,
        related_name="payment"
    )

    razorpay_order_id = models.CharField(max_length=200, null=True, blank=True)
    razorpay_payment_id = models.CharField(max_length=200, null=True, blank=True)
    razorpay_signature = models.CharField(max_length=300, null=True, blank=True)

    amount = models.DecimalField(max_digits=10, decimal_places=2)

    payment_status = models.CharField(
        max_length=20,
        choices=PAYMENT_STATUS,
        default="PENDING"
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Payment for Booking #{self.booking.id}"