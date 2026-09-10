"""Unit tests for core/crosswalk_output.py -- rendering a crosswalk spine
(and its cross-domain findings) into the graph_data.json + claims_layer.json
pair the workbench, the graph viewer, and every export format already read.

Every fixture here is built in-memory: no project directory, no built graph,
no network. The opt-in integration checks against real graphs live in
tests/test_crosswalk_realgraph.py and tests/test_cross_domain_realgraph.py.
"""

from __future__ import annotations

import json

import pytest

from core.crosswalk_output import (
    DOMAIN_NAME,
    CrosswalkOutputError,
    axis_entity_type,
    build_claims_layer,
    build_crosswalk_graph,
    graph_node_id,
    key_node_id,
    load_findings,
    load_json,
    load_spine,
    main,
    render,
    write_crosswalk_output,
)

pytestmark = pytest.mark.unit


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def spine() -> dict:
    """A three-graph spine: one key shared by all three, one by two, two
    unshared, plus an axis only one graph declares."""
    return {
        "spine_version": "1.0",
        "generated_at": "2026-01-01T00:00:00+00:00",
        "graphs": {
            "clinicaltrials": "/tmp/ct",
            "fda-product-labels": "/tmp/labels",
            "pharmacovigilance": "/tmp/pv",
        },
        "axes": {
            "drug": {
                "semaglutide": {
                    "identifiers": {"atc": ["A10BJ06"], "unii": ["53AXN4NNHX"]},
                    "graphs": {
                        "clinicaltrials": ["ct4"],
                        "fda-product-labels": ["lb1"],
                        "pharmacovigilance": ["pv1", "pv9"],
                    },
                },
                "tirzepatide": {
                    "identifiers": {},
                    "graphs": {
                        "fda-product-labels": ["lb6"],
                        "pharmacovigilance": ["pv2"],
                    },
                },
            },
            "adverse_event": {
                "diarrhea": {"identifiers": {}, "graphs": {"pharmacovigilance": ["pv4"]}},
                "nausea": {
                    "identifiers": {},
                    "graphs": {
                        "fda-product-labels": ["lb2"],
                        "pharmacovigilance": ["pv3"],
                    },
                },
            },
            "outcome": {
                "overall survival": {
                    "identifiers": {},
                    "graphs": {"clinicaltrials": ["ct2"]},
                },
            },
        },
        "stats": {
            "drug": {"declared_by": ["clinicaltrials", "fda-product-labels", "pharmacovigilance"]},
            "adverse_event": {"declared_by": ["fda-product-labels", "pharmacovigilance"]},
            "outcome": {"declared_by": ["clinicaltrials"]},
        },
    }


@pytest.fixture
def findings() -> dict:
    """Two real findings plus one rule-level error record."""
    return {
        "cross_domain_version": "1.0",
        "super_domain": {
            "custom_findings": {
                "unlabeled_adverse_event": [
                    {
                        "rule_name": "unlabeled_adverse_event",
                        "type": "safety_signal",
                        "severity": "medium",
                        "description": "diarrhea is reported against semaglutide ...",
                        "evidence": {
                            "subject_axis": "drug",
                            "subject_key": "semaglutide",
                            "object_axis": "adverse_event",
                            "object_key": "diarrhea",
                            "probe_graph": "pharmacovigilance",
                            "reference_graph": "fda-product-labels",
                            "subtype": "absent",
                        },
                    },
                    {
                        # Object key not in the spine -- cannot be drawn.
                        "rule_name": "unlabeled_adverse_event",
                        "type": "safety_signal",
                        "severity": "high",
                        "description": "ghost event",
                        "evidence": {
                            "subject_axis": "drug",
                            "subject_key": "semaglutide",
                            "object_axis": "adverse_event",
                            "object_key": "not-in-the-spine",
                            "subtype": "absent",
                        },
                    },
                ],
                "broken_rule": [{"status": "error", "error": "boom"}],
            }
        },
        "stats": {"unlabeled_adverse_event": {"status": "ok", "findings": 2}},
    }


