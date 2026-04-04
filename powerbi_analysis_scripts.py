# ============================================================
# BISU Computing Research - Power BI Python Visual Scripts
# ============================================================
# HOW TO USE:
#   1. In Power BI, add a "Python visual" from Visualizations
#   2. Drag the needed columns into the Values field
#   3. Copy-paste ONE script block at a time into the editor
#   4. Click the Run (play) button
#
# NOTE: Power BI auto-creates a 'dataset' DataFrame with
#       the columns you dragged into the visual.
# ============================================================

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')

# ============================================================
# SCRIPT 1: Publications Per Year (Bar Chart)
# Required columns in Values: Year, Title
# ============================================================
fig, ax = plt.subplots(figsize=(10, 6))
yearly = dataset.groupby('Year')['Title'].nunique().sort_index()
bars = ax.bar(yearly.index.astype(str), yearly.values, color='#2196F3', edgecolor='white')
for bar, val in zip(bars, yearly.values):
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.3, str(val),
            ha='center', va='bottom', fontweight='bold', fontsize=11)
ax.set_xlabel('Year', fontsize=12)
ax.set_ylabel('Number of Publications', fontsize=12)
ax.set_title('BISU Computing Research Publications Per Year', fontsize=14, fontweight='bold')
plt.xticks(rotation=45)
plt.tight_layout()
plt.show()


# ============================================================
# SCRIPT 2: Publications by Campus (Horizontal Bar)
# Required columns in Values: CampusMatched, Title
# ============================================================
fig, ax = plt.subplots(figsize=(10, 6))
campus = dataset.groupby('CampusMatched')['Title'].nunique().sort_values()
colors = ['#FF9800', '#4CAF50', '#2196F3', '#9C27B0', '#F44336', '#00BCD4', '#795548']
bars = ax.barh(campus.index, campus.values, color=colors[:len(campus)], edgecolor='white')
for bar, val in zip(bars, campus.values):
    ax.text(bar.get_width() + 0.2, bar.get_y() + bar.get_height()/2, str(val),
            ha='left', va='center', fontweight='bold', fontsize=11)
ax.set_xlabel('Number of Publications', fontsize=12)
ax.set_title('BISU Computing Research by Campus', fontsize=14, fontweight='bold')
plt.tight_layout()
plt.show()


# ============================================================
# SCRIPT 3: Publications by Inferred Program (Pie Chart)
# Required columns in Values: ProgramInferred, Title
# ============================================================
fig, ax = plt.subplots(figsize=(8, 8))
program = dataset.groupby('ProgramInferred')['Title'].nunique()
colors = ['#2196F3', '#4CAF50', '#FF9800', '#F44336', '#9C27B0']
wedges, texts, autotexts = ax.pie(program.values, labels=program.index, autopct='%1.1f%%',
                                   colors=colors[:len(program)], startangle=140,
                                   textprops={'fontsize': 10})
for t in autotexts:
    t.set_fontweight('bold')
ax.set_title('Distribution by Computing Program', fontsize=14, fontweight='bold')
plt.tight_layout()
plt.show()


# ============================================================
# SCRIPT 4: Top 10 Researchers by Publication Count
# Required columns in Values: Researchers, Title
# ============================================================
from collections import Counter
import re

def normalize_name(name):
    name = name.strip()
    # Merge known variants
    variants = {
        'epifelward niño amora': 'Epifelward Niño O. Amora',
        'darrel abuyabor cardana': 'Darrel A. Cardaña',
        'darrel abuyabor cardaña': 'Darrel A. Cardaña',
        'darrel cardaña': 'Darrel A. Cardaña',
        'rey anthony godmalin': 'Rey Anthony G. Godmalin',
        'jesszon cano': 'Jesszon B. Cano',
        'estela ibanez': 'Estela Ibañez',
        'ryan carreon reyes': 'Ryan C. Reyes',
        'myriam j. polinar': 'Myriam C. Jumila-Polinar',
    }
    return variants.get(name.lower(), name)

counts = Counter()
for researchers in dataset['Researchers']:
    for name in str(researchers).split(','):
        name = normalize_name(name.strip())
        if name:
            counts[name] += 1

top10 = counts.most_common(10)
names = [n for n, c in top10][::-1]
vals = [c for n, c in top10][::-1]

fig, ax = plt.subplots(figsize=(10, 7))
bars = ax.barh(names, vals, color='#4CAF50', edgecolor='white')
for bar, val in zip(bars, vals):
    ax.text(bar.get_width() + 0.1, bar.get_y() + bar.get_height()/2, str(val),
            ha='left', va='center', fontweight='bold', fontsize=11)
ax.set_xlabel('Number of Publications', fontsize=12)
ax.set_title('Top 10 BISU Computing Researchers', fontsize=14, fontweight='bold')
plt.tight_layout()
plt.show()


