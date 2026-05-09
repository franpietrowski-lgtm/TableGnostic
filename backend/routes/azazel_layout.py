"""V6.25.30 — Azazel-style entity layout for the inverted codex PDF.

Renders a single entity codex node (NPC / faction / creature / location)
in the dramatic, grid-laid-out layout shown in the user's Azazel
reference image:

  ┌──────────────────────────┐  ┌──────────────────────────┐
  │                          │  │      RESOURCES           │
  │     [HERO ART or         │  │                          │
  │      ornamental sigil]   │  │  POWER     PLAYER TARGETS│
  │                          │  │  NETWORKS  PLAYER TARGETS│
  │                          │  │  KNOWLEDGE PLAYER TARGETS│
  │   "pull-quote frame"     │  │  TOOLS     PLAYER TARGETS│
  └──────────────────────────┘  └──────────────────────────┘
  ┌──────────────── WEAKNESS ────────────────────────────┐
  │  description │ why-it's-a-weakness │ what-pcs-can-do │
  └──────────────────────────────────────────────────────┘
  ┌── THE COST ───────────┐  ┌─ PERMANENT CONSEQUENCES ──┐
  └───────────────────────┘  └───────────────────────────┘
  ┌──────────── WHO ELSE KNOWS ABOUT IT ─────────────────┐
  │  glyph │ name │ role  ··  glyph │ name │ role · etc. │
  └──────────────────────────────────────────────────────┘

Reads the following codex node `fields` (all optional — what's present
gets rendered, what's missing gracefully collapses):

    fields.subtitle              str         (e.g. "NEMESIS · FORCE")
    fields.portrait_url          str         (optional image URL)
    fields.quote                 str         (pull-quote in left frame)
    fields.resources             [{title, items[], player_targets[]}]
    fields.weakness.title        str
    fields.weakness.description  [str]       (bullet list)
    fields.weakness.why          [str]
    fields.weakness.player_can   [str]
    fields.weakness.flavour      str         (italic kicker)
    fields.cost.title            str         (default "THE COST")
    fields.cost.body             str
    fields.cost.note             str         (red-italic kicker)
    fields.cost.consequences     [str]
    fields.who_knows             [{name, role, glyph?}]

If none of the structured fields are present, the renderer falls back
to the simple title + summary + content layout (legacy behaviour).
"""
from __future__ import annotations
from typing import Any, Dict, List, Optional


# ── palette (inverted: black-on-white, gritty gold accents) ─────────
AZAZEL_PALETTE = {
    "page":     "#FFFFFF",
    "frame":    "#0B0710",   # near-black
    "ink":      "#0B0710",
    "muted":    "#3A3540",
    "gold":     "#3F2A07",   # darkened gold survives on white
    "gold_lt":  "#7A5912",
    "accent":   "#7A1F2E",   # blood red for cost band
    "shade":    "#F1ECE2",   # ivory wash for sub-panels
}


def _xml(s: Any) -> str:
    """Escape ReportLab Paragraph XML."""
    if s is None:
        return ""
    return (str(s)
              .replace("&", "&amp;")
              .replace("<", "&lt;")
              .replace(">", "&gt;"))


def has_azazel_data(node: Dict[str, Any]) -> bool:
    """True iff the node has at least one structured Azazel field."""
    f = node.get("fields") or {}
    return any(f.get(k) for k in (
        "resources", "weakness", "cost", "who_knows",
        "subtitle", "quote", "portrait_url",
    ))


