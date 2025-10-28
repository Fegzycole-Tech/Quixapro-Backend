from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth.password_validation import validate_password
from .models import User
from .services import UserService
from . import constants


class UserSerializer(serializers.ModelSerializer):
    """Serializer for user data."""

    class Meta:
        model = User
        fields = ['id', 'email', 'name', 'photo_url', 'email_verified', 'created_at', 'updated_at']
        read_only_fields = ['id', 'email_verified', 'created_at', 'updated_at']


class RegisterSerializer(serializers.Serializer):
    """Serializer for user registration (password and social auth)."""

    email = serializers.EmailField()
    name = serializers.CharField(max_length=255)
    password = serializers.CharField(
        write_only=True, required=False, allow_blank=True,
        validators=[validate_password], style={'input_type': 'password'}
    )
    photo_url = serializers.URLField(required=False, allow_blank=True)

    def validate_email(self, value):
        """Check if email is already in use."""
        if not UserService.is_email_available(value):
            raise serializers.ValidationError(constants.ERROR_EMAIL_IN_USE)
        return value

    def create(self, validated_data):
        """Create user via service layer."""
        return UserService.create_user(**validated_data)


class LoginSerializer(TokenObtainPairSerializer):
    """JWT login serializer (password-based only)."""

    @classmethod
    def get_token(cls, user):
        """Add custom claims."""
        token = super().get_token(user)
        token['email'] = user.email
        token['name'] = user.name
        return token

    def validate(self, attrs):
        """Validate credentials and return tokens with user data."""
        data = super().validate(attrs)
        data['user'] = UserSerializer(self.user).data
        return data


class UpdateUserSerializer(serializers.Serializer):
    """Serializer for updating user profile."""

    email = serializers.EmailField(required=False)
    name = serializers.CharField(max_length=255, required=False)
    photo_url = serializers.URLField(required=False, allow_blank=True)

    def validate_email(self, value):
        """Check email availability."""
        user = self.context['request'].user
        if not UserService.is_email_available(value, exclude_user_id=user.pk):
            raise serializers.ValidationError(constants.ERROR_EMAIL_IN_USE)
        return value

    def update(self, instance, validated_data):
        """Update user via service."""
        return UserService.update_user(instance, **validated_data)


class ChangePasswordSerializer(serializers.Serializer):
    """Serializer for password change."""

    old_password = serializers.CharField(write_only=True, style={'input_type': 'password'})
    new_password = serializers.CharField(
        write_only=True, validators=[validate_password], style={'input_type': 'password'}
    )
    new_password_confirm = serializers.CharField(write_only=True, style={'input_type': 'password'})

    def validate(self, attrs):
        """Validate passwords match."""
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError({"new_password": constants.ERROR_PASSWORD_MISMATCH})

        # Check old password is correct
        user = self.context['request'].user
        if not user.check_password(attrs['old_password']):
            raise serializers.ValidationError({"old_password": constants.ERROR_OLD_PASSWORD_INCORRECT})

        return attrs


class LogoutSerializer(serializers.Serializer):
    """Serializer for logout."""

    refresh_token = serializers.CharField()


class ForgotPasswordSerializer(serializers.Serializer):
    """Serializer for requesting password reset."""

    email = serializers.EmailField()


class ResetPasswordSerializer(serializers.Serializer):
    """Serializer for resetting password with token."""

    token = serializers.CharField()
    new_password = serializers.CharField(
        write_only=True, validators=[validate_password], style={'input_type': 'password'}
    )
    new_password_confirm = serializers.CharField(write_only=True, style={'input_type': 'password'})

    def validate(self, attrs):
        """Validate passwords match."""
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError({"new_password": constants.ERROR_PASSWORD_MISMATCH})

        return attrs


class VerifyEmailSerializer(serializers.Serializer):
    """Serializer for email verification."""

    email = serializers.EmailField()
    code = serializers.CharField(min_length=4, max_length=4)

    def validate_code(self, value):
        """Validate code is numeric."""
        if not value.isdigit():
            raise serializers.ValidationError("Verification code must be 4 digits.")
        return value


class ResendVerificationSerializer(serializers.Serializer):
    """Serializer for resending verification email."""

    email = serializers.EmailField()


class GoogleAuthSerializer(serializers.Serializer):
    """Serializer for Google OAuth authentication."""

    access_token = serializers.CharField(required=True)
    code = serializers.CharField(required=False)
    id_token = serializers.CharField(required=False)
