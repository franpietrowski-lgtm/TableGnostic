"""V6.25.51 — Macro grammar resolver.

Extracted from routes/channels.py to keep that file focused on the
chat/spend/undo pipeline. This module owns one public function —
`expand_macro_tokens(formula, char)` — which substitutes a typed
token grammar into raw dice-string formulas using LIVE character
data (sheet, not SRD reference).

Token grammar:

  Stat / ability scalars (legacy, case-insensitive):
    STR DEX CON INT WIS CHA  → D&D ability MOD (signed)
    BODY MIND SOUL           → BESM stat value
    PROF                     → D&D proficiency
    LVL                      → character level

  Typed tokens (V6.25.9+):
    {attr:<Name>}    → effective level of the matching Attribute
                       (Σlimiter.rank − Σenhancement.rank applied).
    {skill:<Name>}   → assigned level of the matching Skill.
    {def:<Name>}     → rank of the matching Defect.
    {stat:body|mind|soul|str|dex|con|int|wis|cha|might|speed|intellect}
                     → raw stat / ability score / Cypher pool value.
    {derived:hp|ep|atk|dfn|cv|dm|ac|init|edge_*|effort|tier}
                     → the named BESM / D&D / Cypher derived value.
    {hp}, {ep}, {sanity}
                     → current resource pool (folio.dnd_state.* or
                       BESM-derived fallback).

Unknown tokens collapse to 0 with a leading '+' so the formula stays
syntactically valid for the dice engine.
"""
from __future__ import annotations
import re


# ── module-level regexes (compile once) ──
_TYPED_PAT = re.compile(
    r"\{(?P<kind>attr|skill|def|stat|derived)\s*:\s*(?P<name>[^}]+)\}",
    re.IGNORECASE,
)
_SHORT_PAT = re.compile(r"\{(hp|ep|sanity)\}", re.IGNORECASE)
_SCALAR_PAT = re.compile(
    r"(?<![A-Za-z0-9_])(STR|DEX|CON|INT|WIS|CHA|BODY|MIND|SOUL|PROF|LVL)(?![A-Za-z0-9_])",
    re.IGNORECASE,
)


def _mod_of(score) -> int:
    try:
        return (int(score) - 10) // 2
    except (TypeError, ValueError):
        return 0


def _mod_rank(m) -> int:
    """Limiter / enhancement rank — defaults to 1 unless explicitly typed."""
    if isinstance(m, str):
        return 1
    if isinstance(m, dict):
        if isinstance(m.get("rank"), (int, float)):
            return max(1, int(m["rank"]))
        if isinstance(m.get("value"), (int, float)):
            return max(1, abs(int(m["value"])))
    return 1


def _attr_eff(attr) -> int:
    """Effective Attribute level = base + Σlimiters − Σenhancements,
    floored at 1. Honours an explicit `effective_level` if the
    validator wrote one (so cached values aren't silently overridden)."""
    if not attr:
        return 0
    if isinstance(attr.get("effective_level"), int):
        return max(1, attr["effective_level"])
    base = int(attr.get("level") or 1)
    lim = sum(_mod_rank(m) for m in (attr.get("limiters") or []))
    enh = sum(_mod_rank(m) for m in (attr.get("enhancements") or []))
    return max(1, base + lim - enh)


def _by_name(rows, name):
    """Case-insensitive name lookup across an attribute / skill /
    defect list. Returns the first match or None."""
    n = (name or "").strip().lower()
    for r in (rows or []):
        rn = (r.get("name") or r.get("group") or "").strip().lower()
        if rn == n:
            return r
    return None


