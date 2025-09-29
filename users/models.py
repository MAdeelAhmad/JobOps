from django.db import models
from django.contrib.auth.models import AbstractUser


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True

class User(AbstractUser, TimeStampedModel):
    """
    Custom user model extending AbstractUser with role-based access.

    Roles:
    - admin: Full system access, can create/edit users
    - technician: Can update assigned jobs and tasks
    - sales_agent: Can create jobs, view reports
    """

    ROLE_CHOICES = (
        ('admin', 'Admin'),
        ('technician', 'Technician'),
        ('sales_agent', 'Sales Agent'),
    )

    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default='technician',
        db_index=True
    )
    phone = models.CharField(max_length=15, blank=True, null=True)

    class Meta:
        db_table = 'users'
        ordering = ['username']
        indexes = [
            models.Index(fields=['role', 'is_active']),
        ]

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"

    def save(self, *args, **kwargs):
        """Ensure admins have staff status"""
        if self.role == 'admin':
            self.is_staff = True
        super().save(*args, **kwargs)
