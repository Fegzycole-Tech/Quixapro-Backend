import logging
from rest_framework import viewsets, filters
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiResponse

from invoices.serializers import InvoiceSerializer
from invoices.services import InvoiceService
from common.permissions import IsEmailVerified

logger = logging.getLogger(__name__)


@extend_schema(tags=["Invoice"])
class InvoiceViewSet(viewsets.ModelViewSet):
    serializer_class = InvoiceSerializer
    permission_classes = [IsAuthenticated, IsEmailVerified]

    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_fields = ["status", "business", "customer"]
    search_fields = ["note", "customer__name", "business__name"]
    ordering_fields = ["start_date", "end_date", "status", "created_at"]
    ordering = ["-created_at"]

    def get_queryset(self):
        return InvoiceService.get_user_invoices(self.request.user.id)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @extend_schema(
        summary="List all invoices for the authenticated user",
        description="Returns paginated list of invoices with business and customer details. The 'count' field in the response shows the total number of results matching the applied filters and search.",
        parameters=[
            OpenApiParameter(
                "status",
                str,
                description="Exact filter by invoice status (overdue, unpaid, paid)",
            ),
            OpenApiParameter(
                "business", int, description="Exact filter by business ID"
            ),
            OpenApiParameter(
                "customer", int, description="Exact filter by customer ID"
            ),
            OpenApiParameter(
                "search",
                str,
                description="Fuzzy search across note, customer name, and business name fields. Case-insensitive partial matching.",
            ),
            OpenApiParameter(
                "ordering",
                str,
                description="Order by one or more fields (e.g. start_date, -end_date, status, created_at)",
            ),
            OpenApiParameter(
                "limit", int, description="Number of results per page (default: 10)"
            ),
            OpenApiParameter(
                "offset", int, description="Starting position of the query (default: 0)"
            ),
        ],
        responses={200: InvoiceSerializer(many=True)},
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @extend_schema(
        summary="Retrieve a single invoice",
        parameters=[OpenApiParameter("pk", int, description="Invoice ID")],
        responses={
            200: InvoiceSerializer,
            404: OpenApiResponse(description="Not found"),
        },
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @extend_schema(
        summary="Create a new invoice",
        request=InvoiceSerializer,
        responses={
            201: InvoiceSerializer,
            400: OpenApiResponse(description="Validation error"),
        },
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @extend_schema(
        summary="Update an existing invoice",
        request=InvoiceSerializer,
        parameters=[OpenApiParameter("pk", int, description="Invoice ID")],
        responses={
            200: InvoiceSerializer,
            404: OpenApiResponse(description="Not found"),
        },
    )
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @extend_schema(
        summary="Delete an invoice",
        parameters=[OpenApiParameter("pk", int, description="Invoice ID")],
        responses={204: OpenApiResponse(description="Deleted")},
    )
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)
