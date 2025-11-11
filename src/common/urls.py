from django.urls import path
from common.views import CloudinarySignatureView

urlpatterns = [
    path('signature/', CloudinarySignatureView.as_view(), name='cloudinary-signature'),
]
