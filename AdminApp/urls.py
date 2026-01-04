from django.urls import path
from AdminApp import views

urlpatterns = [
    path('dashboard/',views.dashboard,name="dashboard"),
    path('add_service_category_form_page/',views.add_service_category_form_page,name="add_service_category_form_page"),
    path('display_service_categories_page/',views.display_service_categories_page,name="display_service_categories_page"),
    path('save_service_category/',views.save_service_category,name="save_service_category"),
    path('edit_service_category_page/<int:category_id>/',views.edit_service_category_page,name="edit_service_category_page"),
    path('update_service_category/<int:category_id>/',views.update_service_category,name="update_service_category"),
    path('delete_service_category/<int:category_id>/',views.delete_service_category,name="delete_service_category"),
]