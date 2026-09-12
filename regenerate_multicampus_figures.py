import csv
import os
from collections import Counter, defaultdict

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

CSV_FILE = "bisu_computing_crossref_results.csv"
OUTPUT_DIR = "charts"
os.makedirs(OUTPUT_DIR, exist_ok=True)

rows = []
with open(CSV_FILE, encoding="utf-8-sig") as f:
    for r in csv.DictReader(f):
        r["Year"] = int(r["Year"]) if (r.get("Year") or "").isdigit() else 0
        rows.append(r)


def campuses_for(row):
    value = (row.get("ContributingCampuses") or "").strip()
    if value:
        return [x.strip() for x in value.split("|") if x.strip()]
    campus = (row.get("CampusMatched") or "").strip()
    return [campus] if campus and campus != "Multiple BISU campuses" else []

campus_counts = Counter()
campus_year = defaultdict(Counter)
campus_program = defaultdict(Counter)
for r in rows:
    for campus in campuses_for(r):
        campus_counts[campus] += 1
        campus_year[campus][r["Year"]] += 1
        campus_program[campus][r.get("ProgramInferred") or "Computing (unspecified)"] += 1

# Figure 02: full-count campus productivity
fig, ax = plt.subplots(figsize=(10, 5))
items = campus_counts.most_common()[::-1]
names = [k for k, _ in items]
vals = [v for _, v in items]
bars = ax.barh(names, vals)
for bar, v in zip(bars, vals):
    ax.text(bar.get_width() + 0.2, bar.get_y() + bar.get_height()/2, str(v), va="center")
ax.set_xlabel("Publication credits (full counting)")
ax.set_title("BISU Computing Publications by Contributing Campus")
fig.tight_layout()
fig.savefig(os.path.join(OUTPUT_DIR, "02_by_campus.png"), dpi=150, bbox_inches="tight")
plt.close(fig)

# Figure 04: campus x year full-count heatmap
campuses = sorted(campus_counts)
years = sorted({r["Year"] for r in rows if r["Year"]})
grid = [[campus_year[c][y] for y in years] for c in campuses]
fig, ax = plt.subplots(figsize=(12, 5))
im = ax.imshow(grid, aspect="auto")
ax.set_xticks(range(len(years)))
ax.set_xticklabels(years, rotation=45)
ax.set_yticks(range(len(campuses)))
ax.set_yticklabels(campuses)
for i, row in enumerate(grid):
    for j, v in enumerate(row):
        if v:
            ax.text(j, i, str(v), ha="center", va="center")
fig.colorbar(im, ax=ax, label="Publication credits")
ax.set_title("Campus × Year Publication Credits (Full Counting)")
fig.tight_layout()
fig.savefig(os.path.join(OUTPUT_DIR, "04_campus_year_heatmap.png"), dpi=150, bbox_inches="tight")
plt.close(fig)

# Figure 07: program distribution per campus, full counting
programs = sorted({r.get("ProgramInferred") or "Computing (unspecified)" for r in rows})
fig, ax = plt.subplots(figsize=(12, 6))
left = [0] * len(campuses)
for program in programs:
    vals = [campus_program[c][program] for c in campuses]
    ax.barh(campuses, vals, left=left, label=program)
    left = [a+b for a, b in zip(left, vals)]
ax.set_xlabel("Publication credits (full counting)")
ax.set_title("Program Distribution by Contributing Campus")
ax.legend(title="Program", bbox_to_anchor=(1.02, 1), loc="upper left", fontsize=8)
fig.tight_layout()
fig.savefig(os.path.join(OUTPUT_DIR, "07_program_by_campus_stacked.png"), dpi=150, bbox_inches="tight")
plt.close(fig)

print("Regenerated campus figures using full counting.")
for campus, n in campus_counts.most_common():
    print(f"{campus}: {n}")
