"""
Build the full research paper DOCX from the template,
filling in real data, citations, charts, and proper formatting.
"""
import csv
import copy
from collections import Counter
from docx import Document
from docx.shared import Pt, Inches, Cm, Emu
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
import os

TEMPLATE = "Completed_Paper Template Colloquium 2026.docx"
OUTPUT = "Bibliometric_Analysis_BISU_Computing_Research_Full_Paper.docx"
CSV_FILE = "bisu_computing_crossref_results.csv"
CHARTS_DIR = "charts"

# ── Load data ────────────────────────────────────────────────
with open(CSV_FILE, encoding="utf-8-sig") as f:
    rows = list(csv.DictReader(f))

total_pubs = len(rows)
year_counts = Counter(r["Year"] for r in rows)
campus_counts = Counter(r["CampusMatched"] for r in rows)
program_counts = Counter(r["ProgramInferred"] for r in rows)
publisher_counts = Counter(r["Publisher"] for r in rows)
type_counts = Counter(r["Type"] for r in rows)
venue_counts = Counter(r["Venue"] for r in rows)
years_sorted = sorted(year_counts.keys())
year_min, year_max = years_sorted[0], years_sorted[-1]

conf_count = type_counts.get("proceedings-article", 0)
journal_count = type_counts.get("journal-article", 0)

# ── References (from attached CSV) ──────────────────────────
# These are the actual references from the user's References CSV.
# We use APA style as the template uses APA.
REFS = sorted([
    'Hendricks, G., Tkaczyk, D., Lin, J., & Feeney, P. (2020). Crossref: The sustainable source of community-owned scholarly metadata. Quantitative Science Studies, 1(1), 414-427. https://doi.org/10.1162/qss_a_00022',
    'Velez-Estevez, A., Pérez, I. J., García-Sánchez, P., Moral-Munoz, J. A., & Cobo, M. (2023). New trends in bibliometric APIs: A comparative analysis. Information Processing & Management, 60(4), 103385. https://doi.org/10.1016/j.ipm.2023.103385',
    'Baas, J., Schotten, M., Plume, A., Côté, G., & Karimi, R. (2020). Scopus as a curated, high-quality bibliometric data source for academic research in quantitative science studies. Quantitative Science Studies, 1(1), 377-386. https://doi.org/10.1162/qss_a_00019',
    'Gerasimov, I., Kc, B., Mehrabian, A., Acker, J. G., & McGuire, M. P. (2024). Comparison of datasets citation coverage in Google Scholar, Web of Science, Scopus, Crossref, and DataCite. Scientometrics, 129, 5765-5790. https://doi.org/10.1007/s11192-024-05073-5',
    'Aria, M., Le, T., Cuccurullo, C., Belfiore, A., & Choe, J. (2024). openalexR: An R-Tool for collecting bibliometric data from OpenAlex. The R Journal, 16(2), 167-180. https://doi.org/10.32614/rj-2023-089',
    'Kaminska, A., & Nazarovets, S. (2018). Crossref as a source of scientometric data for social sciences and humanities. EUREKA: Physics and Engineering, 5, 26-35. https://doi.org/10.30837/2522-9818.2018.5.026',
    'Ricardo, V. A., Rifai, A. I., Savitri, A., & Prasetijo, J. (2024). A bibliometric analysis of drinking water distribution in coastal areas using VOSViewer. Asian Journal of Social and Humanities, 2(8), 335. https://doi.org/10.59888/ajosh.v2i8.335',
    'Lim, W. M., Kumar, S., & Donthu, N. (2024). How to combine and clean bibliometric data and use bibliometric tools synergistically: Guidelines using metaverse research. Journal of Business Research, 182, 114760. https://doi.org/10.1016/j.jbusres.2024.114760',
    'Kumpulainen, M., & Seppänen, M. (2022). Combining Web of Science and Scopus datasets in citation-based literature study. Scientometrics, 127, 5613-5631. https://doi.org/10.1007/s11192-022-04475-7',
    'Nikolić, D., Ivanović, D., & Ivanović, L. (2024). An open-source tool for merging data from multiple citation databases. Scientometrics, 129, 6767-6790. https://doi.org/10.1007/s11192-024-05076-2',
    'Nowakowska, M. (2025). A comprehensive approach to preprocessing data for bibliometric analysis. Scientometrics, 130, 1-35. https://doi.org/10.1007/s11192-025-05415-x',
    'Du, Q., Zhao, R., Wan, Q., Li, S., Li, H., Wang, D., Ho, C. W., Dai, Z., Chen, Y., & Shan, D. (2024). Protocol for conducting bibliometric analysis in biomedicine and related research using CiteSpace and VOSviewer software. STAR Protocols, 5(3), 103269. https://doi.org/10.1016/j.xpro.2024.103269',
], key=lambda r: r.split(',')[0].split()[-1].lower())


# ── Helper functions ─────────────────────────────────────────
def clear_paragraph(p):
    """Remove all runs from a paragraph."""
    for run in p.runs:
        run._element.getparent().remove(run._element)
    # Also clear any remaining text nodes
    el = p._element
    for child in list(el):
        if child.tag.endswith('}r'):
            el.remove(child)


def set_paragraph_text(p, text, bold=False, italic=False, size=12, font="Times New Roman"):
    """Clear paragraph and set new text with formatting."""
    clear_paragraph(p)
    run = p.add_run(text)
    run.font.name = font
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.italic = italic
    return run


