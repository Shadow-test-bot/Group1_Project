from datetime import datetime
import json
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from .models import Message, MessageReadStatus, GroupMessage, GroupMessageReadStatus, GroupInvitation
from .forms import MessageForm
from django.db.models import Q
from django.utils.timezone import make_aware
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from .models import Group, GroupMessage
from .forms import GroupForm
from django.contrib.sites.shortcuts import get_current_site
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes
from django.template.loader import render_to_string
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.http import HttpResponse
from django.utils.encoding import force_str
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_http_methods
from django.contrib import messages
import json

def home(request):
    """Home page view"""
    if request.user.is_authenticated:
        return redirect('chat_redirect')
    return redirect('login')

@login_required
def chat_redirect(request):
    # Only show friends instead of all users
    friends = request.user.profile.get_friends()
    
    if not friends:
        # Redirect to friends page if no friends
        messages.info(request, 'Add some friends to start chatting!')
        return redirect('find_friends')

    # Get unread message counts by sender
    unread_counts = Message.get_unread_count_by_sender(request.user)

    user_last_messages = []
    for user in friends:
        last_message = Message.objects.filter(
            (Q(sender=request.user) & Q(receiver=user)) |
            (Q(receiver=request.user) & Q(sender=user))
        ).order_by('-timestamp').first()
        
        unread_count = unread_counts.get(user.id, 0)
        
        user_last_messages.append({
            'user': user,
            'last_message': last_message,
            'unread_count': unread_count
        })
    
    user_last_messages.sort(
        key=lambda x: x['last_message'].timestamp if x['last_message'] else make_aware(datetime(1970, 1, 1)),
        reverse=True
    )
    
    if user_last_messages:
        latest_chat_user = user_last_messages[0]['user']
        return redirect('chat', room_name=latest_chat_user.username)
    else:
        # If no messages, redirect to the first friend
        return redirect('chat', room_name=friends[0].username)

@login_required
def chat_room(request, room_name):
    search_query = request.GET.get('search', '')
    friends = request.user.profile.get_friends()
    
    # Handle case where there are no friends
    if not friends:
        return render(request, 'chat.html', {
            'room_name': 'No friends',
            'chats': [],
            'users': [],
            'user_last_messages': [],
            'search_query': '',
            'no_friends': True
        })

    # Get the other user and verify they are a friend
    try:
        other_user = User.objects.get(username=room_name)
        if not request.user.profile.is_friend_with(other_user):
            messages.error(request, f"You can only chat with friends. Add {other_user.username} as a friend first.")
            return redirect('find_friends')
    except User.DoesNotExist:
        return redirect('chat_redirect')

    chats = Message.objects.filter(
        (Q(sender=request.user) & Q(receiver__username=room_name)) |
        (Q(receiver=request.user) & Q(sender__username=room_name))
    )

    if search_query:
        chats = chats.filter(Q(content__icontains=search_query))  

    chats = chats.order_by('timestamp')
    
    # Mark all messages from other_user to current user as read
    unread_messages = Message.objects.filter(
        sender=other_user,
        receiver=request.user
    ).exclude(
        id__in=MessageReadStatus.objects.filter(user=request.user).values_list('message_id', flat=True)
    )
    
    for message in unread_messages:
        message.mark_as_read(request.user)
    
    # Get unread message counts by sender for sidebar
    unread_counts = Message.get_unread_count_by_sender(request.user)
    
    user_last_messages = []

    for user in friends:
        last_message = Message.objects.filter(
            (Q(sender=request.user) & Q(receiver=user)) |
            (Q(receiver=request.user) & Q(sender=user))
        ).order_by('-timestamp').first()

        unread_count = unread_counts.get(user.id, 0)

        user_last_messages.append({
            'user': user,
            'last_message': last_message,
            'unread_count': unread_count
        })

    # Sort user_last_messages by the timestamp of the last_message in descending order
    user_last_messages.sort(
    key=lambda x: x['last_message'].timestamp if x['last_message'] else make_aware(datetime(1970, 1, 1)),
    reverse=True
    )

    # Handle POST requests with file attachments
    if request.method == 'POST':
        content = request.POST.get('content', '').strip()
        attachment = request.FILES.get('attachment')
        
        # Check if there's content or attachment
        if not content and not attachment:
            return JsonResponse({'error': 'Message content or attachment is required'}, status=400)
        
        try:
            receiver = User.objects.get(username=room_name)
            message = Message(
                sender=request.user,
                receiver=receiver,
                content=content
            )
            
            if attachment:
                message.attachment = attachment
                
            message.save()
            
            # Return JSON response with attachment URL if available
            response_data = {
                'content': message.content,
                'sender': request.user.username,
                'timestamp': message.timestamp.strftime('%H:%M'),
                'success': True
            }
            
            if message.attachment:
                response_data['attachment_url'] = message.attachment.url
                response_data['attachment_name'] = attachment.name
                
            return JsonResponse(response_data)
            
        except User.DoesNotExist:
            return JsonResponse({'error': 'User not found'}, status=404)
        except Exception as e:
            return JsonResponse({'error': f'Failed to save message: {str(e)}'}, status=500)

    try:
        other_user = User.objects.get(username=room_name)
    except User.DoesNotExist:
        return redirect('chat_redirect')
    return render(request, 'chat.html', {
        'room_name': room_name,
        'chats': chats,
        'users': friends,
        'user_last_messages': user_last_messages,
        'search_query': search_query,
        'other_user': other_user
    })
