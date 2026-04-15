"""Generate Fig 5: Schema coverage heatmap for the Epistract paper."""

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import numpy as np

# ── Data ──────────────────────────────────────────────────────────────
scenarios = ["S1\nNeuro-\ngenetics", "S2\nOncology", "S3\nRare\nDisease",
             "S4\nImmuno-\nOncology", "S5\nCardio-\nvascular", "S6\nGLP-1\nCI"]

entity_labels = [
    "COMPOUND", "METABOLITE", "GENE", "PROTEIN", "PROTEIN_DOMAIN",
    "SEQUENCE_VARIANT", "CELL_OR_TISSUE", "DISEASE", "PHENOTYPE",
    "ADVERSE_EVENT", "CLINICAL_TRIAL", "BIOMARKER", "REGULATORY_ACTION",
    "PATHWAY", "MECHANISM_OF_ACTION", "ORGANIZATION", "PUBLICATION",
]
# S6 entity presence: COMPOUND(34), METABOLITE(2), GENE(0), PROTEIN(11),
# PROTEIN_DOMAIN(2), SEQUENCE_VARIANT(0), CELL_OR_TISSUE(3), DISEASE(31),
# PHENOTYPE(8), ADVERSE_EVENT(9), CLINICAL_TRIAL(19), BIOMARKER(9),
# REGULATORY_ACTION(1), PATHWAY(9), MECHANISM_OF_ACTION(14), ORGANIZATION(8),
# PUBLICATION(9) + PEPTIDE_SEQUENCE(3) mapped to entity types
entity_data = np.array([
    # S1 S2 S3 S4 S5 S6
    [1, 1, 1, 1, 1, 1],  # COMPOUND
    [0, 1, 1, 0, 0, 1],  # METABOLITE
    [1, 1, 1, 1, 1, 0],  # GENE
    [1, 1, 1, 1, 1, 1],  # PROTEIN
    [0, 1, 1, 1, 1, 1],  # PROTEIN_DOMAIN
    [1, 1, 1, 0, 1, 0],  # SEQUENCE_VARIANT
    [1, 1, 1, 1, 1, 1],  # CELL_OR_TISSUE
    [1, 1, 1, 1, 1, 1],  # DISEASE
    [1, 1, 1, 1, 1, 1],  # PHENOTYPE
    [0, 1, 1, 1, 1, 1],  # ADVERSE_EVENT
    [0, 1, 1, 1, 1, 1],  # CLINICAL_TRIAL
    [0, 1, 1, 1, 1, 1],  # BIOMARKER
    [0, 1, 1, 1, 1, 1],  # REGULATORY_ACTION
    [1, 1, 1, 1, 1, 1],  # PATHWAY
    [1, 1, 1, 1, 1, 1],  # MECHANISM_OF_ACTION
    [0, 1, 1, 1, 1, 1],  # ORGANIZATION
    [0, 1, 1, 1, 1, 1],  # PUBLICATION
])

