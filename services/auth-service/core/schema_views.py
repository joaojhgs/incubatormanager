"""OpenAPI UI views with schema generation enabled (base class excludes them)."""

from __future__ import annotations

from drf_spectacular.utils import OpenApiResponse, extend_schema
from drf_spectacular.views import SpectacularSwaggerView


class AuthSpectacularSwaggerView(SpectacularSwaggerView):
    """Same as ``SpectacularSwaggerView`` but listed in ``schema.yml`` for consumers."""

    @extend_schema(
        summary="Swagger UI",
        description="Interactive OpenAPI documentation for the auth service.",
        responses={
            200: OpenApiResponse(
                description="Swagger UI page (HTML).",
            ),
        },
    )
    def get(self, request, *args, **kwargs):  # type: ignore[no-untyped-def]
        return super().get(request, *args, **kwargs)
