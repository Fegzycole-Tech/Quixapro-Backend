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

    def test_fuzzy_search_by_name(self, client, user):
        """Test fuzzy search across business name."""
        Business.objects.create(user=user, name="Tech Solutions LLC", email="tech@example.com", address="1 St", phone_number="111")
        Business.objects.create(user=user, name="Digital Marketing Co", email="digital@example.com", address="2 St", phone_number="222")
        Business.objects.create(user=user, name="Tech Innovations", email="innovations@example.com", address="3 St", phone_number="333")

        response = client.get(f"{self.endpoint}?search=tech")
        assert response.status_code == 200
        assert response.data["count"] == 2
        assert len(response.data["results"]) == 2

        response = client.get(f"{self.endpoint}?search=digital")
        assert response.status_code == 200
        assert response.data["count"] == 1
        assert response.data["results"][0]["name"] == "Digital Marketing Co"

    def test_fuzzy_search_by_email(self, client, user):
        """Test fuzzy search across business email."""
        Business.objects.create(user=user, name="A", email="contact@techcorp.io", address="1 St", phone_number="111")
        Business.objects.create(user=user, name="B", email="info@business.com", address="2 St", phone_number="222")
        Business.objects.create(user=user, name="C", email="hello@techcorp.io", address="3 St", phone_number="333")

        response = client.get(f"{self.endpoint}?search=techcorp.io")
        assert response.status_code == 200
        assert response.data["count"] == 2
        assert len(response.data["results"]) == 2

        response = client.get(f"{self.endpoint}?search=hello")
        assert response.status_code == 200
        assert response.data["count"] == 1
        assert response.data["results"][0]["email"] == "hello@techcorp.io"

    def test_fuzzy_search_by_address(self, client, user):
        """Test fuzzy search across business address."""
        Business.objects.create(user=user, name="A", email="a@test.com", address="Silicon Valley Tech Park", phone_number="111")
        Business.objects.create(user=user, name="B", email="b@test.com", address="New York Business Center", phone_number="222")
        Business.objects.create(user=user, name="C", email="c@test.com", address="Silicon Plaza", phone_number="333")

        response = client.get(f"{self.endpoint}?search=Silicon")
        assert response.status_code == 200
        assert response.data["count"] == 2
        assert len(response.data["results"]) == 2

        response = client.get(f"{self.endpoint}?search=Center")
        assert response.status_code == 200
        assert response.data["count"] == 1
        assert response.data["results"][0]["address"] == "New York Business Center"

    def test_fuzzy_search_by_phone_number(self, client, user):
        """Test fuzzy search across business phone number."""
        Business.objects.create(user=user, name="A", email="a@test.com", address="1 St", phone_number="+1-555-1234")
        Business.objects.create(user=user, name="B", email="b@test.com", address="2 St", phone_number="+1-555-5678")
        Business.objects.create(user=user, name="C", email="c@test.com", address="3 St", phone_number="+1-444-1234")

        response = client.get(f"{self.endpoint}?search=555")
        assert response.status_code == 200
        assert response.data["count"] == 2
        assert len(response.data["results"]) == 2

        response = client.get(f"{self.endpoint}?search=5678")
        assert response.status_code == 200
        assert response.data["count"] == 1
        assert response.data["results"][0]["phone_number"] == "+1-555-5678"

    def test_fuzzy_search_across_multiple_fields(self, client, user):
        """Test fuzzy search works across all searchable fields."""
        Business.objects.create(user=user, name="Cloud Services Inc", email="contact@cloud.io", address="Cloud Tower", phone_number="555-CLOUD")
        Business.objects.create(user=user, name="Data Analytics", email="info@data.com", address="Analytics Plaza", phone_number="555-DATA")

        response = client.get(f"{self.endpoint}?search=cloud")
        assert response.status_code == 200
        assert response.data["count"] == 1
        assert response.data["results"][0]["name"] == "Cloud Services Inc"

        response = client.get(f"{self.endpoint}?search=nonexistent")
        assert response.status_code == 200
        assert response.data["count"] == 0
        assert len(response.data["results"]) == 0
