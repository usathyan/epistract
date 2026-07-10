#!/usr/bin/env python3
"""Tests for the arXiv-backed KG quality upgrades.

Covers: hedging (2405.13319), triple_judge (GraphJudge 2411.17388 / GraphEval
2407.10793), entity_resolution_v2 (ComEM 2405.16884), epistemic_temporal
(Graphiti/Zep 2501.13956 + LegalWiz 2510.03418).

Run: python -m pytest tests/test_kg_quality.py -v
"""

from pathlib import Path

from core import entity_resolution_v2 as erv2
from core import epistemic_temporal as et
from core import hedging
from core import triple_judge


# ---------------------------------------------------------------------------
# Hedge scoring
# ---------------------------------------------------------------------------


def test_hedge_score_orders_by_uncertainty():
    asserted = hedging.hedge_score("We demonstrate that X binds Y.")
    hypothesized = hedging.hedge_score("These results suggest that X may bind Y.")
    speculative = hedging.hedge_score(
        "We hypothesize that X could conceivably bind Y; this remains unclear."
    )
    assert asserted < hypothesized < speculative
    assert 0.0 <= asserted <= 1.0 and 0.0 <= speculative <= 1.0


def test_hedge_score_certainty_discount():
    hedged = hedging.hedge_score("X may increase Y.")
    de_hedged = hedging.hedge_score("We clearly demonstrate X may increase Y.")
    assert de_hedged < hedged


def test_status_from_score_thresholds():
    assert hedging.status_from_score(0.0, 0.9) == "asserted"
    assert hedging.status_from_score(0.3) == "hypothesized"
    assert hedging.status_from_score(0.7) == "speculative"
    assert hedging.status_from_score(0.0, 0.3) == "hypothesized"  # low confidence


def test_score_relation_does_not_mutate():
    link = {"evidence": "X suggests Y", "confidence": 0.9}
    out = hedging.score_relation(link)
    assert "hedge_score" not in link  # original untouched
    assert out["epistemic_status"] in {"asserted", "hypothesized", "speculative"}


def test_score_relation_preserves_superseded():
    link = {
        "evidence": "X suggests Y",
        "confidence": 0.9,
        "epistemic_status": "superseded",
    }
    out = hedging.score_relation(link)
    assert out["epistemic_status"] == "superseded", (
        "re-scoring must not resurrect a superseded edge"
    )
    assert "hedge_score" in out, "hedge annotation should still be attached"


def test_score_relation_tolerates_null_confidence():
    # An explicit JSON null confidence must not crash status_from_score.
    out = hedging.score_relation({"evidence": "X binds Y.", "confidence": None})
    assert isinstance(out, dict), "score_relation must return a dict on null confidence"
    assert out["epistemic_status"] in {"asserted", "hypothesized", "speculative"}


def test_hedge_classifier_hook_blends():
    # A classifier that always says "very hedged" pulls a low lexical score up.
    plain = hedging.hedge_score("X binds Y.")
    blended = hedging.hedge_score("X binds Y.", classifier_fn=lambda t: 1.0)
    assert blended > plain


# ---------------------------------------------------------------------------
# Triple judge
# ---------------------------------------------------------------------------


def test_lexical_judge_supported_when_endpoints_grounded():
    triple = {
        "source": "compound:semaglutide",
        "target": "protein:glp1_receptor",
        "relation_type": "AGONIST",
    }
    verdict = triple_judge.lexical_judge(
        triple, "Semaglutide is an agonist of the GLP1 receptor."
    )
    assert verdict["verdict"] == "supported"
    assert verdict["score"] >= 0.5


def test_lexical_judge_unsupported_when_absent():
    triple = {
        "source": "compound:aspirin",
        "target": "gene:tp53",
        "relation_type": "TARGETS",
    }
    verdict = triple_judge.lexical_judge(triple, "The weather was sunny that day.")
    assert verdict["verdict"] == "unsupported"
    assert verdict["score"] == 0.0


def test_lexical_judge_partial_when_hedged():
    triple = {
        "source": "compound:drugx",
        "target": "disease:cancer",
        "relation_type": "TREATS",
    }
    verdict = triple_judge.lexical_judge(
        triple, "DrugX may potentially help with cancer, though this is speculative."
    )
    assert verdict["verdict"] == "partial"


