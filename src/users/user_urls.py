"""User Management URL Configuration."""
from django.urls import path
from .views import (
    UserProfileView,
    UpdateProfileView,
    ChangePasswordView,
    UserListView,
    UserDetailView,
)

app_name = 'users'

urlpatterns = [
    # User profile management
    path('profile/', UserProfileView.as_view(), name='profile'),
    path('profile/update/', UpdateProfileView.as_view(), name='profile_update'),
    path('profile/change-password/', ChangePasswordView.as_view(), name='change_password'),

    # User list and detail
    path('', UserListView.as_view(), name='user_list'),
    path('<int:pk>/', UserDetailView.as_view(), name='user_detail'),
]
