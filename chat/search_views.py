"""
Add message search functionality to the chat application
"""

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db.models import Q
from .models import Message, GroupMessage
import json

@login_required
def search_messages(request):
    """Search messages for the current user"""
    if request.method == 'GET':
        query = request.GET.get('q', '').strip()
        
        if not query:
            return JsonResponse({'status': 'error', 'message': 'No search query provided'})
        
        # Search in private messages
        private_messages = Message.objects.filter(
            Q(content__icontains=query) & (
                Q(sender=request.user) | Q(receiver=request.user)
            )
        ).select_related('sender', 'receiver').order_by('-timestamp')[:20]
        
        # Search in group messages where user is a member
        user_groups = request.user.group_set.all()
        group_messages = GroupMessage.objects.filter(
            Q(content__icontains=query) & Q(group__in=user_groups)
        ).select_related('sender', 'group').order_by('-timestamp')[:20]
        
        # Format results
        results = []
        
        for msg in private_messages:
            results.append({
                'type': 'private',
                'id': msg.id,
                'content': msg.content,
                'sender': msg.sender.username,
                'receiver': msg.receiver.username,
                'timestamp': msg.timestamp.isoformat(),
                'chat_url': f'/chat/{msg.receiver.username if msg.sender == request.user else msg.sender.username}/'
            })
        
        for msg in group_messages:
            results.append({
                'type': 'group',
                'id': msg.id,
                'content': msg.content,
                'sender': msg.sender.username,
                'group': msg.group.name,
                'timestamp': msg.timestamp.isoformat(),
                'chat_url': f'/groups/{msg.group.id}/'
            })
        
        # Sort by timestamp
        results.sort(key=lambda x: x['timestamp'], reverse=True)
        
        return JsonResponse({
            'status': 'success',
            'results': results[:20],  # Limit to 20 results
            'total_found': len(results)
        })
    
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'})

@login_required 
def advanced_search(request):
    """Advanced search with filters"""
    if request.method == 'POST':
        data = json.loads(request.body)
        query = data.get('query', '').strip()
        message_type = data.get('type', 'all')  # 'all', 'private', 'group'
        date_from = data.get('date_from')
        date_to = data.get('date_to')
        sender_username = data.get('sender')
        
        results = []
        
        # Base query filter
        base_filter = Q()
        if query:
            base_filter &= Q(content__icontains=query)
        
        # Date filters
        if date_from:
            base_filter &= Q(timestamp__gte=date_from)
        if date_to:
            base_filter &= Q(timestamp__lte=date_to)
        
        # Search private messages
        if message_type in ['all', 'private']:
            private_filter = base_filter & (
                Q(sender=request.user) | Q(receiver=request.user)
            )
            
            if sender_username:
                try:
                    from django.contrib.auth.models import User
                    sender = User.objects.get(username=sender_username)
                    private_filter &= Q(sender=sender)
                except User.DoesNotExist:
                    pass
            
            private_messages = Message.objects.filter(private_filter).select_related(
                'sender', 'receiver'
            ).order_by('-timestamp')[:50]
            
            for msg in private_messages:
                results.append({
                    'type': 'private',
                    'id': msg.id,
                    'content': msg.content,
                    'sender': msg.sender.username,
                    'receiver': msg.receiver.username,
                    'timestamp': msg.timestamp.isoformat(),
                    'chat_url': f'/chat/{msg.receiver.username if msg.sender == request.user else msg.sender.username}/'
                })
        
        # Search group messages
        if message_type in ['all', 'group']:
            user_groups = request.user.group_set.all()
            group_filter = base_filter & Q(group__in=user_groups)
            
            if sender_username:
                try:
                    from django.contrib.auth.models import User
                    sender = User.objects.get(username=sender_username)
                    group_filter &= Q(sender=sender)
                except User.DoesNotExist:
                    pass
            
            group_messages = GroupMessage.objects.filter(group_filter).select_related(
                'sender', 'group'
            ).order_by('-timestamp')[:50]
            
            for msg in group_messages:
                results.append({
                    'type': 'group',
                    'id': msg.id,
                    'content': msg.content,
                    'sender': msg.sender.username,
                    'group': msg.group.name,
                    'timestamp': msg.timestamp.isoformat(),
                    'chat_url': f'/groups/{msg.group.id}/'
                })
        
        # Sort by timestamp
        results.sort(key=lambda x: x['timestamp'], reverse=True)
        
        return JsonResponse({
            'status': 'success',
            'results': results[:50],
            'total_found': len(results),
            'filters_applied': {
                'query': query,
                'type': message_type,
                'date_from': date_from,
                'date_to': date_to,
                'sender': sender_username
            }
        })
    
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'})
