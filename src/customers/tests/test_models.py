import pytest
from django.utils import timezone
from customers.models import Customer


@pytest.mark.django_db
def test_customer_str_returns_name(user):
    customer = Customer.objects.create(
        user=user, name="John Doe", email="john@example.com"
    )

    assert str(customer) == "John Doe"


@pytest.mark.django_db
def test_customer_timestamps_auto_populate(user):
    customer = Customer.objects.create(
        user=user, name="Jane Smith", email="jane@example.com"
    )

    assert customer.created_at is not None
    assert customer.updated_at is not None
    assert customer.created_at <= timezone.now()
