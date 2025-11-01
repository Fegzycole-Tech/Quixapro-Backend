import pytest
from rest_framework.test import APIClient
from businesses.models import Business


@pytest.mark.django_db
class TestBusinessViewSet:
    endpoint = "/businesses/"

    @pytest.fixture
    def client(self, user):
        client = APIClient()

        client.force_authenticate(user=user)

        return client

    def test_list_businesses(self, client, user):
        Business.objects.create(user=user, name="A", email="a@example.com", address="123 St", phone_number="111")

        response = client.get(self.endpoint)

        assert response.status_code == 200
        assert len(response.data["results"]) == 1

    def test_create_business(self, client, user):
        payload = {
            "name": "John's Business",
            "email": "john@example.com",
            "address": "456 Main St",
            "phone_number": "+1234567890"
        }

        response = client.post(self.endpoint, payload, format="json")

        assert response.status_code == 201
        assert Business.objects.filter(email="john@example.com").exists()

    def test_retrieve_business(self, client, user):
        business = Business.objects.create(
            user=user, name="Jane's Business", email="jane@example.com", address="789 Ave", phone_number="222"
        )

        response = client.get(f"{self.endpoint}{business.id}/")

        assert response.status_code == 200
        assert response.data["email"] == "jane@example.com"

    def test_update_business(self, client, user):
        business = Business.objects.create(
            user=user, name="Old", email="old@example.com", address="Old St", phone_number="333"
        )

        payload = {"name": "New Name"}

        response = client.patch(f"{self.endpoint}{business.id}/", payload, format="json")

        assert response.status_code == 200

        business.refresh_from_db()

        assert business.name == "New Name"

    def test_delete_business(self, client, user):
        business = Business.objects.create(
            user=user, name="Del", email="del@example.com", address="Del St", phone_number="444"
        )

        response = client.delete(f"{self.endpoint}{business.id}/")

        assert response.status_code == 204
        assert not Business.objects.filter(id=business.id).exists()
