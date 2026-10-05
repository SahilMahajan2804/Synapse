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


class Mapping(BaseModel):
	type: str
	original: str
	surrogate: str
	score: float


class AnonymizeRequest(BaseModel):
	session_id: str | None = None
	text: str


class AnonymizeTiming(BaseModel):
	detect_ms: int
	synthesize_ms: int


class LeakGuardReport(BaseModel):
	passed: bool
	leaked_count: int
	leaked_values: list[str]


class AnonymizeResponse(BaseModel):
	session_id: str
	synthetic_text: str
	entities: list[DetectedEntity]
	mappings: list[Mapping]
	leak_guard: LeakGuardReport
	timings: AnonymizeTiming


class DeanonymizeRequest(BaseModel):
	session_id: str
	text: str


class DeanonymizeResponse(BaseModel):
	session_id: str
	restored_text: str
	replacements: int
	restore_ms: int


class SessionDeleteResponse(BaseModel):
	status: str = "OK"