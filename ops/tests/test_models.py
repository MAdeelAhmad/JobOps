from django.test import TestCase
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta

from ops.models import Equipment, Job, JobTask, JobChangeLog

User = get_user_model()


class EquipmentModelTest(TestCase):
    """Test cases for Equipment model"""

    def setUp(self):
        """Set up test data"""
        self.equipment = Equipment.objects.create(
            name='Test Drill',
            type='tool',
            serial_number='TD-001',
            description='Heavy duty drill',
            is_active=True
        )

    def test_equipment_creation(self):
        """Test equipment is created correctly"""
        self.assertEqual(self.equipment.name, 'Test Drill')
        self.assertEqual(self.equipment.type, 'tool')
        self.assertTrue(self.equipment.is_active)

    def test_equipment_string_representation(self):
        """Test equipment string representation"""
        expected = f"{self.equipment.name} ({self.equipment.serial_number})"
        self.assertEqual(str(self.equipment), expected)

    def test_unique_serial_number(self):
        """Test serial number must be unique"""
        with self.assertRaises(Exception):
            Equipment.objects.create(
                name='Another Drill',
                type='tool',
                serial_number='TD-001',  # Duplicate
                is_active=True
            )

    def test_equipment_type_choices(self):
        """Test equipment type choices"""
        valid_types = ['tool', 'machine', 'vehicle', 'accessory']
        self.assertIn(self.equipment.type, valid_types)


class JobModelTest(TestCase):
    """Test cases for Job model"""

    def setUp(self):
        """Set up test data"""
        self.admin = User.objects.create_user(
            username='admin',
            email='admin@test.com',
            password='pass123',
            role='admin'
        )

        self.technician = User.objects.create_user(
            username='tech',
            email='tech@test.com',
            password='pass123',
            role='technician'
        )

        self.job = Job.objects.create(
            title='Test Job',
            description='Test Description',
            client_name='Test Client',
            created_by=self.admin,
            assigned_to=self.technician,
            status='pending',
            priority='high',
            scheduled_date=timezone.now().date() + timedelta(days=1)
        )

    def test_job_creation(self):
        """Test job is created correctly"""
        self.assertEqual(self.job.title, 'Test Job')
        self.assertEqual(self.job.status, 'pending')
        self.assertEqual(self.job.assigned_to, self.technician)
        self.assertFalse(self.job.overdue)

    def test_job_string_representation(self):
        """Test job string representation"""
        expected = f"{self.job.title} - {self.job.client_name}"
        self.assertEqual(str(self.job), expected)

    def test_can_complete_with_no_tasks(self):
        """Test job can be completed if it has no tasks"""
        self.assertTrue(self.job.can_complete())

    def test_can_complete_with_incomplete_tasks(self):
        """Test job cannot be completed if tasks are incomplete"""
        JobTask.objects.create(
            job=self.job,
            title='Test Task',
            description='Test',
            status='pending',
            order=1
        )
        self.assertFalse(self.job.can_complete())

    def test_can_complete_with_all_tasks_completed(self):
        """Test job can be completed if all tasks are completed"""
        JobTask.objects.create(
            job=self.job,
            title='Test Task',
            description='Test',
            status='completed',
            order=1
        )
        self.assertTrue(self.job.can_complete())

    def test_cannot_mark_completed_with_pending_tasks(self):
        """Test validation error when trying to complete job with pending tasks"""
        JobTask.objects.create(
            job=self.job,
            title='Pending Task',
            description='Test',
            status='pending',
            order=1
        )

        self.job.status = 'completed'
        with self.assertRaises(ValidationError):
            self.job.save()

    def test_job_status_choices(self):
        """Test job status choices"""
        valid_statuses = ['pending', 'in_progress', 'completed', 'cancelled']
        self.assertIn(self.job.status, valid_statuses)

    def test_job_priority_choices(self):
        """Test job priority choices"""
        valid_priorities = ['low', 'medium', 'high', 'urgent']
        self.assertIn(self.job.priority, valid_priorities)


class JobTaskModelTest(TestCase):
    """Test cases for JobTask model"""

    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='test_user',
            email='user@test.com',
            password='pass123',
            role='technician'
        )

        self.job = Job.objects.create(
            title='Test Job',
            description='Test',
            client_name='Client',
            created_by=self.user,
            scheduled_date=timezone.now().date()
        )

        self.equipment = Equipment.objects.create(
            name='Test Tool',
            type='tool',
            serial_number='TT-001',
            is_active=True
        )

        self.task = JobTask.objects.create(
            job=self.job,
            title='Test Task',
            description='Task Description',
            status='pending',
            order=1
        )
        self.task.required_equipment.add(self.equipment)

    def test_task_creation(self):
        """Test task is created correctly"""
        self.assertEqual(self.task.title, 'Test Task')
        self.assertEqual(self.task.status, 'pending')
        self.assertEqual(self.task.order, 1)
        self.assertIsNone(self.task.completed_at)

    def test_task_string_representation(self):
        """Test task string representation"""
        expected = f"{self.job.title} - Step {self.task.order}: {self.task.title}"
        self.assertEqual(str(self.task), expected)

    def test_task_completed_at_auto_set(self):
        """Test completed_at is automatically set when status is completed"""
        self.task.status = 'completed'
        self.task.save()
        self.assertIsNotNone(self.task.completed_at)

    def test_task_equipment_relationship(self):
        """Test task can have multiple equipment"""
        self.assertEqual(self.task.required_equipment.count(), 1)
        self.assertIn(self.equipment, self.task.required_equipment.all())

    def test_task_status_choices(self):
        """Test task status choices"""
        valid_statuses = ['pending', 'in_progress', 'completed']
        self.assertIn(self.task.status, valid_statuses)


class JobChangeLogModelTest(TestCase):
    """Test cases for JobChangeLog model"""

    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='test_user',
            email='user@test.com',
            password='pass123'
        )

        self.job = Job.objects.create(
            title='Test Job',
            description='Test',
            client_name='Client',
            created_by=self.user,
            scheduled_date=timezone.now().date()
        )

        self.log = JobChangeLog.objects.create(
            job=self.job,
            user=self.user,
            action='created',
            changes={'status': 'Job created'}
        )

    def test_change_log_creation(self):
        """Test change log is created correctly"""
        self.assertEqual(self.log.job, self.job)
        self.assertEqual(self.log.user, self.user)
        self.assertEqual(self.log.action, 'created')

    def test_change_log_string_representation(self):
        """Test change log string representation"""
        self.assertIn(self.job.title, str(self.log))
        self.assertIn(self.log.action, str(self.log))

    def test_change_log_ordering(self):
        """Test change logs are ordered by timestamp descending"""
        log2 = JobChangeLog.objects.create(
            job=self.job,
            user=self.user,
            action='updated',
            changes={'status': 'Status updated'}
        )

        logs = JobChangeLog.objects.all()
        self.assertEqual(logs[0], log2)  # Most recent first