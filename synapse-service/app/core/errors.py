class DetectionUnavailableError(Exception):
	"""Raised when the configured PII detector cannot analyze input."""

	def __init__(self) -> None:
		super().__init__("PII detection is unavailable")