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
    role = models.CharField(max_length=20,choices=ROLE_CHOICES)
    is_approved = models.BooleanField(default=False)
