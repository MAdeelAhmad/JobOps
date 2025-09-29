from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.auth import get_user_model

User = get_user_model()


class AuthenticationTestCase(TestCase):
    """Test cases for authentication"""

    def setUp(self):
        """Set up test data"""
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            role='technician'
        )

    def test_login_success(self):
        """Test successful login returns JWT tokens"""
        url = reverse('token_obtain_pair')
        data = {
            'username': 'testuser',
            'password': 'testpass123'
        }
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)

    def test_login_invalid_credentials(self):
        """Test login with invalid credentials fails"""
        url = reverse('token_obtain_pair')
        data = {
            'username': 'testuser',
            'password': 'wrongpassword'
        }
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_token_refresh(self):
        """Test token refresh works"""
        # Get initial tokens
        login_url = reverse('token_obtain_pair')
        login_data = {
            'username': 'testuser',
            'password': 'testpass123'
        }
        login_response = self.client.post(login_url, login_data, format='json')
        refresh_token = login_response.data['refresh']

        # Refresh token
        refresh_url = reverse('token_refresh')
        refresh_data = {'refresh': refresh_token}
        response = self.client.post(refresh_url, refresh_data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)


class UserViewSetTestCase(TestCase):
    """Test cases for User ViewSet"""

    def setUp(self):
        """Set up test data"""
        self.client = APIClient()

        self.admin = User.objects.create_user(
            username='admin',
            email='admin@test.com',
            password='admin123',
            role='admin'
        )

        self.technician = User.objects.create_user(
            username='tech',
            email='tech@test.com',
            password='tech123',
            role='technician'
        )

        self.sales_agent = User.objects.create_user(
            username='sales',
            email='sales@test.com',
            password='sales123',
            role='sales_agent'
        )

    def test_list_users_authenticated(self):
        """Test authenticated users can list users"""
        self.client.force_authenticate(user=self.technician)
        url = reverse('user-list')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data['results']), 3)

    def test_list_users_unauthenticated(self):
        """Test unauthenticated users cannot list users"""
        url = reverse('user-list')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_user_admin_only(self):
        """Test only admins can create users"""
        self.client.force_authenticate(user=self.admin)
        url = reverse('user-list')
        data = {
            'username': 'newtech',
            'email': 'newtech@test.com',
            'password': 'newpass123',
            'password_confirm': 'newpass123',
            'first_name': 'New',
            'last_name': 'Tech',
            'role': 'technician'
        }
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(User.objects.filter(username='newtech').count(), 1)

    def test_create_user_non_admin_forbidden(self):
        """Test non-admins cannot create users"""
        self.client.force_authenticate(user=self.technician)
        url = reverse('user-list')
        data = {
            'username': 'newtech',
            'email': 'newtech@test.com',
            'password': 'newpass123',
            'password_confirm': 'newpass123',
            'role': 'technician'
        }
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_get_current_user_profile(self):
        """Test users can get their own profile"""
        self.client.force_authenticate(user=self.technician)
        url = reverse('user-me')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['username'], 'tech')

    def test_filter_users_by_role(self):
        """Test filtering users by role"""
        self.client.force_authenticate(user=self.admin)
        url = reverse('user-list')
        response = self.client.get(url, {'role': 'technician'})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        for user in response.data['results']:
            self.assertEqual(user['role'], 'technician')
