from django.urls import path
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

from .views import RegisterView, profile_view, LogoutView, CustomTokenObtainPairView

urlpatterns = [
    path("register/", RegisterView.as_view(), name="register"),
    path("login/", CustomTokenObtainPairView.as_view(), name="token_obtain_pair"),  # Use custom view
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),  
    path("profile/", profile_view, name="profile"), 
    path("logout/", LogoutView.as_view(), name="logout"),
]
