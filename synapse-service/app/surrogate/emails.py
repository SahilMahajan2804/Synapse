import random
import re

from app.mapping.session import PersonAlias
from app.surrogate.names import make_person_alias


def make_email(original: str, persons: list[PersonAlias], rng: random.Random) -> str:
	local_part = original.split("@", maxsplit=1)[0]
	for alias in sorted(persons, key=lambda item: len(item.orig_full), reverse=True):
		updated = local_part
		if alias.orig_first:
			updated = re.sub(re.escape(alias.orig_first), alias.sur_first, updated, flags=re.IGNORECASE)
		if alias.orig_last and alias.sur_last:
			updated = re.sub(re.escape(alias.orig_last), alias.sur_last, updated, flags=re.IGNORECASE)
		if updated != local_part:
			return f"{updated.lower()}@example.com"
	name = make_person_alias(local_part.replace(".", " ").replace("_", " "), "", rng)
	return f"{name.sur_full.replace(' ', '.').lower()}@example.com"