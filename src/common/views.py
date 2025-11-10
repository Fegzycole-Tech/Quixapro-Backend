"""Common utility views for the API."""

import logging
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiResponse

from common.cloudinary_service import CloudinaryService
from common.responses import success_response, error_response
from common.permissions import IsEmailVerified

logger = logging.getLogger(__name__)


class CloudinarySignatureView(APIView):
    permission_classes = [IsAuthenticated, IsEmailVerified]

    @extend_schema(
        tags=["Cloudinary"],
        summary="Generate Cloudinary upload signature",
        description=(
            "Generates a secure signature for uploading files to Cloudinary. "
            "The signature ensures that uploads are authenticated and follow your security rules. "
            "Use this signature on the frontend to upload files directly to Cloudinary."
        ),
        parameters=[
            OpenApiParameter(
                "folder",
                str,
                description="Cloudinary folder path (e.g., 'customer_photos', 'business_logos')",
                required=False,
            ),
            OpenApiParameter(
                "public_id",
                str,
                description="Custom public ID for the file (optional)",
                required=False,
            ),
            OpenApiParameter(
                "allowed_formats",
                str,
                description="Comma-separated list of allowed formats (e.g., 'jpg,png,pdf')",
                required=False,
            ),
            OpenApiParameter(
                "max_file_size",
                int,
                description="Maximum file size in bytes for client-side validation (default: 2097152 for 2MB). Note: This is not enforced by Cloudinary's signed upload.",
                required=False,
            ),
            OpenApiParameter(
                "tags",
                str,
                description="Comma-separated list of tags (e.g., 'customer,profile')",
                required=False,
            ),
        ],
        responses={
            200: OpenApiResponse(
                description="Signature generated successfully",
                response={
                    "type": "object",
                    "properties": {
                        "signature": {"type": "string"},
                        "timestamp": {"type": "integer"},
                        "cloud_name": {"type": "string"},
                        "api_key": {"type": "string"},
                        "folder": {"type": "string"},
                        "upload_url": {"type": "string"},
                    },
                },
            ),
            400: OpenApiResponse(description="Invalid parameters"),
            500: OpenApiResponse(description="Failed to generate signature"),
        },
    )
    def get(self, request):
        try:
            folder = request.query_params.get('folder')
            public_id = request.query_params.get('public_id')
            allowed_formats_str = request.query_params.get('allowed_formats')
            max_file_size_str = request.query_params.get('max_file_size')
            tags_str = request.query_params.get('tags')

            allowed_formats = None
            if allowed_formats_str:
                allowed_formats = [fmt.strip() for fmt in allowed_formats_str.split(',')]

            max_file_size = 2097152
            if max_file_size_str:
                try:
                    max_file_size = int(max_file_size_str)
                except ValueError:
                    return error_response(
                        detail="max_file_size must be a valid integer",
                        status_code=status.HTTP_400_BAD_REQUEST
                    )

            tags = None
            if tags_str:
                tags = [tag.strip() for tag in tags_str.split(',')]

            cloudinary_service = CloudinaryService()
            signature_data = cloudinary_service.generate_upload_signature(
                folder=folder,
                public_id=public_id,
                allowed_formats=allowed_formats,
                max_file_size=max_file_size,
                tags=tags
            )

            signature_data['upload_url'] = cloudinary_service.get_upload_url()

            logger.info(
                f"Generated Cloudinary signature for user {request.user.email}, "
                f"folder: {folder}"
            )

            return success_response(
                data=signature_data,
                message="Signature generated successfully"
            )

        except Exception as e:
            logger.error(f"Failed to generate Cloudinary signature: {str(e)}")
            return error_response(
                detail="Failed to generate upload signature",
                error_code="CLOUDINARY_SIGNATURE_ERROR",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
