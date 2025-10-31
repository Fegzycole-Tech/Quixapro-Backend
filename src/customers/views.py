import logging
from rest_framework import status, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiResponse
from customers.models import Customer
from customers.serializers import CustomerSerializer
from customers.services import CustomerService

logger = logging.getLogger(__name__)


@extend_schema(tags=["Customer"])
class CustomerViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing customers.
    Uses CustomerService for business logic and supports full CRUD.
    """

    serializer_class = CustomerSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Return only customers belonging to the authenticated user via the service layer."""

        user_id = self.request.user.id

        logger.info(f"Fetching customers for user_id={user_id}")

        return CustomerService.get_user_customers(user_id)

    def perform_create(self, serializer):
        """Attach the authenticated user to the new customer record."""

        user_id = self.request.user.id

        data = serializer.validated_data

        data["user_id"] = user_id

        logger.info(f"Creating new customer for user_id={user_id}")

        CustomerService.create_customer({**data, "user_id": user_id})

    @extend_schema(
        summary="List all customers for the authenticated user",
        responses={200: CustomerSerializer(many=True)},
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @extend_schema(
        summary="Retrieve a single customer",
        parameters=[OpenApiParameter("pk", int, description="Customer ID")],
        responses={200: CustomerSerializer, 404: OpenApiResponse(description="Not found")},
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @extend_schema(
        summary="Create a new customer",
        request=CustomerSerializer,
        responses={201: CustomerSerializer, 400: OpenApiResponse(description="Validation error")},
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @extend_schema(
        summary="Update an existing customer",
        request=CustomerSerializer,
        parameters=[OpenApiParameter("pk", int, description="Customer ID")],
        responses={200: CustomerSerializer, 404: OpenApiResponse(description="Not found")},
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