def add_paragraph_after(doc, ref_para, text, bold=False, italic=False,
                         size=12, font="Times New Roman",
                         alignment=WD_ALIGN_PARAGRAPH.JUSTIFY,
                         space_after=None, first_line_indent=None):
    """Insert a new paragraph after ref_para."""
    new_p = copy.deepcopy(ref_para._element)
    # Clear all runs
    for child in list(new_p):
        if child.tag.endswith('}r'):
            new_p.remove(child)
    ref_para._element.addnext(new_p)
    from docx.text.paragraph import Paragraph
    para = Paragraph(new_p, ref_para._element.getparent())
    run = para.add_run(text)
    run.font.name = font
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.italic = italic
    para.alignment = alignment
    if space_after is not None:
        para.paragraph_format.space_after = Pt(space_after)
    if first_line_indent is not None:
        para.paragraph_format.first_line_indent = Cm(first_line_indent)
    return para


def insert_image_after(doc, ref_para, image_path, width_inches=5.5):
    """Insert an image in a new paragraph after ref_para using the doc body."""
    # Find position of ref_para in body
    body = doc.element.body
    ref_idx = None
    for i, child in enumerate(body):
        if child is ref_para._element:
            ref_idx = i
            break
    # Add a paragraph to the end then move it
    para = doc.add_paragraph()
    para.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = para.add_run()
    run.add_picture(image_path, width=Inches(width_inches))
    # Move to after ref_para
    body.remove(para._element)
    if ref_idx is not None:
        body.insert(ref_idx + 1, para._element)
    else:
        ref_para._element.addnext(para._element)
    return para


def insert_figure_caption(doc, ref_para, caption_text):
    """Insert a figure caption (TNR 6.5pt, centered, bold label)."""
    new_p = copy.deepcopy(ref_para._element)
    for child in list(new_p):
        if child.tag.endswith('}r'):
            new_p.remove(child)
    ref_para._element.addnext(new_p)
    from docx.text.paragraph import Paragraph
    para = Paragraph(new_p, ref_para._element.getparent())
    para.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = para.add_run(caption_text)
    run.font.name = "Times New Roman"
    run.font.size = Pt(6.5)
    run.font.bold = False
    para.paragraph_format.space_after = Pt(6)
    return para


# ── Build the document ───────────────────────────────────────
doc = Document(TEMPLATE)
paras = doc.paragraphs

# ── TITLE (para 0) ──────────────────────────────────────────
set_paragraph_text(paras[0],
    "Bibliometric Analysis of Computing Research Publications at Bohol Island State University Using Crossref API",
    bold=True, size=12)

# ── Author (para 1) ─────────────────────────────────────────
set_paragraph_text(paras[1], "Max Angelo D. Perin", bold=False, size=12)

# ── Affiliation (para 2) ────────────────────────────────────
set_paragraph_text(paras[2],
    "College of Technology, Bohol Island State University - Bilar Campus, Bohol, Philippines",
    bold=False, size=12)

# ── Email (para 3) ──────────────────────────────────────────
set_paragraph_text(paras[3], "maxangelo.perin@bisu.edu.ph", bold=False, size=12)

# ── ORCID (para 4) ──────────────────────────────────────────
set_paragraph_text(paras[4], "https://orcid.org/0000-0002-2746-7220", bold=False, size=12)

# ── Remove template instructions (paras 5-50) ──────────────
for i in range(5, 51):
    if i < len(paras):
        set_paragraph_text(paras[i], "", size=12)

# ── Abstract (para 51) ──────────────────────────────────────
set_paragraph_text(paras[51],
    "Abstract", bold=True, size=12)

# We need to insert abstract text after para 51. But first let's handle the abstract content.
# Para 52 is blank - we'll use it for abstract text
abstract_text = (
    f"This study presents a bibliometric analysis of computing research publications affiliated with "
    f"Bohol Island State University (BISU), a state university in the province of Bohol, Philippines. "
    f"Using the Crossref REST API as the primary data source, a total of {total_pubs} research publications "
    f"were harvested spanning from {year_min} to {year_max}. The collected metadata were systematically "
    f"cleaned, classified by campus and computing program, and analyzed to identify publication trends, "
    f"research productivity across campuses, thematic focus areas, and preferred publication venues. "
    f"Results reveal that the majority of publications are conference proceedings ({conf_count} of {total_pubs}), "
    f"predominantly published through IEEE. Computer Science accounts for the largest share of publications "
    f"({program_counts.get('Computer Science', 0)}), followed by Information Technology ({program_counts.get('Information Technology', 0)}). "
    f"Among the six campuses, Bilar Campus leads with {campus_counts.get('Bilar Campus', 0)} publications, "
    f"followed by Clarin Campus ({campus_counts.get('Clarin Campus', 0)}) and Candijay Campus ({campus_counts.get('Candijay Campus', 0)}). "
    f"Word cloud analysis of titles and abstracts shows prevalent themes in machine learning, deep learning, "
    f"detection, classification, and neural networks. A significant surge in research output is observed from "
    f"2024 onward, indicating growing research capacity within BISU's computing departments. "
    f"This bibliometric mapping serves as a baseline for institutional research planning and benchmarking."
)
# Use para 52 (blank) for abstract text
set_paragraph_text(paras[52], abstract_text, bold=False, size=12)
paras[52].alignment = WD_ALIGN_PARAGRAPH.JUSTIFY

