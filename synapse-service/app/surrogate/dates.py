from datetime import date, datetime, timedelta


DATE_FORMATS = (
	"%d/%m/%Y",
	"%d-%m-%Y",
	"%d.%m.%Y",
	"%d/%m/%y",
	"%Y-%m-%d",
	"%d %b %Y",
	"%d %B %Y",
	"%B %d, %Y",
	"%b %d, %Y",
)


def parse_date(value: str) -> tuple[date, str] | None:
	for date_format in DATE_FORMATS:
		try:
			return datetime.strptime(value, date_format).date(), date_format
		except ValueError:
			continue
	return None


def shift_date(value: str, offset_days: int, date_map: dict[date, date]) -> str | None:
	parsed = parse_date(value)
	if parsed is None:
		return None
	original_date, date_format = parsed
	shifted = date_map.setdefault(original_date, original_date + timedelta(days=offset_days))
	return shifted.strftime(date_format)