def test_judge_graph_gates_low_scores():
    graph = {
        "links": [
            {
                "source": "a:sema",
                "target": "b:glp1",
                "relation_type": "AGONIST",
                "evidence": "Sema activates GLP1.",
            },
            {
                "source": "a:noise",
                "target": "b:void",
                "relation_type": "X",
                "evidence": "Unrelated sentence about lunch.",
            },
        ]
    }
    summary = triple_judge.judge_graph(graph, min_score=0.35)
    assert summary["total"] == 2
    assert summary["gated_count"] == 1
    assert graph["links"][0]["gated"] is False
    assert graph["links"][1]["gated"] is True


def test_make_llm_judge_falls_back_on_bad_output():
    judge = triple_judge.make_llm_judge(call_fn=lambda s, u, **k: "not json")
    triple = {"source": "a:x", "target": "b:y", "relation_type": "R"}
    verdict = judge(triple, "X relates to Y clearly.")
    # Falls back to lexical judge; still returns a valid verdict schema.
    assert set(verdict) == {"verdict", "score", "reason"}


def test_make_llm_judge_parses_valid_output():
    good = '{"verdict": "supported", "score": 0.9, "reason": "clear"}'
    judge = triple_judge.make_llm_judge(call_fn=lambda s, u, **k: good)
    verdict = judge({"source": "a:x", "target": "b:y", "relation_type": "R"}, "ev")
    assert verdict["verdict"] == "supported"
    assert verdict["score"] == 0.9


def test_make_llm_judge_clamps_score():
    high = '{"verdict": "supported", "score": 5.0, "reason": "x"}'
    judge = triple_judge.make_llm_judge(call_fn=lambda s, u, **k: high)
    verdict = judge({"source": "a:x", "target": "b:y", "relation_type": "R"}, "ev")
    assert verdict["score"] == 1.0, "out-of-range score must clamp to 1.0"

    low = '{"verdict": "unsupported", "score": -1.0, "reason": "x"}'
    judge = triple_judge.make_llm_judge(call_fn=lambda s, u, **k: low)
    verdict = judge({"source": "a:x", "target": "b:y", "relation_type": "R"}, "ev")
    assert verdict["score"] == 0.0, "negative score must clamp to 0.0"


# ---------------------------------------------------------------------------
# Entity resolution cascade
# ---------------------------------------------------------------------------


def test_normalize_strips_legal_suffix_and_accents():
    assert erv2.normalize_name("Aramark, Inc.") == "aramark"
    assert erv2.normalize_name("Nestlé S.A.") == "nestle"


def test_auto_merge_on_high_similarity():
    entities = [
        {"id": "e1", "name": "GLP-1 Receptor", "entity_type": "PROTEIN"},
        {"id": "e2", "name": "GLP1 receptor", "entity_type": "PROTEIN"},
        {"id": "e3", "name": "Insulin", "entity_type": "PROTEIN"},
    ]
    result = erv2.resolve_entities(entities)
    # e1/e2 collapse to one canonical id; e3 stays separate.
    assert len(result["merge_map"]) == 1
    canonical_ids = set(entities[i]["id"] for i in range(3)) - set(result["merge_map"])
    assert "e3" in canonical_ids


def test_verify_fn_only_called_in_borderline_band():
    calls = []

    def verify(a, b):
        calls.append((a["id"], b["id"]))
        return True

    entities = [
        {"id": "e1", "name": "Aspirin tablet", "entity_type": "DRUG"},
        {"id": "e2", "name": "Aspirin capsule", "entity_type": "DRUG"},
    ]
    result = erv2.resolve_entities(entities, verify_fn=verify, high=0.9, low=0.3)
    # Jaccard("aspirin tablet","aspirin capsule") = 1/3 -> borderline -> verify called.
    assert calls, "verify_fn should be consulted for the borderline pair"
    assert len(result["merge_map"]) == 1


def test_different_types_do_not_merge():
    entities = [
        {"id": "e1", "name": "Mercury", "entity_type": "ELEMENT"},
        {"id": "e2", "name": "Mercury", "entity_type": "PLANET"},
    ]
    result = erv2.resolve_entities(entities)
    assert result["merge_map"] == {}


