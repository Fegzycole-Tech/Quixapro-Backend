"""Tests for user views and API endpoints."""

from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase, APIClient
from unittest.mock import patch, MagicMock

from users.models import User, VerificationToken
from users.services import UserService
from users import constants


class RegisterViewTest(APITestCase):
    """Tests for RegisterView."""

    def setUp(self):
        """Set up test client."""
        self.url = reverse('auth:register')
        self.client = APIClient()

    @patch('users.services.EmailService')
    def test_register_with_password_success(self, mock_email_service):
        """Test successful registration with password."""
        mock_instance = MagicMock()
        mock_email_service.return_value = mock_instance

        data = {
            'email': 'newuser@example.com',
            'name': 'New User',
            'password': 'SecurePass123!'
        }

        response = self.client.post(self.url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('user', response.data)
        self.assertNotIn('tokens', response.data)  # Tokens not returned on registration
        self.assertIn('message', response.data)
        self.assertEqual(response.data['message'], constants.SUCCESS_VERIFICATION_EMAIL_SENT)

        # Verify user was created
        user = User.objects.get(email='newuser@example.com')
        self.assertEqual(user.name, 'New User')
        self.assertTrue(user.has_usable_password())

        # Verify email was sent
        mock_instance.send_verification_email.assert_called_once()

    @patch('users.services.EmailService')
    def test_register_without_password_success(self, mock_email_service):
        """Test successful registration without password (social auth)."""
        mock_instance = MagicMock()
        mock_email_service.return_value = mock_instance

        data = {
            'email': 'social@example.com',
            'name': 'Social User'
        }

        response = self.client.post(self.url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Verify user was created
        user = User.objects.get(email='social@example.com')
        self.assertFalse(user.has_usable_password())



class LoginViewTest(APITestCase):
    """Tests for LoginView."""

    def setUp(self):
        """Set up test user and client."""
        self.url = reverse('auth:login')
        self.client = APIClient()
        self.user = User.objects.create_user(
            email='test@example.com',
            name='Test User',
            password='testpass123'
        )

    def test_login_success(self):
        """Test successful login."""
        data = {
            'email': 'test@example.com',
            'password': 'testpass123'
        }

        response = self.client.post(self.url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
        self.assertIn('user', response.data)

    def test_login_invalid_credentials_fails(self):
        """Test login with invalid credentials fails."""
        data = {
            'email': 'test@example.com',
            'password': 'wrongpassword'
        }

        response = self.client.post(self.url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_login_social_auth_user_fails(self):
        """Test login with social auth user fails."""
        social_user = User.objects.create_user(
            email='social@example.com',
            name='Social User'
        )

        data = {
            'email': 'social@example.com',
            'password': 'anypassword'
        }

        response = self.client.post(self.url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('detail', response.data)


class LogoutViewTest(APITestCase):
    """Tests for LogoutView."""

    def setUp(self):
        """Set up test user and authentication."""
        self.url = reverse('auth:logout')
        self.client = APIClient()
        self.user = User.objects.create_user(
            email='test@example.com',
            name='Test User',
            password='testpass123'
        )
        self.tokens = UserService.generate_tokens(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.tokens["access"]}')

    def test_logout_success(self):
        """Test successful logout."""
        data = {'refresh_token': self.tokens['refresh']}

        response = self.client.post(self.url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['message'], constants.SUCCESS_LOGGED_OUT)

    def test_logout_without_authentication_fails(self):
        """Test logout without authentication fails."""
        self.client.credentials()  # Remove authentication
        data = {'refresh_token': self.tokens['refresh']}

        response = self.client.post(self.url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class UserProfileViewTest(APITestCase):
    """Tests for UserProfileView."""

    def setUp(self):
        """Set up test user and authentication."""
        self.url = reverse('users:profile')
        self.client = APIClient()
        self.user = User.objects.create_user(
            email='test@example.com',
            name='Test User',
            password='testpass123'
        )
        self.tokens = UserService.generate_tokens(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.tokens["access"]}')

    def test_get_profile_success(self):
        """Test getting user profile."""
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['email'], 'test@example.com')
        self.assertEqual(response.data['name'], 'Test User')

    def test_get_profile_without_authentication_fails(self):
        """Test getting profile without authentication fails."""
        self.client.credentials()  # Remove authentication

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class UpdateProfileViewTest(APITestCase):
    """Tests for UpdateProfileView."""

    def setUp(self):
        """Set up test user and authentication."""
        self.url = reverse('users:profile_update')
        self.client = APIClient()
        self.user = User.objects.create_user(
            email='test@example.com',
            name='Test User',
            password='testpass123'
        )
        self.tokens = UserService.generate_tokens(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.tokens["access"]}')

    def test_update_name_success(self):
        """Test updating user name."""
        data = {'name': 'Updated Name'}

        response = self.client.patch(self.url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Updated Name')

        # Verify in database
        self.user.refresh_from_db()
        self.assertEqual(self.user.name, 'Updated Name')

    def test_update_email_to_available_email_success(self):
        """Test updating to available email."""
        data = {'email': 'newemail@example.com'}

        response = self.client.patch(self.url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['email'], 'newemail@example.com')

    def test_update_email_to_taken_email_fails(self):
        """Test updating to taken email fails."""
        # Create another user
        User.objects.create_user(
            email='taken@example.com',
            name='Other User',
            password='testpass123'
        )

        data = {'email': 'taken@example.com'}

        response = self.client.patch(self.url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class ChangePasswordViewTest(APITestCase):
    """Tests for ChangePasswordView."""

    def setUp(self):
        """Set up test user and authentication."""
        self.url = reverse('users:change_password')
        self.client = APIClient()
        self.user = User.objects.create_user(
            email='test@example.com',
            name='Test User',
            password='oldpass123'
        )
        self.tokens = UserService.generate_tokens(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.tokens["access"]}')

    def test_change_password_success(self):
        """Test successful password change."""
        data = {
            'old_password': 'oldpass123',
            'new_password': 'NewSecurePass123!',
            'new_password_confirm': 'NewSecurePass123!'
        }

        response = self.client.post(self.url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['message'], constants.SUCCESS_PASSWORD_CHANGED)

        # Verify password was changed
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('NewSecurePass123!'))

    def test_change_password_wrong_old_password_fails(self):
        """Test changing password with wrong old password fails."""
        data = {
            'old_password': 'wrongpass',
            'new_password': 'NewSecurePass123!',
            'new_password_confirm': 'NewSecurePass123!'
        }

        response = self.client.post(self.url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_change_password_social_auth_user_fails(self):
        """Test social auth user cannot change password."""
        social_user = User.objects.create_user(
            email='social@example.com',
            name='Social User'
        )
        tokens = UserService.generate_tokens(social_user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {tokens["access"]}')

        data = {
            'old_password': 'anypass',
            'new_password': 'NewSecurePass123!',
            'new_password_confirm': 'NewSecurePass123!'
        }

        response = self.client.post(self.url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class ForgotPasswordViewTest(APITestCase):
    """Tests for ForgotPasswordView."""

    def setUp(self):
        """Set up test user."""
        self.url = reverse('auth:forgot_password')
        self.client = APIClient()
        self.user = User.objects.create_user(
            email='test@example.com',
            name='Test User',
            password='testpass123'
        )

    @patch('users.services.EmailService')
    def test_forgot_password_success(self, mock_email_service):
        """Test successful password reset request."""
        mock_instance = MagicMock()
        mock_email_service.return_value = mock_instance

        data = {'email': 'test@example.com'}

        response = self.client.post(self.url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['message'], constants.SUCCESS_PASSWORD_RESET_EMAIL_SENT)

        # Verify token was created
        token = VerificationToken.objects.filter(
            user=self.user,
            token_type=VerificationToken.TOKEN_TYPE_PASSWORD_RESET
        ).first()
        self.assertIsNotNone(token)

        # Verify email was sent
        mock_instance.send_password_reset_email.assert_called_once()

    def test_forgot_password_nonexistent_user_fails(self):
        """Test password reset for nonexistent user fails."""
        data = {'email': 'nonexistent@example.com'}

        response = self.client.post(self.url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @patch('users.services.EmailService')
    def test_forgot_password_social_auth_user_fails(self, mock_email_service):
        """Test password reset for social auth user fails."""
        social_user = User.objects.create_user(
            email='social@example.com',
            name='Social User'
        )

        data = {'email': 'social@example.com'}

        response = self.client.post(self.url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class ResetPasswordViewTest(APITestCase):
    """Tests for ResetPasswordView."""

    def setUp(self):
        """Set up test user and reset token."""
        self.url = reverse('auth:reset_password')
        self.client = APIClient()
        self.user = User.objects.create_user(
            email='test@example.com',
            name='Test User',
            password='oldpass123'
        )
        self.reset_token = VerificationToken.create_for_password_reset(self.user)

    def test_reset_password_success(self):
        """Test successful password reset."""
        data = {
            'email': self.user.email,
            'token': self.reset_token.token,
            'new_password': 'NewSecurePass123!'
        }

        response = self.client.post(self.url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['message'], constants.SUCCESS_PASSWORD_RESET)

        # Verify password was reset
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('NewSecurePass123!'))

        # Verify token was marked as used
        self.reset_token.refresh_from_db()
        self.assertTrue(self.reset_token.is_used)

    def test_reset_password_invalid_token_fails(self):
        """Test password reset with invalid token fails."""
        data = {
            'email': self.user.email,
            'token': 'invalid-token',
            'new_password': 'NewSecurePass123!'
        }

        response = self.client.post(self.url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_reset_password_email_token_mismatch_fails(self):
        """Test password reset with email/token mismatch fails."""
        # Create another user
        other_user = User.objects.create_user(
            email='other@example.com',
            name='Other User',
            password='password123'
        )

        data = {
            'email': other_user.email,
            'token': self.reset_token.token,  # Token belongs to self.user
            'new_password': 'NewSecurePass123!'
        }

        response = self.client.post(self.url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class VerifyEmailViewTest(APITestCase):
    """Tests for VerifyEmailView."""

    def setUp(self):
        """Set up test user and verification token."""
        self.url = reverse('auth:verify_email')
        self.client = APIClient()
        self.user = User.objects.create_user(
            email='test@example.com',
            name='Test User',
            password='testpass123'
        )
        self.verification_token = VerificationToken.create_for_email_verification(self.user)

    def test_verify_email_success(self):
        """Test successful email verification without authentication."""
        data = {
            'email': 'test@example.com',
            'code': self.verification_token.token
        }

        response = self.client.post(self.url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['message'], constants.SUCCESS_EMAIL_VERIFIED)

        # Verify response contains user data and tokens
        self.assertIn('user', response.data)
        self.assertIn('tokens', response.data)
        self.assertEqual(response.data['user']['email'], 'test@example.com')
        self.assertIn('access', response.data['tokens'])
        self.assertIn('refresh', response.data['tokens'])

        # Verify email was marked as verified
        self.user.refresh_from_db()
        self.assertTrue(self.user.email_verified)

        # Verify token was marked as used
        self.verification_token.refresh_from_db()
        self.assertTrue(self.verification_token.is_used)

    def test_verify_email_invalid_code_fails(self):
        """Test email verification with invalid code fails."""
        data = {
            'email': 'test@example.com',
            'code': '9999'
        }

        response = self.client.post(self.url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # Verify email was not marked as verified
        self.user.refresh_from_db()
        self.assertFalse(self.user.email_verified)

    def test_verify_email_invalid_email_fails(self):
        """Test email verification with non-existent email fails."""
        data = {
            'email': 'nonexistent@example.com',
            'code': '1234'
        }

        response = self.client.post(self.url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_verify_email_mismatched_code_fails(self):
        """Test verification fails when code doesn't match email."""
        other_user = User.objects.create_user(
            email='other@example.com',
            name='Other User',
            password='testpass123'
        )
        other_token = VerificationToken.create_for_email_verification(other_user)

        data = {
            'email': 'test@example.com',
            'code': other_token.token
        }

        response = self.client.post(self.url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # Verify email was not marked as verified
        self.user.refresh_from_db()
        self.assertFalse(self.user.email_verified)

    def test_verify_email_already_verified_fails(self):
        """Test verification fails for already verified user."""
        self.user.email_verified = True
        self.user.save()

        data = {
            'email': 'test@example.com',
            'code': self.verification_token.token
        }
        response = self.client.post(self.url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('detail', response.data)


class ResendVerificationViewTest(APITestCase):
    """Tests for ResendVerificationView."""

    def setUp(self):
        """Set up test user."""
        self.url = reverse('auth:resend_verification')
        self.client = APIClient()
        self.user = User.objects.create_user(
            email='test@example.com',
            name='Test User',
            password='testpass123'
        )

    @patch('users.services.EmailService')
    def test_resend_verification_success(self, mock_email_service):
        """Test successful verification code resend without authentication."""
        mock_instance = MagicMock()
        mock_email_service.return_value = mock_instance

        data = {'email': 'test@example.com'}
        response = self.client.post(self.url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['message'], constants.SUCCESS_VERIFICATION_CODE_RESENT)

        # Verify email was sent
        mock_instance.send_verification_email.assert_called_once()

    @patch('users.services.EmailService')
    def test_resend_verification_already_verified_fails(self, mock_email_service):
        """Test resending verification for already verified user fails."""
        self.user.email_verified = True
        self.user.save()

        data = {'email': 'test@example.com'}
        response = self.client.post(self.url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_resend_verification_nonexistent_user_fails(self):
        """Test resending verification for non-existent user returns error."""
        data = {'email': 'nonexistent@example.com'}
        response = self.client.post(self.url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn('detail', response.data)
        self.assertEqual(response.data['error_code'], 'USER_NOT_FOUND')


class UserListViewTest(APITestCase):
    """Tests for UserListView."""

    def setUp(self):
        """Set up test users."""
        self.url = reverse('users:user_list')
        self.client = APIClient()
        self.user = User.objects.create_user(
            email='test@example.com',
            name='Test User',
            password='testpass123'
        )
        User.objects.create_user(
            email='other@example.com',
            name='Other User',
            password='testpass123'
        )
        self.tokens = UserService.generate_tokens(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.tokens["access"]}')

    def test_list_users_success(self):
        """Test listing all users."""
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Handle both paginated and non-paginated responses
        if isinstance(response.data, dict) and 'results' in response.data:
            users = response.data['results']
        else:
            users = response.data

        self.assertGreaterEqual(len(users), 2)

        # Verify our test users are in the response
        emails = [user['email'] for user in users]
        self.assertIn('test@example.com', emails)
        self.assertIn('other@example.com', emails)


class UserDetailViewTest(APITestCase):
    """Tests for UserDetailView."""

    def setUp(self):
        """Set up test users."""
        self.client = APIClient()
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
        self.tokens = UserService.generate_tokens(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.tokens["access"]}')

    def test_get_user_detail_success(self):
        """Test getting user detail by ID."""
        url = reverse('users:user_detail', kwargs={'pk': self.other_user.pk})

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['email'], 'other@example.com')
        self.assertEqual(response.data['name'], 'Other User')
