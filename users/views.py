from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import update_session_auth_hash, authenticate, login, logout
from .models import Profile, Friendship, FriendRequest
from .forms import UserUpdateForm, ProfileUpdateForm, CustomPasswordChangeForm, FriendRequestForm, UserSearchForm
from django.http import JsonResponse
from django.db.models import Q
from django.core.paginator import Paginator


def login_page(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        print(username)
        print(password)
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, 'Login successful!')
            return redirect('chat_redirect')
        else:
            messages.error(request, 'Invalid email or password. Please try again.')
    if request.user.is_authenticated:
        return redirect('chat_redirect')
    return render(request,'login.html')


@login_required
def logout_page(request):
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('/')


def signup_view(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        username = request.POST.get('username')
        password1 = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')
        profile_pic = request.FILES.get('profile_picture')

        # Check if passwords match
        if password1 != confirm_password:
            messages.error(request, 'Passwords do not match. Please try again.')
            return render(request, 'signup.html')

        # Check if email is already taken
        if User.objects.filter(email=email).exists():
            messages.error(request, 'Email is already in use. Please try another.')
            return render(request, 'signup.html')

        # Check if username is already taken
        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username is already in use. Please try another.')
            return render(request, 'signup.html')

        # Create the new user
        user = User.objects.create_user(username=username,
                                        email=email,
                                        password=password1
                                        )
        user.save()

        # Update the profile with the profile picture (profile is auto-created by signal)
        if profile_pic:
            profile = user.profile
            profile.profile_pic = profile_pic
            profile.save()
        
        messages.success(request, 'Signup successful! You can now log in.')
        return redirect('login')
    if request.user.is_authenticated:
        return redirect('chat_redirect')
    return render(request, 'signup.html')


@login_required
def profile_view(request):
    """Display user profile"""
    # Check if viewing another user's profile
    username = request.GET.get('user')
    
    if username:
        # Viewing another user's profile
        try:
            viewed_user = User.objects.get(username=username)
            
            # Check if the viewed user is a friend or if it's the user's own profile
            if viewed_user == request.user:
                # User viewing their own profile
                is_own_profile = True
                is_friend = False
                can_send_request = False
                pending_request = None
            else:
                # Check friendship status
                is_own_profile = False
                is_friend = request.user.profile.is_friend_with(viewed_user)
                
                # Check if there's a pending friend request
                pending_request = Friendship.objects.filter(
                    Q(user1=request.user, user2=viewed_user) | 
                    Q(user1=viewed_user, user2=request.user),
                    status='pending'
                ).first()
                
                can_send_request = not is_friend and not pending_request
            
            context = {
                'user': viewed_user,
                'profile': viewed_user.profile,
                'is_own_profile': is_own_profile,
                'is_friend': is_friend,
                'can_send_request': can_send_request,
                'pending_request': pending_request,
                'current_user': request.user,
            }
            return render(request, 'users/profile.html', context)
            
        except User.DoesNotExist:
            messages.error(request, 'User not found.')
            return redirect('find_friends')
    
    else:
        # Viewing own profile (default behavior)
        user = request.user
        profile = user.profile
        
        context = {
            'user': user,
            'profile': profile,
            'is_own_profile': True,
            'is_friend': False,
            'can_send_request': False,
            'pending_request': None,
            'current_user': request.user,
        }
        return render(request, 'users/profile.html', context)


@login_required
def profile_edit(request):
    """Edit user profile and personal information"""
    if request.method == 'POST':
        user_form = UserUpdateForm(request.POST, instance=request.user)
        profile_form = ProfileUpdateForm(request.POST, request.FILES, instance=request.user.profile)
        
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, 'Your profile has been updated successfully!')
            return redirect('profile')
        else:
            # Collect all form errors
            for form in [user_form, profile_form]:
                for field, errors in form.errors.items():
                    for error in errors:
                        messages.error(request, f"{field}: {error}")
    else:
        user_form = UserUpdateForm(instance=request.user)
        profile_form = ProfileUpdateForm(instance=request.user.profile)
    
    context = {
        'user_form': user_form,
        'profile_form': profile_form,
    }
    return render(request, 'users/profile_edit.html', context)


@login_required
def change_password(request):
    """Change user password"""
    if request.method == 'POST':
        form = CustomPasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)  # Important for keeping user logged in
            messages.success(request, 'Your password has been changed successfully!')
            return redirect('profile')
        else:
            # Display form errors
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    else:
        form = CustomPasswordChangeForm(request.user)
    
    context = {
        'form': form,
    }
    return render(request, 'users/change_password.html', context)


@login_required
def delete_profile_picture(request):
    """Delete user's profile picture"""
    if request.method == 'POST':
        profile = request.user.profile
        if profile.profile_pic:
            # Delete the file from storage
            profile.profile_pic.delete(save=False)
            profile.profile_pic = None
            profile.save()
            messages.success(request, 'Profile picture deleted successfully!')
        else:
            messages.info(request, 'No profile picture to delete.')
        return redirect('profile_edit')
    return redirect('profile')


@login_required
def account_settings(request):
    """Account settings page with links to various profile functions"""
    return render(request, 'users/account_settings.html')


