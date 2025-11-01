import logging
from rest_framework import viewsets, filters
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiResponse

from businesses.models import Business
from businesses.serializers import BusinessSerializer
from businesses.services import BusinessService

logger = logging.getLogger(__name__)


@extend_schema(tags=["Business"])
class BusinessViewSet(viewsets.ModelViewSet):
    serializer_class = BusinessSerializer
    permission_classes = [IsAuthenticated]

    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ["name", "email"]
    ordering_fields = ["name", "email", "address", "phone_number", "created_at"]
    ordering = ["-created_at"]

    def get_queryset(self):
        return BusinessService.get_user_businesses(self.request.user.id)

    def perform_create(self, serializer):
        BusinessService.create_business(
            serializer.validated_data, user=self.request.user
        )

    @extend_schema(
        summary="List all businesses for the authenticated user",
        parameters=[
            OpenApiParameter("name", str, description="Filter by business name"),
            OpenApiParameter("email", str, description="Filter by business email"),
            OpenApiParameter(
                "ordering",
                str,
                description="Order by one or more fields (e.g. name, -email, created_at)",
            ),
        ],
        responses={200: BusinessSerializer(many=True)},
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @extend_schema(
        summary="Retrieve a single business",
        parameters=[OpenApiParameter("pk", int, description="Business ID")],
        responses={
            200: BusinessSerializer,
            404: OpenApiResponse(description="Not found"),
        },
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @extend_schema(
        summary="Create a new business",
        request=BusinessSerializer,
        responses={
            201: BusinessSerializer,
            400: OpenApiResponse(description="Validation error"),
        },
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @extend_schema(
        summary="Update an existing business",
        request=BusinessSerializer,
        parameters=[OpenApiParameter("pk", int, description="Business ID")],
        responses={
            200: BusinessSerializer,
            404: OpenApiResponse(description="Not found"),
        },
    )
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @extend_schema(
        summary="Delete a business",
        parameters=[OpenApiParameter("pk", int, description="Business ID")],
        responses={204: OpenApiResponse(description="Deleted")},
    )
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)
