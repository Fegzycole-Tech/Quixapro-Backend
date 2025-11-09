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
        assert response.data["count"] == 1

    def test_create_customer(self, client):
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

    def test_unverified_user_cannot_list_customers(self, unverified_user):
        """Test that unverified users cannot list customers."""
        client = APIClient()
        client.force_authenticate(user=unverified_user)
        response = client.get(self.endpoint)
        assert response.status_code == 403
        assert "Email verification required" in str(response.data)

    def test_unverified_user_cannot_create_customer(self, unverified_user):
        """Test that unverified users cannot create customers."""
        client = APIClient()
        client.force_authenticate(user=unverified_user)
        payload = {"name": "Test", "email": "test@example.com"}
        response = client.post(self.endpoint, payload, format="json")
        assert response.status_code == 403
        assert "Email verification required" in str(response.data)

    def test_unverified_user_cannot_retrieve_customer(self, unverified_user):
        """Test that unverified users cannot retrieve customers."""
        client = APIClient()
        client.force_authenticate(user=unverified_user)
        customer = Customer.objects.create(user=unverified_user, name="Test", email="test@example.com")
        response = client.get(f"{self.endpoint}{customer.id}/")
        assert response.status_code == 403
        assert "Email verification required" in str(response.data)

    def test_unverified_user_cannot_update_customer(self, unverified_user):
        """Test that unverified users cannot update customers."""
        client = APIClient()
        client.force_authenticate(user=unverified_user)
        customer = Customer.objects.create(user=unverified_user, name="Old", email="old@example.com")
        payload = {"name": "New Name"}
        response = client.patch(f"{self.endpoint}{customer.id}/", payload, format="json")
        assert response.status_code == 403
        assert "Email verification required" in str(response.data)

    def test_unverified_user_cannot_delete_customer(self, unverified_user):
        """Test that unverified users cannot delete customers."""
        client = APIClient()
        client.force_authenticate(user=unverified_user)
        customer = Customer.objects.create(user=unverified_user, name="Del", email="del@example.com")
        response = client.delete(f"{self.endpoint}{customer.id}/")
        assert response.status_code == 403
        assert "Email verification required" in str(response.data)

    def test_list_customers_with_filters(self, client, user):
        """Test that count respects filters."""
        Customer.objects.create(user=user, name="Alice", email="alice@example.com")
        Customer.objects.create(user=user, name="Bob", email="bob@example.com")
        Customer.objects.create(user=user, name="Charlie", email="charlie@example.com")

        response = client.get(self.endpoint)
        assert response.status_code == 200
        assert response.data["count"] == 3
        assert len(response.data["results"]) == 3

        response = client.get(f"{self.endpoint}?name=Alice")
        assert response.status_code == 200
        assert response.data["count"] == 1
        assert len(response.data["results"]) == 1

        response = client.get(f"{self.endpoint}?email=bob@example.com")
        assert response.status_code == 200
        assert response.data["count"] == 1
        assert len(response.data["results"]) == 1

    def test_list_customers_with_pagination(self, client, user):
        """Test that count reflects all filtered results, not just the page."""
        for i in range(15):
            Customer.objects.create(user=user, name=f"Customer {i}", email=f"customer{i}@example.com")

        response = client.get(f"{self.endpoint}?limit=10&offset=0")
        assert response.status_code == 200
        assert response.data["count"] == 15
        assert len(response.data["results"]) == 10

        response = client.get(f"{self.endpoint}?limit=10&offset=10")
        assert response.status_code == 200
        assert response.data["count"] == 15
        assert len(response.data["results"]) == 5

    def test_fuzzy_search_by_name(self, client, user):
        """Test fuzzy search across customer name."""
        Customer.objects.create(user=user, name="John Doe", email="john@example.com", address="123 Main St")
        Customer.objects.create(user=user, name="Jane Smith", email="jane@example.com", address="456 Oak Ave")
        Customer.objects.create(user=user, name="Bob Johnson", email="bob@example.com", address="789 Pine Rd")

        response = client.get(f"{self.endpoint}?search=john")
        assert response.status_code == 200
        assert response.data["count"] == 2
        assert len(response.data["results"]) == 2

        response = client.get(f"{self.endpoint}?search=jane")
        assert response.status_code == 200
        assert response.data["count"] == 1
        assert response.data["results"][0]["name"] == "Jane Smith"

    def test_fuzzy_search_by_email(self, client, user):
        """Test fuzzy search across customer email."""
        Customer.objects.create(user=user, name="Alice", email="alice.wonder@example.com", address="1 St")
        Customer.objects.create(user=user, name="Bob", email="bob.builder@test.com", address="2 St")
        Customer.objects.create(user=user, name="Charlie", email="charlie@example.com", address="3 St")

        response = client.get(f"{self.endpoint}?search=example.com")
        assert response.status_code == 200
        assert response.data["count"] == 2
        assert len(response.data["results"]) == 2

        response = client.get(f"{self.endpoint}?search=builder")
        assert response.status_code == 200
        assert response.data["count"] == 1
        assert response.data["results"][0]["email"] == "bob.builder@test.com"

    def test_fuzzy_search_by_address(self, client, user):
        """Test fuzzy search across customer address."""
        Customer.objects.create(user=user, name="A", email="a@test.com", address="123 Main Street")
        Customer.objects.create(user=user, name="B", email="b@test.com", address="456 Main Avenue")
        Customer.objects.create(user=user, name="C", email="c@test.com", address="789 Oak Boulevard")

        response = client.get(f"{self.endpoint}?search=Main")
        assert response.status_code == 200
        assert response.data["count"] == 2
        assert len(response.data["results"]) == 2

        response = client.get(f"{self.endpoint}?search=Boulevard")
        assert response.status_code == 200
        assert response.data["count"] == 1
        assert response.data["results"][0]["address"] == "789 Oak Boulevard"

    def test_fuzzy_search_across_multiple_fields(self, client, user):
        """Test fuzzy search works across all searchable fields."""
        Customer.objects.create(user=user, name="Tech Corp", email="contact@techcorp.com", address="Tech Park")
        Customer.objects.create(user=user, name="Innovation Inc", email="info@innovation.com", address="Innovation Plaza")
        Customer.objects.create(user=user, name="Digital Solutions", email="hello@digital.com", address="Business Center")

        response = client.get(f"{self.endpoint}?search=tech")
        assert response.status_code == 200
        assert response.data["count"] == 1
        assert response.data["results"][0]["name"] == "Tech Corp"

        response = client.get(f"{self.endpoint}?search=nonexistent")
        assert response.status_code == 200
        assert response.data["count"] == 0
        assert len(response.data["results"]) == 0
