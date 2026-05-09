"""V6.25.25 (Cycle E) — Codex Node PDF export with inverted theme.

The user requested an Azazel-style gothic/layered aesthetic for the
codex-node PDF export. The simplest, most striking implementation is
to invert the campaign chronicle's existing palette: white borders /
text become black, black backgrounds become white. Everything else
(layout, font choices, section ordering) stays the same.

This is a SEPARATE endpoint from the main chronicle export at
`/campaigns/{cid}/export.pdf` — it does NOT change the chronicle's
look. GMs invoke it explicitly when they want a printable, white-paper-
friendly codex book.

Endpoint:
    GET /api/campaigns/{cid}/codex-export.pdf
"""
from __future__ import annotations
import io
from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse

from core.db import db
from core.security import get_current_user
from .azazel_layout import has_azazel_data, render_azazel_entity

router = APIRouter(prefix="/api", tags=["codex-pdf"])


# Inverted palette — black ink on white paper, with the secondary gold
# darkened so it reads on white. Matches the user's "Azazel-style gothic"
# brief: stark, layered, white-paper-friendly.
INVERTED_PALETTE = {
    "background": "#FFFFFF",
    "primary":    "#000000",   # was light gold/cream → now hard black
    "secondary":  "#3F2A07",   # darkened gold so it survives on white
    "accent":     "#7A1F2E",
    "ink":        "#0B0710",
    "muted":      "#3A3540",
    "rule":       "#000000",
    "callout_bg": "#FFFFFF",
    "callout_border": "#000000",
}


def _inverted_text_color(c: str) -> str:
    """Map the dark-theme ink colors to the inverted palette."""
    table = {
        "#FAF6EC": "#0B0710",  # parchment text → ink
        "#FFFFFF": "#000000",
        "#C8A34A": "#3F2A07",
    }
    return table.get(c.upper(), c)


