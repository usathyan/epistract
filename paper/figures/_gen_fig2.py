#!/usr/bin/env python3
"""Generate publication-quality schema linkage diagram (Fig 2)."""

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import networkx as nx
import numpy as np

# ---------------------------------------------------------------------------
# Graph definition
# ---------------------------------------------------------------------------
G = nx.DiGraph()

nodes = {
    # Molecular (blues)
    "GENE":              {"label": "GENE\n(HGNC)",              "color": "#4393C3", "group": "molecular"},
    "PROTEIN":           {"label": "PROTEIN\n(UniProt)",        "color": "#2166AC", "group": "molecular"},
    "SEQUENCE_VARIANT":  {"label": "SEQUENCE\nVARIANT\n(ClinVar/COSMIC)", "color": "#92C5DE", "group": "molecular"},
    "PATHWAY":           {"label": "PATHWAY\n(KEGG/Reactome)",  "color": "#74ADD1", "group": "molecular"},
    "CELL_OR_TISSUE":    {"label": "CELL /\nTISSUE\n(Cell Ontology)",  "color": "#B8D4E8", "group": "molecular"},
    # Drug / compound (oranges)
    "COMPOUND":          {"label": "COMPOUND\n(ChEBI/DrugBank)", "color": "#F4A582", "group": "drug"},
    "MECHANISM_OF_ACTION": {"label": "MECHANISM\nOF ACTION",    "color": "#FDDBC7", "group": "drug"},
    # Clinical (greens)
    "DISEASE":           {"label": "DISEASE\n(MeSH)",           "color": "#66C2A5", "group": "clinical"},
    "CLINICAL_TRIAL":    {"label": "CLINICAL\nTRIAL\n(NCT)",    "color": "#A6DBA0", "group": "clinical"},
    "ADVERSE_EVENT":     {"label": "ADVERSE\nEVENT\n(MedDRA)",  "color": "#D9F0D3", "group": "clinical"},
    "BIOMARKER":         {"label": "BIOMARKER\n(BEST)",         "color": "#1B7837", "group": "clinical"},
}

for name, attrs in nodes.items():
    G.add_node(name, **attrs)

edges = [
    ("GENE",             "PROTEIN",           "ENCODES"),
    ("GENE",             "SEQUENCE_VARIANT",  "HAS_VARIANT"),
    ("PROTEIN",          "PATHWAY",           "PARTICIPATES_IN"),
    ("PROTEIN",          "CELL_OR_TISSUE",    "EXPRESSED_IN"),
    ("PATHWAY",          "DISEASE",           "IMPLICATED_IN"),
    ("SEQUENCE_VARIANT", "COMPOUND",          "CONFERS_RESISTANCE_TO"),
    ("SEQUENCE_VARIANT", "COMPOUND",          "PREDICTS_RESPONSE_TO"),
    ("COMPOUND",         "PROTEIN",           "TARGETS"),
    ("COMPOUND",         "PROTEIN",           "INHIBITS"),
    ("COMPOUND",         "DISEASE",           "INDICATED_FOR"),
    ("COMPOUND",         "CLINICAL_TRIAL",    "EVALUATED_IN"),
    ("COMPOUND",         "ADVERSE_EVENT",     "CAUSES"),
    ("COMPOUND",         "MECHANISM_OF_ACTION", "HAS_MECHANISM"),
    ("BIOMARKER",        "COMPOUND",          "PREDICTS_RESPONSE_TO"),
    ("BIOMARKER",        "DISEASE",           "DIAGNOSTIC_FOR"),
]

for src, dst, rel in edges:
    G.add_edge(src, dst, label=rel)

# ---------------------------------------------------------------------------
# Manual layout — top-to-bottom, layered
# ---------------------------------------------------------------------------
pos = {
    # Layer 0 – top
    "GENE":              (0.0,  1.0),
    # Layer 1
    "PROTEIN":           (-0.25, 0.78),
    "SEQUENCE_VARIANT":  (0.35,  0.78),
    # Layer 2
    "PATHWAY":           (-0.45, 0.55),
    "CELL_OR_TISSUE":    (-0.05, 0.55),
    # Layer 3 – central hub
    "COMPOUND":          (0.25,  0.40),
    "BIOMARKER":         (-0.55, 0.30),
    # Layer 4
    "DISEASE":           (-0.30, 0.15),
    "MECHANISM_OF_ACTION": (0.55, 0.28),
    # Layer 5 – bottom
    "CLINICAL_TRIAL":    (0.10,  0.02),
    "ADVERSE_EVENT":     (0.50,  0.05),
}

