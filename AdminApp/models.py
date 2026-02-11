from django.db import models

# Create your models here.

class ServiceCategoryDb(models.Model):

    category_name = models.CharField(max_length=150)
    category_description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True,blank=True)
    category_image = models.ImageField(upload_to="category_image")




