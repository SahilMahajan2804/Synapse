import random
import re

from app.detection.verhoeff import check_digit


def _replace_digits_preserving_groups(original: str, digits: str) -> str:
	position = 0
	output: list[str] = []
	for char in original:
		if char.isdigit():
			output.append(digits[position])
			position += 1
		else:
			output.append(char)
	return "".join(output)


def make_aadhaar(original: str, rng: random.Random) -> str:
	if len(re.sub(r"\D", "", original)) != 12:
		raise ValueError("Aadhaar value must contain twelve digits")
	prefix = str(rng.randint(2, 9)) + "".join(str(rng.randint(0, 9)) for _ in range(10))
	digits = prefix + str(check_digit(prefix))
	return _replace_digits_preserving_groups(original, digits)


def make_pan(original: str, rng: random.Random) -> str:
	if len(original) != 10 or not original[3].isalpha():
		raise ValueError("PAN value must have ten characters")
	letters = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
	return (
		"".join(rng.choice(letters) for _ in range(3))
		+ original[3].upper()
		+ rng.choice(letters)
		+ f"{rng.randint(0, 9999):04d}"
		+ rng.choice(letters)
	)