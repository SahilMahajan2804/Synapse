import random


INDIAN_CITIES = [
	"Pune", "Nagpur", "Indore", "Bhopal", "Kochi", "Coimbatore", "Mysuru", "Vadodara", "Surat", "Lucknow",
	"Jaipur", "Chandigarh", "Bhubaneswar", "Guwahati", "Visakhapatnam", "Nashik", "Madurai", "Ranchi", "Dehradun", "Patna",
	"Amritsar", "Agra", "Kanpur", "Varanasi", "Jodhpur", "Udaipur", "Mangaluru", "Thiruvananthapuram", "Vijayawada", "Rajkot",
	"Aurangabad", "Jabalpur", "Raipur", "Jamshedpur", "Noida", "Gurugram", "Thane", "Navi Mumbai", "Tiruchirappalli", "Kozhikode",
]


def make_location(original: str, rng: random.Random) -> str:
	candidates = [city for city in INDIAN_CITIES if city.casefold() != original.casefold()]
	city = rng.choice(candidates)
	if original.isupper():
		return city.upper()
	if original.islower():
		return city.lower()
	return city