from dataclasses import dataclass
from typing import Protocol

from app.mapping.session import SessionContext
from app.models.schemas import DetectedEntity, Mapping


@dataclass
class SubstitutionResult:
	synthetic_text: str
	mappings: list[Mapping]


class SurrogateGenerator(Protocol):
	def substitute(
		self,
		text: str,
		entities: list[DetectedEntity],
		session: SessionContext,
	) -> SubstitutionResult: ...