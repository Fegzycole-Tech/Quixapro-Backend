import pytest
from customers.models import Customer
from customers.services import CustomerService


@pytest.mark.django_db
def test_create_customer(user):
    data = {
        "name": "Alice",
        "email": "alice@example.com",
        "address": "123 Main St",
        "photo_url": "https://example.com/photo.jpg",
    }

    customer = CustomerService.create_customer(data, user=user)

    assert customer.id is not None
    assert customer.user == user
    assert customer.email == data["email"]


@pytest.mark.django_db
def test_update_customer(user):
    customer = Customer.objects.create(user=user, name="Bob", email="bob@example.com")
    updated = CustomerService.update_customer(customer, {"name": "Bobby Updated"})
    assert updated.name == "Bobby Updated"


@pytest.mark.django_db
def test_get_customer_by_id(user):
    customer = Customer.objects.create(user=user, name="Carl", email="carl@example.com")
    found = CustomerService.get_customer_by_id(user.id, customer.id)
    assert found == customer


@pytest.mark.django_db
def test_get_user_customers_filters_by_user(user, django_user_model):
    other_user = django_user_model.objects.create_user(
        name="other", email="other@example.com", password="Password123"
    )
    Customer.objects.create(user=user, name="A", email="a@example.com")
    Customer.objects.create(user=other_user, name="B", email="b@example.com")

    results = CustomerService.get_user_customers(user.id)
    assert len(results) == 1
    assert results[0].user == user


@pytest.mark.django_db
def test_delete_customer(user):
    customer = Customer.objects.create(user=user, name="Del", email="del@example.com")
    CustomerService.delete_customer(customer.id)
    assert Customer.objects.count() == 0
