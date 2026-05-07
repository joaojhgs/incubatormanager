"""Maturity stage API — list/detail for any authenticated user; writes Director-only."""

from __future__ import annotations

from drf_spectacular.utils import extend_schema, extend_schema_view
from ilb_common.permissions import IsDirector
from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ModelViewSet

from core.models import MaturityStage
from core.serializers import MaturityStageSerializer


@extend_schema_view(
    list=extend_schema(description="List maturity stages. Any authenticated role."),
    retrieve=extend_schema(description="Retrieve one maturity stage. Any authenticated role."),
    create=extend_schema(description="Create a maturity stage. Director only."),
    partial_update=extend_schema(description="Partially update a maturity stage. Director only."),
)
class MaturityStageViewSet(ModelViewSet):
    queryset = MaturityStage.objects.all()
    serializer_class = MaturityStageSerializer
    http_method_names = ["get", "post", "head", "options", "patch"]
    # No PUT (full replace) or DELETE — task scope is GET + POST + PATCH only.

    def get_permissions(self):  # type: ignore[override]
        if self.action in {"create", "partial_update", "update"}:
            return [IsAuthenticated(), IsDirector()]
        return [IsAuthenticated()]