# ── Keywords (para 53) ──────────────────────────────────────
clear_paragraph(paras[53])
run_k = paras[53].add_run("Keywords: ")
run_k.font.name = "Times New Roman"
run_k.font.size = Pt(12)
run_k.font.bold = True
run_v = paras[53].add_run("bibliometric analysis, computing research, Crossref API, Bohol Island State University, research productivity")
run_v.font.name = "Times New Roman"
run_v.font.size = Pt(12)
run_v.font.bold = False

# ── INTRODUCTION (para 56 = heading, para 58-59 = body) ─────
set_paragraph_text(paras[56], "Introduction", bold=True, size=12)

intro_p1 = (
    "Bibliometric analysis has emerged as a critical methodology for evaluating research output, "
    "identifying trends, and informing institutional decision-making in higher education. "
    "As academic institutions increasingly rely on quantitative metrics to assess research productivity, "
    "the availability of open scholarly metadata has become essential. Crossref, one of the largest "
    "community-owned scholarly metadata repositories, provides access to over 106 million records "
    "across 13 content types, making it a valuable resource for scientometric research "
    "(Hendricks et al., 2020). Unlike proprietary databases such as Scopus and Web of Science, "
    "which require institutional subscriptions and impose access restrictions "
    "(Baas et al., 2020), the Crossref REST API offers free and unrestricted access to bibliographic "
    "metadata, enabling researchers from resource-constrained institutions to conduct comprehensive "
    "bibliometric studies (Velez-Estevez et al., 2023)."
)

intro_p2 = (
    "    The use of application programming interfaces (APIs) for bibliometric data retrieval has gained "
    "significant attention in recent years. Velez-Estevez et al. (2023) conducted a comparative analysis "
    "of bibliometric APIs and found that while commercial providers such as Clarivate Analytics and Elsevier "
    "offer versatile tools, non-profit organizations like Crossref and OpenCitations promote open science "
    "with fewer restrictions on metadata retrieval. Similarly, Gerasimov et al. (2024) compared citation "
    "coverage across Google Scholar, Web of Science, Scopus, Crossref, and DataCite, noting that although "
    "Crossref trails in dataset citation coverage, it remains a robust source for article-level metadata. "
    "Kaminska and Nazarovets (2018) further demonstrated Crossref's utility for scientometric analysis "
    "in the social sciences and humanities through the ScientoMiner ICR module."
)

intro_p3 = (
    "    Data preprocessing remains a significant challenge in bibliometric research. Nowakowska (2025) "
    "emphasized that combining and cleaning bibliographic data from multiple databases requires substantial "
    "manual effort, and no fully automatic solution currently exists. Lim et al. (2024) proposed guidelines "
    "for combining and cleaning bibliometric data using tools such as bibliometrix and VOSviewer. "
    "Kumpulainen and Seppänen (2022) documented the extensive data wrangling required when merging "
    "Web of Science and Scopus datasets, while Nikolić et al. (2024) developed an open-source "
    "deduplication tool that achieves up to 99% precision in merging records from multiple databases."
)

intro_p4 = (
    "    In the Philippine context, state universities and colleges (SUCs) play a vital role in expanding "
    "access to higher education and fostering regional research capacity. Bohol Island State University (BISU) "
    "is a multi-campus institution with six campuses across the province of Bohol, offering computing programs "
    "including Computer Science, Information Technology, Computer Engineering, and Information Systems. "
    "Despite the growing body of computing research produced by BISU faculty and students, no systematic "
    "bibliometric analysis has been conducted to map the institution's research landscape in the computing domain. "
    "Understanding the distribution of publications across campuses, programs, and years is essential for "
    "strategic research planning, resource allocation, and identifying areas for capacity building."
)

intro_p5 = (
    "    This study addresses this gap by conducting a bibliometric analysis of computing research publications "
    "affiliated with BISU using the Crossref REST API. The methodology involves automated data harvesting "
    "through affiliation-based queries, systematic data cleaning and classification, and visual analytics "
    "to present findings through statistical charts and word clouds. This approach aligns with established "
    "bibliometric protocols, including those described by Du et al. (2024) for conducting bibliometric "
    "analysis using visualization software, and by Ricardo et al. (2024) who demonstrated the use of "
    "VOSviewer for keyword co-occurrence analysis in bibliometric studies."
)

set_paragraph_text(paras[58], intro_p1, bold=False, size=12)
paras[58].alignment = WD_ALIGN_PARAGRAPH.JUSTIFY

set_paragraph_text(paras[59], intro_p2, bold=False, size=12)
paras[59].alignment = WD_ALIGN_PARAGRAPH.JUSTIFY

# Insert additional intro paragraphs after para 59
p_ref = paras[59]
p_ref = add_paragraph_after(doc, p_ref, intro_p3, size=12,
                             alignment=WD_ALIGN_PARAGRAPH.JUSTIFY)
p_ref = add_paragraph_after(doc, p_ref, intro_p4, size=12,
                             alignment=WD_ALIGN_PARAGRAPH.JUSTIFY)
p_ref = add_paragraph_after(doc, p_ref, intro_p5, size=12,
                             alignment=WD_ALIGN_PARAGRAPH.JUSTIFY)

