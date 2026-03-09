#!/usr/bin/env python3
from __future__ import annotations

import argparse
import html
import re
import shutil
import zipfile
from pathlib import Path
import xml.etree.ElementTree as ET


NS = {
    "hp": "http://www.hancom.co.kr/hwpml/2011/paragraph",
    "hc": "http://www.hancom.co.kr/hwpml/2011/core",
}


def qname(prefix: str, local: str) -> str:
    return f"{{{NS[prefix]}}}{local}"


def clean_text(text: str) -> str:
    text = text.replace("\xa0", " ")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def paragraph_text(p: ET.Element) -> str:
    parts: list[str] = []
    for run in p.findall("hp:run", NS):
        if run.text:
            parts.append(run.text)
        for child in run:
            tag = child.tag.split("}")[-1]
            if tag == "t":
                if child.text:
                    parts.append(child.text)
                for sub in child:
                    if sub.tag == qname("hp", "lineBreak"):
                        parts.append("\n")
                    if sub.tail:
                        parts.append(sub.tail)
                if child.tail:
                    parts.append(child.tail)
            elif tag == "lineBreak":
                parts.append("\n")
            elif child.tail:
                parts.append(child.tail)
        if run.tail:
            parts.append(run.tail)
    return clean_text("".join(parts))


def paragraph_images(p: ET.Element, image_map: dict[str, str]) -> list[str]:
    refs: list[str] = []
    for pic in p.findall(".//hp:pic", NS):
        img = pic.find("hc:img", NS)
        if img is None:
            continue
        ref = img.get("binaryItemIDRef")
        if not ref:
            continue
        filename = image_map.get(ref)
        if filename:
            refs.append(filename)
    return refs


def cell_text(tc: ET.Element) -> str:
    chunks: list[str] = []
    for sub in tc.findall(".//hp:subList", NS):
        texts = []
        for p in sub.findall("hp:p", NS):
            text = paragraph_text(p)
            if text:
                texts.append(text)
        if texts:
            chunks.append("\n".join(texts))
    return clean_text("\n".join(chunks))


def render_table(tbl: ET.Element) -> str:
    rows: list[str] = []
    for tr in tbl.findall("hp:tr", NS):
        cells: list[str] = []
        for tc in tr.findall("hp:tc", NS):
            span = tc.find("hp:cellSpan", NS)
            colspan = span.get("colSpan", "1") if span is not None else "1"
            rowspan = span.get("rowSpan", "1") if span is not None else "1"
            text = html.escape(cell_text(tc)).replace("\n", "<br>")
            attrs = []
            if colspan != "1":
                attrs.append(f' colspan="{colspan}"')
            if rowspan != "1":
                attrs.append(f' rowspan="{rowspan}"')
            cells.append(f"<td{''.join(attrs)}>{text or '&nbsp;'}</td>")
        rows.append(f"<tr>{''.join(cells)}</tr>")
    return '<table class="hwpx-table">' + "".join(rows) + "</table>"


def top_level_blocks(root: ET.Element, image_map: dict[str, str]) -> list[str]:
    blocks: list[str] = []
    seen_tables: set[str] = set()
    for p in root.findall("hp:p", NS):
        # Inline images anchored in a paragraph.
        for filename in paragraph_images(p, image_map):
            blocks.append(
                f'<figure class="hwpx-image"><img src="{html.escape(filename)}" alt=""></figure>'
            )

        for tbl in p.findall("hp:run/hp:tbl", NS):
            tbl_id = tbl.get("id") or str(id(tbl))
            if tbl_id in seen_tables:
                continue
            seen_tables.add(tbl_id)
            blocks.append(render_table(tbl))

        text = paragraph_text(p)
        if text:
            escaped = html.escape(text).replace("\n", "<br>")
            blocks.append(f'<p class="hwpx-paragraph">{escaped}</p>')
    return blocks


def extract_images(zf: zipfile.ZipFile, asset_dir: Path) -> dict[str, str]:
    if asset_dir.exists():
        shutil.rmtree(asset_dir)
    asset_dir.mkdir(parents=True, exist_ok=True)

    image_map: dict[str, str] = {}
    for name in zf.namelist():
        if not name.startswith("BinData/"):
            continue
        src = Path(name)
        stem = src.stem
        dest = asset_dir / src.name
        dest.write_bytes(zf.read(name))
        image_map[stem] = f"{asset_dir.name}/{dest.name}"
    return image_map


def render_html(title: str, blocks: list[str]) -> str:
    body = "\n".join(blocks)
    return f"""<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{html.escape(title)}</title>
  <style>
    body {{
      margin: 0;
      padding: 24px;
      background: #f3f3f3;
      color: #111;
      font-family: "Malgun Gothic", "Apple SD Gothic Neo", sans-serif;
      line-height: 1.6;
    }}
    .document {{
      max-width: 1120px;
      margin: 0 auto;
      padding: 32px;
      background: #fff;
      box-shadow: 0 8px 30px rgba(0,0,0,0.08);
    }}
    h1 {{
      margin: 0 0 24px;
      font-size: 28px;
    }}
    .hwpx-paragraph {{
      margin: 10px 0;
      white-space: normal;
      word-break: keep-all;
    }}
    .hwpx-table {{
      width: 100%;
      border-collapse: collapse;
      margin: 18px 0 28px;
      font-size: 13px;
    }}
    .hwpx-table td {{
      border: 1px solid #222;
      padding: 6px 8px;
      vertical-align: top;
      word-break: break-word;
      min-width: 36px;
    }}
    .hwpx-image {{
      margin: 16px 0;
    }}
    .hwpx-image img {{
      max-width: 100%;
      height: auto;
      border: 1px solid #ddd;
    }}
    @media print {{
      body {{
        padding: 0;
        background: #fff;
      }}
      .document {{
        box-shadow: none;
        max-width: none;
        padding: 0;
      }}
    }}
  </style>
</head>
<body>
  <main class="document">
    <h1>{html.escape(title)}</h1>
    {body}
  </main>
</body>
</html>
"""


def main() -> None:
    parser = argparse.ArgumentParser(description="Convert HWTX/HWPX to a basic HTML document.")
    parser.add_argument("input", type=Path, help="Path to .hwtx/.hwpx file")
    parser.add_argument("output", type=Path, help="Path to output HTML file")
    args = parser.parse_args()

    with zipfile.ZipFile(args.input) as zf:
        root = ET.fromstring(zf.read("Contents/section0.xml"))
        asset_dir = args.output.with_name(args.output.stem + "_assets")
        image_map = extract_images(zf, asset_dir)
        blocks = top_level_blocks(root, image_map)

    title = args.input.stem
    args.output.write_text(render_html(title, blocks), encoding="utf-8")
    print(f"wrote {args.output}")


if __name__ == "__main__":
    main()
