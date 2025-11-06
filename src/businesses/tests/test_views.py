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
        assert response.data["count"] == 1

    def test_create_business(self, client):
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

    def test_unverified_user_cannot_list_businesses(self, unverified_user):
        """Test that unverified users cannot list businesses."""
        client = APIClient()
        client.force_authenticate(user=unverified_user)
        response = client.get(self.endpoint)
        assert response.status_code == 403
        assert "Email verification required" in str(response.data)

    def test_unverified_user_cannot_create_business(self, unverified_user):
        """Test that unverified users cannot create businesses."""
        client = APIClient()
        client.force_authenticate(user=unverified_user)
        payload = {
            "name": "Test Business",
            "email": "test@example.com",
            "address": "Test St",
            "phone_number": "555"
        }
        response = client.post(self.endpoint, payload, format="json")
        assert response.status_code == 403
        assert "Email verification required" in str(response.data)

    def test_unverified_user_cannot_retrieve_business(self, unverified_user):
        """Test that unverified users cannot retrieve businesses."""
        client = APIClient()
        client.force_authenticate(user=unverified_user)
        business = Business.objects.create(
            user=unverified_user, name="Test", email="test@example.com", address="Test St", phone_number="555"
        )
        response = client.get(f"{self.endpoint}{business.id}/")
        assert response.status_code == 403
        assert "Email verification required" in str(response.data)

    def test_unverified_user_cannot_update_business(self, unverified_user):
        """Test that unverified users cannot update businesses."""
        client = APIClient()
        client.force_authenticate(user=unverified_user)
        business = Business.objects.create(
            user=unverified_user, name="Old", email="old@example.com", address="Old St", phone_number="333"
        )
        payload = {"name": "New Name"}
        response = client.patch(f"{self.endpoint}{business.id}/", payload, format="json")
        assert response.status_code == 403
        assert "Email verification required" in str(response.data)

    def test_unverified_user_cannot_delete_business(self, unverified_user):
        """Test that unverified users cannot delete businesses."""
        client = APIClient()
        client.force_authenticate(user=unverified_user)
        business = Business.objects.create(
            user=unverified_user, name="Del", email="del@example.com", address="Del St", phone_number="444"
        )
        response = client.delete(f"{self.endpoint}{business.id}/")
        assert response.status_code == 403
        assert "Email verification required" in str(response.data)

    def test_list_businesses_with_filters(self, client, user):
        """Test that count respects filters."""
        Business.objects.create(user=user, name="Company A", email="a@company.com", address="1 St", phone_number="111")
        Business.objects.create(user=user, name="Company B", email="b@company.com", address="2 St", phone_number="222")
        Business.objects.create(user=user, name="Company C", email="c@company.com", address="3 St", phone_number="333")

        response = client.get(self.endpoint)
        assert response.status_code == 200
        assert response.data["count"] == 3
        assert len(response.data["results"]) == 3

        response = client.get(f"{self.endpoint}?name=Company A")
        assert response.status_code == 200
        assert response.data["count"] == 1
        assert len(response.data["results"]) == 1

        response = client.get(f"{self.endpoint}?email=b@company.com")
        assert response.status_code == 200
        assert response.data["count"] == 1
        assert len(response.data["results"]) == 1

    def test_list_businesses_with_pagination(self, client, user):
        """Test that count reflects all filtered results, not just the page."""
        for i in range(15):
            Business.objects.create(
                user=user,
                name=f"Business {i}",
                email=f"business{i}@example.com",
                address=f"{i} Main St",
                phone_number=f"{i}00"
            )

        response = client.get(f"{self.endpoint}?limit=10&offset=0")
        assert response.status_code == 200
        assert response.data["count"] == 15
        assert len(response.data["results"]) == 10

        response = client.get(f"{self.endpoint}?limit=10&offset=10")
        assert response.status_code == 200
        assert response.data["count"] == 15
        assert len(response.data["results"]) == 5