def test_embed_fn_drives_similarity():
    entities = [
        {"id": "e1", "name": "heart attack", "entity_type": "CONDITION"},
        {"id": "e2", "name": "myocardial infarction", "entity_type": "CONDITION"},
    ]
    # No token overlap -> lexical would not merge; identical embeddings force a merge.
    vecs = {"heart attack": [1.0, 0.0], "myocardial infarction": [1.0, 0.0]}
    result = erv2.resolve_entities(
        entities, embed_fn=lambda names: [vecs[n] for n in names]
    )
    assert len(result["merge_map"]) == 1


def test_resolve_entities_skips_document_nodes():
    entities = [
        {
            "id": "doc:veg_menu_akka13th_1092025_ver1",
            "name": "veg_menu_akka13th_1092025_ver1",
            "entity_type": "DOCUMENT",
        },
        {
            "id": "doc:non_veg_menu_akka13th_1092025_ver1",
            "name": "non_veg_menu_akka13th_1092025_ver1",
            "entity_type": "DOCUMENT",
        },
        {"id": "e1", "name": "GLP-1 Receptor", "entity_type": "PROTEIN"},
        {"id": "e2", "name": "GLP1 receptor", "entity_type": "PROTEIN"},
    ]
    result = erv2.resolve_entities(entities)
    doc_ids = {
        "doc:veg_menu_akka13th_1092025_ver1",
        "doc:non_veg_menu_akka13th_1092025_ver1",
    }
    merged_ids = set(result["merge_map"]) | set(result["merge_map"].values())
    assert not (doc_ids & merged_ids), (
        f"DOCUMENT nodes must never appear in merge_map, got {result['merge_map']}"
    )
    assert len(result["merge_map"]) == 1, (
        "similar non-DOCUMENT entities in the same input must still merge"
    )


def test_apply_merge_map_repoints_links_and_drops_selfloops():
    graph = {
        "nodes": [
            {"id": "e1", "name": "A"},
            {"id": "e2", "name": "A"},
            {"id": "e3", "name": "B"},
        ],
        "links": [
            {"source": "e2", "target": "e3", "relation_type": "R"},
            {"source": "e1", "target": "e2", "relation_type": "R"},  # becomes self-loop
        ],
    }
    merged = erv2.apply_merge_map(graph, {"e2": "e1"})
    ids = {n["id"] for n in merged["nodes"]}
    assert ids == {"e1", "e3"}
    assert len(merged["links"]) == 1
    assert merged["links"][0]["source"] == "e1"


# ---------------------------------------------------------------------------
# Bi-temporal epistemic layer
# ---------------------------------------------------------------------------


def test_antonym_relations_contradict():
    a = {"source": "n1", "target": "n2", "relation_type": "INCREASES"}
    b = {"source": "n1", "target": "n2", "relation_type": "DECREASES"}
    assert et.relations_contradict(a, b)


def test_negation_polarity_contradiction():
    a = {
        "source": "n1",
        "target": "n2",
        "relation_type": "BINDS",
        "evidence": "X binds Y.",
    }
    b = {
        "source": "n1",
        "target": "n2",
        "relation_type": "BINDS",
        "evidence": "X does not bind Y.",
    }
    assert et.relations_contradict(a, b)


def test_no_contradiction_for_different_pairs():
    a = {"source": "n1", "target": "n2", "relation_type": "INCREASES"}
    b = {"source": "n3", "target": "n4", "relation_type": "DECREASES"}
    assert not et.relations_contradict(a, b)


def test_temporal_layer_invalidates_older_edge():
    links = [
        {
            "source": "drug",
            "target": "marker",
            "relation_type": "INCREASES",
            "confidence": 0.8,
            "valid_at": "2020-01-01",
        },
        {
            "source": "drug",
            "target": "marker",
            "relation_type": "DECREASES",
            "confidence": 0.8,
            "valid_at": "2024-01-01",
        },
    ]
    result = et.apply_temporal_layer(links, now="2026-07-04T00:00:00Z")
    assert result["invalidated"] == 1
    # Older (2020) edge is superseded; newer (2024) stays active.
    older = result["links"][0]
    newer = result["links"][1]
    assert older["epistemic_status"] == "superseded"
    assert older["invalid_at"] == "2026-07-04T00:00:00Z"
    assert older["superseded_by"] == "drug|DECREASES|marker"
    assert newer.get("epistemic_status") != "superseded"


