"""Tests for user serializers."""

from django.test import TestCase, RequestFactory
from rest_framework.exceptions import ValidationError
from users.models import User
from users.serializers import (
    UserSerializer,
    RegisterSerializer,
    UpdateUserSerializer,
    ChangePasswordSerializer,
    ForgotPasswordSerializer,
    ResetPasswordSerializer,
    VerifyEmailSerializer,
    ResendVerificationSerializer
)
from users import constants


class UserSerializerTest(TestCase):
    """Tests for UserSerializer."""

    def setUp(self):
        """Set up test user."""
        self.user = User.objects.create_user(
            email='test@example.com',
            name='Test User',
            password='testpass123'
        )

    def test_serializer_fields(self):
        """Test serializer contains expected fields."""
        serializer = UserSerializer(self.user)
        data = serializer.data

        self.assertIn('id', data)
        self.assertIn('email', data)
        self.assertIn('name', data)
        self.assertIn('photo_url', data)
        self.assertIn('email_verified', data)
        self.assertIn('created_at', data)
        self.assertIn('updated_at', data)

    def test_serializer_data(self):
        """Test serializer returns correct data."""
        serializer = UserSerializer(self.user)
        data = serializer.data

        self.assertEqual(data['email'], 'test@example.com')
        self.assertEqual(data['name'], 'Test User')
        self.assertEqual(data['email_verified'], False)


class RegisterSerializerTest(TestCase):
    """Tests for RegisterSerializer."""

    def test_valid_registration_with_password(self):
        """Test valid registration with password."""
        data = {
            'email': 'new@example.com',
            'name': 'New User',
            'password': 'SecurePass123!'
        }
        serializer = RegisterSerializer(data=data)
        self.assertTrue(serializer.is_valid())

    def test_valid_registration_without_password(self):
        """Test valid registration without password (social auth)."""
        data = {
            'email': 'social@example.com',
            'name': 'Social User'
        }
        serializer = RegisterSerializer(data=data)
        self.assertTrue(serializer.is_valid())


    def test_invalid_email_fails(self):
        """Test invalid email format fails."""
        data = {
            'email': 'not-an-email',
            'name': 'New User',
            'password': 'SecurePass123!'
        }
        serializer = RegisterSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('email', serializer.errors)

    def test_weak_password_fails(self):
        """Test weak password fails validation."""
        data = {
            'email': 'new@example.com',
            'name': 'New User',
            'password': '123'
        }
        serializer = RegisterSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('password', serializer.errors)

    def test_create_user_with_password(self):
        """Test creating user with password."""
        data = {
            'email': 'new@example.com',
            'name': 'New User',
            'password': 'SecurePass123!'
        }
        serializer = RegisterSerializer(data=data)
        self.assertTrue(serializer.is_valid())

        user = serializer.save()
        self.assertEqual(user.email, 'new@example.com')
        self.assertEqual(user.name, 'New User')
        self.assertTrue(user.has_usable_password())


class UpdateUserSerializerTest(TestCase):
    """Tests for UpdateUserSerializer."""

    def setUp(self):
        """Set up test users."""
        self.user = User.objects.create_user(
            email='test@example.com',
            name='Test User',
            password='testpass123'
        )
        self.other_user = User.objects.create_user(
            email='other@example.com',
            name='Other User',
            password='testpass123'
        )
        self.factory = RequestFactory()

    def test_update_name(self):
        """Test updating user name."""
        data = {'name': 'Updated Name'}
        request = self.factory.post('/')
        request.user = self.user

        serializer = UpdateUserSerializer(
            instance=self.user,
            data=data,
            context={'request': request},
            partial=True
        )
        self.assertTrue(serializer.is_valid())

    def test_update_email_to_available_email(self):
        """Test updating to available email."""
        data = {'email': 'newemail@example.com'}
        request = self.factory.post('/')
        request.user = self.user

        serializer = UpdateUserSerializer(
            instance=self.user,
            data=data,
            context={'request': request},
            partial=True
        )
        self.assertTrue(serializer.is_valid())

    def test_update_email_to_taken_email_fails(self):
        """Test updating to already taken email fails."""
        data = {'email': 'other@example.com'}
        request = self.factory.post('/')
        request.user = self.user

        serializer = UpdateUserSerializer(
            instance=self.user,
            data=data,
            context={'request': request},
            partial=True
        )
        self.assertFalse(serializer.is_valid())
        self.assertIn('email', serializer.errors)

    def test_update_email_to_own_email(self):
        """Test updating to own email (should succeed)."""
        data = {'email': 'test@example.com'}
        request = self.factory.post('/')
        request.user = self.user

        serializer = UpdateUserSerializer(
            instance=self.user,
            data=data,
            context={'request': request},
            partial=True
        )
        self.assertTrue(serializer.is_valid())


