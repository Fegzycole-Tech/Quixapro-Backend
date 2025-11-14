from rest_framework import serializers
from .models import Invoice, InvoiceItem
from customers.serializers import CustomerSerializer
from businesses.serializers import BusinessSerializer


class InvoiceItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = InvoiceItem
        fields = [
            "id",
            "item_name",
            "item_quantity",
            "item_price",
            "item_total",
        ]
        read_only_fields = ["id"]


class InvoiceSerializer(serializers.ModelSerializer):
    items = InvoiceItemSerializer(many=True)
    business_details = BusinessSerializer(source="business", read_only=True)
    customer_details = CustomerSerializer(source="customer", read_only=True)
    created_at = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S", read_only=True)
    updated_at = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S", read_only=True)

    class Meta:
        model = Invoice
        fields = [
            "id",
            "business",
            "customer",
            "business_details",
            "customer_details",
            "items",
            "start_date",
            "end_date",
            "status",
            "currency",
            "amount",
            "note",
            "attached_documents",
            "created_at",
            "updated_at",
            "user",
        ]
        read_only_fields = [
            "id",
            "user",
            "amount",
            "created_at",
            "updated_at",
            "business_details",
            "customer_details",
        ]

    def create(self, validated_data):
        items_data = validated_data.pop("items")
        user = self.context.get("user")

        if user:
            validated_data["user"] = user

        from decimal import Decimal

        amount = sum(Decimal(str(item["item_total"])) for item in items_data)
        validated_data["amount"] = amount

        invoice = Invoice.objects.create(**validated_data)

        for item_data in items_data:
            InvoiceItem.objects.create(invoice=invoice, **item_data)

        return invoice

    def update(self, instance, validated_data):
        items_data = validated_data.pop("items", None)

        if items_data is not None:
            from decimal import Decimal

            amount = sum(Decimal(str(item["item_total"])) for item in items_data)
            validated_data["amount"] = amount

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if items_data is not None:
            instance.items.all().delete()

            for item_data in items_data:
                InvoiceItem.objects.create(invoice=instance, **item_data)

        return instance
