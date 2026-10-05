from typing import Protocol

from app.mapping.session import SessionContext


class MappingStore(Protocol):
	def get_or_create(self, session_id: str | None = None) -> SessionContext: ...

	def find(self, session_id: str) -> SessionContext | None: ...

	def delete(self, session_id: str) -> bool: ...