def expand_macro_tokens(formula: str, char) -> str:
    """Substitute every recognised token in `formula` with its live
    value from `char`. Safe to call with falsy inputs — returns the
    original formula unchanged."""
    if not char or not formula:
        return formula

    folio = (char.get("folio") or {})
    dnd_state = (folio.get("dnd_state") or {})
    abilities = (dnd_state.get("ability_scores") or {})
    stats = (char.get("stats") or {})
    lvl = int(dnd_state.get("level") or char.get("level") or 1)
    prof = max(2, 2 + (lvl - 1) // 4)

    body = int(stats.get("body") or 0)
    mind = int(stats.get("mind") or 0)
    soul = int(stats.get("soul") or 0)
    cv = (body + mind + soul) // 3 if (body + mind + soul) else 0

    # V6.25.36 — Anime 5E hybrid point-buy rows.
    pb_rows = ((folio.get("anime5e_state") or {}).get("point_buys") or [])
    # V6.25.36 — Cypher sheet state.
    cyp_state = folio.get("cypher_state") or {}
    cyp_pools = cyp_state.get("pools") or {}
    cyp_edges = cyp_state.get("edges") or {}

    def _attr_lvl(name):
        a = _by_name(char.get("attributes"), name) or _by_name(pb_rows, name)
        return int(a.get("level") or 0) if a else 0

    derived = {
        "cv":   cv,
        "atk":  cv + _attr_lvl("Attack Mastery"),
        "dfn":  max(0, cv - 2 + _attr_lvl("Defence Mastery")),
        "hp":   (body + soul) * 5 + _attr_lvl("Tough") * 5,
        "ep":   (mind + soul) * 5 + _attr_lvl("Energised") * 5,
        "dm":   5 + _attr_lvl("Massive Damage") * 5,
        "ac":   int(dnd_state.get("ac") or 10),
        "init": _mod_of(abilities.get("Dexterity")),
        # Cypher derived.
        "edge_might":     int(cyp_edges.get("Might") or 0),
        "edge_speed":     int(cyp_edges.get("Speed") or 0),
        "edge_intellect": int(cyp_edges.get("Intellect") or 0),
        "effort":         int(cyp_state.get("effort") or 1),
        "tier":           int(cyp_state.get("tier") or 1),
    }

    scalar_tokens = {
        "STR": _mod_of(abilities.get("Strength")),
        "DEX": _mod_of(abilities.get("Dexterity")),
        "CON": _mod_of(abilities.get("Constitution")),
        "INT": _mod_of(abilities.get("Intelligence")),
        "WIS": _mod_of(abilities.get("Wisdom")),
        "CHA": _mod_of(abilities.get("Charisma")),
        "BODY": body, "MIND": mind, "SOUL": soul,
        "PROF": prof, "LVL": lvl,
    }

    # Typed tokens come first so `{stat:body}` resolves before the
    # bare BODY scalar pattern can shadow it.
    def repl_typed(m):
        kind = (m.group("kind") or "").lower()
        name = (m.group("name") or "").strip()
        v = 0
        try:
            if kind == "attr":
                a = _by_name(char.get("attributes"), name) or _by_name(pb_rows, name)
                v = _attr_eff(a)
            elif kind == "skill":
                s = _by_name(char.get("skills"), name)
                v = int(s.get("level") or 0) if s else 0
            elif kind == "def":
                d = _by_name(char.get("defects"), name)
                v = int(d.get("rank") or 0) if d else 0
            elif kind == "stat":
                key = name.lower()
                if key in ("body", "mind", "soul"):
                    v = scalar_tokens.get(key.upper(), 0)
                elif key in ("str", "dex", "con", "int", "wis", "cha"):
                    v = _mod_of(abilities.get({
                        "str": "Strength", "dex": "Dexterity", "con": "Constitution",
                        "int": "Intelligence", "wis": "Wisdom", "cha": "Charisma",
                    }.get(key)))
                elif key in ("might", "speed", "intellect"):
                    v = int(cyp_pools.get(key.title()) or 0)
            elif kind == "derived":
                v = int(derived.get(name.lower(), 0))
            elif kind == "hp":
                v = derived["hp"]
        except (TypeError, ValueError):
            v = 0
        return f"+{v}" if v >= 0 else str(v)

    def repl_short(m):
        key = (m.group(1) or "").lower()
        if key == "hp":
            v = derived["hp"]
        elif key == "ep":
            v = derived["ep"]
        elif key == "sanity":
            v = int((dnd_state.get("sanity") or 0))
        else:
            v = 0
        return f"+{v}" if v >= 0 else str(v)

    def repl_scalar(m):
        key = m.group(0).upper()
        v = scalar_tokens.get(key, 0)
        return f"+{v}" if v >= 0 else str(v)

    out = _TYPED_PAT.sub(repl_typed, formula)
    out = _SHORT_PAT.sub(repl_short, out)
    out = _SCALAR_PAT.sub(repl_scalar, out)
    # Clean up sign sandwiches introduced by chained subs.
    out = re.sub(r"\+\+", "+", out)
    out = re.sub(r"\+-", "-", out)
    out = re.sub(r"--", "+", out)
    return out
