from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta

from ops.models import Equipment, Job, JobTask
from ops.serializers import (
    EquipmentSerializer, JobSerializer, JobCreateSerializer, JobTaskSerializer
)

User = get_user_model()


class EquipmentSerializerTestCase(TestCase):
    """Test cases for Equipment serializer"""

    def setUp(self):
        """Set up test data"""
        self.equipment = Equipment.objects.create(
            name='Test Drill',
            type='tool',
            serial_number='TD-001',
            description='Heavy duty drill',
            is_active=True
        )

    def test_equipment_serializer_contains_expected_fields(self):
        """Test EquipmentSerializer contains expected fields"""
        serializer = EquipmentSerializer(instance=self.equipment)
        data = serializer.data

        self.assertEqual(set(data.keys()), {
            'id', 'name', 'type', 'serial_number', 'is_active',
            'description', 'created_at', 'updated_at'
        })

    def test_equipment_serializer_validates_unique_serial(self):
        """Test serial number uniqueness validation"""
        data = {
            'name': 'Another Drill',
            'type': 'tool',
            'serial_number': 'TD-001',  # Duplicate
            'is_active': True
        }
        serializer = EquipmentSerializer(data=data)

        self.assertFalse(serializer.is_valid())
        self.assertIn('serial_number', serializer.errors)

    def test_equipment_serializer_creates_equipment(self):
        """Test EquipmentSerializer creates equipment correctly"""
        data = {
            'name': 'Hydraulic Lift',
            'type': 'machine',
            'serial_number': 'HL-001',
            'description': 'Heavy duty lift',
            'is_active': True
        }
        serializer = EquipmentSerializer(data=data)

        self.assertTrue(serializer.is_valid())
        equipment = serializer.save()

        self.assertEqual(equipment.name, 'Hydraulic Lift')
        self.assertEqual(equipment.type, 'machine')


class JobSerializerTestCase(TestCase):
    """Test cases for Job serializers"""

    def setUp(self):
        """Set up test data"""
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

    def test_job_serializer_contains_expected_fields(self):
        """Test JobSerializer contains expected fields"""
        serializer = JobSerializer(instance=self.job)
        data = serializer.data

        expected_fields = {
            'id', 'title', 'description', 'client_name', 'created_by',
            'assigned_to', 'status', 'priority', 'scheduled_date', 'overdue',
            'tasks', 'tasks_count', 'completed_tasks_count', 'progress_percentage',
            'created_at', 'updated_at'
        }
        self.assertEqual(set(data.keys()), expected_fields)

    def test_job_serializer_calculates_progress(self):
        """Test JobSerializer calculates progress percentage correctly"""
        # Create tasks
        JobTask.objects.create(
            job=self.job,
            title='Task 1',
            description='Test',
            status='completed',
            order=1
        )
        JobTask.objects.create(
            job=self.job,
            title='Task 2',
            description='Test',
            status='pending',
            order=2
        )

        serializer = JobSerializer(instance=self.job)
        data = serializer.data

        self.assertEqual(data['tasks_count'], 2)
        self.assertEqual(data['completed_tasks_count'], 1)
        self.assertEqual(data['progress_percentage'], 50.0)

    def test_job_create_serializer_creates_job(self):
        """Test JobCreateSerializer creates job correctly"""
        data = {
            'title': 'New Job',
            'description': 'New job description',
            'client_name': 'New Client',
            'assigned_to_id': self.technician.id,
            'priority': 'medium',
            'scheduled_date': (timezone.now().date() + timedelta(days=2)).isoformat()
        }
        serializer = JobCreateSerializer(data=data)

        self.assertTrue(serializer.is_valid())
        job = serializer.save(created_by=self.admin)

        self.assertEqual(job.title, 'New Job')
        self.assertEqual(job.assigned_to, self.technician)
        self.assertEqual(job.created_by, self.admin)

    def test_job_serializer_validates_client_name(self):
        """Test client name validation"""
        data = {
            'title': 'Test Job',
            'description': 'Test',
            'client_name': '   ',  # Empty after strip
            'priority': 'low',
            'scheduled_date': timezone.now().date().isoformat()
        }
        serializer = JobCreateSerializer(data=data)

        self.assertFalse(serializer.is_valid())
        self.assertIn('client_name', serializer.errors)


class JobTaskSerializerTestCase(TestCase):
    """Test cases for JobTask serializer"""

    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='testuser',
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

    def test_task_serializer_contains_expected_fields(self):
        """Test JobTaskSerializer contains expected fields"""
        serializer = JobTaskSerializer(instance=self.task)
        data = serializer.data

        expected_fields = {
            'id', 'job', 'title', 'description', 'status', 'order',
            'required_equipment', 'completed_at', 'created_at', 'updated_at'
        }
        self.assertEqual(set(data.keys()), expected_fields)

    def test_task_serializer_includes_equipment(self):
        """Test JobTaskSerializer includes equipment details"""
        serializer = JobTaskSerializer(instance=self.task)
        data = serializer.data

        self.assertEqual(len(data['required_equipment']), 1)
        self.assertEqual(data['required_equipment'][0]['name'], 'Test Tool')

    def test_task_serializer_validates_order(self):
        """Test task order validation"""
        data = {
            'job': self.job.id,
            'title': 'New Task',
            'description': 'Test',
            'order': -1  # Invalid
        }
        serializer = JobTaskSerializer(data=data)

        self.assertFalse(serializer.is_valid())
        self.assertIn('order', serializer.errors)

    def test_task_serializer_creates_task_with_equipment(self):
        """Test JobTaskSerializer creates task with equipment"""
        data = {
            'job': self.job.id,
            'title': 'New Task',
            'description': 'New task description',
            'order': 2,
            'required_equipment_ids': [self.equipment.id]
        }
        serializer = JobTaskSerializer(data=data)

        self.assertTrue(serializer.is_valid())
        task = serializer.save()

        self.assertEqual(task.title, 'New Task')
        self.assertEqual(task.required_equipment.count(), 1)