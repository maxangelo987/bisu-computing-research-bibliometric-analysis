import csv
import html
import os
import re
from collections import Counter, defaultdict

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
from wordcloud import WordCloud

# ============================================================
# LOAD DATA
# ============================================================
CSV_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        "bisu_computing_crossref_results.csv")
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "charts")
os.makedirs(OUTPUT_DIR, exist_ok=True)

rows = []
with open(CSV_FILE, encoding="utf-8-sig") as f:
    reader = csv.DictReader(f)
    for r in reader:
        r["Year"] = int(r["Year"]) if r["Year"].isdigit() else 0
        rows.append(r)

print(f"Loaded {len(rows)} records from CSV\n")

# ============================================================
# RESOLVE "BISU (campus unspecified)" TO ACTUAL CAMPUS
# ============================================================
COLLEGE_TO_CAMPUS = {
    "candijay": "Candijay Campus",
    "clarin": "Clarin Campus",
    "bilar": "Bilar Campus",
    "balilihan": "Balilihan Campus",
    "calape": "Calape Campus",
    "main campus": "Main Campus",
    "tagbilaran": "Main Campus",
    "college of sciences": "Candijay Campus",
    "college of technology": "Bilar Campus",
    "college of science and management": "Clarin Campus",
    "college of engineering and architecture": "Main Campus",
    "college of engineering, architecture and industrial design": "Main Campus",
    "computer engineering department": "Main Campus",
    "college of computing and information sciences": "Balilihan Campus",
}

resolved_count = 0
for r in rows:
    r["CampusOriginal"] = r["CampusMatched"]
    if r["CampusMatched"] != "BISU (campus unspecified)":
        continue
    aff_text = html.unescape(r["AllAffiliations"]).lower()
    resolved = None
    for keyword in ["candijay", "clarin", "bilar", "balilihan", "calape",
                    "main campus", "tagbilaran"]:
        if keyword in aff_text:
            resolved = COLLEGE_TO_CAMPUS[keyword]
            break
    if not resolved:
        for keyword in ["college of sciences", "college of technology",
                        "college of science and management",
                        "college of engineering and architecture",
                        "college of engineering, architecture and industrial design",
                        "computer engineering department",
                        "college of computing and information sciences"]:
            if keyword in aff_text:
                resolved = COLLEGE_TO_CAMPUS[keyword]
                break
    if resolved:
        r["CampusMatched"] = resolved
        resolved_count += 1

unspecified_total = sum(1 for r in rows if r["CampusOriginal"] == "BISU (campus unspecified)")
print(f"Resolved {resolved_count} of {unspecified_total} 'campus unspecified' records:")
campus_resolved_detail = Counter()
for r in rows:
    if r["CampusOriginal"] == "BISU (campus unspecified)":
        campus_resolved_detail[r["CampusMatched"]] += 1
for c, n in campus_resolved_detail.most_common():
    print(f"  -> {c}: {n}")

still_unspecified = sum(1 for r in rows if r["CampusMatched"] == "BISU (campus unspecified)")
print(f"  Still unspecified: {still_unspecified}\n")

# ============================================================
# AGGREGATE DATA
# ============================================================
year_counts = Counter()
campus_counts = Counter()
program_counts = Counter()
publisher_counts = Counter()
type_counts = Counter()
campus_year = defaultdict(Counter)
program_year = defaultdict(Counter)
campus_program = defaultdict(Counter)
venue_counts = Counter()

all_titles = []
all_abstracts = []

for r in rows:
    y = r["Year"]
    campus = r["CampusMatched"]
    program = r["ProgramInferred"]
    year_counts[y] += 1
    campus_counts[campus] += 1
    program_counts[program] += 1
    publisher_counts[r["Publisher"]] += 1
    type_counts[r["Type"]] += 1
    campus_year[campus][y] += 1
    program_year[program][y] += 1
    campus_program[campus][program] += 1
    venue_counts[r["Venue"]] += 1
    all_titles.append(r["Title"])
    if r.get("Abstract"):
        all_abstracts.append(r["Abstract"])

