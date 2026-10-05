import random
import re


def make_phone(original: str, rng: random.Random) -> str:
	prefix_match = re.match(r"^(\+91|0)", original)
	prefix = prefix_match.group(1) if prefix_match else ""
	body = original[len(prefix) :]
	if len(re.sub(r"\D", "", body)) != 10:
		raise ValueError("Phone number must have ten subscriber digits")
	subscriber = str(rng.randint(6, 9)) + "".join(str(rng.randint(0, 9)) for _ in range(9))
	digit_index = 0
	output: list[str] = []
	for char in body:
		if char.isdigit():
			output.append(subscriber[digit_index])
			digit_index += 1
		else:
			output.append(char)
	return prefix + "".join(output)