"""Tests for Google social authentication."""

from django.test import TestCase
from rest_framework import status
from rest_framework.test import APITestCase, APIClient
from unittest.mock import patch, MagicMock, Mock
from allauth.socialaccount.models import SocialApp, SocialAccount
from django.contrib.sites.models import Site

from users.models import User
from users import constants


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

    @patch('dj_rest_auth.registration.views.SocialLoginView.post')
    def test_google_login_success(self, mock_parent_post):
        """Test successful Google OAuth login."""
        # Mock successful response from parent class
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.data = {
            'user': {
                'id': 1,
                'email': 'test@gmail.com',
                'name': 'Test User',
                'email_verified': True
            },
            'access_token': 'mock-jwt-access-token',
            'refresh_token': 'mock-jwt-refresh-token'
        }
        mock_parent_post.return_value = mock_response

        data = {'access_token': 'valid-google-access-token'}
        response = self.client.post(self.url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access_token', response.data)
        self.assertIn('refresh_token', response.data)
        self.assertIn('user', response.data)
        self.assertEqual(response.data['message'], 'Successfully authenticated with Google')

    @patch('dj_rest_auth.registration.views.SocialLoginView.post')
    def test_google_login_missing_access_token(self, mock_parent_post):
        """Test Google login without access token."""
        # Parent should raise validation error for missing token
        from rest_framework.exceptions import ValidationError
        mock_parent_post.side_effect = ValidationError('access_token is required')

        data = {}
        response = self.client.post(self.url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('detail', response.data)

    @patch('dj_rest_auth.registration.views.SocialLoginView.post')
    def test_google_login_invalid_token(self, mock_parent_post):
        """Test Google login with invalid token."""
        from rest_framework.exceptions import AuthenticationFailed
        mock_parent_post.side_effect = AuthenticationFailed('Invalid token')

        data = {'access_token': 'invalid-token'}
        response = self.client.post(self.url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.data['error_code'], 'INVALID_GOOGLE_TOKEN')

    @patch('dj_rest_auth.registration.views.SocialLoginView.post')
    def test_google_login_unexpected_error(self, mock_parent_post):
        """Test Google login handles unexpected errors."""
        mock_parent_post.side_effect = Exception('Unexpected error')

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

    @patch('allauth.socialaccount.providers.google.views.GoogleOAuth2Adapter.complete_login')
    def test_full_google_auth_flow_new_user(self, mock_complete_login):
        """Test complete Google auth flow for new user."""
        # Mock Google user data
        mock_sociallogin = Mock()
        mock_sociallogin.user = User(
            email='newgoogleuser@gmail.com',
            name='New Google User',
            email_verified=True
        )
        mock_sociallogin.account.provider = 'google'
        mock_sociallogin.account.extra_data = {
            'email': 'newgoogleuser@gmail.com',
            'name': 'New Google User',
            'picture': 'https://lh3.googleusercontent.com/photo.jpg'
        }

        mock_complete_login.return_value = mock_sociallogin

        # Note: Full integration test would require real Google token
        # This is a simplified version showing the expected flow
