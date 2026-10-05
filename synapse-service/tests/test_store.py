import random

from app.core.config import Settings
from app.mapping.memory_store import InMemoryMappingStore


class FakeClock:
	def __init__(self) -> None:
		self.now = 0.0

	def __call__(self) -> float:
		return self.now


def test_store_reuses_sessions_creates_ids_and_deletes() -> None:
	store = InMemoryMappingStore(settings=Settings(max_sessions=3), rng=random.Random(4))
	session = store.get_or_create("session-1")

	assert store.get_or_create("session-1") is session
	assert store.get_or_create(None).session_id
	assert store.get_or_create("   ").session_id
	assert store.delete("session-1")
	assert store.find("session-1") is None
	assert not store.delete("session-1")


def test_store_expires_sessions_using_injected_timer() -> None:
	clock = FakeClock()
	settings = Settings(session_ttl_seconds=10, max_sessions=2)
	store = InMemoryMappingStore(settings=settings, rng=random.Random(5), timer=clock)
	session = store.get_or_create("expires")
	clock.now = 11

	assert store.find("expires") is None
	assert store.get_or_create("expires") is not session


def test_session_day_offset_is_nonzero_and_within_configured_bounds() -> None:
	settings = Settings(date_shift_min=30, date_shift_max=180)
	store = InMemoryMappingStore(settings=settings, rng=random.Random(6))
	day_offset = store.get_or_create("date-session").day_offset

	assert 30 <= abs(day_offset) <= 180