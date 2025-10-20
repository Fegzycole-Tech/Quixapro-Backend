"""Tests for user models."""

from django.test import TestCase
from django.utils import timezone
from datetime import timedelta
from users.models import User, VerificationToken


class UserModelTest(TestCase):
    """Tests for User model."""

    def test_create_user_with_password(self):
        """Test creating a user with password."""
        user = User.objects.create_user(
            email='test@example.com',
            name='Test User',
            password='testpass123'
        )
        self.assertEqual(user.email, 'test@example.com')
        self.assertEqual(user.name, 'Test User')
        self.assertTrue(user.has_usable_password())
        self.assertTrue(user.check_password('testpass123'))
        self.assertFalse(user.email_verified)
        self.assertTrue(user.is_active)
        self.assertFalse(user.is_staff)

    def test_create_user_without_password(self):
        """Test creating a user without password (social auth)."""
        user = User.objects.create_user(
            email='social@example.com',
            name='Social User'
        )
        self.assertEqual(user.email, 'social@example.com')
        self.assertFalse(user.has_usable_password())

    def test_create_superuser(self):
        """Test creating a superuser."""
        user = User.objects.create_superuser(
            email='admin@example.com',
            name='Admin User',
            password='adminpass123'
        )
        self.assertTrue(user.is_staff)
        self.assertTrue(user.is_superuser)
        self.assertTrue(user.has_usable_password())

    def test_email_normalization(self):
        """Test email is normalized."""
        user = User.objects.create_user(
            email='Test@EXAMPLE.com',
            name='Test User',
            password='testpass123'
        )
        self.assertEqual(user.email, 'Test@example.com')

    def test_user_string_representation(self):
        """Test user string representation."""
        user = User.objects.create_user(
            email='test@example.com',
            name='Test User',
            password='testpass123'
        )
        self.assertEqual(str(user), 'test@example.com')


class VerificationTokenModelTest(TestCase):
    """Tests for VerificationToken model."""

    def setUp(self):
        """Set up test user."""
        self.user = User.objects.create_user(
            email='test@example.com',
            name='Test User',
            password='testpass123'
        )

    def test_create_email_verification_token(self):
        """Test creating email verification token."""
        token = VerificationToken.create_for_email_verification(self.user)

        self.assertEqual(token.user, self.user)
        self.assertEqual(token.token_type, VerificationToken.TOKEN_TYPE_EMAIL)
        self.assertEqual(len(token.token), 4)
        self.assertTrue(token.token.isdigit())
        self.assertFalse(token.is_used)
        self.assertTrue(token.is_valid())

    def test_create_password_reset_token(self):
        """Test creating password reset token."""
        token = VerificationToken.create_for_password_reset(self.user)

        self.assertEqual(token.user, self.user)
        self.assertEqual(token.token_type, VerificationToken.TOKEN_TYPE_PASSWORD_RESET)
        self.assertTrue(len(token.token) > 20)
        self.assertFalse(token.is_used)
        self.assertTrue(token.is_valid())

    def test_token_expiration(self):
        """Test token expiration."""
        token = VerificationToken.create_for_email_verification(self.user)

        # Token should be valid initially
        self.assertTrue(token.is_valid())

        # Make token expired
        token.expires_at = timezone.now() - timedelta(minutes=1)
        token.save()

        # Token should now be invalid
        self.assertFalse(token.is_valid())

    def test_token_usage(self):
        """Test token can only be used once."""
        token = VerificationToken.create_for_email_verification(self.user)

        # Token should be valid initially
        self.assertTrue(token.is_valid())

        # Mark as used
        token.is_used = True
        token.save()

        # Token should now be invalid
        self.assertFalse(token.is_valid())

    def test_token_string_representation(self):
        """Test token string representation."""
        token = VerificationToken.create_for_email_verification(self.user)
        self.assertIn('Email Verification', str(token))
        self.assertIn(self.user.email, str(token))

    def test_numeric_code_generation(self):
        """Test numeric code is 4 digits."""
        for _ in range(10):  # Test multiple times
            code = VerificationToken.generate_numeric_code()
            self.assertEqual(len(code), 4)
            self.assertTrue(code.isdigit())
            self.assertGreaterEqual(int(code), 1000)
            self.assertLessEqual(int(code), 9999)

    def test_secure_token_generation(self):
        """Test secure token generation."""
        token1 = VerificationToken.generate_secure_token()
        token2 = VerificationToken.generate_secure_token()

        # Tokens should be different
        self.assertNotEqual(token1, token2)
        # Tokens should be long enough
        self.assertGreater(len(token1), 20)
        self.assertGreater(len(token2), 20)