class ChangePasswordSerializerTest(TestCase):
    """Tests for ChangePasswordSerializer."""

    def setUp(self):
        """Set up test user."""
        self.user = User.objects.create_user(
            email='test@example.com',
            name='Test User',
            password='oldpass123'
        )
        self.factory = RequestFactory()

    def test_valid_password_change(self):
        """Test valid password change."""
        data = {
            'old_password': 'oldpass123',
            'new_password': 'NewSecurePass123!',
            'new_password_confirm': 'NewSecurePass123!'
        }
        request = self.factory.post('/')
        request.user = self.user

        serializer = ChangePasswordSerializer(
            data=data,
            context={'request': request}
        )
        self.assertTrue(serializer.is_valid())

    def test_wrong_old_password_fails(self):
        """Test wrong old password fails."""
        data = {
            'old_password': 'wrongpass',
            'new_password': 'NewSecurePass123!',
            'new_password_confirm': 'NewSecurePass123!'
        }
        request = self.factory.post('/')
        request.user = self.user

        serializer = ChangePasswordSerializer(
            data=data,
            context={'request': request}
        )
        self.assertFalse(serializer.is_valid())
        self.assertIn('old_password', serializer.errors)

    def test_new_password_mismatch_fails(self):
        """Test new password mismatch fails."""
        data = {
            'old_password': 'oldpass123',
            'new_password': 'NewSecurePass123!',
            'new_password_confirm': 'DifferentPass123!'
        }
        request = self.factory.post('/')
        request.user = self.user

        serializer = ChangePasswordSerializer(
            data=data,
            context={'request': request}
        )
        self.assertFalse(serializer.is_valid())
        self.assertIn('new_password', serializer.errors)

    def test_weak_new_password_fails(self):
        """Test weak new password fails validation."""
        data = {
            'old_password': 'oldpass123',
            'new_password': '123',
            'new_password_confirm': '123'
        }
        request = self.factory.post('/')
        request.user = self.user

        serializer = ChangePasswordSerializer(
            data=data,
            context={'request': request}
        )
        self.assertFalse(serializer.is_valid())
        self.assertIn('new_password', serializer.errors)


class ForgotPasswordSerializerTest(TestCase):
    """Tests for ForgotPasswordSerializer."""

    def test_valid_email(self):
        """Test valid email."""
        data = {'email': 'test@example.com'}
        serializer = ForgotPasswordSerializer(data=data)
        self.assertTrue(serializer.is_valid())

    def test_invalid_email_format_fails(self):
        """Test invalid email format fails."""
        data = {'email': 'not-an-email'}
        serializer = ForgotPasswordSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('email', serializer.errors)


class ResetPasswordSerializerTest(TestCase):
    """Tests for ResetPasswordSerializer."""

    def test_valid_reset_password(self):
        """Test valid password reset."""
        data = {
            'token': 'some-valid-token',
            'new_password': 'NewSecurePass123!',
            'new_password_confirm': 'NewSecurePass123!'
        }
        serializer = ResetPasswordSerializer(data=data)
        self.assertTrue(serializer.is_valid())

    def test_password_mismatch_fails(self):
        """Test password mismatch fails."""
        data = {
            'token': 'some-valid-token',
            'new_password': 'NewSecurePass123!',
            'new_password_confirm': 'DifferentPass123!'
        }
        serializer = ResetPasswordSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('new_password', serializer.errors)

    def test_weak_password_fails(self):
        """Test weak password fails validation."""
        data = {
            'token': 'some-valid-token',
            'new_password': '123',
            'new_password_confirm': '123'
        }
        serializer = ResetPasswordSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('new_password', serializer.errors)


class VerifyEmailSerializerTest(TestCase):
    """Tests for VerifyEmailSerializer."""

    def test_valid_4_digit_code(self):
        """Test valid 4-digit code."""
        data = {'code': '1234'}
        serializer = VerifyEmailSerializer(data=data)
        self.assertTrue(serializer.is_valid())

    def test_non_numeric_code_fails(self):
        """Test non-numeric code fails."""
        data = {'code': 'abcd'}
        serializer = VerifyEmailSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('code', serializer.errors)

    def test_too_short_code_fails(self):
        """Test code shorter than 4 digits fails."""
        data = {'code': '123'}
        serializer = VerifyEmailSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('code', serializer.errors)

    def test_too_long_code_fails(self):
        """Test code longer than 4 digits fails."""
        data = {'code': '12345'}
        serializer = VerifyEmailSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('code', serializer.errors)


class ResendVerificationSerializerTest(TestCase):
    """Tests for ResendVerificationSerializer."""

    def test_valid_empty_serializer(self):
        """Test serializer is valid with no data."""
        serializer = ResendVerificationSerializer(data={})
        self.assertTrue(serializer.is_valid())
