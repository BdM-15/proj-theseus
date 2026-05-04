from types import SimpleNamespace

from src.core.neo4j_config import get_neo4j_connection_config


def test_neo4j_connection_config_normalizes_settings() -> None:
    settings = SimpleNamespace(
        graph_storage="Neo4JStorage",
        neo4j_uri="neo4j://example:7687",
        neo4j_username="neo4j-user",
        neo4j_password=None,
        neo4j_database="",
    )

    config = get_neo4j_connection_config(
        database_fallback="workspace-db",
        settings_provider=lambda: settings,
    )

    assert config.enabled is True
    assert config.uri == "neo4j://example:7687"
    assert config.auth == ("neo4j-user", "")
    assert config.database == "workspace-db"


def test_neo4j_connection_config_preserves_networkx_storage() -> None:
    settings = SimpleNamespace(
        graph_storage="NetworkXStorage",
        neo4j_uri="neo4j://localhost:7687",
        neo4j_username="neo4j",
        neo4j_password="secret",
        neo4j_database="neo4j",
    )

    config = get_neo4j_connection_config(settings_provider=lambda: settings)

    assert config.enabled is False
    assert config.graph_storage == "NetworkXStorage"
    assert config.auth == ("neo4j", "secret")
