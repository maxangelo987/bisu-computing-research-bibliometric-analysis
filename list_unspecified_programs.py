import csv

with open('bisu_computing_crossref_results.csv', encoding='utf-8-sig') as f:
    rows = [r for r in csv.DictReader(f) if r['ProgramInferred'] == 'Computing (unspecified)']

print(f"{len(rows)} records with 'Computing (unspecified)':\n")
for i, r in enumerate(rows, 1):
    title = r['Title'][:110]
    print(f"{i}. [{r['Year']}] {title}")
    print(f"   Subjects: {r['Subjects'][:100]}")
    print()