# ---------------------------------------------------------------------------
# Naming
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("axis", "expected"),
    [
        ("drug", "Drug"),
        ("adverse_event", "AdverseEvent"),
        ("trial", "Trial"),
        ("a_b_c", "ABC"),
        ("", "Axis"),
        ("_", "Axis"),
    ],
)
def test_axis_entity_type(axis, expected):
    assert axis_entity_type(axis) == expected


def test_node_ids_use_a_double_colon_namespace():
    """A single colon appears inside real canonical keys, so the id
    separator must not be one."""
    assert key_node_id("trial", "phase 2: extension") == "trial::phase 2: extension"
    assert graph_node_id("fda-product-labels") == "graph::fda-product-labels"


# ---------------------------------------------------------------------------
# Graph construction
# ---------------------------------------------------------------------------


def test_graph_has_one_node_per_source_graph_and_one_per_canonical_key(spine):
    graph = build_crosswalk_graph(spine)
    by_type: dict[str, list[dict]] = {}
    for node in graph["nodes"]:
        by_type.setdefault(node["entity_type"], []).append(node)

    assert len(by_type["Graph"]) == 3
    assert {n["name"] for n in by_type["Graph"]} == set(spine["graphs"])
    assert {n["name"] for n in by_type["Drug"]} == {"semaglutide", "tirzepatide"}
    assert {n["name"] for n in by_type["AdverseEvent"]} == {"diarrhea", "nausea"}
    assert {n["name"] for n in by_type["Outcome"]} == {"overall survival"}
    assert graph["metadata"]["canonical_keys"] == 5


def test_axes_become_entity_types_so_the_workbench_can_filter_by_them(spine):
    """The legend and the type filter are built from distinct entity_type
    values, so an axis that does not surface as one is invisible."""
    graph = build_crosswalk_graph(spine)
    assert graph["metadata"]["entity_types"] == [
        "AdverseEvent",
        "Drug",
        "Graph",
        "Outcome",
    ]


def test_key_node_records_its_members_graphs_and_identifiers(spine):
    graph = build_crosswalk_graph(spine)
    node = next(n for n in graph["nodes"] if n["id"] == "drug::semaglutide")
    attrs = node["attributes"]

    assert attrs["axis"] == "drug"
    assert attrs["canonical_key"] == "semaglutide"
    assert attrs["graphs"] == ["clinicaltrials", "fda-product-labels", "pharmacovigilance"]
    assert attrs["graph_count"] == 3
    assert attrs["member_node_count"] == 4  # pv contributes two member nodes
    assert attrs["shared"] is True
    assert attrs["members"]["pharmacovigilance"] == ["pv1", "pv9"]
    # Identifiers merge across graphs onto the one canonical key.
    assert attrs["id_atc"] == ["A10BJ06"]
    assert attrs["id_unii"] == ["53AXN4NNHX"]


def test_unshared_key_is_marked_unshared_not_dropped(spine):
    graph = build_crosswalk_graph(spine)
    node = next(n for n in graph["nodes"] if n["id"] == "adverse_event::diarrhea")
    assert node["attributes"]["shared"] is False
    assert node["attributes"]["graph_count"] == 1


def test_shared_key_count_counts_keys_in_two_or_more_graphs(spine):
    graph = build_crosswalk_graph(spine)
    shared = [n["id"] for n in graph["nodes"] if n["attributes"].get("shared")]
    assert sorted(shared) == [
        "adverse_event::nausea",
        "drug::semaglutide",
        "drug::tirzepatide",
    ]


def test_membership_links_carry_the_member_node_ids(spine):
    graph = build_crosswalk_graph(spine)
    link = next(
        link
        for link in graph["links"]
        if link["source"] == "drug::semaglutide"
        and link["target"] == "graph::pharmacovigilance"
    )
    assert link["relation_type"] == "PRESENT_IN"
    assert link["attributes"]["member_node_ids"] == ["pv1", "pv9"]
    assert link["attributes"]["member_count"] == 2


def test_graph_node_lists_the_axes_that_graph_declared(spine):
    graph = build_crosswalk_graph(spine)
    ct = next(n for n in graph["nodes"] if n["id"] == "graph::clinicaltrials")
    assert ct["attributes"]["axes_declared"] == ["drug", "outcome"]
    labels = next(n for n in graph["nodes"] if n["id"] == "graph::fda-product-labels")
    assert labels["attributes"]["axes_declared"] == ["adverse_event", "drug"]