# ============================================================
# SCRIPT 5: Campus x Year Heatmap
# Required columns in Values: Year, CampusMatched, Title
# ============================================================
import numpy as np

pivot = dataset.pivot_table(index='CampusMatched', columns='Year',
                             values='Title', aggfunc='nunique', fill_value=0)
fig, ax = plt.subplots(figsize=(12, 6))
im = ax.imshow(pivot.values, cmap='YlGnBu', aspect='auto')
ax.set_xticks(range(len(pivot.columns)))
ax.set_xticklabels(pivot.columns.astype(str), rotation=45)
ax.set_yticks(range(len(pivot.index)))
ax.set_yticklabels(pivot.index)
for i in range(len(pivot.index)):
    for j in range(len(pivot.columns)):
        val = pivot.values[i, j]
        if val > 0:
            ax.text(j, i, str(int(val)), ha='center', va='center',
                    fontweight='bold', color='black' if val < pivot.values.max()/2 else 'white')
plt.colorbar(im, ax=ax, label='Publications')
ax.set_title('Publications Heatmap: Campus vs Year', fontsize=14, fontweight='bold')
plt.tight_layout()
plt.show()


# ============================================================
# SCRIPT 6: Publisher Distribution (Top Publishers)
# Required columns in Values: Publisher, Title
# ============================================================
fig, ax = plt.subplots(figsize=(10, 6))
pub = dataset.groupby('Publisher')['Title'].nunique().sort_values(ascending=False).head(8)
bars = ax.bar(range(len(pub)), pub.values, color='#9C27B0', edgecolor='white')
ax.set_xticks(range(len(pub)))
ax.set_xticklabels(pub.index, rotation=30, ha='right', fontsize=9)
for bar, val in zip(bars, pub.values):
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.2, str(val),
            ha='center', va='bottom', fontweight='bold', fontsize=11)
ax.set_ylabel('Number of Publications', fontsize=12)
ax.set_title('Top Publishers of BISU Computing Research', fontsize=14, fontweight='bold')
plt.tight_layout()
plt.show()


# ============================================================
# SCRIPT 7: Publication Type Distribution (Donut Chart)
# Required columns in Values: Type, Title
# ============================================================
fig, ax = plt.subplots(figsize=(8, 8))
types = dataset.groupby('Type')['Title'].nunique()
colors = ['#2196F3', '#FF9800', '#4CAF50', '#F44336', '#9C27B0']
wedges, texts, autotexts = ax.pie(types.values, labels=types.index, autopct='%1.1f%%',
                                   colors=colors[:len(types)], startangle=90,
                                   pctdistance=0.8, textprops={'fontsize': 10})
centre = plt.Circle((0, 0), 0.55, fc='white')
ax.add_artist(centre)
ax.set_title('Publication Types', fontsize=14, fontweight='bold')
plt.tight_layout()
plt.show()


# ============================================================
# SCRIPT 8: Program Distribution by Campus (Stacked Bar)
# Required columns in Values: CampusMatched, ProgramInferred, Title
# ============================================================
fig, ax = plt.subplots(figsize=(12, 7))
ct = dataset.pivot_table(index='CampusMatched', columns='ProgramInferred',
                          values='Title', aggfunc='nunique', fill_value=0)
colors = ['#2196F3', '#4CAF50', '#FF9800', '#F44336', '#9C27B0']
ct.plot(kind='barh', stacked=True, ax=ax, color=colors[:len(ct.columns)], edgecolor='white')
ax.set_xlabel('Number of Publications', fontsize=12)
ax.set_title('Program Distribution per Campus', fontsize=14, fontweight='bold')
ax.legend(title='Program', bbox_to_anchor=(1.02, 1), loc='upper left', fontsize=9)
plt.tight_layout()
plt.show()


# ============================================================
# SCRIPT 9: Research Trend Over Time by Program (Line Chart)
# Required columns in Values: Year, ProgramInferred, Title
# ============================================================
fig, ax = plt.subplots(figsize=(11, 6))
trend = dataset.pivot_table(index='Year', columns='ProgramInferred',
                             values='Title', aggfunc='nunique', fill_value=0)
colors = ['#2196F3', '#4CAF50', '#FF9800', '#F44336', '#9C27B0']
for i, col in enumerate(trend.columns):
    ax.plot(trend.index, trend[col], marker='o', linewidth=2,
            color=colors[i % len(colors)], label=col)
ax.set_xlabel('Year', fontsize=12)
ax.set_ylabel('Number of Publications', fontsize=12)
ax.set_title('Research Trend by Program Over Time', fontsize=14, fontweight='bold')
ax.legend(title='Program', fontsize=9)
ax.grid(True, alpha=0.3)
plt.tight_layout()
plt.show()