def chat_view(request):
    if request.method == 'POST':
        form = MessageForm(request.POST, request.FILES)
        if form.is_valid():
            message = form.save(commit=False)
            message.sender = request.user
            message.save()
            return redirect('chat')
    else:
        form = MessageForm()

    messages = Message.objects.all().order_by('-timestamp')
    return render(request, 'chat/chat.html', {'form': form, 'messages': messages})

@login_required
@login_required
def group_list(request):
    groups = Group.objects.filter(members=request.user)
    
    # Get unread message counts by group
    unread_counts = GroupMessage.get_unread_count_by_group(request.user)
    
    # Add unread count to each group
    groups_with_unread = []
    for group in groups:
        unread_count = unread_counts.get(group.id, 0)
        groups_with_unread.append({
            'group': group,
            'unread_count': unread_count
        })
    
    return render(request, 'chat/group_list.html', {'groups_with_unread': groups_with_unread})

@login_required
def group_chat(request, group_id):
    group = get_object_or_404(Group, id=group_id)
    if request.user not in group.members.all():
        return redirect('group_list')
    
    chat_messages = GroupMessage.objects.filter(group=group).order_by('timestamp')
    
    # Mark all unread messages in this group as read for the current user
    unread_messages = GroupMessage.objects.filter(
        group=group
    ).exclude(
        sender=request.user  # Don't mark own messages as read
    ).exclude(
        id__in=GroupMessageReadStatus.objects.filter(user=request.user).values_list('message_id', flat=True)
    )
    
    for message in unread_messages:
        message.mark_as_read(request.user)
    
    return render(request, 'chat/group_chat.html', {'group': group, 'chat_messages': chat_messages})

@login_required
def send_group_message(request, group_id):
    if request.method == 'POST':
        group = get_object_or_404(Group, id=group_id)
        if request.user in group.members.all():
            content = request.POST.get('message')
            attachment = request.FILES.get('attachment')
            if content or attachment:
                message = GroupMessage(group=group, sender=request.user, content=content)
                if attachment:
                    message.attachment = attachment
                message.save()
    return redirect('group_chat', group_id=group_id)

@login_required
def create_group(request):
    if request.method == 'POST':
        form = GroupForm(request.POST)
        if form.is_valid():
            group = form.save()
            group.members.add(request.user)  # Automatically add the creator as a member
            return redirect('group_list')
    else:
        form = GroupForm()
    return render(request, 'chat/create_group.html', {'form': form})

