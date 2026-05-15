from django.db import models
from UserApp.models import  UserDb

# Create your models here.

class ServiceCategoryDb(models.Model):

    category_name = models.CharField(max_length=150)
    category_description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True,blank=True)
    category_image = models.ImageField(upload_to="category_image")

class CustomerContactDb(models.Model):

    user = models.ForeignKey(
        UserDb,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )

    full_name = models.CharField(max_length=150)
    email = models.EmailField()
    message = models.TextField()

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.full_name} - {self.email}"



class ServiceProviderContactDb(models.Model):

    user = models.ForeignKey(
        UserDb,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )

    full_name = models.CharField(max_length=150)
    email = models.EmailField()
    message = models.TextField()

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.full_name} - P{self.email}"