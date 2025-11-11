from django.urls import path
from common.views import CloudinarySignatureView

urlpatterns = [
    path('cloudinary/signature/', CloudinarySignatureView.as_view(), name='cloudinary-signature'),
]
