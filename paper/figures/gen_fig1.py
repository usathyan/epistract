#!/usr/bin/env python3
"""Generate Figure 1: Epistract architecture pipeline diagram."""

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

fig, ax = plt.subplots(figsize=(7, 2.5))
ax.set_xlim(0, 8.4)
ax.set_ylim(0, 2.5)
ax.axis('off')
fig.patch.set_facecolor('white')

# Font settings
font_label = {'family': 'Helvetica', 'size': 8, 'weight': 'bold'}
font_sub = {'family': 'Helvetica', 'size': 6, 'color': '#444444'}

# Colors
box_fill = '#E8EEF4'
box_edge = '#5A5A5A'
input_fill = '#F0F0F0'
output_fill = '#EAF2EA'
arrow_color = '#666666'

# Pipeline stages with wider spacing
stages = [
    (0.55,  'Documents',               'PDF, DOCX, HTML,\nTXT, Patents', input_fill),
    (1.65,  'Text Extraction',         '+ Chunking',                     box_fill),
    (2.75,  'Claude Agent\nExtraction', 'Entities + Relations',          box_fill),
    (3.85,  'Molecular\nValidation',   'RDKit, Biopython',              box_fill),
    (4.95,  'Graph\nBuilding',         'Dedup, Communities',             box_fill),
    (6.05,  'Community\nLabeling',     'Auto-generated\nnames',          box_fill),
]

box_w = 0.88
box_h = 0.90
y_center = 1.35

# Draw main pipeline boxes
for xc, label, sublabel, fill in stages:
    rect = FancyBboxPatch(
        (xc - box_w / 2, y_center - box_h / 2), box_w, box_h,
        boxstyle="round,pad=0.04",
        facecolor=fill, edgecolor=box_edge, linewidth=0.8,
    )
    ax.add_patch(rect)
    ax.text(xc, y_center + 0.13, label, ha='center', va='center',
            fontdict=font_label, clip_on=False)
    ax.text(xc, y_center - 0.25, sublabel, ha='center', va='center',
            fontdict=font_sub, clip_on=False)

# Arrows between main stages
for i in range(len(stages) - 1):
    x_start = stages[i][0] + box_w / 2 + 0.02
    x_end = stages[i + 1][0] - box_w / 2 - 0.02
    ax.annotate(
        '', xy=(x_end, y_center), xytext=(x_start, y_center),
        arrowprops=dict(arrowstyle='->', color=arrow_color, lw=1.2),
    )

# "Output" hub
out_x = 7.10
out_w = 0.50
out_h = 1.55
rect_out = FancyBboxPatch(
    (out_x - out_w / 2, y_center - out_h / 2), out_w, out_h,
    boxstyle="round,pad=0.04",
    facecolor=output_fill, edgecolor=box_edge, linewidth=0.8,
)
ax.add_patch(rect_out)
ax.text(out_x, y_center, 'Output', ha='center', va='center',
        fontdict=font_label, rotation=90)

# Arrow from Community Labeling to Output
ax.annotate(
    '', xy=(out_x - out_w / 2 - 0.02, y_center),
    xytext=(stages[-1][0] + box_w / 2 + 0.02, y_center),
    arrowprops=dict(arrowstyle='->', color=arrow_color, lw=1.2),
)

# Three output branches
branch_x = 7.95
branch_items = [
    ('Interactive\nViewer',              1.95),
    ('Export\n(GraphML, SQLite, CSV)',    1.35),
    ('Search\n& Query',                  0.75),
]
branch_w = 0.78
branch_h = 0.48

for blabel, by in branch_items:
    rect_b = FancyBboxPatch(
        (branch_x - branch_w / 2, by - branch_h / 2), branch_w, branch_h,
        boxstyle="round,pad=0.03",
        facecolor=output_fill, edgecolor=box_edge, linewidth=0.7,
    )
    ax.add_patch(rect_b)
    ax.text(branch_x, by, blabel, ha='center', va='center',
            fontdict={'family': 'Helvetica', 'size': 6})
    ax.annotate(
        '', xy=(branch_x - branch_w / 2 - 0.01, by),
        xytext=(out_x + out_w / 2 + 0.01, by),
        arrowprops=dict(arrowstyle='->', color=arrow_color, lw=0.9),
    )

# Title
ax.text(
    4.2, 2.42, 'Figure 1.  Epistract processing pipeline',
    ha='center', va='top',
    fontdict={'family': 'Helvetica', 'size': 9, 'style': 'italic'},
)

plt.tight_layout(pad=0.1)
out_path = 'paper/figures/fig1-architecture.pdf'
fig.savefig(
    out_path, format='pdf', dpi=300, bbox_inches='tight',
    facecolor='white', edgecolor='none',
)
print(f"Saved {out_path}")
