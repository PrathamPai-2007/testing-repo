import unittest
from unittest.mock import patch

from services.admin_service import fetch_all_user_overviews
from services.auth_service import create_user, increment_generated_quiz_count, touch_user_last_online
from tests.fake_supabase import FakeSupabaseClient


class AdminServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.fake_client = FakeSupabaseClient()
        self.create_client_patch = patch("services.auth_service.create_supabase_client", return_value=self.fake_client)
        self.create_client_patch.start()

    def tearDown(self) -> None:
        self.create_client_patch.stop()

    def test_user_overview_includes_generated_count_and_last_online(self) -> None:
        admin_user = create_user(
            email="admin@example.com",
            password="AdminPass123",
        )
        self.fake_client.table("profiles").update({"is_admin": True}).eq("id", admin_user.id).execute()

        regular_user = create_user(
            email="quiz_user@example.com",
            password="Password123",
        )
        increment_generated_quiz_count(
            user_id=regular_user.id,
            access_token=regular_user.access_token,
            refresh_token=regular_user.refresh_token,
        )
        increment_generated_quiz_count(
            user_id=regular_user.id,
            access_token=regular_user.access_token,
            refresh_token=regular_user.refresh_token,
        )
        touch_user_last_online(
            user_id=regular_user.id,
            access_token=regular_user.access_token,
            refresh_token=regular_user.refresh_token,
        )

        user_overviews = fetch_all_user_overviews(
            access_token=admin_user.access_token,
            refresh_token=admin_user.refresh_token,
        )

        self.assertEqual(len(user_overviews), 2)
        matching_user = next(user for user in user_overviews if user.email == "quiz_user@example.com")
        self.assertEqual(matching_user.generated_quiz_count, 2)
        self.assertIsNotNone(matching_user.last_online_at_iso)
        self.assertFalse(matching_user.is_admin)


if __name__ == "__main__":
    unittest.main()
