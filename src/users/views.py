"""Views for user authentication and management."""

from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from drf_spectacular.utils import extend_schema

from .models import User
from .serializers import (
    RegisterSerializer, LoginSerializer, UserSerializer,
    UpdateUserSerializer, ChangePasswordSerializer,
    LogoutSerializer, ForgotPasswordSerializer, ResetPasswordSerializer,
    VerifyEmailSerializer, ResendVerificationSerializer
)
from .services import UserService, TokenService
from . import constants


@extend_schema(tags=['Authentication'])
class RegisterView(generics.CreateAPIView):
    """Register a new user (password or social auth)."""

    permission_classes = [AllowAny]
    serializer_class = RegisterSerializer

    def create(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        # Send verification email
        UserService.send_verification_email(user)

        return Response({
            'user': UserSerializer(user).data,
            'tokens': UserService.generate_tokens(user),
            'message': constants.SUCCESS_VERIFICATION_EMAIL_SENT
        }, status=status.HTTP_201_CREATED)


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
            except Exception as e:
                return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)

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
            return Response(
                {'message': constants.SUCCESS_LOGGED_OUT},
                status=status.HTTP_200_OK
            )
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


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
        # Business validation
        try:
            UserService.validate_user_can_change_password(request.user)
        except Exception as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)

        # Data validation
        serializer = ChangePasswordSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)

        # Execute business logic
        UserService.change_password(request.user, serializer.validated_data['new_password'])

        return Response({'message': constants.SUCCESS_PASSWORD_CHANGED}, status=status.HTTP_200_OK)


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
            return Response({
                'message': constants.SUCCESS_PASSWORD_RESET_EMAIL_SENT
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)


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
            return Response({
                'message': constants.SUCCESS_PASSWORD_RESET
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)


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
            return Response({
                'message': constants.SUCCESS_EMAIL_VERIFIED
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)


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
            return Response({
                'message': constants.SUCCESS_VERIFICATION_CODE_RESENT
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)
