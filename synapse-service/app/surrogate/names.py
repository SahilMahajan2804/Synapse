import random
import re

from app.mapping.session import PersonAlias
from app.surrogate.name_data import FEMALE_FIRST, LAST, MALE_FIRST


def _gender_from_context(prefix: str, rng: random.Random) -> str:
	match = re.search(r"(mr|shri|sri|mrs|ms|miss|smt|kumari|dr)\.?\s*$", prefix[-6:].casefold())
	if match:
		title = match.group(1)
		if title in {"mr", "shri", "sri"}:
			return "male"
		if title in {"mrs", "ms", "miss", "smt", "kumari"}:
			return "female"
	return rng.choice(("male", "female"))


def make_person_alias(original: str, prefix: str, rng: random.Random) -> PersonAlias:
	tokens = original.split()
	if not tokens:
		raise ValueError("Person name is empty")
	gender = _gender_from_context(prefix, rng)
	first_pool = MALE_FIRST if gender == "male" else FEMALE_FIRST
	sur_first = rng.choice(first_pool)
	if len(tokens) == 1:
		sur_last = ""
		sur_full = sur_first
		orig_first = tokens[0]
		orig_last = ""
	else:
		sur_last = rng.choice(LAST)
		middle_count = len(tokens) - 2
		middle_names = [rng.choice(first_pool) for _ in range(middle_count)]
		sur_full = " ".join([sur_first, *middle_names, sur_last])
		orig_first = tokens[0]
		orig_last = tokens[-1]
	if original.isupper():
		sur_first = sur_first.upper()
		sur_last = sur_last.upper()
		sur_full = sur_full.upper()
	return PersonAlias(orig_first, orig_last, original, sur_first, sur_last, sur_full)