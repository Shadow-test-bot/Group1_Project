from django.urls import path
from users.views import (
    login_page, logout_page, signup_view, 
    profile_view, profile_edit, change_password, 
    delete_profile_picture, account_settings,
    friends_list, send_friend_request, respond_friend_request,
    remove_friend, find_friends, quick_add_friend,
    get_friend_requests_count
)

urlpatterns = [
    path('login/', login_page, name="login"),
    path('logout/', logout_page, name="logout"),
    path('signup/', signup_view, name="signup"),
    path('profile/', profile_view, name="profile"),
    path('profile/edit/', profile_edit, name="profile_edit"),
    path('profile/password/', change_password, name="change_password"),
    path('profile/delete-picture/', delete_profile_picture, name="delete_profile_picture"),
    path('account/', account_settings, name="account_settings"),
    
    # Friend management URLs
    path('friends/', friends_list, name='friends_list'),
    path('friends/send-request/', send_friend_request, name='send_friend_request'),
    path('friends/respond/<int:request_id>/<str:action>/', respond_friend_request, name='respond_friend_request'),
    path('friends/remove/<int:user_id>/', remove_friend, name='remove_friend'),
    path('friends/find/', find_friends, name='find_friends'),
    path('friends/quick-add/<int:user_id>/', quick_add_friend, name='quick_add_friend'),
    path('api/friend-requests-count/', get_friend_requests_count, name='friend_requests_count'),
]
