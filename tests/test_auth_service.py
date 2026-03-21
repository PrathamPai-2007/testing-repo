import unittest
from unittest.mock import patch

from services.auth_service import (
    authenticate_user,
    create_user,
    increment_generated_quiz_count,
    restore_authenticated_user,
    sign_out_user,
    touch_user_last_online,
    validate_email,
    validate_password,
)
from tests.fake_supabase import FakeSupabaseClient


class AuthServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.fake_client = FakeSupabaseClient()
        self.create_client_patch = patch("services.auth_service.create_supabase_client", return_value=self.fake_client)
        self.create_client_patch.start()

    def tearDown(self) -> None:
        self.create_client_patch.stop()

    def test_validate_email_rejects_invalid_email(self) -> None:
        with self.assertRaisesRegex(ValueError, "valid email"):
            validate_email("not-an-email")

    def test_validate_password_rejects_short_password(self) -> None:
        with self.assertRaisesRegex(ValueError, "at least 8 characters"):
            validate_password("short")

    def test_create_user_and_authenticate_successfully(self) -> None:
        created_user = create_user(
            email="quiz_master@example.com",
            password="supersecret123",
        )
        authenticated_user = authenticate_user(
            email="quiz_master@example.com",
            password="supersecret123",
        )

        self.assertEqual(created_user.email, "quiz_master@example.com")
        self.assertFalse(created_user.is_admin)
        self.assertIsNotNone(authenticated_user)
        self.assertEqual(authenticated_user.email, "quiz_master@example.com")  # type: ignore[union-attr]

    def test_duplicate_email_is_rejected(self) -> None:
        create_user(
            email="quiz_master@example.com",
            password="supersecret123",
        )

        with self.assertRaisesRegex(ValueError, "already registered"):
            create_user(
                email="quiz_master@example.com",
                password="anothersecret123",
            )

    def test_authentication_fails_with_wrong_password(self) -> None:
        create_user(
            email="quiz_master@example.com",
            password="supersecret123",
        )

        authenticated_user = authenticate_user(
            email="quiz_master@example.com",
            password="wrong-password",
        )

        self.assertIsNone(authenticated_user)

    def test_restore_authenticated_user_returns_user_for_valid_tokens(self) -> None:
        created_user = create_user(
            email="quiz_master@example.com",
            password="supersecret123",
        )

        restored_user = restore_authenticated_user(
            access_token=created_user.access_token,
            refresh_token=created_user.refresh_token,
        )

        self.assertIsNotNone(restored_user)
        self.assertEqual(restored_user.email, "quiz_master@example.com")  # type: ignore[union-attr]

    def test_sign_out_invalidates_existing_session(self) -> None:
        created_user = create_user(
            email="quiz_master@example.com",
            password="supersecret123",
        )

        sign_out_user(
            access_token=created_user.access_token,
            refresh_token=created_user.refresh_token,
        )

        restored_user = restore_authenticated_user(
            access_token=created_user.access_token,
            refresh_token=created_user.refresh_token,
        )

        self.assertIsNone(restored_user)

    def test_increment_generated_quiz_count_and_touch_last_online_update_profile(self) -> None:
        created_user = create_user(
            email="quiz_master@example.com",
            password="supersecret123",
        )

        increment_generated_quiz_count(
            user_id=created_user.id,
            access_token=created_user.access_token,
            refresh_token=created_user.refresh_token,
        )
        touch_user_last_online(
            user_id=created_user.id,
            access_token=created_user.access_token,
            refresh_token=created_user.refresh_token,
        )

        profile_row = self.fake_client.table("profiles").select("*").eq("id", created_user.id).limit(1).execute().data[0]
        self.assertEqual(profile_row["generated_quiz_count"], 1)
        self.assertIsNotNone(profile_row["last_online_at"])


if __name__ == "__main__":
    unittest.main()
