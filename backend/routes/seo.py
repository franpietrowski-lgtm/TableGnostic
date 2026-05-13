"""V6.25.41 — SEO infrastructure (sitemap, robots, OG images).

Public endpoints (no auth, served at root paths via path-rewrite-friendly
prefixes so ingress can route them):

  GET  /api/seo/sitemap.xml      — XML sitemap (cached 1h in-process)
  GET  /api/seo/robots.txt       — robots.txt
  GET  /api/seo/og/{slug}.svg    — Open-Graph card SVG for a showcase
                                    (server-rendered, no fonts needed —
                                    1200×630 spec)

Routing convention: the React frontend serves `/sitemap.xml` and
`/robots.txt` as static rewrites to these API paths (see
`frontend/public/_redirects`).
"""
from datetime import datetime, timezone, timedelta
from typing import Optional
from xml.sax.saxutils import escape as xml_escape

from fastapi import APIRouter, Response, HTTPException

from core.db import db


router = APIRouter(prefix="/api", tags=["seo"])

PUBLIC_BASE_URL = "https://tablegnostic.com"


# Tiny in-process cache (TTL 1h). The sitemap walks the campaign +
# news_issues collections so we don't want to re-query on every crawl.
_sitemap_cache: dict = {"at": None, "body": ""}


@router.get("/seo/robots.txt", include_in_schema=False)
async def robots_txt() -> Response:
    body = (
        "User-agent: *\n"
        "Allow: /\n"
        "Allow: /discover\n"
        "Allow: /landing\n"
        "Disallow: /app\n"
        "Disallow: /api/admin\n"
        "Disallow: /api/auth\n"
        f"Sitemap: {PUBLIC_BASE_URL}/sitemap.xml\n"
    )
    return Response(content=body, media_type="text/plain")


@router.get("/seo/sitemap.xml", include_in_schema=False)
async def sitemap_xml() -> Response:
    """Build a fresh sitemap (cached for 1h). Includes the marketing
    routes + every `discover_published` campaign's showcase + its
    gazette. Issue-level pages are NOT enumerated to keep the file
    crawl-friendly — they're reachable through the campaign showcase."""
    now = datetime.now(timezone.utc)
    if (_sitemap_cache["at"]
            and (now - _sitemap_cache["at"]) < timedelta(hours=1)
            and _sitemap_cache["body"]):
        return Response(content=_sitemap_cache["body"], media_type="application/xml")

    urls: list = [
        (f"{PUBLIC_BASE_URL}/", "1.0", "weekly"),
        (f"{PUBLIC_BASE_URL}/landing", "0.9", "weekly"),
        (f"{PUBLIC_BASE_URL}/discover", "0.9", "daily"),
        (f"{PUBLIC_BASE_URL}/discover/browse", "0.9", "daily"),
    ]

    pubs = await db.campaigns.find(
        {"discover_published": True},
        {"_id": 0, "discover_slug": 1, "updated_at": 1, "created_at": 1},
    ).to_list(2000)
    for c in pubs:
        slug = c.get("discover_slug")
        if not slug:
            continue
        last = c.get("updated_at") or c.get("created_at") or ""
        urls.append((f"{PUBLIC_BASE_URL}/discover/{slug}", "0.8", "weekly", last))
        urls.append((f"{PUBLIC_BASE_URL}/discover/{slug}/gazette", "0.7", "weekly", last))

    rows: list = []
    rows.append('<?xml version="1.0" encoding="UTF-8"?>')
    rows.append('<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">')
    for u in urls:
        loc, prio, freq = u[0], u[1], u[2]
        rows.append("  <url>")
        rows.append(f"    <loc>{xml_escape(loc)}</loc>")
        if len(u) > 3 and u[3]:
            iso = (u[3] or "")[:10]
            rows.append(f"    <lastmod>{iso}</lastmod>")
        rows.append(f"    <changefreq>{freq}</changefreq>")
        rows.append(f"    <priority>{prio}</priority>")
        rows.append("  </url>")
    rows.append("</urlset>")
    body = "\n".join(rows)

    _sitemap_cache["at"] = now
    _sitemap_cache["body"] = body
    return Response(content=body, media_type="application/xml")


@router.get("/seo/og/{slug}.svg", include_in_schema=False)
async def og_card_svg(slug: str) -> Response:
    """Open-Graph card for a campaign showcase. SVG (1200×630 per Twitter
    + FB spec). No web-font dependency — uses generic-family serif + sans
    so the platform crawler renders it identically.

    Most crawlers prefer PNG/JPG, but every major one (FB, Twitter, LinkedIn,
    Discord, Slack) handles SVG via `og:image` as of 2025.
    """
    camp = await db.campaigns.find_one(
        {"discover_slug": slug, "discover_published": True},
        {"_id": 0, "name": 1, "system_id": 1, "gm_name": 1, "canon_blurb": 1, "featured": 1},
    )
    if not camp:
        raise HTTPException(404, "Showcase not found.")

    name = (camp.get("name") or "TableGnostic Showcase")[:80]
    system = (camp.get("system_id") or "").upper()
    gm = (camp.get("gm_name") or "")[:60]
    blurb = (camp.get("canon_blurb") or "")[:200]
    featured = bool(camp.get("featured"))

    def e(s: str) -> str:
        return xml_escape(s)

    # 1200x630 — golden ratio masthead band, body block, footer GM strip.
    svg = f'''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="630" viewBox="0 0 1200 630">
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="#0b0810"/>
      <stop offset="1" stop-color="#1c1208"/>
    </linearGradient>
    <linearGradient id="gold" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0" stop-color="#d4af37"/>
      <stop offset="1" stop-color="#f3d36b"/>
    </linearGradient>
  </defs>
  <rect width="1200" height="630" fill="url(#bg)"/>
  <rect x="40" y="40" width="1120" height="550" fill="none" stroke="url(#gold)" stroke-width="2"/>
  <rect x="60" y="60" width="1080" height="6" fill="url(#gold)"/>
  <rect x="60" y="564" width="1080" height="6" fill="url(#gold)"/>
  <text x="80" y="110" fill="#d4af37" font-family="serif" font-size="22" letter-spacing="6">
    TABLE-GNOSTIC{('  ·  FEATURED' if featured else '')}
  </text>
  <text x="80" y="150" fill="#9a8f80" font-family="serif" font-size="18" letter-spacing="3">
    {e(system)}  ·  GM {e(gm)}
  </text>
  <text x="80" y="270" fill="#f4ecd4" font-family="serif" font-size="64" font-weight="700" letter-spacing="-1">
    <tspan>{e(name[:38])}</tspan>
  </text>
  {('<text x="80" y="330" fill="#f4ecd4" font-family="serif" font-size="56" font-weight="700">' + e(name[38:76]) + '</text>') if len(name) > 38 else ''}
  <text x="80" y="410" fill="#c2b9a8" font-family="serif" font-size="26" font-style="italic">
    {e(blurb[:70])}
  </text>
  {('<text x="80" y="448" fill="#c2b9a8" font-family="serif" font-size="26" font-style="italic">' + e(blurb[70:140]) + '</text>') if len(blurb) > 70 else ''}
  <text x="80" y="540" fill="#9a8f80" font-family="serif" font-size="16" letter-spacing="3">
    NOT THE SYSTEM.  ·  THE TABLE.
  </text>
  <text x="1120" y="540" fill="#9a8f80" font-family="serif" font-size="14" letter-spacing="2" text-anchor="end">
    tablegnostic.com/discover/{e(slug[:48])}
  </text>
</svg>'''
    return Response(content=svg, media_type="image/svg+xml")
