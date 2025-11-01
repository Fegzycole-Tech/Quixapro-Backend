import pytest
from django.contrib.auth import get_user_model
from businesses.models import Business

User = get_user_model()


@pytest.mark.django_db
class TestBusinessModel:
    def test_create_business(self, user):
        business = Business.objects.create(
            user=user,
            name="Test Business",
            email="business@example.com",
            address="123 Business St",
            phone_number="+1234567890"
        )

        assert business.name == "Test Business"
        assert business.email == "business@example.com"
        assert business.address == "123 Business St"
        assert business.phone_number == "+1234567890"
        assert business.user == user

    def test_business_str(self, user):
        business = Business.objects.create(
            user=user,
            name="My Business",
            email="my@business.com",
            address="456 Main St",
            phone_number="+0987654321"
        )

        assert str(business) == "My Business"
