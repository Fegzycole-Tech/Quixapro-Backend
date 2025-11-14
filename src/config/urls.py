from django.contrib import admin
from django.urls import path, include
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
    SpectacularRedocView,
)

urlpatterns = [
    path("admin/", admin.site.urls),
    path("schema/", SpectacularAPIView.as_view(), name="schema"),
    path("docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
    path("auth/", include("users.auth_urls")),
    path("users/", include("users.user_urls")),
    path("customers/", include("customers.urls")),
    path("businesses/", include("businesses.urls")),
    path("invoices/", include("invoices.urls")),
    path("cloudinary/", include("common.urls")),
]
