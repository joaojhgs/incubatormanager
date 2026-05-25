"""Cold-start dashboard snapshots from upstream service APIs."""

from __future__ import annotations

from django.core.management.base import BaseCommand

from core.models import DashboardSnapshot
from core.views import METRIC_ENDPOINTS, _env_url, _fetch_json


class Command(BaseCommand):
    help = "Fetch upstream dashboard snapshot endpoints into dashboard snapshot storage."

    def add_arguments(self, parser) -> None:  # type: ignore[override]
        parser.add_argument(
            "--source",
            action="append",
            choices=tuple(METRIC_ENDPOINTS),
            help="Limit rebuild to one or more metric sources.",
        )

    def handle(self, *args: object, **options: object) -> None:
        sources = options.get("source") or list(METRIC_ENDPOINTS)
        headers = {"X-User-Id": "dashboard-rebuild", "X-User-Role": "Director"}
        fetched = 0
        failed = 0
        for source in sources:
            default_url = METRIC_ENDPOINTS[source]
            ok, payload = _fetch_json(
                _env_url("METRICS", source, default_url),
                headers,
                timeout=3.0,
            )
            if ok:
                DashboardSnapshot.objects.update_or_create(
                    source=source,
                    defaults={
                        "payload": payload if isinstance(payload, dict) else {"data": payload}
                    },
                )
                fetched += 1
            else:
                failed += 1
                self.stderr.write(f"{source}: {payload}")
        self.stdout.write(
            self.style.SUCCESS(f"dashboard_rebuild: fetched={fetched} failed={failed}")
        )
