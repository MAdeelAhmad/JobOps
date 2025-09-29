"""
Django admin configuration for ops app.
"""
from django.contrib import admin
from .models import Equipment, Job, JobTask, JobChangeLog

@admin.register(Equipment)
class EquipmentAdmin(admin.ModelAdmin):
    """Admin configuration for Equipment model"""

    list_display = ['name', 'type', 'serial_number', 'is_active', 'created_at']
    list_filter = ['type', 'is_active', 'created_at']
    search_fields = ['name', 'serial_number', 'description']
    ordering = ['name']
    readonly_fields = ['created_at', 'updated_at']

    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'type', 'serial_number', 'description')
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


class JobTaskInline(admin.TabularInline):
    """Inline admin for JobTask within Job admin"""

    model = JobTask
    extra = 1
    fields = ['title', 'status', 'order', 'completed_at']
    readonly_fields = ['completed_at']
    ordering = ['order']


class JobChangeLogInline(admin.TabularInline):
    """Inline admin for JobChangeLog within Job admin"""

    model = JobChangeLog
    extra = 0
    fields = ['user', 'action', 'timestamp']
    readonly_fields = ['user', 'action', 'changes', 'timestamp']
    ordering = ['-timestamp']
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    """Admin configuration for Job model"""

    list_display = [
        'title', 'client_name', 'status', 'priority',
        'assigned_to', 'scheduled_date', 'overdue', 'created_at'
    ]
    list_filter = ['status', 'priority', 'overdue', 'scheduled_date', 'created_at']
    search_fields = ['title', 'client_name', 'description']
    ordering = ['-created_at']
    readonly_fields = ['created_by', 'created_at', 'updated_at']

    inlines = [JobTaskInline, JobChangeLogInline]

    fieldsets = (
        ('Job Information', {
            'fields': ('title', 'description', 'client_name')
        }),
        ('Assignment', {
            'fields': ('created_by', 'assigned_to')
        }),
        ('Status & Priority', {
            'fields': ('status', 'priority', 'overdue')
        }),
        ('Schedule', {
            'fields': ('scheduled_date',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def save_model(self, request, obj, form, change):
        """Set created_by to current user if creating"""
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(JobTask)
class JobTaskAdmin(admin.ModelAdmin):
    """Admin configuration for JobTask model"""

    list_display = ['title', 'job', 'status', 'order', 'completed_at', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['title', 'description', 'job__title']
    ordering = ['job', 'order']
    readonly_fields = ['completed_at', 'created_at', 'updated_at']
    filter_horizontal = ['required_equipment']

    fieldsets = (
        ('Task Information', {
            'fields': ('job', 'title', 'description', 'order')
        }),
        ('Status', {
            'fields': ('status', 'completed_at')
        }),
        ('Equipment', {
            'fields': ('required_equipment',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(JobChangeLog)
class JobChangeLogAdmin(admin.ModelAdmin):
    """Admin configuration for JobChangeLog model"""

    list_display = ['job', 'user', 'action', 'timestamp']
    list_filter = ['action', 'timestamp']
    search_fields = ['job__title', 'user__username', 'action']
    ordering = ['-timestamp']
    readonly_fields = ['job', 'user', 'action', 'changes', 'timestamp']

    def has_add_permission(self, request):
        """Prevent manual creation of change logs"""
        return False

    def has_change_permission(self, request, obj=None):
        """Prevent editing of change logs"""
        return False