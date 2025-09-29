from django.test import TestCase, RequestFactory
from django.contrib.auth import get_user_model
from django.utils import timezone

from ops.models import Job, JobTask, Equipment
from ops.permissions import (
    IsAdmin, IsAdminOrSalesAgent, CanManageUsers,
    CanCreateJob, CanUpdateJobProgress, CanManageEquipment,
    CanViewAnalytics
)

User = get_user_model()


class IsAdminPermissionTestCase(TestCase):
    """Test cases for IsAdmin permission"""

    def setUp(self):
        """Set up test data"""
        self.factory = RequestFactory()
        self.permission = IsAdmin()

        self.admin = User.objects.create_user(
            username='admin',
            password='pass123',
            role='admin'
        )

        self.technician = User.objects.create_user(
            username='tech',
            password='pass123',
            role='technician'
        )

    def test_admin_has_permission(self):
        """Test admin users have permission"""
        request = self.factory.get('/')
        request.user = self.admin

        self.assertTrue(self.permission.has_permission(request, None))

    def test_non_admin_denied_permission(self):
        """Test non-admin users are denied permission"""
        request = self.factory.get('/')
        request.user = self.technician

        self.assertFalse(self.permission.has_permission(request, None))


class IsAdminOrSalesAgentPermissionTestCase(TestCase):
    """Test cases for IsAdminOrSalesAgent permission"""

    def setUp(self):
        """Set up test data"""
        self.factory = RequestFactory()
        self.permission = IsAdminOrSalesAgent()

        self.admin = User.objects.create_user(
            username='admin',
            password='pass123',
            role='admin'
        )

        self.sales_agent = User.objects.create_user(
            username='sales',
            password='pass123',
            role='sales_agent'
        )

        self.technician = User.objects.create_user(
            username='tech',
            password='pass123',
            role='technician'
        )

    def test_admin_has_permission(self):
        """Test admin has permission"""
        request = self.factory.get('/')
        request.user = self.admin

        self.assertTrue(self.permission.has_permission(request, None))

    def test_sales_agent_has_permission(self):
        """Test sales agent has permission"""
        request = self.factory.get('/')
        request.user = self.sales_agent

        self.assertTrue(self.permission.has_permission(request, None))

    def test_technician_denied_permission(self):
        """Test technician is denied permission"""
        request = self.factory.get('/')
        request.user = self.technician

        self.assertFalse(self.permission.has_permission(request, None))


class CanManageUsersPermissionTestCase(TestCase):
    """Test cases for CanManageUsers permission"""

    def setUp(self):
        """Set up test data"""
        self.factory = RequestFactory()
        self.permission = CanManageUsers()

        self.admin = User.objects.create_user(
            username='admin',
            password='pass123',
            role='admin'
        )

        self.technician = User.objects.create_user(
            username='tech',
            password='pass123',
            role='technician'
        )

    def test_any_user_can_read(self):
        """Test any authenticated user can read users"""
        request = self.factory.get('/')
        request.user = self.technician

        self.assertTrue(self.permission.has_permission(request, None))

    def test_only_admin_can_create(self):
        """Test only admin can create users"""
        # Admin can create
        request = self.factory.post('/')
        request.user = self.admin
        self.assertTrue(self.permission.has_permission(request, None))

        # Technician cannot create
        request.user = self.technician
        self.assertFalse(self.permission.has_permission(request, None))


class CanCreateJobPermissionTestCase(TestCase):
    """Test cases for CanCreateJob permission"""

    def setUp(self):
        """Set up test data"""
        self.factory = RequestFactory()
        self.permission = CanCreateJob()

        self.admin = User.objects.create_user(
            username='admin',
            password='pass123',
            role='admin'
        )

        self.sales_agent = User.objects.create_user(
            username='sales',
            password='pass123',
            role='sales_agent'
        )

        self.technician = User.objects.create_user(
            username='tech',
            password='pass123',
            role='technician'
        )

    def test_any_user_can_read_jobs(self):
        """Test any authenticated user can read jobs"""
        request = self.factory.get('/')
        request.user = self.technician

        self.assertTrue(self.permission.has_permission(request, None))

    def test_admin_can_create_job(self):
        """Test admin can create jobs"""
        request = self.factory.post('/')
        request.user = self.admin

        self.assertTrue(self.permission.has_permission(request, None))

    def test_sales_agent_can_create_job(self):
        """Test sales agent can create jobs"""
        request = self.factory.post('/')
        request.user = self.sales_agent

        self.assertTrue(self.permission.has_permission(request, None))

    def test_technician_cannot_create_job(self):
        """Test technician cannot create jobs"""
        request = self.factory.post('/')
        request.user = self.technician

        self.assertFalse(self.permission.has_permission(request, None))


