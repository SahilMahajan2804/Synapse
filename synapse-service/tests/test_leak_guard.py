import random
from datetime import datetime, timezone

from app.core.config import Settings
from app.guard.leak_guard import LeakGuardResult, LeakGuard
from app.mapping.memory_store import InMemoryMappingStore
from app.mapping.session import SessionContext


def test_clean_and_detected_values() -> None:
    guard = LeakGuard()
    clean = guard.check("The patient is stable.", ["Rahul", "9876543210"])
    assert clean.passed is True
    assert clean.leaked_count == 0

    leak = guard.check("RAHUL SHARMA and +91 98765 43210", ["RAHUL SHARMA", "+91 98765 43210", "xy"])
    assert leak.passed is False
    assert leak.leaked_count == 2
    assert "RAHUL SHARMA" in leak.leaked_values or any(v.casefold() == "rahul sharma" for v in leak.leaked_values)
    assert any(v.startswith("+91") or "98765" in v for v in leak.leaked_values)

    small = guard.check("Rahul and Priya", ["Ra", "Pi"])
    assert small.passed is True
    assert small.leaked_count == 0


def test_guard_ignores_non_originals_and_accepts_session_context() -> None:
    settings = Settings(date_shift_min=30, date_shift_max=180)
    store = InMemoryMappingStore(settings=settings, rng=random.Random(7))
    session = store.get_or_create("session-guard")
    assert isinstance(session, SessionContext)
    assert session.created_at.tzinfo == timezone.utc

    guard = LeakGuard()
    text = "The patient is Rahul Sharma and his phone is +91 98765 43210."
    result = guard.check(text, ["Rahul Sharma", "+91 98765 43210"])
    assert result.passed is False
    assert result.leaked_count == 2


LeakGuardResult