def render_azazel_entity(node: Dict[str, Any], styles: Dict[str, Any]) -> List[Any]:
    """Return a flowable list rendering one entity in the Azazel layout.

    `styles` carries the calling module's pre-built ParagraphStyles
    (body, h_title, h_section, etc.) so we don't redefine them.
    """
    from reportlab.lib.colors import HexColor
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.platypus import (Paragraph, Spacer, Table, TableStyle,
                                       PageBreak, Image as RLImage)

    pal = AZAZEL_PALETTE
    f = node.get("fields") or {}
    title = (node.get("title") or node.get("name") or "Untitled").upper()
    subtitle = (f.get("subtitle") or _kind_subtitle(node)).upper()

    # ── styles tuned for the Azazel page ────────────────────────
    name_style = ParagraphStyle(
        "AzazelName", parent=styles["h_title"],
        fontName="Helvetica-Bold", fontSize=28, leading=32,
        textColor=HexColor(pal["frame"]),
        alignment=1)  # centre
    sub_style = ParagraphStyle(
        "AzazelSub", parent=styles["h_kind"],
        fontName="Helvetica-Oblique", fontSize=10, leading=12,
        textColor=HexColor(pal["gold"]),
        alignment=1)
    panel_h = ParagraphStyle(
        "AzazelPanelH", parent=styles["h_section"],
        fontName="Helvetica-Bold", fontSize=11, leading=14,
        textColor=HexColor(pal["gold"]),
        alignment=1, spaceAfter=4)
    sub_h = ParagraphStyle(
        "AzazelSubH", parent=styles["body"],
        fontName="Helvetica-Bold", fontSize=8, leading=10,
        textColor=HexColor(pal["frame"]),
        spaceAfter=2)
    bullet = ParagraphStyle(
        "AzazelBullet", parent=styles["body"],
        fontName="Helvetica", fontSize=8, leading=11,
        textColor=HexColor(pal["ink"]),
        leftIndent=8, bulletIndent=0,
        spaceBefore=0, spaceAfter=1)
    quote_style = ParagraphStyle(
        "AzazelQuote", parent=styles["body"],
        fontName="Helvetica-Oblique", fontSize=9, leading=12,
        textColor=HexColor(pal["muted"]),
        alignment=1, leftIndent=4, rightIndent=4,
        spaceBefore=4, spaceAfter=4)
    flav_style = ParagraphStyle(
        "AzazelFlav", parent=styles["body"],
        fontName="Helvetica-Oblique", fontSize=8, leading=10,
        textColor=HexColor(pal["accent"]),
        spaceBefore=4)
    band_h = ParagraphStyle(
        "AzazelBandH", parent=styles["h_section"],
        fontName="Helvetica-Bold", fontSize=12, leading=14,
        textColor=HexColor(pal["frame"]),
        alignment=1, spaceAfter=4)

    flow: List[Any] = []

    # ── Title bar ───────────────────────────────────────────────
    flow.append(Paragraph(_xml(title), name_style))
    flow.append(Paragraph(_xml("— " + subtitle + " —"), sub_style))
    flow.append(Spacer(1, 0.12 * inch))

    # ── Hero (left) + Resources (right) ─────────────────────────
    # Hero column content: art (placeholder ornament) + pull-quote.
    hero_cell: List[Any] = []
    portrait = f.get("portrait_url")
    if portrait:
        try:
            img = RLImage(portrait, width=3.0 * inch, height=3.6 * inch,
                            kind="proportional")
            hero_cell.append(img)
        except Exception:  # noqa: BLE001 — fall through to ornament
            hero_cell.append(_ornament_placeholder())
    else:
        hero_cell.append(_ornament_placeholder())
    summary = (node.get("summary") or "").strip()
    if summary:
        hero_cell.append(Spacer(1, 0.1 * inch))
        hero_cell.append(Paragraph(_xml(summary), styles["body"]))
    quote = (f.get("quote") or "").strip()
    if quote:
        hero_cell.append(Spacer(1, 0.1 * inch))
        hero_cell.append(_quote_frame(quote, quote_style, pal))

    # Resources column.
    res_cell = _resources_block(f.get("resources") or [],
                                  panel_h, sub_h, bullet, pal)

    main = Table([[hero_cell, res_cell]],
                 colWidths=[3.5 * inch, 3.5 * inch])
    main.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("BOX", (0, 0), (-1, -1), 0.5, HexColor(pal["frame"])),
        ("LINEBETWEEN", (0, 0), (-1, -1), 0.5, HexColor(pal["frame"])),
    ]))
    flow.append(main)
    flow.append(Spacer(1, 0.1 * inch))

    # ── Weakness band ───────────────────────────────────────────
    weakness = f.get("weakness") or {}
    if weakness:
        flow.append(_weakness_band(weakness, band_h, sub_h, bullet, flav_style, pal))
        flow.append(Spacer(1, 0.08 * inch))

    # ── Cost band ───────────────────────────────────────────────
    cost = f.get("cost") or {}
    if cost:
        flow.append(_cost_band(cost, band_h, sub_h, bullet, flav_style, pal))
        flow.append(Spacer(1, 0.08 * inch))

    # ── Who knows footer ────────────────────────────────────────
    who_knows = f.get("who_knows") or []
    if who_knows:
        flow.append(_who_knows_band(who_knows, band_h, sub_h, bullet, pal))

    # ── tags / kind footer ──────────────────────────────────────
    tags = node.get("tags") or []
    if tags:
        flow.append(Spacer(1, 0.08 * inch))
        flow.append(Paragraph(
            "<i>tags:</i> " + ", ".join(_xml(t) for t in tags),
            styles["h_kind"]))

    flow.append(PageBreak())
    return flow


