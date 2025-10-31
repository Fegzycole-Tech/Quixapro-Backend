from django.contrib import admin
from customers.models import Customer


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    """Admin configuration for the Customer model."""

    list_display = ("id", "name", "email", "user", "created_at", "updated_at")

    search_fields = ("name", "email", "user__email")

    list_filter = ("user", "created_at")

    ordering = ("-created_at",)

    readonly_fields = ("created_at", "updated_at")

    fieldsets = (
        (None, {"fields": ("user", "name", "email", "address", "photo_url")}),
        ("Timestamps", {"fields": ("created_at", "updated_at")}),
    )
