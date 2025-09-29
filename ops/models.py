"""
Models for ops app - JobOps system.
"""
from django.contrib.auth import get_user_model
from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone
from users.models import TimeStampedModel

User = get_user_model()


class Equipment(TimeStampedModel):
    """
    Global equipment catalog for tools, machines, and vehicles.
    Equipment can be assigned to multiple tasks.
    """

    TYPE_CHOICES = (
        ('tool', 'Tool'),
        ('machine', 'Machine'),
        ('vehicle', 'Vehicle'),
        ('accessory', 'Accessory'),
    )

    name = models.CharField(max_length=200, db_index=True)
    type = models.CharField(max_length=20, choices=TYPE_CHOICES, db_index=True)
    serial_number = models.CharField(max_length=100, unique=True)
    is_active = models.BooleanField(default=True, db_index=True)
    description = models.TextField(blank=True)

    class Meta:
        db_table = 'equipment'
        ordering = ['name']
        verbose_name_plural = 'Equipment'
        indexes = [
            models.Index(fields=['type', 'is_active']),
        ]

    def __str__(self):
        return f"{self.name} ({self.serial_number})"


class Job(TimeStampedModel):
    """
    Main job entity representing client work orders.
    Contains multiple tasks and lifecycle management.
    """

    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    )

    PRIORITY_CHOICES = (
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    )

    title = models.CharField(max_length=255, db_index=True)
    description = models.TextField()
    client_name = models.CharField(max_length=200, db_index=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_jobs'
    )
    assigned_to = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_jobs',
        limit_choices_to={'role': 'technician'}
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        db_index=True
    )
    priority = models.CharField(
        max_length=20,
        choices=PRIORITY_CHOICES,
        default='medium',
        db_index=True
    )
    scheduled_date = models.DateField(db_index=True)
    overdue = models.BooleanField(default=False, db_index=True)

    class Meta:
        db_table = 'jobs'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'scheduled_date']),
            models.Index(fields=['assigned_to', 'status']),
            models.Index(fields=['overdue', 'status']),
        ]

    def __str__(self):
        return f"{self.title} - {self.client_name}"

    def can_complete(self):
        """
        Check if all tasks are completed before allowing job completion.

        Returns:
            bool: True if all tasks are completed, False otherwise
        """
        if not self.pk:
            return True

        try:
            incomplete_tasks = self.tasks.filter(
                status__in=['pending', 'in_progress']
            ).exists()
            return not incomplete_tasks
        except ValueError:
            # Handle case where relationship can't be used yet
            return True

    def clean(self):
        """Validate job data before saving"""
        if self.status == 'completed' and not self.can_complete():
            raise ValidationError(
                "Cannot complete job. All tasks must be completed first."
            )

    def save(self, *args, **kwargs):
        """Override save to enforce business rules"""
        self.full_clean()
        super().save(*args, **kwargs)


class JobTask(TimeStampedModel):
    """
    Individual task within a job representing ordered workflow steps.
    Tasks can have required equipment and track completion status.
    """

    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
    )

    job = models.ForeignKey(
        Job,
        on_delete=models.CASCADE,
        related_name='tasks'
    )
    title = models.CharField(max_length=255)
    description = models.TextField()
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        db_index=True
    )
    order = models.PositiveIntegerField(default=0, db_index=True)
    required_equipment = models.ManyToManyField(
        Equipment,
        related_name='tasks',
        blank=True
    )
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'job_tasks'
        ordering = ['order', 'created_at']
        indexes = [
            models.Index(fields=['job', 'status']),
            models.Index(fields=['job', 'order']),
        ]

    def __str__(self):
        return f"{self.job.title} - Step {self.order}: {self.title}"

    def save(self, *args, **kwargs):
        """Auto-set completed_at when task is marked as completed"""
        if self.status == 'completed' and not self.completed_at:
            self.completed_at = timezone.now()
        elif self.status != 'completed' and self.completed_at:
            self.completed_at = None
        super().save(*args, **kwargs)


class JobChangeLog(TimeStampedModel):
    """
    Audit log for tracking job and task changes.
    Provides history and accountability for all modifications.
    """

    job = models.ForeignKey(
        Job,
        on_delete=models.CASCADE,
        related_name='change_logs'
    )
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True
    )
    action = models.CharField(max_length=50, db_index=True)
    changes = models.JSONField(default=dict)
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        db_table = 'job_change_logs'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['job', '-timestamp']),
        ]

    def __str__(self):
        return f"{self.job.title} - {self.action} at {self.timestamp}"