# ── Re-index paragraphs after insertions ─────────────────────
paras = doc.paragraphs

# Find section headings by text content
def find_para(text_match, bold_only=True):
    for i, p in enumerate(paras):
        if text_match in p.text:
            if bold_only and p.runs and p.runs[0].font.bold:
                return i
            elif not bold_only:
                return i
    return None

# ── OBJECTIVES OF THE STUDY ──────────────────────────────────
idx = find_para("Objectives of the Study")
if idx:
    # Find the next paragraph(s) with placeholder text
    body_idx = idx + 2  # skip blank
    if body_idx < len(paras):
        set_paragraph_text(paras[body_idx],
            "This study aims to conduct a bibliometric analysis of computing research publications "
            "at Bohol Island State University (BISU) using the Crossref REST API. Specifically, it seeks to:",
            bold=False, size=12)
        paras[body_idx].alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    
    # Add numbered objectives
    obj_ref = paras[body_idx]
    objectives = [
        "1. Determine the volume and temporal trends of computing research publications affiliated with BISU from 2018 to 2026.",
        "2. Identify the distribution of publications across BISU campuses and computing programs.",
        "3. Analyze the dominant research themes through word frequency and word cloud analysis of titles and abstracts.",
        "4. Determine the preferred publication venues, publishers, and document types.",
        "5. Provide a baseline bibliometric profile for institutional research planning and benchmarking.",
    ]
    for obj in objectives:
        obj_ref = add_paragraph_after(doc, obj_ref, obj, size=12,
                                       alignment=WD_ALIGN_PARAGRAPH.JUSTIFY)

# Re-index
paras = doc.paragraphs

# ── METHODOLOGY ──────────────────────────────────────────────
idx = find_para("Methodology")
# Don't rewrite the heading itself

# Research Design
idx_rd = find_para("Research Design")
if idx_rd:
    body_idx = idx_rd + 2
    if body_idx < len(paras):
        set_paragraph_text(paras[body_idx],
            "This study employs a quantitative bibliometric research design using the Crossref REST API "
            "as the primary data source. Bibliometric analysis is a statistical method that quantitatively "
            "analyzes research publications to identify patterns and trends (Ricardo et al., 2024). "
            "The approach involves automated data harvesting through API queries, systematic data cleaning "
            "and classification, and statistical visualization of the results.",
            bold=False, size=12)
        paras[body_idx].alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    # Next para (indented second paragraph)
    next_body = body_idx + 1
    if next_body < len(paras) and "Start here your second" in paras[next_body].text:
        set_paragraph_text(paras[next_body],
            "    The Crossref REST API was selected over proprietary databases because it provides free, "
            "unrestricted access to scholarly metadata without requiring institutional subscriptions "
            "(Hendricks et al., 2020). While Scopus and Web of Science offer curated and high-quality "
            "data (Baas et al., 2020), their access restrictions make them less suitable for institutions "
            "with limited resources. The API queries used affiliation-based searches with the parameter "
            "\"query.affiliation\" set to \"Bohol Island State University\" to retrieve all publications "
            "with BISU-affiliated authors.",
            bold=False, size=12)
        paras[next_body].alignment = WD_ALIGN_PARAGRAPH.JUSTIFY

# Research Respondent and Locale
idx_rr = find_para("Research Respondent and Locale")
if idx_rr:
    body_idx = idx_rr + 2
    if body_idx < len(paras):
        set_paragraph_text(paras[body_idx],
            f"The study analyzes {total_pubs} computing research publications affiliated with Bohol Island "
            f"State University (BISU), a state university in the province of Bohol, Central Visayas, Philippines. "
            f"BISU operates six campuses: Main Campus (Tagbilaran City), Bilar Campus, Candijay Campus, "
            f"Clarin Campus, Balilihan Campus, and Calape Campus. The dataset covers publications from "
            f"{year_min} to {year_max}, encompassing four computing programs: Computer Science, Information Technology, "
            f"Computer Engineering, and Information Systems.",
            bold=False, size=12)
        paras[body_idx].alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    next_body = body_idx + 1
    if next_body < len(paras) and "Start here your second" in paras[next_body].text:
        set_paragraph_text(paras[next_body],
            "    The unit of analysis is the individual research publication (article or conference paper) "
            "rather than individual researchers. Each publication record includes metadata such as title, "
            "authors, year, venue, publisher, DOI, affiliations, subjects, and abstract. "
            "The locale of the study is the Crossref database, which indexes publications from major "
            "publishers including IEEE, ACM, MDPI, and others.",
            bold=False, size=12)
        paras[next_body].alignment = WD_ALIGN_PARAGRAPH.JUSTIFY

