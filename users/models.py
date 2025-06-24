from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from PIL import Image
from django.utils import timezone

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, unique=True)
    profile_pic = models.ImageField(upload_to='profile_pics', blank=True)
    bio = models.TextField(max_length=500, blank=True, help_text="Tell us about yourself")
    location = models.CharField(max_length=100, blank=True)
    birth_date = models.DateField(null=True, blank=True)
    phone_number = models.CharField(max_length=20, blank=True)
    website = models.URLField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'{self.user.username} Profile'
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        
        # Resize image if it exists
        if self.profile_pic:
            try:
                img = Image.open(self.profile_pic.path)
                
                # Resize if image is too large
                if img.height > 300 or img.width > 300:
                    output_size = (300, 300)
                    img.thumbnail(output_size)
                    img.save(self.profile_pic.path)
            except Exception as e:
                # Log error but don't prevent saving
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Error resizing profile image: {e}")
    
    @property
    def get_full_name(self):
        return f"{self.user.first_name} {self.user.last_name}".strip() or self.user.username
    
    class Meta:
        verbose_name = 'User Profile'
        verbose_name_plural = 'User Profiles'

    def get_friends(self):
        """Get all friends of this user"""
        friendships = Friendship.objects.filter(
            models.Q(user1=self.user) | models.Q(user2=self.user),
            status='accepted'
        )
        friends = []
        for friendship in friendships:
            if friendship.user1 == self.user:
                friends.append(friendship.user2)
            else:
                friends.append(friendship.user1)
        return friends
    
    def get_friend_count(self):
        """Get total number of friends"""
        return len(self.get_friends())
    
    def is_friend_with(self, other_user):
        """Check if this user is friends with another user"""
        return Friendship.objects.filter(
            models.Q(user1=self.user, user2=other_user) | 
            models.Q(user1=other_user, user2=self.user),
            status='accepted'
        ).exists()

@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    """Create or update a Profile instance whenever a User is created or updated"""
    try:
        if created:
            # Only create if profile doesn't exist
            Profile.objects.get_or_create(user=instance)
        else:
            # For existing users, ensure they have a profile
            profile, profile_created = Profile.objects.get_or_create(user=instance)
            if not profile_created:
                profile.save()
    except Exception as e:
        # Log the error but don't prevent user creation
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error creating/updating profile for user {instance.username}: {e}")

class Friendship(models.Model):
    """Model to manage friendships between users"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('declined', 'Declined'),
        ('blocked', 'Blocked'),
    ]
    
    user1 = models.ForeignKey(User, on_delete=models.CASCADE, related_name='friendship_requests_sent')
    user2 = models.ForeignKey(User, on_delete=models.CASCADE, related_name='friendship_requests_received')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ('user1', 'user2')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user1.username} -> {self.user2.username} ({self.status})"
    
    @classmethod
    def send_friend_request(cls, from_user, to_user):
        """Send a friend request"""
        if from_user == to_user:
            return None, "Cannot send friend request to yourself"
        
        # Check if friendship already exists
        existing = cls.objects.filter(
            models.Q(user1=from_user, user2=to_user) | 
            models.Q(user1=to_user, user2=from_user)
        ).first()
        
        if existing:
            if existing.status == 'accepted':
                return None, "You are already friends"
            elif existing.status == 'pending':
                return None, "Friend request already sent"
            elif existing.status == 'blocked':
                return None, "Cannot send friend request"
            elif existing.status == 'declined':
                # Update the declined request to pending instead of creating new
                existing.status = 'pending'
                existing.user1 = from_user  # Ensure correct sender
                existing.user2 = to_user    # Ensure correct receiver
                existing.save()
                return existing, "Friend request sent successfully"
        
        # Create new friend request
        friendship = cls.objects.create(user1=from_user, user2=to_user)
        return friendship, "Friend request sent successfully"
    
    @classmethod
    def accept_friend_request(cls, from_user, to_user):
        """Accept a friend request"""
        # Look for friendship in both directions
        friendship = cls.objects.filter(
            models.Q(user1=from_user, user2=to_user) | 
            models.Q(user1=to_user, user2=from_user),
            status='pending'
        ).first()
        
        if friendship:
            friendship.status = 'accepted'
            friendship.save()
            return True, "Friend request accepted"
        else:
            return False, "Friend request not found"
    
    @classmethod
    def decline_friend_request(cls, from_user, to_user):
        """Decline a friend request"""
        # Look for friendship in both directions
        friendship = cls.objects.filter(
            models.Q(user1=from_user, user2=to_user) | 
            models.Q(user1=to_user, user2=from_user),
            status='pending'
        ).first()
        
        if friendship:
            friendship.status = 'declined'
            friendship.save()
            return True, "Friend request declined"
        else:
            return False, "Friend request not found"
    
    @classmethod
    def remove_friend(cls, user1, user2):
        """Remove friendship between two users"""
        friendship = cls.objects.filter(
            models.Q(user1=user1, user2=user2) | models.Q(user1=user2, user2=user1),
            status='accepted'
        ).first()
        
        if friendship:
            friendship.delete()
            return True, "Friend removed successfully"
        return False, "Friendship not found"
    
    @classmethod
    def get_pending_requests_for_user(cls, user):
        """Get all pending friend requests for a user"""
        return cls.objects.filter(user2=user, status='pending')
    
    @classmethod
    def get_sent_requests_by_user(cls, user):
        """Get all friend requests sent by a user"""
        return cls.objects.filter(user1=user, status='pending')

class FriendRequest(models.Model):
    """Model for friend request notifications"""
    from_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_friend_requests')
    to_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_friend_requests')
    message = models.TextField(blank=True, help_text="Optional message with friend request")
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Friend request from {self.from_user.username} to {self.to_user.username}"
