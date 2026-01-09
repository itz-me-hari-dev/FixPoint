from django.db import models

# Create your models here.

class ServiceCategoryDb(models.Model):

    category_name = models.CharField(max_length=150)
    category_description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True,blank=True)
    category_image = models.ImageField(upload_to="category_image")




# class CustomerProfileDb(models.Model):
#     user = models.OneToOneField(UserDb, on_delete=models.CASCADE)
#     full_name = models.CharField(max_length=150)
#     phone_number = models.CharField(max_length=15)
#     address = models.TextField()
#     location = models.CharField(max_length=150)
#     latitude = models.DecimalField(max_digits=9, decimal_places=6)
#     longitude = models.DecimalField(max_digits=9, decimal_places=6)
#
# class ServiceProviderProfileDb(models.Model):
#
#     user = models.OneToOneField(UserDb, on_delete=models.CASCADE)
#     full_name = models.CharField(max_length=150)
#     service_type = models.CharField(max_length=100)
#     experience = models.PositiveIntegerField(help_text="Experience in years")
#     hourly_rate = models.DecimalField(max_digits=8, decimal_places=2)
#     location = models.CharField(max_length=150)
#     latitude = models.DecimalField(max_digits=9, decimal_places=6)
#     longitude = models.DecimalField(max_digits=9, decimal_places=6)
#     is_available = models.BooleanField(default=True)
#     is_approved = models.BooleanField(default=False)
