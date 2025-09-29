"""
Celery tasks for ops app - JobOps system.
"""
from celery import shared_task
from django.utils import timezone
from django.contrib.auth import get_user_model
from .models import Job

User = get_user_model()


@shared_task(name='ops.tasks.check_overdue_jobs')
def check_overdue_jobs():
    """
    Check and flag overdue jobs.

    This task runs daily at midnight to mark jobs as overdue
    if their scheduled date has passed and they are not completed.

    Returns:
        str: Message with count of jobs marked as overdue
    """
    today = timezone.now().date()

    overdue_jobs = Job.objects.filter(
        scheduled_date__lt=today,
        status__in=['pending', 'in_progress'],
        overdue=False
    )

    count = overdue_jobs.update(overdue=True)

    message = f"Marked {count} jobs as overdue"
    print(message)

    return message


@shared_task(name='ops.tasks.send_daily_task_reminder')
def send_daily_task_reminder():
    """
    Send daily task reminders to technicians.

    This task runs daily at 7 AM to remind technicians
    about their scheduled tasks for the day.

    Sends actual emails via MailHog (for testing) or configured SMTP server.

    Returns:
        str: Message with count of reminders sent
    """
    from django.core.mail import send_mail
    from django.conf import settings

    today = timezone.now().date()

    technicians = User.objects.filter(
        role='technician',
        is_active=True
    )

    reminder_count = 0
    email_sent_count = 0

    for technician in technicians:
        jobs = Job.objects.filter(
            assigned_to=technician,
            scheduled_date=today,
            status__in=['pending', 'in_progress']
        ).prefetch_related('tasks')

        if jobs.exists():
            reminder_count += 1

            job_details = []
            total_tasks = 0

            for job in jobs:
                tasks = job.tasks.exclude(status='completed')
                task_count = tasks.count()
                total_tasks += task_count

                job_details.append(
                    f"• {job.title} ({job.client_name}) - Priority: {job.priority.upper()}\n"
                    f"  Tasks: {task_count} pending"
                )

            job_list = "\n\n".join(job_details)

            subject = f"Daily Task Reminder - {jobs.count()} Job{'s' if jobs.count() > 1 else ''} Scheduled for Today"

            message = f"""
                    Hello {technician.first_name or technician.username},
                    
                    You have {jobs.count()} job(s) scheduled for today ({today.strftime('%B %d, %Y')}) with {total_tasks} pending task(s).
                    
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
                    recipient_list=[technician.email],
                    fail_silently=False,
                )
                email_sent_count += 1
                print(f"Email sent to {technician.username} ({technician.email}): {jobs.count()} jobs today")
            except Exception as e:
                print(f"Failed to send email to {technician.username}: {str(e)}")

    message = f"Processed {reminder_count} technician(s) with tasks today. Emails sent: {email_sent_count}"
    print(message)

    return message


@shared_task(name='ops.tasks.cleanup_old_logs')
def cleanup_old_logs():
    """
    Clean up old job change logs (older than 90 days).

    This task helps keep the database clean by removing old audit logs.
    Runs monthly.

    Returns:
        str: Message with count of logs deleted
    """
    from .models import JobChangeLog
    from datetime import timedelta

    cutoff_date = timezone.now() - timedelta(days=90)
    old_logs = JobChangeLog.objects.filter(timestamp__lt=cutoff_date)

    count = old_logs.count()
    old_logs.delete()

    message = f"Deleted {count} old job change logs"
    print(message)

    return message


@shared_task(name='ops.tasks.update_job_statistics')
def update_job_statistics():
    """
    Update job statistics and performance metrics.

    This task can be used to pre-calculate and cache statistics
    for faster analytics dashboard loading.

    Returns:
        str: Message with statistics summary
    """
    total_jobs = Job.objects.count()
    completed_jobs = Job.objects.filter(status='completed').count()
    overdue_jobs = Job.objects.filter(overdue=True).count()

    completion_rate = (completed_jobs / total_jobs * 100) if total_jobs > 0 else 0

    message = (
        f"Job Statistics - Total: {total_jobs}, "
        f"Completed: {completed_jobs}, "
        f"Overdue: {overdue_jobs}, "
        f"Completion Rate: {completion_rate:.2f}%"
    )
    print(message)

    return message