import logging
from typing import Any, Dict
from businesses.models import Business
from businesses.serializers import BusinessSerializer

logger = logging.getLogger(__name__)


class BusinessService:
    @staticmethod
    def create_business(data: Dict[str, Any], user) -> Business:
        logger.info(f"Creating business for user {user.email} with data: {data}")

        serializer = BusinessSerializer(data=data, context={"user": user})

        serializer.is_valid(raise_exception=True)

        business = serializer.save()

        logger.info(f"Business created: ID={business.id}, Email={business.email}")

        return business

    @staticmethod
    def update_business(business: Business, data: Dict[str, Any]) -> Business:
        serializer = BusinessSerializer(business, data=data, partial=True)

        serializer.is_valid(raise_exception=True)

        updated_business = serializer.save()

        logger.debug(f"Updated business ID={updated_business.id}")

        return updated_business

    @staticmethod
    def delete_business(business_id: int) -> None:
        business = Business.objects.get(id=business_id)
        business.delete()
        logger.info(f"Business deleted: ID={business_id}")

    @staticmethod
    def get_user_businesses(user_id: int):
        return Business.objects.filter(user_id=user_id).order_by("-created_at")

    @staticmethod
    def get_business_by_id(user_id: int, business_id: int) -> Business:
        return Business.objects.get(id=business_id, user_id=user_id)
