from django.urls import path
from UserApp import views

urlpatterns = [
    path("",views.index,name="index"),
    path("user_authentication/",views.user_authentication,name="user_authentication"),
    path("user_sign_up/",views.user_sign_up,name="user_sign_up"),
]