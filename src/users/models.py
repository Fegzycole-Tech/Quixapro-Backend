"""User models for authentication."""

import secrets
import random
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils import timezone


class UserManager(BaseUserManager):
    """Manager for User model with email-based authentication."""

    def create_user(self, email: str, name: str, password: str = None, **extra_fields):
        """Create regular user with optional password (for social auth)."""
        if not email:
            raise ValueError('Email is required')
        if not name:
            raise ValueError('Name is required')

        email = self.normalize_email(email)
        user = self.model(email=email, name=name, **extra_fields)

        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()

        user.save(using=self._db)
        return user

    def create_superuser(self, email: str, password: str, name: str, **extra_fields):
        """Create superuser with required password."""
        if not password:
            raise ValueError('Superuser requires password')

        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        return self.create_user(email, name, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    """Custom user model with email authentication."""

    email = models.EmailField(unique=True, max_length=255)
    name = models.CharField(max_length=255)
    photo_url = models.URLField(blank=True, null=True, max_length=500)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    email_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['name']

    class Meta:
        db_table = 'users'
        ordering = ['-created_at']

    def __str__(self) -> str:
        return self.email

    def get_full_name(self) -> str:
        return self.name

    def get_short_name(self) -> str:
        return self.email


class VerificationToken(models.Model):
    """Unified model for all verification tokens (email, password reset, etc)."""

    TOKEN_TYPE_EMAIL = 'email_verification'
    TOKEN_TYPE_PASSWORD_RESET = 'password_reset'

    TOKEN_TYPE_CHOICES = [
        (TOKEN_TYPE_EMAIL, 'Email Verification'),
        (TOKEN_TYPE_PASSWORD_RESET, 'Password Reset'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='verification_tokens')
    token = models.CharField(max_length=64, db_index=True)
    token_type = models.CharField(max_length=20, choices=TOKEN_TYPE_CHOICES, db_index=True)
    created_at = models.DateTimeField(default=timezone.now)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)

    class Meta:
        db_table = 'verification_tokens'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['token', 'token_type', 'is_used']),
        ]

    def __str__(self) -> str:
        return f"{self.get_token_type_display()} for {self.user.email}"

    @staticmethod
    def generate_secure_token() -> str:
        """Generate a secure random token for password resets."""
        return secrets.token_urlsafe(32)

    @staticmethod
    def generate_numeric_code() -> str:
        """Generate a 4-digit numeric code for email verification."""
        return str(random.randint(1000, 9999))

    def is_valid(self) -> bool:
        """Check if token is still valid."""
        return not self.is_used and timezone.now() < self.expires_at

    @classmethod
    def create_for_email_verification(cls, user: User, expiry_minutes: int = 15):
        """Create a new email verification token (4-digit code)."""
        token = cls.generate_numeric_code()
        expires_at = timezone.now() + timezone.timedelta(minutes=expiry_minutes)
        return cls.objects.create(
            user=user,
            token=token,
            token_type=cls.TOKEN_TYPE_EMAIL,
            expires_at=expires_at
        )

    @classmethod
    def create_for_password_reset(cls, user: User, expiry_hours: int = 1):
        """Create a new password reset token (secure random string)."""
        token = cls.generate_secure_token()
        expires_at = timezone.now() + timezone.timedelta(hours=expiry_hours)
        return cls.objects.create(
            user=user,
            token=token,
            token_type=cls.TOKEN_TYPE_PASSWORD_RESET,
            expires_at=expires_at
        )