def test_metadata_domain_is_crosswalk_so_the_workbench_resolves_a_template(spine):
    """resolve_domain() reads metadata.domain; without it the workbench falls
    back to the generic template and prints a legacy-graph warning."""
    graph = build_crosswalk_graph(spine)
    assert graph["metadata"]["domain"] == DOMAIN_NAME


def test_no_source_graph_nodes_are_merged_into_the_output(spine):
    """The output is a graph ABOUT the joins. Member node IDs appear only as
    attributes -- never as nodes -- which is what keeps the one-domain-per-
    project assumption intact."""
    graph = build_crosswalk_graph(spine)
    ids = {n["id"] for n in graph["nodes"]}
    assert not ids & {"ct4", "lb1", "pv1", "pv9", "lb6", "pv2", "pv3", "pv4", "ct2"}


# ---------------------------------------------------------------------------
# Findings
# ---------------------------------------------------------------------------


def test_finding_becomes_a_link_named_after_its_rule(spine, findings):
    graph = build_crosswalk_graph(spine, findings)
    link = next(
        link for link in graph["links"] if link["relation_type"] == "UNLABELED_ADVERSE_EVENT"
    )
    assert link["source"] == "drug::semaglutide"
    assert link["target"] == "adverse_event::diarrhea"
    assert link["severity"] == "medium"
    assert link["attributes"]["subtype"] == "absent"
    assert link["attributes"]["probe_graph"] == "pharmacovigilance"


def test_finding_referencing_a_key_absent_from_the_spine_is_counted_not_silently_dropped(
    spine, findings
):
    """A findings file and a spine from different runs must not render as a
    clean, finding-free graph."""
    graph = build_crosswalk_graph(spine, findings)
    assert graph["metadata"]["finding_links"] == 1
    assert graph["metadata"]["findings_unattached"] == 1


def test_rule_error_records_do_not_become_links(spine, findings):
    graph = build_crosswalk_graph(spine, findings)
    assert not [link for link in graph["links"] if link["relation_type"] == "BROKEN_RULE"]


def test_findings_are_optional(spine):
    graph = build_crosswalk_graph(spine)
    assert graph["metadata"]["finding_links"] == 0
    assert all(link["relation_type"] == "PRESENT_IN" for link in graph["links"])


# ---------------------------------------------------------------------------
# Claims layer
# ---------------------------------------------------------------------------


def test_claims_layer_exposes_shared_keys_as_cross_references(spine):
    """examples/workbench/system_prompt.py renders top-level
    `cross_references`; this is what makes the join itself answerable in
    chat, not just its findings."""
    claims = build_claims_layer(spine)
    entities = [x["entity"] for x in claims["cross_references"]]
    assert entities == [
        "nausea (adverse_event)",
        "semaglutide (drug)",
        "tirzepatide (drug)",
    ]
    nausea = claims["cross_references"][0]
    assert nausea["appears_in"] == ["fda-product-labels", "pharmacovigilance"]
    assert nausea["axis"] == "adverse_event"


def test_unshared_keys_are_not_cross_references(spine):
    claims = build_claims_layer(spine)
    assert "diarrhea (adverse_event)" not in [x["entity"] for x in claims["cross_references"]]


def test_claims_layer_writes_both_the_top_level_and_super_domain_shapes(spine):
    """system_prompt.py reads the claims layer at top level; api_graph.py
    reads it under super_domain. Both must see the same cross-references."""
    claims = build_claims_layer(spine)
    assert claims["cross_references"] == claims["super_domain"]["cross_contract_entities"]


def test_claims_layer_carries_findings_under_custom_findings(spine, findings):
    claims = build_claims_layer(spine, findings)
    custom = claims["super_domain"]["custom_findings"]
    assert set(custom) == {"unlabeled_adverse_event", "broken_rule"}
    assert custom["unlabeled_adverse_event"][0]["severity"] == "medium"
    assert custom["broken_rule"][0]["status"] == "error"