# Research Instrument
idx_ri = find_para("Research Instrument")
if idx_ri:
    body_idx = idx_ri + 2
    if body_idx < len(paras):
        set_paragraph_text(paras[body_idx],
            "The primary research instrument is a custom Python script that interfaces with the Crossref "
            "REST API (https://api.crossref.org/works) to harvest bibliographic metadata. The script sends "
            "HTTP GET requests with the \"query.affiliation\" parameter and retrieves JSON responses containing "
            "publication metadata. The harvested records are filtered for computing-related publications using "
            "keyword matching against titles, subjects, and venue names. The filtered data is exported to "
            "CSV format for subsequent analysis.",
            bold=False, size=12)
        paras[body_idx].alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    next_body = body_idx + 1
    if next_body < len(paras) and "Start here your second" in paras[next_body].text:
        set_paragraph_text(paras[next_body],
            "    A second Python script performs data analysis and visualization using the matplotlib "
            "and wordcloud libraries. This script generates 13 statistical charts including bar charts, "
            "pie charts, heatmaps, stacked bar charts, word clouds, and trend lines. "
            "The data preprocessing pipeline includes HTML entity decoding, campus resolution from "
            "affiliation strings, and program classification based on department names and title keywords. "
            "All scripts and data are version-controlled using Git and hosted on GitHub.",
            bold=False, size=12)
        paras[next_body].alignment = WD_ALIGN_PARAGRAPH.JUSTIFY

# Statistical Treatment
idx_st = find_para("Statistical Treatment")
if idx_st:
    body_idx = idx_st + 2
    if body_idx < len(paras):
        set_paragraph_text(paras[body_idx],
            "The study employs descriptive statistics including frequency counts, percentages, and "
            "cross-tabulations to analyze the distribution of publications across years, campuses, "
            "programs, publishers, venues, and document types. Year-over-year growth rates are calculated "
            "as percentage changes between consecutive years. Cumulative publication counts are computed "
            "to visualize the overall growth trajectory.",
            bold=False, size=12)
        paras[body_idx].alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    next_body = body_idx + 1
    if next_body < len(paras) and "Start here your second" in paras[next_body].text:
        set_paragraph_text(paras[next_body],
            "    Word frequency analysis is performed on publication titles and abstracts to identify "
            "dominant research themes. Common English stopwords are removed, and the resulting word "
            "frequencies are visualized as word clouds using the Python wordcloud library. "
            "Cross-tabulation of campus and program variables produces a heatmap showing the "
            "concentration of research output by institutional unit and academic program. "
            "These methods are consistent with bibliometric analysis protocols described by "
            "Du et al. (2024) and Lim et al. (2024).",
            bold=False, size=12)
        paras[next_body].alignment = WD_ALIGN_PARAGRAPH.JUSTIFY

# Ethical Consideration
idx_ec = find_para("Ethical Consideration")
if idx_ec:
    body_idx = idx_ec + 2
    if body_idx < len(paras):
        set_paragraph_text(paras[body_idx],
            "This study uses only publicly available bibliographic metadata retrieved from the Crossref "
            "REST API. No human subjects are involved, and no personal, private, or sensitive information "
            "is collected beyond what is publicly listed in academic publication records (author names, "
            "affiliations, and publication details). The Crossref API provides open access to metadata "
            "in compliance with its terms of service. All data sources are properly cited and acknowledged.",
            bold=False, size=12)
        paras[body_idx].alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    next_body = body_idx + 1
    if next_body < len(paras) and "Start here your second" in paras[next_body].text:
        set_paragraph_text(paras[next_body],
            "    The study adheres to responsible bibliometric practices by accurately representing "
            "the data as retrieved from Crossref without manipulation or fabrication. Limitations of "
            "the data source, including potential incomplete coverage of BISU publications not indexed "
            "in Crossref, are transparently acknowledged in the discussion section.",
            bold=False, size=12)
        paras[next_body].alignment = WD_ALIGN_PARAGRAPH.JUSTIFY

# Expected Output
idx_eo = find_para("Expected Output")
if idx_eo:
    body_idx = idx_eo + 2
    if body_idx < len(paras):
        set_paragraph_text(paras[body_idx],
            "The expected output of this study is a comprehensive bibliometric profile of computing research "
            "at Bohol Island State University, including: (1) a dataset of all BISU computing publications "
            "indexed in Crossref with cleaned and classified metadata; (2) statistical summaries and "
            "visualizations of publication trends by year, campus, program, publisher, and venue; "
            "(3) word cloud analyses revealing dominant research themes; and (4) a citation-ready "
            "PDF catalog of all publications in APA, IEEE, and ACM formats for use by students and researchers.",
            bold=False, size=12)
        paras[body_idx].alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    next_body = body_idx + 1
    if next_body < len(paras) and "Start here your second" in paras[next_body].text:
        set_paragraph_text(paras[next_body],
            "    These outputs serve as a baseline for future longitudinal studies on BISU's research "
            "productivity and can inform institutional policies on research incentives, faculty development, "
            "and strategic investment in computing research infrastructure.",
            bold=False, size=12)
        paras[next_body].alignment = WD_ALIGN_PARAGRAPH.JUSTIFY

# Re-index after all insertions
paras = doc.paragraphs

