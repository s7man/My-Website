from __future__ import annotations

import html
import json
import re
from pathlib import Path

from docx import Document
from docx.oxml.ns import qn
from docx.oxml.table import CT_Tbl
from docx.oxml.text.paragraph import CT_P
from docx.table import Table
from docx.text.paragraph import Paragraph


ROOT = Path(__file__).resolve().parents[1]
SOURCE_DIR = ROOT / "resources" / "source-docx"
OUTPUT_DIR = ROOT / "Notes" / "6th-sem"
CATALOG_PATH = ROOT / "data" / "notes-catalog.js"

SUBJECTS = [
    {
        "id": "entc",
        "slug": "electrical-testing-and-commissioning",
        "name": "ENTC",
        "fullName": "Electrical Testing and Commissioning",
        "description": "Safety, installation, testing, commissioning, and maintenance notes.",
        "source": "electrical-testing-and-commissioning.docx",
    },
    {
        "id": "eca",
        "slug": "energy-conservation-and-audit",
        "name": "ECA",
        "fullName": "Energy Conservation and Audit",
        "description": "Energy conservation basics, machines, installations, cogeneration, tariffs, and audit methods.",
        "source": "energy-conservation-and-audit.docx",
    },
    {
        "id": "eep",
        "slug": "engineering-economics-and-project",
        "name": "EEP",
        "fullName": "Engineering Economics and Project",
        "description": "Engineering economics concepts and project management study material.",
        "source": "engineering-economics-and-project.docx",
    },
    {
        "id": "ens",
        "slug": "entrepreneurship-and-start-up",
        "name": "ENS",
        "fullName": "Entrepreneurship and Start-up",
        "description": "Entrepreneurship, small enterprises, start-up ventures, funding, and exit strategies.",
        "source": "entrepreneurship-and-start-up.docx",
    },
]


# Converts heading text into a browser-friendly anchor id.
def slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or "section"


# Keeps generated ids unique inside one subject page.
def unique_id(value: str, used_ids: set[str]) -> str:
    base = slugify(value)
    candidate = base
    counter = 2

    while candidate in used_ids:
        candidate = f"{base}-{counter}"
        counter += 1

    used_ids.add(candidate)
    return candidate


# Yields paragraphs and tables in the same order Word stores them.
def iter_blocks(document: Document):
    for child in document.element.body.iterchildren():
        if isinstance(child, CT_P):
            yield Paragraph(child, document)
        elif isinstance(child, CT_Tbl):
            yield Table(child, document)


# Converts Word heading styles into page heading levels.
def get_heading_level(paragraph: Paragraph) -> int | None:
    style_name = paragraph.style.name if paragraph.style else ""
    match = re.fullmatch(r"Heading ([1-6])", style_name)

    if match:
        return min(int(match.group(1)) + 1, 6)

    return None


# Extracts text from a table cell without losing paragraph breaks.
def cell_text(cell) -> str:
    return "\n".join(part.strip() for part in cell.text.splitlines() if part.strip())


# Converts a Word table into simple, responsive HTML.
def table_to_html(table: Table) -> str:
    if not table.rows:
        return ""

    rows = []
    for row_index, row in enumerate(table.rows):
        tag = "th" if row_index == 0 else "td"
        cells = "".join(
            f"<{tag}>{html.escape(cell_text(cell)).replace(chr(10), '<br>')}</{tag}>"
            for cell in row.cells
        )
        rows.append(f"<tr>{cells}</tr>")

    head = f"<thead>{rows[0]}</thead>"
    body = f"<tbody>{''.join(rows[1:])}</tbody>" if len(rows) > 1 else ""
    return f'<div class="table-wrap"><table>{head}{body}</table></div>'


# Saves images from one paragraph and returns matching figure HTML.
def extract_paragraph_images(paragraph: Paragraph, media_dir: Path, subject_title: str, start_index: int) -> tuple[list[str], int]:
    figures = []
    image_index = start_index

    for blip in paragraph._p.xpath(".//a:blip"):
        rel_id = blip.get(qn("r:embed"))
        if not rel_id:
            continue

        image_part = paragraph.part.related_parts[rel_id]
        extension = image_part.content_type.split("/")[-1].replace("jpeg", "jpg")
        image_name = f"image-{image_index}.{extension}"
        image_path = media_dir / image_name
        image_path.write_bytes(image_part.blob)

        figures.append(
            '<figure class="doc-figure">'
            f'<img src="media/{image_name}" alt="{html.escape(subject_title)} figure {image_index}">'
            "</figure>"
        )
        image_index += 1

    return figures, image_index


