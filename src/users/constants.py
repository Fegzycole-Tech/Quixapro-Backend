"""Constants for the users module."""

# Error messages
ERROR_SOCIAL_AUTH_LOGIN = "This account uses social authentication. Please login via your social provider."
ERROR_SOCIAL_AUTH_PASSWORD_CHANGE = (
    "This account uses social authentication and doesn't have a password. "
    "Password cannot be changed."
)
ERROR_PASSWORD_MISMATCH = "Password fields didn't match."
ERROR_PASSWORD_REQUIRED = "Password is required when password_confirm is provided."
ERROR_OLD_PASSWORD_INCORRECT = "Old password is incorrect."
ERROR_EMAIL_IN_USE = "This email is already in use."
ERROR_INVALID_RESET_TOKEN = "Invalid or expired reset token."
ERROR_USER_NOT_FOUND = "User with this email does not exist."
ERROR_SOCIAL_AUTH_PASSWORD_RESET = (
    "This account uses social authentication and doesn't have a password. "
    "Password reset is not available."
)
ERROR_INVALID_VERIFICATION_CODE = "Invalid or expired verification code."
ERROR_EMAIL_ALREADY_VERIFIED = "Email is already verified."
ERROR_EMAIL_NOT_VERIFIED = "Please verify your email address before logging in."

# Success messages
SUCCESS_PASSWORD_CHANGED = "Password changed successfully"
SUCCESS_LOGGED_OUT = "Successfully logged out"
SUCCESS_PASSWORD_RESET_EMAIL_SENT = "Password reset instructions have been sent to your email."
SUCCESS_PASSWORD_RESET = "Password has been reset successfully."
SUCCESS_VERIFICATION_EMAIL_SENT = "A verification code has been sent to your email."
SUCCESS_EMAIL_VERIFIED = "Email verified successfully."
SUCCESS_VERIFICATION_CODE_RESENT = "A new verification code has been sent to your email."

# Validation messages
VALIDATION_REFRESH_TOKEN_REQUIRED = "Refresh token is required"
