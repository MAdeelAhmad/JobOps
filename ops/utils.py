"""
Utility functions for ops app.
"""
from django.core.mail import send_mail
from django.conf import settings
from typing import List


def send_task_reminder_email(user, jobs):
    """
    Send task reminder email to a technician.

    Args:
        user: User object (technician)
        jobs: QuerySet of Job objects scheduled for the user

    Returns:
        bool: True if email sent successfully, False otherwise
    """
    if not jobs.exists():
        return False

    job_details = []
    total_tasks = 0

    for job in jobs:
        tasks = job.tasks.exclude(status='completed')
        task_count = tasks.count()
        total_tasks += task_count

        job_details.append({
            'title': job.title,
            'client': job.client_name,
            'priority': job.priority,
            'task_count': task_count,
            'status': job.status
        })

    subject = f"Daily Task Reminder - {jobs.count()} Job{'s' if jobs.count() > 1 else ''} Today"

    job_list = "\n\n".join([
        f"• {job['title']} ({job['client']}) - Priority: {job['priority'].upper()}\n"
        f"  Tasks: {job['task_count']} pending"
        for job in job_details
    ])

    message = f"""
            Hello {user.first_name or user.username},
            
            You have {jobs.count()} job(s) scheduled for today with {total_tasks} pending task(s).
            
            Job Details:
            {job_list}
            
            Please review your tasks and update their status as you progress.
            
            Access your dashboard: http://localhost:8000/ops/technician-dashboard/
            
            Best regards,
            JobOps Management System
                """.strip()

    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False,
        )
        return True
    except Exception as e:
        print(f"Error sending email to {user.email}: {str(e)}")
        return False


def send_job_assignment_email(job, technician):
    """
    Send email notification when a job is assigned to a technician.

    Args:
        job: Job object
        technician: User object (technician)

    Returns:
        bool: True if email sent successfully
    """
    subject = f"New Job Assignment: {job.title}"

    message = f"""
            Hello {technician.first_name or technician.username},
            
            A new job has been assigned to you:
            
            Job Title: {job.title}
            Client: {job.client_name}
            Priority: {job.priority.upper()}
            Scheduled Date: {job.scheduled_date.strftime('%B %d, %Y')}
            Description: {job.description}
            
            Total Tasks: {job.tasks.count()}
            
            Please review the job details and prepare accordingly.
            
            Best regards,
            JobOps Management System
                """.strip()

    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[technician.email],
            fail_silently=False,
        )
        return True
    except Exception as e:
        print(f"Error sending assignment email: {str(e)}")
        return False


def send_job_status_change_email(job, old_status, new_status):
    """
    Send email notification when job status changes.

    Args:
        job: Job object
        old_status: Previous status
        new_status: New status

    Returns:
        bool: True if email sent successfully
    """
    recipients = []

    if job.created_by and job.created_by.email:
        recipients.append(job.created_by.email)

    if job.assigned_to and job.assigned_to.email and job.assigned_to.email not in recipients:
        recipients.append(job.assigned_to.email)

    if not recipients:
        return False

    subject = f"Job Status Update: {job.title}"

    message = f"""
        Job Status Update
        
        Job: {job.title}
        Client: {job.client_name}
        Status Changed: {old_status.upper()} → {new_status.upper()}
        Scheduled Date: {job.scheduled_date.strftime('%B %d, %Y')}
        
        Progress: {job.tasks.filter(status='completed').count()}/{job.tasks.count()} tasks completed
        
        Best regards,
        JobOps Management System
            """.strip()

    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=recipients,
            fail_silently=False,
        )
        return True
    except Exception as e:
        print(f"Error sending status change email: {str(e)}")
        return False


def send_overdue_job_alert(jobs: List):
    """
    Send alert email to admins about overdue jobs.

    Args:
        jobs: List of overdue Job objects

    Returns:
        bool: True if email sent successfully
    """
    from django.contrib.auth import get_user_model
    User = get_user_model()

    admins = User.objects.filter(role='admin', is_active=True)
    admin_emails = [admin.email for admin in admins if admin.email]

    if not admin_emails or not jobs:
        return False

    subject = f"Overdue Jobs Alert - {len(jobs)} Job{'s' if len(jobs) > 1 else ''} Overdue"

    job_list = "\n".join([
        f"• {job.title} - {job.client_name} (Scheduled: {job.scheduled_date}, Assigned: {job.assigned_to.username if job.assigned_to else 'Unassigned'})"
        for job in jobs
    ])

    message = f"""
            Overdue Jobs Alert
            
            {len(jobs)} job(s) are currently overdue:
            
            {job_list}
            
            Please review and take necessary action.
            
            JobOps Management System
                """.strip()

    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=admin_emails,
            fail_silently=False,
        )
        return True
    except Exception as e:
        print(f"Error sending overdue alert: {str(e)}")
        return False