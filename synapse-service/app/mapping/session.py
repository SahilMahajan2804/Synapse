import random
import re
import threading
from dataclasses import dataclass, field
from datetime import date, datetime, timezone

from app.core.config import Settings
from app.models.schemas import Mapping


@dataclass(slots=True)
class PersonAlias:
	orig_first: str
	orig_last: str
	orig_full: str
	sur_first: str
	sur_last: str
	sur_full: str


@dataclass
class SessionContext:
	session_id: str
	created_at: datetime
	day_offset: int
	by_original: dict[str, Mapping] = field(default_factory=dict)
	by_surrogate: dict[str, Mapping] = field(default_factory=dict)
	used_surrogates: set[str] = field(default_factory=set)
	persons: list[PersonAlias] = field(default_factory=list)
	date_map: dict[date, date] = field(default_factory=dict)
	type_counters: dict[str, int] = field(default_factory=dict)
	lock: threading.Lock = field(default_factory=threading.Lock)


def normalized_mapping_key(entity_type: str, value: str) -> str:
	normalized_type = entity_type.upper()
	if normalized_type in {"PHONE_NUMBER", "IN_AADHAAR"}:
		digits = re.sub(r"\D", "", value)
		if normalized_type == "PHONE_NUMBER" and digits.startswith("91") and len(digits) == 12:
			digits = digits[2:]
		elif normalized_type == "PHONE_NUMBER" and digits.startswith("0") and len(digits) == 11:
			digits = digits[1:]
		return f"{normalized_type}:{digits}"
	return f"{normalized_type}:{' '.join(value.split()).casefold()}"


def create_session_context(session_id: str, rng: random.Random, settings: Settings) -> SessionContext:
	shift_days = rng.randint(settings.date_shift_min, settings.date_shift_max)
	if rng.choice((False, True)):
		shift_days = -shift_days
	return SessionContext(
		session_id=session_id,
		created_at=datetime.now(timezone.utc),
		day_offset=shift_days,
	)