"""
Views for ops app - JobOps system.
"""
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from django.db.models import Count
from django.utils import timezone
from datetime import timedelta
from collections import defaultdict
from django_filters.rest_framework import DjangoFilterBackend

from ops.models import Equipment, Job, JobTask, JobChangeLog
from ops.serializers import (
    EquipmentSerializer, EquipmentListSerializer,
    JobSerializer, JobListSerializer, JobCreateSerializer, JobUpdateSerializer,
    JobTaskSerializer, JobTaskCreateSerializer,
    JobChangeLogSerializer, JobAnalyticsSerializer,
)
from ops.permissions import (
    CanCreateJob, CanUpdateJobProgress, CanManageEquipment, CanViewAnalytics
)


class EquipmentViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Equipment management.

    All authenticated users can view equipment.
    Only admins can create/update/delete equipment.
    """

    queryset = Equipment.objects.all()
    permission_classes = [CanManageEquipment]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['type', 'is_active']
    search_fields = ['name', 'serial_number', 'description']
    ordering_fields = ['name', 'type', 'created_at']
    ordering = ['name']

    def get_serializer_class(self):
        """Return lightweight serializer for list view"""
        if self.action == 'list':
            return EquipmentListSerializer
        return EquipmentSerializer

    def get_queryset(self):
        """Filter equipment based on query parameters"""
        queryset = Equipment.objects.all()

        is_active = self.request.query_params.get('is_active', None)
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')

        equipment_type = self.request.query_params.get('type', None)
        if equipment_type:
            queryset = queryset.filter(type=equipment_type)

        return queryset

    @action(detail=True, methods=['get'])
    def usage_stats(self, request, pk=None):
        """Get usage statistics for specific equipment"""
        equipment = self.get_object()

        total_tasks = equipment.tasks.count()
        completed_tasks = equipment.tasks.filter(status='completed').count()
        pending_tasks = equipment.tasks.filter(status='pending').count()
        in_progress_tasks = equipment.tasks.filter(status='in_progress').count()

        return Response({
            'equipment_id': equipment.id,
            'equipment_name': equipment.name,
            'total_tasks': total_tasks,
            'completed_tasks': completed_tasks,
            'pending_tasks': pending_tasks,
            'in_progress_tasks': in_progress_tasks
        })


class JobViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Job management.

    Admins and sales agents can create jobs.
    Only assigned technicians can update their jobs.
    """

    queryset = Job.objects.all()
    permission_classes = [CanCreateJob, CanUpdateJobProgress]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'priority', 'overdue', 'assigned_to']
    search_fields = ['title', 'client_name', 'description']
    ordering_fields = ['created_at', 'scheduled_date', 'priority']
    ordering = ['-created_at']

    def get_serializer_class(self):
        """Return appropriate serializer based on action"""
        if self.action == 'create':
            return JobCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return JobUpdateSerializer
        elif self.action == 'list':
            return JobListSerializer
        return JobSerializer

    def get_queryset(self):
        """Filter jobs based on user role and query parameters"""
        queryset = Job.objects.select_related('created_by', 'assigned_to').prefetch_related('tasks')

        user = self.request.user
        if user.role == 'technician':
            queryset = queryset.filter(assigned_to=user)
        elif user.role == 'sales_agent':
            queryset = queryset.filter(created_by=user)

        status_filter = self.request.query_params.get('status', None)
        if status_filter:
            queryset = queryset.filter(status=status_filter)

        priority = self.request.query_params.get('priority', None)
        if priority:
            queryset = queryset.filter(priority=priority)

        assigned_to = self.request.query_params.get('assigned_to', None)
        if assigned_to:
            queryset = queryset.filter(assigned_to_id=assigned_to)

        overdue = self.request.query_params.get('overdue', None)
        if overdue is not None:
            queryset = queryset.filter(overdue=overdue.lower() == 'true')

        start_date = self.request.query_params.get('start_date', None)
        end_date = self.request.query_params.get('end_date', None)
        if start_date:
            queryset = queryset.filter(scheduled_date__gte=start_date)
        if end_date:
            queryset = queryset.filter(scheduled_date__lte=end_date)

        return queryset

    def perform_create(self, serializer):
        """Set created_by to current user and log creation"""
        job = serializer.save(created_by=self.request.user)

        JobChangeLog.objects.create(
            job=job,
            user=self.request.user,
            action='created',
            changes={
                'status': 'Job created',
                'title': job.title,
                'client_name': job.client_name
            }
        )

    def perform_update(self, serializer):
        """Log status changes"""
        old_instance = self.get_object()
        old_status = old_instance.status
        old_assigned = old_instance.assigned_to

        job = serializer.save()

        changes = {}

        if old_status != job.status:
            changes['status'] = {
                'old': old_status,
                'new': job.status
            }

        if old_assigned != job.assigned_to:
            changes['assigned_to'] = {
                'old': old_assigned.username if old_assigned else None,
                'new': job.assigned_to.username if job.assigned_to else None
            }

        if changes:
            JobChangeLog.objects.create(
                job=job,
                user=self.request.user,
                action='updated',
                changes=changes
            )

    @action(detail=True, methods=['get'])
    def change_logs(self, request, pk=None):
        """Get change logs for a specific job"""
        job = self.get_object()
        logs = job.change_logs.all()
        serializer = JobChangeLogSerializer(logs, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        """Mark job as completed (if all tasks are done)"""
        job = self.get_object()

        if not job.can_complete():
            return Response(
                {'error': 'Cannot complete job. All tasks must be completed first.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        job.status = 'completed'
        job.save()

        JobChangeLog.objects.create(
            job=job,
            user=request.user,
            action='completed',
            changes={'status': 'Job marked as completed'}
        )

        serializer = self.get_serializer(job)
        return Response(serializer.data)


class JobTaskViewSet(viewsets.ModelViewSet):
    """
    ViewSet for JobTask management.

    Only assigned technicians can update tasks for their jobs.
    """

    queryset = JobTask.objects.all()
    permission_classes = [IsAuthenticated, CanUpdateJobProgress]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['job', 'status']
    ordering_fields = ['order', 'created_at']
    ordering = ['order']

    def get_serializer_class(self):
        """Return appropriate serializer based on action"""
        if self.action == 'create':
            return JobTaskCreateSerializer
        return JobTaskSerializer

    def get_queryset(self):
        """Filter tasks based on job and status"""
        queryset = JobTask.objects.select_related('job').prefetch_related('required_equipment')

        job_id = self.request.query_params.get('job', None)
        if job_id:
            queryset = queryset.filter(job_id=job_id)

        status_filter = self.request.query_params.get('status', None)
        if status_filter:
            queryset = queryset.filter(status=status_filter)

        if self.request.user.role == 'technician':
            queryset = queryset.filter(job__assigned_to=self.request.user)

        return queryset

    def perform_update(self, serializer):
        """Log task updates and handle completion"""
        old_status = self.get_object().status
        task = serializer.save()

        if old_status != task.status:
            JobChangeLog.objects.create(
                job=task.job,
                user=self.request.user,
                action='task_updated',
                changes={
                    'task_id': task.id,
                    'task_title': task.title,
                    'old_status': old_status,
                    'new_status': task.status
                }
            )


class TechnicianDashboardView(APIView):
    """
    Dashboard view for technicians showing daily tasks.

    GET /ops/technician-dashboard/?days=7
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Get upcoming tasks for technician"""
        user = request.user

        today = timezone.now().date()
        days_ahead = int(request.query_params.get('days', 7))
        end_date = today + timedelta(days=days_ahead)

        if user.role == 'technician':
            jobs = Job.objects.filter(
                assigned_to=user,
                scheduled_date__gte=today,
                scheduled_date__lte=end_date
            ).exclude(status='completed')
        else:
            jobs = Job.objects.filter(
                scheduled_date__gte=today,
                scheduled_date__lte=end_date
            ).exclude(status='completed')

        tasks_by_date = defaultdict(list)

        for job in jobs:
            tasks = job.tasks.exclude(status='completed')
            for task in tasks:
                task_data = {
                    'task_id': task.id,
                    'task_title': task.title,
                    'task_description': task.description,
                    'task_status': task.status,
                    'task_order': task.order,
                    'job_id': job.id,
                    'job_title': job.title,
                    'client_name': job.client_name,
                    'priority': job.priority,
                    'job_status': job.status,
                    'equipment': [
                        {
                            'id': eq.id,
                            'name': eq.name,
                            'serial_number': eq.serial_number,
                            'type': eq.type
                        }
                        for eq in task.required_equipment.all()
                    ]
                }
                tasks_by_date[str(job.scheduled_date)].append(task_data)

        response_data = [
            {
                'date': date,
                'tasks': tasks,
                'total_tasks': len(tasks)
            }
            for date, tasks in sorted(tasks_by_date.items())
        ]

        return Response(response_data)


class JobAnalyticsView(APIView):
    """
    Admin-only analytics endpoint for job statistics.

    GET /ops/analytics/
    """

    permission_classes = [CanViewAnalytics]

    def get(self, request):
        """Get comprehensive job analytics"""

        total_jobs = Job.objects.count()
        completed_jobs = Job.objects.filter(status='completed').count()
        pending_jobs = Job.objects.filter(status='pending').count()
        in_progress_jobs = Job.objects.filter(status='in_progress').count()
        cancelled_jobs = Job.objects.filter(status='cancelled').count()
        overdue_jobs = Job.objects.filter(overdue=True).count()

        completed_tasks = JobTask.objects.filter(
            status='completed',
            completed_at__isnull=False
        )

        avg_time = 0
        if completed_tasks.exists():
            time_diffs = [
                (task.completed_at - task.created_at).total_seconds() / 3600
                for task in completed_tasks
                if task.completed_at and task.created_at
            ]
            avg_time = sum(time_diffs) / len(time_diffs) if time_diffs else 0

        equipment_usage = Equipment.objects.annotate(
            usage_count=Count('tasks')
        ).filter(usage_count__gt=0).order_by('-usage_count')[:10]

        most_used_equipment = [
            {
                'id': eq.id,
                'name': eq.name,
                'type': eq.type,
                'serial_number': eq.serial_number,
                'usage_count': eq.usage_count
            }
            for eq in equipment_usage
        ]

        jobs_by_priority = dict(
            Job.objects.values('priority').annotate(
                count=Count('id')
            ).values_list('priority', 'count')
        )

        jobs_by_status = dict(
            Job.objects.values('status').annotate(
                count=Count('id')
            ).values_list('status', 'count')
        )

        analytics_data = {
            'total_jobs': total_jobs,
            'completed_jobs': completed_jobs,
            'pending_jobs': pending_jobs,
            'in_progress_jobs': in_progress_jobs,
            'cancelled_jobs': cancelled_jobs,
            'overdue_jobs': overdue_jobs,
            'average_completion_time_hours': round(avg_time, 2),
            'most_used_equipment': most_used_equipment,
            'jobs_by_priority': jobs_by_priority,
            'jobs_by_status': jobs_by_status
        }

        serializer = JobAnalyticsSerializer(analytics_data)
        return Response(serializer.data)