@login_required
def join_group(request, group_id):
    group = get_object_or_404(Group, id=group_id)
    group.members.add(request.user)
    return redirect('group_chat', group_id=group.id)

@login_required  
def send_group_email_api(request):
    """API endpoint for sending group emails"""
    if request.method == 'POST':
        try:
            group_id = request.POST.get('group_id')
            subject = request.POST.get('subject', 'Group Message')
            message = request.POST.get('message', '')
            
            if not group_id or not message:
                return JsonResponse({'error': 'Group ID and message are required'}, status=400)
            
            group = get_object_or_404(Group, id=group_id)
            
            # Check if user is a member of the group
            if request.user not in group.members.all():
                return JsonResponse({'error': 'You are not a member of this group'}, status=403)
            
            # Get all group members' emails
            member_emails = [member.email for member in group.members.all() if member.email]
            
            if not member_emails:
                return JsonResponse({'error': 'No members with email addresses found'}, status=400)
            
            # Send email to all group members
            try:
                send_mail(
                    subject=f"[{group.name}] {subject}",
                    message=f"Message from {request.user.get_full_name() or request.user.username}:\n\n{message}",
                    from_email=None,  # Will use DEFAULT_FROM_EMAIL
                    recipient_list=member_emails,
                    fail_silently=False
                )
                
                # Also save as a group message
                GroupMessage.objects.create(
                    group=group,
                    sender=request.user,
                    content=f"Email sent: {subject}\n{message}"
                )
                
                return JsonResponse({
                    'success': True,
                    'message': f'Email sent to {len(member_emails)} members'
                })
                
            except Exception as e:
                return JsonResponse({'error': f'Failed to send email: {str(e)}'}, status=500)
                
        except Exception as e:
            return JsonResponse({'error': f'An error occurred: {str(e)}'}, status=500)
    
    return JsonResponse({'error': 'Only POST method allowed'}, status=405)