def test_temporal_layer_never_deletes():
    links = [
        {
            "source": "a",
            "target": "b",
            "relation_type": "ACTIVATES",
            "valid_at": "2021",
        },
        {"source": "a", "target": "b", "relation_type": "INHIBITS", "valid_at": "2022"},
    ]
    result = et.apply_temporal_layer(links, now="t")
    assert len(result["links"]) == 2  # both retained, one just flagged


def test_adjudicate_fn_can_veto_lexical_contradiction():
    links = [
        {"source": "a", "target": "b", "relation_type": "INCREASES", "valid_at": "1"},
        {"source": "a", "target": "b", "relation_type": "DECREASES", "valid_at": "2"},
    ]
    # Adjudicator says "not actually a contradiction" -> nothing invalidated.
    result = et.apply_temporal_layer(links, adjudicate_fn=lambda a, b: False, now="t")
    assert result["invalidated"] == 0


def test_temporal_layer_reports_stable_identities():
    links = [
        {"source": "a", "target": "b", "relation_type": "ACTIVATES", "valid_at": "1"},
        {"source": "a", "target": "b", "relation_type": "INHIBITS", "valid_at": "2"},
    ]
    result = et.apply_temporal_layer(links, now="t")
    (report,) = result["contradictions"]
    assert report["active"] == "a|INHIBITS|b"
    assert report["superseded"] == "a|ACTIVATES|b"


def test_apply_temporal_layer_idempotent_on_superseded():
    links = [
        {
            "source": "drug",
            "target": "marker",
            "relation_type": "INCREASES",
            "confidence": 0.8,
            "valid_at": "2020-01-01",
        },
        {
            "source": "drug",
            "target": "marker",
            "relation_type": "DECREASES",
            "confidence": 0.8,
            "valid_at": "2024-01-01",
        },
    ]
    first = et.apply_temporal_layer(links, now="2026-01-01T00:00:00Z")
    assert first["invalidated"] == 1
    second = et.apply_temporal_layer(first["links"], now="2026-06-01T00:00:00Z")
    assert second["invalidated"] == 0, "second pass must not re-invalidate"
    superseded = [
        link
        for link in second["links"]
        if link.get("epistemic_status") == "superseded"
    ]
    assert len(superseded) == 1
    assert superseded[0]["invalid_at"] == "2026-01-01T00:00:00Z", (
        "re-running must not re-stamp invalid_at"
    )


def test_temporal_layer_tolerates_null_confidence():
    # An explicit JSON null confidence must not break the tie-break comparison.
    links = [
        {
            "source": "drug",
            "target": "marker",
            "relation_type": "INCREASES",
            "confidence": None,
            "valid_at": "2020-01-01",
        },
        {
            "source": "drug",
            "target": "marker",
            "relation_type": "DECREASES",
            "confidence": 0.8,
            "valid_at": "2020-01-01",
        },
    ]
    result = et.apply_temporal_layer(links, now="t")
    assert result["invalidated"] == 1, "exactly one edge should be superseded"
    superseded = [
        link
        for link in result["links"]
        if link.get("epistemic_status") == "superseded"
    ]
    assert len(superseded) == 1


def test_contradiction_grouping_scoped():
    # Two different (source, target) pairs, each internally contradictory.
    links = [
        {"source": "a", "target": "b", "relation_type": "INCREASES", "valid_at": "1"},
        {"source": "x", "target": "y", "relation_type": "ACTIVATES", "valid_at": "1"},
        {"source": "a", "target": "b", "relation_type": "DECREASES", "valid_at": "2"},
        {"source": "x", "target": "y", "relation_type": "INHIBITS", "valid_at": "2"},
    ]
    result = et.apply_temporal_layer(links, now="t")
    assert result["invalidated"] == 2
    pairs = {(c["source"], c["target"]) for c in result["contradictions"]}
    assert pairs == {("a", "b"), ("x", "y")}, "no cross-pair contradictions"


