from django.urls import path
from AdminApp import views

urlpatterns = [
    path('dashboard/',views.dashboard,name="dashboard")
]