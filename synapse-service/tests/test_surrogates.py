import random
import re
from datetime import datetime

from app.core.config import Settings
from app.detection.verhoeff import is_valid
from app.mapping.memory_store import InMemoryMappingStore
from app.models.schemas import DetectedEntity
from app.surrogate.engine import RuleBasedSurrogateGenerator


def entity(text: str, source: str, value: str, entity_type: str) -> DetectedEntity:
	start = text.index(value, source.index(value) if value in source else 0)
	return DetectedEntity(
		type=entity_type,
		start=start,
		end=start + len(value),
		utf16_start=0,
		utf16_end=0,
		text=value,
		score=0.9,
		source="regex",
	)


def find_entity(text: str, value: str, entity_type: str) -> DetectedEntity:
	start = text.index(value)
	return DetectedEntity(
		type=entity_type,
		start=start,
		end=start + len(value),
		utf16_start=0,
		utf16_end=0,
		text=value,
		score=0.9,
		source="regex",
	)


def setup_session(seed: int = 11):
	settings = Settings(max_sessions=1000, date_shift_min=30, date_shift_max=180)
	store = InMemoryMappingStore(settings=settings, rng=random.Random(seed))
	return store.get_or_create("test-session")


def test_repeated_names_reuse_mapping_and_single_name_reuses_alias() -> None:
	session = setup_session()
	engine = RuleBasedSurrogateGenerator(random.Random(21))
	text = "Rahul Sharma met Rahul Sharma"
	first_start = text.index("Rahul Sharma")
	second_start = text.index("Rahul Sharma", first_start + len("Rahul Sharma"))
	entities = [
		find_entity(text, "Rahul Sharma", "PERSON"),
		DetectedEntity(
			type="PERSON",
			start=second_start,
			end=second_start + len("Rahul Sharma"),
			utf16_start=0,
			utf16_end=0,
			text="Rahul Sharma",
			score=0.9,
			source="regex",
		),
	]
	result = engine.substitute(text, entities, session)

	assert result.synthetic_text.split(" met ")[0] == result.synthetic_text.split(" met ")[1]
	assert "Rahul Sharma" not in result.synthetic_text
	assert len(result.mappings) == 1

	first_name = "Rahul"
	second = engine.substitute(first_name, [find_entity(first_name, first_name, "PERSON")], session)
	assert second.synthetic_text == result.mappings[0].surrogate.split()[0]


def test_phone_aadhaar_pan_and_email_preserve_required_shapes() -> None:
	session = setup_session()
	engine = RuleBasedSurrogateGenerator(random.Random(31))
	phone = "+91-98765-43210"
	phone_result = engine.substitute(phone, [find_entity(phone, phone, "PHONE_NUMBER")], session)
	assert re.fullmatch(r"\+91-[6-9]\d{4}-\d{5}", phone_result.synthetic_text)

	aadhaar = "2345-6789-0124"
	aadhaar_result = engine.substitute(aadhaar, [find_entity(aadhaar, aadhaar, "IN_AADHAAR")], session)
	assert re.fullmatch(r"[2-9]\d{3}-\d{4}-\d{4}", aadhaar_result.synthetic_text)
	assert is_valid(aadhaar_result.synthetic_text.replace("-", ""))

	pan = "ABCPX1234F"
	pan_result = engine.substitute(pan, [find_entity(pan, pan, "IN_PAN")], session)
	assert len(pan_result.synthetic_text) == 10
	assert pan_result.synthetic_text[3] == pan[3]

	text = "Rahul Sharma rahul.sharma@gmail.com"
	person = find_entity(text, "Rahul Sharma", "PERSON")
	email = find_entity(text, "rahul.sharma@gmail.com", "EMAIL_ADDRESS")
	result = engine.substitute(text, [person, email], setup_session(32))
	name_mapping, email_mapping = result.mappings
	assert email_mapping.surrogate == f"{name_mapping.surrogate.replace(' ', '.').lower()}@example.com"


def test_dates_share_shift_and_preserve_five_day_interval() -> None:
	session = setup_session(45)
	engine = RuleBasedSurrogateGenerator(random.Random(46))
	text = "03/08/2026 and 08/08/2026"
	entities = [find_entity(text, "03/08/2026", "DATE_TIME"), find_entity(text, "08/08/2026", "DATE_TIME")]
	result = engine.substitute(text, entities, session)
	first, second = [mapping.surrogate for mapping in result.mappings]

	assert first.endswith("/2026") or first.endswith("/2027")
	assert second.endswith("/2026") or second.endswith("/2027")
	first_date = datetime.strptime(first, "%d/%m/%Y").date()
	second_date = datetime.strptime(second, "%d/%m/%Y").date()
	assert (second_date - first_date).days == 5
	assert session.date_map
	assert result.synthetic_text != text
	assert result.synthetic_text.count("/") == 4


def test_two_hundred_person_surrogates_are_unique_and_not_originals() -> None:
	session = setup_session(71)
	engine = RuleBasedSurrogateGenerator(random.Random(72))
	parts = [f"Person{index} Surname{index}" for index in range(200)]
	text = "; ".join(parts)
	entities = [find_entity(text, value, "PERSON") for value in parts]
	result = engine.substitute(text, entities, session)
	surrogates = [mapping.surrogate.casefold() for mapping in result.mappings]
	originals = {value.casefold() for value in parts}

	assert len(surrogates) == 200
	assert len(set(surrogates)) == 200
	assert not originals.intersection(surrogates)