import unittest

from main import (
    LAST_ONLINE_SYNC_INTERVAL_SECONDS,
    build_auth_token_key,
    should_restore_authenticated_user,
    should_touch_last_online,
)


class MainPerformanceHelperTests(unittest.TestCase):
    def test_build_auth_token_key_requires_both_tokens(self) -> None:
        self.assertIsNone(build_auth_token_key("access-only", ""))
        self.assertIsNone(build_auth_token_key("", "refresh-only"))
        self.assertEqual(
            build_auth_token_key(" access-token ", " refresh-token "),
            "access-token:refresh-token",
        )

    def test_should_restore_authenticated_user_when_tokens_change(self) -> None:
        self.assertTrue(
            should_restore_authenticated_user(
                token_key="new-access:new-refresh",
                restored_token_key="old-access:old-refresh",
                is_authenticated_user=True,
            )
        )

    def test_should_not_restore_authenticated_user_for_same_tokens_and_active_auth(self) -> None:
        self.assertFalse(
            should_restore_authenticated_user(
                token_key="same-access:same-refresh",
                restored_token_key="same-access:same-refresh",
                is_authenticated_user=True,
            )
        )

    def test_should_restore_authenticated_user_when_auth_state_is_missing(self) -> None:
        self.assertTrue(
            should_restore_authenticated_user(
                token_key="same-access:same-refresh",
                restored_token_key="same-access:same-refresh",
                is_authenticated_user=False,
            )
        )

    def test_should_touch_last_online_when_never_synced_or_tokens_change(self) -> None:
        self.assertTrue(
            should_touch_last_online(
                token_key="access:refresh",
                last_synced_token_key=None,
                last_synced_at=None,
                now_ts=100.0,
            )
        )
        self.assertTrue(
            should_touch_last_online(
                token_key="new-access:new-refresh",
                last_synced_token_key="old-access:old-refresh",
                last_synced_at=100.0,
                now_ts=101.0,
            )
        )

    def test_should_throttle_last_online_until_interval_passes(self) -> None:
        self.assertFalse(
            should_touch_last_online(
                token_key="access:refresh",
                last_synced_token_key="access:refresh",
                last_synced_at=100.0,
                now_ts=100.0 + LAST_ONLINE_SYNC_INTERVAL_SECONDS - 1.0,
            )
        )
        self.assertTrue(
            should_touch_last_online(
                token_key="access:refresh",
                last_synced_token_key="access:refresh",
                last_synced_at=100.0,
                now_ts=100.0 + LAST_ONLINE_SYNC_INTERVAL_SECONDS,
            )
        )


if __name__ == "__main__":
    unittest.main()
