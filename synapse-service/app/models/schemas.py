from typing import Literal

from pydantic import BaseModel


class DetectedEntity(BaseModel):
	type: str
	start: int
	end: int
	utf16_start: int
	utf16_end: int
	text: str
	score: float
	source: Literal["presidio", "regex"]