# ---------------------------------------------------------------------------
# Render
# ---------------------------------------------------------------------------
fig, ax = plt.subplots(figsize=(14, 16))
fig.patch.set_facecolor("white")
ax.set_facecolor("white")
ax.axis("off")

node_colors = [G.nodes[n]["color"] for n in G.nodes()]
node_labels = {n: G.nodes[n]["label"] for n in G.nodes()}

# Draw nodes
nx.draw_networkx_nodes(
    G, pos, ax=ax,
    node_size=5200,
    node_color=node_colors,
    edgecolors="#333333",
    linewidths=1.5,
    node_shape="o",
)

# Draw node labels
nx.draw_networkx_labels(
    G, pos, labels=node_labels, ax=ax,
    font_size=7.5, font_family="Helvetica", font_weight="bold",
    font_color="#1a1a1a",
)

# Draw edges with curvature for multi-edges
drawn_pairs = {}
for src, dst, data in G.edges(data=True):
    pair = (src, dst)
    rev_pair = (dst, src)
    # Determine connection style
    count = drawn_pairs.get(pair, 0) + drawn_pairs.get(rev_pair, 0)
    drawn_pairs[pair] = drawn_pairs.get(pair, 0) + 1

    if count == 0 and not G.has_edge(dst, src) and len([(s, d) for s, d in G.edges() if s == src and d == dst]) <= 1:
        style = "arc3,rad=0.0"
    else:
        rad = 0.15 * (count + 1) * (1 if count % 2 == 0 else -1)
        style = f"arc3,rad={rad}"

    nx.draw_networkx_edges(
        G, pos, edgelist=[(src, dst)], ax=ax,
        connectionstyle=style,
        edge_color="#555555",
        width=1.4,
        arrows=True,
        arrowsize=16,
        arrowstyle="-|>",
        min_source_margin=38,
        min_target_margin=38,
        alpha=0.85,
    )

# Edge labels — position manually along each edge
for src, dst, data in G.edges(data=True):
    label = data["label"].replace("_", " ")
    x1, y1 = pos[src]
    x2, y2 = pos[dst]
    # Place label at ~40% along the edge
    t = 0.40
    lx = x1 + t * (x2 - x1)
    ly = y1 + t * (y2 - y1)
    # Small perpendicular offset to avoid overlap with arrow
    dx, dy = x2 - x1, y2 - y1
    length = np.sqrt(dx**2 + dy**2) + 1e-9
    nx_, ny_ = -dy / length, dx / length
    offset = 0.018
    lx += nx_ * offset
    ly += ny_ * offset
    angle = np.degrees(np.arctan2(dy, dx))
    if angle > 90:
        angle -= 180
    elif angle < -90:
        angle += 180
    ax.text(
        lx, ly, label,
        fontsize=5.8, fontfamily="Helvetica", fontstyle="italic",
        color="#333333", ha="center", va="center",
        rotation=angle, rotation_mode="anchor",
        bbox=dict(boxstyle="round,pad=0.15", facecolor="white", edgecolor="none", alpha=0.85),
    )

# Legend
legend_items = [
    mpatches.Patch(facecolor="#4393C3", edgecolor="#333", label="Molecular entities"),
    mpatches.Patch(facecolor="#F4A582", edgecolor="#333", label="Drug / compound"),
    mpatches.Patch(facecolor="#66C2A5", edgecolor="#333", label="Clinical entities"),
]
ax.legend(
    handles=legend_items, loc="lower left", frameon=True,
    fontsize=10, title="Entity categories", title_fontsize=11,
    fancybox=False, edgecolor="#999999",
)

ax.set_title(
    "Drug-Discovery Knowledge-Graph Schema",
    fontsize=16, fontfamily="Helvetica", fontweight="bold", pad=20,
)

plt.tight_layout()
out = "/Users/umeshbhatt/code/epistract/paper/figures/fig2-schema-linkage.pdf"
fig.savefig(out, format="pdf", dpi=300, bbox_inches="tight", facecolor="white")
print(f"Saved → {out}")
