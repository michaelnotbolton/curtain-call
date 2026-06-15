#!/usr/bin/env python3
"""
Curtain Call — Dallas show scraper
Fetches shows from Dallas-area theater websites and outputs public/data/shows-dallas.json

Extraction pipeline (in order, first success wins):
  1. schema.org JSON-LD  — free, near-perfect where it exists
  2. CSS pattern heuristics — common WordPress/Squarespace theater templates
  3. Ollama local model   — fallback for unstructured pages (requires Ollama running)

Usage:
  python3 scraper/scrape.py            # full run
  python3 scraper/scrape.py --dry-run  # print venues, don't fetch
  python3 scraper/scrape.py --venue "Kitchen Dog Theater"  # single venue
"""

import json
import re
import sys
import time
import logging
import argparse
from datetime import datetime
from pathlib import Path
from typing import Optional
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

# Allow running as `python3 scraper/scrape.py` or `python3 -m scraper.scrape`
sys.path.insert(0, str(Path(__file__).parent))
from venues_dallas import VENUES

# ── Configuration ────────────────────────────────────────────────────────────

OLLAMA_MODEL = "qwen2.5:7b"
OLLAMA_URL = "http://localhost:11434/api/generate"
REQUEST_DELAY = 2.5  # seconds between requests (be a good citizen)
REQUEST_TIMEOUT = 15
OUTPUT_FILE = Path(__file__).parent.parent / "public" / "data" / "shows-dallas.json"
CITY = "Dallas"

HEADERS = {
    "User-Agent": (
        "CurtainCall/0.1 (theater show indexer for audience discovery; "
        "contact michaelnotbolton@gmail.com)"
    ),
    "Accept": "text/html,application/xhtml+xml",
    "Accept-Language": "en-US,en;q=0.9",
}

log = logging.getLogger(__name__)


# ── Fetching ─────────────────────────────────────────────────────────────────

