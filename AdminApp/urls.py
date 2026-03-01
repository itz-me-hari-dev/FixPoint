from django.urls import path
from AdminApp import views
urlpatterns = [
    path('',views.dashboard,name="dashboard"),
    path('add_service_category_form_page/',views.add_service_category_form_page,name="add_service_category_form_page"),
    path('display_service_categories_page/',views.display_service_categories_page,name="display_service_categories_page"),
    path('save_service_category/',views.save_service_category,name="save_service_category"),
    path('edit_service_category_page/<int:category_id>/',views.edit_service_category_page,name="edit_service_category_page"),
    path('update_service_category/<int:category_id>/',views.update_service_category,name="update_service_category"),
    path('delete_service_category/<int:category_id>/',views.delete_service_category,name="delete_service_category"),

    path('display_service_providers_for_approval_page/', views.display_service_providers_for_approval_page, name='display_service_providers_for_approval_page'),
    path('approve_provider/<int:provider_id>/',views.approve_provider,name='approve_provider'),
    path('reject_provider/<int:provider_id>/',views.reject_provider,name='reject_provider'),

    path('admin_login/',views.admin_login,name="admin_login"),
    path('admin_logout/',views.admin_logout,name="admin_logout"),

    path("admin_contact_messages/", views.admin_contact_messages, name="admin_contact_messages"),
    path("delete_customer_message/<int:message_id>/",views.delete_customer_message,name="delete_customer_message"),
    path("delete_service_provider_message/<int:message_id>/",views.delete_service_provider_message,name="delete_service_provider_message"),
    path("customers_details/",views.customers_details,name="customers_details"),
    path("service_providers_details/", views.service_providers_details, name="service_providers_details"),
    path("delete_user/<int:user_id>/",views.delete_user,name="delete_user"),


]