# ── RESULT AND DISCUSSIONS ───────────────────────────────────
idx_rd = find_para("Result and Discussions")
if idx_rd:
    body_idx = idx_rd + 2
    if body_idx < len(paras):
        set_paragraph_text(paras[body_idx],
            f"A total of {total_pubs} computing research publications affiliated with BISU were "
            f"retrieved from the Crossref API, spanning from {year_min} to {year_max}. The publications "
            f"are distributed across six campuses and four computing programs. The following subsections "
            f"present the detailed findings organized by research objective.",
            bold=False, size=12)
        paras[body_idx].alignment = WD_ALIGN_PARAGRAPH.JUSTIFY

    # Replace the second paragraph placeholder
    next_body = body_idx + 1
    if next_body < len(paras) and "Start here your second" in paras[next_body].text:
        set_paragraph_text(paras[next_body], "", size=12)

    # Now insert all charts and discussions after the results heading area
    p_ref = paras[next_body]

    # Chart definitions: (filename, figure_num, caption, discussion)
    charts_info = [
        ("01_publications_per_year.png", 1,
         "FIGURE 1. Publications per Year (2018-2026)",
         f"Figure 1 presents the temporal distribution of BISU computing research publications. "
         f"The data reveals minimal research output from 2018 to 2020, with only {year_counts.get('2018', 0)} and "
         f"{year_counts.get('2020', 0)} publication(s) respectively. A gradual increase is observed from 2021 "
         f"({year_counts.get('2021', 0)} publications) through 2022 ({year_counts.get('2022', 0)} publications). "
         f"A significant acceleration occurs in 2024 with {year_counts.get('2024', 0)} publications, peaking at "
         f"{year_counts.get('2025', 0)} publications in 2025. The 2026 figure of {year_counts.get('2026', 0)} publications "
         f"represents partial-year data as of the time of data collection. This exponential growth pattern "
         f"suggests increasing research capacity and institutional support for computing research at BISU."),

        ("02_by_campus.png", 2,
         "FIGURE 2. Publications by Campus",
         f"Figure 2 displays the distribution of publications across BISU campuses. "
         f"Bilar Campus leads with {campus_counts.get('Bilar Campus', 0)} publications, followed by "
         f"Clarin Campus ({campus_counts.get('Clarin Campus', 0)}) and Candijay Campus ({campus_counts.get('Candijay Campus', 0)}). "
         f"Main Campus (Tagbilaran) accounts for {campus_counts.get('Main Campus', 0)} publications, "
         f"while Balilihan Campus and Calape Campus each have {campus_counts.get('Balilihan Campus', 0)} and "
         f"{campus_counts.get('Calape Campus', 0)} publication(s) respectively. The dominance of the three satellite "
         f"campuses (Bilar, Clarin, Candijay) is notable, collectively accounting for "
         f"{campus_counts.get('Bilar Campus', 0) + campus_counts.get('Clarin Campus', 0) + campus_counts.get('Candijay Campus', 0)} "
         f"of {total_pubs} total publications ({(campus_counts.get('Bilar Campus', 0) + campus_counts.get('Clarin Campus', 0) + campus_counts.get('Candijay Campus', 0)) / total_pubs * 100:.1f}%)."),

        ("03_by_program_pie.png", 3,
         "FIGURE 3. Publications by Program",
         f"Figure 3 shows the distribution of publications by computing program. Computer Science "
         f"accounts for the largest share with {program_counts.get('Computer Science', 0)} publications "
         f"({program_counts.get('Computer Science', 0) / total_pubs * 100:.1f}%), followed by Information Technology "
         f"with {program_counts.get('Information Technology', 0)} publications "
         f"({program_counts.get('Information Technology', 0) / total_pubs * 100:.1f}%). Computer Engineering "
         f"contributes {program_counts.get('Computer Engineering', 0)} publications "
         f"({program_counts.get('Computer Engineering', 0) / total_pubs * 100:.1f}%), and Information Systems "
         f"has {program_counts.get('Information Systems', 0)} publication "
         f"({program_counts.get('Information Systems', 0) / total_pubs * 100:.1f}%). The strong representation of "
         f"Computer Science reflects the prevalence of machine learning and artificial intelligence "
         f"research topics among BISU publications."),

        ("04_campus_year_heatmap.png", 4,
         "FIGURE 4. Campus-Year Heatmap",
         "Figure 4 presents a heatmap cross-tabulating campuses and publication years. "
         "The visualization reveals that the research output surge in 2025 is distributed across "
         "multiple campuses rather than concentrated in a single unit. Candijay Campus shows "
         "consistent activity from 2024 onward, while Clarin Campus demonstrates sustained output "
         "across multiple years from 2021. Bilar Campus contributes significantly in 2024-2025. "
         "The heatmap also highlights temporal gaps, with no publications recorded for 2019 and 2023 "
         "across all campuses."),

        ("05_top_publishers.png", 5,
         "FIGURE 5. Top Publishers",
         f"Figure 5 identifies the top publishers of BISU computing research. IEEE dominates with "
         f"{publisher_counts.get('IEEE', 0)} publications ({publisher_counts.get('IEEE', 0) / total_pubs * 100:.1f}%), "
         f"reflecting the conference-oriented nature of computing research. ACM follows with "
         f"{publisher_counts.get('ACM', 0)} publications, while MDPI and Informa UK Limited contribute "
         f"{publisher_counts.get('MDPI', 0) + publisher_counts.get('MDPI AG', 0)} and "
         f"{publisher_counts.get('Informa UK Limited', 0)} publications respectively. "
         f"The strong preference for IEEE venues aligns with the global trend in computing research "
         f"where conference publications are considered primary dissemination channels."),

        ("06_publication_types_donut.png", 6,
         "FIGURE 6. Publication Types",
         f"Figure 6 illustrates the distribution of publication types. Conference proceedings articles "
         f"constitute {conf_count} of {total_pubs} publications ({conf_count / total_pubs * 100:.1f}%), "
         f"while journal articles account for {journal_count} ({journal_count / total_pubs * 100:.1f}%). "
         f"This distribution is typical of emerging research programs where conference publications serve "
         f"as the primary mechanism for rapid dissemination of research findings before maturation into "
         f"journal publications."),

        ("07_program_by_campus_stacked.png", 7,
         "FIGURE 7. Program Distribution by Campus",
         "Figure 7 presents a stacked bar chart showing the program distribution within each campus. "
         "Candijay Campus publications are predominantly in Computer Science, consistent with its "
         "College of Sciences hosting the Computer Science department. Clarin Campus shows a mix of "
         "Computer Science and Information Technology. Bilar Campus demonstrates diversity across "
         "Computer Science and Information Technology programs. Main Campus shows representation "
         "across multiple programs including Computer Engineering."),

        ("08_trend_by_program.png", 8,
         "FIGURE 8. Publication Trend by Program",
         "Figure 8 tracks the publication trends of each computing program over time. Computer Science "
         "shows the most dramatic growth, rising sharply from 2024 to 2025. Information Technology "
         "publications also increase in 2025-2026. Computer Engineering maintains a small but consistent "
         "presence. The trend lines suggest that Computer Science is the primary driver of BISU's "
         "recent research output growth."),

        ("09_wordcloud_titles.png", 9,
         "FIGURE 9. Word Cloud of Research Titles",
         "Figure 9 presents a word cloud generated from the titles of all publications. "
         "The most prominent terms include \"Machine,\" \"Learning,\" \"Detection,\" \"Classification,\" "
         "\"Neural,\" \"Network,\" \"Deep,\" \"Convolutional,\" and \"Predicting.\" These terms indicate "
         "a strong research orientation toward machine learning and deep learning applications, "
         "computer vision tasks (detection, classification, recognition), and predictive modeling. "
         "Domain-specific terms such as \"Leaf,\" \"Species,\" \"Marine,\" and \"Agricultural\" suggest "
         "that BISU researchers are applying computing techniques to locally relevant problems."),

        ("10_wordcloud_abstracts.png", 10,
         "FIGURE 10. Word Cloud of Abstracts",
         "Figure 10 shows a word cloud derived from the abstracts of publications that contain "
         "abstract text. Prominent terms include \"learning,\" \"student,\" \"device,\" \"teaching,\" "
         "\"weighted,\" \"mean,\" and \"competency.\" The presence of education-related terms alongside "
         "technical computing terms reflects the dual nature of BISU research, which encompasses both "
         "technical computing innovations and studies on computing education, student performance, "
         "and teaching methodologies."),

        ("11_top_venues.png", 11,
         "FIGURE 11. Top 10 Publication Venues",
         f"Figure 11 lists the top 10 publication venues. The {venue_counts.most_common(1)[0][0]} "
         f"is the most frequent venue with {venue_counts.most_common(1)[0][1]} publications. "
         f"Other prominent venues include international IEEE conferences on information technology, "
         f"intelligent communication, and sustainable computing. The concentration of publications "
         f"in IEEE-organized conferences reflects active participation in international computing "
         f"conferences by BISU researchers."),

        ("12_yoy_growth.png", 12,
         "FIGURE 12. Year-over-Year Growth Rate",
         "Figure 12 displays the year-over-year growth rates in publication output. The most notable "
         "growth periods are from 2020 to 2021 and from 2022 to 2024, with substantial percentage "
         "increases. The growth rate from 2024 to 2025 demonstrates continued expansion of research "
         "output. The negative growth shown for 2025 to 2026 reflects the incomplete data for 2026 "
         "rather than an actual decline, as data collection was conducted in early 2026."),

        ("13_cumulative_publications.png", 13,
         "FIGURE 13. Cumulative Publications Over Time",
         f"Figure 13 shows the cumulative publication count over time, illustrating the overall "
         f"growth trajectory. The curve shows a slow initial phase from 2018 to 2022, an inflection "
         f"point around 2023-2024, and rapid acceleration through 2025-2026. The cumulative total "
         f"reaches {total_pubs} publications by the end of the observation period. This S-curve pattern "
         f"is consistent with the growth trajectory of emerging research programs transitioning from "
         f"an establishment phase to an active production phase."),
    ]

    for chart_file, fig_num, caption, discussion in charts_info:
        chart_path = os.path.join(CHARTS_DIR, chart_file)
        if os.path.exists(chart_path):
            # Discussion text
            p_ref = add_paragraph_after(doc, p_ref, discussion, size=12,
                                         alignment=WD_ALIGN_PARAGRAPH.JUSTIFY,
                                         space_after=6)
            # Image
            p_ref = insert_image_after(doc, p_ref, chart_path, width_inches=5.0)
            # Caption
            p_ref = insert_figure_caption(doc, p_ref, caption)
            # Blank line
            p_ref = add_paragraph_after(doc, p_ref, "", size=12)

