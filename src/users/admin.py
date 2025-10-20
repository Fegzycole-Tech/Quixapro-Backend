from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, VerificationToken


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Admin configuration for custom User model."""

    list_display = ['email', 'name', 'email_verified', 'is_active', 'is_staff', 'created_at']
    list_filter = ['email_verified', 'is_active', 'is_staff', 'is_superuser', 'created_at']
    search_fields = ['email', 'name']
    ordering = ['-created_at']

    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal Info', {'fields': ('name', 'photo_url', 'email_verified')}),
        ('Permissions', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')
        }),
        ('Important dates', {'fields': ('last_login', 'created_at', 'updated_at')}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'name', 'password1', 'password2'),
        }),
    )

    readonly_fields = ['created_at', 'updated_at', 'last_login']


@admin.register(VerificationToken)
class VerificationTokenAdmin(admin.ModelAdmin):
    """Admin configuration for unified VerificationToken model."""

    list_display = ['user', 'token_type', 'token', 'created_at', 'expires_at', 'is_used']
    list_filter = ['token_type', 'is_used', 'created_at', 'expires_at']
    search_fields = ['user__email', 'token']
    ordering = ['-created_at']
    readonly_fields = ['token', 'created_at']
