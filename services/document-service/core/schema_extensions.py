"""drf-spectacular extensions for this service."""

from __future__ import annotations

from drf_spectacular.extensions import OpenApiAuthenticationExtension


class GatewayHeaderAuthenticationExtension(OpenApiAuthenticationExtension):
    """Maps :class:`ilb_common.permissions.HeaderAuthentication` to OpenAPI security."""

    target_class = "ilb_common.permissions.HeaderAuthentication"
    name = "GatewayJWT"

    def get_security_definition(self, auto_schema: object) -> dict[str, str]:
        return {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
            "description": (
                "JWT validated by the gateway; upstream requests include "
                "X-User-Id, X-User-Role, and optionally X-Company-Id."
            ),
        }
