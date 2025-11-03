import pytest
from django.contrib.auth import get_user_model


@pytest.fixture
def user(db):
    """Create a verified user for testing."""
    return get_user_model().objects.create_user(
        name="testuser",
        email="test@example.com",
        password="password123",
        email_verified=True,
    )


@pytest.fixture
def unverified_user(db):
    """Create an unverified user for testing email verification permissions."""
    return get_user_model().objects.create_user(
        name="unverified",
        email="unverified@example.com",
        password="password123",
        email_verified=False,
    )
