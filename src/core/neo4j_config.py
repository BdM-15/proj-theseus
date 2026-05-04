"""Neo4j connection settings helpers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from src.core.config import Settings, get_settings


@dataclass(frozen=True)
class Neo4jConnectionConfig:
    """Runtime Neo4j connection details derived from centralized settings."""

    graph_storage: str
    uri: str
    username: str
    password: str
    database: str

    @property
    def enabled(self) -> bool:
        """Whether Neo4j is the active graph backend."""
        return self.graph_storage == "Neo4JStorage"

    @property
    def auth(self) -> tuple[str, str]:
        """Auth tuple expected by the Neo4j Python driver."""
        return (self.username, self.password)


def get_neo4j_connection_config(
    *,
    database_fallback: str | None = None,
    settings_provider: Callable[[], Settings] = get_settings,
) -> Neo4jConnectionConfig:
    """Return Neo4j connection details from centralized settings."""
    settings = settings_provider()
    return Neo4jConnectionConfig(
        graph_storage=settings.graph_storage,
        uri=settings.neo4j_uri,
        username=settings.neo4j_username,
        password=settings.neo4j_password or "",
        database=settings.neo4j_database or database_fallback or "neo4j",
    )
