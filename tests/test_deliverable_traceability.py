"""
Neo4j integration test (optional): deliverable traceability.

This file used to execute as a standalone script at import time (connecting to Neo4j),
which breaks `pytest` in environments without a running Neo4j instance.
"""

import os

import pytest
from dotenv import load_dotenv
from neo4j import GraphDatabase
from neo4j.exceptions import ServiceUnavailable


def _enabled() -> bool:
    return (os.getenv("RUN_NEO4J_TESTS", "") or "").strip().lower() in {"1", "true", "yes", "y"}


def _neo4j_driver():
    load_dotenv()
    uri = os.getenv("NEO4J_URI", "neo4j://localhost:7687")
    user = os.getenv("NEO4J_USER", os.getenv("NEO4J_USERNAME", "neo4j"))
    pwd = os.getenv("NEO4J_PASSWORD")
    if not pwd:
        pytest.skip("NEO4J_PASSWORD not set")
    return GraphDatabase.driver(uri, auth=(user, pwd))


@pytest.mark.skipif(not _enabled(), reason="Set RUN_NEO4J_TESTS=true to run Neo4j integration tests")
def test_deliverable_traceability_queries_execute():
    driver = _neo4j_driver()
    try:
        with driver.session() as session:
            q1 = """
            MATCH (r:Entity {entity_type: 'requirement'})-[:SATISFIED_BY]->(d:Entity {entity_type: 'deliverable'})
            RETURN count(*) AS n
            """
            n1 = session.run(q1).single()["n"]

            q2 = """
            MATCH (w:Entity)-[:PRODUCES]->(d:Entity {entity_type: 'deliverable'})
            WHERE w.entity_type IN ['statement_of_work', 'pws', 'soo']
            RETURN count(*) AS n
            """
            n2 = session.run(q2).single()["n"]

        assert isinstance(n1, int) and isinstance(n2, int)
    except ServiceUnavailable:
        pytest.skip("Neo4j not reachable on NEO4J_URI")
    finally:
        driver.close()

