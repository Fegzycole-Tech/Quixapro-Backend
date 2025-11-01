from django.contrib import admin
from .models import Business


@admin.register(Business)
class BusinessAdmin(admin.ModelAdmin):
    list_display = ["name", "email", "phone_number", "user", "created_at"]

    list_filter = ["created_at", "updated_at"]

    search_fields = ["name", "email", "phone_number", "address"]

    readonly_fields = ["created_at", "updated_at"]

    ordering = ["-created_at"]

    fieldsets = (
        (
            "Business Information",
            {"fields": ("name", "email", "phone_number", "address", "photo_url")},
        ),
        ("Association", {"fields": ("user",)}),
        ("Timestamps", {"fields": ("created_at", "updated_at")}),
    )