# ---------------------------------------------------------------------------
# CLI wiring: `epistract enhance`
# ---------------------------------------------------------------------------


def test_cli_enhance_end_to_end(tmp_path, monkeypatch, capsys):
    import json as _json

    from core import cli
    from core import registry

    monkeypatch.setenv("EPISTRACT_HOME", str(tmp_path / "home"))
    monkeypatch.delenv("EPISTRACT_PROJECT", raising=False)
    project = registry.init_project(
        "enh", root=tmp_path / "enh", domain="drug-discovery"
    )

    graph = {
        "nodes": [
            {"id": "d:sema", "name": "GLP-1 Receptor", "entity_type": "PROTEIN"},
            {"id": "d:sema2", "name": "GLP1 receptor", "entity_type": "PROTEIN"},
            {"id": "d:t2d", "name": "Type 2 Diabetes", "entity_type": "DISEASE"},
        ],
        "links": [
            {
                "source": "d:sema",
                "target": "d:t2d",
                "relation_type": "INCREASES",
                "confidence": 0.7,
                "evidence": "The drug increases the marker.",
                "valid_at": "2020-01-01",
            },
            {
                "source": "d:sema",
                "target": "d:t2d",
                "relation_type": "DECREASES",
                "confidence": 0.9,
                "evidence": "Later trials show the drug decreases the marker.",
                "valid_at": "2024-01-01",
            },
        ],
    }
    (Path(project["root"]) / "graph_data.json").write_text(_json.dumps(graph))

    assert cli.main(["enhance", "--project", "enh", "--json"]) == 0
    report = _json.loads(capsys.readouterr().out)
    assert report["resolve"]["merged_ids"] == 1  # GLP-1 / GLP1 collapsed
    assert report["judge"]["total"] >= 1
    assert report["epistemic"]["contradictions"] == 1  # INCREASES vs DECREASES
    assert report["epistemic"]["invalidated"] == 1

    written = _json.loads((Path(project["root"]) / "graph_data.json").read_text())
    superseded = [
        link
        for link in written["links"]
        if link.get("epistemic_status") == "superseded"
    ]
    assert len(superseded) == 1
    assert (Path(project["root"]) / "enhancement_report.json").exists()


def test_cli_enhance_requires_graph(tmp_path, monkeypatch, capsys):
    from core import cli
    from core import registry

    monkeypatch.setenv("EPISTRACT_HOME", str(tmp_path / "home"))
    monkeypatch.delenv("EPISTRACT_PROJECT", raising=False)
    registry.init_project("nograph", root=tmp_path / "nograph")
    assert cli.main(["enhance", "--project", "nograph"]) == 1
    assert "no graph_data.json" in capsys.readouterr().err


def test_cli_enhance_llm_import_guard(tmp_path, monkeypatch, capsys):
    """A broken llm_client import under --llm degrades to a friendly error."""
    import json as _json

    from core import cli
    from core import registry

    monkeypatch.setenv("EPISTRACT_HOME", str(tmp_path / "home"))
    monkeypatch.delenv("EPISTRACT_PROJECT", raising=False)
    project = registry.init_project(
        "llmguard", root=tmp_path / "llmguard", domain="drug-discovery"
    )
    graph = {
        "nodes": [{"id": "d:sema", "name": "Semaglutide", "entity_type": "COMPOUND"}],
        "links": [
            {
                "source": "d:sema",
                "target": "d:sema",
                "relation_type": "SELF",
                "confidence": 0.9,
                "evidence": "Semaglutide is semaglutide.",
            }
        ],
    }
    (Path(project["root"]) / "graph_data.json").write_text(_json.dumps(graph))

    def broken_make_llm_judge(call_fn=None):
        raise ImportError("No module named 'litellm'")

    monkeypatch.setattr(triple_judge, "make_llm_judge", broken_make_llm_judge)
    assert (
        cli.main(["enhance", "--project", "llmguard", "--judge", "--llm"]) == 1
    ), "expected exit code 1 when the LLM client cannot be imported"
    err = capsys.readouterr().err
    assert "--llm" in err, f"stderr should mention --llm guidance, got: {err!r}"