# Re-index
paras = doc.paragraphs

# ── CONCLUSION ───────────────────────────────────────────────
idx_c = find_para("Conclusion")
if idx_c:
    body_idx = idx_c + 2
    if body_idx < len(paras):
        set_paragraph_text(paras[body_idx],
            f"This study conducted a bibliometric analysis of {total_pubs} computing research publications "
            f"affiliated with Bohol Island State University using the Crossref REST API. The analysis "
            f"covers publications from {year_min} to {year_max} across six campuses and four computing programs. "
            f"The findings reveal a significant growth trajectory in BISU's computing research output, "
            f"with the majority of publications emerging from 2024 onwards. IEEE conference proceedings "
            f"dominate the publication landscape ({conf_count} of {total_pubs}), and Computer Science is the most "
            f"productive program ({program_counts.get('Computer Science', 0)} publications). Bilar, Clarin, and "
            f"Candijay campuses collectively account for the majority of research output.",
            bold=False, size=12)
        paras[body_idx].alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    next_body = body_idx + 1
    if next_body < len(paras) and "Start here your second" in paras[next_body].text:
        set_paragraph_text(paras[next_body],
            "    Word cloud analysis reveals that machine learning, deep learning, and computer vision "
            "are the dominant research themes, with applications in agriculture, biodiversity, education, "
            "and marine science. The Crossref API proved to be a viable and accessible data source for "
            "institutional bibliometric analysis, consistent with the findings of Hendricks et al. (2020) "
            "and Velez-Estevez et al. (2023). However, the coverage may not capture all BISU publications, "
            "particularly those in local or non-indexed journals, representing a limitation of this study. "
            "The bibliometric profile established in this study provides a quantitative foundation for "
            "evidence-based research planning at BISU.",
            bold=False, size=12)
        paras[next_body].alignment = WD_ALIGN_PARAGRAPH.JUSTIFY