# ── helper composers ────────────────────────────────────────────────
def _kind_subtitle(node: Dict[str, Any]) -> str:
    """Generate a default subtitle from node_kind + creation_tree.section."""
    kind = (node.get("node_kind") or node.get("type") or "").replace("_", " ")
    section = ((node.get("creation_tree") or {}).get("section") or "")
    if kind and section:
        return f"{kind} · {section}"
    return kind or section or "codex entry"


def _ornament_placeholder():
    """Centred ornamental sigil rendered as a Table with a glyph."""
    from reportlab.lib.colors import HexColor
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import inch
    from reportlab.platypus import Paragraph, Table, TableStyle
    sheet = getSampleStyleSheet()
    glyph = ParagraphStyle("Glyph", parent=sheet["Normal"],
                              fontName="Helvetica-Bold", fontSize=84,
                              leading=90,
                              textColor=HexColor(AZAZEL_PALETTE["gold"]),
                              alignment=1)
    sub = ParagraphStyle("OrnSub", parent=sheet["Normal"],
                            fontName="Helvetica-Oblique", fontSize=8,
                            textColor=HexColor(AZAZEL_PALETTE["muted"]),
                            alignment=1)
    cell = [Paragraph("✦", glyph),
            Paragraph("— sigil unmarked —", sub)]
    t = Table([[cell]], colWidths=[3.0 * inch], rowHeights=[3.4 * inch])
    t.setStyle(TableStyle([
        ("BOX", (0, 0), (-1, -1), 0.5, HexColor(AZAZEL_PALETTE["gold_lt"])),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("BACKGROUND", (0, 0), (-1, -1), HexColor(AZAZEL_PALETTE["shade"])),
    ]))
    return t


def _quote_frame(quote: str, style, pal: Dict[str, str]):
    from reportlab.lib.colors import HexColor
    from reportlab.lib.units import inch
    from reportlab.platypus import Paragraph, Table, TableStyle
    para = Paragraph(f"&ldquo; {_xml(quote)} &rdquo;", style)
    t = Table([[para]], colWidths=[3.0 * inch])
    t.setStyle(TableStyle([
        ("BOX", (0, 0), (-1, -1), 0.5, HexColor(pal["accent"])),
        ("BACKGROUND", (0, 0), (-1, -1), HexColor(pal["shade"])),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    return t


def _resources_block(resources: List[Dict[str, Any]],
                      panel_h, sub_h, bullet, pal):
    """Build the 4-row Resources panel (or whatever count was provided).

    Each resource: { title, items[], player_targets[] }
    """
    from reportlab.lib.colors import HexColor
    from reportlab.platypus import Paragraph, Table, TableStyle, Spacer
    from reportlab.lib.units import inch
    rows: List[List[Any]] = []
    rows.append([Paragraph("RESOURCES", panel_h)])
    if not resources:
        rows.append([Paragraph("<i>No structured resources provided.</i>", bullet)])
    else:
        for r in resources:
            t = (r.get("title") or "").upper()
            items = r.get("items") or []
            targets = r.get("player_targets") or []
            inner = Table([[
                _bulletset(t or "—", items, sub_h, bullet),
                _bulletset("PLAYER TARGETS", targets, sub_h, bullet),
            ]], colWidths=[1.7 * inch, 1.5 * inch])
            inner.setStyle(TableStyle([
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 4),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                ("BOX", (0, 0), (-1, -1), 0.4, HexColor(pal["gold_lt"])),
                ("LINEBETWEEN", (0, 0), (-1, -1), 0.3, HexColor(pal["gold_lt"])),
                ("BACKGROUND", (0, 0), (-1, -1), HexColor(pal["shade"])),
            ]))
            rows.append([inner])
            rows.append([Spacer(1, 0.05 * inch)])
    outer = Table(rows, colWidths=[3.4 * inch])
    outer.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
    ]))
    return outer


def _bulletset(title: str, items: List[str], sub_h, bullet):
    from reportlab.platypus import Paragraph
    out: List[Any] = [Paragraph(_xml(title), sub_h)]
    if not items:
        out.append(Paragraph("—", bullet))
    else:
        for it in items:
            out.append(Paragraph(f"♦ {_xml(it)}", bullet))
    return out


