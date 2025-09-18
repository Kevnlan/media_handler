from rest_framework import generics
from rest_framework.permissions import AllowAny
from .serializers import RegisterSerializer
from django.contrib.auth import get_user_model

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView
from .serializers import CustomTokenObtainPairSerializer
from drf_spectacular.utils import extend_schema, OpenApiExample

User = get_user_model()

class CustomTokenObtainPairView(TokenObtainPairView):
    """Custom JWT token obtain view that adds user info to token claims."""
    serializer_class = CustomTokenObtainPairSerializer
    
    @extend_schema(
        summary="Obtain JWT token pair",
        description="Login with email/username and password to get access and refresh tokens",
        examples=[
            OpenApiExample(
                'Login Example',
                value={
                    'email': 'user@example.com',
                    'password': 'password123'
                }
            )
        ]
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


class RegisterView(generics.CreateAPIView):
    """User registration view."""
    queryset = User.objects.all()
    permission_classes = [AllowAny]
    serializer_class = RegisterSerializer
    
    @extend_schema(
        summary="Register a new user",
        description="Create a new user account with email, password and optional profile info"
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


@extend_schema(
    summary="Get user profile",
    description="Get authenticated user's profile information"
)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def profile_view(request):
    user = request.user
    return Response({
        "id": user.id,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "email": user.email,
        "username": user.username,
        "phone_number": user.phone_number,
    })

class LogoutView(APIView):
    """Logout view that blacklists the refresh token."""
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Logout user",
        description="Blacklist the refresh token to log out the user",
        examples=[
            OpenApiExample(
                'Logout Example',
                value={'refresh': 'refresh_token_here'}
            )
        ]
    )
    def post(self, request):
        try:
            refresh_token = request.data.get("refresh")
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response({"message": "Successfully logged out."}, status=status.HTTP_205_RESET_CONTENT)
        except Exception:
            return Response({"error": "Invalid token or already blacklisted."}, status=status.HTTP_400_BAD_REQUEST)