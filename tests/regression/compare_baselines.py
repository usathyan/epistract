"""Baseline comparison logic for regression testing.

Compares current scenario output against V1/V2 baselines using
threshold-based validation for nodes, edges, communities, and
epistemic layer presence.

Usage:
    from tests.regression.compare_baselines import (
        load_baseline, load_graph_data, load_epistemic_data,
        compare_scenario, format_report,
    )
"""

from __future__ import annotations

import json
from pathlib import Path


def load_baseline(path: str) -> dict:
    """Read a baseline JSON file and return its contents as a dict.

    Args:
        path: Path to baseline JSON file.

    Returns:
        Baseline dict with scenario metadata, counts, and thresholds.
    """
    with Path(path).open() as f:
        return json.load(f)


def load_graph_data(output_dir: str) -> dict:
    """Read graph_data.json and communities.json from an output directory.

    Extracts node count (len of nodes list), edge count (len of links
    list), and community count (unique values in communities dict).

    Args:
        output_dir: Path to scenario output directory containing
            graph_data.json and communities.json.

    Returns:
        Dict with keys: nodes, edges, communities (int or None),
        documents (int or None).
    """
    output_path = Path(output_dir)
    result: dict = {
        "nodes": 0,
        "edges": 0,
        "communities": None,
        "documents": None,
    }

    graph_path = output_path / "graph_data.json"
    if graph_path.exists():
        with graph_path.open() as f:
            graph = json.load(f)
        result["nodes"] = len(graph.get("nodes", []))
        result["edges"] = len(graph.get("links", []))
        metadata = graph.get("metadata", {})
        result["documents"] = metadata.get("document_count")

    communities_path = output_path / "communities.json"
    if communities_path.exists():
        with communities_path.open() as f:
            communities = json.load(f)
        if isinstance(communities, dict):
            result["communities"] = len(set(communities.values()))
        elif isinstance(communities, list):
            result["communities"] = len(communities)

    return result


def load_epistemic_data(output_dir: str) -> dict:
    """Read claims_layer.json and check its existence and structure.

    Args:
        output_dir: Path to scenario output directory.

    Returns:
        Dict with keys: claims_layer_exists (bool),
        claims_count (int or None).
    """
    output_path = Path(output_dir)
    result: dict = {
        "claims_layer_exists": False,
        "claims_count": None,
    }

    claims_path = output_path / "claims_layer.json"
    if claims_path.exists():
        result["claims_layer_exists"] = True
        with claims_path.open() as f:
            claims = json.load(f)
        if isinstance(claims, list):
            result["claims_count"] = len(claims)
        elif isinstance(claims, dict):
            result["claims_count"] = len(claims.get("claims", []))

    return result


def compare_scenario(baseline: dict, actual: dict) -> dict:
    """Compare actual counts against baseline using threshold percentages.

    For each metric (nodes, edges, communities), computes the minimum
    required value as baseline * threshold_pct / 100 and checks whether
    the actual value meets or exceeds it.

    Args:
        baseline: Baseline dict from load_baseline().
        actual: Actual counts dict from load_graph_data().

    Returns:
        Dict with keys: passed (bool), scenario (str), results (dict
        of per-metric comparison dicts with baseline, actual, threshold,
        min_required, passed).
    """
    thresholds = baseline.get("thresholds", {})
    results: dict = {}
    all_passed = True

    # -- Graph structure metrics --
    for metric, threshold_key in [
        ("nodes", "nodes_pct"),
        ("edges", "edges_pct"),
        ("communities", "communities_pct"),
    ]:
        baseline_val = baseline.get(metric)
        actual_val = actual.get(metric)
        threshold_pct = thresholds.get(threshold_key)

        # Skip metrics where baseline is null (e.g., contracts communities)
        if baseline_val is None or threshold_pct is None:
            results[metric] = {
                "baseline": baseline_val,
                "actual": actual_val,
                "threshold": threshold_pct,
                "min_required": None,
                "passed": True,
                "skipped": True,
            }
            continue

        min_required = baseline_val * threshold_pct / 100
        passed = actual_val is not None and actual_val >= min_required

        results[metric] = {
            "baseline": baseline_val,
            "actual": actual_val,
            "threshold": threshold_pct,
            "min_required": min_required,
            "passed": passed,
        }

        if not passed:
            all_passed = False

    # -- Epistemic layer check --
    epistemic_baseline = baseline.get("epistemic", {})
    if epistemic_baseline.get("claims_layer_exists"):
        results["epistemic"] = {
            "baseline": "required",
            "actual": "present" if actual.get("claims_layer_exists") else "missing",
            "passed": actual.get("claims_layer_exists", False),
        }
        if not results["epistemic"]["passed"]:
            all_passed = False

    return {
        "passed": all_passed,
        "scenario": baseline.get("scenario", "unknown"),
        "scenario_label": baseline.get("scenario_label", "Unknown"),
        "results": results,
    }


def format_report(comparisons: list[dict]) -> str:
    """Format a human-readable table showing all scenarios and pass/fail.

    Args:
        comparisons: List of dicts from compare_scenario().

    Returns:
        Formatted string with scenario table and summary line.
    """
    lines: list[str] = []
    lines.append("")
    lines.append("=" * 78)
    lines.append("  REGRESSION REPORT")
    lines.append("=" * 78)
    lines.append("")

    header = f"{'Scenario':<30} {'Nodes':>12} {'Edges':>12} {'Communities':>12} {'Result':>8}"
    lines.append(header)
    lines.append("-" * 78)

    passed_count = 0
    failed_count = 0
    skipped_count = 0

    for comp in comparisons:
        scenario_label = comp.get("scenario_label", comp.get("scenario", "?"))
        results = comp.get("results", {})

        def _fmt_metric(key: str) -> str:
            r = results.get(key, {})
            if r.get("skipped"):
                return "skip"
            actual = r.get("actual", "?")
            baseline = r.get("baseline", "?")
            return f"{actual}/{baseline}"

        nodes_str = _fmt_metric("nodes")
        edges_str = _fmt_metric("edges")
        comms_str = _fmt_metric("communities")

        if comp.get("skipped"):
            result_str = "SKIP"
            skipped_count += 1
        elif comp["passed"]:
            result_str = "\033[32mPASS\033[0m"
            passed_count += 1
        else:
            result_str = "\033[31mFAIL\033[0m"
            failed_count += 1

        lines.append(
            f"{scenario_label:<30} {nodes_str:>12} {edges_str:>12} {comms_str:>12} {result_str:>8}"
        )

    lines.append("-" * 78)
    summary = f"  Total: {passed_count + failed_count + skipped_count}  |  "
    summary += f"\033[32mPassed: {passed_count}\033[0m  |  "
    summary += f"\033[31mFailed: {failed_count}\033[0m  |  "
    summary += f"Skipped: {skipped_count}"
    lines.append(summary)
    lines.append("=" * 78)
    lines.append("")

    return "\n".join(lines)