class CanUpdateJobProgressPermissionTestCase(TestCase):
    """Test cases for CanUpdateJobProgress permission"""

    def setUp(self):
        """Set up test data"""
        self.factory = RequestFactory()
        self.permission = CanUpdateJobProgress()

        self.admin = User.objects.create_user(
            username='admin',
            password='pass123',
            role='admin'
        )

        self.sales_agent = User.objects.create_user(
            username='sales',
            password='pass123',
            role='sales_agent'
        )

        self.technician1 = User.objects.create_user(
            username='tech1',
            password='pass123',
            role='technician'
        )

        self.technician2 = User.objects.create_user(
            username='tech2',
            password='pass123',
            role='technician'
        )

        self.job = Job.objects.create(
            title='Test Job',
            description='Test',
            client_name='Client',
            created_by=self.sales_agent,
            assigned_to=self.technician1,
            scheduled_date=timezone.now().date()
        )

    def test_any_user_can_read(self):
        """Test any authenticated user can read jobs"""
        request = self.factory.get('/')
        request.user = self.technician2

        self.assertTrue(self.permission.has_object_permission(request, None, self.job))

    def test_admin_can_update_any_job(self):
        """Test admin can update any job"""
        request = self.factory.put('/')
        request.user = self.admin

        self.assertTrue(self.permission.has_object_permission(request, None, self.job))

    def test_assigned_technician_can_update(self):
        """Test assigned technician can update their job"""
        request = self.factory.put('/')
        request.user = self.technician1

        self.assertTrue(self.permission.has_object_permission(request, None, self.job))

    def test_unassigned_technician_cannot_update(self):
        """Test unassigned technician cannot update job"""
        request = self.factory.put('/')
        request.user = self.technician2

        self.assertFalse(self.permission.has_object_permission(request, None, self.job))

    def test_creator_sales_agent_can_update(self):
        """Test sales agent who created job can update it"""
        request = self.factory.put('/')
        request.user = self.sales_agent

        self.assertTrue(self.permission.has_object_permission(request, None, self.job))


class CanManageEquipmentPermissionTestCase(TestCase):
    """Test cases for CanManageEquipment permission"""

    def setUp(self):
        """Set up test data"""
        self.factory = RequestFactory()
        self.permission = CanManageEquipment()

        self.admin = User.objects.create_user(
            username='admin',
            password='pass123',
            role='admin'
        )

        self.technician = User.objects.create_user(
            username='tech',
            password='pass123',
            role='technician'
        )

    def test_any_user_can_read_equipment(self):
        """Test any authenticated user can read equipment"""
        request = self.factory.get('/')
        request.user = self.technician

        self.assertTrue(self.permission.has_permission(request, None))

    def test_only_admin_can_create_equipment(self):
        """Test only admin can create equipment"""
        # Admin can create
        request = self.factory.post('/')
        request.user = self.admin
        self.assertTrue(self.permission.has_permission(request, None))

        # Technician cannot create
        request.user = self.technician
        self.assertFalse(self.permission.has_permission(request, None))


class CanViewAnalyticsPermissionTestCase(TestCase):
    """Test cases for CanViewAnalytics permission"""

    def setUp(self):
        """Set up test data"""
        self.factory = RequestFactory()
        self.permission = CanViewAnalytics()

        self.admin = User.objects.create_user(
            username='admin',
            password='pass123',
            role='admin'
        )

        self.sales_agent = User.objects.create_user(
            username='sales',
            password='pass123',
            role='sales_agent'
        )

    def test_admin_can_view_analytics(self):
        """Test admin can view analytics"""
        request = self.factory.get('/')
        request.user = self.admin

        self.assertTrue(self.permission.has_permission(request, None))

    def test_non_admin_cannot_view_analytics(self):
        """Test non-admin cannot view analytics"""
        request = self.factory.get('/')
        request.user = self.sales_agent

        self.assertFalse(self.permission.has_permission(request, None))