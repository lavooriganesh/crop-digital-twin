import os
import matplotlib.pyplot as plt

output_png = os.path.join("data", "kalaburagi_class_distribution.png")

categories = [
    'Water Bodies\n(< 0.0)',
    'Built-up / Bare\n(0.0 - 0.2)',
    'Moderate Veg\n(0.2 - 0.5)',
    'Dense Canopy\n(>= 0.5)'
]
percentages = [1.77, 7.39, 61.29, 29.55]
pixel_counts = [104582, 436664, 3618954, 1744722]
colors = ['#1f77b4', '#d95f02', '#e6ab02', '#1b9e77']

fig, ax = plt.subplots(figsize=(9, 5), dpi=200)
bars = ax.bar(categories, percentages, color=colors, edgecolor='black', width=0.55)

ax.set_ylabel('Ground Area Share (%)', fontsize=11, fontweight='bold')
ax.set_title('Kalaburagi Regional Land Cover Distribution\nSentinel-2 Level-2A (5 January 2026)', fontsize=12, fontweight='bold')
ax.set_ylim(0, 70)
ax.grid(axis='y', linestyle='--', alpha=0.5)

for bar, pct, count in zip(bars, percentages, pixel_counts):
    height = bar.get_height()
    ax.annotate(f'{pct:.2f}%\n({count:,} px)',
                xy=(bar.get_x() + bar.get_width() / 2, height),
                xytext=(0, 4),
                textcoords="offset points",
                ha='center', va='bottom', fontsize=9, fontweight='bold')

plt.tight_layout()
plt.savefig(output_png, bbox_inches='tight')
plt.close()

print(f"[SUCCESS] Distribution chart generated: {output_png}")