def test_findings_gain_affected_entities_for_the_graph_severity_filter(spine, findings):
    """graph.js builds its severity filter's node set from
    `affected_entities`; deriving the crosswalk node IDs here keeps that
    frontend code from having to know the "<axis>::<key>" scheme."""
    claims = build_claims_layer(spine, findings)
    first = claims["super_domain"]["custom_findings"]["unlabeled_adverse_event"][0]
    assert first["affected_entities"] == ["drug::semaglutide", "adverse_event::diarrhea"]
    # A record with no subject/object evidence gets no key at all.
    assert "affected_entities" not in claims["super_domain"]["custom_findings"]["broken_rule"][0]


def test_building_the_claims_layer_does_not_mutate_the_findings_artifact(spine, findings):
    before = json.dumps(findings, sort_keys=True)
    build_claims_layer(spine, findings)
    assert json.dumps(findings, sort_keys=True) == before


def test_building_the_graph_does_not_mutate_the_spine(spine, findings):
    before = json.dumps(spine, sort_keys=True)
    build_crosswalk_graph(spine, findings)
    assert json.dumps(spine, sort_keys=True) == before


# ---------------------------------------------------------------------------
# Writing / CLI
# ---------------------------------------------------------------------------


def test_write_creates_a_project_shaped_output_directory(tmp_path, spine, findings):
    out = tmp_path / "nested" / "cw"
    summary = write_crosswalk_output(out, spine, findings)

    graph = json.loads((out / "graph_data.json").read_text())
    claims = json.loads((out / "claims_layer.json").read_text())
    assert graph["metadata"]["domain"] == DOMAIN_NAME
    assert claims["domain"] == DOMAIN_NAME
    assert summary["nodes"] == len(graph["nodes"])
    assert summary["links"] == len(graph["links"])
    assert summary["shared_keys"] == 3
    assert summary["cross_references"] == 3


def test_render_reads_both_artifacts_from_disk(tmp_path, spine, findings):
    (tmp_path / "spine.json").write_text(json.dumps(spine))
    (tmp_path / "findings.json").write_text(json.dumps(findings))
    summary = render(tmp_path / "spine.json", tmp_path / "out", tmp_path / "findings.json")
    assert summary["finding_links"] == 1
    assert (tmp_path / "out" / "graph_data.json").is_file()


def test_render_without_findings(tmp_path, spine):
    (tmp_path / "spine.json").write_text(json.dumps(spine))
    summary = render(tmp_path / "spine.json", tmp_path / "out")
    assert summary["finding_links"] == 0


@pytest.mark.parametrize(
    ("write", "match"),
    [
        (None, "not found"),
        ("{not json", "Could not parse"),
        ("[1, 2, 3]", "must be a JSON object"),
    ],
)
def test_a_missing_or_malformed_artifact_fails_loudly(tmp_path, write, match):
    """A truncated spine must never degrade into an empty graph that reads
    as 'the crosswalk found nothing'."""
    path = tmp_path / "spine.json"
    if write is not None:
        path.write_text(write)
    with pytest.raises(CrosswalkOutputError, match=match):
        load_json(path, "spine.json")


def test_a_json_object_that_is_not_a_spine_is_rejected_by_shape(tmp_path, findings):
    """Every artifact in a crosswalk run is a JSON object with a `graphs`
    block, so the wrong file in the --spine slot parses cleanly. Caught by
    the missing `axes` key, not by json.loads."""
    path = tmp_path / "findings.json"
    path.write_text(json.dumps(findings))
    with pytest.raises(CrosswalkOutputError, match="is not a spine"):
        load_spine(path)


def test_a_json_object_that_is_not_a_findings_file_is_rejected_by_shape(tmp_path):
    """The review artifacts written beside a real findings file carry their
    own top-level `findings` key in a different shape; pointing --findings
    at one used to render zero finding links and exit 0."""
    path = tmp_path / "review-data.json"
    path.write_text(
        json.dumps({"generated_at": "x", "graphs": {}, "axis_stats": {}, "findings": []})
    )
    with pytest.raises(CrosswalkOutputError, match="is not a cross-domain findings file"):
        load_findings(path)


