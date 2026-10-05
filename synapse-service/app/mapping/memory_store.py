import random
import threading
import time
import uuid
from collections.abc import Callable

from cachetools import TTLCache

from app.core.config import Settings, get_settings
from app.mapping.base import MappingStore
from app.mapping.session import SessionContext, create_session_context


class InMemoryMappingStore:
	"""Process-local TTL store; Phase 1 requires a single service replica."""

	def __init__(
		self,
		settings: Settings | None = None,
		rng: random.Random | None = None,
		timer: Callable[[], float] = time.monotonic,
	) -> None:
		self._settings = settings or get_settings()
		self._rng = rng or random.Random()
		self._cache: TTLCache[str, SessionContext] = TTLCache(
			maxsize=self._settings.max_sessions,
			ttl=self._settings.session_ttl_seconds,
			timer=timer,
		)
		self._lock = threading.Lock()

	def get_or_create(self, session_id: str | None = None) -> SessionContext:
		with self._lock:
			resolved_id = session_id.strip() if session_id and session_id.strip() else self._new_session_id()
			session = self._cache.get(resolved_id)
			if session is None:
				session = create_session_context(resolved_id, self._rng, self._settings)
				self._cache[resolved_id] = session
			return session

	def find(self, session_id: str) -> SessionContext | None:
		with self._lock:
			return self._cache.get(session_id)

	def delete(self, session_id: str) -> bool:
		with self._lock:
			return self._cache.pop(session_id, None) is not None

	def _new_session_id(self) -> str:
		return str(uuid.UUID(int=self._rng.getrandbits(128), version=4))