import csv

with open('bisu_computing_crossref_results.csv', encoding='utf-8-sig') as f:
    reader = csv.DictReader(f)
    rows = [r for r in reader if r['CampusMatched'] == 'BISU (campus unspecified)']

kws = {
    'candijay', 'clarin', 'bilar', 'balilihan', 'calape', 'tagbilaran',
    'college of technology', 'college of sciences',
    'college of science and management', 'college of engineering',
    'college of advanced'
}

unresolved = []
for r in rows:
    aff = r.get('AllAffiliations', '').lower()
    if not any(k in aff for k in kws):
        unresolved.append(r)

print(f"{len(unresolved)} publications still campus-unspecified:\n")
for i, r in enumerate(unresolved, 1):
    print(f"{i}. {r['Title']}")
    print(f"   Researchers: {r['Researchers']}")
    print(f"   Year: {r['Year']}")
    print(f"   DOI: {r['DOI']}")
    print(f"   Affiliations: {r['AllAffiliations'][:300]}")
    print()
