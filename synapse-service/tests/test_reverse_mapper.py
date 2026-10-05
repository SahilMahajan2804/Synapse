import random

from app.core.config import Settings
from app.mapping.memory_store import InMemoryMappingStore
from app.reverse.mapper import DefaultReverseMapper


def test_restore_names_dates_and_digits() -> None:
    settings = Settings(date_shift_min=30, date_shift_max=180)
    store = InMemoryMappingStore(settings=settings, rng=random.Random(3))
    session = store.get_or_create("restore-session")
    session.by_original["PERSON:rahul sharma"] = type("M", (), {"type": "PERSON", "original": "Rahul Sharma", "surrogate": "Arjun Mehta", "score": 0.9})()
    session.by_original["PHONE_NUMBER:9876543210"] = type("M", (), {"type": "PHONE_NUMBER", "original": "+91 98765 43210", "surrogate": "+91 87412 60395", "score": 0.9})()
    session.by_original["DATE_TIME:03/08/2026"] = type("M", (), {"type": "DATE_TIME", "original": "03/08/2026", "surrogate": "19/09/2026", "score": 0.9})()

    mapper = DefaultReverseMapper()
    restored, count = mapper.restore("Mr. Arjun Mehta called on 19/09/2026 and +91 87412 60395.", session)

    assert "Mr. Rahul Sharma" in restored
    assert "03/08/2026" in restored
    assert "+91 98765 43210" in restored
    assert count >= 3


def test_known_only_keeps_unmapped_llm_dates() -> None:
    settings = Settings(reverse_date_mode="KNOWN_ONLY")
    store = InMemoryMappingStore(settings=settings, rng=random.Random(9))
    session = store.get_or_create("date-session")
    session.by_original["DATE_TIME:03/08/2026"] = type("M", (), {"type": "DATE_TIME", "original": "03/08/2026", "surrogate": "19/09/2026", "score": 0.9})()

    mapper = DefaultReverseMapper()
    restored, _ = mapper.restore("Discharged on 21/09/2026.", session)
    assert "21/09/2026" in restored
