"""Unit tests for action calculations without a Home Assistant runtime."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
import importlib.util
from pathlib import Path
import unittest


SPEC = importlib.util.spec_from_file_location(
    "voltcast_helpers",
    Path(__file__).parents[1] / "custom_components" / "voltcast" / "helpers.py",
)
assert SPEC is not None and SPEC.loader is not None
HELPERS = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(HELPERS)


class ActionHelperTest(unittest.TestCase):
    def setUp(self) -> None:
        self.now = datetime(2026, 9, 1, 12, 0, tzinfo=timezone.utc)
        self.window = {
            "start": "2026-09-01T11:45:00Z",
            "end": "2026-09-01T13:45:00Z",
            "objective": "balanced",
        }

    def test_charge_now_uses_half_open_window(self) -> None:
        payload = {"optimization": {"data": [self.window]}}

        self.assertTrue(HELPERS.charge_now(payload, self.now))
        self.assertFalse(
            HELPERS.charge_now(
                payload,
                datetime(2026, 9, 1, 13, 45, tzinfo=timezone.utc),
            )
        )

    def test_recommended_window_is_absent_when_optional_api_failed(self) -> None:
        self.assertIsNone(
            HELPERS.recommended_window(
                {"optimization": {"data": [], "meta": {"available": False}}}
            )
        )

    def test_negative_risk_is_limited_to_next_24_hours(self) -> None:
        payload = {
            "risk": {
                "data": {
                    "curve": [
                        {
                            "target_start": "2026-09-01T16:00:00Z",
                            "p_negative": 0.65,
                        },
                        {
                            "target_start": "2026-09-02T13:00:00Z",
                            "p_negative": 0.90,
                        },
                    ]
                }
            }
        }

        result = HELPERS.negative_risk(
            payload,
            self.now,
            horizon=timedelta(hours=24),
        )

        self.assertTrue(result["incoming"])
        self.assertEqual(result["next_start"], "2026-09-01T16:00:00Z")
        self.assertEqual(result["max_probability"], 0.65)


if __name__ == "__main__":
    unittest.main()