def debug_profile_photos(request):
    """Debug view to test profile photo display"""
    users = User.objects.all()
    
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Profile Photos Debug</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; }
            .user-card { 
                border: 1px solid #ccc; 
                margin: 10px; 
                padding: 15px; 
                border-radius: 8px;
                display: inline-block;
                width: 300px;
            }
            .profile-img { 
                width: 64px; 
                height: 64px; 
                border-radius: 50%; 
                object-fit: cover;
                margin-right: 10px;
                vertical-align: top;
            }
            .user-info { display: inline-block; vertical-align: top; }
        </style>
    </head>
    <body>
        <h1>Profile Photos Debug Page</h1>
        <p>Testing profile photo display for all users</p>
    """
    
    for user in users:
        try:
            profile = user.profile
            has_pic = bool(profile.profile_pic)
            
            html += f"""
            <div class="user-card">
                <div>
            """
            
            if profile.profile_pic:
                html += f'<img src="{profile.profile_pic.url}" alt="{user.username}\'s Profile" class="profile-img">'
            else:
                html += f'<img src="https://ui-avatars.com/api/?name={user.username}&size=64&background=random&color=fff&bold=true" alt="{user.username}\'s Profile" class="profile-img">'
            
            html += f"""
                    <div class="user-info">
                        <strong>{user.username}</strong><br>
                        Has Profile: ✅<br>
                        Has Photo: {"✅" if has_pic else "❌"}<br>
                        {f"Photo URL: {profile.profile_pic.url}" if profile.profile_pic else "No photo"}
                    </div>
                </div>
            </div>
            """
        except Exception as e:
            html += f"""
            <div class="user-card">
                <strong>{user.username}</strong><br>
                Error: {str(e)}
            </div>
            """
    
    html += """
        <hr>
        <p><a href="/chat/">← Back to Chat</a></p>
    </body>
    </html>
    """
    
    return HttpResponse(html)

def profile_photo_test(request):
    """Test view to check profile photo display"""
    all_users = User.objects.all().select_related('profile')
    return render(request, 'profile_photo_test.html', {
        'all_users': all_users
    })

@login_required
def mark_messages_read(request):
    """API endpoint to mark messages as read"""
    if request.method == 'POST':
        data = json.loads(request.body)
        other_username = data.get('other_user')
        
        if other_username:
            try:
                other_user = User.objects.get(username=other_username)
                
                # Mark all unread messages from other_user as read
                unread_messages = Message.objects.filter(
                    sender=other_user,
                    receiver=request.user
                ).exclude(
                    id__in=MessageReadStatus.objects.filter(user=request.user).values_list('message_id', flat=True)
                )
                
                for message in unread_messages:
                    message.mark_as_read(request.user)
                
                return JsonResponse({'status': 'success', 'marked_count': unread_messages.count()})
                
            except User.DoesNotExist:
                return JsonResponse({'status': 'error', 'message': 'User not found'})
    
    return JsonResponse({'status': 'error', 'message': 'Invalid request'})

@login_required
def get_unread_counts(request):
    """API endpoint to get current unread message counts"""
    unread_counts = Message.get_unread_count_by_sender(request.user)
    group_unread_counts = GroupMessage.get_unread_count_by_group(request.user)
    
    return JsonResponse({
        'status': 'success',
        'unread_counts': unread_counts,
        'group_unread_counts': group_unread_counts,
        'total_unread': sum(unread_counts.values()) + sum(group_unread_counts.values())
    })

@login_required
def mark_all_messages_read(request):
    """API endpoint to mark all messages from a specific sender as read"""
    try:
        data = json.loads(request.body)
        sender_id = data.get('sender_id')
        
        if not sender_id:
            return JsonResponse({'status': 'error', 'message': 'sender_id is required'}, status=400)
        
        # Get all unread messages from this sender
        unread_messages = Message.objects.filter(
            sender_id=sender_id,
            receiver=request.user
        ).exclude(
            id__in=MessageReadStatus.objects.filter(user=request.user).values_list('message_id', flat=True)
        )
        
        # Mark all as read
        for message in unread_messages:
            message.mark_as_read(request.user)
        
        return JsonResponse({
            'status': 'success',
            'marked_count': unread_messages.count()
        })
    except Exception as e:
        return JsonResponse({
            'status': 'error', 
            'message': str(e)
        }, status=500)

@login_required
@require_http_methods(["POST"])
def mark_group_messages_read(request):
    """API endpoint to mark all group messages as read"""
    try:
        data = json.loads(request.body)
        group_id = data.get('group_id')
        
        if not group_id:
            return JsonResponse({'status': 'error', 'message': 'group_id is required'}, status=400)
        
        # Get all unread group messages
        unread_messages = GroupMessage.objects.filter(
            group_id=group_id
        ).exclude(
            id__in=GroupMessageReadStatus.objects.filter(user=request.user).values_list('group_message_id', flat=True)
        ).exclude(
            sender=request.user  # Don't mark own messages
        )
        
        # Mark all as read
        for message in unread_messages:
            message.mark_as_read(request.user)
        
        return JsonResponse({
            'status': 'success',
            'marked_count': unread_messages.count()
        })
    except Exception as e:
        return JsonResponse({
            'status': 'error', 
            'message': str(e)
        }, status=500)

@login_required
def generate_group_invite_link(request, group_id):
    """Generate and return a group invitation link"""
    try:
        group = get_object_or_404(Group, id=group_id)
        
        # Check if user can invite others to this group
        if not group.can_user_invite(request.user):
            return JsonResponse({
                'status': 'error',
                'message': 'You do not have permission to invite users to this group'
            }, status=403)
        
        # Generate the invite link
        invite_link = group.get_invite_link(request)
        
        return JsonResponse({
            'status': 'success',
            'invite_link': invite_link,
            'group_name': group.name
        })
    
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)

@login_required
def join_group_by_invite(request, invite_code):
    """Join a group using invitation code"""
    try:
        # Use filter and first() to handle potential duplicates gracefully
        groups = Group.objects.filter(invite_code=invite_code)
        
        if not groups.exists():
            messages.error(request, 'Invalid or expired invitation link.')
            return redirect('group_list')
        
        if groups.count() > 1:
            # Log the issue and use the first group
            print(f"Warning: Multiple groups found with invite code {invite_code}. Using the first one.")
            group = groups.first()
        else:
            group = groups.first()
        
        if request.user in group.members.all():
            messages.info(request, f'You are already a member of {group.name}')
            return redirect('group_chat', group_id=group.id)
        
        if request.method == 'POST':
            # Add user to group
            group.members.add(request.user)
            
            # Create a welcome message
            GroupMessage.objects.create(
                group=group,
                sender=request.user,
                content=f"{request.user.username} joined the group via invitation link! 👋"
            )
            
            messages.success(request, f'Welcome to {group.name}! 🎉')
            return redirect('group_chat', group_id=group.id)
        
        return render(request, 'chat/join_group_invite.html', {
            'group': group,
            'invite_code': invite_code
        })
    
    except Group.DoesNotExist:
        messages.error(request, 'Invalid or expired invitation link')
        return redirect('group_list')

@login_required
@require_http_methods(["POST"])
def send_group_invite_in_chat(request, group_id):
    """Send a group invitation link as a message in the current chat"""
    try:
        data = json.loads(request.body)
        target_username = data.get('target_username')
        personal_message = data.get('message', '')
        
        if not target_username:
            return JsonResponse({
                'status': 'error',
                'message': 'Target username is required'
            }, status=400)
        
        # Get the group and target user
        group = get_object_or_404(Group, id=group_id)
        target_user = get_object_or_404(User, username=target_username)
        
        # Check permissions
        if not group.can_user_invite(request.user):
            return JsonResponse({
                'status': 'error',
                'message': 'You do not have permission to invite users to this group'
            }, status=403)
        
        # Check if target user is already a member
        if target_user in group.members.all():
            return JsonResponse({
                'status': 'error',
                'message': f'{target_username} is already a member of {group.name}'
            }, status=400)
        
        # Generate invite link
        invite_link = group.get_invite_link(request)
        
        # Create invitation message content
        invite_message = f"🎉 You're invited to join our group chat '{group.name}'!\n"
        if personal_message:
            invite_message += f"\n💬 {personal_message}\n"
        invite_message += f"\n🔗 Click here to join: {invite_link}\n\n"
        invite_message += f"Invited by {request.user.get_full_name() or request.user.username}"
        
        # Send the invitation as a direct message
        Message.objects.create(
            sender=request.user,
            receiver=target_user,
            content=invite_message
        )
        
        # Create invitation record
        GroupInvitation.objects.get_or_create(
            group=group,
            invited_by=request.user,
            invited_user=target_user,
            defaults={
                'message': personal_message
            }
        )
        
        return JsonResponse({
            'status': 'success',
            'message': f'Group invitation sent to {target_username}!'
        })
        
    except User.DoesNotExist:
        return JsonResponse({
            'status': 'error',
            'message': f'User {target_username} not found'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)

@login_required
def get_user_groups(request):
    """Get groups that the current user is a member of"""
    try:
        user_groups = request.user.chat_groups.all()
        groups_data = []
        
        for group in user_groups:
            # Only include groups where user can invite others
            if group.can_user_invite(request.user):
                groups_data.append({
                    'id': group.id,
                    'name': group.name,
                    'member_count': group.members.count(),
                    'created_at': group.created_at.isoformat(),
                    'allow_invites': group.allow_invites
                })
        
        return JsonResponse({
            'status': 'success',
            'groups': groups_data
        })
    
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)