def test_a_spine_that_joined_nothing_is_still_valid(tmp_path):
    """An empty `axes` block is a finding about the corpora, not a malformed
    file, and must not be conflated with the wrong-file case."""
    path = tmp_path / "spine.json"
    path.write_text(json.dumps({"spine_version": "1.0", "graphs": {"a": "/a"}, "axes": {}}))
    assert load_spine(path)["axes"] == {}


def test_a_findings_file_whose_rules_were_all_skipped_is_still_valid(tmp_path):
    """`custom_findings: {}` is exactly what an advisory-only run emits."""
    path = tmp_path / "findings.json"
    path.write_text(json.dumps({"super_domain": {"custom_findings": {}}}))
    assert load_findings(path)["super_domain"]["custom_findings"] == {}


def test_cli_warns_when_nothing_joined(tmp_path, capsys):
    (tmp_path / "spine.json").write_text(
        json.dumps(
            {
                "graphs": {"a": "/a", "b": "/b"},
                "axes": {"drug": {"aspirin": {"identifiers": {}, "graphs": {"a": ["n1"]}}}},
                "stats": {"drug": {"declared_by": ["a", "b"]}},
            }
        )
    )
    main(["render", "--spine", str(tmp_path / "spine.json"), "--out", str(tmp_path / "out")])
    assert "nothing joined" in capsys.readouterr().out


def test_cli_render_writes_and_reports(tmp_path, spine, findings, capsys):
    (tmp_path / "spine.json").write_text(json.dumps(spine))
    (tmp_path / "findings.json").write_text(json.dumps(findings))
    code = main(
        [
            "render",
            "--spine",
            str(tmp_path / "spine.json"),
            "--findings",
            str(tmp_path / "findings.json"),
            "--out",
            str(tmp_path / "out"),
            "--json",
        ]
    )
    assert code == 0
    summary = json.loads(capsys.readouterr().out)
    assert summary["domain"] == DOMAIN_NAME
    assert summary["findings_unattached"] == 1


def test_cli_reports_a_bad_spine_path_and_exits_nonzero(tmp_path, capsys):
    code = main(
        ["render", "--spine", str(tmp_path / "nope.json"), "--out", str(tmp_path / "out")]
    )
    assert code == 1
    assert "not found" in capsys.readouterr().err


def test_cli_warns_when_findings_could_not_be_attached(tmp_path, spine, findings, capsys):
    (tmp_path / "spine.json").write_text(json.dumps(spine))
    (tmp_path / "findings.json").write_text(json.dumps(findings))
    main(
        [
            "render",
            "--spine",
            str(tmp_path / "spine.json"),
            "--findings",
            str(tmp_path / "findings.json"),
            "--out",
            str(tmp_path / "out"),
        ]
    )
    assert "1 finding(s) referenced a canonical key absent" in capsys.readouterr().out


# ---------------------------------------------------------------------------
# Claims-layer authorship — the epistemic clobber guard
#
# core/label_epistemic.py rewrites claims_layer.json unconditionally, and a
# crosswalk output directory looks enough like a pipeline output directory
# that /epistract:epistemic accepts it. Before the generator stamp, a routine
# run replaced every join and finding with a biomedical-fallback summary.
# ---------------------------------------------------------------------------


@pytest.fixture
def crosswalk_dir(tmp_path, spine, findings) -> "object":
    """A rendered crosswalk output directory."""
    out = tmp_path / "cw"
    write_crosswalk_output(out, spine, findings)
    return out


def test_the_crosswalk_claims_layer_is_stamped_with_its_generator(spine):
    from core.crosswalk_output import GENERATOR

    assert build_claims_layer(spine)["generator"] == GENERATOR


def test_claims_layer_generator_reads_the_stamp(crosswalk_dir):
    from core.crosswalk_output import GENERATOR
    from core.label_epistemic import claims_layer_generator

    assert claims_layer_generator(crosswalk_dir) == GENERATOR


