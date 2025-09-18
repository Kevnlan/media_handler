from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken
import json

User = get_user_model()


class CustomUserModelTest(TestCase):
    """Test the CustomUser model."""
    
    def setUp(self):
        self.user_data = {
            'email': 'test@example.com',
            'password': 'testpass123',
            'first_name': 'Test',
            'last_name': 'User',
            'username': 'testuser',
            'phone_number': '1234567890'
        }

    def test_create_user(self):
        """Test creating a new user."""
        user = User.objects.create_user(**self.user_data)  # type: ignore
        
        self.assertEqual(user.email, 'test@example.com')  # type: ignore
        self.assertEqual(user.first_name, 'Test')  # type: ignore
        self.assertEqual(user.last_name, 'User')  # type: ignore
        self.assertEqual(user.username, 'testuser')  # type: ignore
        self.assertEqual(user.phone_number, '1234567890')  # type: ignore
        self.assertTrue(user.is_active)  # type: ignore
        self.assertFalse(user.is_staff)  # type: ignore
        self.assertFalse(user.is_superuser)  # type: ignore
        self.assertTrue(user.check_password('testpass123'))  # type: ignore

    def test_create_superuser(self):
        """Test creating a superuser."""
        user = User.objects.create_superuser(  # type: ignore
            email='admin@example.com',
            password='adminpass123',
            first_name='Admin',
            last_name='User',
            username='adminuser'
        )
        self.assertEqual(user.email, 'admin@example.com')  # type: ignore
        self.assertTrue(user.is_active)  # type: ignore
        self.assertTrue(user.is_staff)  # type: ignore
        self.assertTrue(user.is_superuser)  # type: ignore

    def test_create_user_without_email(self):
        """Test creating user without email raises ValueError."""
        with self.assertRaises(ValueError):
            User.objects.create_user(  # type: ignore
                email='',
                password='testpass123',
                first_name='Test',
                last_name='User',
                username='testuser'
            )

    def test_string_representation(self):
        """Test the user string representation."""
        user = User.objects.create_user(**self.user_data)  # type: ignore
        self.assertEqual(str(user), 'test@example.com')  # type: ignore

    def test_email_normalize(self):
        """Test email normalization."""
        user = User.objects.create_user(  # type: ignore
            email='TEST@EXAMPLE.COM',
            password='testpass123',
            first_name='Test',
            last_name='User',
            username='testuser'
        )
        self.assertEqual(user.email, 'TEST@example.com')  # type: ignore


class RegisterViewTest(APITestCase):
    """Test the user registration API."""
    
    def setUp(self):
        self.register_url = reverse('register')
        self.user_data = {
            'email': 'test@example.com',
            'password': 'testpass123',
            'first_name': 'Test',
            'last_name': 'User',
            'username': 'testuser',
            'phone_number': '1234567890'
        }

    def test_user_registration_success(self):
        """Test successful user registration."""
        response = self.client.post(self.register_url, self.user_data)  # type: ignore
        
        self.assertEqual(response.status_code, 201)
        self.assertEqual(User.objects.count(), 1)  # type: ignore
        
        user = User.objects.get(email='test@example.com')  # type: ignore
        self.assertEqual(user.first_name, 'Test')  # type: ignore
        self.assertEqual(user.last_name, 'User')  # type: ignore
        self.assertEqual(user.username, 'testuser')  # type: ignore
        self.assertEqual(user.phone_number, '1234567890')  # type: ignore

    def test_user_registration_duplicate_email(self):
        """Test registration with duplicate email fails."""
        # Create first user
        User.objects.create_user(**self.user_data)  # type: ignore
        
        # Try to create another user with same email
        response = self.client.post(self.register_url, self.user_data)  # type: ignore
        
        self.assertEqual(response.status_code, 400)

    def test_user_registration_invalid_data(self):
        """Test registration with invalid data fails."""
        invalid_data = self.user_data.copy()
        invalid_data['email'] = 'invalid-email'
        
        response = self.client.post(self.register_url, invalid_data)  # type: ignore
        
        self.assertEqual(response.status_code, 400)

    def test_user_registration_missing_required_fields(self):
        """Test registration with missing required fields fails."""
        incomplete_data = {
            'email': 'test@example.com'
        }
        
        response = self.client.post(self.register_url, incomplete_data)  # type: ignore
        
        self.assertEqual(response.status_code, 400)


