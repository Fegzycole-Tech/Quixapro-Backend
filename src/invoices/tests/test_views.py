import pytest
from rest_framework.test import APIClient
from invoices.models import Invoice, InvoiceItem
from customers.models import Customer
from businesses.models import Business
from decimal import Decimal


@pytest.mark.django_db
class TestInvoiceViewSet:
    endpoint = "/invoices/"

    @pytest.fixture
    def client(self, user):
        client = APIClient()
        client.force_authenticate(user=user)
        return client

    @pytest.fixture
    def customer(self, user):
        return Customer.objects.create(
            user=user,
            name="Test Customer",
            email="customer@example.com"
        )

    @pytest.fixture
    def business(self, user):
        return Business.objects.create(
            user=user,
            name="Test Business",
            email="business@example.com",
            address="123 Business St",
            phone_number="+1234567890"
        )

    def test_list_invoices(self, client, user, customer, business):
        Invoice.objects.create(
            user=user,
            customer=customer,
            business=business,
            start_date="2025-11-01",
            end_date="2025-11-30",
            status="overdue",
            currency="USD",
            amount=Decimal("1000.00")
        )
        response = client.get(self.endpoint)
        assert response.status_code == 200
        assert len(response.data["results"]) == 1
        assert response.data["count"] == 1

    def test_create_invoice(self, client, customer, business):
        payload = {
            "business": business.id,
            "customer": customer.id,
            "start_date": "2025-11-01",
            "end_date": "2025-11-30",
            "status": "overdue",
            "currency": "USD",
            "items": [
                {
                    "item_name": "Web Development",
                    "item_quantity": "10.00",
                    "item_price": "100.00",
                    "item_total": "1000.00"
                },
                {
                    "item_name": "Design",
                    "item_quantity": "5.00",
                    "item_price": "80.00",
                    "item_total": "400.00"
                }
            ]
        }
        response = client.post(self.endpoint, payload, format="json")
        assert response.status_code == 201
        assert Invoice.objects.filter(customer=customer, business=business).exists()

        invoice = Invoice.objects.get(customer=customer, business=business)
        assert invoice.amount == Decimal("1400.00")
        assert invoice.items.count() == 2

    def test_create_invoice_calculates_amount(self, client, customer, business):
        """Test that invoice amount is calculated from item totals."""
        payload = {
            "business": business.id,
            "customer": customer.id,
            "start_date": "2025-11-01",
            "end_date": "2025-11-30",
            "status": "unpaid",
            "currency": "USD",
            "items": [
                {
                    "item_name": "Item 1",
                    "item_quantity": "2.00",
                    "item_price": "50.00",
                    "item_total": "100.00"
                },
                {
                    "item_name": "Item 2",
                    "item_quantity": "3.00",
                    "item_price": "75.00",
                    "item_total": "225.00"
                }
            ]
        }
        response = client.post(self.endpoint, payload, format="json")
        assert response.status_code == 201
        assert response.data["amount"] == "325.00"

    def test_retrieve_invoice(self, client, user, customer, business):
        invoice = Invoice.objects.create(
            user=user,
            customer=customer,
            business=business,
            start_date="2025-11-01",
            end_date="2025-11-30",
            status="paid",
            currency="USD",
            amount=Decimal("500.00")
        )
        InvoiceItem.objects.create(
            invoice=invoice,
            item_name="Service",
            item_quantity=Decimal("5.00"),
            item_price=Decimal("100.00"),
            item_total=Decimal("500.00")
        )
        response = client.get(f"{self.endpoint}{invoice.id}/")
        assert response.status_code == 200
        assert response.data["status"] == "paid"
        assert response.data["amount"] == "500.00"
        assert response.data["currency"] == "USD"
        assert len(response.data["items"]) == 1
        assert "business_details" in response.data
        assert "customer_details" in response.data
        assert response.data["business_details"]["name"] == "Test Business"
        assert response.data["customer_details"]["name"] == "Test Customer"

    def test_update_invoice(self, client, user, customer, business):
        invoice = Invoice.objects.create(
            user=user,
            customer=customer,
            business=business,
            start_date="2025-11-01",
            end_date="2025-11-30",
            status="overdue",
            currency="USD",
            amount=Decimal("100.00")
        )
        payload = {
            "business": business.id,
            "customer": customer.id,
            "start_date": "2025-11-01",
            "end_date": "2025-11-30",
            "status": "paid",
            "currency": "EUR",
            "items": [
                {
                    "item_name": "Updated Item",
                    "item_quantity": "2.00",
                    "item_price": "150.00",
                    "item_total": "300.00"
                }
            ]
        }
        response = client.put(f"{self.endpoint}{invoice.id}/", payload, format="json")
        assert response.status_code == 200
        invoice.refresh_from_db()
        assert invoice.status == "paid"
        assert invoice.currency == "EUR"
        assert invoice.amount == Decimal("300.00")

    def test_partial_update_invoice(self, client, user, customer, business):
        invoice = Invoice.objects.create(
            user=user,
            customer=customer,
            business=business,
            start_date="2025-11-01",
            end_date="2025-11-30",
            status="overdue",
            currency="USD",
            amount=Decimal("1000.00")
        )
        payload = {"status": "unpaid"}
        response = client.patch(f"{self.endpoint}{invoice.id}/", payload, format="json")
        assert response.status_code == 200
        invoice.refresh_from_db()
        assert invoice.status == "unpaid"
        assert invoice.amount == Decimal("1000.00")

    def test_delete_invoice(self, client, user, customer, business):
        invoice = Invoice.objects.create(
            user=user,
            customer=customer,
            business=business,
            start_date="2025-11-01",
            end_date="2025-11-30",
            status="overdue",
            currency="USD",
            amount=Decimal("100.00")
        )
        response = client.delete(f"{self.endpoint}{invoice.id}/")
        assert response.status_code == 204
        assert not Invoice.objects.filter(id=invoice.id).exists()

    def test_filter_by_status(self, client, user, customer, business):
        Invoice.objects.create(
            user=user,
            customer=customer,
            business=business,
            start_date="2025-11-01",
            end_date="2025-11-30",
            status="overdue",
            currency="USD",
            amount=Decimal("100.00")
        )
        Invoice.objects.create(
            user=user,
            customer=customer,
            business=business,
            start_date="2025-11-01",
            end_date="2025-11-30",
            status="paid",
            currency="USD",
            amount=Decimal("200.00")
        )
        response = client.get(f"{self.endpoint}?status=paid")
        assert response.status_code == 200
        assert response.data["count"] == 1
        assert response.data["results"][0]["status"] == "paid"

    def test_filter_by_business(self, client, user, customer, business):
        business2 = Business.objects.create(
            user=user,
            name="Business 2",
            email="biz2@example.com",
            address="456 St",
            phone_number="+0987654321"
        )
        Invoice.objects.create(
            user=user,
            customer=customer,
            business=business,
            start_date="2025-11-01",
            end_date="2025-11-30",
            status="overdue",
            currency="USD",
            amount=Decimal("100.00")
        )
        Invoice.objects.create(
            user=user,
            customer=customer,
            business=business2,
            start_date="2025-11-01",
            end_date="2025-11-30",
            status="overdue",
            currency="USD",
            amount=Decimal("200.00")
        )
        response = client.get(f"{self.endpoint}?business={business2.id}")
        assert response.status_code == 200
        assert response.data["count"] == 1

    def test_filter_by_customer(self, client, user, customer, business):
        customer2 = Customer.objects.create(
            user=user,
            name="Customer 2",
            email="cust2@example.com"
        )
        Invoice.objects.create(
            user=user,
            customer=customer,
            business=business,
            start_date="2025-11-01",
            end_date="2025-11-30",
            status="overdue",
            currency="USD",
            amount=Decimal("100.00")
        )
        Invoice.objects.create(
            user=user,
            customer=customer2,
            business=business,
            start_date="2025-11-01",
            end_date="2025-11-30",
            status="overdue",
            currency="USD",
            amount=Decimal("200.00")
        )
        response = client.get(f"{self.endpoint}?customer={customer2.id}")
        assert response.status_code == 200
        assert response.data["count"] == 1

    def test_search_invoices_by_note(self, client, user, customer, business):
        Invoice.objects.create(
            user=user,
            customer=customer,
            business=business,
            start_date="2025-11-01",
            end_date="2025-11-30",
            status="overdue",
            currency="USD",
            amount=Decimal("100.00"),
            note="Payment for web development"
        )
        Invoice.objects.create(
            user=user,
            customer=customer,
            business=business,
            start_date="2025-11-01",
            end_date="2025-11-30",
            status="overdue",
            currency="USD",
            amount=Decimal("200.00"),
            note="Design services"
        )
        response = client.get(f"{self.endpoint}?search=web development")
        assert response.status_code == 200
        assert response.data["count"] == 1
        assert "web development" in response.data["results"][0]["note"]

    def test_search_invoices_by_customer_name(self, client, user, business):
        customer1 = Customer.objects.create(
            user=user,
            name="Acme Corporation",
            email="acme@example.com"
        )
        customer2 = Customer.objects.create(
            user=user,
            name="Tech Startup Inc",
            email="tech@example.com"
        )
        Invoice.objects.create(
            user=user,
            customer=customer1,
            business=business,
            start_date="2025-11-01",
            end_date="2025-11-30",
            status="overdue",
            currency="USD",
            amount=Decimal("100.00")
        )
        Invoice.objects.create(
            user=user,
            customer=customer2,
            business=business,
            start_date="2025-11-01",
            end_date="2025-11-30",
            status="overdue",
            currency="USD",
            amount=Decimal("200.00")
        )
        response = client.get(f"{self.endpoint}?search=Acme")
        assert response.status_code == 200
        assert response.data["count"] == 1
        assert response.data["results"][0]["customer_details"]["name"] == "Acme Corporation"

    def test_search_invoices_by_business_name(self, client, user, customer):
        business1 = Business.objects.create(
            user=user,
            name="Consulting Services LLC",
            email="consulting@example.com",
            address="123 St",
            phone_number="+1234567890"
        )
        business2 = Business.objects.create(
            user=user,
            name="Marketing Agency",
            email="marketing@example.com",
            address="456 St",
            phone_number="+0987654321"
        )
        Invoice.objects.create(
            user=user,
            customer=customer,
            business=business1,
            start_date="2025-11-01",
            end_date="2025-11-30",
            status="overdue",
            currency="USD",
            amount=Decimal("100.00")
        )
        Invoice.objects.create(
            user=user,
            customer=customer,
            business=business2,
            start_date="2025-11-01",
            end_date="2025-11-30",
            status="overdue",
            currency="USD",
            amount=Decimal("200.00")
        )
        response = client.get(f"{self.endpoint}?search=Consulting")
        assert response.status_code == 200
        assert response.data["count"] == 1
        assert response.data["results"][0]["business_details"]["name"] == "Consulting Services LLC"

    def test_search_invoices_case_insensitive(self, client, user, customer, business):
        Invoice.objects.create(
            user=user,
            customer=customer,
            business=business,
            start_date="2025-11-01",
            end_date="2025-11-30",
            status="overdue",
            currency="USD",
            amount=Decimal("100.00"),
            note="URGENT Payment Required"
        )
        response = client.get(f"{self.endpoint}?search=urgent payment")
        assert response.status_code == 200
        assert response.data["count"] == 1

    def test_unverified_user_cannot_access_invoices(self, unverified_user, customer, business):
        client = APIClient()
        client.force_authenticate(user=unverified_user)
        response = client.get(self.endpoint)
        assert response.status_code == 403
        assert "Email verification required" in str(response.data)

    def test_create_invoice_with_optional_fields(self, client, customer, business):
        payload = {
            "business": business.id,
            "customer": customer.id,
            "start_date": "2025-11-01",
            "end_date": "2025-11-30",
            "status": "unpaid",
            "currency": "GBP",
            "note": "Special instructions",
            "attached_documents": [
                "https://example.com/doc1.pdf",
                "https://example.com/doc2.pdf"
            ],
            "items": [
                {
                    "item_name": "Service",
                    "item_quantity": "1.00",
                    "item_price": "500.00",
                    "item_total": "500.00"
                }
            ]
        }
        response = client.post(self.endpoint, payload, format="json")
        assert response.status_code == 201
        assert response.data["note"] == "Special instructions"
        assert len(response.data["attached_documents"]) == 2
        assert response.data["currency"] == "GBP"
