"""
Generate a PDF catalog of BISU Computing Research Publications
with APA 7th, IEEE, and ACM citation formats for each paper.
"""
import csv
import html
import re
from fpdf import FPDF

CSV_FILE = "bisu_computing_crossref_results.csv"
OUTPUT_PDF = "BISU_Computing_Research_Publications_Catalog.pdf"


# ── helpers ──────────────────────────────────────────────────
def clean(text):
    """Decode HTML entities and normalize whitespace."""
    if not text:
        return ""
    text = html.unescape(text)
    text = text.replace("\u2013", "-").replace("\u2014", "-")
    text = re.sub(r"\s+", " ", text).strip()
    return text


def split_authors(raw):
    """Return a list of author name strings."""
    raw = clean(raw)
    return [a.strip() for a in raw.split(",") if a.strip()]


def last_first(name):
    """Convert 'First M. Last' → 'Last, F. M.' for APA."""
    parts = name.strip().split()
    if len(parts) < 2:
        return name
    last = parts[-1]
    initials = " ".join(p[0] + "." for p in parts[:-1])
    return f"{last}, {initials}"


def first_initial_last(name):
    """Convert 'First M. Last' → 'F. M. Last' for IEEE."""
    parts = name.strip().split()
    if len(parts) < 2:
        return name
    last = parts[-1]
    initials = " ".join(p[0] + "." for p in parts[:-1])
    return f"{initials} {last}"


# ── citation formatters ─────────────────────────────────────
def cite_apa(r, authors):
    """APA 7th edition."""
    year = r["Year"]
    title = clean(r["Title"])
    venue = clean(r["Venue"])
    doi = r["DOI"]

    # Authors in APA: Last, F. M., & Last, F. M.
    apa_authors = [last_first(a) for a in authors]
    if len(apa_authors) == 1:
        auth_str = apa_authors[0]
    elif len(apa_authors) == 2:
        auth_str = f"{apa_authors[0]} & {apa_authors[1]}"
    elif len(apa_authors) <= 20:
        auth_str = ", ".join(apa_authors[:-1]) + ", & " + apa_authors[-1]
    else:
        auth_str = ", ".join(apa_authors[:19]) + " ... " + apa_authors[-1]

    pub_type = r["Type"]
    if pub_type == "proceedings-article":
        cite = f"{auth_str} ({year}). {title}. In {venue}. https://doi.org/{doi}"
    else:
        cite = f"{auth_str} ({year}). {title}. {venue}. https://doi.org/{doi}"
    return cite


def cite_ieee(r, authors):
    """IEEE style."""
    year = r["Year"]
    title = clean(r["Title"])
    venue = clean(r["Venue"])
    doi = r["DOI"]

    # Authors: F. M. Last, F. M. Last, and F. M. Last
    ieee_authors = [first_initial_last(a) for a in authors]
    if len(ieee_authors) == 1:
        auth_str = ieee_authors[0]
    elif len(ieee_authors) == 2:
        auth_str = f"{ieee_authors[0]} and {ieee_authors[1]}"
    else:
        auth_str = ", ".join(ieee_authors[:-1]) + ", and " + ieee_authors[-1]

    pub_type = r["Type"]
    if pub_type == "proceedings-article":
        cite = (f'{auth_str}, "{title}," in {venue}, {year}. '
                f"doi: {doi}.")
    else:
        cite = (f'{auth_str}, "{title}," {venue}, {year}. '
                f"doi: {doi}.")
    return cite


def cite_acm(r, authors):
    """ACM style."""
    year = r["Year"]
    title = clean(r["Title"])
    venue = clean(r["Venue"])
    doi = r["DOI"]
    publisher = clean(r["Publisher"])

    # Authors: First M. Last, First M. Last, and First M. Last
    if len(authors) == 1:
        auth_str = authors[0]
    elif len(authors) == 2:
        auth_str = f"{authors[0]} and {authors[1]}"
    else:
        auth_str = ", ".join(authors[:-1]) + ", and " + authors[-1]

    pub_type = r["Type"]
    if pub_type == "proceedings-article":
        cite = (f"{auth_str}. {year}. {title}. In {venue}. "
                f"{publisher}. https://doi.org/{doi}")
    else:
        cite = (f"{auth_str}. {year}. {title}. {venue}. "
                f"https://doi.org/{doi}")
    return cite


