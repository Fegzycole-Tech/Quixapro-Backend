import pytest
from django.contrib.auth import get_user_model
from decimal import Decimal
from invoices.models import Invoice, InvoiceItem
from invoices.services import InvoiceService
from customers.models import Customer
from businesses.models import Business

User = get_user_model()


@pytest.mark.django_db
class TestInvoiceService:
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

    def test_get_user_invoices(self, user, customer, business):
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

        Invoice.objects.create(
            user=user,
            customer=customer,
            business=business,
            start_date="2025-12-01",
            end_date="2025-12-31",
            status="paid",
            currency="USD",
            amount=Decimal("2000.00")
        )

        invoices = InvoiceService.get_user_invoices(user.id)

        assert invoices.count() == 2

    def test_create_invoice(self, user, customer, business):
        data = {
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
                }
            ]
        }

        invoice = InvoiceService.create_invoice(data, user)

        assert invoice.user == user
        assert invoice.customer == customer
        assert invoice.business == business
        assert invoice.amount == Decimal("1000.00")
        assert invoice.items.count() == 1

    def test_get_invoice_by_id(self, user, customer, business):
        invoice = Invoice.objects.create(
            user=user,
            customer=customer,
            business=business,
            start_date="2025-11-01",
            end_date="2025-11-30",
            status="overdue",
            currency="USD",
            amount=Decimal("500.00")
        )

        retrieved = InvoiceService.get_invoice_by_id(user.id, invoice.id)

        assert retrieved == invoice

    def test_update_invoice(self, user, customer, business):
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

        InvoiceItem.objects.create(
            invoice=invoice,
            item_name="Old Item",
            item_quantity=Decimal("1.00"),
            item_price=Decimal("100.00"),
            item_total=Decimal("100.00")
        )

        updated_data = {
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

        updated = InvoiceService.update_invoice(invoice, updated_data)

        assert updated.status == "paid"
        assert updated.currency == "EUR"
        assert updated.amount == Decimal("300.00")
        assert updated.items.count() == 1
        assert updated.items.first().item_name == "Updated Item"

    def test_delete_invoice(self, user, customer, business):
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

        InvoiceService.delete_invoice(invoice.id)

        assert not Invoice.objects.filter(id=invoice.id).exists()

    def test_get_user_invoices_filters_by_user(self, user, customer, business, django_user_model):
        other_user = django_user_model.objects.create_user(
            name="other",
            email="other@example.com",
            password="Password123"
        )

        other_customer = Customer.objects.create(
            user=other_user,
            name="Other Customer",
            email="other_customer@example.com"
        )

        other_business = Business.objects.create(
            user=other_user,
            name="Other Business",
            email="other_business@example.com",
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
            amount=Decimal("1000.00")
        )

        Invoice.objects.create(
            user=other_user,
            customer=other_customer,
            business=other_business,
            start_date="2025-11-01",
            end_date="2025-11-30",
            status="paid",
            currency="USD",
            amount=Decimal("2000.00")
        )

        results = InvoiceService.get_user_invoices(user.id)
        assert results.count() == 1
        assert results[0].user == user

    def test_create_invoice_with_multiple_items(self, user, customer, business):
        data = {
            "business": business.id,
            "customer": customer.id,
            "start_date": "2025-11-01",
            "end_date": "2025-11-30",
            "status": "unpaid",
            "currency": "GBP",
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
                },
                {
                    "item_name": "Item 3",
                    "item_quantity": "1.00",
                    "item_price": "175.00",
                    "item_total": "175.00"
                }
            ]
        }

        invoice = InvoiceService.create_invoice(data, user)

        assert invoice.items.count() == 3
        assert invoice.amount == Decimal("500.00")

    def test_create_invoice_with_optional_fields(self, user, customer, business):
        data = {
            "business": business.id,
            "customer": customer.id,
            "start_date": "2025-11-01",
            "end_date": "2025-11-30",
            "status": "overdue",
            "currency": "USD",
            "note": "Special instructions for this invoice",
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

        invoice = InvoiceService.create_invoice(data, user)

        assert invoice.note == "Special instructions for this invoice"
        assert len(invoice.attached_documents) == 2
        assert invoice.attached_documents[0] == "https://example.com/doc1.pdf"
