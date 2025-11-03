"""Custom permission classes for the application."""

from rest_framework import permissions


class IsEmailVerified(permissions.BasePermission):
    message = "Email verification required. Please verify your email to access this resource."

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.email_verified
        )
