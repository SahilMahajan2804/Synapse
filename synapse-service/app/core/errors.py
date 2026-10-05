class DetectionUnavailableError(Exception):
	"""Raised when the configured PII detector cannot analyze input."""

	def __init__(self) -> None:
		super().__init__("PII detection is unavailable")


class SynapseHttpError(Exception):
	def __init__(self, code: str, message: str, status_code: int, leak_guard: dict | None = None) -> None:
		super().__init__(message)
		self.code = code
		self.message = message
		self.status_code = status_code
		self.leak_guard = leak_guard
