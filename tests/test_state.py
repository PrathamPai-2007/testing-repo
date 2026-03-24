import unittest
from types import SimpleNamespace
from unittest.mock import patch

import state
from services.auth_service import AuthenticatedUser


class FakeSessionState(dict):
    def __getattr__(self, name: str):
        try:
            return self[name]
        except KeyError as exc:
            raise AttributeError(name) from exc

    def __setattr__(self, name: str, value) -> None:
        self[name] = value


def _seed_session_state() -> FakeSessionState:
    return FakeSessionState(
        {
            "questions": [
                {
                    "question": "What is 2 + 2?",
                    "options": ["1", "2", "3", "4"],
                    "correct_answer": "4",
                }
            ],
            "answers": ["4"],
            "hints": ["Use addition."],
            "question_index": 0,
            "selected_option": "4",
            "submitted": True,
            "score": 4,
            "phase": "completed",
            "quiz_attempt_recorded": True,
            "is_generating": True,
            "pending_generation": {"count": 1},
            "generation_feedback": {"type": "success", "message": "done"},
            "is_generating_hint": True,
            "pending_hint_generation": {"question_index": 0},
            "hint_feedback": {"type": "success", "message": "ready"},
            "auth_user_id": "prior-user",
            "auth_user_email": "prior@example.com",
            "auth_is_admin": False,
            "auth_access_token": "old-access",
            "auth_refresh_token": "old-refresh",
            "auth_is_guest": False,
            "auth_view": "app",
            "app_screen": "history",
            "sidebar_default_applied": True,
        }
    )


class StateAuthBoundaryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.fake_st = SimpleNamespace(session_state=_seed_session_state())
        self.streamlit_patch = patch.object(state, "st", self.fake_st)
        self.streamlit_patch.start()

    def tearDown(self) -> None:
        self.streamlit_patch.stop()

    def test_clear_auth_state_resets_auth_bound_quiz_state(self) -> None:
        state.clear_auth_state()

        self.assertEqual(self.fake_st.session_state.questions, [])
        self.assertEqual(self.fake_st.session_state.answers, [])
        self.assertEqual(self.fake_st.session_state.hints, [])
        self.assertEqual(self.fake_st.session_state.phase, "setup")
        self.assertEqual(self.fake_st.session_state.score, 0)
        self.assertFalse(self.fake_st.session_state.quiz_attempt_recorded)
        self.assertFalse(self.fake_st.session_state.is_generating)
        self.assertIsNone(self.fake_st.session_state.pending_generation)
        self.assertFalse(self.fake_st.session_state.is_generating_hint)
        self.assertIsNone(self.fake_st.session_state.pending_hint_generation)
        self.assertIsNone(self.fake_st.session_state.auth_user_id)
        self.assertIsNone(self.fake_st.session_state.auth_access_token)
        self.assertEqual(self.fake_st.session_state.auth_view, "login")
        self.assertEqual(self.fake_st.session_state.app_screen, "quiz")

    def test_log_in_user_resets_quiz_state_for_new_identity(self) -> None:
        new_user = AuthenticatedUser(
            id="new-user",
            email="new@example.com",
            is_admin=False,
            access_token="new-access",
            refresh_token="new-refresh",
        )

        state.log_in_user(new_user)

        self.assertEqual(self.fake_st.session_state.questions, [])
        self.assertEqual(self.fake_st.session_state.answers, [])
        self.assertEqual(self.fake_st.session_state.hints, [])
        self.assertEqual(self.fake_st.session_state.phase, "setup")
        self.assertEqual(self.fake_st.session_state.auth_user_id, "new-user")
        self.assertEqual(self.fake_st.session_state.auth_user_email, "new@example.com")
        self.assertFalse(self.fake_st.session_state.auth_is_guest)
        self.assertEqual(self.fake_st.session_state.app_screen, "quiz")
        self.assertFalse(self.fake_st.session_state.sidebar_default_applied)

    def test_sync_authenticated_user_preserves_quiz_state_for_same_identity(self) -> None:
        same_user = AuthenticatedUser(
            id="prior-user",
            email="prior@example.com",
            is_admin=False,
            access_token="refreshed-access",
            refresh_token="refreshed-refresh",
        )

        state.sync_authenticated_user(same_user)

        self.assertEqual(len(self.fake_st.session_state.questions), 1)
        self.assertEqual(self.fake_st.session_state.answers, ["4"])
        self.assertEqual(self.fake_st.session_state.hints, ["Use addition."])
        self.assertEqual(self.fake_st.session_state.phase, "completed")
        self.assertEqual(self.fake_st.session_state.score, 4)
        self.assertEqual(self.fake_st.session_state.auth_access_token, "refreshed-access")
        self.assertEqual(self.fake_st.session_state.auth_refresh_token, "refreshed-refresh")
        self.assertEqual(self.fake_st.session_state.app_screen, "history")

    def test_log_in_guest_user_resets_previous_authenticated_state(self) -> None:
        state.log_in_guest_user()

        self.assertEqual(self.fake_st.session_state.questions, [])
        self.assertEqual(self.fake_st.session_state.answers, [])
        self.assertEqual(self.fake_st.session_state.hints, [])
        self.assertEqual(self.fake_st.session_state.phase, "setup")
        self.assertTrue(self.fake_st.session_state.auth_is_guest)
        self.assertEqual(self.fake_st.session_state.auth_user_email, "Guest")
        self.assertEqual(self.fake_st.session_state.app_screen, "quiz")
        self.assertFalse(self.fake_st.session_state.sidebar_default_applied)


if __name__ == "__main__":
    unittest.main()
