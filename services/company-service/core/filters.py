"""Query filters for company list API."""

from __future__ import annotations

import django_filters

from core.models import Company


class CompanyFilter(django_filters.FilterSet):
    """Filter queryset by CAE, maturity stage UUID, activity flag."""

    cae = django_filters.UUIDFilter(field_name="cae_id")
    maturity = django_filters.UUIDFilter(field_name="maturity_stage_id")
    is_active = django_filters.BooleanFilter(field_name="is_active")

    class Meta:
        model = Company
        fields = ()