@router.get("/campaigns/{cid}/codex-export.pdf")
async def export_codex_pdf(cid: str, user: dict = Depends(get_current_user)):
    """V6.25.25 (Cycle E) — codex-only PDF with inverted (white-paper) theme.

    Produces a clean, printable PDF containing ONLY shared codex nodes
    for the campaign — no narrative, no characters, no chronicle prose.
    The palette is inverted (black on white) so the result prints
    cleanly on standard office paper.
    """
    camp = await db.campaigns.find_one({"id": cid}, {"_id": 0})
    if not camp:
        raise HTTPException(404, "Campaign not found.")
    if camp["gm_id"] != user["id"] and user.get("role") != "admin":
        raise HTTPException(403, "GM/admin only.")

    nodes = await db.nodes.find(
        {"campaign_id": cid}, {"_id": 0}
    ).sort("title", 1).to_list(1000)

    if not nodes:
        raise HTTPException(400, "No shared codex nodes to export.")

    # Build a simple ReportLab PDF. Using SimpleDocTemplate so we don't
    # need to re-implement the chronicle's chapter machinery — codex
    # nodes are short, self-contained entries.
    from reportlab.lib.colors import HexColor
    from reportlab.lib.pagesizes import LETTER
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer,
                                       PageBreak, Table, TableStyle)

    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=LETTER,
        leftMargin=0.75 * inch, rightMargin=0.75 * inch,
        topMargin=0.85 * inch, bottomMargin=0.85 * inch,
        title=f"{camp.get('name', 'Codex')} — Codex",
        author=user.get("name", "Table-Gnostic GM"),
    )

    p = INVERTED_PALETTE
    sheet = getSampleStyleSheet()
    body = ParagraphStyle("Body", parent=sheet["Normal"],
                           fontName="Helvetica", fontSize=10, leading=14,
                           textColor=HexColor(p["ink"]))
    h_title = ParagraphStyle("H_Title", parent=sheet["Title"],
                              fontName="Helvetica-Bold", fontSize=22, leading=26,
                              textColor=HexColor(p["primary"]),
                              spaceAfter=6)
    h_section = ParagraphStyle("H_Section", parent=sheet["Heading1"],
                                fontName="Helvetica-Bold", fontSize=14, leading=18,
                                textColor=HexColor(p["primary"]),
                                spaceBefore=10, spaceAfter=4,
                                borderPadding=(0, 0, 4, 0))
    h_kind = ParagraphStyle("H_Kind", parent=sheet["Normal"],
                             fontName="Helvetica-Oblique", fontSize=9, leading=12,
                             textColor=HexColor(p["secondary"]),
                             spaceAfter=2)
    callout = ParagraphStyle("Callout", parent=body,
                               fontName="Helvetica-Oblique",
                               textColor=HexColor(p["accent"]))
    # V6.25.30 — pre-bundled style map for the Azazel composer.
    az_styles = {"body": body, "h_title": h_title,
                 "h_section": h_section, "h_kind": h_kind}

    flow: List[Any] = []
    flow.append(Paragraph(camp.get("name", "Codex"), h_title))
    flow.append(Paragraph("World Codex · printable edition", h_kind))
    flow.append(Spacer(1, 0.15 * inch))
    flow.append(_horizontal_rule(p))
    flow.append(Spacer(1, 0.2 * inch))

    # Group nodes by node_kind for easier scanning.
    from collections import defaultdict
    grouped = defaultdict(list)
    for n in nodes:
        kind = (n.get("node_kind") or n.get("type") or "concept").strip() or "concept"
        grouped[kind].append(n)

    # V6.25.30 — entity-class kinds get the dramatic Azazel-style page.
    # Everything else stays on the legacy compact layout.
    AZAZEL_KINDS = {"npc", "character", "creature", "monster",
                    "person", "faction", "location"}

    for kind in sorted(grouped.keys()):
        flow.append(Paragraph(f"{kind.replace('_', ' ').title()} ({len(grouped[kind])})", h_section))
        flow.append(_horizontal_rule(p, weight=0.5))
        flow.append(Spacer(1, 0.1 * inch))
        for n in grouped[kind]:
            if kind in AZAZEL_KINDS and has_azazel_data(n):
                # Rich entity — render with the Azazel-style sectioned page.
                flow.extend(render_azazel_entity(n, az_styles))
                continue
            title = n.get("title") or n.get("name") or "Untitled"
            section = (n.get("creation_tree") or {}).get("section") or ""
            flow.append(Paragraph(f"<b>{_xml(title)}</b>", body))
            if section:
                flow.append(Paragraph(f"<i>{_xml(section)}</i>", h_kind))
            summary = n.get("summary") or ""
            if summary:
                flow.append(Paragraph(_xml(summary), body))
            content = (n.get("content") or "").strip()
            if content:
                flow.append(Paragraph(_xml(content), body))
            tags = n.get("tags") or []
            if tags:
                flow.append(Paragraph(
                    "<i>tags:</i> " + ", ".join(_xml(t) for t in tags),
                    h_kind))
            flow.append(Spacer(1, 0.13 * inch))
        flow.append(PageBreak())

    flow.append(Paragraph("— end of codex —", callout))

    doc.build(flow,
               onFirstPage=lambda c, d: _bg(c, d, p),
               onLaterPages=lambda c, d: _bg(c, d, p))

    buf.seek(0)
    # Header values must be latin-1 safe; strip non-ASCII from filename
    # (campaign names commonly contain em-dashes / accented chars).
    raw_name = (camp.get("name") or "codex").replace(" ", "-").replace("/", "-")
    safe_name = "".join(
        ch if ord(ch) < 128 and ch not in '"\\' else "-" for ch in raw_name
    ).strip("-") or "codex"
    return StreamingResponse(
        buf, media_type="application/pdf",
        headers={
            "Content-Disposition":
                f'attachment; filename="{safe_name}-codex.pdf"',
        })


def _xml(s: Any) -> str:
    """ReportLab Paragraph treats text as XML — escape the basics."""
    if s is None:
        return ""
    return (str(s)
              .replace("&", "&amp;")
              .replace("<", "&lt;")
              .replace(">", "&gt;"))


def _horizontal_rule(palette: Dict[str, str], weight: float = 1.0):
    """Black horizontal rule for the inverted theme."""
    from reportlab.lib.colors import HexColor
    from reportlab.platypus import Table, TableStyle
    t = Table([[""]], colWidths=["100%"], rowHeights=[0.02 * 72])
    t.setStyle(TableStyle([
        ("LINEBELOW", (0, 0), (-1, -1), weight, HexColor(palette["primary"])),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
    ]))
    return t


def _bg(canvas, doc, palette: Dict[str, str]):
    """Paint the white background + a thin border so each page reads as
    an inverted Azazel-style gothic page."""
    from reportlab.lib.colors import HexColor
    canvas.saveState()
    canvas.setFillColor(HexColor(palette["background"]))
    canvas.rect(0, 0, doc.pagesize[0], doc.pagesize[1], stroke=0, fill=1)
    canvas.setStrokeColor(HexColor(palette["primary"]))
    canvas.setLineWidth(1)
    margin = 0.5 * 72
    canvas.rect(margin, margin,
                 doc.pagesize[0] - 2 * margin,
                 doc.pagesize[1] - 2 * margin,
                 stroke=1, fill=0)
    canvas.restoreState()
