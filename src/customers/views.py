import logging
from rest_framework import viewsets, filters
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiResponse

from customers.models import Customer
from customers.serializers import CustomerSerializer
from customers.services import CustomerService

logger = logging.getLogger(__name__)


@extend_schema(tags=["Customer"])
class CustomerViewSet(viewsets.ModelViewSet):
    serializer_class = CustomerSerializer
    permission_classes = [IsAuthenticated]

    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ["name", "email"]
    ordering_fields = ["name", "email", "address", "created_at"]
    ordering = ["-created_at"]

    def get_queryset(self):
        return CustomerService.get_user_customers(self.request.user.id)

    def perform_create(self, serializer):
        CustomerService.create_customer(
            serializer.validated_data, user=self.request.user
        )

    @extend_schema(
        summary="List all customers for the authenticated user",
        parameters=[
            OpenApiParameter("name", str, description="Filter by customer name"),
            OpenApiParameter("email", str, description="Filter by customer email"),
            OpenApiParameter(
                "ordering",
                str,
                description="Order by one or more fields (e.g. name, -email, created_at)",
            ),
        ],
        responses={200: CustomerSerializer(many=True)},
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @extend_schema(
        summary="Retrieve a single customer",
        parameters=[OpenApiParameter("pk", int, description="Customer ID")],
        responses={
            200: CustomerSerializer,
            404: OpenApiResponse(description="Not found"),
        },
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @extend_schema(
        summary="Create a new customer",
        request=CustomerSerializer,
        responses={
            201: CustomerSerializer,
            400: OpenApiResponse(description="Validation error"),
        },
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @extend_schema(
        summary="Update an existing customer",
        request=CustomerSerializer,
        parameters=[OpenApiParameter("pk", int, description="Customer ID")],
        responses={
            200: CustomerSerializer,
            404: OpenApiResponse(description="Not found"),
        },
    )
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @extend_schema(
        summary="Delete a customer",
        parameters=[OpenApiParameter("pk", int, description="Customer ID")],
        responses={204: OpenApiResponse(description="Deleted")},
    )
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)
