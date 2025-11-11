import pytest
from unittest.mock import patch, MagicMock
from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status

from common.cloudinary_service import CloudinaryService

User = get_user_model()


class CloudinaryServiceTests(TestCase):
    @patch('common.cloudinary_service.cloudinary.config')
    @patch('common.cloudinary_service.cloudinary.utils.api_sign_request')
    def test_generate_upload_signature(self, mock_sign_request, mock_config):
        mock_sign_request.return_value = 'test_signature_123'

        service = CloudinaryService()
        signature_data = service.generate_upload_signature(
            folder='customer_photos',
            allowed_formats=['jpg', 'png'],
            max_file_size=2097152,
            tags=['customer', 'profile']
        )

        assert signature_data['signature'] == 'test_signature_123'
        assert 'timestamp' in signature_data
        assert signature_data['folder'] == 'customer_photos'
        assert signature_data['allowed_formats'] == ['jpg', 'png']
        assert signature_data['max_file_size'] == 2097152
        assert signature_data['tags'] == ['customer', 'profile']

    @patch('common.cloudinary_service.cloudinary.config')
    def test_get_upload_url(self, mock_config):
        service = CloudinaryService()
        url = service.get_upload_url()

        assert url.startswith('https://api.cloudinary.com/v1_1/')
        assert '/image/upload' in url


class CloudinarySignatureViewTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email='test@example.com',
            name='Test User',
            password='testpass123',
            email_verified=True
        )
        self.client.force_authenticate(user=self.user)

    @patch('common.views.CloudinaryService.generate_upload_signature')
    @patch('common.views.CloudinaryService.get_upload_url')
    def test_generate_signature_success(self, mock_get_url, mock_generate_sig):
        mock_generate_sig.return_value = {
            'signature': 'test_signature',
            'timestamp': 1699632000,
            'cloud_name': 'test_cloud',
            'api_key': 'test_key',
            'folder': 'test_folder',
            'allowed_formats': ['jpg', 'png'],
            'max_file_size': 2097152,
            'tags': ['test']
        }
        mock_get_url.return_value = 'https://api.cloudinary.com/v1_1/test_cloud/image/upload'

        response = self.client.get(
            '/api/cloudinary/signature/',
            {
                'folder': 'test_folder',
                'allowed_formats': 'jpg,png',
                'max_file_size': '2097152',
                'tags': 'test'
            }
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data['signature'] == 'test_signature'
        assert response.data['timestamp'] == 1699632000
        assert response.data['upload_url'] == 'https://api.cloudinary.com/v1_1/test_cloud/image/upload'
        assert response.data['message'] == 'Signature generated successfully'

    def test_generate_signature_unauthenticated(self):
        self.client.force_authenticate(user=None)

        response = self.client.get('/api/cloudinary/signature/')

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @patch('common.views.CloudinaryService.generate_upload_signature')
    @patch('common.views.CloudinaryService.get_upload_url')
    def test_generate_signature_with_invalid_max_file_size(
        self, mock_get_url, mock_generate_sig
    ):
        response = self.client.get(
            '/api/cloudinary/signature/',
            {'max_file_size': 'invalid'}
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'max_file_size must be a valid integer' in response.data['detail']

    def test_generate_signature_unverified_email(self):
        """Test signature generation with unverified email."""
        unverified_user = User.objects.create_user(
            email='unverified@example.com',
            name='Unverified User',
            password='testpass123',
            email_verified=False
        )
        self.client.force_authenticate(user=unverified_user)

        response = self.client.get('/api/cloudinary/signature/')

        assert response.status_code == status.HTTP_403_FORBIDDEN
