from rest_framework.authentication import BaseAuthentication
from rest_framework import exceptions
import jwt
from django.conf import settings
from datetime import datetime, timezone


class JWTUser:
    """
    A simple user-like object for JWT authenticated requests.
    This represents a user from the auth service without needing database access.
    """
    def __init__(self, user_id, email, is_authenticated=True):
        self.id = user_id
        self.email = email
        self.is_authenticated = is_authenticated
        self.is_active = True
        self.is_anonymous = False
        
    def __str__(self):
        return self.email


class JWTAuthentication(BaseAuthentication):
    """
    JWT authentication for validating tokens from the auth service.
    """
    
    def authenticate(self, request):
        auth_header = request.headers.get("Authorization")
        
        if not auth_header:
            return None
            
        try:
            prefix, token = auth_header.split(" ")
        except ValueError:
            raise exceptions.AuthenticationFailed("Invalid Authorization header format.")
            
        if prefix != "Bearer":
            raise exceptions.AuthenticationFailed("Invalid token prefix. Expected 'Bearer'.")
            
        try:
            # Decode the JWT token using the same signing key as auth service
            payload = jwt.decode(
                token,
                settings.SIMPLE_JWT["SIGNING_KEY"],
                algorithms=["HS256"]
            )
            
            # Check if token is expired
            exp = payload.get('exp')
            if exp:
                exp_datetime = datetime.fromtimestamp(exp, tz=timezone.utc)
                if exp_datetime < datetime.now(timezone.utc):
                    raise exceptions.AuthenticationFailed("Token has expired.")
            
            # Create a user object from the JWT payload
            user = JWTUser(
                user_id=payload.get('user_id'),
                email=payload.get('email', '')  # You might need to add email to JWT payload
            )
            
            return (user, token)
            
        except jwt.ExpiredSignatureError:
            raise exceptions.AuthenticationFailed("Token has expired.")
        except jwt.InvalidTokenError as e:
            raise exceptions.AuthenticationFailed(f"Invalid token: {str(e)}")