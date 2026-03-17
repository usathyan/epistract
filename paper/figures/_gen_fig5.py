"""Generate Fig 5: Schema coverage heatmap for the Epistract paper."""

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import numpy as np

# ── Data ──────────────────────────────────────────────────────────────
scenarios = ["S1\nNeuro-\ngenetics", "S2\nOncology", "S3\nRare\nDisease",
             "S4\nImmuno-\nOncology", "S5\nCardio-\nvascular"]

entity_labels = [
    "COMPOUND", "METABOLITE", "GENE", "PROTEIN", "PROTEIN_DOMAIN",
    "SEQUENCE_VARIANT", "CELL_OR_TISSUE", "DISEASE", "PHENOTYPE",
    "ADVERSE_EVENT", "CLINICAL_TRIAL", "BIOMARKER", "REGULATORY_ACTION",
    "PATHWAY", "MECHANISM_OF_ACTION", "ORGANIZATION", "PUBLICATION",
]
entity_data = np.array([
    [1,1,1,1,1],[0,1,1,0,0],[1,1,1,1,1],[1,1,1,1,1],[0,1,1,1,1],
    [1,1,1,0,1],[1,1,1,1,1],[1,1,1,1,1],[1,1,1,1,1],[0,1,1,1,1],
    [0,1,1,1,1],[0,1,1,1,1],[0,1,1,1,1],[1,1,1,1,1],[1,1,1,1,1],
    [0,1,1,1,1],[0,1,1,1,1],
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
relation_data = np.array([
    [0,1,0,0,1],[0,1,1,1,1],[0,1,0,0,0],[0,0,0,1,1],[0,1,1,1,1],
    [0,1,1,1,1],[0,0,1,0,1],[0,1,1,1,1],[0,1,1,1,1],[0,0,0,0,0],
    [0,1,0,1,0],[0,1,0,0,0],[1,1,1,1,1],[1,1,1,1,1],[1,1,1,1,1],
    [0,1,0,0,0],[1,0,0,0,0],[1,0,0,0,0],[1,1,0,0,1],[0,0,0,0,0],
    [0,0,0,0,0],[1,0,0,0,0],[1,0,0,0,0],[1,0,0,0,0],[0,1,1,1,1],
    [0,0,1,1,1],[0,0,0,0,0],[0,1,1,1,1],[0,0,1,0,0],[1,1,1,1,0],
])

# ── Colour map ────────────────────────────────────────────────────────
cmap = mcolors.ListedColormap(["#E8E8E8", "#3274A1"])  # light gray, blue

# ── Figure ────────────────────────────────────────────────────────────
n_ent = len(entity_labels)
n_rel = len(relation_labels)
height_ratio_ent = n_ent
height_ratio_rel = n_rel

fig, (ax_ent, ax_rel) = plt.subplots(
    2, 1,
    figsize=(8, 10),
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
        ax.text(n_cols + 0.15, i, f"{int(coverage[i])}/5",
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
