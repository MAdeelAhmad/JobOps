"""
Test cases for serializers in ops app.
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from users.serializers import (
    UserSerializer, UserCreateSerializer
)

User = get_user_model()


class UserSerializerTestCase(TestCase):
    """Test cases for User serializers"""

    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User',
            role='technician',
            phone='1234567890'
        )

    def test_user_serializer_contains_expected_fields(self):
        """Test UserSerializer contains expected fields"""
        serializer = UserSerializer(instance=self.user)
        data = serializer.data

        self.assertEqual(set(data.keys()), {
            'id', 'username', 'email', 'first_name', 'last_name',
            'role', 'phone', 'is_active', 'date_joined'
        })

    def test_user_create_serializer_password_validation(self):
        """Test password confirmation validation"""
        data = {
            'username': 'newuser',
            'email': 'new@example.com',
            'password': 'pass123456',
            'password_confirm': 'differentpass',
            'role': 'technician'
        }
        serializer = UserCreateSerializer(data=data)

        self.assertFalse(serializer.is_valid())
        self.assertIn('password', serializer.errors)

    def test_user_create_serializer_creates_user(self):
        """Test UserCreateSerializer creates user correctly"""
        data = {
            'username': 'newuser',
            'email': 'new@example.com',
            'password': 'pass123456',
            'password_confirm': 'pass123456',
            'first_name': 'New',
            'last_name': 'User',
            'role': 'sales_agent'
        }
        serializer = UserCreateSerializer(data=data)

        self.assertTrue(serializer.is_valid())
        user = serializer.save()

        self.assertEqual(user.username, 'newuser')
        self.assertEqual(user.role, 'sales_agent')
        self.assertTrue(user.check_password('pass123456'))
