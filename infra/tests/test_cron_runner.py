from __future__ import annotations

import importlib.util
import sys
from datetime import datetime
from pathlib import Path

MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "cron-runner.py"
spec = importlib.util.spec_from_file_location("cron_runner", MODULE_PATH)
assert spec is not None and spec.loader is not None
cron_runner = importlib.util.module_from_spec(spec)
sys.modules["cron_runner"] = cron_runner
spec.loader.exec_module(cron_runner)


def test_parse_crontab_ignores_comments_and_splits_commands(tmp_path: Path) -> None:
    crontab = tmp_path / "jobs.crontab"
    crontab.write_text(
        "# comment\n"
        "0 2 1 * * python manage.py generate_monthly_billing --as-of 2026-05-01\n"
    )

    entries = cron_runner.parse_crontab(crontab)

    assert len(entries) == 1
    assert entries[0].minute == "0"
    assert entries[0].hour == "2"
    assert entries[0].command == (
        "python",
        "manage.py",
        "generate_monthly_billing",
        "--as-of",
        "2026-05-01",
    )


def test_due_entries_matches_expected_schedule(tmp_path: Path) -> None:
    crontab = tmp_path / "jobs.crontab"
    crontab.write_text("0 2 1 * * python manage.py generate_monthly_billing\n")
    entries = cron_runner.parse_crontab(crontab)

    assert cron_runner.due_entries(entries, datetime(2026, 5, 1, 2, 0)) == entries
    assert cron_runner.due_entries(entries, datetime(2026, 5, 1, 2, 1)) == []
    assert cron_runner.due_entries(entries, datetime(2026, 5, 2, 2, 0)) == []


def test_parse_project_crontabs_are_valid() -> None:
    cron_dir = Path(__file__).resolve().parents[1] / "cron"
    for crontab in ("booking.crontab", "contract.crontab", "finance.crontab"):
        entries = cron_runner.parse_crontab(cron_dir / crontab)
        assert entries, crontab
        assert all(entry.command[:2] == ("python", "manage.py") for entry in entries)
