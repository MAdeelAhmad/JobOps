from django.test import TestCase
from django.contrib.auth import get_user_model

User = get_user_model()


class UserModelTest(TestCase):
    """Test cases for User model"""

    def setUp(self):
        """Set up test data"""
        self.admin_user = User.objects.create_user(
            username='admin_test',
            email='admin@test.com',
            password='testpass123',
            role='admin'
        )

        self.technician = User.objects.create_user(
            username='tech_test',
            email='tech@test.com',
            password='testpass123',
            role='technician'
        )

        self.sales_agent = User.objects.create_user(
            username='sales_test',
            email='sales@test.com',
            password='testpass123',
            role='sales_agent'
        )

    def test_user_creation(self):
        """Test user is created correctly"""
        self.assertEqual(self.technician.username, 'tech_test')
        self.assertEqual(self.technician.role, 'technician')
        self.assertTrue(self.technician.is_active)

    def test_admin_has_staff_status(self):
        """Test admin users automatically get staff status"""
        self.assertTrue(self.admin_user.is_staff)

    def test_user_string_representation(self):
        """Test user string representation"""
        expected = f"{self.technician.username} ({self.technician.get_role_display()})"
        self.assertEqual(str(self.technician), expected)

    def test_user_role_choices(self):
        """Test user role choices are valid"""
        valid_roles = ['admin', 'technician', 'sales_agent']
        self.assertIn(self.technician.role, valid_roles)
