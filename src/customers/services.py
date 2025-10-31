import logging
from typing import Any, Dict
from customers.models import Customer
from customers.serializers import CustomerSerializer

logger = logging.getLogger(__name__)


class CustomerService:
    """Service class for customer-related business logic."""

    @staticmethod
    def create_customer(data: Dict[str, Any]) -> Customer:
        """Create a new customer."""

        logger.info(f"Starting customer creation with data: {data}")

        serializer = CustomerSerializer(data=data)

        serializer.is_valid(raise_exception=True)

        customer: Customer = serializer.save()

        logger.info(f"Customer created: ID={customer.id}, Email={customer.email}")

        return customer

    @staticmethod
    def update_customer(customer: Customer, data: Dict[str, Any]) -> Customer:
        """Update an existing customer."""

        serializer = CustomerSerializer(customer, data=data, partial=True)

        serializer.is_valid(raise_exception=True)

        updated_customer = serializer.save()

        logger.debug(f"Updated customer ID={updated_customer.id}")

        return updated_customer

    @staticmethod
    def delete_customer(customer_id: int) -> None:
        """Delete a customer by ID."""
        customer = Customer.objects.get(id=customer_id)
        customer.delete()
        logger.info(f"Customer deleted: ID={customer_id}")

    @staticmethod
    def get_user_customers(user_id: int):
        """Return a QuerySet of customers belonging to the given user."""

        logger.debug(f"Fetching customers for user_id={user_id}")

        return Customer.objects.filter(user_id=user_id).order_by("-created_at")

    @staticmethod
    def get_customer_by_id(user_id: int, customer_id: int) -> Customer:
        """Get a customer belonging to the given user."""

        customer = Customer.objects.get(id=customer_id, user_id=user_id)

        logger.info(f"Found customer ID={customer_id} for user_id={user_id}")

        return customer
