import csv

# DOIs to update
main_campus_dois = [
    '10.1109/it67293.2026.11435679',
    '10.1109/it67293.2026.11435705',
    '10.1109/it67293.2026.11435749',
    '10.1109/it67293.2026.11435683',
]
bilar_doi = '10.1109/dsit67006.2025.11390029'

rows = []
updated = 0
with open('bisu_computing_crossref_results.csv', encoding='utf-8-sig') as f:
    reader = csv.DictReader(f)
    fieldnames = reader.fieldnames
    for r in reader:
        doi = r.get('DOI', '').strip()
        if doi in main_campus_dois:
            r['CampusMatched'] = 'Main Campus'
            r['CampusMatchedConfidence'] = 'manual'
            updated += 1
        elif doi == bilar_doi:
            r['CampusMatched'] = 'Bilar Campus'
            r['CampusMatchedConfidence'] = 'manual'
            updated += 1
        rows.append(r)

with open('bisu_computing_crossref_results.csv', 'w', encoding='utf-8-sig', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(rows)

print(f"Updated {updated} records. Total rows: {len(rows)}")