# Converts one DOCX into a subject HTML page and returns catalog unit entries.
def convert_subject(subject: dict) -> dict:
    source_path = SOURCE_DIR / subject["source"]
    subject_dir = OUTPUT_DIR / subject["slug"]
    media_dir = subject_dir / "media"
    document = Document(source_path)
    content_html = []
    toc_entries = []
    used_ids = set()
    current_toc_entry = None
    image_index = 1
    list_open = False

    subject_dir.mkdir(parents=True, exist_ok=True)
    media_dir.mkdir(parents=True, exist_ok=True)

    for block in iter_blocks(document):
        if isinstance(block, Table):
            if list_open:
                content_html.append("</ul>")
                list_open = False
            content_html.append(table_to_html(block))
            continue

        text = " ".join(block.text.split())
        heading_level = get_heading_level(block)
        figures, image_index = extract_paragraph_images(block, media_dir, subject["fullName"], image_index)

        if heading_level:
            if list_open:
                content_html.append("</ul>")
                list_open = False

            section_id = unique_id(text, used_ids)
            content_html.append(f'<h{heading_level} id="{section_id}">{html.escape(text)}</h{heading_level}>')

            if heading_level == 2:
                current_toc_entry = {
                    "title": text,
                    "id": section_id,
                    "summary": "",
                }
                toc_entries.append(current_toc_entry)
        elif text:
            if block.style and "List" in block.style.name:
                if not list_open:
                    content_html.append("<ul>")
                    list_open = True
                content_html.append(f"<li>{html.escape(text)}</li>")
            else:
                if list_open:
                    content_html.append("</ul>")
                    list_open = False
                content_html.append(f"<p>{html.escape(text)}</p>")

            if current_toc_entry and not current_toc_entry["summary"] and len(text) > 24:
                current_toc_entry["summary"] = text[:150]

        content_html.extend(figures)

    if list_open:
        content_html.append("</ul>")

    if not toc_entries:
        toc_entries.append(
            {
                "title": "Full Notes",
                "id": "full-notes",
                "summary": subject["description"],
            }
        )
        content_html.insert(0, '<h2 id="full-notes">Full Notes</h2>')

    page_html = build_subject_page(subject, toc_entries, "\n".join(content_html))
    (subject_dir / "index.html").write_text(page_html, encoding="utf-8")

    return {
        "id": subject["id"],
        "name": subject["name"],
        "fullName": subject["fullName"],
        "description": subject["description"],
        "units": [
            {
                "title": entry["title"],
                "href": f'Notes/6th-sem/{subject["slug"]}/index.html#{entry["id"]}',
                "summary": entry["summary"] or "Open this section notes.",
                "keywords": f'{subject["name"]} {subject["fullName"]} {entry["title"]}',
                "available": True,
            }
            for entry in toc_entries
        ],
    }


# Builds the complete subject page around converted DOCX content.
def build_subject_page(subject: dict, toc_entries: list[dict], content: str) -> str:
    toc_links = "\n".join(
        f'<li><a href="#{entry["id"]}">{html.escape(entry["title"])}</a></li>'
        for entry in toc_entries
    )
    source_doc = f'../../../resources/source-docx/{subject["source"]}'

    return f"""<!DOCTYPE html>
<html lang="en">

<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{html.escape(subject["fullName"])} | Notes Share</title>
  <script src="../../../data/theme-init.js"></script>
  <link rel="stylesheet" href="../../../style.css">
</head>

<body>
  <nav aria-label="Primary navigation">
    <a href="../../../index.html">Home</a>
    <a href="../../../index.html#semesters">Semesters</a>
    <a href="../../../index.html#catalog">Subjects</a>
    <a href="../../../support and contact/support.html">Contact Us</a>
    <button class="theme-toggle" id="themeToggle" type="button" aria-label="Switch to dark mode" aria-pressed="false">
      <span class="theme-toggle-mark" aria-hidden="true"></span>
      <span id="themeToggleText">Dark</span>
    </button>
  </nav>

  <main class="doc-page">
    <header class="doc-header">
      <p class="eyebrow">6th Semester</p>
      <h1>{html.escape(subject["fullName"])}</h1>
      <p>{html.escape(subject["description"])}</p>
      <div class="doc-actions">
        <a class="button primary-button" href="../../../index.html#sem-6">Back to 6th Semester</a>
        <a class="button secondary-button" href="{source_doc}" download>Download DOCX</a>
      </div>
    </header>

    <nav class="subject-toc" aria-label="Subject contents">
      <h2>Contents</h2>
      <ol>
        {toc_links}
      </ol>
    </nav>

    <article class="doc-content">
      {content}
    </article>
  </main>

  <footer>
    <p>&copy; 2026 Notes Share | All Rights Reserved</p>
  </footer>

  <script src="../../../data/theme.js"></script>
</body>

</html>
"""


# Regenerates the catalog file so imported subjects appear in 6th semester.
def write_catalog(subjects: list[dict]) -> None:
    catalog = [
        {
            "id": "sem-1",
            "title": "1st Semester",
            "description": "Foundation subjects can be added here.",
            "subjects": [],
        },
        {
            "id": "sem-2",
            "title": "2nd Semester",
            "description": "Add second semester subjects when notes are ready.",
            "subjects": [],
        },
        {
            "id": "sem-3",
            "title": "3rd Semester",
            "description": "Add third semester subjects when notes are ready.",
            "subjects": [],
        },
        {
            "id": "sem-4",
            "title": "4th Semester",
            "description": "Add fourth semester subjects when notes are ready.",
            "subjects": [],
        },
        {
            "id": "sem-5",
            "title": "5th Semester",
            "description": "Add fifth semester subjects when notes are ready.",
            "subjects": [],
        },
        {
            "id": "sem-6",
            "title": "6th Semester",
            "description": "Final semester notes organized by subject and unit.",
            "subjects": subjects,
        },
    ]
    output = (
        "// Main notes data: add semesters, subjects, and unit links here.\n"
        "// The homepage reads this file and builds the catalog automatically.\n"
        f"window.notesCatalog = {json.dumps(catalog, indent=2, ensure_ascii=False)};\n"
    )
    CATALOG_PATH.write_text(output, encoding="utf-8")


# Runs the full DOCX import for all configured 6th semester subjects.
def main() -> None:
    converted_subjects = [convert_subject(subject) for subject in SUBJECTS]
    write_catalog(converted_subjects)
    print(f"Imported {len(converted_subjects)} subjects into {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
