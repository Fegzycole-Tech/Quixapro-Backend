import logging
import time
from typing import Dict, Any, Optional
from django.conf import settings
import cloudinary
import cloudinary.uploader

logger = logging.getLogger(__name__)


class CloudinaryService:
    def __init__(self):
        self.cloud_name = settings.CLOUDINARY_CLOUD_NAME
        self.api_key = settings.CLOUDINARY_API_KEY
        self.api_secret = settings.CLOUDINARY_API_SECRET

        cloudinary.config(
            cloud_name=self.cloud_name,
            api_key=self.api_key,
            api_secret=self.api_secret,
            secure=True
        )

    def generate_upload_signature(
        self,
        folder: Optional[str] = None,
        public_id: Optional[str] = None,
        allowed_formats: Optional[list] = None,
        max_file_size: Optional[int] = None,
        tags: Optional[list] = None
    ) -> Dict[str, Any]:
        timestamp = int(time.time())

        params = {
            'timestamp': timestamp
        }

        if folder:
            params['folder'] = folder

        if public_id:
            params['public_id'] = public_id

        if allowed_formats:
            params['allowed_formats'] = ','.join(allowed_formats)

        if tags:
            params['tags'] = ','.join(tags)

        signature = cloudinary.utils.api_sign_request(
            params,
            self.api_secret
        )

        logger.info(f"Generated upload signature for folder: {folder}")

        return {
            'signature': signature,
            'timestamp': timestamp,
            'cloud_name': self.cloud_name,
            'api_key': self.api_key,
            'folder': folder,
            'allowed_formats': allowed_formats,
            'max_file_size': max_file_size,
            'tags': tags
        }

    def delete_resource(self, public_id: str, resource_type: str = 'image') -> Dict[str, Any]:
        try:
            result = cloudinary.uploader.destroy(public_id, resource_type=resource_type)
            logger.info(f"Deleted resource: {public_id}")
            return result
        except Exception as e:
            logger.error(f"Failed to delete resource {public_id}: {str(e)}")
            raise

    def get_upload_url(self) -> str:
        return f"https://api.cloudinary.com/v1_1/{self.cloud_name}/image/upload"
