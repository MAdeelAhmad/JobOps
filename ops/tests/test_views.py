from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta

from ops.models import Equipment, Job, JobTask

User = get_user_model()


class EquipmentViewSetTestCase(TestCase):
    """Test cases for Equipment ViewSet"""

    def setUp(self):
        """Set up test data"""
        self.client = APIClient()

        self.admin = User.objects.create_user(
            username='admin',
            password='admin123',
            role='admin'
        )

        self.technician = User.objects.create_user(
            username='tech',
            password='tech123',
            role='technician'
        )

        self.equipment = Equipment.objects.create(
            name='Test Drill',
            type='tool',
            serial_number='TD-001',
            is_active=True
        )

    def test_list_equipment_authenticated(self):
        """Test authenticated users can list equipment"""
        self.client.force_authenticate(user=self.technician)
        url = reverse('equipment-list')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data['results']), 1)

    def test_create_equipment_admin_only(self):
        """Test only admins can create equipment"""
        self.client.force_authenticate(user=self.admin)
        url = reverse('equipment-list')
        data = {
            'name': 'Hydraulic Lift',
            'type': 'machine',
            'serial_number': 'HL-001',
            'is_active': True,
            'description': 'Heavy duty lift'
        }
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Equipment.objects.filter(serial_number='HL-001').count(), 1)

    def test_create_equipment_technician_forbidden(self):
        """Test technicians cannot create equipment"""
        self.client.force_authenticate(user=self.technician)
        url = reverse('equipment-list')
        data = {
            'name': 'New Tool',
            'type': 'tool',
            'serial_number': 'NT-001',
            'is_active': True
        }
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_filter_equipment_by_type(self):
        """Test filtering equipment by type"""
        self.client.force_authenticate(user=self.technician)
        url = reverse('equipment-list')
        response = self.client.get(url, {'type': 'tool'})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        for equipment in response.data['results']:
            self.assertEqual(equipment['type'], 'tool')

    def test_get_equipment_usage_stats(self):
        """Test getting equipment usage statistics"""
        self.client.force_authenticate(user=self.admin)
        url = reverse('equipment-usage-stats', kwargs={'pk': self.equipment.pk})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('equipment_id', response.data)
        self.assertIn('total_tasks', response.data)


