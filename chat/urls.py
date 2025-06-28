from django.urls import path , include
from . import views 
from django.contrib.auth import views as auth_views

urlpatterns = [
     path('', views.home, name='home'),
     path('chat/', views.chat_redirect, name='chat_redirect'),
     path('chat/<str:room_name>/', views.chat_room, name='chat'),
     path('password_reset/', views.CustomPasswordResetView.as_view(), name='password_reset'),
     path('password_reset_done/', auth_views.PasswordResetDoneView.as_view(), name='password_reset_done'),
     path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
     path('reset/done/', auth_views.PasswordResetCompleteView.as_view(), name='password_reset_complete'),
     path('groups/', views.group_list, name='group_list'),
     path('groups/create/', views.create_group, name='create_group'),
     path('groups/<int:group_id>/', views.group_chat, name='group_chat'),
     path('groups/<int:group_id>/send/', views.send_group_message, name='send_group_message'),
     path('groups/<int:group_id>/join/', views.join_group, name='join_group'),
     path('api/send_group_email/', views.send_group_email_api, name='send_group_email'),
     path('debug/photos/', views.debug_profile_photos, name='debug_photos'),
     path('profile-photo-test/', views.profile_photo_test, name='profile_photo_test'),
     path('api/mark-messages-read/', views.mark_messages_read, name='mark_messages_read'),
     path('api/get-unread-counts/', views.get_unread_counts, name='get_unread_counts'),
     path('api/mark-all-messages-read/', views.mark_all_messages_read, name='mark_all_messages_read'),
     path('api/mark-group-messages-read/<int:group_id>/', views.mark_group_messages_read, name='mark_group_messages_read'),
     path('api/generate-group-invite-link/<int:group_id>/', views.generate_group_invite_link, name='generate_group_invite_link'),
     path('api/send-group-invite-in-chat/<int:group_id>/', views.send_group_invite_in_chat, name='send_group_invite_in_chat'),
     path('api/get-user-groups/', views.get_user_groups, name='get_user_groups'),
     path('join-group/<uuid:invite_code>/', views.join_group_by_invite, name='join_group_by_invite'),
]