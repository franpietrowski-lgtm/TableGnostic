"""V6.6 — Mobile-optimised character-sheet PDF export.

Phone-portrait single-column layout, styled to mirror each system's
core-rulebook character sheet:

  * BESM 4E   — Tri-Stat block style (Body/Mind/Soul + Attributes grid)
  * Anime 5E  — D&D chassis summary + Anime 5E point-buy supplement
  * D&D 5E    — Ability scores / saves / skills column + spell-slot row
  * Cypher    — Might/Speed/Intellect pool-column + cyphers list

Endpoint: `GET /api/characters/{cid}/export.pdf?mode=mobile`
Falls back to `mode=desktop` which renders a classic letter-portrait.

Keeps the existing campaign-level PDF export untouched; this is a
character-scope surface for handing a printable reference to a player
mid-session.
"""
from __future__ import annotations

import io
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse

from core.db import db
from core.security import get_current_user
from routes.pdf_export import STYLE_PROFILES, _profile_for


router = APIRouter(prefix="/api", tags=["pdf"])


def _build_mobile_sheet(ch: Dict[str, Any], camp: Dict[str, Any]) -> bytes:
    """Render a phone-portrait 1-column character sheet PDF."""
    from reportlab.lib.pagesizes import A6  # 4.13 × 5.83 in — phone-portrait approx
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.lib.colors import HexColor
    from reportlab.lib.enums import TA_LEFT, TA_CENTER
    from reportlab.platypus import (
        BaseDocTemplate, Frame, PageTemplate,
        Paragraph, Spacer, KeepTogether, HRFlowable, Table, TableStyle,
    )

    profile = _profile_for(camp.get("system_id"))
    p = profile["palette"]
    f = profile["fonts"]
    primary = HexColor(p["primary"])
    ink = HexColor(p["ink"])
    muted = HexColor(p["muted"])
    rule = HexColor(p["rule"])
    pw, ph = A6
    margin = 0.25 * inch

    # Frame + page chrome.
    frame = Frame(margin, margin + 0.25 * inch, pw - 2 * margin,
                   ph - 2 * margin - 0.45 * inch,
                   leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0,
                   id="sheet")

    def chrome(canv, doc):
        # Top band with character name, system chip.
        canv.saveState()
        canv.setFillColor(primary)
        canv.rect(0, ph - 0.3 * inch, pw, 0.3 * inch, fill=1, stroke=0)
        canv.setFillColor(HexColor("#FFFFFF"))
        canv.setFont(f["heading"], 10)
        canv.drawString(margin, ph - 0.2 * inch, (ch.get("name") or "—")[:30])
        canv.setFont(f["subheading"], 7)
        canv.drawRightString(pw - margin, ph - 0.2 * inch,
                              profile["name"].upper())
        # Footer rule + page number.
        canv.setStrokeColor(rule)
        canv.setLineWidth(0.4)
        canv.line(margin, 0.25 * inch, pw - margin, 0.25 * inch)
        canv.setFillColor(muted)
        canv.setFont(f["body"], 6)
        canv.drawCentredString(pw / 2, 0.12 * inch,
                                f"TableGnostic · {camp.get('name', '')[:40]}  ·  p. {doc.page}")
        canv.restoreState()

    buf = io.BytesIO()
    doc = BaseDocTemplate(buf, pagesize=A6,
                          leftMargin=margin, rightMargin=margin,
                          topMargin=margin, bottomMargin=margin,
                          title=f"{ch.get('name','Character')} — sheet",
                          author=ch.get("owner_name") or "Player")
    doc.addPageTemplates([PageTemplate(id="sheet", frames=[frame], onPage=chrome)])

    h1 = ParagraphStyle("h1", fontName=f["heading"], fontSize=9,
                        textColor=primary, spaceBefore=4, spaceAfter=2,
                        leading=11)
    body = ParagraphStyle("body", fontName=f["body"], fontSize=7,
                          textColor=ink, leading=9, alignment=TA_LEFT)

    story = []
    sys_id = camp.get("system_id")
    folio = ch.get("folio") or {}

    # Identity strip (every system).
    story.append(Paragraph(ch.get("concept") or "—", body))
    story.append(HRFlowable(width="100%", thickness=0.4, color=rule,
                              spaceBefore=2, spaceAfter=2))

    def mini_table(rows, col_widths=None):
        tbl = Table(rows, colWidths=col_widths)
        tbl.setStyle(TableStyle([
            ("FONT", (0, 0), (-1, -1), f["body"], 7),
            ("TEXTCOLOR", (0, 0), (-1, -1), ink),
            ("BOX", (0, 0), (-1, -1), 0.3, rule),
            ("INNERGRID", (0, 0), (-1, -1), 0.2, rule),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("BACKGROUND", (0, 0), (-1, 0), HexColor(p["callout_bg"])),
        ]))
        return tbl

    # ─── BESM 4E: Stats + Attributes + Defects grid ───
    if sys_id == "besm-4e":
        stats = ch.get("stats") or {}
        story.append(Paragraph("STATS", h1))
        story.append(mini_table([
            ["Body", "Mind", "Soul"],
            [str(stats.get("body", 4)), str(stats.get("mind", 4)), str(stats.get("soul", 4))],
        ]))
        story.append(Spacer(1, 4))
        attrs = ch.get("attributes") or []
        if attrs:
            story.append(Paragraph("ATTRIBUTES", h1))
            rows = [["Attribute", "Lvl", "CPL"]]
            for a in attrs[:20]:
                rows.append([(a.get("display_name") or a.get("name") or "—")[:18],
                             str(a.get("level") or 1), str(a.get("cost_per_level") or 0)])
            story.append(mini_table(rows, col_widths=[pw * 0.55, pw * 0.12, pw * 0.15]))
            story.append(Spacer(1, 4))
        defects = ch.get("defects") or []
        if defects:
            story.append(Paragraph("DEFECTS", h1))
            rows = [["Defect", "Rank", "Refund"]]
            for d in defects[:10]:
                rows.append([(d.get("display_name") or d.get("name") or "—")[:18],
                             str(d.get("rank") or 1),
                             str((d.get("points_per_rank") or 1) * (d.get("rank") or 1))])
            story.append(mini_table(rows, col_widths=[pw * 0.55, pw * 0.15, pw * 0.15]))
    # ─── D&D 5E / Anime 5E: chassis column ───
    elif sys_id in ("dnd-5e", "anime-5e"):
        d = folio.get("dnd_state") or {}
        story.append(Paragraph(
            f"{d.get('class','?')} {d.get('level','?')} · {d.get('race','?')}", body))
        abilities = d.get("abilities") or {}
        if abilities:
            story.append(Paragraph("ABILITIES", h1))
            story.append(mini_table([
                list(abilities.keys()),
                [str(v) for v in abilities.values()],
            ]))
            story.append(Spacer(1, 4))
        if d.get("ac") or d.get("hp_max"):
            story.append(Paragraph("COMBAT", h1))
            rows = [["AC", "HP", "Init"],
                    [str(d.get("ac", 10)), str(d.get("hp_max", 10)),
                     str(d.get("initiative", 0))]]
            story.append(mini_table(rows))
            story.append(Spacer(1, 4))
        slots = d.get("spell_slots") or {}
        if slots:
            story.append(Paragraph("SPELL SLOTS", h1))
            slot_rows = [["Lvl", "Max", "Used"]]
            for k, v in slots.items():
                slot_rows.append([str(k), str(v.get("max", v) if isinstance(v, dict) else v),
                                   str(v.get("used", 0) if isinstance(v, dict) else 0)])
            story.append(mini_table(slot_rows,
                                     col_widths=[pw * 0.25, pw * 0.3, pw * 0.3]))
            story.append(Spacer(1, 4))
        # Anime 5E hybrid supplement (optional).
        if sys_id == "anime-5e":
            anime_state = folio.get("anime5e_state") or {}
            buys = anime_state.get("point_buys") or []
            if buys:
                story.append(Paragraph("BESM POINT-BUY LAYER", h1))
                rows = [["Name", "Lvl", "Pts"]]
                for b in buys[:12]:
                    rows.append([(b.get("name") or "—")[:20],
                                 str(b.get("level") or 1),
                                 str(int((b.get("cost_per_level") or 0) * (b.get("level") or 1)))])
                story.append(mini_table(rows,
                                         col_widths=[pw * 0.55, pw * 0.15, pw * 0.15]))
    # ─── Cypher: pool column + cyphers ───
    elif sys_id == "cypher":
        c = folio.get("cypher_state") or {}
        story.append(Paragraph(
            f"{c.get('descriptor','?')} {c.get('type','?')} who "
            f"{c.get('focus','?')} · Tier {c.get('tier', 1)}", body))
        pools = c.get("pools") or {}
        edge = c.get("edge") or {}
        if pools:
            story.append(Paragraph("POOLS / EDGE", h1))
            story.append(mini_table([
                ["", "Might", "Speed", "Intellect"],
                ["Pool", str(pools.get("Might", 0)),
                         str(pools.get("Speed", 0)),
                         str(pools.get("Intellect", 0))],
                ["Edge", str(edge.get("Might", 0)),
                         str(edge.get("Speed", 0)),
                         str(edge.get("Intellect", 0))],
            ]))
            story.append(Spacer(1, 4))
        cyphers = c.get("cyphers_held") or []
        if cyphers:
            story.append(Paragraph(f"CYPHERS ({len(cyphers)}/{c.get('cypher_limit', 2)})", h1))
            rows = [["Cypher", "Lvl"]]
            for cy in cyphers[:10]:
                rows.append([(cy.get("name") or "—")[:22], str(cy.get("level") or "—")])
            story.append(mini_table(rows, col_widths=[pw * 0.7, pw * 0.2]))

    # Notes at the bottom (truncated for mobile).
    if ch.get("notes"):
        story.append(Paragraph("NOTES", h1))
        story.append(Paragraph(ch["notes"][:400], body))

    doc.build(story)
    return buf.getvalue()