class JobViewSetTestCase(TestCase):
    """Test cases for Job ViewSet"""

    def setUp(self):
        """Set up test data"""
        self.client = APIClient()

        self.admin = User.objects.create_user(
            username='admin',
            email='admin@test.com',
            password='admin123',
            role='admin'
        )

        self.sales_agent = User.objects.create_user(
            username='sales',
            email='sales@test.com',
            password='sales123',
            role='sales_agent'
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
            created_by=self.sales_agent,
            assigned_to=self.technician,
            status='pending',
            priority='high',
            scheduled_date=timezone.now().date() + timedelta(days=1)
        )

    def test_list_jobs_authenticated(self):
        """Test authenticated users can list jobs"""
        self.client.force_authenticate(user=self.technician)
        url = reverse('job-list')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_technician_sees_only_assigned_jobs(self):
        """Test technicians see only their assigned jobs"""
        # Create another job assigned to different technician
        other_tech = User.objects.create_user(
            username='other_tech',
            password='pass123',
            role='technician'
        )
        Job.objects.create(
            title='Other Job',
            description='Other',
            client_name='Other Client',
            created_by=self.admin,
            assigned_to=other_tech,
            scheduled_date=timezone.now().date()
        )

        self.client.force_authenticate(user=self.technician)
        url = reverse('job-list')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['title'], 'Test Job')

    def test_create_job_sales_agent(self):
        """Test sales agents can create jobs"""
        self.client.force_authenticate(user=self.sales_agent)
        url = reverse('job-list')
        data = {
            'title': 'New Installation',
            'description': 'Install new system',
            'client_name': 'New Client',
            'assigned_to_id': self.technician.id,
            'priority': 'medium',
            'scheduled_date': (timezone.now().date() + timedelta(days=2)).isoformat()
        }
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Job.objects.filter(title='New Installation').count(), 1)

    def test_create_job_technician_forbidden(self):
        """Test technicians cannot create jobs"""
        self.client.force_authenticate(user=self.technician)
        url = reverse('job-list')
        data = {
            'title': 'Unauthorized Job',
            'description': 'Should fail',
            'client_name': 'Client',
            'priority': 'low',
            'scheduled_date': timezone.now().date().isoformat()
        }
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_update_job_by_assigned_technician(self):
        """Test assigned technician can update job status"""
        self.client.force_authenticate(user=self.technician)
        url = reverse('job-detail', kwargs={'pk': self.job.pk})
        data = {
            'status': 'in_progress'
        }
        response = self.client.patch(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.job.refresh_from_db()
        self.assertEqual(self.job.status, 'in_progress')

    def test_filter_jobs_by_status(self):
        """Test filtering jobs by status"""
        self.client.force_authenticate(user=self.admin)
        url = reverse('job-list')
        response = self.client.get(url, {'status': 'pending'})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        for job in response.data['results']:
            self.assertEqual(job['status'], 'pending')

    def test_get_job_change_logs(self):
        """Test getting job change logs"""
        # Create a change log
        from ops.models import JobChangeLog
        JobChangeLog.objects.create(
            job=self.job,
            user=self.sales_agent,
            action='created',
            changes={'status': 'Job created'}
        )

        self.client.force_authenticate(user=self.admin)
        url = reverse('job-change-logs', kwargs={'pk': self.job.pk})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreater(len(response.data), 0)

    def test_complete_job_with_incomplete_tasks(self):
        """Test cannot complete job with incomplete tasks"""
        JobTask.objects.create(
            job=self.job,
            title='Pending Task',
            description='Test',
            status='pending',
            order=1
        )

        self.client.force_authenticate(user=self.technician)
        url = reverse('job-complete', kwargs={'pk': self.job.pk})
        response = self.client.post(url)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)

    def test_complete_job_with_all_tasks_completed(self):
        """Test can complete job when all tasks are completed"""
        JobTask.objects.create(
            job=self.job,
            title='Completed Task',
            description='Test',
            status='completed',
            order=1
        )

        self.client.force_authenticate(user=self.technician)
        url = reverse('job-complete', kwargs={'pk': self.job.pk})
        response = self.client.post(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.job.refresh_from_db()
        self.assertEqual(self.job.status, 'completed')


class JobTaskViewSetTestCase(TestCase):
    """Test cases for JobTask ViewSet"""

    def setUp(self):
        """Set up test data"""
        self.client = APIClient()

        self.technician = User.objects.create_user(
            username='tech',
            email='tech@test.com',
            password='tech123',
            role='technician'
        )

        self.admin = User.objects.create_user(
            username='admin',
            password='admin123',
            role='admin'
        )

        self.job = Job.objects.create(
            title='Test Job',
            description='Test',
            client_name='Client',
            created_by=self.admin,
            assigned_to=self.technician,
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

    def test_list_tasks_authenticated(self):
        """Test authenticated users can list tasks"""
        self.client.force_authenticate(user=self.technician)
        url = reverse('task-list')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_create_task(self):
        """Test creating a task"""
        self.client.force_authenticate(user=self.admin)
        url = reverse('task-list')
        data = {
            'job': self.job.id,
            'title': 'New Task',
            'description': 'New task description',
            'order': 2,
            'required_equipment_ids': [self.equipment.id]
        }
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(JobTask.objects.filter(title='New Task').count(), 1)

    def test_update_task_status_by_assigned_technician(self):
        """Test assigned technician can update task status"""
        self.client.force_authenticate(user=self.technician)
        url = reverse('task-detail', kwargs={'pk': self.task.pk})
        data = {
            'status': 'in_progress'
        }
        response = self.client.patch(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.task.refresh_from_db()
        self.assertEqual(self.task.status, 'in_progress')

    def test_task_completed_at_auto_set(self):
        """Test completed_at is set automatically when status is completed"""
        self.client.force_authenticate(user=self.technician)
        url = reverse('task-detail', kwargs={'pk': self.task.pk})
        data = {
            'status': 'completed'
        }
        response = self.client.patch(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.task.refresh_from_db()
        self.assertIsNotNone(self.task.completed_at)

    def test_filter_tasks_by_job(self):
        """Test filtering tasks by job"""
        self.client.force_authenticate(user=self.technician)
        url = reverse('task-list')
        response = self.client.get(url, {'job': self.job.id})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        for task in response.data['results']:
            self.assertEqual(task['job'], self.job.id)


class TechnicianDashboardViewTestCase(TestCase):
    """Test cases for Technician Dashboard View"""

    def setUp(self):
        """Set up test data"""
        self.client = APIClient()

        self.technician = User.objects.create_user(
            username='tech',
            email='tech@test.com',
            password='tech123',
            role='technician'
        )

        self.job = Job.objects.create(
            title='Today Job',
            description='Job for today',
            client_name='Client',
            created_by=self.technician,
            assigned_to=self.technician,
            scheduled_date=timezone.now().date(),
            status='pending'
        )

        self.task = JobTask.objects.create(
            job=self.job,
            title='Today Task',
            description='Task for today',
            status='pending',
            order=1
        )

    def test_get_technician_dashboard(self):
        """Test technician can get their dashboard"""
        self.client.force_authenticate(user=self.technician)
        url = reverse('technician-dashboard')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data, list)

    def test_dashboard_shows_upcoming_tasks(self):
        """Test dashboard shows upcoming tasks"""
        self.client.force_authenticate(user=self.technician)
        url = reverse('technician-dashboard')
        response = self.client.get(url, {'days': 7})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreater(len(response.data), 0)

    def test_dashboard_unauthenticated(self):
        """Test unauthenticated users cannot access dashboard"""
        url = reverse('technician-dashboard')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class JobAnalyticsViewTestCase(TestCase):
    """Test cases for Job Analytics View"""

    def setUp(self):
        """Set up test data"""
        self.client = APIClient()

        self.admin = User.objects.create_user(
            username='admin',
            password='admin123',
            role='admin'
        )

        self.technician = User.objects.create_user(
            username='tech',
            password='tech123',
            role='technician'
        )

        # Create some jobs for analytics
        for i in range(5):
            Job.objects.create(
                title=f'Job {i}',
                description='Test',
                client_name='Client',
                created_by=self.admin,
                scheduled_date=timezone.now().date(),
                status='completed' if i < 3 else 'pending'
            )

    def test_get_analytics_admin_only(self):
        """Test only admins can access analytics"""
        self.client.force_authenticate(user=self.admin)
        url = reverse('job-analytics')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('total_jobs', response.data)
        self.assertIn('completed_jobs', response.data)

    def test_analytics_technician_forbidden(self):
        """Test technicians cannot access analytics"""
        self.client.force_authenticate(user=self.technician)
        url = reverse('job-analytics')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_analytics_contains_correct_data(self):
        """Test analytics returns correct statistics"""
        self.client.force_authenticate(user=self.admin)
        url = reverse('job-analytics')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['total_jobs'], 5)
        self.assertEqual(response.data['completed_jobs'], 3)
        self.assertEqual(response.data['pending_jobs'], 2)