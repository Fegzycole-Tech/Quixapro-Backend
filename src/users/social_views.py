"""Views for social authentication."""

import logging
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from drf_spectacular.utils import extend_schema
from allauth.socialaccount.providers.google.views import GoogleOAuth2Adapter
from allauth.socialaccount.providers.oauth2.client import OAuth2Client
from dj_rest_auth.registration.views import SocialLoginView
from django.conf import settings
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework.exceptions import AuthenticationFailed, ValidationError

from .serializers import GoogleAuthSerializer
from common.responses import (
    success_response,
    error_response,
    internal_server_error_response
)

logger = logging.getLogger(__name__)


class GoogleLoginView(SocialLoginView):
    """
    Google OAuth2 login view.

    Accepts a Google access_token and returns JWT tokens for authenticated user.

    Frontend should:
    1. Use Google Sign-In button/SDK to get access_token
    2. Send access_token to this endpoint
    3. Receive JWT tokens in response
    """

    adapter_class = GoogleOAuth2Adapter
    callback_url = settings.SOCIALACCOUNT_PROVIDERS.get('google', {}).get('APP', {}).get('redirect_uri', 'http://localhost:3000/auth/callback')
    client_class = OAuth2Client
    permission_classes = [AllowAny]
    serializer_class = GoogleAuthSerializer

    @extend_schema(
        tags=['Authentication'],
        request=GoogleAuthSerializer,
        description="""
        Authenticate with Google OAuth2.

        **Frontend Integration:**
        1. Use Google Sign-In JavaScript library or React Google Login
        2. Get the access_token from Google
        3. POST the access_token to this endpoint
        4. Receive JWT tokens (access + refresh) in response

        **Example:**
        ```javascript
        // After Google sign-in success
        const googleAccessToken = googleResponse.access_token;

        // Send to backend
        fetch('/api/users/auth/google/', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ access_token: googleAccessToken })
        })
        .then(res => res.json())
        .then(data => {
          // Use data.access_token and data.refresh_token for API calls
          localStorage.setItem('access_token', data.access_token);
          localStorage.setItem('refresh_token', data.refresh_token);
        });
        ```
        """
    )
    def post(self, request, *args, **kwargs):
        """
        Handle Google OAuth login with defensive error handling.

        Returns:
            Response: Success with JWT tokens or error response
        """
        try:
            # Call parent class to handle the OAuth flow (includes serializer validation)
            response = super().post(request, *args, **kwargs)

            # If successful, the response will have user and tokens
            if response.status_code == 200:
                user_email = response.data.get('user', {}).get('email', 'unknown')
                logger.info(f"Google login successful for user: {user_email}")

                return success_response(
                    data=response.data,
                    message='Successfully authenticated with Google',
                    status_code=status.HTTP_200_OK
                )

            # Log and return unexpected status codes
            logger.warning(f"Google login returned status {response.status_code}")
            return response

        except AuthenticationFailed as e:
            logger.warning(f"Google authentication failed: {str(e)}")
            return error_response(
                detail='Invalid Google access token or authentication failed',
                error_code='INVALID_GOOGLE_TOKEN',
                status_code=status.HTTP_401_UNAUTHORIZED
            )

        except (ValidationError, DjangoValidationError) as e:
            logger.error(f"Validation error during Google login: {str(e)}")
            return error_response(
                detail=str(e),
                error_code='VALIDATION_ERROR',
                status_code=status.HTTP_400_BAD_REQUEST
            )

        except Exception as e:
            logger.error(f"Unexpected error during Google authentication: {str(e)}", exc_info=True)
            return internal_server_error_response(
                detail='An unexpected error occurred during Google authentication',
                error_code='GOOGLE_AUTH_ERROR'
            )
