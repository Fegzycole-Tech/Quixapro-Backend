import pytest
from django.contrib.auth import get_user_model
from businesses.models import Business
from businesses.services import BusinessService

User = get_user_model()


@pytest.mark.django_db
class TestBusinessService:
    def test_get_user_businesses(self, user):
        Business.objects.create(
            user=user, name="Business A", email="a@example.com", address="123 St", phone_number="111"
        )

        Business.objects.create(
            user=user, name="Business B", email="b@example.com", address="456 St", phone_number="222"
        )

        businesses = BusinessService.get_user_businesses(user.id)

        assert businesses.count() == 2

    def test_create_business(self, user):
        data = {
            "name": "New Business",
            "email": "new@example.com",
            "address": "789 Ave",
            "phone_number": "+1234567890"
        }

        business = BusinessService.create_business(data, user)

        assert business.name == "New Business"
        assert business.user == user

    def test_get_business_by_id(self, user):
        business = Business.objects.create(
            user=user, name="Get Business", email="get@example.com", address="321 Rd", phone_number="333"
        )

        retrieved = BusinessService.get_business_by_id(user.id, business.id)

        assert retrieved == business

    def test_update_business(self, user):
        business = Business.objects.create(
            user=user, name="Old Name", email="old@example.com", address="Old St", phone_number="444"
        )

        updated = BusinessService.update_business(business, {"name": "New Name"})

        assert updated.name == "New Name"

    def test_delete_business(self, user):
        business = Business.objects.create(
            user=user, name="Delete Me", email="delete@example.com", address="Del St", phone_number="555"
        )

        BusinessService.delete_business(business.id)

        assert not Business.objects.filter(id=business.id).exists()