@pytest.mark.parametrize(
    ("contents", "why"),
    [
        (None, "no claims layer on disk"),
        ('{"summary": {}}', "written before stamping existed"),
        ("{not json", "unreadable"),
        ("[1, 2, 3]", "not an object"),
    ],
)
def test_an_unstamped_claims_layer_reads_as_unowned(tmp_path, contents, why):
    """None means 'this module may overwrite it'. Every claims layer written
    before stamping existed came from label_epistemic, so refusing to
    overwrite those would break re-running analysis on existing projects."""
    from core.label_epistemic import claims_layer_generator

    if contents is not None:
        (tmp_path / "claims_layer.json").write_text(contents)
    assert claims_layer_generator(tmp_path) is None, why


def test_epistemic_refuses_to_clobber_a_crosswalk_claims_layer(crosswalk_dir, capsys):
    from core.label_epistemic import analyze_epistemic

    before_claims = (crosswalk_dir / "claims_layer.json").read_text()
    before_graph = (crosswalk_dir / "graph_data.json").read_text()

    with pytest.raises(SystemExit) as exc:
        analyze_epistemic(crosswalk_dir, narrate=False)
    assert exc.value.code == 1

    err = capsys.readouterr().err
    assert "crosswalk_output" in err
    assert "--force" in err

    # Both files untouched: the guard runs before any write, because the
    # write path replaces graph_data.json too.
    assert (crosswalk_dir / "claims_layer.json").read_text() == before_claims
    assert (crosswalk_dir / "graph_data.json").read_text() == before_graph


def test_epistemic_overwrites_a_crosswalk_claims_layer_when_forced(crosswalk_dir):
    from core.label_epistemic import GENERATOR, analyze_epistemic

    analyze_epistemic(crosswalk_dir, narrate=False, force=True)
    written = json.loads((crosswalk_dir / "claims_layer.json").read_text())
    assert written["generator"] == GENERATOR


def test_epistemic_still_overwrites_its_own_and_legacy_output(tmp_path):
    """Backward compatibility: the guard must not break the ordinary
    re-run-analysis-on-an-existing-project path."""
    from core.label_epistemic import GENERATOR, analyze_epistemic

    out = tmp_path / "proj"
    out.mkdir()
    (out / "graph_data.json").write_text(
        json.dumps({"nodes": [], "links": [], "metadata": {"domain": "drug-discovery"}})
    )
    # A legacy, unstamped claims layer.
    (out / "claims_layer.json").write_text(json.dumps({"summary": {"note": "legacy"}}))

    analyze_epistemic(out, narrate=False)
    first = json.loads((out / "claims_layer.json").read_text())
    assert "legacy" not in json.dumps(first)
    assert first["generator"] == GENERATOR

    # And again, now over its own stamped output.
    analyze_epistemic(out, narrate=False)
    assert json.loads((out / "claims_layer.json").read_text())["generator"] == GENERATOR


# ---------------------------------------------------------------------------
# Domain package
# ---------------------------------------------------------------------------


def test_the_crosswalk_domain_package_resolves_like_any_other_domain():
    """`crosswalk` must be a real domain: /epistract:domain-list enumerates
    domains/ and the workbench resolves metadata.domain against it."""
    from core.domain_resolver import list_domains, resolve_domain

    assert DOMAIN_NAME in list_domains()
    resolved = resolve_domain(DOMAIN_NAME)
    schema = resolved["schema"]
    assert schema["name"] == "Crosswalk"
    assert "Graph" in schema["entity_types"]
    assert "PRESENT_IN" in schema["relation_types"]


def test_every_pharma_axis_has_a_matching_entity_type_and_legend_colour():
    """An axis with no entity type falls back to the workbench's rotating
    default palette instead of a stable colour."""
    from pathlib import Path

    import yaml

    root = Path(__file__).resolve().parent.parent
    axes = yaml.safe_load((root / "crosswalks" / "pharma.yaml").read_text())["axes"]
    schema = yaml.safe_load((root / "domains" / DOMAIN_NAME / "domain.yaml").read_text())
    template = yaml.safe_load(
        (root / "domains" / DOMAIN_NAME / "workbench" / "template.yaml").read_text()
    )

    for axis in axes:
        entity_type = axis_entity_type(axis)
        assert entity_type in schema["entity_types"], f"axis {axis!r} has no entity type"
        assert entity_type in template["entity_colors"], f"axis {axis!r} has no colour"
