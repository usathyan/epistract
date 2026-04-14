"""Regression runner for epistract scenario validation.

Validates current scenario output against V1/V2 baselines using
threshold-based comparison. Reports pass/fail per scenario with
colored terminal output.

Usage:
    python tests/regression/run_regression.py
    python tests/regression/run_regression.py --baselines tests/baselines/v1/
    python tests/regression/run_regression.py --scenario s01_picalm
    python tests/regression/run_regression.py --update-baselines
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from compare_baselines import (
    compare_scenario,
    format_report,
    load_baseline,
    load_epistemic_data,
    load_graph_data,
)


# ---------------------------------------------------------------------------
# Scenario output directory mapping
# ---------------------------------------------------------------------------

# Map scenario names to their output directories relative to --output-dir
_DRUG_DISCOVERY_SCENARIOS = {
    "01_picalm_alzheimers",
    "02_kras_g12c_landscape",
    "03_rare_disease",
    "04_immunooncology",
    "05_cardiovascular",
    "06_glp1_landscape",
}


def _resolve_output_dir(baseline: dict, corpora_root: Path) -> Path | None:
    """Resolve the output directory for a given baseline scenario.

    Prefers `output-v2/` when present so Phase 11 V2 validation runs
    can coexist with V1 output that remains pinned as the canonical
    baseline input. Falls back to `output/` once V2 is canonical.

    Args:
        baseline: Baseline dict with scenario and corpora_dir keys.
        corpora_root: Root directory for corpora (e.g., tests/corpora/).

    Returns:
        Path to the output directory, or None if not found.
    """
    scenario = baseline.get("scenario", "")

    if scenario in _DRUG_DISCOVERY_SCENARIOS:
        for subdir in ("output-v2", "output"):
            candidate = corpora_root / scenario / subdir
            if candidate.exists():
                return candidate
        return None

    if "contracts" in scenario:
        for candidate in [
            Path("sample-output-v2"),
            Path("sample-output"),
            corpora_root / "contracts" / "output-v2",
            corpora_root / "contracts" / "output",
            corpora_root.parent / "sample-output-v2",
            corpora_root.parent / "sample-output",
        ]:
            if candidate.exists():
                return candidate
        return None

    return None


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    """Run regression suite against baselines."""
    parser = argparse.ArgumentParser(
        description="Regression suite for epistract scenario validation"
    )
    parser.add_argument(
        "--baselines",
        default=None,
        help="Path to baseline directory (default: tests/baselines/v2/, fallback v1/)",
    )
    parser.add_argument(
        "--output-dir",
        default="tests/corpora",
        help="Path to scenario output directories (default: tests/corpora/)",
    )
    parser.add_argument(
        "--skip-extraction",
        action="store_true",
        help="Only validate existing output, don't run extraction",
    )
    parser.add_argument(
        "--update-baselines",
        action="store_true",
        help="Save current output as new V2 baselines",
    )
    parser.add_argument(
        "--scenario",
        default=None,
        help="Run only a specific scenario (e.g., s01_picalm)",
    )
    args = parser.parse_args()

    # Resolve baselines directory
    if args.baselines:
        baselines_dir = Path(args.baselines)
    elif Path("tests/baselines/v2").exists():
        baselines_dir = Path("tests/baselines/v2")
    else:
        baselines_dir = Path("tests/baselines/v1")

    if not baselines_dir.exists():
        print(f"\033[31mError: Baselines directory not found: {baselines_dir}\033[0m")
        sys.exit(1)

    corpora_root = Path(args.output_dir)

    # Load all baseline files
    baseline_files = sorted(baselines_dir.glob("*.json"))
    if not baseline_files:
        print(f"\033[31mError: No baseline files found in {baselines_dir}\033[0m")
        sys.exit(1)

    # Filter by scenario if specified
    if args.scenario:
        baseline_files = [
            f for f in baseline_files if args.scenario in f.stem
        ]
        if not baseline_files:
            print(f"\033[31mError: No baseline found matching '{args.scenario}'\033[0m")
            sys.exit(1)

    # Update baselines mode
    if args.update_baselines:
        _update_baselines(baseline_files, corpora_root)
        return

    # Compare mode (default)
    comparisons: list[dict] = []

    for bf in baseline_files:
        baseline = load_baseline(str(bf))
        output_dir = _resolve_output_dir(baseline, corpora_root)

        if output_dir is None:
            print(
                f"  \033[33mWARN: Output not found for "
                f"{baseline.get('scenario_label', bf.stem)} — skipping\033[0m"
            )
            comparisons.append({
                "passed": True,
                "skipped": True,
                "scenario": baseline.get("scenario", bf.stem),
                "scenario_label": baseline.get("scenario_label", bf.stem),
                "results": {},
            })
            continue

        actual = load_graph_data(str(output_dir))
        epistemic = load_epistemic_data(str(output_dir))
        actual.update(epistemic)

        comparison = compare_scenario(baseline, actual)
        comparisons.append(comparison)

    # Print report
    report = format_report(comparisons)
    print(report)

    # Exit code
    any_failed = any(
        not c["passed"] for c in comparisons if not c.get("skipped")
    )
    if any_failed:
        sys.exit(1)
    else:
        sys.exit(0)


def _update_baselines(
    baseline_files: list[Path], corpora_root: Path
) -> None:
    """Save current output as new V2 baselines.

    Args:
        baseline_files: List of existing baseline JSON paths.
        corpora_root: Root directory for corpora.
    """
    v2_dir = Path("tests/baselines/v2")
    v2_dir.mkdir(parents=True, exist_ok=True)

    for bf in baseline_files:
        baseline = load_baseline(str(bf))
        output_dir = _resolve_output_dir(baseline, corpora_root)

        if output_dir is None:
            print(f"  \033[33mSKIP: No output for {bf.stem}\033[0m")
            continue

        actual = load_graph_data(str(output_dir))
        epistemic = load_epistemic_data(str(output_dir))

        new_baseline = {
            "scenario": baseline["scenario"],
            "scenario_label": baseline["scenario_label"],
            "version": "v2",
            "corpora_dir": baseline["corpora_dir"],
            "documents": actual.get("documents") or baseline.get("documents"),
            "nodes": actual["nodes"],
            "edges": actual["edges"],
            "communities": actual["communities"],
            "epistemic": {
                "claims_layer_exists": epistemic.get("claims_layer_exists", False),
                **{k: v for k, v in baseline.get("epistemic", {}).items()
                   if k != "claims_layer_exists"},
            },
            "thresholds": baseline.get("thresholds", {}),
        }

        out_path = v2_dir / bf.name
        with out_path.open("w") as f:
            json.dump(new_baseline, f, indent=2)
            f.write("\n")

        print(
            f"  \033[32mUPDATED: {out_path} "
            f"(nodes={actual['nodes']}, edges={actual['edges']})\033[0m"
        )

    print(f"\n  V2 baselines written to {v2_dir}/")


if __name__ == "__main__":
    main()
