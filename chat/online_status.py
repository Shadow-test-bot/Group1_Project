"""
Online Status Tracking for Chat Application
Tracks when users are online and shows their status
"""

from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta

class UserOnlineStatus(models.Model):
    """Track user online status"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='online_status')
    is_online = models.BooleanField(default=False)
    last_seen = models.DateTimeField(auto_now=True)
    last_activity = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "User Online Status"
        verbose_name_plural = "User Online Statuses"
    
    def __str__(self):
        status = "Online" if self.is_online else f"Last seen {self.last_seen}"
        return f"{self.user.username} - {status}"
    
    @property
    def status_text(self):
        """Get human readable status"""
        if self.is_online:
            return "Online"
        
        time_diff = timezone.now() - self.last_seen
        
        if time_diff < timedelta(minutes=5):
            return "Just now"
        elif time_diff < timedelta(hours=1):
            minutes = int(time_diff.total_seconds() / 60)
            return f"{minutes} minutes ago"
        elif time_diff < timedelta(days=1):
            hours = int(time_diff.total_seconds() / 3600)
            return f"{hours} hours ago"
        else:
            days = time_diff.days
            return f"{days} days ago"
    
    @classmethod
    def update_user_activity(cls, user):
        """Update user's last activity"""
        status, created = cls.objects.get_or_create(user=user)
        status.is_online = True
        status.last_activity = timezone.now()
        status.save()
        return status
    
    @classmethod
    def set_user_offline(cls, user):
        """Set user as offline"""
        try:
            status = cls.objects.get(user=user)
            status.is_online = False
            status.save()
        except cls.DoesNotExist:
            pass
    
    @classmethod
    def get_online_users(cls):
        """Get list of currently online users"""
        # Consider users online if they were active in last 5 minutes
        cutoff_time = timezone.now() - timedelta(minutes=5)
        return cls.objects.filter(
            is_online=True,
            last_activity__gte=cutoff_time
        ).select_related('user')
    
    @classmethod
    def cleanup_offline_users(cls):
        """Mark users as offline if they haven't been active"""
        cutoff_time = timezone.now() - timedelta(minutes=5)
        cls.objects.filter(
            is_online=True,
            last_activity__lt=cutoff_time
        ).update(is_online=False)

# Middleware to track user activity
class OnlineStatusMiddleware:
    """Middleware to update user online status"""
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        response = self.get_response(request)
        
        # Update user activity if authenticated
        if request.user.is_authenticated:
            UserOnlineStatus.update_user_activity(request.user)
        
        return response

# Management command to clean up offline users
from django.core.management.base import BaseCommand

class Command(BaseCommand):
    """Management command to clean up offline users"""
    help = 'Clean up offline users from online status'
    
    def handle(self, *args, **options):
        UserOnlineStatus.cleanup_offline_users()
        online_count = UserOnlineStatus.get_online_users().count()
        self.stdout.write(
            self.style.SUCCESS(
                f'Cleaned up offline users. Currently {online_count} users online.'
            )
        )