def fetch_page(url: str) -> Optional[str]:
    try:
        resp = requests.get(url, headers=HEADERS, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        return resp.text
    except requests.exceptions.HTTPError as e:
        log.warning(f"HTTP {e.response.status_code} fetching {url}")
    except requests.exceptions.ConnectionError:
        log.warning(f"Connection error fetching {url}")
    except requests.exceptions.Timeout:
        log.warning(f"Timeout fetching {url}")
    except Exception as e:
        log.warning(f"Error fetching {url}: {e}")
    return None


# ── Extraction: schema.org JSON-LD ───────────────────────────────────────────

def extract_schema_org(html: str, venue: dict) -> list[dict]:
    soup = BeautifulSoup(html, "html.parser")
    shows = []

    for tag in soup.find_all("script", type="application/ld+json"):
        try:
            data = json.loads(tag.string or "")
        except (json.JSONDecodeError, TypeError):
            continue

        # Handle both single object and @graph array
        items = data if isinstance(data, list) else data.get("@graph", [data])

        for item in items:
            type_ = item.get("@type", "")
            if type_ not in ("Event", "TheaterEvent", "MusicEvent", "SocialEvent",
                              "EntertainmentEvent"):
                continue

            show = _parse_schema_event(item, venue["url"])
            if show and show.get("title"):
                shows.append(show)

    return shows


def _parse_schema_event(item: dict, base_url: str) -> Optional[dict]:
    name = item.get("name", "").strip()
    if not name:
        return None

    start = item.get("startDate", "")
    end = item.get("endDate", "")

    location = item.get("location", {})
    if isinstance(location, list):
        location = location[0] if location else {}

    url = item.get("url", "") or item.get("offers", {}).get("url", "")
    if url and not url.startswith("http"):
        url = urljoin(base_url, url)

    return {
        "title": name,
        "playwright": None,  # schema.org rarely includes this
        "director": _coerce_str(item.get("director")),
        "start_date": _parse_date(start),
        "end_date": _parse_date(end),
        "showtimes": None,
        "ticket_url": url or None,
        "description": (item.get("description", "") or "")[:300] or None,
    }


def _coerce_str(val) -> Optional[str]:
    if not val:
        return None
    if isinstance(val, str):
        return val.strip() or None
    if isinstance(val, dict):
        return (val.get("name", "") or "").strip() or None
    if isinstance(val, list) and val:
        return _coerce_str(val[0])
    return None


def _parse_date(val: str) -> Optional[str]:
    if not val:
        return None
    # Extract YYYY-MM-DD from ISO strings like 2026-06-15T19:30:00
    m = re.match(r"(\d{4}-\d{2}-\d{2})", val)
    return m.group(1) if m else None


# ── Extraction: CSS heuristics ───────────────────────────────────────────────

# Common class/id patterns used by The Events Calendar (WordPress), Squarespace,
# and hand-coded theater sites.
TITLE_SELECTORS = [
    ".tribe-events-list-event-title",
    ".event-title",
    ".show-title",
    ".production-title",
    "h2.tribe-event-title",
    "article h2",
    "article h3",
    ".entry-title",
    "[class*='show'] h2",
    "[class*='production'] h2",
    "[class*='event'] h2",
]

DATE_SELECTORS = [
    ".tribe-events-schedule",
    ".tribe-event-date-start",
    ".event-date",
    ".show-dates",
    ".run-dates",
    ".performance-dates",
    "[class*='date']",
    "time",
]

TICKET_SELECTORS = [
    "a.tribe-event-url",
    "a[href*='ticket']",
    "a[href*='order']",
    "a[href*='buy']",
    "a.buy-tickets",
    "a.ticket-link",
    ".tribe-events-cal-links a",
]

PLAYWRIGHT_SELECTORS = [
    ".playwright",
    ".by-line",
    ".written-by",
    "[class*='playwright']",
    "[class*='author']",
]


_NOISE_PHRASES = re.compile(
    r"subscribe|mailing list|support our|our mission|our story|equity.{0,5}diversity"
    r"|summer camp|pagination|season ticket|donate|membership|contact us|about us"
    r"|upcoming shows?[\s!]*$|past shows?[\s!]*$|current season[\s!]*$|next season[\s!]*$"
    r"|newsletter|gift card|ticket package|volunteer|internship|audition|youth program"
    r"|follow us|social media|copyright|all rights|privacy policy"
    r"|anniversary season|mainstage season|announcing\s|join us\b|up next"
    r"|there is always|birthday party for|honoring legacy|living our"
    r"|news\s*$|season!$|\d+(st|nd|rd|th)\s+season"
    r"|for a great .{1,10} season|first tuesdays?$|upcoming.*shows?\s+in",
    re.IGNORECASE,
)
_DATE_ONLY = re.compile(
    r"^(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\w*\s+\d",
    re.IGNORECASE,
)
_DATE_RANGE = re.compile(
    r"^(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec|\d{1,2})[^a-z]*"
    r"(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec|\d{4})",
    re.IGNORECASE,
)
_PLAYWRIGHT_ATTR = re.compile(r"^by\s+[A-Z]", re.IGNORECASE)
_NAV_SINGLE_WORD = re.compile(
    r"^(community|events?|tickets?|home|about|news|season|subscribe|donate|shop)$",
    re.IGNORECASE,
)


def _is_likely_show_title(text: str) -> bool:
    """Return False for nav headings, org boilerplate, and attribution strings."""
    if not text or len(text) < 4 or len(text) > 100:
        return False
    if _NOISE_PHRASES.search(text):
        return False
    if _DATE_ONLY.match(text) or _DATE_RANGE.match(text):
        return False
    if _PLAYWRIGHT_ATTR.match(text):
        return False
    if _NAV_SINGLE_WORD.match(text.strip()):
        return False
    return True


def extract_css_patterns(html: str, venue: dict) -> list[dict]:
    soup = BeautifulSoup(html, "html.parser")
    shows = []

    # Try The Events Calendar structure first (most common on theater WP sites)
    articles = soup.find_all("article", class_=re.compile(r"tribe_events|tribe-event"))
    if not articles:
        articles = soup.find_all("article", class_=re.compile(r"event|show|production"))

    if articles:
        for art in articles:
            show = _extract_from_article(art, venue["url"])
            if show:
                show["title"] = _split_concat_date(show["title"])
                if _is_likely_show_title(show["title"]):
                    shows.append(show)
        return shows

    # Fallback: look for title-like elements and pair with nearby dates
    titles = _find_by_selectors(soup, TITLE_SELECTORS)
    for title_el in titles[:20]:  # cap at 20 to avoid grabbing nav links
        text = _split_concat_date(title_el.get_text(strip=True))
        if not _is_likely_show_title(text):
            continue

        # Look for a nearby date
        parent = title_el.parent
        date_text = None
        for sel in DATE_SELECTORS:
            date_el = parent.select_one(sel)
            if date_el:
                date_text = date_el.get_text(strip=True)
                break

        ticket_url = None
        for sel in TICKET_SELECTORS:
            a = parent.select_one(sel)
            if a and a.get("href"):
                href = a["href"]
                ticket_url = href if href.startswith("http") else urljoin(venue["url"], href)
                break

        shows.append({
            "title": text,
            "playwright": None,
            "director": None,
            "start_date": None,
            "end_date": None,
            "showtimes": date_text,
            "ticket_url": ticket_url,
            "description": None,
        })

    return shows


def _extract_from_article(art, base_url: str) -> Optional[dict]:
    title_el = _find_by_selectors(art, TITLE_SELECTORS)
    if not title_el:
        return None
    title_el = title_el[0] if isinstance(title_el, list) else title_el
    title = title_el.get_text(strip=True)
    if not title:
        return None

    date_text = None
    for sel in DATE_SELECTORS:
        el = art.select_one(sel)
        if el:
            date_text = el.get_text(" ", strip=True)
            break

    playwright_text = None
    for sel in PLAYWRIGHT_SELECTORS:
        el = art.select_one(sel)
        if el:
            playwright_text = el.get_text(strip=True) or None
            break

    ticket_url = None
    for sel in TICKET_SELECTORS:
        el = art.select_one(sel)
        if el and el.get("href"):
            href = el["href"]
            ticket_url = href if href.startswith("http") else urljoin(base_url, href)
            break

    return {
        "title": title,
        "playwright": playwright_text,
        "director": None,
        "start_date": None,
        "end_date": None,
        "showtimes": date_text,
        "ticket_url": ticket_url,
        "description": None,
    }


_CONCAT_DATE = re.compile(
    r"([A-Za-z])(January|February|March|April|May|June|July|August|September|October|November|December)\b"
)


def _split_concat_date(title: str) -> str:
    """Fix titles like 'Shrek the MusicalJune 25 - July 12' → 'Shrek the Musical'."""
    m = _CONCAT_DATE.search(title)
    if m:
        return title[: m.start(2)].strip()
    return title


def _find_by_selectors(soup, selectors: list):
    for sel in selectors:
        found = soup.select(sel)
        if found:
            return found
    return []


# ── Extraction: Ollama local model ────────────────────────────────────────────

EXTRACTION_PROMPT = """Extract theater show listings from the HTML below.
Return a JSON array of show objects. Each object must have these keys:
- title (string, required)
- playwright (string or null)
- director (string or null)
- start_date (string "YYYY-MM-DD" or null)
- end_date (string "YYYY-MM-DD" or null)
- showtimes (string like "Thursdays-Saturdays 8pm, Sundays 3pm" or null)
- ticket_url (full URL string or null)
- description (brief string or null)

Include only upcoming theatrical productions. Skip past shows, navigation links, staff bios, classes, or events that are not performances.
If no shows are found, return an empty JSON array: []
Return ONLY valid JSON. No explanation, no markdown, no code fences.

Venue: {venue_name}
Page URL: {url}

HTML:
{html}"""


def _is_ollama_running() -> bool:
    try:
        resp = requests.get("http://localhost:11434/api/tags", timeout=3)
        return resp.status_code == 200
    except Exception:
        return False


def _trim_html(html: str, max_chars: int = 6000) -> str:
    """Strip scripts, styles, and nav to reduce noise before sending to model."""
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "nav", "footer", "head", "noscript", "svg"]):
        tag.decompose()
    text = soup.get_text(" ", strip=True)
    # Fall back to raw HTML if get_text is too short (JS-heavy site)
    if len(text) < 200:
        text = html
    return text[:max_chars]


