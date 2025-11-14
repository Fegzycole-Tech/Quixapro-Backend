from django.conf import settings
from django.db import models
from customers.models import Customer
from businesses.models import Business


class Invoice(models.Model):
    STATUS_OVERDUE = "overdue"
    STATUS_UNPAID = "unpaid"
    STATUS_PAID = "paid"

    STATUS_CHOICES = [
        (STATUS_OVERDUE, "Overdue"),
        (STATUS_UNPAID, "Unpaid"),
        (STATUS_PAID, "Paid"),
    ]

    business = models.ForeignKey(
        Business, on_delete=models.CASCADE, related_name="invoices"
    )
    customer = models.ForeignKey(
        Customer, on_delete=models.CASCADE, related_name="invoices"
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="invoices"
    )

    start_date = models.DateField()
    end_date = models.DateField()
    status = models.CharField(
        max_length=10, choices=STATUS_CHOICES, default=STATUS_UNPAID
    )
    currency = models.CharField(max_length=3, default="USD")
    amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    note = models.TextField(blank=True, null=True)
    attached_documents = models.JSONField(blank=True, null=True, default=list)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "invoices"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Invoice #{self.id} - {self.customer.name}"


class InvoiceItem(models.Model):
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name="items")
    item_name = models.CharField(max_length=200)
    item_quantity = models.DecimalField(max_digits=10, decimal_places=2)
    item_price = models.DecimalField(max_digits=10, decimal_places=2)
    item_total = models.DecimalField(max_digits=10, decimal_places=2)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "invoice_items"
        ordering = ["id"]

    def __str__(self):
        return f"{self.item_name} - {self.invoice.id}"