class LoginViewTest(APITestCase):
    """Test the user login API."""
    
    def setUp(self):
        self.login_url = reverse('login')
        self.user_data = {
            'email': 'test@example.com',
            'password': 'testpass123',
            'first_name': 'Test',
            'last_name': 'User',
            'username': 'testuser',
            'phone_number': '1234567890'
        }
        self.user = User.objects.create_user(**self.user_data)  # type: ignore

    def test_user_login_success(self):
        """Test successful user login."""
        login_data = {
            'email': 'test@example.com',
            'password': 'testpass123'
        }
        
        response = self.client.post(self.login_url, login_data)  # type: ignore
        
        self.assertEqual(response.status_code, 201)
        self.assertIn('access', response.data)  # type: ignore
        self.assertIn('refresh', response.data)  # type: ignore

    def test_user_login_invalid_credentials(self):
        """Test login with invalid credentials fails."""
        invalid_data = {
            'email': 'test@example.com',
            'password': 'wrongpassword'
        }
        
        response = self.client.post(self.login_url, invalid_data)  # type: ignore
        
        self.assertEqual(response.status_code, 401)

    def test_user_login_nonexistent_user(self):
        """Test login with nonexistent user fails."""
        invalid_data = {
            'email': 'nonexistent@example.com',
            'password': 'testpass123'
        }
        
        response = self.client.post(self.login_url, invalid_data)  # type: ignore
        
        self.assertEqual(response.status_code, 401)

    def test_user_login_missing_fields(self):
        """Test login with missing fields fails."""
        incomplete_data = {
            'email': 'test@example.com'
        }
        
        response = self.client.post(self.login_url, incomplete_data)  # type: ignore
        
        self.assertEqual(response.status_code, 400)


class ProfileViewTest(APITestCase):
    """Test the user profile API."""
    
    def setUp(self):
        self.profile_url = reverse('profile')
        self.user_data = {
            'email': 'test@example.com',
            'password': 'testpass123',
            'first_name': 'Test',
            'last_name': 'User',
            'username': 'testuser',
            'phone_number': '1234567890'
        }
        self.user = User.objects.create_user(**self.user_data)  # type: ignore
        self.refresh = RefreshToken.for_user(self.user)  # type: ignore
        self.access_token = str(self.refresh.access_token)  # type: ignore

    def test_get_profile_authenticated(self):
        """Test getting profile with valid authentication."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token}')  # type: ignore
        
        response = self.client.get(self.profile_url)  # type: ignore
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['email'], 'test@example.com')  # type: ignore
        self.assertEqual(response.data['first_name'], 'Test')  # type: ignore
        self.assertEqual(response.data['last_name'], 'User')  # type: ignore
        self.assertEqual(response.data['username'], 'testuser')  # type: ignore
        self.assertEqual(response.data['phone_number'], '1234567890')  # type: ignore
        self.assertIn('id', response.data)  # type: ignore

    def test_get_profile_unauthenticated(self):
        """Test getting profile without authentication fails."""
        response = self.client.get(self.profile_url)  # type: ignore
        
        self.assertEqual(response.status_code, 401)

    def test_update_profile_authenticated(self):
        """Test updating profile with valid authentication."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token}')  # type: ignore
        
        update_data = {
            'first_name': 'Updated',
            'last_name': 'Name',
            'phone_number': '9876543210'
        }
        
        response = self.client.patch(self.profile_url, update_data)  # type: ignore
        
        self.assertEqual(response.status_code, 200)
        
        # Refresh user from database
        self.user.refresh_from_db()  # type: ignore
        self.assertEqual(self.user.first_name, 'Updated')  # type: ignore
        self.assertEqual(self.user.last_name, 'Name')  # type: ignore
        self.assertEqual(self.user.phone_number, '9876543210')  # type: ignore

    def test_update_profile_unauthenticated(self):
        """Test updating profile without authentication fails."""
        update_data = {
            'first_name': 'Updated'
        }
        
        response = self.client.patch(self.profile_url, update_data)  # type: ignore
        
        self.assertEqual(response.status_code, 401)


