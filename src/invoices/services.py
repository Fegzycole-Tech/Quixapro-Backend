import logging
from typing import Any, Dict
from invoices.models import Invoice
from invoices.serializers import InvoiceSerializer

logger = logging.getLogger(__name__)


class InvoiceService:
    @staticmethod
    def create_invoice(data: Dict[str, Any], user) -> Invoice:
        logger.info(f"Creating invoice for user {user.email} with data: {data}")

        serializer = InvoiceSerializer(data=data, context={"user": user})

        serializer.is_valid(raise_exception=True)

        invoice = serializer.save()

        logger.info(
            f"Invoice created: ID={invoice.id}, Customer={invoice.customer.name}"
        )

        return invoice

    @staticmethod
    def update_invoice(invoice: Invoice, data: Dict[str, Any]) -> Invoice:
        serializer = InvoiceSerializer(invoice, data=data, partial=True)

        serializer.is_valid(raise_exception=True)

        updated_invoice = serializer.save()

        logger.debug(f"Updated invoice ID={updated_invoice.id}")

        return updated_invoice

    @staticmethod
    def delete_invoice(invoice_id: int) -> None:
        invoice = Invoice.objects.get(id=invoice_id)
        invoice.delete()
        logger.info(f"Invoice deleted: ID={invoice_id}")

    @staticmethod
    def get_user_invoices(user_id: int):
        return (
            Invoice.objects.filter(user_id=user_id)
            .select_related("business", "customer")
            .prefetch_related("items")
            .order_by("-created_at")
        )

    @staticmethod
    def get_invoice_by_id(user_id: int, invoice_id: int) -> Invoice:
        return (
            Invoice.objects.select_related("business", "customer")
            .prefetch_related("items")
            .get(id=invoice_id, user_id=user_id)
        )
