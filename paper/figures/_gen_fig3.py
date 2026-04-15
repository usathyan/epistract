"""Generate Fig 3: 6-panel composite of scenario graph screenshots."""

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.image import imread

screenshots_dir = "/Users/umeshbhatt/code/epistract/tests/scenarios/screenshots"

panels = [
    ("scenario-01-graph.png", "(a) Neurogenetics — 149 nodes"),
    ("scenario-02-graph.png", "(b) Oncology — 108 nodes"),
    ("scenario-03-graph.png", "(c) Rare Disease — 94 nodes"),
    ("scenario-04-graph.png", "(d) Immuno-Oncology — 132 nodes"),
    ("scenario-05-graph.png", "(e) CV/Inflammation — 94 nodes"),
    ("scenario-06-graph.png", "(f) GLP-1 CI — 206 nodes"),
]

fig, axes = plt.subplots(2, 3, figsize=(18, 11))
fig.patch.set_facecolor("white")

for idx, (fname, label) in enumerate(panels):
    row, col = divmod(idx, 3)
    ax = axes[row][col]
    img = imread(f"{screenshots_dir}/{fname}")
    ax.imshow(img)
    ax.set_title(label, fontsize=10, fontweight="bold", fontfamily="sans-serif", pad=8)
    ax.axis("off")

plt.subplots_adjust(wspace=0.05, hspace=0.12)

out = "/Users/umeshbhatt/code/epistract/paper/figures/fig3-scenario-graphs.png"
fig.savefig(out, dpi=200, bbox_inches="tight", facecolor="white")
print(f"Saved → {out}")
