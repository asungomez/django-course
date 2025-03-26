from django.urls import path

from . import views

urlpatterns = [
  path("login-callback", views.LoginView.as_view(), name="login-callback"),
]
