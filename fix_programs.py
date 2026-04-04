import csv

# Manual reclassification based on title content analysis:
# - Deep learning, CNN, ML, computer vision, image recognition, NLP -> Computer Science
# - GIS, spatial analysis, system development, robotic -> Information Technology
# - Education/teaching studies (non-technical) -> Information Technology
# - Pure math/topology -> Computer Science
# - Structural equation modeling, AI adoption -> Information Technology
TITLE_TO_PROGRAM = {
    "Enhancing Mango Leaf Disease Diagnosis Using Convolutional Neural Networks": "Computer Science",
    "Deep Learning Approach For Weed Detection To Determine Soil Condition": "Computer Science",
    "Exploring Sentiment and Moral Dynamics in Children": "Computer Science",  # partial match
    "Predicting Student Entrepreneurial Intentions": "Computer Science",
    "Subject-taught mismatch": "Information Technology",
    "OPeraTE.AI": "Information Technology",
    "Enhancing Scholarship Allocation Through Machine Learning": "Computer Science",
    "MangroveLens": "Information Technology",
    "Predicting the Use Behavior of Micro-Mobility": "Information Technology",
    "Predicting the Determinants of Artificial Intelligence in Green Energy": "Information Technology",
    "GIS-based watershed characterization": "Information Technology",
    "Implementing a Support Vector Classifier for Student Risk Assessment": "Computer Science",
    "Vision-based Real-Time Disaster Recognition Monitoring System": "Computer Science",
    "Acceptability Level of Operator Interface Controller of Robotic Arm": "Information Technology",
    "Incorporating Landscape Dynamics in Small-Scale Hydropower": "Information Technology",
    "Computer Vision-Based Signature Forgery Detection System": "Computer Science",
    "A Deep Learning Approach of Recognizing Natural Disasters": "Computer Science",
    "The Adoption of Online Learning during the Pandemic": "Information Technology",
    "A Correlational Study on the Teaching Methodologies": "Information Technology",
    "Some regular generalized star b-separation axiom": "Computer Science",
}

with open('bisu_computing_crossref_results.csv', encoding='utf-8-sig') as f:
    reader = csv.DictReader(f)
    fieldnames = reader.fieldnames
    rows = list(reader)

updated = 0
for r in rows:
    if r['ProgramInferred'] == 'Computing (unspecified)':
        title = r['Title']
        for key, program in TITLE_TO_PROGRAM.items():
            if key in title:
                r['ProgramInferred'] = program
                updated += 1
                print(f"  {program:25s} <- {title[:80]}")
                break

with open('bisu_computing_crossref_results.csv', 'w', encoding='utf-8-sig', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(rows)

# Verify none remain
remaining = sum(1 for r in rows if r['ProgramInferred'] == 'Computing (unspecified)')
print(f"\nUpdated {updated} records. Still unspecified: {remaining}")
