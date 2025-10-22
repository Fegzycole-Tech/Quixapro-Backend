"""Custom adapters for django-allauth."""

import logging
from allauth.account.adapter import DefaultAccountAdapter
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.core.exceptions import ValidationError

logger = logging.getLogger(__name__)


class CustomAccountAdapter(DefaultAccountAdapter):
    """Custom account adapter for allauth."""

    def is_open_for_signup(self, request):
        """Allow signup."""
        return True

    def save_user(self, request, user, form, commit=True):
        """
        Save user with custom logic.

        Args:
            request: HTTP request
            user: User instance
            form: Registration form
            commit: Whether to save to database

        Returns:
            User instance
        """
        try:
            user = super().save_user(request, user, form, commit=False)
            if commit:
                user.save()
            return user
        except Exception as e:
            logger.error(f"Error saving user: {str(e)}")
            raise ValidationError(f"Failed to save user: {str(e)}")


class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):
    """Custom social account adapter for Google OAuth."""

    def is_open_for_signup(self, request, sociallogin):
        """
        Check if social account signup is allowed.

        Args:
            request: HTTP request
            sociallogin: Social login object

        Returns:
            bool: True if signup is allowed
        """
        return True

    def populate_user(self, request, sociallogin, data):
        """
        Populate user instance from social provider data.

        Args:
            request: HTTP request
            sociallogin: Social login object
            data: User data from provider

        Returns:
            User instance populated with provider data
        """
        try:
            user = super().populate_user(request, sociallogin, data)

            # Get additional data from Google
            if sociallogin.account.provider == 'google':
                extra_data = sociallogin.account.extra_data or {}

                # Set user fields from Google data with fallbacks
                user.email = data.get('email', '').lower()
                user.name = data.get('name') or extra_data.get('name', '')

                # Get photo URL if available
                picture_url = extra_data.get('picture')
                if picture_url:
                    user.photo_url = picture_url

                # Mark email as verified for Google accounts
                user.email_verified = True

                logger.info(f"Populated user from Google: {user.email}")

            return user

        except Exception as e:
            logger.error(f"Error populating user from social data: {str(e)}")
            raise ValidationError(f"Failed to populate user data: {str(e)}")

    def pre_social_login(self, request, sociallogin):
        """
        Connect social account to existing user if email matches.
        This prevents creating duplicate users when they already exist.

        Args:
            request: HTTP request
            sociallogin: Social login object
        """
        if sociallogin.is_existing:
            return

        try:
            email = sociallogin.account.extra_data.get('email', '').lower()
            if not email:
                logger.warning("No email provided in social login data")
                return

            from .models import User

            try:
                existing_user = User.objects.get(email=email)
                # Connect this social account to the existing user
                sociallogin.connect(request, existing_user)
                logger.info(f"Connected Google account to existing user: {email}")
            except User.DoesNotExist:
                # User doesn't exist, will be created
                logger.info(f"New user will be created for: {email}")

        except Exception as e:
            logger.error(f"Error in pre_social_login: {str(e)}")
            # Don't raise - allow login to proceed even if linking fails
