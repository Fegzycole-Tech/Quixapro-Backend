"""Views for user authentication and management."""

from rest_framework import generics, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework.exceptions import ValidationError as DRFValidationError
from drf_spectacular.utils import extend_schema
from django.db import transaction
from django.core.exceptions import ValidationError

from .models import User
from .serializers import (
    RegisterSerializer, LoginSerializer, UserSerializer,
    UpdateUserSerializer, ChangePasswordSerializer,
    LogoutSerializer, ForgotPasswordSerializer, ResetPasswordSerializer,
    VerifyEmailSerializer, ResendVerificationSerializer
)
from .services import UserService, TokenService
from . import constants
from common.exceptions import EmailSendError
from common.responses import (
    success_response,
    error_response,
    service_unavailable_response,
    internal_server_error_response
)


@extend_schema(tags=['Authentication'])
class RegisterView(generics.CreateAPIView):
    """Register a new user (password or social auth)."""

    permission_classes = [AllowAny]
    serializer_class = RegisterSerializer

    def create(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            with transaction.atomic():
                user = serializer.save()

                # Send verification email - if this fails, user creation will be rolled back
                UserService.send_verification_email(user)

            return success_response(
                data={
                    'user': UserSerializer(user).data,
                    'tokens': UserService.generate_tokens(user)
                },
                message=constants.SUCCESS_VERIFICATION_EMAIL_SENT,
                status_code=status.HTTP_201_CREATED
            )

        except EmailSendError:
            return service_unavailable_response(
                detail='User registration failed due to email service error. Please try again later.',
                error_code='EMAIL_SERVICE_ERROR'
            )
        except Exception:
            return internal_server_error_response(
                detail='An unexpected error occurred during registration.',
                error_code='REGISTRATION_ERROR'
            )


@extend_schema(tags=['Authentication'])
class LoginView(TokenObtainPairView):
    """Login with email and password."""

    permission_classes = [AllowAny]
    serializer_class = LoginSerializer

    def post(self, request):
        """Validate user can login before processing."""
        email = request.data.get('email')
        if email:
            try:
                UserService.validate_user_can_login(email)
            except ValidationError as e:
                return error_response(
                    detail=str(e),
                    error_code='VALIDATION_ERROR',
                    status_code=status.HTTP_400_BAD_REQUEST
                )
            except Exception:
                return internal_server_error_response(
                    detail='An unexpected error occurred during login validation.',
                    error_code='LOGIN_VALIDATION_ERROR'
                )

        return super().post(request)


class LogoutView(APIView):
    """Logout by blacklisting refresh token."""

    permission_classes = [IsAuthenticated]
    serializer_class = LogoutSerializer

    @extend_schema(
        tags=['Authentication'],
        request=LogoutSerializer
    )
    def post(self, request):
        serializer = LogoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            TokenService.blacklist_token(serializer.validated_data['refresh_token'])
            return success_response(
                message=constants.SUCCESS_LOGGED_OUT,
                status_code=status.HTTP_200_OK
            )
        except (InvalidToken, TokenError):
            return error_response(
                detail='Invalid or expired refresh token.',
                error_code='INVALID_TOKEN',
                status_code=status.HTTP_400_BAD_REQUEST
            )
        except Exception:
            return internal_server_error_response(
                detail='An unexpected error occurred during logout.',
                error_code='LOGOUT_ERROR'
            )


@extend_schema(tags=['Authentication'])
class RefreshTokenView(TokenRefreshView):
    """Refresh access token."""

    permission_classes = [AllowAny]


@extend_schema(tags=['User Profile'])
class UserProfileView(generics.RetrieveAPIView):
    """Get current user profile."""

    permission_classes = [IsAuthenticated]
    serializer_class = UserSerializer

    def get_object(self):
        return self.request.user


@extend_schema(tags=['User Profile'])
class UpdateProfileView(generics.UpdateAPIView):
    """Update current user profile."""

    permission_classes = [IsAuthenticated]
    serializer_class = UpdateUserSerializer

    def get_object(self):
        return self.request.user


class ChangePasswordView(APIView):
    """Change user password."""

    permission_classes = [IsAuthenticated]
    serializer_class = ChangePasswordSerializer

    @extend_schema(
        tags=['User Profile'],
        request=ChangePasswordSerializer
    )
    def post(self, request):
        try:
            # Business validation
            UserService.validate_user_can_change_password(request.user)

            # Data validation
            serializer = ChangePasswordSerializer(data=request.data, context={'request': request})
            serializer.is_valid(raise_exception=True)

            # Execute business logic
            UserService.change_password(request.user, serializer.validated_data['new_password'])

            return success_response(
                message=constants.SUCCESS_PASSWORD_CHANGED,
                status_code=status.HTTP_200_OK
            )
        except (ValidationError, DRFValidationError) as e:
            return error_response(
                detail=str(e),
                error_code='VALIDATION_ERROR',
                status_code=status.HTTP_400_BAD_REQUEST
            )
        except Exception:
            return internal_server_error_response(
                detail='An unexpected error occurred while changing password.',
                error_code='PASSWORD_CHANGE_ERROR'
            )


@extend_schema(tags=['User Management'])
class UserListView(generics.ListAPIView):
    """List all users."""

    queryset = User.objects.all()
    permission_classes = [IsAuthenticated]
    serializer_class = UserSerializer


@extend_schema(tags=['User Management'])
class UserDetailView(generics.RetrieveAPIView):
    """Get user details by ID."""

    queryset = User.objects.all()
    permission_classes = [IsAuthenticated]
    serializer_class = UserSerializer


class ForgotPasswordView(APIView):
    """Request password reset token."""

    permission_classes = [AllowAny]
    serializer_class = ForgotPasswordSerializer

    @extend_schema(
        tags=['Password Reset'],
        request=ForgotPasswordSerializer,
        description="Request a password reset token. An email will be sent with reset instructions."
    )
    def post(self, request):
        serializer = ForgotPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            UserService.request_password_reset(serializer.validated_data['email'])
            return success_response(
                message=constants.SUCCESS_PASSWORD_RESET_EMAIL_SENT,
                status_code=status.HTTP_200_OK
            )
        except ValidationError as e:
            return error_response(
                detail=str(e),
                error_code='VALIDATION_ERROR',
                status_code=status.HTTP_400_BAD_REQUEST
            )
        except EmailSendError:
            return service_unavailable_response(
                detail='Password reset email could not be sent. Please try again later.',
                error_code='EMAIL_SERVICE_ERROR'
            )
        except Exception:
            return internal_server_error_response(
                detail='An unexpected error occurred during password reset request.',
                error_code='PASSWORD_RESET_REQUEST_ERROR'
            )


class ResetPasswordView(APIView):
    """Reset password using token."""

    permission_classes = [AllowAny]
    serializer_class = ResetPasswordSerializer

    @extend_schema(
        tags=['Password Reset'],
        request=ResetPasswordSerializer,
        description="Reset password using the token received via email."
    )
    def post(self, request):
        serializer = ResetPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            UserService.reset_password(
                serializer.validated_data['token'],
                serializer.validated_data['new_password']
            )
            return success_response(
                message=constants.SUCCESS_PASSWORD_RESET,
                status_code=status.HTTP_200_OK
            )
        except ValidationError as e:
            return error_response(
                detail=str(e),
                error_code='VALIDATION_ERROR',
                status_code=status.HTTP_400_BAD_REQUEST
            )
        except Exception:
            return internal_server_error_response(
                detail='An unexpected error occurred during password reset.',
                error_code='PASSWORD_RESET_ERROR'
            )


class VerifyEmailView(APIView):
    """Verify email address with code."""

    permission_classes = [IsAuthenticated]
    serializer_class = VerifyEmailSerializer

    @extend_schema(
        tags=['Email Verification'],
        request=VerifyEmailSerializer,
        description="Verify email address using the 4-digit code sent to your email."
    )
    def post(self, request):
        serializer = VerifyEmailSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            UserService.verify_email(
                code=serializer.validated_data['code'],
                user=request.user
            )
            return success_response(
                message=constants.SUCCESS_EMAIL_VERIFIED,
                status_code=status.HTTP_200_OK
            )
        except ValidationError as e:
            return error_response(
                detail=str(e),
                error_code='VALIDATION_ERROR',
                status_code=status.HTTP_400_BAD_REQUEST
            )
        except Exception:
            return internal_server_error_response(
                detail='An unexpected error occurred during email verification.',
                error_code='EMAIL_VERIFICATION_ERROR'
            )


class ResendVerificationView(APIView):
    """Resend email verification code."""

    permission_classes = [IsAuthenticated]
    serializer_class = ResendVerificationSerializer

    @extend_schema(
        tags=['Email Verification'],
        description="Resend verification code to your email address."
    )
    def post(self, request):
        try:
            UserService.send_verification_email(request.user)
            return success_response(
                message=constants.SUCCESS_VERIFICATION_CODE_RESENT,
                status_code=status.HTTP_200_OK
            )
        except ValidationError as e:
            return error_response(
                detail=str(e),
                error_code='VALIDATION_ERROR',
                status_code=status.HTTP_400_BAD_REQUEST
            )
        except EmailSendError:
            return service_unavailable_response(
                detail='Verification email could not be sent. Please try again later.',
                error_code='EMAIL_SERVICE_ERROR'
            )
        except Exception:
            return internal_server_error_response(
                detail='An unexpected error occurred while resending verification code.',
                error_code='RESEND_VERIFICATION_ERROR'
            )
