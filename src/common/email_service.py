"""Email service for sending emails via MailerSend."""

import logging
from typing import Optional
from django.conf import settings
from mailersend import MailerSendClient, Email, EmailBuilder, EmailContact

logger = logging.getLogger(__name__)


class EmailService:
    """Reusable email service using MailerSend."""

    def __init__(self):
        """Initialize MailerSend client."""
        self.api_key = settings.MAILERSEND_API_KEY
        self.from_email = settings.DEFAULT_FROM_EMAIL
        self.from_name = settings.DEFAULT_FROM_NAME
        self.client = MailerSendClient(api_key=self.api_key)

    def send_email(
        self,
        to_email: str,
        subject: str,
        text_content: str,
        html_content: Optional[str] = None,
        to_name: Optional[str] = None
    ) -> bool:
        """
        Send an email via MailerSend.

        Args:
            to_email: Recipient email address
            subject: Email subject
            text_content: Plain text email content
            html_content: Optional HTML email content
            to_name: Optional recipient name

        Returns:
            True if sent successfully, False otherwise
        """
        try:
            # Build email
            email = EmailBuilder()
            email.set_from(EmailContact(email=self.from_email, name=self.from_name))
            email.set_to([EmailContact(email=to_email, name=to_name or to_email)])
            email.set_subject(subject)
            email.set_text_content(text_content)

            if html_content:
                email.set_html_content(html_content)

            # Send email
            self.client.email.send(email.build())

            logger.info(f"Email sent successfully to {to_email}")
            return True

        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {str(e)}")
            return False

    def send_verification_email(self, to_email: str, to_name: str, verification_code: str) -> bool:
        """
        Send email verification code.

        Args:
            to_email: Recipient email address
            to_name: Recipient name
            verification_code: 4-digit verification code

        Returns:
            True if sent successfully, False otherwise
        """
        subject = "Verify Your Email Address"

        text_content = f"""
Hello {to_name},

Thank you for registering! Please use the verification code below to verify your email address:

Verification Code: {verification_code}

This code will expire in 15 minutes.

If you didn't create an account, please ignore this email.

Best regards,
QuixaPro Team
        """.strip()

        return self.send_email(
            to_email=to_email,
            subject=subject,
            text_content=text_content,
            to_name=to_name
        )

    def send_password_reset_email(
        self,
        to_email: str,
        to_name: str,
        reset_token: str,
        reset_url: Optional[str] = None
    ) -> bool:
        """
        Send password reset email.

        Args:
            to_email: Recipient email address
            to_name: Recipient name
            reset_token: Password reset token
            reset_url: Optional custom reset URL

        Returns:
            True if sent successfully, False otherwise
        """
        subject = "Password Reset Request"

        if reset_url:
            reset_link = f"{reset_url}?token={reset_token}"
            text_content = f"""
Hello {to_name},

We received a request to reset your password. Click the link below to reset your password:

{reset_link}

If you prefer, you can use this token: {reset_token}

This link will expire in 1 hour.

If you didn't request a password reset, please ignore this email.

Best regards,
QuixaPro Team
            """.strip()
        else:
            text_content = f"""
Hello {to_name},

We received a request to reset your password. Please use the token below to reset your password:

Reset Token: {reset_token}

This token will expire in 1 hour.

If you didn't request a password reset, please ignore this email.

Best regards,
The Team
            """.strip()

        return self.send_email(
            to_email=to_email,
            subject=subject,
            text_content=text_content,
            to_name=to_name
        )
