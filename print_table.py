import csv

with open('bisu_computing_crossref_results.csv', encoding='utf-8-sig') as f:
    rows = list(csv.DictReader(f))

rows.sort(key=lambda r: (r['CampusMatched'], r['Year'], r['Title']))

for i, r in enumerate(rows, 1):
    t = r['Title'][:85]
    if len(r['Title']) > 85:
        t += '...'
    res = r['Researchers'][:55]
    if len(r['Researchers']) > 55:
        res += '...'
    yr = r['Year']
    campus = r['CampusMatched']
    prog = r['ProgramInferred']
    print(f"{i}|{yr}|{campus}|{prog}|{t}|{res}")