relation_labels = [
    "TARGETS", "INHIBITS", "ACTIVATES", "BINDS_TO", "HAS_MECHANISM",
    "INDICATED_FOR", "CONTRAINDICATED_FOR", "EVALUATED_IN", "CAUSES",
    "DERIVED_FROM", "COMBINED_WITH", "INTERACTS_WITH", "ENCODES",
    "PARTICIPATES_IN", "IMPLICATED_IN", "CONFERS_RESISTANCE_TO",
    "EXPRESSED_IN", "LOCALIZED_TO", "HAS_VARIANT", "HAS_DOMAIN",
    "METABOLIZED_BY", "PHOSPHORYLATES", "FORMS_COMPLEX_WITH",
    "REGULATES_EXPRESSION", "PREDICTS_RESPONSE_TO", "DIAGNOSTIC_FOR",
    "DEVELOPED_BY", "PUBLISHED_IN", "GRANTS_APPROVAL_FOR",
    "ASSOCIATED_WITH",
]
# S6 relation presence from graph: TARGETS(3), ACTIVATES(26), BINDS_TO(4),
# HAS_MECHANISM(20), INDICATED_FOR(64), EVALUATED_IN(21), CAUSES(15),
# DERIVED_FROM(3), COMBINED_WITH(6), PARTICIPATES_IN(12), IMPLICATED_IN(6),
# EXPRESSED_IN(3), HAS_DOMAIN(2), REGULATES_EXPRESSION(1),
# PREDICTS_RESPONSE_TO(1), DIAGNOSTIC_FOR(7), DEVELOPS(11), PUBLISHED_IN(9),
# GRANTS_APPROVAL_FOR(2), ASSOCIATED_WITH(30)
relation_data = np.array([
    # S1 S2 S3 S4 S5 S6
    [0, 1, 0, 0, 1, 1],  # TARGETS
    [0, 1, 1, 1, 1, 0],  # INHIBITS
    [0, 1, 0, 0, 0, 1],  # ACTIVATES
    [0, 0, 0, 1, 1, 1],  # BINDS_TO
    [0, 1, 1, 1, 1, 1],  # HAS_MECHANISM
    [0, 1, 1, 1, 1, 1],  # INDICATED_FOR
    [0, 0, 1, 0, 1, 0],  # CONTRAINDICATED_FOR
    [0, 1, 1, 1, 1, 1],  # EVALUATED_IN
    [0, 1, 1, 1, 1, 1],  # CAUSES
    [0, 0, 0, 0, 0, 1],  # DERIVED_FROM
    [0, 1, 0, 1, 0, 1],  # COMBINED_WITH
    [0, 1, 0, 0, 0, 0],  # INTERACTS_WITH
    [1, 1, 1, 1, 1, 0],  # ENCODES
    [1, 1, 1, 1, 1, 1],  # PARTICIPATES_IN
    [1, 1, 1, 1, 1, 1],  # IMPLICATED_IN
    [0, 1, 0, 0, 0, 0],  # CONFERS_RESISTANCE_TO
    [1, 0, 0, 0, 0, 1],  # EXPRESSED_IN
    [1, 0, 0, 0, 0, 0],  # LOCALIZED_TO
    [1, 1, 0, 0, 1, 0],  # HAS_VARIANT
    [0, 0, 0, 0, 0, 1],  # HAS_DOMAIN
    [0, 0, 0, 0, 0, 0],  # METABOLIZED_BY
    [1, 0, 0, 0, 0, 0],  # PHOSPHORYLATES
    [1, 0, 0, 0, 0, 0],  # FORMS_COMPLEX_WITH
    [1, 0, 0, 0, 0, 1],  # REGULATES_EXPRESSION
    [0, 1, 1, 1, 1, 1],  # PREDICTS_RESPONSE_TO
    [0, 0, 1, 1, 1, 1],  # DIAGNOSTIC_FOR
    [0, 0, 0, 0, 0, 1],  # DEVELOPED_BY
    [0, 1, 1, 1, 1, 1],  # PUBLISHED_IN
    [0, 0, 1, 0, 0, 1],  # GRANTS_APPROVAL_FOR
    [1, 1, 1, 1, 0, 1],  # ASSOCIATED_WITH
])

# ── Colour map ────────────────────────────────────────────────────────
cmap = mcolors.ListedColormap(["#E8E8E8", "#3274A1"])  # light gray, blue

# ── Figure ────────────────────────────────────────────────────────────
n_ent = len(entity_labels)
n_rel = len(relation_labels)
height_ratio_ent = n_ent
height_ratio_rel = n_rel
n_scenarios = 6

fig, (ax_ent, ax_rel) = plt.subplots(
    2, 1,
    figsize=(9, 10),
    gridspec_kw={"height_ratios": [height_ratio_ent, height_ratio_rel],
                 "hspace": 0.35},
)

def draw_heatmap(ax, data, row_labels, title):
    n_rows, n_cols = data.shape
    coverage = data.sum(axis=1)

    # Append coverage column (use NaN so we can colour it differently)
    ax.imshow(data, cmap=cmap, aspect="auto", vmin=0, vmax=1)

    # Grid lines
    ax.set_xticks(np.arange(n_cols) - 0.5, minor=True)
    ax.set_yticks(np.arange(n_rows) - 0.5, minor=True)
    ax.grid(which="minor", color="white", linewidth=1.5)
    ax.tick_params(which="minor", bottom=False, left=False)

    # Labels
    ax.set_xticks(range(n_cols))
    ax.set_xticklabels(scenarios, fontsize=7, fontfamily="sans-serif")
    ax.set_yticks(range(n_rows))
    ax.set_yticklabels(row_labels, fontsize=7, fontfamily="sans-serif", fontstyle="normal")
    ax.xaxis.set_ticks_position("top")
    ax.xaxis.set_label_position("top")

    # Title
    ax.set_title(title, fontsize=10, fontweight="bold", fontfamily="sans-serif",
                 pad=12, loc="left")

    # Coverage column on the right
    for i in range(n_rows):
        ax.text(n_cols + 0.15, i, f"{int(coverage[i])}/{n_scenarios}",
                va="center", ha="center", fontsize=7, fontfamily="sans-serif",
                color="#333333")
    ax.text(n_cols + 0.15, -1.1, "Coverage", va="center", ha="center",
            fontsize=7, fontweight="bold", fontfamily="sans-serif", color="#333333")

    ax.set_xlim(-0.5, n_cols - 0.5 + 0.8)

    # Remove spines
    for spine in ax.spines.values():
        spine.set_visible(False)

draw_heatmap(ax_ent, entity_data, entity_labels, "Entity Types")
draw_heatmap(ax_rel, relation_data, relation_labels, "Relation Types")

fig.patch.set_facecolor("white")

out = "/Users/umeshbhatt/code/epistract/paper/figures/fig5-schema-coverage.pdf"
fig.savefig(out, dpi=300, bbox_inches="tight", facecolor="white")
print(f"Saved → {out}")
