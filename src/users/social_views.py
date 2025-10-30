"""Views for social authentication."""

import logging
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from drf_spectacular.utils import extend_schema
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework.exceptions import AuthenticationFailed, ValidationError

from .serializers import GoogleAuthSerializer, UserSerializer
from .services import UserService
from common.responses import (
    success_response,
    error_response,
    internal_server_error_response
)

logger = logging.getLogger(__name__)


class GoogleLoginView(APIView):
    """
    Google OAuth2 login view.

    Accepts a Google access_token and returns JWT tokens for authenticated user.

    Frontend should:
    1. Use Google Sign-In button/SDK to get access_token
    2. Send access_token to this endpoint
    3. Receive JWT tokens in response
    """

    permission_classes = [AllowAny]
    serializer_class = GoogleAuthSerializer

    @extend_schema(
        tags=['Authentication'],
        request=GoogleAuthSerializer,
        description="""
        Authenticate with Google OAuth2.

        **Request Body:**
        ```json
        {
          "access_token": "ya29.A0ATi6K2sg8r4PavvvPMt4aXPPJ..."
        }
        ```

        **Success Response (200 OK):**
        ```json
        {
          "user": {
            "id": 1,
            "email": "user@gmail.com",
            "name": "John Doe",
            "photo_url": "https://lh3.googleusercontent.com/...",
            "email_verified": true,
            "created_at": "2025-10-30T10:00:00Z",
            "updated_at": "2025-10-30T10:00:00Z"
          },
          "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
          "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
          "message": "Successfully authenticated with Google"
        }
        ```

        **Error Responses:**
        - **400 Bad Request** - Missing or invalid access_token
          ```json
          {
            "detail": "{'access_token': ['This field is required.']}",
            "error_code": "VALIDATION_ERROR"
          }
          ```

        - **401 Unauthorized** - Invalid Google token or unverified email
          ```json
          {
            "detail": "Invalid Google access token or authentication failed",
            "error_code": "INVALID_GOOGLE_TOKEN"
          }
          ```

        - **500 Internal Server Error** - Unexpected server error
          ```json
          {
            "detail": "An unexpected error occurred during Google authentication",
            "error_code": "GOOGLE_AUTH_ERROR"
          }
          ```

        **Frontend Integration:**
        1. Use Google Sign-In JavaScript library or React Google Login
        2. Get the access_token from Google after successful sign-in
        3. POST the access_token to this endpoint
        4. Store the returned JWT tokens for authenticated API calls

        **Example:**
        ```javascript
        // After Google sign-in success
        const googleAccessToken = googleResponse.access_token;

        // Send to backend
        const response = await fetch('/auth/google/', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ access_token: googleAccessToken })
        });

        const data = await response.json();

        if (response.ok) {
          // Store tokens and user data
          localStorage.setItem('access_token', data.access_token);
          localStorage.setItem('refresh_token', data.refresh_token);
          localStorage.setItem('user', JSON.stringify(data.user));

          // User is now authenticated
          console.log('Logged in as:', data.user.email);
        } else {
          // Handle error
          console.error('Login failed:', data.detail);
        }
        ```

        **Notes:**
        - Google users are created with email_verified=true
        - Google users have no password (social auth only)
        - If user already exists with the same email, they will be logged in
        - The access_token must be a valid Google OAuth2 token
        """
    )
    def post(self, request):
        """
        Handle Google OAuth login with defensive error handling.

        Returns:
            Response: Success with JWT tokens or error response
        """
        try:
            # Validate the request data
            serializer = GoogleAuthSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)

            access_token = serializer.validated_data['access_token']

            # Authenticate with Google via service layer
            auth_data = UserService.authenticate_with_google(access_token)

            # Prepare response data with serialized user
            response_data = {
                'user': UserSerializer(auth_data['user']).data,
                'access_token': auth_data['access_token'],
                'refresh_token': auth_data['refresh_token'],
            }

            return success_response(
                data=response_data,
                message='Successfully authenticated with Google',
                status_code=status.HTTP_200_OK
            )

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
