"""Business logic for user operations."""

import logging
import requests
from typing import Optional
from django.core.exceptions import ValidationError
from django.conf import settings
from django.db import transaction
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.tokens import RefreshToken
from .models import User, VerificationToken
from common.email_service import EmailService
from . import constants

logger = logging.getLogger(__name__)


class UserService:
    """Service class for user-related business logic."""

    @staticmethod
    def create_user(email: str, name: str, password: Optional[str] = None,
                   photo_url: Optional[str] = None) -> User:
        """
        Create a new user with optional password.

        Args:
            email: User's email address
            name: User's full name
            password: Optional password (None for social auth)
            photo_url: Optional profile photo URL

        Returns:
            Created User instance
        """
        user = User.objects.create_user(
            email=email,
            name=name,
            password=password,
            photo_url=photo_url
        )
        logger.info(f"User created: {email} (social auth: {password is None})")
        return user

    @staticmethod
    def generate_tokens(user: User) -> dict:
        """
        Generate JWT tokens for a user.

        Args:
            user: User instance

        Returns:
            Dictionary with 'access' and 'refresh' tokens
        """
        refresh = RefreshToken.for_user(user)
        return {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }

    @staticmethod
    def is_email_available(email: str, exclude_user_id: Optional[int] = None) -> bool:
        """
        Check if an email is available for use.

        Args:
            email: Email to check
            exclude_user_id: Optional user ID to exclude from check

        Returns:
            True if email is available, False otherwise
        """
        queryset = User.objects.filter(email=email)
        if exclude_user_id:
            queryset = queryset.exclude(pk=exclude_user_id)
        return not queryset.exists()

    @staticmethod
    def update_user(user: User, **kwargs) -> User:
        """
        Update user fields.

        Args:
            user: User instance to update
            **kwargs: Fields to update

        Returns:
            Updated User instance
        """
        for field, value in kwargs.items():
            setattr(user, field, value)
        user.save()
        return user

    @staticmethod
    def change_password(user: User, new_password: str) -> None:
        """
        Change user's password.

        Args:
            user: User instance
            new_password: New password to set
        """
        user.set_password(new_password)
        user.save()
        logger.info(f"Password changed for user: {user.email}")

    @staticmethod
    def validate_user_can_login(email: str) -> User:
        """
        Validate user exists and can login with password.

        Args:
            email: User's email

        Returns:
            User instance

        Raises:
            ValidationError: If user doesn't exist or uses social auth
        """
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            logger.warning(f"Login attempt with non-existent email: {email}")
            raise ValidationError("Invalid credentials")

        if not user.has_usable_password():
            logger.warning(f"Password login attempt for social auth user: {email}")
            raise ValidationError(constants.ERROR_SOCIAL_AUTH_LOGIN)

        return user

    @staticmethod
    def validate_user_can_change_password(user: User) -> None:
        """
        Validate user can change password.

        Args:
            user: User instance

        Raises:
            ValidationError: If user uses social auth
        """
        if not user.has_usable_password():
            logger.warning(f"Password change attempt for social auth user: {user.email}")
            raise ValidationError(constants.ERROR_SOCIAL_AUTH_PASSWORD_CHANGE)

    @staticmethod
    def request_password_reset(email: str) -> None:
        """
        Create and send password reset token to user.

        Args:
            email: User's email address

        Raises:
            ValidationError: If user doesn't exist or uses social auth
        """
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            logger.warning(f"Password reset requested for non-existent user: {email}")
            raise ValidationError(constants.ERROR_USER_NOT_FOUND)

        if not user.has_usable_password():
            logger.warning(f"Password reset requested for social auth user: {email}")
            raise ValidationError(constants.ERROR_SOCIAL_AUTH_PASSWORD_RESET)

        # Invalidate any existing unused password reset tokens
        invalidated_count = VerificationToken.objects.filter(
            user=user,
            token_type=VerificationToken.TOKEN_TYPE_PASSWORD_RESET,
            is_used=False
        ).update(is_used=True)
        if invalidated_count > 0:
            logger.info(f"Invalidated {invalidated_count} existing password reset tokens for user: {email}")

        # Create new token
        reset_token = VerificationToken.create_for_password_reset(user)

        # Send email with reset URL including email and token
        email_service = EmailService()
        email_service.send_password_reset_email(
            to_email=user.email,
            to_name=user.name,
            reset_token=reset_token.token,
            reset_url=settings.PASSWORD_RESET_URL
        )
        logger.info(f"Password reset token created and email sent for user: {email}")

    @staticmethod
    def reset_password(email: str, token: str, new_password: str) -> None:
        """
        Reset user password using email and reset token.

        Args:
            email: User's email address
            token: Password reset token
            new_password: New password to set

        Raises:
            ValidationError: If email/token combination is invalid or expired
        """
        # First verify the user exists
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            logger.warning(f"Password reset attempted with invalid email: {email}")
            raise ValidationError(constants.ERROR_INVALID_RESET_TOKEN)

        # Get the reset token for this specific user
        try:
            reset_token = VerificationToken.objects.get(
                user=user,
                token=token,
                token_type=VerificationToken.TOKEN_TYPE_PASSWORD_RESET
            )
        except VerificationToken.DoesNotExist:
            logger.warning(f"Password reset attempted with invalid token for user: {email}")
            raise ValidationError(constants.ERROR_INVALID_RESET_TOKEN)

        if not reset_token.is_valid():
            logger.warning(f"Password reset attempted with expired token for user: {email}")
            raise ValidationError(constants.ERROR_INVALID_RESET_TOKEN)

        # Reset the password
        user.set_password(new_password)
        user.save()

        # Mark token as used
        reset_token.is_used = True
        reset_token.save()

        logger.info(f"Password reset successfully for user: {email}")

    @staticmethod
    def send_verification_email(user: User) -> VerificationToken:
        """
        Send email verification code to user.

        Args:
            user: User instance

        Returns:
            VerificationToken instance

        Raises:
            ValidationError: If email is already verified
        """
        if user.email_verified:
            logger.warning(f"Verification email requested for already verified user: {user.email}")
            raise ValidationError(constants.ERROR_EMAIL_ALREADY_VERIFIED)

        # Invalidate any existing unused email verification codes
        invalidated_count = VerificationToken.objects.filter(
            user=user,
            token_type=VerificationToken.TOKEN_TYPE_EMAIL,
            is_used=False
        ).update(is_used=True)
        if invalidated_count > 0:
            logger.info(f"Invalidated {invalidated_count} existing verification codes for user: {user.email}")

        # Create new verification code
        verification_token = VerificationToken.create_for_email_verification(user)

        # Send email
        email_service = EmailService()
        email_service.send_verification_email(
            to_email=user.email,
            to_name=user.name,
            verification_code=verification_token.token
        )

        logger.info(f"Verification email sent to user: {user.email}")
        return verification_token

    @staticmethod
    def resend_verification_email(email: str) -> VerificationToken:
        """
        Resend verification email to user by email address.

        Args:
            email: User's email address

        Returns:
            VerificationToken instance

        Raises:
            ValidationError: If user doesn't exist or email is already verified
        """
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            logger.warning(f"Resend verification requested for non-existent email: {email}")
            raise ValidationError(constants.ERROR_USER_NOT_FOUND)

        # send_verification_email already checks if email is verified
        return UserService.send_verification_email(user)

    @staticmethod
    def verify_email(email: str, code: str) -> User:
        """
        Verify user email using verification code.

        Args:
            email: User's email address
            code: 4-digit verification code

        Returns:
            User: The user whose email was verified

        Raises:
            ValidationError: If code is invalid, expired, or doesn't match the email
        """
        # First verify the user exists
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            logger.warning(f"Email verification attempted for non-existent email: {email}")
            raise ValidationError(constants.ERROR_INVALID_VERIFICATION_CODE)

        # Check if user is already verified
        if user.email_verified:
            logger.warning(f"Email verification attempted for already verified user: {user.email}")
            raise ValidationError(constants.ERROR_EMAIL_ALREADY_VERIFIED)

        # Get verification token for this specific user and code
        try:
            verification_token = VerificationToken.objects.get(
                user=user,
                token=code,
                token_type=VerificationToken.TOKEN_TYPE_EMAIL,
                is_used=False
            )
        except VerificationToken.DoesNotExist:
            logger.warning(f"Email verification attempted with invalid code for user: {email}")
            raise ValidationError(constants.ERROR_INVALID_VERIFICATION_CODE)

        if not verification_token.is_valid():
            logger.warning(f"Email verification attempted with expired code for user: {user.email}")
            raise ValidationError(constants.ERROR_INVALID_VERIFICATION_CODE)

        # Mark email as verified
        user.email_verified = True
        user.save()

        # Mark code as used
        verification_token.is_used = True
        verification_token.save()

        logger.info(f"Email verified successfully for user: {user.email}")
        return user

    @staticmethod
    def authenticate_with_google(access_token: str) -> dict:
        """
        Authenticate user with Google OAuth access token.

        Args:
            access_token: Google OAuth2 access token

        Returns:
            dict: Dictionary containing user, access_token, and refresh_token

        Raises:
            AuthenticationFailed: If token is invalid or authentication fails
        """
        # Fetch user info from Google
        user_info = UserService._get_google_user_info(access_token)

        # Get or create user
        user = UserService._get_or_create_google_user(user_info)

        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)

        logger.info(f"Google authentication successful for user: {user.email}")

        return {
            'user': user,
            'access_token': str(refresh.access_token),
            'refresh_token': str(refresh),
        }

    @staticmethod
    def _get_google_user_info(access_token: str) -> dict:
        """
        Fetch user information from Google using the access token.

        Args:
            access_token: Google OAuth2 access token

        Returns:
            dict: User information from Google

        Raises:
            AuthenticationFailed: If token is invalid or request fails
        """
        try:
            response = requests.get(
                'https://www.googleapis.com/oauth2/v2/userinfo',
                headers={'Authorization': f'Bearer {access_token}'},
                timeout=10
            )

            if response.status_code != 200:
                logger.error(f"Google API returned status {response.status_code}: {response.text}")
                raise AuthenticationFailed('Invalid access token')

            user_info = response.json()

            # Validate required fields
            if not user_info.get('email'):
                raise AuthenticationFailed('Email not provided by Google')

            if not user_info.get('verified_email'):
                raise AuthenticationFailed('Email not verified by Google')

            return user_info

        except requests.RequestException as e:
            logger.error(f"Failed to fetch Google user info: {str(e)}")
            raise AuthenticationFailed('Failed to verify access token with Google')

    @staticmethod
    def _get_or_create_google_user(user_info: dict) -> User:
        """
        Get or create a user based on Google user information.

        Args:
            user_info: User information from Google

        Returns:
            User: The created or existing user
        """
        email = user_info['email']

        try:
            # Try to get existing user
            user = User.objects.get(email=email)
            logger.info(f"Existing user found for Google auth: {email}")
            return user

        except User.DoesNotExist:
            # Create new user
            with transaction.atomic():
                # Extract name from Google user info
                given_name = user_info.get('given_name', '')
                family_name = user_info.get('family_name', '')
                name = f"{given_name} {family_name}".strip() or email.split('@')[0]

                # Create user without password (social auth user)
                user = User.objects.create_user(
                    email=email,
                    name=name,
                    password=None,  # No password for social auth users
                    photo_url=user_info.get('picture'),
                    email_verified=True,  # Google emails are already verified
                )
                # Note: password=None makes user.has_usable_password() return False
                logger.info(f"New user created from Google auth: {email}")
                return user


class TokenService:
    """Service class for token-related operations."""

    @staticmethod
    def blacklist_token(refresh_token: str) -> None:
        """
        Blacklist a refresh token.

        Args:
            refresh_token: Refresh token string to blacklist

        Raises:
            Exception: If token is invalid
        """
        token = RefreshToken(refresh_token)
        token.blacklist()
        logger.info(f"Refresh token blacklisted: {refresh_token[:20]}...")
