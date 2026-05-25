#!/usr/bin/env python3
"""Tiny cron-compatible runner for Django scheduler sidecars.

The project intentionally avoids Celery. This runner lets compose scheduler
containers execute checked-in crontab files without requiring a host cron daemon
or extra Python dependencies.
"""

from __future__ import annotations

import argparse
import dataclasses
import os
import shlex
import subprocess
import sys
import time
from collections.abc import Iterable
from datetime import datetime
from pathlib import Path


@dataclasses.dataclass(frozen=True)
class CronEntry:
    minute: str
    hour: str
    day: str
    month: str
    weekday: str
    command: tuple[str, ...]
    source_line: int

    @property
    def display_command(self) -> str:
        return " ".join(shlex.quote(part) for part in self.command)


def _matches_field(expression: str, value: int) -> bool:
    """Return whether one simple cron field matches the current value."""
    for part in expression.split(","):
        part = part.strip()
        if part == "*":
            return True
        if part.startswith("*/"):
            step = int(part[2:])
            if step > 0 and value % step == 0:
                return True
            continue
        if "-" in part:
            start, end = (int(piece) for piece in part.split("-", 1))
            if start <= value <= end:
                return True
            continue
        if part and int(part) == value:
            return True
    return False


def _cron_weekday(now: datetime) -> int:
    """Return cron weekday where Sunday can be 0."""
    return (now.weekday() + 1) % 7


def parse_crontab(path: Path) -> list[CronEntry]:
    entries: list[CronEntry] = []
    for line_no, raw_line in enumerate(path.read_text().splitlines(), start=1):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        fields = line.split(maxsplit=5)
        if len(fields) != 6:
            raise ValueError(f"{path}:{line_no}: expected 5 schedule fields plus command")
        command = tuple(shlex.split(fields[5]))
        if not command:
            raise ValueError(f"{path}:{line_no}: command cannot be empty")
        entries.append(CronEntry(*fields[:5], command=command, source_line=line_no))
    return entries


def due_entries(entries: Iterable[CronEntry], now: datetime) -> list[CronEntry]:
    return [
        entry
        for entry in entries
        if _matches_field(entry.minute, now.minute)
        and _matches_field(entry.hour, now.hour)
        and _matches_field(entry.day, now.day)
        and _matches_field(entry.month, now.month)
        and _matches_field(entry.weekday, _cron_weekday(now))
    ]


def run_entry(entry: CronEntry) -> int:
    print(f"cron-runner: running line {entry.source_line}: {entry.display_command}", flush=True)
    completed = subprocess.run(entry.command, check=False)  # noqa: S603
    print(
        f"cron-runner: line {entry.source_line} exited {completed.returncode}: "
        f"{entry.display_command}",
        flush=True,
    )
    return completed.returncode


def sleep_to_next_minute() -> None:
    now = time.time()
    time.sleep(max(1.0, 60.0 - (now % 60.0)))


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Run commands from a simple cron file")
    parser.add_argument("crontab", type=Path)
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="parse and print jobs without looping",
    )
    args = parser.parse_args(argv)

    entries = parse_crontab(args.crontab)
    if not entries:
        raise SystemExit(f"cron-runner: no jobs found in {args.crontab}")

    print(f"cron-runner: loaded {len(entries)} job(s) from {args.crontab}", flush=True)
    for entry in entries:
        print(f"cron-runner: job line {entry.source_line}: {entry.display_command}", flush=True)

    if args.dry_run:
        return 0

    if os.environ.get("CRON_RUN_ON_START", "").lower() in {"1", "true", "yes"}:
        for entry in entries:
            run_entry(entry)

    while True:
        now = datetime.now().replace(second=0, microsecond=0).astimezone()
        for entry in due_entries(entries, now):
            run_entry(entry)
        sleep_to_next_minute()


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
