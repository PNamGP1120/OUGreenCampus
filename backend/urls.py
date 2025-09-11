from django.contrib import admin
from django.urls import path, include
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

# Admin tùy biến
from OUGreenApp.admin import admin_site

schema_view = get_schema_view(
    openapi.Info(
        title="OU Green Campus API",
        default_version="v1",
        description="API documentation for OU Green Campus project",
    ),
    public=True,
    permission_classes=[permissions.AllowAny],
)

urlpatterns = [
    # Admin mặc định của Django
    path("django-admin/", admin.site.urls),

    # Admin tùy biến OU Green Campus
    path("admin/", admin_site.urls),

    # API
    path("api/", include("OUGreenApp.urls")),

    # Swagger docs
    path("docs/", schema_view.with_ui("swagger", cache_timeout=0), name="schema-swagger-ui"),
]
