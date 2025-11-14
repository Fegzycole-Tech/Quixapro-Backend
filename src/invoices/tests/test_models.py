import pytest
from django.contrib.auth import get_user_model
from decimal import Decimal
from invoices.models import Invoice, InvoiceItem
from customers.models import Customer
from businesses.models import Business

User = get_user_model()


@pytest.mark.django_db
class TestInvoiceModel:
    def test_create_invoice(self, user):
        customer = Customer.objects.create(
            user=user,
            name="Test Customer",
            email="customer@example.com"
        )
        business = Business.objects.create(
            user=user,
            name="Test Business",
            email="business@example.com",
            address="123 Business St",
            phone_number="+1234567890"
        )

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

        assert invoice.user == user
        assert invoice.customer == customer
        assert invoice.business == business
        assert invoice.status == "overdue"
        assert invoice.currency == "USD"
        assert invoice.amount == Decimal("1000.00")

    def test_invoice_str(self, user):
        customer = Customer.objects.create(
            user=user,
            name="John Doe",
            email="john@example.com"
        )
        business = Business.objects.create(
            user=user,
            name="My Business",
            email="biz@example.com",
            address="456 St",
            phone_number="+1234567890"
        )

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

        assert str(invoice) == f"Invoice #{invoice.id} - John Doe"

    def test_invoice_status_choices(self, user):
        customer = Customer.objects.create(
            user=user,
            name="Test Customer",
            email="customer@example.com"
        )
        business = Business.objects.create(
            user=user,
            name="Test Business",
            email="business@example.com",
            address="123 St",
            phone_number="+1234567890"
        )

        # Test all status choices
        for status, _ in Invoice.STATUS_CHOICES:
            invoice = Invoice.objects.create(
                user=user,
                customer=customer,
                business=business,
                start_date="2025-11-01",
                end_date="2025-11-30",
                status=status,
                currency="USD",
                amount=Decimal("100.00")
            )
            assert invoice.status == status

    def test_invoice_default_values(self, user):
        customer = Customer.objects.create(
            user=user,
            name="Test Customer",
            email="customer@example.com"
        )
        business = Business.objects.create(
            user=user,
            name="Test Business",
            email="business@example.com",
            address="123 St",
            phone_number="+1234567890"
        )

        invoice = Invoice.objects.create(
            user=user,
            customer=customer,
            business=business,
            start_date="2025-11-01",
            end_date="2025-11-30"
        )

        assert invoice.status == "unpaid"
        assert invoice.currency == "USD"
        assert invoice.amount == Decimal("0.00")
        assert invoice.attached_documents == []

    def test_invoice_timestamps_auto_populate(self, user):
        customer = Customer.objects.create(
            user=user,
            name="Test Customer",
            email="customer@example.com"
        )
        business = Business.objects.create(
            user=user,
            name="Test Business",
            email="business@example.com",
            address="123 St",
            phone_number="+1234567890"
        )

        invoice = Invoice.objects.create(
            user=user,
            customer=customer,
            business=business,
            start_date="2025-11-01",
            end_date="2025-11-30"
        )

        assert invoice.created_at is not None
        assert invoice.updated_at is not None


@pytest.mark.django_db
class TestInvoiceItemModel:
    def test_create_invoice_item(self, user):
        customer = Customer.objects.create(
            user=user,
            name="Test Customer",
            email="customer@example.com"
        )
        business = Business.objects.create(
            user=user,
            name="Test Business",
            email="business@example.com",
            address="123 St",
            phone_number="+1234567890"
        )
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

        item = InvoiceItem.objects.create(
            invoice=invoice,
            item_name="Web Development",
            item_quantity=Decimal("10.00"),
            item_price=Decimal("100.00"),
            item_total=Decimal("1000.00")
        )

        assert item.invoice == invoice
        assert item.item_name == "Web Development"
        assert item.item_quantity == Decimal("10.00")
        assert item.item_price == Decimal("100.00")
        assert item.item_total == Decimal("1000.00")

    def test_invoice_item_str(self, user):
        customer = Customer.objects.create(
            user=user,
            name="Test Customer",
            email="customer@example.com"
        )
        business = Business.objects.create(
            user=user,
            name="Test Business",
            email="business@example.com",
            address="123 St",
            phone_number="+1234567890"
        )
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

        item = InvoiceItem.objects.create(
            invoice=invoice,
            item_name="Design Services",
            item_quantity=Decimal("5.00"),
            item_price=Decimal("100.00"),
            item_total=Decimal("500.00")
        )

        assert str(item) == f"Design Services - {invoice.id}"

    def test_invoice_items_relationship(self, user):
        customer = Customer.objects.create(
            user=user,
            name="Test Customer",
            email="customer@example.com"
        )
        business = Business.objects.create(
            user=user,
            name="Test Business",
            email="business@example.com",
            address="123 St",
            phone_number="+1234567890"
        )
        invoice = Invoice.objects.create(
            user=user,
            customer=customer,
            business=business,
            start_date="2025-11-01",
            end_date="2025-11-30",
            status="overdue",
            currency="USD",
            amount=Decimal("1400.00")
        )

        InvoiceItem.objects.create(
            invoice=invoice,
            item_name="Item 1",
            item_quantity=Decimal("10.00"),
            item_price=Decimal("100.00"),
            item_total=Decimal("1000.00")
        )
        InvoiceItem.objects.create(
            invoice=invoice,
            item_name="Item 2",
            item_quantity=Decimal("5.00"),
            item_price=Decimal("80.00"),
            item_total=Decimal("400.00")
        )

        assert invoice.items.count() == 2
        assert invoice.items.all()[0].item_name == "Item 1"
        assert invoice.items.all()[1].item_name == "Item 2"
