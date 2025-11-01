from rest_framework import serializers
from .models import Business


class BusinessSerializer(serializers.ModelSerializer):
    created_at = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S", read_only=True)
    updated_at = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S", read_only=True)

    class Meta:
        model = Business
        fields = [
            "id",
            "name",
            "email",
            "address",
            "phone_number",
            "photo_url",
            "created_at",
            "updated_at",
            "user",
        ]
        read_only_fields = ["id", "user", "created_at", "updated_at"]

    def create(self, validated_data):
        user = self.context.get("user")

        if user:
            validated_data["user"] = user

        return super().create(validated_data)
