import pytest
from rest_framework.test import APIClient
from customers.models import Customer


@pytest.mark.django_db
class TestCustomerViewSet:
    endpoint = "/customers/"

    @pytest.fixture
    def client(self, user):
        client = APIClient()
        client.force_authenticate(user=user)
        return client

    def test_list_customers(self, client, user):
        Customer.objects.create(user=user, name="A", email="a@example.com")
        response = client.get(self.endpoint)
        assert response.status_code == 200
        assert len(response.data["results"]) == 1

    def test_create_customer(self, client, user):
        payload = {"name": "John", "email": "john@example.com"}
        response = client.post(self.endpoint, payload, format="json")
        assert response.status_code == 201
        assert Customer.objects.filter(email="john@example.com").exists()

    def test_retrieve_customer(self, client, user):
        customer = Customer.objects.create(user=user, name="Jane", email="jane@example.com")
        response = client.get(f"{self.endpoint}{customer.id}/")
        assert response.status_code == 200
        assert response.data["email"] == "jane@example.com"

    def test_update_customer(self, client, user):
        customer = Customer.objects.create(user=user, name="Old", email="old@example.com")
        payload = {"name": "New Name"}
        response = client.patch(f"{self.endpoint}{customer.id}/", payload, format="json")
        assert response.status_code == 200
        customer.refresh_from_db()
        assert customer.name == "New Name"

    def test_delete_customer(self, client, user):
        customer = Customer.objects.create(user=user, name="Del", email="del@example.com")
        response = client.delete(f"{self.endpoint}{customer.id}/")
        assert response.status_code == 204
        assert not Customer.objects.filter(id=customer.id).exists()
