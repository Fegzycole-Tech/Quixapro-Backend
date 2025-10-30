"""Tests for Google social authentication."""

from django.test import TestCase
from rest_framework import status
from rest_framework.test import APITestCase, APIClient
from unittest.mock import patch, Mock
from allauth.socialaccount.models import SocialApp
from django.contrib.sites.models import Site
from rest_framework.exceptions import AuthenticationFailed

from users.models import User
from users.services import UserService


class GoogleAuthViewTest(APITestCase):
    """Tests for Google OAuth authentication views."""

    def setUp(self):
        """Set up test client and Google social app."""
        self.client = APIClient()
        self.url = '/auth/google/'

        # Create site for allauth
        self.site = Site.objects.get_current()

        # Create Google social app
        self.social_app = SocialApp.objects.create(
            provider='google',
            name='Google',
            client_id='test-client-id',
            secret='test-secret'
        )
        self.social_app.sites.add(self.site)

    @patch('users.services.UserService.authenticate_with_google')
    def test_google_login_success(self, mock_authenticate):
        """Test successful Google OAuth login."""
        # Create a test user for the mock
        test_user = User.objects.create(
            email='test@gmail.com',
            name='Test User',
            email_verified=True
        )

        # Mock successful authentication
        mock_authenticate.return_value = {
            'user': test_user,
            'access_token': 'mock-jwt-access-token',
            'refresh_token': 'mock-jwt-refresh-token'
        }

        data = {'access_token': 'valid-google-access-token'}
        response = self.client.post(self.url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access_token', response.data)
        self.assertIn('refresh_token', response.data)
        self.assertIn('user', response.data)
        self.assertEqual(response.data['message'], 'Successfully authenticated with Google')
        self.assertEqual(response.data['user']['email'], 'test@gmail.com')

        # Verify service was called with correct token
        mock_authenticate.assert_called_once_with('valid-google-access-token')

        # Cleanup
        test_user.delete()

    def test_google_login_missing_access_token(self):
        """Test Google login without access token."""
        data = {}
        response = self.client.post(self.url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('detail', response.data)
        self.assertEqual(response.data['error_code'], 'VALIDATION_ERROR')

    @patch('users.services.UserService.authenticate_with_google')
    def test_google_login_invalid_token(self, mock_authenticate):
        """Test Google login with invalid token."""
        mock_authenticate.side_effect = AuthenticationFailed('Invalid token')

        data = {'access_token': 'invalid-token'}
        response = self.client.post(self.url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.data['error_code'], 'INVALID_GOOGLE_TOKEN')

    @patch('users.services.UserService.authenticate_with_google')
    def test_google_login_unexpected_error(self, mock_authenticate):
        """Test Google login handles unexpected errors."""
        mock_authenticate.side_effect = Exception('Unexpected error')

        data = {'access_token': 'some-token'}
        response = self.client.post(self.url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertEqual(response.data['error_code'], 'GOOGLE_AUTH_ERROR')


class GoogleAdapterTest(TestCase):
    """Tests for Google OAuth adapters."""

    def setUp(self):
        """Set up test data."""
        self.user_data = {
            'email': 'test@gmail.com',
            'name': 'Test User'
        }

    def test_populate_user_from_google(self):
        """Test populating user from Google data."""
        from users.adapters import CustomSocialAccountAdapter
        from allauth.socialaccount.models import SocialLogin

        adapter = CustomSocialAccountAdapter()

        # Mock sociallogin object with proper nested attributes
        mock_account = Mock()
        mock_account.provider = 'google'
        mock_account.extra_data = {
            'email': 'test@gmail.com',
            'name': 'Test User',
            'picture': 'https://example.com/photo.jpg'
        }

        sociallogin = Mock(spec=SocialLogin)
        sociallogin.account = mock_account

        # Mock request
        request = Mock()

        # Create a user instance
        user = User(email='', name='')

        # Mock the parent populate_user to return our user
        with patch('allauth.socialaccount.adapter.DefaultSocialAccountAdapter.populate_user', return_value=user):
            result = adapter.populate_user(request, sociallogin, self.user_data)

            self.assertEqual(result.email, 'test@gmail.com')
            self.assertEqual(result.name, 'Test User')
            self.assertEqual(result.photo_url, 'https://example.com/photo.jpg')
            self.assertTrue(result.email_verified)

    def test_pre_social_login_connects_existing_user(self):
        """Test that Google account connects to existing user with same email."""
        from users.adapters import CustomSocialAccountAdapter
        from allauth.socialaccount.models import SocialLogin

        # Create existing user
        existing_user = User.objects.create_user(
            email='existing@gmail.com',
            name='Existing User',
            password='testpass123'
        )

        adapter = CustomSocialAccountAdapter()

        # Mock sociallogin object with proper nested attributes
        mock_account = Mock()
        mock_account.extra_data = {
            'email': 'existing@gmail.com'
        }

        sociallogin = Mock(spec=SocialLogin)
        sociallogin.is_existing = False
        sociallogin.account = mock_account
        sociallogin.connect = Mock()

        # Mock request
        request = Mock()

        adapter.pre_social_login(request, sociallogin)

        # Verify connect was called with existing user
        sociallogin.connect.assert_called_once_with(request, existing_user)

    def test_pre_social_login_no_existing_user(self):
        """Test pre_social_login when user doesn't exist."""
        from users.adapters import CustomSocialAccountAdapter
        from allauth.socialaccount.models import SocialLogin

        adapter = CustomSocialAccountAdapter()

        # Mock sociallogin object with proper nested attributes
        mock_account = Mock()
        mock_account.extra_data = {
            'email': 'newuser@gmail.com'
        }

        sociallogin = Mock(spec=SocialLogin)
        sociallogin.is_existing = False
        sociallogin.account = mock_account
        sociallogin.connect = Mock()

        # Mock request
        request = Mock()

        # Should not raise exception
        adapter.pre_social_login(request, sociallogin)

        # Connect should not be called
        sociallogin.connect.assert_not_called()

    def test_pre_social_login_handles_missing_email(self):
        """Test pre_social_login handles missing email gracefully."""
        from users.adapters import CustomSocialAccountAdapter
        from allauth.socialaccount.models import SocialLogin

        adapter = CustomSocialAccountAdapter()

        # Mock sociallogin object without email
        mock_account = Mock()
        mock_account.extra_data = {}

        sociallogin = Mock(spec=SocialLogin)
        sociallogin.is_existing = False
        sociallogin.account = mock_account
        sociallogin.connect = Mock()

        # Mock request
        request = Mock()

        # Should not raise exception
        adapter.pre_social_login(request, sociallogin)

        # Connect should not be called
        sociallogin.connect.assert_not_called()

    def test_save_user_handles_errors(self):
        """Test save_user handles errors gracefully."""
        from users.adapters import CustomAccountAdapter
        from django.core.exceptions import ValidationError

        adapter = CustomAccountAdapter()

        # Mock request, user, and form
        request = Mock()
        user = Mock()
        user.save.side_effect = Exception('Database error')
        form = Mock()

        # Mock parent save_user
        with patch('users.adapters.DefaultAccountAdapter.save_user', return_value=user):
            with self.assertRaises(ValidationError) as context:
                adapter.save_user(request, user, form, commit=True)

            self.assertIn('Failed to save user', str(context.exception))


class GoogleAuthIntegrationTest(APITestCase):
    """Integration tests for Google authentication flow."""

    def setUp(self):
        """Set up test environment."""
        self.client = APIClient()
        self.url = '/api/users/auth/google/'

        # Create site for allauth
        self.site = Site.objects.get_current()

        # Create Google social app
        self.social_app = SocialApp.objects.create(
            provider='google',
            name='Google',
            client_id='test-client-id',
            secret='test-secret'
        )
        self.social_app.sites.add(self.site)

    @patch('users.services.requests.get')
    def test_full_google_auth_flow_new_user(self, mock_get):
        """Test complete Google auth flow for new user."""
        # Mock Google API response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'email': 'newgoogleuser@gmail.com',
            'verified_email': True,
            'given_name': 'New',
            'family_name': 'User',
            'picture': 'https://lh3.googleusercontent.com/photo.jpg'
        }
        mock_get.return_value = mock_response

        data = {'access_token': 'valid-google-token'}
        response = self.client.post('/auth/google/', data, format='json')

        # Verify response
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access_token', response.data)
        self.assertIn('refresh_token', response.data)
        self.assertIn('user', response.data)
        self.assertEqual(response.data['message'], 'Successfully authenticated with Google')

        # Verify user was created
        user = User.objects.get(email='newgoogleuser@gmail.com')
        self.assertEqual(user.name, 'New User')
        self.assertTrue(user.email_verified)
        self.assertFalse(user.has_usable_password())
        self.assertEqual(user.photo_url, 'https://lh3.googleusercontent.com/photo.jpg')

        # Cleanup
        user.delete()


class GoogleServiceTest(TestCase):
    """Tests for Google OAuth service methods."""

    @patch('users.services.requests.get')
    def test_authenticate_with_google_new_user(self, mock_get):
        """Test authenticating a new user with Google."""
        # Mock Google API response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'email': 'newuser@gmail.com',
            'verified_email': True,
            'given_name': 'New',
            'family_name': 'User',
            'picture': 'https://example.com/photo.jpg'
        }
        mock_get.return_value = mock_response

        result = UserService.authenticate_with_google('valid-token')

        # Verify user was created
        self.assertIsNotNone(result['user'])
        self.assertEqual(result['user'].email, 'newuser@gmail.com')
        self.assertEqual(result['user'].name, 'New User')
        self.assertTrue(result['user'].email_verified)
        self.assertFalse(result['user'].has_usable_password())
        self.assertEqual(result['user'].photo_url, 'https://example.com/photo.jpg')

        # Verify tokens were generated
        self.assertIsNotNone(result['access_token'])
        self.assertIsNotNone(result['refresh_token'])

        # Cleanup
        result['user'].delete()

    @patch('users.services.requests.get')
    def test_authenticate_with_google_existing_user(self, mock_get):
        """Test authenticating an existing user with Google."""
        # Create existing user
        existing_user = User.objects.create(
            email='existing@gmail.com',
            name='Existing User',
            email_verified=True
        )

        # Mock Google API response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'email': 'existing@gmail.com',
            'verified_email': True,
            'given_name': 'Existing',
            'family_name': 'User',
        }
        mock_get.return_value = mock_response

        result = UserService.authenticate_with_google('valid-token')

        # Verify same user was returned (not created)
        self.assertEqual(result['user'].id, existing_user.id)
        self.assertEqual(result['user'].email, 'existing@gmail.com')

        # Verify no duplicate was created
        user_count = User.objects.filter(email='existing@gmail.com').count()
        self.assertEqual(user_count, 1)

        # Verify tokens were generated
        self.assertIsNotNone(result['access_token'])
        self.assertIsNotNone(result['refresh_token'])

        # Cleanup
        existing_user.delete()

    @patch('users.services.requests.get')
    def test_authenticate_with_google_invalid_token(self, mock_get):
        """Test authentication with invalid Google token."""
        # Mock Google API error response
        mock_response = Mock()
        mock_response.status_code = 401
        mock_response.text = 'Invalid token'
        mock_get.return_value = mock_response

        with self.assertRaises(AuthenticationFailed) as context:
            UserService.authenticate_with_google('invalid-token')

        self.assertIn('Invalid access token', str(context.exception))

    @patch('users.services.requests.get')
    def test_authenticate_with_google_unverified_email(self, mock_get):
        """Test authentication with unverified Google email."""
        # Mock Google API response with unverified email
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'email': 'unverified@gmail.com',
            'verified_email': False,
            'given_name': 'Test',
            'family_name': 'User',
        }
        mock_get.return_value = mock_response

        with self.assertRaises(AuthenticationFailed) as context:
            UserService.authenticate_with_google('some-token')

        self.assertIn('Email not verified', str(context.exception))

    @patch('users.services.requests.get')
    def test_authenticate_with_google_missing_email(self, mock_get):
        """Test authentication with missing email from Google."""
        # Mock Google API response without email
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'given_name': 'Test',
            'family_name': 'User',
        }
        mock_get.return_value = mock_response

        with self.assertRaises(AuthenticationFailed) as context:
            UserService.authenticate_with_google('some-token')

        self.assertIn('Email not provided', str(context.exception))

    @patch('users.services.requests.get')
    def test_authenticate_with_google_request_exception(self, mock_get):
        """Test authentication when Google API request fails."""
        import requests
        mock_get.side_effect = requests.RequestException('Network error')

        with self.assertRaises(AuthenticationFailed) as context:
            UserService.authenticate_with_google('some-token')

        self.assertIn('Failed to verify access token', str(context.exception))
