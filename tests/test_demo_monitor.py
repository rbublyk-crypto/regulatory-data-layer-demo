from datetime import date
import unittest

from demo_monitor import DisclosureRecord, compare_snapshots, latest_snapshot


def record(source: str, percent: float, day: int = 22) -> DisclosureRecord:
    return DisclosureRecord(source, "FR0000000001", "Northstar", percent, date(2026, 9, day), "https://example.invalid")


class MonitorTests(unittest.TestCase):
    def test_latest_snapshot_uses_newest_lifecycle_record(self) -> None:
        snapshot = latest_snapshot([record("demo_fr", 0.58, 20), record("demo_fr", 0.72, 22)])
        self.assertEqual(snapshot[("demo_fr", "FR0000000001", "Northstar")].short_percent, 0.72)

    def test_first_snapshot_emits_baseline(self) -> None:
        events = compare_snapshots(None, latest_snapshot([record("demo_fr", 0.58)]))
        self.assertEqual(events[0]["eventType"], "BASELINE_POSITION")

    def test_failed_source_does_not_emit_closure(self) -> None:
        previous = latest_snapshot([record("demo_fr", 0.58)])
        events = compare_snapshots(previous, {}, failed_sources={"demo_fr"})
        self.assertEqual(events, [])

    def test_successful_absence_emits_public_disclosure_closure(self) -> None:
        previous = latest_snapshot([record("demo_fr", 0.58)])
        events = compare_snapshots(previous, {})
        self.assertEqual(events[0]["eventType"], "POSITION_CLOSED")

    def test_percentage_change_is_directional(self) -> None:
        previous = latest_snapshot([record("demo_fr", 0.58)])
        current = latest_snapshot([record("demo_fr", 0.72)])
        events = compare_snapshots(previous, current)
        self.assertEqual(events[0]["eventType"], "POSITION_INCREASED")


if __name__ == "__main__":
    unittest.main()
