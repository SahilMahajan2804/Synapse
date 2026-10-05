import random
import re
import threading
from contextlib import nullcontext

from app.mapping.session import PersonAlias, SessionContext, normalized_mapping_key
from app.models.schemas import DetectedEntity, Mapping
from app.surrogate.base import SubstitutionResult, SurrogateGenerator
from app.surrogate.dates import shift_date
from app.surrogate.emails import make_email
from app.surrogate.ids import make_aadhaar, make_pan
from app.surrogate.locations import make_location
from app.surrogate.names import make_person_alias
from app.surrogate.phones import make_phone


class RuleBasedSurrogateGenerator(SurrogateGenerator):
	def __init__(self, rng: random.Random | None = None) -> None:
		self._rng = rng or random.Random()
		self._rng_lock = threading.Lock()

	def substitute(
		self,
		text: str,
		entities: list[DetectedEntity],
		session: SessionContext,
	) -> SubstitutionResult:
		session_lock = getattr(session, "lock", None)
		lock_context = session_lock if session_lock is not None and hasattr(session_lock, "__enter__") and hasattr(session_lock, "__exit__") else nullcontext()
		with self._rng_lock, lock_context:
			mappings: list[Mapping] = []
			replacements: list[tuple[int, int, str]] = []
			originals = [(entity.type, entity.text) for entity in entities]
			originals.extend((mapping.type, mapping.original) for mapping in session.by_original.values())
			for entity in sorted(entities, key=lambda item: item.start):
				if text[entity.start : entity.end] != entity.text:
					raise ValueError("Detected entity offsets do not match source text")
				key = normalized_mapping_key(entity.type, entity.text)
				mapping = session.by_original.get(key)
				if mapping is None:
					surrogate = self._unique_surrogate(text, entity, session, originals)
					if surrogate is None:
						continue
					mapping = Mapping(
						type=entity.type,
						original=entity.text,
						surrogate=surrogate,
						score=entity.score,
					)
					session.by_original[key] = mapping
					session.by_surrogate[surrogate] = mapping
					session.used_surrogates.add(surrogate)
					if entity.type.upper() in {"PERSON", "PER"} and self._known_person_part(entity.text, session.persons) is None:
						session.persons.append(self._alias_from_surrogate(entity.text, surrogate))
				mappings.append(mapping)
				replacements.append((entity.start, entity.end, mapping.surrogate))

			output = text
			for start, end, surrogate in sorted(replacements, reverse=True):
				output = output[:start] + surrogate + output[end:]
		unique: dict[str, Mapping] = {}
		for mapping in mappings:
			unique.setdefault(mapping.surrogate, mapping)
		return SubstitutionResult(output, list(unique.values()))

	def _unique_surrogate(
		self,
		text: str,
		entity: DetectedEntity,
		session: SessionContext,
		originals: list[tuple[str, str]],
	) -> str | None:
		for _ in range(20):
			candidate = self._make_surrogate(text, entity, session)
			if candidate is None:
				return None
			if candidate.casefold() in {value.casefold() for value in session.used_surrogates}:
				continue
			if any(self._same_value(candidate, original, entity.type, original_type) for original_type, original in originals):
				continue
			return candidate
		raise RuntimeError("Could not create a distinct surrogate")

	def _make_surrogate(self, text: str, entity: DetectedEntity, session: SessionContext) -> str | None:
		entity_type = entity.type.upper()
		if entity_type in {"PERSON", "PER"}:
			known_part = self._known_person_part(entity.text, session.persons)
			if known_part is not None:
				return known_part
			prefix = text[max(0, entity.start - 6) : entity.start]
			alias = make_person_alias(entity.text, prefix, self._rng)
			return alias.sur_full
		if entity_type in {"PHONE_NUMBER", "PHONE"}:
			return make_phone(entity.text, self._rng)
		if entity_type == "EMAIL_ADDRESS":
			return make_email(entity.text, session.persons, self._rng)
		if entity_type == "IN_AADHAAR":
			return make_aadhaar(entity.text, self._rng)
		if entity_type == "IN_PAN":
			return make_pan(entity.text, self._rng)
		if "DATE" in entity_type:
			return shift_date(entity.text, session.day_offset, session.date_map)
		if entity_type in {"LOCATION", "GPE", "LOC"}:
			return make_location(entity.text, self._rng)
		counter = session.type_counters.get(entity_type, 0) + 1
		session.type_counters[entity_type] = counter
		return f"<{entity_type}_{counter}>"

	@staticmethod
	def _known_person_part(value: str, persons: list[PersonAlias]) -> str | None:
		normalized = value.casefold().strip()
		for alias in persons:
			if alias.orig_first.casefold() == normalized:
				return alias.sur_first
			if alias.orig_last and alias.orig_last.casefold() == normalized:
				return alias.sur_last
		return None

	@staticmethod
	def _alias_from_surrogate(original: str, surrogate: str) -> PersonAlias:
		original_tokens = original.split()
		surrogate_tokens = surrogate.split()
		if len(original_tokens) == 1:
			return PersonAlias(
				original_tokens[0],
				"",
				original,
				surrogate_tokens[0],
				"",
				surrogate,
			)
		return PersonAlias(
			original_tokens[0],
			original_tokens[-1],
			original,
			surrogate_tokens[0],
			surrogate_tokens[-1],
			surrogate,
		)

	@staticmethod
	def _same_value(candidate: str, original: str, candidate_type: str, original_type: str) -> bool:
		if " ".join(candidate.split()).casefold() == " ".join(original.split()).casefold():
			return True
		if candidate_type in {"PHONE_NUMBER", "PHONE", "IN_AADHAAR"} or original_type in {
			"PHONE_NUMBER",
			"PHONE",
			"IN_AADHAAR",
		}:
			candidate_digits = re.sub(r"\D", "", candidate)
			original_digits = re.sub(r"\D", "", original)
			return bool(candidate_digits) and candidate_digits == original_digits
		return False