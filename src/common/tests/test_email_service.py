"""Tests for email service."""

from django.test import TestCase, override_settings
from unittest.mock import patch, MagicMock
from common.email_service import EmailService


class EmailServiceTest(TestCase):
    """Tests for EmailService."""

    @override_settings(
        MAILERSEND_API_KEY='test-api-key',
        DEFAULT_FROM_EMAIL='noreply@test.com',
        DEFAULT_FROM_NAME='Test App'
    )
    @patch('common.email_service.MailerSendClient')
    def test_init_success(self, mock_client):
        """Test EmailService initialization."""
        mock_instance = MagicMock()
        mock_client.return_value = mock_instance

        service = EmailService()

        self.assertEqual(service.api_key, 'test-api-key')
        self.assertEqual(service.from_email, 'noreply@test.com')
        self.assertEqual(service.from_name, 'Test App')
        mock_client.assert_called_once_with(api_key='test-api-key')
        self.assertEqual(service.client, mock_instance)

    @override_settings(
        MAILERSEND_API_KEY='test-api-key',
        DEFAULT_FROM_EMAIL='noreply@test.com',
        DEFAULT_FROM_NAME='Test App'
    )
    @patch('common.email_service.MailerSendClient')
    def test_send_email_success(self, mock_client):
        """Test sending email successfully."""
        # Setup mocks
        mock_client_instance = MagicMock()
        mock_client.return_value = mock_client_instance
        mock_email_builder = MagicMock()
        mock_email_obj = MagicMock()
        mock_email_builder.build.return_value = mock_email_obj

        with patch('common.email_service.EmailBuilder', return_value=mock_email_builder):
            with patch('common.email_service.EmailContact') as mock_contact:
                service = EmailService()

                # Call send_email
                result = service.send_email(
                    to_email='recipient@test.com',
                    subject='Test Subject',
                    text_content='Test content',
                    html_content='<p>Test content</p>',
                    to_name='Test Recipient'
                )

                # Verify result
                self.assertTrue(result)

                # Verify EmailBuilder was called correctly
                mock_email_builder.set_subject.assert_called_once_with('Test Subject')
                mock_email_builder.set_text_content.assert_called_once_with('Test content')
                mock_email_builder.set_html_content.assert_called_once_with('<p>Test content</p>')

                # Verify EmailContact was called for from and to
                self.assertEqual(mock_contact.call_count, 2)

                # Verify email was sent
                mock_client_instance.email.send.assert_called_once_with(mock_email_obj)

    @override_settings(
        MAILERSEND_API_KEY='test-api-key',
        DEFAULT_FROM_EMAIL='noreply@test.com',
        DEFAULT_FROM_NAME='Test App'
    )
    @patch('common.email_service.MailerSendClient')
    def test_send_email_without_html(self, mock_client):
        """Test sending email without HTML content."""
        # Setup mocks
        mock_client_instance = MagicMock()
        mock_client.return_value = mock_client_instance
        mock_email_builder = MagicMock()
        mock_email_obj = MagicMock()
        mock_email_builder.build.return_value = mock_email_obj

        with patch('common.email_service.EmailBuilder', return_value=mock_email_builder):
            with patch('common.email_service.EmailContact'):
                service = EmailService()

                # Call send_email without html_content
                result = service.send_email(
                    to_email='recipient@test.com',
                    subject='Test Subject',
                    text_content='Test content'
                )

                # Verify result
                self.assertTrue(result)

                # Verify set_html_content was NOT called
                mock_email_builder.set_html_content.assert_not_called()

    @override_settings(
        MAILERSEND_API_KEY='test-api-key',
        DEFAULT_FROM_EMAIL='noreply@test.com',
        DEFAULT_FROM_NAME='Test App'
    )
    @patch('common.email_service.MailerSendClient')
    def test_send_email_failure(self, mock_client):
        """Test send_email handles exceptions gracefully."""
        # Setup mocks to raise exception
        mock_client_instance = MagicMock()
        mock_client.return_value = mock_client_instance
        mock_client_instance.email.send.side_effect = Exception('Send failed')

        with patch('common.email_service.EmailBuilder'):
            with patch('common.email_service.EmailContact'):
                service = EmailService()

                # Call send_email
                result = service.send_email(
                    to_email='recipient@test.com',
                    subject='Test Subject',
                    text_content='Test content'
                )

                # Verify failure returns False
                self.assertFalse(result)

    @override_settings(
        MAILERSEND_API_KEY='test-api-key',
        DEFAULT_FROM_EMAIL='noreply@test.com',
        DEFAULT_FROM_NAME='Test App'
    )
    @patch('common.email_service.MailerSendClient')
    def test_send_verification_email(self, mock_client):
        """Test sending verification email."""
        mock_client_instance = MagicMock()
        mock_client.return_value = mock_client_instance

        with patch('common.email_service.EmailBuilder'):
            with patch('common.email_service.EmailContact'):
                service = EmailService()

                # Mock send_email method
                with patch.object(service, 'send_email', return_value=True) as mock_send:
                    result = service.send_verification_email(
                        to_email='user@test.com',
                        to_name='Test User',
                        verification_code='1234'
                    )

                    # Verify result
                    self.assertTrue(result)

                    # Verify send_email was called with correct params
                    mock_send.assert_called_once()
                    call_args = mock_send.call_args

                    self.assertEqual(call_args.kwargs['to_email'], 'user@test.com')
                    self.assertEqual(call_args.kwargs['to_name'], 'Test User')
                    self.assertEqual(call_args.kwargs['subject'], 'Verify Your Email Address')
                    self.assertIn('1234', call_args.kwargs['text_content'])
                    self.assertIn('Test User', call_args.kwargs['text_content'])

    @override_settings(
        MAILERSEND_API_KEY='test-api-key',
        DEFAULT_FROM_EMAIL='noreply@test.com',
        DEFAULT_FROM_NAME='Test App'
    )
    @patch('common.email_service.MailerSendClient')
    def test_send_password_reset_email_with_url(self, mock_client):
        """Test sending password reset email with reset URL."""
        mock_client_instance = MagicMock()
        mock_client.return_value = mock_client_instance

        with patch('common.email_service.EmailBuilder'):
            with patch('common.email_service.EmailContact'):
                service = EmailService()

                # Mock send_email method
                with patch.object(service, 'send_email', return_value=True) as mock_send:
                    result = service.send_password_reset_email(
                        to_email='user@test.com',
                        to_name='Test User',
                        reset_token='reset-token-123',
                        reset_url='https://example.com/reset'
                    )

                    # Verify result
                    self.assertTrue(result)

                    # Verify send_email was called with correct params
                    mock_send.assert_called_once()
                    call_args = mock_send.call_args

                    self.assertEqual(call_args.kwargs['to_email'], 'user@test.com')
                    self.assertEqual(call_args.kwargs['to_name'], 'Test User')
                    self.assertEqual(call_args.kwargs['subject'], 'Password Reset Request')
                    self.assertIn('reset-token-123', call_args.kwargs['text_content'])
                    self.assertIn('https://example.com/reset?token=reset-token-123',
                                  call_args.kwargs['text_content'])
                    self.assertIn('Test User', call_args.kwargs['text_content'])

    @override_settings(
        MAILERSEND_API_KEY='test-api-key',
        DEFAULT_FROM_EMAIL='noreply@test.com',
        DEFAULT_FROM_NAME='Test App'
    )
    @patch('common.email_service.MailerSendClient')
    def test_send_password_reset_email_without_url(self, mock_client):
        """Test sending password reset email without reset URL."""
        mock_client_instance = MagicMock()
        mock_client.return_value = mock_client_instance

        with patch('common.email_service.EmailBuilder'):
            with patch('common.email_service.EmailContact'):
                service = EmailService()

                # Mock send_email method
                with patch.object(service, 'send_email', return_value=True) as mock_send:
                    result = service.send_password_reset_email(
                        to_email='user@test.com',
                        to_name='Test User',
                        reset_token='reset-token-123'
                    )

                    # Verify result
                    self.assertTrue(result)

                    # Verify send_email was called with correct params
                    mock_send.assert_called_once()
                    call_args = mock_send.call_args

                    self.assertEqual(call_args.kwargs['to_email'], 'user@test.com')
                    self.assertEqual(call_args.kwargs['to_name'], 'Test User')
                    self.assertEqual(call_args.kwargs['subject'], 'Password Reset Request')
                    self.assertIn('reset-token-123', call_args.kwargs['text_content'])
                    self.assertIn('Reset Token:', call_args.kwargs['text_content'])
                    self.assertIn('Test User', call_args.kwargs['text_content'])
                    # Should not contain a URL
                    self.assertNotIn('http', call_args.kwargs['text_content'])