# ============================================================
# PRINT SUMMARY
# ============================================================
print("=" * 60)
print("BISU COMPUTING RESEARCH ANALYSIS SUMMARY")
print("=" * 60)
print(f"Total publications: {len(rows)}")
years = sorted(year_counts.keys())
print(f"Year range: {min(years)} - {max(years)}")
print(f"Campuses: {len(campus_counts)}")
print(f"Programs: {len(program_counts)}")

print("\n--- Publications by Year ---")
for y in sorted(year_counts):
    print(f"  {y}: {year_counts[y]}")

print("\n--- Publications by Campus (after resolution) ---")
for c, n in campus_counts.most_common():
    print(f"  {c}: {n}")

print("\n--- Publications by Program ---")
for p, n in program_counts.most_common():
    print(f"  {p}: {n}")

print("\n--- Publishers ---")
for p, n in publisher_counts.most_common():
    print(f"  {p}: {n}")

print("\n--- Publication Types ---")
for t, n in type_counts.most_common():
    print(f"  {t}: {n}")

print("\n--- Top 10 Venues ---")
for v, n in venue_counts.most_common(10):
    print(f"  {v}: {n}")

# ============================================================
# CHART HELPERS
# ============================================================
COLORS = ["#2196F3", "#4CAF50", "#FF9800", "#F44336", "#9C27B0",
          "#00BCD4", "#795548", "#607D8B", "#E91E63", "#CDDC39"]

def save(fig, name):
    path = os.path.join(OUTPUT_DIR, name)
    fig.savefig(path, dpi=150, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"  Saved {path}")

# ============================================================
# CHART 1: Publications Per Year
# ============================================================
fig, ax = plt.subplots(figsize=(10, 5))
ys = sorted(year_counts)
vals = [year_counts[y] for y in ys]
bars = ax.bar([str(y) for y in ys], vals, color="#2196F3", edgecolor="white", linewidth=0.5)
for bar, v in zip(bars, vals):
    ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.3,
            str(v), ha="center", va="bottom", fontweight="bold", fontsize=10)
ax.set_xlabel("Year")
ax.set_ylabel("Publications")
ax.set_title("BISU Computing Research Publications Per Year", fontweight="bold")
ax.yaxis.set_major_locator(ticker.MaxNLocator(integer=True))
plt.xticks(rotation=45)
save(fig, "01_publications_per_year.png")

# ============================================================
# CHART 2: Publications by Campus (after resolution)
# ============================================================
fig, ax = plt.subplots(figsize=(10, 5))
items = campus_counts.most_common()[::-1]
names = [i[0] for i in items]
vals = [i[1] for i in items]
bars = ax.barh(names, vals, color=COLORS[: len(names)], edgecolor="white")
for bar, v in zip(bars, vals):
    ax.text(bar.get_width() + 0.2, bar.get_y() + bar.get_height() / 2,
            str(v), ha="left", va="center", fontweight="bold")
ax.set_xlabel("Publications")
ax.set_title("Publications by Campus", fontweight="bold")
save(fig, "02_by_campus.png")

# ============================================================
# CHART 3: Publications by Program (Pie)
# ============================================================
fig, ax = plt.subplots(figsize=(8, 8))
labels = list(program_counts.keys())
sizes = list(program_counts.values())
wedges, texts, autotexts = ax.pie(
    sizes, labels=labels, autopct="%1.1f%%",
    colors=COLORS[: len(labels)], startangle=140, textprops={"fontsize": 9})
for t in autotexts:
    t.set_fontweight("bold")
ax.set_title("Distribution by Computing Program", fontweight="bold")
save(fig, "03_by_program_pie.png")

# ============================================================
# CHART 4: Campus x Year Heatmap
# ============================================================
all_years = sorted(year_counts)
all_campuses = sorted(campus_year.keys())
grid = [[campus_year[c][y] for y in all_years] for c in all_campuses]

fig, ax = plt.subplots(figsize=(12, 5))
im = ax.imshow(grid, cmap="YlGnBu", aspect="auto")
ax.set_xticks(range(len(all_years)))
ax.set_xticklabels([str(y) for y in all_years], rotation=45)
ax.set_yticks(range(len(all_campuses)))
ax.set_yticklabels(all_campuses)
max_val = max(max(row) for row in grid) if grid else 1
for i, row in enumerate(grid):
    for j, v in enumerate(row):
        if v > 0:
            ax.text(j, i, str(v), ha="center", va="center", fontweight="bold",
                    color="black" if v < max_val / 2 else "white")
