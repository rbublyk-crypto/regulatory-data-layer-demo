"""Deterministic portfolio demo for a stateful disclosure-change monitor.

The module consumes only in-memory fixture records. It deliberately has no network
or production-source adapter code.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Iterable


@dataclass(frozen=True)
class DisclosureRecord:
    source: str
    isin: str
    holder: str
    short_percent: float
    effective_date: date
    source_url: str

    @property
    def identity(self) -> tuple[str, str, str]:
        return (self.source, self.isin, self.holder)


def latest_snapshot(records: Iterable[DisclosureRecord]) -> dict[tuple[str, str, str], DisclosureRecord]:
    """Return the latest source row for each stable public-disclosure identity."""
    snapshot: dict[tuple[str, str, str], DisclosureRecord] = {}
    for record in records:
        existing = snapshot.get(record.identity)
        if existing is None or record.effective_date > existing.effective_date:
            snapshot[record.identity] = record
    return snapshot


def compare_snapshots(
    previous: dict[tuple[str, str, str], DisclosureRecord] | None,
    current: dict[tuple[str, str, str], DisclosureRecord],
    failed_sources: set[str] | None = None,
) -> list[dict[str, object]]:
    """Emit deterministic events; failed sources retain prior state and cannot close positions."""
    failed_sources = failed_sources or set()
    if previous is None:
        return [_event("BASELINE_POSITION", record) for record in _sorted(current.values())]

    events: list[dict[str, object]] = []
    identities = sorted(set(previous) | set(current))
    for identity in identities:
        old, new = previous.get(identity), current.get(identity)
        source = identity[0]

        if old is None and new is not None:
            events.append(_event("NEW_POSITION", new))
        elif old is not None and new is None:
            if source not in failed_sources:
                events.append(_event("POSITION_CLOSED", old))
        elif old is not None and new is not None:
            if new.short_percent > old.short_percent:
                events.append(_event("POSITION_INCREASED", new, old))
            elif new.short_percent < old.short_percent:
                events.append(_event("POSITION_DECREASED", new, old))
            elif new.effective_date != old.effective_date:
                events.append(_event("SOURCE_CORRECTION", new, old))
            else:
                events.append(_event("UNCHANGED", new, old))
    return events


def _event(event_type: str, record: DisclosureRecord, previous: DisclosureRecord | None = None) -> dict[str, object]:
    return {
        "eventType": event_type,
        "positionIdentity": "|".join(record.identity),
        "source": record.source,
        "isin": record.isin,
        "holder": record.holder,
        "shortPercent": record.short_percent,
        "previousShortPercent": previous.short_percent if previous else None,
        "effectiveDate": record.effective_date.isoformat(),
        "sourceUrl": record.source_url,
    }


def _sorted(records: Iterable[DisclosureRecord]) -> list[DisclosureRecord]:
    return sorted(records, key=lambda record: record.identity)


def demo_records() -> list[DisclosureRecord]:
    """A lifecycle-style source contains two rows for the same public position."""
    return [
        DisclosureRecord("demo_fr", "FR0000000001", "Northstar Capital", 0.58, date(2026, 9, 20), "https://example.invalid/fr/1"),
        DisclosureRecord("demo_fr", "FR0000000001", "Northstar Capital", 0.72, date(2026, 9, 22), "https://example.invalid/fr/2"),
        DisclosureRecord("demo_no", "NO0000000002", "Orion Partners", 0.61, date(2026, 9, 22), "https://example.invalid/no/1"),
    ]


if __name__ == "__main__":
    import json

    baseline = latest_snapshot(demo_records())
    print(json.dumps(compare_snapshots(None, baseline), indent=2))
