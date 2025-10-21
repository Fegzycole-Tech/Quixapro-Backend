"""Custom exceptions for the application."""


class EmailSendError(Exception):
    """Raised when email sending fails."""

    def __init__(self, message: str = "Failed to send email", email: str = None):
        self.message = message
        self.email = email
        super().__init__(self.message)
