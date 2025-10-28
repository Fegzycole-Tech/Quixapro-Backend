"""Tests for user services."""

from django.test import TestCase
from django.core.exceptions import ValidationError
from unittest.mock import patch, MagicMock
from users.models import User, VerificationToken
from users.services import UserService, TokenService
from users import constants


class UserServiceTest(TestCase):
    """Tests for UserService."""

    def setUp(self):
        """Set up test users."""
        self.user = User.objects.create_user(
            email='test@example.com',
            name='Test User',
            password='testpass123'
        )
        self.social_user = User.objects.create_user(
            email='social@example.com',
            name='Social User'
        )

    def test_create_user(self):
        """Test creating a user via service."""
        user = UserService.create_user(
            email='new@example.com',
            name='New User',
            password='newpass123'
        )
        self.assertEqual(user.email, 'new@example.com')
        self.assertEqual(user.name, 'New User')
        self.assertTrue(user.check_password('newpass123'))

    def test_generate_tokens(self):
        """Test generating JWT tokens."""
        tokens = UserService.generate_tokens(self.user)

        self.assertIn('access', tokens)
        self.assertIn('refresh', tokens)
        self.assertTrue(isinstance(tokens['access'], str))
        self.assertTrue(isinstance(tokens['refresh'], str))

    def test_is_email_available(self):
        """Test email availability check."""
        # Existing email should not be available
        self.assertFalse(UserService.is_email_available('test@example.com'))

        # New email should be available
        self.assertTrue(UserService.is_email_available('new@example.com'))

        # Same email excluded should be available
        self.assertTrue(
            UserService.is_email_available('test@example.com', exclude_user_id=self.user.pk)
        )

    def test_update_user(self):
        """Test updating user."""
        updated_user = UserService.update_user(
            self.user,
            name='Updated Name',
            photo_url='https://example.com/photo.jpg'
        )

        self.assertEqual(updated_user.name, 'Updated Name')
        self.assertEqual(updated_user.photo_url, 'https://example.com/photo.jpg')

    def test_change_password(self):
        """Test changing password."""
        UserService.change_password(self.user, 'newpassword123')

        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('newpassword123'))

    def test_validate_user_can_login_success(self):
        """Test validating user can login."""
        user = UserService.validate_user_can_login('test@example.com')
        self.assertEqual(user, self.user)

    def test_validate_user_can_login_social_auth_fails(self):
        """Test social auth user cannot login with password."""
        with self.assertRaises(ValidationError) as cm:
            UserService.validate_user_can_login('social@example.com')

        self.assertIn(constants.ERROR_SOCIAL_AUTH_LOGIN, str(cm.exception))

    def test_validate_user_can_login_nonexistent_fails(self):
        """Test nonexistent user cannot login."""
        with self.assertRaises(ValidationError):
            UserService.validate_user_can_login('nonexistent@example.com')

    def test_validate_user_can_change_password_success(self):
        """Test user with password can change it."""
        # Should not raise exception
        UserService.validate_user_can_change_password(self.user)

    def test_validate_user_can_change_password_social_auth_fails(self):
        """Test social auth user cannot change password."""
        with self.assertRaises(ValidationError) as cm:
            UserService.validate_user_can_change_password(self.social_user)

        self.assertIn(constants.ERROR_SOCIAL_AUTH_PASSWORD_CHANGE, str(cm.exception))

    @patch('users.services.EmailService')
    def test_request_password_reset_success(self, mock_email_service):
        """Test requesting password reset."""
        mock_instance = MagicMock()
        mock_email_service.return_value = mock_instance

        UserService.request_password_reset('test@example.com')

        # Should create a token
        token = VerificationToken.objects.filter(
            user=self.user,
            token_type=VerificationToken.TOKEN_TYPE_PASSWORD_RESET
        ).first()
        self.assertIsNotNone(token)

        # Should send email
        mock_instance.send_password_reset_email.assert_called_once()

    def test_request_password_reset_nonexistent_user(self):
        """Test password reset for nonexistent user."""
        with self.assertRaises(ValidationError) as cm:
            UserService.request_password_reset('nonexistent@example.com')

        self.assertIn(constants.ERROR_USER_NOT_FOUND, str(cm.exception))

    @patch('users.services.EmailService')
    def test_request_password_reset_social_auth_fails(self, mock_email_service):
        """Test password reset fails for social auth user."""
        with self.assertRaises(ValidationError) as cm:
            UserService.request_password_reset('social@example.com')

        self.assertIn(constants.ERROR_SOCIAL_AUTH_PASSWORD_RESET, str(cm.exception))

    def test_reset_password_success(self):
        """Test resetting password with valid token."""
        # Create reset token
        reset_token = VerificationToken.create_for_password_reset(self.user)

        # Reset password
        UserService.reset_password(reset_token.token, 'newpassword123')

        # Verify password changed
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('newpassword123'))

        # Verify token marked as used
        reset_token.refresh_from_db()
        self.assertTrue(reset_token.is_used)

    def test_reset_password_invalid_token(self):
        """Test resetting password with invalid token."""
        with self.assertRaises(ValidationError) as cm:
            UserService.reset_password('invalid-token', 'newpassword123')

        self.assertIn(constants.ERROR_INVALID_RESET_TOKEN, str(cm.exception))

    @patch('users.services.EmailService')
    def test_send_verification_email_success(self, mock_email_service):
        """Test sending verification email."""
        mock_instance = MagicMock()
        mock_email_service.return_value = mock_instance

        token = UserService.send_verification_email(self.user)

        self.assertIsNotNone(token)
        self.assertEqual(token.token_type, VerificationToken.TOKEN_TYPE_EMAIL)
        mock_instance.send_verification_email.assert_called_once()

    @patch('users.services.EmailService')
    def test_send_verification_email_already_verified(self, mock_email_service):
        """Test sending verification email to already verified user."""
        self.user.email_verified = True
        self.user.save()

        with self.assertRaises(ValidationError) as cm:
            UserService.send_verification_email(self.user)

        self.assertIn(constants.ERROR_EMAIL_ALREADY_VERIFIED, str(cm.exception))

    def test_verify_email_success(self):
        """Test verifying email with valid email and code."""
        # Create verification token
        token = VerificationToken.create_for_email_verification(self.user)

        # Verify email using email and code
        returned_user = UserService.verify_email(self.user.email, token.token)

        # Verify correct user was returned
        self.assertEqual(returned_user.id, self.user.id)

        # Verify email marked as verified
        self.user.refresh_from_db()
        self.assertTrue(self.user.email_verified)

        # Verify token marked as used
        token.refresh_from_db()
        self.assertTrue(token.is_used)

    def test_verify_email_invalid_code(self):
        """Test verifying email with invalid code."""
        with self.assertRaises(ValidationError) as cm:
            UserService.verify_email(self.user.email, '9999')

        self.assertIn(constants.ERROR_INVALID_VERIFICATION_CODE, str(cm.exception))

    def test_verify_email_invalid_email(self):
        """Test verifying email with non-existent email."""
        with self.assertRaises(ValidationError) as cm:
            UserService.verify_email('nonexistent@example.com', '1234')

        self.assertIn(constants.ERROR_INVALID_VERIFICATION_CODE, str(cm.exception))

    def test_verify_email_mismatched_code(self):
        """Test verifying email with code belonging to different user."""
        other_user = User.objects.create_user(
            email='other@example.com',
            name='Other User',
            password='testpass123'
        )
        token = VerificationToken.create_for_email_verification(other_user)

        with self.assertRaises(ValidationError) as cm:
            UserService.verify_email(self.user.email, token.token)

        self.assertIn(constants.ERROR_INVALID_VERIFICATION_CODE, str(cm.exception))

    def test_verify_email_already_verified(self):
        """Test verifying email for already verified user."""
        self.user.email_verified = True
        self.user.save()

        token = VerificationToken.create_for_email_verification(self.user)

        with self.assertRaises(ValidationError) as cm:
            UserService.verify_email(self.user.email, token.token)

        self.assertIn(constants.ERROR_EMAIL_ALREADY_VERIFIED, str(cm.exception))


class TokenServiceTest(TestCase):
    """Tests for TokenService."""

    def setUp(self):
        """Set up test user."""
        self.user = User.objects.create_user(
            email='test@example.com',
            name='Test User',
            password='testpass123'
        )

    def test_blacklist_token_success(self):
        """Test blacklisting a refresh token."""
        # Generate tokens
        tokens = UserService.generate_tokens(self.user)

        # Blacklist refresh token
        TokenService.blacklist_token(tokens['refresh'])

        # Verify token is blacklisted (would need actual token validation)
        # This is a basic test - full test would verify token can't be used

    def test_blacklist_invalid_token_fails(self):
        """Test blacklisting invalid token raises exception."""
        with self.assertRaises(Exception):
            TokenService.blacklist_token('invalid-token')