# ── RECOMMENDATION ───────────────────────────────────────────
idx_rec = find_para("Recommendation")
if idx_rec:
    body_idx = idx_rec + 2
    if body_idx < len(paras):
        set_paragraph_text(paras[body_idx],
            "Based on the findings of this study, the following recommendations are proposed: "
            "(1) BISU should establish an institutional repository to centralize and track all "
            "research publications across campuses, ensuring comprehensive coverage beyond Crossref-indexed works. "
            "(2) Campuses with lower publication counts, such as Balilihan and Calape, should receive "
            "targeted research capacity-building support, including mentoring programs and research grants. "
            "(3) Faculty should be encouraged to publish in peer-reviewed journals in addition to "
            "conference proceedings to diversify the publication portfolio. "
            "(4) Future studies should extend this analysis by incorporating data from multiple databases "
            "such as Scopus and Google Scholar, as recommended by Kumpulainen and Seppänen (2022) "
            "and Nikolić et al. (2024), to achieve more comprehensive coverage.",
            bold=False, size=12)
        paras[body_idx].alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    next_body = body_idx + 1
    if next_body < len(paras) and "Start here your second" in paras[next_body].text:
        set_paragraph_text(paras[next_body],
            "    (5) The university should consider conducting periodic bibliometric analyses (e.g., annually) "
            "to track research productivity trends and measure the impact of research policies and interventions. "
            "(6) The open-source tools and scripts developed in this study should be institutionalized "
            "and maintained for ongoing research monitoring. "
            "(7) Research collaboration networks should be analyzed in future studies to understand "
            "inter-campus and inter-institutional collaboration patterns among BISU researchers.",
            bold=False, size=12)
        paras[next_body].alignment = WD_ALIGN_PARAGRAPH.JUSTIFY

# ── ACKNOWLEDGEMENT ──────────────────────────────────────────
idx_ack = find_para("Acknowledgement")
if idx_ack:
    body_idx = idx_ack + 2
    if body_idx < len(paras):
        set_paragraph_text(paras[body_idx],
            "The author would like to express sincere gratitude to Bohol Island State University "
            "for the institutional support in conducting this research. Appreciation is extended "
            "to the Crossref organization for providing open access to scholarly metadata through "
            "their REST API. The author also acknowledges the computing faculty and researchers "
            "across all BISU campuses whose published works made this bibliometric analysis possible.",
            bold=False, size=12)
        paras[body_idx].alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    next_body = body_idx + 1
    if next_body < len(paras) and "Start here your second" in paras[next_body].text:
        set_paragraph_text(paras[next_body], "", size=12)

# ── REFERENCES ───────────────────────────────────────────────
idx_ref = find_para("References")
if idx_ref:
    # Find the sub-headings (Book, Journals, Conferences, Online) and replace them
    # We'll replace from the first sub-heading onward
    # First, find Book heading
    idx_book = find_para("Book")
    if idx_book:
        # Clear Book, Journals, Conferences, Online headings and their blanks
        for label in ["Book", "Journals", "Conferences", "Online"]:
            i = find_para(label)
            if i:
                set_paragraph_text(paras[i], "", size=12)

    # Insert references after the References heading
    # Find the blank after References heading
    ref_body = idx_ref + 1
    p_ref = paras[ref_body]
    
    for ref_text in REFS:
        p_ref = add_paragraph_after(doc, p_ref, ref_text, size=12,
                                     alignment=WD_ALIGN_PARAGRAPH.JUSTIFY,
                                     space_after=6,
                                     first_line_indent=-1.27)
        # Set hanging indent (negative first line = hanging)
        p_ref.paragraph_format.left_indent = Cm(1.27)
        p_ref.paragraph_format.first_line_indent = Cm(-1.27)

# ── Save ─────────────────────────────────────────────────────
doc.save(OUTPUT)
print(f"Paper saved: {OUTPUT}")
print(f"Total paragraphs: {len(doc.paragraphs)}")