def _weakness_band(w: Dict[str, Any], band_h, sub_h, bullet, flav, pal):
    from reportlab.lib.colors import HexColor
    from reportlab.lib.units import inch
    from reportlab.platypus import Paragraph, Table, TableStyle
    title = (w.get("title") or "WEAKNESS").upper()
    desc = w.get("description") or []
    why = w.get("why") or []
    can = w.get("player_can") or []
    flavour = w.get("flavour") or ""

    inner_left  = _bulletset_block("DESCRIPTION", desc, sub_h, bullet, flav, flavour)
    inner_mid   = _bulletset_block("WHY THIS IS A WEAKNESS", why, sub_h, bullet, flav)
    inner_right = _bulletset_block("WHAT PLAYERS CAN DO", can, sub_h, bullet, flav)

    body = Table([[inner_left, inner_mid, inner_right]],
                  colWidths=[2.4 * inch, 2.2 * inch, 2.4 * inch])
    body.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LINEBETWEEN", (0, 0), (-1, -1), 0.4, HexColor(pal["gold_lt"])),
        ("BACKGROUND", (0, 0), (-1, -1), HexColor(pal["shade"])),
    ]))
    head = Table([[Paragraph(title, band_h)]], colWidths=[7.0 * inch])
    head.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), HexColor(pal["shade"])),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    wrap = Table([[head], [body]], colWidths=[7.0 * inch])
    wrap.setStyle(TableStyle([
        ("BOX", (0, 0), (-1, -1), 0.6, HexColor(pal["frame"])),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
    ]))
    return wrap


def _bulletset_block(title: str, items: List[str], sub_h, bullet,
                       flav_style=None, flav_text: Optional[str] = None):
    from reportlab.platypus import Paragraph
    out: List[Any] = [Paragraph(_xml(title), sub_h)]
    if not items:
        out.append(Paragraph("—", bullet))
    else:
        for it in items:
            out.append(Paragraph(f"♦ {_xml(it)}", bullet))
    if flav_text and flav_style is not None:
        out.append(Paragraph(f"<i>{_xml(flav_text)}</i>", flav_style))
    return out


def _cost_band(c: Dict[str, Any], band_h, sub_h, bullet, flav, pal):
    from reportlab.lib.colors import HexColor
    from reportlab.lib.units import inch
    from reportlab.platypus import Paragraph, Table, TableStyle
    title = (c.get("title") or "THE COST").upper()
    body_text = c.get("body") or "—"
    note = c.get("note") or ""
    cons = c.get("consequences") or []

    cost_cell: List[Any] = [Paragraph(_xml(body_text), bullet)]
    if note:
        cost_cell.append(Paragraph(f"<i>{_xml(note)}</i>", flav))
    cons_cell = _bulletset_block("PERMANENT CONSEQUENCE OPTIONS",
                                    cons, sub_h, bullet)

    body = Table([[cost_cell, cons_cell]],
                  colWidths=[3.5 * inch, 3.5 * inch])
    body.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LINEBETWEEN", (0, 0), (-1, -1), 0.4, HexColor(pal["accent"])),
        ("BACKGROUND", (0, 0), (-1, -1), "#F8E5E2"),
    ]))
    head = Table([[Paragraph(title, band_h)]], colWidths=[7.0 * inch])
    head.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), HexColor(pal["accent"])),
        ("TEXTCOLOR", (0, 0), (-1, -1), HexColor(pal["page"])),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    wrap = Table([[head], [body]], colWidths=[7.0 * inch])
    wrap.setStyle(TableStyle([
        ("BOX", (0, 0), (-1, -1), 0.6, HexColor(pal["accent"])),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
    ]))
    return wrap


def _who_knows_band(rows: List[Dict[str, Any]], band_h, sub_h, bullet, pal):
    from reportlab.lib.colors import HexColor
    from reportlab.lib.units import inch
    from reportlab.platypus import Paragraph, Table, TableStyle
    head = Table([[Paragraph("WHO ELSE KNOWS ABOUT IT", band_h)]],
                  colWidths=[7.0 * inch])
    head.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), HexColor(pal["shade"])),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]))
    cells: List[List[Any]] = []
    for r in rows[:5]:
        glyph = r.get("glyph") or "✦"
        name = (r.get("name") or "").upper()
        role = r.get("role") or ""
        cell = [
            Paragraph(f"<font size='14'>{_xml(glyph)}</font>", sub_h),
            Paragraph(_xml(name), sub_h),
            Paragraph(f"<i>{_xml(role)}</i>", bullet),
        ]
        cells.append(cell)
    while len(cells) < 5:
        cells.append([Paragraph("—", bullet)])
    body = Table([cells], colWidths=[1.4 * inch] * 5)
    body.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LINEBETWEEN", (0, 0), (-1, -1), 0.3, HexColor(pal["gold_lt"])),
        ("BACKGROUND", (0, 0), (-1, -1), HexColor(pal["shade"])),
    ]))
    wrap = Table([[head], [body]], colWidths=[7.0 * inch])
    wrap.setStyle(TableStyle([
        ("BOX", (0, 0), (-1, -1), 0.6, HexColor(pal["frame"])),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
    ]))
    return wrap