# ── PDF generation ───────────────────────────────────────────
class CatalogPDF(FPDF):
    def header(self):
        if self.page_no() == 1:
            return  # skip header on title page
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(120, 120, 120)
        self.cell(0, 5, "BISU Computing Research Publications Catalog", align="C")
        self.ln(8)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(120, 120, 120)
        self.cell(0, 10, f"Page {self.page_no()}/{{nb}}", align="C")


def build_pdf(rows):
    pdf = CatalogPDF(orientation="P", unit="mm", format="A4")
    pdf.alias_nb_pages()
    pdf.set_auto_page_break(auto=True, margin=20)

    # ── Title page ───────────────────────────────────────────
    pdf.add_page()
    pdf.ln(40)
    pdf.set_font("Helvetica", "B", 22)
    pdf.set_text_color(25, 60, 120)
    pdf.multi_cell(0, 12, "BISU Computing Research\nPublications Catalog", align="C")
    pdf.ln(8)
    pdf.set_font("Helvetica", "", 13)
    pdf.set_text_color(60, 60, 60)
    pdf.multi_cell(0, 8,
        "A Bibliometric Compilation of Computing Research Publications\n"
        "from Bohol Island State University (BISU)\n"
        "Sourced from the Crossref API",
        align="C")
    pdf.ln(10)
    pdf.set_font("Helvetica", "I", 11)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 8, f"Total Publications: {len(rows)}", align="C")
    pdf.ln(6)

    # Year range
    years = sorted(set(r["Year"] for r in rows))
    pdf.cell(0, 8, f"Coverage: {years[0]} - {years[-1]}", align="C")
    pdf.ln(6)

    # Campus list
    campuses = sorted(set(r["CampusMatched"] for r in rows))
    pdf.cell(0, 8, f"Campuses: {', '.join(campuses)}", align="C")
    pdf.ln(20)

    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(80, 80, 80)
    pdf.multi_cell(0, 6,
        "This catalog provides citation-ready references in APA 7th Edition, "
        "IEEE, and ACM formats. Each entry includes the DOI link for easy access. "
        "Students and researchers may copy the appropriate citation format "
        "for their papers.",
        align="C")
    pdf.ln(15)
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_text_color(25, 60, 120)
    pdf.cell(0, 8, "How to Cite:", align="L")
    pdf.ln(7)
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(60, 60, 60)
    guides = [
        ("APA 7th Edition", "Used in social sciences, education, and many computing journals."),
        ("IEEE", "Standard for electrical engineering, computer science, and IT conferences/journals."),
        ("ACM", "Used in ACM-published computing and information technology research."),
    ]
    for style, desc in guides:
        pdf.set_font("Helvetica", "B", 9)
        pdf.cell(35, 6, f"  {style}:", ln=0)
        pdf.set_font("Helvetica", "", 9)
        pdf.cell(0, 6, desc, ln=1)

    # ── Publication entries ──────────────────────────────────
    # Sort by year desc then title
    rows.sort(key=lambda r: (-int(r["Year"]), r["Title"]))

    current_year = None
    for idx, r in enumerate(rows, 1):
        year = r["Year"]
        title = clean(r["Title"])
        authors = split_authors(r["Researchers"])
        campus = r["CampusMatched"]
        program = r["ProgramInferred"]
        doi = r["DOI"]
        url = f"https://doi.org/{doi}"
        pub_type = "Conference Paper" if r["Type"] == "proceedings-article" else "Journal Article"

        # Year section header
        if year != current_year:
            current_year = year
            pdf.add_page()
            pdf.set_font("Helvetica", "B", 16)
            pdf.set_text_color(25, 60, 120)
            year_count = sum(1 for x in rows if x["Year"] == year)
            pdf.cell(0, 10, f"{year}  ({year_count} publication{'s' if year_count != 1 else ''})", ln=1)
            pdf.set_draw_color(25, 60, 120)
            pdf.line(10, pdf.get_y(), 200, pdf.get_y())
            pdf.ln(4)

        # Check space - if less than 70mm remain, add new page
        if pdf.get_y() > 220:
            pdf.add_page()

        # Publication number and title
        pdf.set_font("Helvetica", "B", 10)
        pdf.set_text_color(30, 30, 30)
        pdf.multi_cell(0, 5, f"[{idx}]  {title}")
        pdf.ln(1)

        # Metadata line
        pdf.set_font("Helvetica", "", 8)
        pdf.set_text_color(80, 80, 80)
        pdf.cell(0, 4, f"{pub_type}  |  {campus}  |  {program}  |  DOI: {doi}", ln=1)
        pdf.ln(2)

        # Authors
        pdf.set_font("Helvetica", "I", 8)
        pdf.set_text_color(60, 60, 60)
        pdf.multi_cell(0, 4, f"Authors: {', '.join(authors)}")
        pdf.ln(2)

        # APA citation
        pdf.set_font("Helvetica", "B", 8)
        pdf.set_text_color(0, 100, 0)
        pdf.cell(0, 4, "APA 7th Edition:", ln=1)
        pdf.set_font("Helvetica", "", 8)
        pdf.set_text_color(40, 40, 40)
        apa = cite_apa(r, authors)
        pdf.multi_cell(0, 4, apa)
        pdf.ln(1)

        # IEEE citation
        pdf.set_font("Helvetica", "B", 8)
        pdf.set_text_color(0, 60, 150)
        pdf.cell(0, 4, "IEEE:", ln=1)
        pdf.set_font("Helvetica", "", 8)
        pdf.set_text_color(40, 40, 40)
        ieee = cite_ieee(r, authors)
        pdf.multi_cell(0, 4, ieee)
        pdf.ln(1)

        # ACM citation
        pdf.set_font("Helvetica", "B", 8)
        pdf.set_text_color(150, 50, 0)
        pdf.cell(0, 4, "ACM:", ln=1)
        pdf.set_font("Helvetica", "", 8)
        pdf.set_text_color(40, 40, 40)
        acm = cite_acm(r, authors)
        pdf.multi_cell(0, 4, acm)
        pdf.ln(1)

        # DOI Link
        pdf.set_font("Helvetica", "U", 8)
        pdf.set_text_color(0, 0, 200)
        pdf.cell(0, 4, url, link=url, ln=1)

        # Separator
        pdf.ln(2)
        pdf.set_draw_color(200, 200, 200)
        pdf.line(10, pdf.get_y(), 200, pdf.get_y())
        pdf.ln(3)

    # ── Summary page ─────────────────────────────────────────
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 16)
    pdf.set_text_color(25, 60, 120)
    pdf.cell(0, 10, "Summary Statistics", ln=1)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(6)

    # By campus
    from collections import Counter
    campus_counts = Counter(r["CampusMatched"] for r in rows)
    pdf.set_font("Helvetica", "B", 11)
    pdf.set_text_color(40, 40, 40)
    pdf.cell(0, 7, "Publications by Campus:", ln=1)
    pdf.set_font("Helvetica", "", 10)
    for campus, count in campus_counts.most_common():
        pdf.cell(10)
        pdf.cell(0, 6, f"{campus}: {count}", ln=1)
    pdf.ln(4)

    # By program
    prog_counts = Counter(r["ProgramInferred"] for r in rows)
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(0, 7, "Publications by Program:", ln=1)
    pdf.set_font("Helvetica", "", 10)
    for prog, count in prog_counts.most_common():
        pdf.cell(10)
        pdf.cell(0, 6, f"{prog}: {count}", ln=1)
    pdf.ln(4)

    # By year
    year_counts = Counter(r["Year"] for r in rows)
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(0, 7, "Publications by Year:", ln=1)
    pdf.set_font("Helvetica", "", 10)
    for yr in sorted(year_counts):
        pdf.cell(10)
        pdf.cell(0, 6, f"{yr}: {year_counts[yr]}", ln=1)
    pdf.ln(4)

    # By type
    type_counts = Counter(
        "Conference Paper" if r["Type"] == "proceedings-article" else "Journal Article"
        for r in rows
    )
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(0, 7, "Publications by Type:", ln=1)
    pdf.set_font("Helvetica", "", 10)
    for t, count in type_counts.most_common():
        pdf.cell(10)
        pdf.cell(0, 6, f"{t}: {count}", ln=1)

    # Save
    pdf.output(OUTPUT_PDF)
    print(f"PDF saved: {OUTPUT_PDF}")
    print(f"Total pages: {pdf.page_no()}")


# ── main ─────────────────────────────────────────────────────
with open(CSV_FILE, encoding="utf-8-sig") as f:
    rows = list(csv.DictReader(f))

print(f"Loaded {len(rows)} publications")
build_pdf(rows)