class LogoutViewTest(APITestCase):
    """Test the user logout API."""
    
    def setUp(self):
        self.logout_url = reverse('logout')
        self.user_data = {
            'email': 'test@example.com',
            'password': 'testpass123',
            'first_name': 'Test',
            'last_name': 'User',
            'username': 'testuser',
            'phone_number': '1234567890'
        }
        self.user = User.objects.create_user(**self.user_data)  # type: ignore
        self.refresh = RefreshToken.for_user(self.user)  # type: ignore
        self.access_token = str(self.refresh.access_token)  # type: ignore

    def test_logout_success(self):
        """Test successful logout."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token}')  # type: ignore
        
        logout_data = {
            'refresh_token': str(self.refresh)
        }
        
        response = self.client.post(self.logout_url, logout_data)  # type: ignore
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['message'], 'Successfully logged out.')  # type: ignore

    def test_logout_unauthenticated(self):
        """Test logout without authentication fails."""
        logout_data = {
            'refresh_token': str(self.refresh)
        }
        
        response = self.client.post(self.logout_url, logout_data)  # type: ignore
        
        self.assertEqual(response.status_code, 401)

    def test_logout_invalid_token(self):
        """Test logout with invalid refresh token."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token}')  # type: ignore
        
        logout_data = {
            'refresh_token': 'invalid_token'
        }
        
        response = self.client.post(self.logout_url, logout_data)  # type: ignore
        
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data['error'], 'Invalid token or already blacklisted.')  # type: ignore


class UserSerializerTest(TestCase):
    """Test the UserSerializer."""
    
    def setUp(self):
        from accounts.serializers import UserSerializer  # type: ignore
        self.serializer_class = UserSerializer
        self.user_data = {
            'email': 'test@example.com',
            'password': 'testpass123',
            'first_name': 'Test',
            'last_name': 'User',
            'username': 'testuser',
            'phone_number': '1234567890'
        }

    def test_serializer_with_valid_data(self):
        """Test serializer with valid data."""
        serializer = self.serializer_class(data=self.user_data)  # type: ignore
        self.assertTrue(serializer.is_valid())  # type: ignore

    def test_serializer_with_invalid_email(self):
        """Test serializer with invalid email."""
        invalid_data = self.user_data.copy()
        invalid_data['email'] = 'invalid-email'
        
        serializer = self.serializer_class(data=invalid_data)  # type: ignore
        self.assertFalse(serializer.is_valid())  # type: ignore

    def test_serializer_missing_required_fields(self):
        """Test serializer with missing required fields."""
        incomplete_data = {
            'email': 'test@example.com'
        }
        
        serializer = self.serializer_class(data=incomplete_data)  # type: ignore
        self.assertFalse(serializer.is_valid())  # type: ignore

    def test_serializer_create_user(self):
        """Test creating user through serializer."""
        serializer = self.serializer_class(data=self.user_data)  # type: ignore
        self.assertTrue(serializer.is_valid())  # type: ignore
        
        user = serializer.save()  # type: ignore
        self.assertEqual(user.email, 'test@example.com')  # type: ignore
        self.assertTrue(user.check_password('testpass123'))  # type: ignore


class LoginSerializerTest(TestCase):
    """Test the LoginSerializer."""
    
    def setUp(self):
        from accounts.serializers import LoginSerializer  # type: ignore
        self.serializer_class = LoginSerializer
        self.user_data = {
            'email': 'test@example.com',
            'password': 'testpass123',
            'first_name': 'Test',
            'last_name': 'User',
            'username': 'testuser',
            'phone_number': '1234567890'
        }
        self.user = User.objects.create_user(**self.user_data)  # type: ignore

    def test_serializer_with_valid_credentials(self):
        """Test serializer with valid credentials."""
        login_data = {
            'email': 'test@example.com',
            'password': 'testpass123'
        }
        
        serializer = self.serializer_class(data=login_data)  # type: ignore
        self.assertTrue(serializer.is_valid())  # type: ignore

    def test_serializer_with_invalid_credentials(self):
        """Test serializer with invalid credentials."""
        login_data = {
            'email': 'test@example.com',
            'password': 'wrongpassword'
        }
        
        serializer = self.serializer_class(data=login_data)  # type: ignore
        self.assertFalse(serializer.is_valid())  # type: ignore

    def test_serializer_missing_fields(self):
        """Test serializer with missing fields."""
        incomplete_data = {
            'email': 'test@example.com'
        }
        
        serializer = self.serializer_class(data=incomplete_data)  # type: ignore
        self.assertFalse(serializer.is_valid())  # type: ignore
