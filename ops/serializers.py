"""
Serializers for ops app - JobOps system.
"""
from rest_framework import serializers
from django.contrib.auth import get_user_model
from ops.models import Equipment, Job, JobTask, JobChangeLog
from users.serializers import UserSerializer

User = get_user_model()


class EquipmentSerializer(serializers.ModelSerializer):
    """Serializer for Equipment model"""

    class Meta:
        model = Equipment
        fields = [
            'id', 'name', 'type', 'serial_number',
            'is_active', 'description', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def validate_serial_number(self, value):
        """Ensure serial number is unique"""
        instance = self.instance
        if Equipment.objects.exclude(pk=instance.pk if instance else None).filter(serial_number=value).exists():
            raise serializers.ValidationError("Equipment with this serial number already exists.")
        return value


class EquipmentListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for equipment lists"""

    class Meta:
        model = Equipment
        fields = ['id', 'name', 'serial_number', 'type', 'is_active']


class JobTaskSerializer(serializers.ModelSerializer):
    """Serializer for JobTask model"""

    required_equipment = EquipmentListSerializer(many=True, read_only=True)
    required_equipment_ids = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Equipment.objects.filter(is_active=True),
        write_only=True,
        required=False,
        source='required_equipment'
    )

    class Meta:
        model = JobTask
        fields = [
            'id', 'job', 'title', 'description', 'status', 'order',
            'required_equipment', 'required_equipment_ids',
            'completed_at', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'completed_at', 'created_at', 'updated_at']

    def validate_order(self, value):
        """Ensure order is positive"""
        if value < 0:
            raise serializers.ValidationError("Order must be a positive number.")
        return value


class JobTaskCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating job tasks"""

    required_equipment_ids = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Equipment.objects.filter(is_active=True),
        required=False,
        source='required_equipment'
    )

    class Meta:
        model = JobTask
        fields = [
            'job', 'title', 'description', 'order', 'required_equipment_ids'
        ]


class JobSerializer(serializers.ModelSerializer):
    """Serializer for Job model - List and Detail"""

    created_by = UserSerializer(read_only=True)
    assigned_to = UserSerializer(read_only=True)
    tasks = JobTaskSerializer(many=True, read_only=True)
    tasks_count = serializers.SerializerMethodField()
    completed_tasks_count = serializers.SerializerMethodField()
    progress_percentage = serializers.SerializerMethodField()

    class Meta:
        model = Job
        fields = [
            'id', 'title', 'description', 'client_name',
            'created_by', 'assigned_to',
            'status', 'priority', 'scheduled_date', 'overdue',
            'tasks', 'tasks_count', 'completed_tasks_count', 'progress_percentage',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_by', 'overdue', 'created_at', 'updated_at']

    def get_tasks_count(self, obj):
        """Get total number of tasks"""
        return obj.tasks.count()

    def get_completed_tasks_count(self, obj):
        """Get number of completed tasks"""
        return obj.tasks.filter(status='completed').count()

    def get_progress_percentage(self, obj):
        """Calculate job completion percentage"""
        total = obj.tasks.count()
        if total == 0:
            return 0
        completed = obj.tasks.filter(status='completed').count()
        return round((completed / total) * 100, 2)


class JobListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for job lists"""

    created_by_name = serializers.CharField(source='created_by.username', read_only=True)
    assigned_to_name = serializers.CharField(source='assigned_to.username', read_only=True)
    tasks_count = serializers.SerializerMethodField()

    class Meta:
        model = Job
        fields = [
            'id', 'title', 'client_name', 'status', 'priority',
            'scheduled_date', 'overdue', 'created_by_name',
            'assigned_to_name', 'tasks_count', 'created_at'
        ]

    def get_tasks_count(self, obj):
        return obj.tasks.count()


class JobCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating jobs"""

    assigned_to_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.filter(role='technician', is_active=True),
        write_only=True,
        source='assigned_to',
        required=False,
        allow_null=True
    )

    class Meta:
        model = Job
        fields = [
            'title', 'description', 'client_name',
            'assigned_to_id', 'priority', 'scheduled_date'
        ]

    def validate_client_name(self, value):
        """Validate client name is not empty"""
        if not value or value.strip() == '':
            raise serializers.ValidationError("Client name cannot be empty.")
        return value.strip()


class JobUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating jobs"""

    assigned_to_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.filter(role='technician', is_active=True),
        write_only=True,
        source='assigned_to',
        required=False,
        allow_null=True
    )

    class Meta:
        model = Job
        fields = [
            'title', 'description', 'client_name',
            'assigned_to_id', 'status', 'priority', 'scheduled_date'
        ]

    def validate(self, attrs):
        """Validate job completion"""
        instance = self.instance
        new_status = attrs.get('status', instance.status)

        if new_status == 'completed' and not instance.can_complete():
            raise serializers.ValidationError({
                "status": "Cannot complete job. All tasks must be completed first."
            })

        return attrs


class JobChangeLogSerializer(serializers.ModelSerializer):
    """Serializer for job change log"""

    user = UserSerializer(read_only=True)
    job_title = serializers.CharField(source='job.title', read_only=True)

    class Meta:
        model = JobChangeLog
        fields = [
            'id', 'job', 'job_title', 'user',
            'action', 'changes', 'timestamp'
        ]
        read_only_fields = ['id', 'timestamp']


class JobAnalyticsSerializer(serializers.Serializer):
    """Serializer for job analytics"""

    total_jobs = serializers.IntegerField()
    completed_jobs = serializers.IntegerField()
    pending_jobs = serializers.IntegerField()
    in_progress_jobs = serializers.IntegerField()
    cancelled_jobs = serializers.IntegerField()
    overdue_jobs = serializers.IntegerField()
    average_completion_time_hours = serializers.FloatField()
    most_used_equipment = serializers.ListField(child=serializers.DictField())
    jobs_by_priority = serializers.DictField()
    jobs_by_status = serializers.DictField()


class TechnicianDashboardSerializer(serializers.Serializer):
    """Serializer for technician dashboard view"""

    date = serializers.DateField()
    tasks = serializers.ListField(child=serializers.DictField())
    total_tasks = serializers.IntegerField()