import asyncio
import unittest

from academic_hub.clients.telegram.session import load_session, save_session
from academic_hub.domain.models import RetryRequest, TelegramSession


class FakeState:
    def __init__(self, data=None) -> None:
        self.data = dict(data or {})

    async def get_data(self):
        return dict(self.data)

    async def update_data(self, **kwargs):
        self.data.update(kwargs)
        return dict(self.data)


class SessionTests(unittest.TestCase):
    def test_load_session_recovers_from_invalid_payload(self) -> None:
        state = FakeState({"session": "broken"})

        session = asyncio.run(load_session(state))

        self.assertEqual(session.level, "home")
        self.assertIsInstance(state.data.get("session"), dict)
        self.assertEqual(state.data["session"]["level"], "home")

    def test_save_session_round_trips_retry_request(self) -> None:
        state = FakeState()
        original = TelegramSession(
            level="course",
            quarter=2,
            course_id="physics_ii",
            section="week_category",
            week_number=3,
            retry_request=RetryRequest(
                scope="week",
                course_id="physics_ii",
                category_slug="lecture_notes",
                week_number=3,
                failed_paths=("C:\\tmp\\Week 3 Notes.pdf",),
            ),
        )

        asyncio.run(save_session(state, original))
        loaded = asyncio.run(load_session(state))

        self.assertIsNotNone(loaded.retry_request)
        assert loaded.retry_request is not None
        self.assertEqual(loaded.retry_request.scope, "week")
        self.assertEqual(loaded.retry_request.failed_paths, ("C:/tmp/Week 3 Notes.pdf",))
