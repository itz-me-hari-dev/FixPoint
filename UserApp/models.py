from django.db import models

# Create your models here.

class UserDb(models.Model):

    ROLE_CHOICES = (
        ('SERVICE_PROVIDER', 'Service Provider'),
        ('CUSTOMER', 'Customer'),
    )

    username = models.CharField(max_length=100, unique=True)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=255)
    user_role = models.CharField(max_length=20,choices=ROLE_CHOICES)
    is_approved = models.BooleanField(default=False)


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
    experience = models.PositiveIntegerField()
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