def extract_with_ollama(html: str, venue: dict) -> list[dict]:
    if not _is_ollama_running():
        log.warning("Ollama not running — skipping LLM extraction for %s", venue["name"])
        return []

    trimmed = _trim_html(html)
    prompt = EXTRACTION_PROMPT.format(
        venue_name=venue["name"],
        url=venue["url"],
        html=trimmed,
    )

    try:
        resp = requests.post(
            OLLAMA_URL,
            json={
                "model": OLLAMA_MODEL,
                "prompt": prompt,
                "stream": False,
                "options": {"temperature": 0.1},  # low temp for structured extraction
            },
            timeout=120,
        )
        resp.raise_for_status()
        raw = resp.json().get("response", "").strip()

        # Strip markdown code fences if model added them anyway
        raw = re.sub(r"^```(?:json)?\s*", "", raw)
        raw = re.sub(r"\s*```$", "", raw)

        shows = json.loads(raw)
        if isinstance(shows, list):
            return [s for s in shows if isinstance(s, dict) and s.get("title")]
        return []
    except json.JSONDecodeError as e:
        log.warning("Ollama returned invalid JSON for %s: %s", venue["name"], e)
        return []
    except Exception as e:
        log.warning("Ollama error for %s: %s", venue["name"], e)
        return []


