"""Tests for email service."""

from django.test import TestCase, override_settings
from unittest.mock import patch, MagicMock
from common.email_service import EmailService
from common.exceptions import EmailSendError


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
    @patch('common.email_service.EmailBuilder')
    def test_send_email_success(self, mock_email_builder_class, mock_client):
        """Test sending email successfully."""
        # Setup mocks
        mock_client_instance = MagicMock()
        mock_client.return_value = mock_client_instance

        # Mock the chainable EmailBuilder
        mock_builder_instance = MagicMock()
        mock_email_builder_class.return_value = mock_builder_instance

        # Setup chainable methods
        mock_builder_instance.from_email.return_value = mock_builder_instance
        mock_builder_instance.to.return_value = mock_builder_instance
        mock_builder_instance.subject.return_value = mock_builder_instance
        mock_builder_instance.text.return_value = mock_builder_instance
        mock_builder_instance.html.return_value = mock_builder_instance

        mock_email_request = MagicMock()
        mock_builder_instance.build.return_value = mock_email_request

        service = EmailService()

        # Call send_email
        service.send_email(
            to_email='recipient@test.com',
            subject='Test Subject',
            text_content='Test content',
            html_content='<p>Test content</p>',
            to_name='Test Recipient'
        )

        # Verify EmailBuilder methods were called
        mock_builder_instance.from_email.assert_called_once_with('noreply@test.com', 'Test App')
        mock_builder_instance.to.assert_called_once_with('recipient@test.com', 'Test Recipient')
        mock_builder_instance.subject.assert_called_once_with('Test Subject')
        mock_builder_instance.text.assert_called_once_with('Test content')
        mock_builder_instance.html.assert_called_once_with('<p>Test content</p>')
        mock_builder_instance.build.assert_called_once()

        # Verify email was sent (note: .emails not .email)
        mock_client_instance.emails.send.assert_called_once_with(mock_email_request)

    @override_settings(
        MAILERSEND_API_KEY='test-api-key',
        DEFAULT_FROM_EMAIL='noreply@test.com',
        DEFAULT_FROM_NAME='Test App'
    )
    @patch('common.email_service.MailerSendClient')
    @patch('common.email_service.EmailBuilder')
    def test_send_email_without_html(self, mock_email_builder_class, mock_client):
        """Test sending email without HTML content."""
        # Setup mocks
        mock_client_instance = MagicMock()
        mock_client.return_value = mock_client_instance

        # Mock the chainable EmailBuilder
        mock_builder_instance = MagicMock()
        mock_email_builder_class.return_value = mock_builder_instance

        # Setup chainable methods
        mock_builder_instance.from_email.return_value = mock_builder_instance
        mock_builder_instance.to.return_value = mock_builder_instance
        mock_builder_instance.subject.return_value = mock_builder_instance
        mock_builder_instance.text.return_value = mock_builder_instance

        mock_email_request = MagicMock()
        mock_builder_instance.build.return_value = mock_email_request

        service = EmailService()

        # Call send_email without html_content
        service.send_email(
            to_email='recipient@test.com',
            subject='Test Subject',
            text_content='Test content'
        )

        # Verify html method was NOT called
        mock_builder_instance.html.assert_not_called()

        # Verify other methods were called
        mock_builder_instance.from_email.assert_called_once()
        mock_builder_instance.to.assert_called_once()
        mock_builder_instance.subject.assert_called_once()
        mock_builder_instance.text.assert_called_once()

    @override_settings(
        MAILERSEND_API_KEY='test-api-key',
        DEFAULT_FROM_EMAIL='noreply@test.com',
        DEFAULT_FROM_NAME='Test App'
    )
    @patch('common.email_service.MailerSendClient')
    @patch('common.email_service.EmailBuilder')
    def test_send_email_failure(self, mock_email_builder_class, mock_client):
        """Test send_email raises EmailSendError on failure."""
        # Setup mocks to raise exception
        mock_client_instance = MagicMock()
        mock_client.return_value = mock_client_instance
        mock_client_instance.emails.send.side_effect = Exception('Send failed')

        # Mock the chainable EmailBuilder
        mock_builder_instance = MagicMock()
        mock_email_builder_class.return_value = mock_builder_instance
        mock_builder_instance.from_email.return_value = mock_builder_instance
        mock_builder_instance.to.return_value = mock_builder_instance
        mock_builder_instance.subject.return_value = mock_builder_instance
        mock_builder_instance.text.return_value = mock_builder_instance
        mock_builder_instance.build.return_value = MagicMock()

        service = EmailService()

        # Call send_email and expect EmailSendError
        with self.assertRaises(EmailSendError) as context:
            service.send_email(
                to_email='recipient@test.com',
                subject='Test Subject',
                text_content='Test content'
            )

        # Verify the error message contains details
        self.assertIn('recipient@test.com', str(context.exception))

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

        service = EmailService()

        # Mock send_email method
        with patch.object(service, 'send_email') as mock_send:
            service.send_verification_email(
                to_email='user@test.com',
                to_name='Test User',
                verification_code='1234'
            )

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

        service = EmailService()

        # Mock send_email method
        with patch.object(service, 'send_email') as mock_send:
            service.send_password_reset_email(
                to_email='user@test.com',
                to_name='Test User',
                reset_token='reset-token-123',
                reset_url='https://example.com/reset'
            )

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

        service = EmailService()

        # Mock send_email method
        with patch.object(service, 'send_email') as mock_send:
            service.send_password_reset_email(
                to_email='user@test.com',
                to_name='Test User',
                reset_token='reset-token-123'
            )

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
