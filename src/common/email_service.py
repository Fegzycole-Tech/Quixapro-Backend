import logging
from typing import Optional
from pathlib import Path
from django.conf import settings
from mailersend import MailerSendClient, EmailBuilder
from pybars import Compiler
from .exceptions import EmailSendError

logger = logging.getLogger(__name__)


class EmailService:
    """Reusable email service using MailerSend."""

    def __init__(self):
        """Initialize MailerSend client."""
        self.api_key = settings.MAILERSEND_API_KEY
        self.from_email = settings.DEFAULT_FROM_EMAIL
        self.from_name = settings.DEFAULT_FROM_NAME
        self.client = MailerSendClient(api_key=self.api_key)
        self.compiler = Compiler()
        self.templates_dir = Path(__file__).parent / 'templates' / 'emails'

    def _render_template(self, template_name: str, context: dict) -> str:
        """
        Render a Handlebars template with the given context.

        Args:
            template_name: Name of the template file (e.g., 'verification_email.html')
            context: Dictionary of variables to pass to the template

        Returns:
            Rendered HTML string

        Raises:
            FileNotFoundError: If template file doesn't exist
        """
        template_path = self.templates_dir / template_name

        if not template_path.exists():
            raise FileNotFoundError(f"Email template not found: {template_path}")

        with open(template_path, 'r', encoding='utf-8') as f:
            template_source = f.read()

        template = self.compiler.compile(template_source)
        return template(context)

    def send_email(
        self,
        to_email: str,
        subject: str,
        text_content: str,
        html_content: Optional[str] = None,
        to_name: Optional[str] = None
    ) -> None:
        """
        Send an email via MailerSend.

        Args:
            to_email: Recipient email address
            subject: Email subject
            text_content: Plain text email content
            html_content: Optional HTML email content
            to_name: Optional recipient name

        Raises:
            EmailSendError: If email sending fails
        """
        try:
            email_builder = (EmailBuilder()
                .from_email(self.from_email, self.from_name)
                .to(to_email, to_name or to_email)
                .subject(subject)
                .text(text_content))

            if html_content:
                email_builder = email_builder.html(html_content)

            email_request = email_builder.build()
            self.client.emails.send(email_request)

            logger.info(f"Email sent successfully to {to_email}")

        except Exception as e:
            error_msg = f"Failed to send email to {to_email}: {str(e)}"
            logger.error(error_msg)
            raise EmailSendError(error_msg, email=to_email) from e

    def send_verification_email(self, to_email: str, to_name: str, verification_code: str) -> None:
        """
        Send email verification code using Handlebars template.

        Args:
            to_email: Recipient email address
            to_name: Recipient name
            verification_code: 4-digit verification code

        Raises:
            EmailSendError: If email sending fails
        """
        subject = "Verify Your Email Address"

        html_content = self._render_template('verification_email.html', {
            'name': to_name,
            'verification_code': verification_code
        })

        self.send_email(
            to_email=to_email,
            subject=subject,
            text_content='',
            html_content=html_content,
            to_name=to_name
        )

    def send_password_reset_email(
        self,
        to_email: str,
        to_name: str,
        reset_token: str,
        reset_url: Optional[str] = None
    ) -> None:
        """
        Send password reset email using Handlebars template.

        Args:
            to_email: Recipient email address
            to_name: Recipient name
            reset_token: Password reset token
            reset_url: Optional custom reset URL

        Raises:
            EmailSendError: If email sending fails
        """
        subject = "Password Reset Request"

        full_reset_url = None
        if reset_url:
            full_reset_url = f"{reset_url}?token={reset_token}"

        html_content = self._render_template('password_reset_email.html', {
            'name': to_name,
            'reset_token': reset_token,
            'reset_url': full_reset_url
        })

        self.send_email(
            to_email=to_email,
            subject=subject,
            text_content='',
            html_content=html_content,
            to_name=to_name
        )
