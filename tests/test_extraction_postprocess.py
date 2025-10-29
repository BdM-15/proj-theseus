import json
from src.core.extraction_postprocess import (
    tolerant_parse_entities,
    split_into_chunks,
    summarize_parse_results,
)


def test_split_json_array():
    raw = json.dumps([{"text": "Req A", "type": "requirement"}, {"text": "Req B", "type": "requirement"}])
    chunks = split_into_chunks(raw)
    assert len(chunks) == 2


def test_heuristic_pipe_parsing():
    raw = "Do X | requirement | confidence: 0.92"
    results = tolerant_parse_entities(raw)
    assert len(results) == 1
    r = results[0]
    assert r.get("parsed") is not None
    assert r["parsed"].get("type") == "requirement"
    # confidence may or may not be present depending on heuristic; ensure parsed exists
    assert isinstance(r["parsed"], dict)


def test_unparseable_but_preserved():
    raw = """
    This is a long unstructured block that doesn't follow any known delimiter or JSON
    and should be preserved as a single raw chunk while returning an "unparsed" error
    message in the record.
    """
    results = tolerant_parse_entities(raw)
    # We expect at least one chunk to be returned; parser should preserve raw text
    assert len(results) >= 1
    # Each returned record should contain the raw field and either parsed or error info
    for rec in results:
        assert "raw" in rec
        assert rec.get("parsed") is not None or rec.get("error") is not None