plt.colorbar(im, ax=ax, label="Publications")
ax.set_title("Publications Heatmap: Campus x Year", fontweight="bold")
save(fig, "04_campus_year_heatmap.png")

# ============================================================
# CHART 5: Top Publishers
# ============================================================
fig, ax = plt.subplots(figsize=(10, 5))
top_pub = publisher_counts.most_common(8)
pnames = [p for p, c in top_pub]
pvals = [c for p, c in top_pub]
bars = ax.bar(range(len(pnames)), pvals, color="#9C27B0", edgecolor="white")
ax.set_xticks(range(len(pnames)))
ax.set_xticklabels(pnames, rotation=25, ha="right", fontsize=8)
for bar, v in zip(bars, pvals):
    ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.2,
            str(v), ha="center", va="bottom", fontweight="bold")
ax.set_ylabel("Publications")
ax.set_title("Top Publishers of BISU Computing Research", fontweight="bold")
ax.yaxis.set_major_locator(ticker.MaxNLocator(integer=True))
save(fig, "05_top_publishers.png")

# ============================================================
# CHART 6: Publication Type (Donut)
# ============================================================
fig, ax = plt.subplots(figsize=(7, 7))
tlabels = list(type_counts.keys())
tsizes = list(type_counts.values())
wedges, texts, autotexts = ax.pie(
    tsizes, labels=tlabels, autopct="%1.1f%%",
    colors=COLORS[: len(tlabels)], startangle=90, pctdistance=0.8)
centre = plt.Circle((0, 0), 0.55, fc="white")
ax.add_artist(centre)
ax.set_title("Publication Types", fontweight="bold")
save(fig, "06_publication_types_donut.png")

# ============================================================
# CHART 7: Program by Campus (Stacked Horizontal Bar)
# ============================================================
all_programs = sorted(program_counts.keys())
fig, ax = plt.subplots(figsize=(12, 6))
left = [0] * len(all_campuses)
for pi, prog in enumerate(all_programs):
    vals = [campus_program[c][prog] for c in all_campuses]
    ax.barh(all_campuses, vals, left=left, label=prog,
            color=COLORS[pi % len(COLORS)], edgecolor="white")
    left = [l + v for l, v in zip(left, vals)]
ax.set_xlabel("Publications")
ax.set_title("Program Distribution per Campus", fontweight="bold")
ax.legend(title="Program", bbox_to_anchor=(1.02, 1), loc="upper left", fontsize=8)
save(fig, "07_program_by_campus_stacked.png")

# ============================================================
# CHART 8: Research Trend by Program (Line)
# ============================================================
fig, ax = plt.subplots(figsize=(11, 5))
for pi, prog in enumerate(sorted(program_year.keys())):
    yvals = [program_year[prog][y] for y in all_years]
    ax.plot(all_years, yvals, marker="o", linewidth=2,
            color=COLORS[pi % len(COLORS)], label=prog)
ax.set_xlabel("Year")
ax.set_ylabel("Publications")
ax.set_title("Research Trend by Program Over Time", fontweight="bold")
ax.legend(title="Program", fontsize=8)
ax.grid(True, alpha=0.3)
ax.yaxis.set_major_locator(ticker.MaxNLocator(integer=True))
save(fig, "08_trend_by_program.png")

# ============================================================
# CHART 9: Word Cloud from Titles
# ============================================================
STOPWORDS_EXTRA = {
    "using", "based", "a", "an", "the", "of", "in", "for", "and", "with",
    "on", "to", "from", "by", "its", "as", "is", "are", "was", "were",
    "that", "this", "at", "or", "be", "it", "has", "have", "had", "not",
    "approach", "study", "analysis", "system", "model", "models",
    "campus", "university", "bohol", "island", "state", "philippines",
}

title_text = " ".join(all_titles)
wc = WordCloud(width=1200, height=600, background_color="white",
               colormap="viridis", max_words=80,
               stopwords=STOPWORDS_EXTRA, collocations=True,
               min_font_size=10)
wc.generate(title_text)

