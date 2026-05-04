"""Workspace-scoped graph snapshot routes for the Theseus UI."""

from __future__ import annotations

import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Callable

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)

# Cap at 5000 nodes because larger Cytoscape/fcose layouts become unusable.
GRAPH_HARD_CAP = 5000
GRAPH_DEFAULT = 2000


def json_safe(value: Any) -> Any:
    """Coerce neo4j/numpy/datetime values into JSON-serializable scalars."""
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, (list, tuple, set)):
        return [json_safe(item) for item in value]
    if isinstance(value, dict):
        return {str(key): json_safe(item) for key, item in value.items()}
    for attr in ("isoformat", "iso_format", "to_native"):
        if hasattr(value, attr):
            try:
                coerced = getattr(value, attr)()
                if isinstance(coerced, datetime):
                    return coerced.isoformat()
                return json_safe(coerced)
            except Exception:  # noqa: BLE001
                pass
    try:
        return str(value)
    except Exception:  # noqa: BLE001
        return None


async def load_graph_neo4j(
    workspace: str,
    max_nodes: int,
    entity_type: str | None,
) -> dict[str, Any]:
    """Pull a Cytoscape-friendly subgraph from Neo4j, top-degree nodes first."""
    from neo4j import AsyncGraphDatabase

    uri = os.getenv("NEO4J_URI", "neo4j://localhost:7687")
    user = os.getenv("NEO4J_USERNAME", "neo4j")
    password = os.getenv("NEO4J_PASSWORD", "")
    database = os.getenv("NEO4J_DATABASE", "neo4j")
    label = workspace

    type_filter = ""
    params: dict[str, Any] = {"max_nodes": int(max_nodes)}
    if entity_type:
        type_filter = "WHERE toLower(n.entity_type) = toLower($etype)"
        params["etype"] = entity_type

    nodes_query = f"""
        MATCH (n:`{label}`)
        {type_filter}
        WITH n, COUNT {{ (n)--() }} AS degree
        ORDER BY degree DESC
        LIMIT $max_nodes
        RETURN elementId(n) AS nid, n AS node, degree
    """
    total_query = f"MATCH (n:`{label}`) {type_filter} RETURN count(n) AS total"
    edges_query = f"""
        MATCH (a:`{label}`)-[r]->(b:`{label}`)
        WHERE elementId(a) IN $ids AND elementId(b) IN $ids
        RETURN elementId(r) AS rid, elementId(a) AS src, elementId(b) AS tgt,
               type(r) AS rtype, properties(r) AS props
    """

    driver = AsyncGraphDatabase.driver(uri, auth=(user, password))
    try:
        async with driver.session(database=database, default_access_mode="READ") as session:
            total_res = await session.run(
                total_query,
                **({"etype": entity_type} if entity_type else {}),
            )
            total = (await total_res.single())["total"]
            await total_res.consume()

            nodes_res = await session.run(nodes_query, **params)
            nodes_payload: list[dict[str, Any]] = []
            ids: list[str] = []
            async for record in nodes_res:
                node_id = record["nid"]
                props = json_safe(dict(record["node"]))
                ids.append(node_id)
                nodes_payload.append(
                    {
                        "id": str(node_id),
                        "labels": [str(props.get("entity_id", node_id))],
                        "properties": {
                            **props,
                            "_degree": int(record["degree"] or 0),
                        },
                    }
                )
            await nodes_res.consume()

            edges_payload: list[dict[str, Any]] = []
            if ids:
                edges_res = await session.run(edges_query, ids=ids)
                async for record in edges_res:
                    edges_payload.append(
                        {
                            "id": str(record["rid"]),
                            "source": str(record["src"]),
                            "target": str(record["tgt"]),
                            "type": record["rtype"],
                            "properties": json_safe(dict(record["props"] or {})),
                        }
                    )
                await edges_res.consume()
    finally:
        await driver.close()

    return {
        "backend": "neo4j",
        "workspace": workspace,
        "nodes": nodes_payload,
        "edges": edges_payload,
        "total_nodes": int(total),
        "returned_nodes": len(nodes_payload),
        "returned_edges": len(edges_payload),
        "is_truncated": int(total) > len(nodes_payload),
    }


def load_graph_networkx(
    workspace: str,
    max_nodes: int,
    entity_type: str | None,
    *,
    working_dir: Path,
) -> dict[str, Any]:
    """Read graph_chunk_entity_relation.graphml and build a UI payload."""
    import networkx as nx

    graphml = working_dir / workspace / "graph_chunk_entity_relation.graphml"
    if not graphml.exists():
        return {
            "backend": "networkx",
            "workspace": workspace,
            "nodes": [],
            "edges": [],
            "total_nodes": 0,
            "returned_nodes": 0,
            "returned_edges": 0,
            "is_truncated": False,
        }

    graph = nx.read_graphml(str(graphml))
    if entity_type:
        keep = [
            node
            for node, data in graph.nodes(data=True)
            if str(data.get("entity_type", "")).lower() == entity_type.lower()
        ]
        graph = graph.subgraph(keep).copy()

    total = graph.number_of_nodes()
    if total > max_nodes:
        top = sorted(graph.degree(), key=lambda item: item[1], reverse=True)[:max_nodes]
        keep = [node for node, _ in top]
        graph = graph.subgraph(keep).copy()

    nodes_payload: list[dict[str, Any]] = []
    for node, data in graph.nodes(data=True):
        props = json_safe(dict(data))
        nodes_payload.append(
            {
                "id": str(node),
                "labels": [str(props.get("entity_id", node))],
                "properties": {**props, "_degree": int(graph.degree(node))},
            }
        )

    edges_payload: list[dict[str, Any]] = []
    for index, (source, target, data) in enumerate(graph.edges(data=True)):
        props = json_safe(dict(data))
        relationship_type = (
            props.pop("relationship_type", None)
            or props.get("keywords")
            or "RELATED_TO"
        )
        edges_payload.append(
            {
                "id": str(index),
                "source": str(source),
                "target": str(target),
                "type": str(relationship_type),
                "properties": props,
            }
        )

    return {
        "backend": "networkx",
        "workspace": workspace,
        "nodes": nodes_payload,
        "edges": edges_payload,
        "total_nodes": int(total),
        "returned_nodes": len(nodes_payload),
        "returned_edges": len(edges_payload),
        "is_truncated": total > len(nodes_payload),
    }


def register_graph_routes(
    app: FastAPI,
    *,
    workspace_name: Callable[[], str],
    graph_storage: Callable[[], str],
    working_dir: Callable[[], Path],
) -> None:
    """Register graph snapshot route for the Theseus UI."""

    @app.get("/api/ui/graph", tags=["theseus-ui"])
    async def ui_graph(
        max_nodes: int = GRAPH_DEFAULT,
        entity_type: str | None = None,
    ) -> JSONResponse:
        """Return a Cytoscape-friendly subgraph for the active workspace."""
        try:
            cap = max(1, min(int(max_nodes), GRAPH_HARD_CAP))
        except (TypeError, ValueError):
            cap = GRAPH_DEFAULT

        workspace = workspace_name()
        backend = (graph_storage() or "").lower()
        try:
            if "neo4j" in backend:
                payload = await load_graph_neo4j(workspace, cap, entity_type)
            else:
                payload = load_graph_networkx(
                    workspace,
                    cap,
                    entity_type,
                    working_dir=working_dir(),
                )
            return JSONResponse(payload)
        except Exception as exc:  # noqa: BLE001
            logger.exception(
                "Graph snapshot failed for workspace=%s: %s", workspace, exc
            )
            raise HTTPException(500, f"Graph snapshot failed: {exc}") from exc
