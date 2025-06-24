from django.db import models
from django.contrib.auth.models import User
import uuid
from django.urls import reverse

class Chat(models.Model):
    participants = models.ManyToManyField(User, related_name='chats')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Chat {self.id} - {', '.join([user.username for user in self.participants.all()])}"

class Message(models.Model):
    chat = models.ForeignKey(Chat, on_delete=models.CASCADE, related_name='messages', null=True, blank=True)
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    attachment = models.FileField(upload_to='chat_attachments/', blank=True, null=True)
    receiver = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_messages', null=True)

    def __str__(self):
        return f"Message from {self.sender.username} at {self.timestamp}"
    
    def is_read_by(self, user):
        """Check if message is read by a specific user"""
        return self.read_status.filter(user=user).exists()
    
    def mark_as_read(self, user):
        """Mark message as read by a specific user"""
        MessageReadStatus.objects.get_or_create(message=self, user=user)
    
    def get_unread_count_for_user(user, other_user):
        """Get count of unread messages from other_user to user"""
        unread_messages = Message.objects.filter(
            sender=other_user,
            receiver=user
        ).exclude(
            id__in=MessageReadStatus.objects.filter(user=user).values_list('message_id', flat=True)
        )
        return unread_messages.count()
    
    @staticmethod
    def get_unread_count_by_sender(user):
        """Get unread message count grouped by sender"""
        from django.db.models import Count, Q
        
        unread_counts = {}
        
        # Get all users who have sent messages to this user
        senders = User.objects.filter(
            sent_messages__receiver=user
        ).distinct()
        
        for sender in senders:
            unread_count = Message.objects.filter(
                sender=sender,
                receiver=user
            ).exclude(
                id__in=MessageReadStatus.objects.filter(user=user).values_list('message_id', flat=True)
            ).count()
            
            if unread_count > 0:
                unread_counts[sender.id] = unread_count
        
        return unread_counts
    
class Group(models.Model):
    name = models.CharField(max_length=100)
    members = models.ManyToManyField(User, related_name='chat_groups')
    created_at = models.DateTimeField(auto_now_add=True)
    invite_code = models.UUIDField(default=uuid.uuid4, editable=False, null=True, blank=True, unique=True)
    allow_invites = models.BooleanField(default=True)

    def save(self, *args, **kwargs):
        if not self.invite_code:
            self.invite_code = uuid.uuid4()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name
    
    def get_invite_link(self, request=None):
        """Generate invitation link for the group"""
        if not self.invite_code:
            self.invite_code = uuid.uuid4()
            self.save()
        
        if request:
            return request.build_absolute_uri(
                reverse('join_group_by_invite', kwargs={'invite_code': self.invite_code})
            )
        return reverse('join_group_by_invite', kwargs={'invite_code': self.invite_code})
    
    def can_user_invite(self, user):
        """Check if user can send invitations to this group"""
        return self.allow_invites and user in self.members.all()

class GroupMessage(models.Model):
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField(blank=True, null=True)
    attachment = models.FileField(upload_to='chat_attachments/', blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.sender} in {self.group}: {self.content[:20]}"
    
    def is_read_by(self, user):
        """Check if group message is read by a specific user"""
        return self.read_status.filter(user=user).exists()
    
    def mark_as_read(self, user):
        """Mark group message as read by a specific user"""
        GroupMessageReadStatus.objects.get_or_create(message=self, user=user)
    
    @staticmethod
    def get_unread_count_for_group(user, group):
        """Get count of unread messages in a group for a user"""
        unread_messages = GroupMessage.objects.filter(
            group=group
        ).exclude(
            sender=user  # Don't count own messages
        ).exclude(
            id__in=GroupMessageReadStatus.objects.filter(user=user).values_list('message_id', flat=True)
        )
        return unread_messages.count()
    
    @staticmethod
    def get_unread_count_by_group(user):
        """Get unread message count grouped by group"""
        unread_counts = {}
        
        # Get all groups the user is a member of
        groups = Group.objects.filter(members=user)
        
        for group in groups:
            unread_count = GroupMessage.objects.filter(
                group=group
            ).exclude(
                sender=user  # Don't count own messages
            ).exclude(
                id__in=GroupMessageReadStatus.objects.filter(user=user).values_list('message_id', flat=True)
            ).count()
            
            if unread_count > 0:
                unread_counts[group.id] = unread_count
        
        return unread_counts

class MessageReadStatus(models.Model):
    """Track read status of messages for each user"""
    message = models.ForeignKey(Message, on_delete=models.CASCADE, related_name='read_status')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    read_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('message', 'user')
        verbose_name = 'Message Read Status'
        verbose_name_plural = 'Message Read Statuses'
    
    def __str__(self):
        return f"{self.user.username} read message {self.message.id} at {self.read_at}"

class GroupMessageReadStatus(models.Model):
    """Track read status of group messages for each user"""
    message = models.ForeignKey(GroupMessage, on_delete=models.CASCADE, related_name='read_status')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    read_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('message', 'user')
        verbose_name = 'Group Message Read Status'
        verbose_name_plural = 'Group Message Read Statuses'
    
    def __str__(self):
        return f"{self.user.username} read group message {self.message.id} at {self.read_at}"

class GroupInvitation(models.Model):
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='invitations')
    invited_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_group_invitations')
    invited_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_group_invitations', null=True, blank=True)
    invited_email = models.EmailField(null=True, blank=True)  # For inviting non-users
    invite_code = models.UUIDField(default=uuid.uuid4, unique=True)
    message = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    accepted_at = models.DateTimeField(null=True, blank=True)
    is_accepted = models.BooleanField(default=False)

    class Meta:
        unique_together = ['group', 'invited_user']

    def __str__(self):
        target = self.invited_user.username if self.invited_user else self.invited_email
        return f"Invitation to {self.group.name} for {target}"