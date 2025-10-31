from django.conf import settings
from django.db import models

class Customer(models.Model):
    name = models.CharField(max_length=100)

    email = models.EmailField(unique=True)

    photo_url = models.URLField(blank=True, null=True, max_length=500)

    address = models.CharField(blank=True, null=True, max_length=250)

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="customers"
    )

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name
