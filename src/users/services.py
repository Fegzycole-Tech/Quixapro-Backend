"""Business logic for user operations."""

from typing import Optional
from django.core.exceptions import ValidationError
from django.utils import timezone
from rest_framework_simplejwt.tokens import RefreshToken
from .models import User, VerificationToken
from common.email_service import EmailService
from . import constants


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
        return User.objects.create_user(
            email=email,
            name=name,
            password=password,
            photo_url=photo_url
        )

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
            raise ValidationError("Invalid credentials")

        if not user.has_usable_password():
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
            raise ValidationError(constants.ERROR_USER_NOT_FOUND)

        if not user.has_usable_password():
            raise ValidationError(constants.ERROR_SOCIAL_AUTH_PASSWORD_RESET)

        # Invalidate any existing unused password reset tokens
        VerificationToken.objects.filter(
            user=user,
            token_type=VerificationToken.TOKEN_TYPE_PASSWORD_RESET,
            is_used=False
        ).update(is_used=True)

        # Create new token
        reset_token = VerificationToken.create_for_password_reset(user)

        # Send email
        email_service = EmailService()
        email_service.send_password_reset_email(
            to_email=user.email,
            to_name=user.name,
            reset_token=reset_token.token
        )

    @staticmethod
    def reset_password(token: str, new_password: str) -> None:
        """
        Reset user password using a reset token.

        Args:
            token: Password reset token
            new_password: New password to set

        Raises:
            ValidationError: If token is invalid or expired
        """
        try:
            reset_token = VerificationToken.objects.get(
                token=token,
                token_type=VerificationToken.TOKEN_TYPE_PASSWORD_RESET
            )
        except VerificationToken.DoesNotExist:
            raise ValidationError(constants.ERROR_INVALID_RESET_TOKEN)

        if not reset_token.is_valid():
            raise ValidationError(constants.ERROR_INVALID_RESET_TOKEN)

        # Reset the password
        user = reset_token.user
        user.set_password(new_password)
        user.save()

        # Mark token as used
        reset_token.is_used = True
        reset_token.save()

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
            raise ValidationError(constants.ERROR_EMAIL_ALREADY_VERIFIED)

        # Invalidate any existing unused email verification codes
        VerificationToken.objects.filter(
            user=user,
            token_type=VerificationToken.TOKEN_TYPE_EMAIL,
            is_used=False
        ).update(is_used=True)

        # Create new verification code
        verification_token = VerificationToken.create_for_email_verification(user)

        # Send email
        email_service = EmailService()
        email_service.send_verification_email(
            to_email=user.email,
            to_name=user.name,
            verification_code=verification_token.token
        )

        return verification_token

    @staticmethod
    def verify_email(code: str, user: User) -> None:
        """
        Verify user email using verification code.

        Args:
            code: 4-digit verification code
            user: User instance

        Raises:
            ValidationError: If code is invalid or expired
        """
        try:
            verification_token = VerificationToken.objects.get(
                token=code,
                user=user,
                token_type=VerificationToken.TOKEN_TYPE_EMAIL
            )
        except VerificationToken.DoesNotExist:
            raise ValidationError(constants.ERROR_INVALID_VERIFICATION_CODE)

        if not verification_token.is_valid():
            raise ValidationError(constants.ERROR_INVALID_VERIFICATION_CODE)

        # Mark email as verified
        user.email_verified = True
        user.save()

        # Mark code as used
        verification_token.is_used = True
        verification_token.save()


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
