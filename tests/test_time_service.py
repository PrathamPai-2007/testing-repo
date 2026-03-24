import unittest
from zoneinfo import ZoneInfo

from services.time_service import format_timestamp_local


class TimeServiceTests(unittest.TestCase):
    def test_format_timestamp_local_converts_utc_to_target_timezone(self) -> None:
        formatted = format_timestamp_local(
            "2026-03-24T15:00:00+00:00",
            target_tz=ZoneInfo("Asia/Kolkata"),
        )

        self.assertEqual(formatted, "24 Mar 2026, 08:30 PM")

    def test_format_timestamp_local_handles_z_suffix(self) -> None:
        formatted = format_timestamp_local(
            "2026-03-24T15:00:00Z",
            target_tz=ZoneInfo("Asia/Kolkata"),
        )

        self.assertEqual(formatted, "24 Mar 2026, 08:30 PM")

    def test_format_timestamp_local_returns_input_for_invalid_values(self) -> None:
        self.assertEqual(format_timestamp_local("not-a-timestamp"), "not-a-timestamp")
        self.assertEqual(format_timestamp_local(None), "Never")


if __name__ == "__main__":
    unittest.main()
