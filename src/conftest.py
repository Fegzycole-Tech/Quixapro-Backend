import pytest
from django.contrib.auth import get_user_model


@pytest.fixture
def user(db):
    return get_user_model().objects.create_user(
        name="testuser",
        email="test@example.com",
        password="password123",
    )
