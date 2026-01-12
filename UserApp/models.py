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
    service_type = models.CharField(max_length=100)
    experience = models.PositiveIntegerField()
    hourly_rate = models.DecimalField(max_digits=8, decimal_places=2)

    location = models.CharField(max_length=150)
    latitude = models.DecimalField(max_digits=9, decimal_places=6)
    longitude = models.DecimalField(max_digits=9, decimal_places=6)

    is_available = models.BooleanField(default=True)

    approval_status = models.CharField(
        max_length=10,
        choices=APPROVAL_STATUS,
        default='PENDING'
    )

    rejection_reason = models.TextField(blank=True, null=True)