from django.urls import path
from UserApp import views

urlpatterns = [
    path("",views.home,name="home"),
    path("user_authentication/",views.user_authentication,name="user_authentication"),
    path("user_sign_up/",views.user_sign_up,name="user_sign_up"),
    path("user_sign_in/",views.user_sign_in,name="user_sign_in"),
    path("user_logout/",views.user_logout,name="user_logout"),
]