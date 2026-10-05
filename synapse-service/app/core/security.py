import secrets
from typing import Annotated

from fastapi import Depends, Header, HTTPException, status

from app.core.config import Settings, get_settings


def require_internal_key(
	supplied_key: Annotated[str | None, Header(alias="X-Internal-Key")] = None,
	settings: Settings = Depends(get_settings),
) -> None:
	configured_key = settings.internal_key
	if configured_key is None or supplied_key is None:
		raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="UNAUTHORIZED")
	if not secrets.compare_digest(supplied_key, configured_key.get_secret_value()):
		raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="UNAUTHORIZED")