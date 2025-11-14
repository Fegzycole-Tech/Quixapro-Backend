from django.contrib import admin
from .models import Invoice, InvoiceItem


class InvoiceItemInline(admin.TabularInline):
    model = InvoiceItem
    extra = 1


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "customer",
        "business",
        "status",
        "start_date",
        "end_date",
        "created_at",
    ]
    list_filter = ["status", "created_at"]
    search_fields = ["customer__name", "business__name", "note"]
    inlines = [InvoiceItemInline]
    readonly_fields = ["created_at", "updated_at"]


@admin.register(InvoiceItem)
class InvoiceItemAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "invoice",
        "item_name",
        "item_quantity",
        "item_price",
        "item_total",
    ]
    search_fields = ["item_name", "invoice__id"]