@login_required
def friends_list(request):
    """Display user's friends list"""
    friends = request.user.profile.get_friends()
    pending_requests = FriendRequest.objects.filter(to_user=request.user)
    sent_requests = FriendRequest.objects.filter(from_user=request.user)
    
    context = {
        'friends': friends,
        'pending_requests': pending_requests,
        'sent_requests': sent_requests,
        'friend_count': len(friends),
        'pending_count': pending_requests.count(),
    }
    return render(request, 'users/friends_list.html', context)

@login_required
def send_friend_request(request):
    """Send a friend request"""
    if request.method == 'POST':
        form = FriendRequestForm(request.POST)
        if form.is_valid():
            to_user = form.cleaned_data['username']
            message = form.cleaned_data.get('message', '')
            
            # Send friend request
            friendship, msg = Friendship.send_friend_request(request.user, to_user)
            
            if friendship:
                # Create notification (or get existing one if friendship was reused)
                friend_request, created = FriendRequest.objects.get_or_create(
                    from_user=request.user,
                    to_user=to_user,
                    defaults={'message': message}
                )
                if not created:
                    # Update message if request already exists
                    friend_request.message = message
                    friend_request.is_read = False
                    friend_request.save()
                
                messages.success(request, msg)
            else:
                messages.error(request, msg)
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, error)
    
    return redirect('friends_list')

@login_required
def respond_friend_request(request, request_id, action):
    """Accept or decline a friend request"""
    if action not in ['accept', 'decline']:
        messages.error(request, "Invalid action")
        return redirect('friends_list')
    
    try:
        friend_request = FriendRequest.objects.get(id=request_id, to_user=request.user)
        from_user = friend_request.from_user
        
        if action == 'accept':
            success, msg = Friendship.accept_friend_request(from_user, request.user)
            if success:
                messages.success(request, f"You are now friends with {from_user.username}!")
            else:
                messages.error(request, msg)
        else:  # decline
            success, msg = Friendship.decline_friend_request(from_user, request.user)
            if success:
                messages.info(request, f"Friend request from {from_user.username} declined")
            else:
                messages.error(request, msg)
        
        # Mark notification as read and delete it
        friend_request.delete()
        
    except FriendRequest.DoesNotExist:
        messages.error(request, "Friend request not found")
    
    return redirect('friends_list')

@login_required
def remove_friend(request, user_id):
    """Remove a friend"""
    if request.method == 'POST':
        try:
            friend = User.objects.get(id=user_id)
            success, msg = Friendship.remove_friend(request.user, friend)
            
            if success:
                messages.success(request, f"Removed {friend.username} from your friends")
            else:
                messages.error(request, msg)
                
        except User.DoesNotExist:
            messages.error(request, "User not found")
    
    return redirect('friends_list')

@login_required
def find_friends(request):
    """Search for users to add as friends"""
    form = UserSearchForm(request.GET)
    users = []
    
    if form.is_valid() and form.cleaned_data['search_query']:
        search_query = form.cleaned_data['search_query']
        
        # Search users by username, first name, or last name
        users = User.objects.filter(
            Q(username__icontains=search_query) |
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query)
        ).exclude(id=request.user.id)[:20]  # Limit to 20 results
        
        # Add friendship status to each user
        for user in users:
            # Check friendship status
            friendship = Friendship.objects.filter(
                Q(user1=request.user, user2=user) | Q(user1=user, user2=request.user)
            ).first()
            
            if friendship:
                if friendship.status == 'accepted':
                    user.friendship_status = 'friends'
                elif friendship.status == 'pending':
                    if friendship.user1 == request.user:
                        user.friendship_status = 'request_sent'
                    else:
                        user.friendship_status = 'request_received'
                else:
                    user.friendship_status = 'not_friends'
            else:
                user.friendship_status = 'not_friends'
    
    context = {
        'form': form,
        'users': users,
        'friend_request_form': FriendRequestForm(),
    }
    return render(request, 'users/find_friends.html', context)

@login_required
def quick_add_friend(request, user_id):
    """Quickly add a friend via AJAX"""
    if request.method == 'POST':
        try:
            to_user = User.objects.get(id=user_id)
            friendship, msg = Friendship.send_friend_request(request.user, to_user)
            
            if friendship:
                # Create notification (or get existing one if friendship was reused)
                friend_request, created = FriendRequest.objects.get_or_create(
                    from_user=request.user,
                    to_user=to_user,
                    defaults={'message': ''}
                )
                if not created:
                    # Update request if it already exists
                    friend_request.is_read = False
                    friend_request.save()
                
                return JsonResponse({
                    'success': True,
                    'message': msg,
                    'status': 'request_sent'
                })
            else:
                return JsonResponse({
                    'success': False,
                    'message': msg
                })
                
        except User.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'User not found'
            })
    
    return JsonResponse({'success': False, 'message': 'Invalid request'})

@login_required
def get_friend_requests_count(request):
    """Get count of pending friend requests for notifications"""
    count = FriendRequest.objects.filter(to_user=request.user).count()
    return JsonResponse({'count': count})