fig, ax = plt.subplots(figsize=(14, 7))
ax.imshow(wc, interpolation="bilinear")
ax.axis("off")
ax.set_title("Word Cloud: Research Titles", fontweight="bold", fontsize=16, pad=15)
save(fig, "09_wordcloud_titles.png")

# ============================================================
# CHART 10: Word Cloud from Abstracts (if available)
# ============================================================
if all_abstracts:
    abs_text = " ".join(all_abstracts)
    wc2 = WordCloud(width=1200, height=600, background_color="white",
                    colormap="plasma", max_words=80,
                    stopwords=STOPWORDS_EXTRA, collocations=True,
                    min_font_size=10)
    wc2.generate(abs_text)

    fig, ax = plt.subplots(figsize=(14, 7))
    ax.imshow(wc2, interpolation="bilinear")
    ax.axis("off")
    ax.set_title("Word Cloud: Abstracts", fontweight="bold", fontsize=16, pad=15)
    save(fig, "10_wordcloud_abstracts.png")
else:
    print("  Skipped abstract word cloud (no abstracts)")

# ============================================================
# CHART 11: Top 10 Conference Venues
# ============================================================
fig, ax = plt.subplots(figsize=(12, 6))
top_venues = venue_counts.most_common(10)[::-1]
vnames = [v[:65] + "..." if len(v) > 65 else v for v, c in top_venues]
vvals = [c for v, c in top_venues]
bars = ax.barh(vnames, vvals, color="#00BCD4", edgecolor="white")
for bar, v in zip(bars, vvals):
    ax.text(bar.get_width() + 0.1, bar.get_y() + bar.get_height() / 2,
            str(v), ha="left", va="center", fontweight="bold")
ax.set_xlabel("Publications")
ax.set_title("Top 10 Publication Venues", fontweight="bold")
save(fig, "11_top_venues.png")



# ============================================================
# CHART 12: Year-over-Year Growth Rate
# ============================================================
fig, ax = plt.subplots(figsize=(10, 5))
sorted_years = sorted(year_counts)
growth = []
growth_labels = []
for i in range(1, len(sorted_years)):
    prev = year_counts[sorted_years[i - 1]]
    curr = year_counts[sorted_years[i]]
    pct = ((curr - prev) / prev * 100) if prev > 0 else 0
    growth.append(pct)
    growth_labels.append(f"{sorted_years[i-1]}-{sorted_years[i]}")

bar_colors = ["#4CAF50" if g >= 0 else "#F44336" for g in growth]
bars = ax.bar(growth_labels, growth, color=bar_colors, edgecolor="white")
for bar, v in zip(bars, growth):
    ypos = bar.get_height() + 2 if v >= 0 else bar.get_height() - 8
    ax.text(bar.get_x() + bar.get_width() / 2, ypos,
            f"{v:+.0f}%", ha="center", va="bottom", fontweight="bold", fontsize=9)
ax.axhline(y=0, color="gray", linewidth=0.5)
ax.set_ylabel("Growth %")
ax.set_title("Year-over-Year Publication Growth Rate", fontweight="bold")
plt.xticks(rotation=45)
save(fig, "12_yoy_growth.png")

# ============================================================
# CHART 13: Cumulative Publications Over Time
# ============================================================
fig, ax = plt.subplots(figsize=(10, 5))
cumulative = []
total = 0
for y in sorted_years:
    total += year_counts[y]
    cumulative.append(total)
ax.fill_between(sorted_years, cumulative, alpha=0.3, color="#2196F3")
ax.plot(sorted_years, cumulative, marker="o", linewidth=2.5, color="#2196F3")
for y, c in zip(sorted_years, cumulative):
    ax.text(y, c + 1, str(c), ha="center", va="bottom", fontweight="bold", fontsize=10)
ax.set_xlabel("Year")
ax.set_ylabel("Cumulative Publications")
ax.set_title("Cumulative BISU Computing Research Output", fontweight="bold")
ax.grid(True, alpha=0.3)
ax.yaxis.set_major_locator(ticker.MaxNLocator(integer=True))
save(fig, "13_cumulative_publications.png")

# ============================================================
# DONE
# ============================================================
print(f"\nAll charts saved to: {OUTPUT_DIR}")
print("Open the 'charts' folder to view them.")
