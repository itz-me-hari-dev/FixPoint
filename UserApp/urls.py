from django.urls import path
from UserApp import views

urlpatterns = [
    path("",views.home,name="home"),
    path("user_authentication/",views.user_authentication,name="user_authentication"),
    path("user_sign_up/",views.user_sign_up,name="user_sign_up"),
    path("user_sign_in/",views.user_sign_in,name="user_sign_in"),
    path("user_logout/",views.user_logout,name="user_logout"),
    path("service_provider_dashboard/",views.service_provider_dashboard,name="service_provider_dashboard"),
    path("manage_service_provider_profile/",views.manage_service_provider_profile,name="manage_service_provider_profile"),
    path("customer_dashboard/",views.customer_dashboard,name="customer_dashboard"),
    path("manage_customer_profile", views.manage_customer_profile, name="manage_customer_profile"),
    path("customer_service_post_page", views.customer_service_post_page, name="customer_service_post_page"),
    path('toggle_availability/', views.toggle_availability, name='toggle_availability'),
    path('provider_profile_view/<int:provider_id>/', views.provider_profile_view, name='provider_profile_view'),
    path('provider_start_job/<int:booking_id>/', views.provider_start_job, name="provider_start_job"),
    path('provider_stop_job/<int:booking_id>/', views.provider_stop_job, name="provider_stop_job"),
    path('create_booking/<int:provider_id>/', views.create_booking, name="create_booking"),
    path('accept_booking/<int:booking_id>/', views.accept_booking, name="accept_booking"),
    path('reject_booking/<int:booking_id>/', views.reject_booking, name="reject_booking"),


]