# ── Main pipeline ─────────────────────────────────────────────────────────────

def scrape_venue(venue: dict) -> tuple[list[dict], str]:
    """Returns (shows, extraction_method). Shows may be empty."""
    html = fetch_page(venue["url"])
    if not html:
        return [], "fetch-failed"

    # 1. schema.org
    shows = extract_schema_org(html, venue)
    if shows:
        return shows, "schema.org"

    # 2. CSS heuristics
    shows = extract_css_patterns(html, venue)
    if shows:
        return shows, "css-patterns"

    # 3. Ollama
    shows = extract_with_ollama(html, venue)
    if shows:
        return shows, "ollama"

    return [], "no-match"


def run(target_venue: Optional[str] = None, dry_run: bool = False):
    venues = VENUES
    if target_venue:
        venues = [v for v in VENUES if target_venue.lower() in v["name"].lower()]
        if not venues:
            print(f"No venue matching '{target_venue}'. Known venues:")
            for v in VENUES:
                print(f"  {v['name']}")
            sys.exit(1)

    if dry_run:
        print(f"Would scrape {len(venues)} venues:")
        for v in venues:
            print(f"  {v['name']}: {v['url']}")
        return

    all_shows = []
    stats = {"schema.org": 0, "css-patterns": 0, "ollama": 0, "no-match": 0, "fetch-failed": 0}

    log.info("Starting scrape of %d venues", len(venues))
    ollama_ok = _is_ollama_running()
    if not ollama_ok:
        log.warning(
            "Ollama not detected at localhost:11434. "
            "LLM fallback disabled. Run: ollama serve"
        )

    for i, venue in enumerate(venues):
        log.info("[%d/%d] %s", i + 1, len(venues), venue["name"])
        shows, method = scrape_venue(venue)
        stats[method] = stats.get(method, 0) + 1

        for show in shows:
            show["venue"] = venue["name"]
            show["source_url"] = venue["url"]
            show["extraction_method"] = method
            show["id"] = _make_id(show["title"], venue["name"])
        all_shows.extend(shows)

        log.info("  → %d show(s) via %s", len(shows), method)

        if i < len(venues) - 1:
            time.sleep(REQUEST_DELAY)

    output = {
        "city": CITY,
        "scraped_at": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "show_count": len(all_shows),
        "venue_count": len(venues),
        "stats": stats,
        "shows": all_shows,
    }

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"\n✓ {len(all_shows)} shows from {len(venues)} venues → {OUTPUT_FILE}")
    print(f"  schema.org: {stats['schema.org']} venues  |  "
          f"css-patterns: {stats['css-patterns']}  |  "
          f"ollama: {stats['ollama']}  |  "
          f"no-match: {stats['no-match']}  |  "
          f"failed: {stats['fetch-failed']}")


def _make_id(title: str, venue: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", (title + " " + venue).lower()).strip("-")
    return slug[:80]


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s  %(levelname)-7s  %(message)s",
        datefmt="%H:%M:%S",
    )

    parser = argparse.ArgumentParser(description="Curtain Call Dallas show scraper")
    parser.add_argument("--dry-run", action="store_true", help="List venues without fetching")
    parser.add_argument("--venue", metavar="NAME", help="Scrape a single venue by name")
    args = parser.parse_args()

    run(target_venue=args.venue, dry_run=args.dry_run)