@router.get("/characters/{cid}/export.pdf")
async def export_character_sheet_pdf(
    cid: str, mode: str = "mobile",
    user: dict = Depends(get_current_user),
):
    """Download a phone-portrait (A6) character-sheet PDF.

    * `mode=mobile`  — phone-optimised 1-column, styled by campaign system.
    * `mode=desktop` — currently same layout (will diverge in a future sprint).
    """
    ch = await db.characters.find_one({"id": cid}, {"_id": 0})
    if not ch:
        raise HTTPException(404, "Character not found")
    camp = await db.campaigns.find_one({"id": ch["campaign_id"]}, {"_id": 0})
    if not camp:
        raise HTTPException(404, "Campaign not found")
    allowed = (
        user["id"] == ch.get("owner_id")
        or user["id"] == camp["gm_id"]
        or user["id"] in (camp.get("member_ids") or [])
        or user.get("role") == "admin"
    )
    if not allowed:
        raise HTTPException(403, "Not a table member.")
    data = _build_mobile_sheet(ch, camp)
    raw_name = (ch.get("name") or "character").replace("/", "-").replace(" ", "_")
    safe_name = "".join(
        c if ord(c) < 128 and c not in '"\\' else "_" for c in raw_name
    ).strip("_") or "character"
    return StreamingResponse(
        io.BytesIO(data),
        media_type="application/pdf",
        headers={
            "Content-Disposition":
                f'attachment; filename="{safe_name}-sheet-{mode}.pdf"',
        },
    )
