#!/usr/bin/env python3
"""Fill meeting-minutes template.docx by updating column-2 table cells only."""

from __future__ import annotations

import argparse
import copy
import json
import re
import sys
import tempfile
import zipfile
from datetime import date
from pathlib import Path
from xml.etree import ElementTree as ET

W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
XML_SPACE = "{http://www.w3.org/XML/1998/namespace}space"

FIELD_ORDER = [
    "project_name",
    "interview_purpose",
    "interview_time",
    "interview_location",
    "participants",
    "topics",
    "interview_notes",
    "interview_results",
    "interviewee_suggestions",
]

INVALID_FS_CHARS = re.compile(r'[\\/:*?"<>|]')


def sanitize_filename_part(value: str, fallback: str = "待补充") -> str:
    cleaned = INVALID_FS_CHARS.sub("-", value.strip())
    return cleaned or fallback


def parse_date(value: str) -> str:
    value = value.strip()
    m = re.search(r"(\d{4})[-/年.](\d{1,2})[-/月.](\d{1,2})", value)
    if m:
        y, mo, d = m.groups()
        return f"{int(y):04d}-{int(mo):02d}-{int(d):02d}"
    m = re.search(r"(\d{4})(\d{2})(\d{2})", value)
    if m:
        y, mo, d = m.groups()
        return f"{int(y):04d}-{int(mo):02d}-{int(d):02d}"
    return date.today().isoformat()


def output_filename(fields: dict[str, str]) -> str:
    project = sanitize_filename_part(fields.get("project_name", ""))
    when = parse_date(fields.get("interview_time", ""))
    return f"【{project}】客户访谈记录-{when}.docx"


def normalize_cell_text(text: str) -> str:
    """Normalize line endings; trim trailing spaces per line; collapse 3+ blank lines."""
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    lines = [line.rstrip() for line in text.split("\n")]
    out: list[str] = []
    blank_run = 0
    for line in lines:
        if line == "":
            blank_run += 1
            if blank_run <= 2:
                out.append("")
            continue
        blank_run = 0
        out.append(line)
    return "\n".join(out).strip("\n")


def split_lines(text: str) -> list[str]:
    normalized = normalize_cell_text(text)
    if not normalized:
        return [""]
    return normalized.split("\n")


def clone_paragraph_prototype(tc: ET.Element) -> tuple[ET.Element | None, ET.Element]:
    paragraphs = tc.findall(f"{W}p")
    if not paragraphs:
        raise ValueError("table cell has no paragraphs")

    template_p = paragraphs[0]
    template_pPr = template_p.find(f"{W}pPr")
    template_r = template_p.find(f"{W}r")
    if template_r is None:
        template_r = ET.Element(f"{W}r")
    return (
        copy.deepcopy(template_pPr) if template_pPr is not None else None,
        copy.deepcopy(template_r),
    )


def make_text_run(run_prototype: ET.Element, line: str) -> ET.Element:
    new_r = copy.deepcopy(run_prototype)
    for child in list(new_r):
        if child.tag in (f"{W}t", f"{W}br", f"{W}tab", f"{W}lastRenderedPageBreak"):
            new_r.remove(child)

    if line == "":
        t = ET.SubElement(new_r, f"{W}t")
        t.text = ""
        return new_r

    t = ET.SubElement(new_r, f"{W}t")
    if line.startswith(" ") or line.endswith(" ") or "\t" in line:
        t.set(XML_SPACE, "preserve")
    t.text = line
    return new_r


def make_paragraph(pPr_prototype: ET.Element | None, run_prototype: ET.Element, line: str) -> ET.Element:
    p = ET.Element(f"{W}p")
    if pPr_prototype is not None:
        p.append(copy.deepcopy(pPr_prototype))
    p.append(make_text_run(run_prototype, line))
    return p


def set_cell_text(tc: ET.Element, text: str) -> None:
    """Write text into column-2 cell; each \\n becomes a separate Word paragraph."""
    lines = split_lines(text)
    pPr_proto, run_proto = clone_paragraph_prototype(tc)

    for old_p in tc.findall(f"{W}p"):
        tc.remove(old_p)

    for line in lines:
        tc.append(make_paragraph(pPr_proto, run_proto, line))


def fill_document_xml(xml_bytes: bytes, fields: dict[str, str]) -> bytes:
    root = ET.fromstring(xml_bytes)
    tables = root.findall(f".//{W}tbl")
    if len(tables) != 1:
        raise ValueError(f"expected 1 table, found {len(tables)}")

    rows = tables[0].findall(f"{W}tr")
    if len(rows) != 9:
        raise ValueError(f"expected 9 rows, found {len(rows)}")

    for idx, key in enumerate(FIELD_ORDER):
        cells = rows[idx].findall(f"{W}tc")
        if len(cells) != 2:
            raise ValueError(f"row {idx + 1}: expected 2 columns, found {len(cells)}")
        set_cell_text(cells[1], fields.get(key, "[待补充]"))

    ET.register_namespace("w", "http://schemas.openxmlformats.org/wordprocessingml/2006/main")
    return ET.tostring(root, encoding="utf-8", xml_declaration=True)


def fill_template(template: Path, output: Path, fields: dict[str, str]) -> Path:
    if not template.is_file():
        raise FileNotFoundError(template)

    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        extracted = Path(tmp) / "doc"
        with zipfile.ZipFile(template) as zin:
            zin.extractall(extracted)

        doc_xml = extracted / "word" / "document.xml"
        doc_xml.write_bytes(fill_document_xml(doc_xml.read_bytes(), fields))

        with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as zout:
            for path in sorted(extracted.rglob("*")):
                if path.is_file():
                    zout.write(path, path.relative_to(extracted).as_posix())

    return output


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    default_template = Path(__file__).resolve().parents[1] / "assets" / "template.docx"
    parser.add_argument("--template", type=Path, default=default_template)
    parser.add_argument("--fields-json", type=Path, help="JSON file with field values")
    parser.add_argument("--output-dir", type=Path, default=Path.cwd())
    parser.add_argument("--output", type=Path, help="Explicit output .docx path")
    args = parser.parse_args()

    if args.fields_json:
        fields = json.loads(args.fields_json.read_text(encoding="utf-8"))
    else:
        fields = json.loads(sys.stdin.read())

    for key in FIELD_ORDER:
        fields.setdefault(key, "[待补充]")

    out = args.output or (args.output_dir / output_filename(fields))
    fill_template(args.template, out, fields)
    print(out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
