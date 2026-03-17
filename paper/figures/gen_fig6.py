"""Generate Fig 6: GraphRAG → Epistract evolution infographic."""

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch
import numpy as np

# ── Configuration ──────────────────────────────────────────────────────
DPI = 300
W, H = 8, 4  # inches

fig, ax = plt.subplots(figsize=(W, H), dpi=DPI)
ax.set_xlim(0, W)
ax.set_ylim(0, H)
ax.axis("off")
fig.patch.set_facecolor("white")

# ── Colours ────────────────────────────────────────────────────────────
LEFT_BG   = "#FFF0E8"   # warm peach
RIGHT_BG  = "#E8F5F0"   # cool mint
LEFT_HDR  = "#D84315"   # deep orange
RIGHT_HDR = "#00796B"   # teal
ARROW_CLR = "#455A64"   # blue-grey
STAT_CLR  = "#37474F"
TEXT_CLR  = "#212121"
BULLET_L  = "#E64A19"
BULLET_R  = "#00897B"

# ── Font helpers ───────────────────────────────────────────────────────
FONT = "Helvetica"
def fp(**kw):
    return dict(fontfamily=FONT, **kw)

# ── Panel geometry ─────────────────────────────────────────────────────
PAD = 0.15
panel_w = 3.15
panel_h = H - 2 * PAD
lx = PAD
rx = W - PAD - panel_w

# Draw panel backgrounds
for x, color in [(lx, LEFT_BG), (rx, RIGHT_BG)]:
    box = FancyBboxPatch(
        (x, PAD), panel_w, panel_h,
        boxstyle="round,pad=0.08",
        facecolor=color, edgecolor="#BDBDBD", linewidth=0.8,
    )
    ax.add_patch(box)

# ── Center arrow ───────────────────────────────────────────────────────
arrow_cx = W / 2
arrow_cy = H / 2
arrow_len = 0.65

ax.annotate(
    "", xy=(arrow_cx + arrow_len, arrow_cy),
    xytext=(arrow_cx - arrow_len, arrow_cy),
    arrowprops=dict(
        arrowstyle="->,head_width=0.35,head_length=0.2",
        color=ARROW_CLR, lw=2.5,
        connectionstyle="arc3,rad=0",
    ),
)
ax.text(arrow_cx, arrow_cy + 0.28, "Evolution", ha="center", va="bottom",
        fontsize=8, color=ARROW_CLR, fontweight="bold", fontstyle="italic",
        **fp())

# ── Helper: draw a panel ──────────────────────────────────────────────
def draw_panel(x0, header, subheader, items, stat, hdr_color, bullet_color):
    cx = x0 + panel_w / 2
    top = H - PAD

    # Header
    ax.text(cx, top - 0.28, header, ha="center", va="top",
            fontsize=14, fontweight="bold", color=hdr_color, **fp())
    # Subheader
    ax.text(cx, top - 0.55, subheader, ha="center", va="top",
            fontsize=7.5, color="#616161", fontstyle="italic", **fp())

    # Divider line
    ax.plot([x0 + 0.25, x0 + panel_w - 0.25], [top - 0.68, top - 0.68],
            color="#BDBDBD", lw=0.6)

    # Bullet items
    bullet_x = x0 + 0.32
    text_x = x0 + 0.52
    y = top - 0.88
    line_h = 0.34

    for item in items:
        ax.text(bullet_x, y, "\u25B8", ha="center", va="center",
                fontsize=7, color=bullet_color, **fp())
        ax.text(text_x, y, item, ha="left", va="center",
                fontsize=6.3, color=TEXT_CLR, **fp())
        y -= line_h

    # Bottom stat box
    stat_y = PAD + 0.32
    stat_box = FancyBboxPatch(
        (x0 + 0.2, stat_y - 0.15), panel_w - 0.4, 0.32,
        boxstyle="round,pad=0.05",
        facecolor="white", edgecolor="#BDBDBD", linewidth=0.5, alpha=0.85,
    )
    ax.add_patch(stat_box)
    ax.text(cx, stat_y, stat, ha="center", va="center",
            fontsize=6.5, fontweight="bold", color=STAT_CLR, **fp())


# ── Left panel content ────────────────────────────────────────────────
left_items = [
    "Embedding similarity edges",
    "Generic NER entities",
    'Numbered communities ("Community 1")',
    "No molecular validation",
    "No evidence traceability",
    "6 articles, single domain",
    "Scripts + manual setup",
]

draw_panel(
    lx,
    "GraphRAG",
    "Similarity-Based Assembly",
    left_items,
    "3,224 entities  /  2,242 relations",
    LEFT_HDR, BULLET_L,
)

# ── Right panel content ───────────────────────────────────────────────
right_items = [
    "Typed, directional relations (INHIBITS, CAUSES\u2026)",
    "17 entity types, 40+ ontologies",
    'Semantic community labels ("AD Risk Loci")',
    "RDKit + Biopython validation",
    "Source passage + confidence scores",
    "111 documents, 6 domains, zero retraining",
    "One-command plugin install",
]

draw_panel(
    rx,
    "Epistract",
    "Comprehension-Based Synthesis",
    right_items,
    "783 nodes  /  2,230 links  /  25/25 UATs",
    RIGHT_HDR, BULLET_R,
)

# ── Save ───────────────────────────────────────────────────────────────
out = "/Users/umeshbhatt/code/epistract/paper/figures/fig6-evolution.pdf"
fig.savefig(out, bbox_inches="tight", dpi=DPI, facecolor="white")
plt.close(fig)
print(f"Saved → {out}")
