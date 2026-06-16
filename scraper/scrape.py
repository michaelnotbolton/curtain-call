#!/usr/bin/env python3
"""
Curtain Call — Dallas show scraper
Fetches shows from Dallas-area theater websites and outputs public/data/shows-dallas.json

Extraction pipeline (in order, first success wins):
  1. schema.org JSON-LD    — free, structured, near-perfect where it exists
  2. CSS pattern heuristics — common WordPress/Squarespace theater templates
  3. PDF extraction         — pdfplumber text → Ollama; catches season brochures/order forms
  4. Ollama on HTML         — LLM fallback for unstructured pages (requires Ollama running)

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
import urllib.robotparser
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

try:
    import pdfplumber
    _PDFPLUMBER_AVAILABLE = True
except ImportError:
    _PDFPLUMBER_AVAILABLE = False

SCRAPER_DIR = Path(__file__).parent
REPO_ROOT = SCRAPER_DIR.parent

# ── Configuration ────────────────────────────────────────────────────────────

def _load_config() -> dict:
    defaults = {
        "ollama_model": "qwen2.5:7b",
        "ollama_url": "http://localhost:11434/api/generate",
        "request_delay": 2.5,
        "request_timeout": 15,
        "stale_show_threshold": 0,
        "min_title_pass_rate": 0.5,
        "resynth_cooldown_days": 7,
    }
    cfg_path = SCRAPER_DIR / "config.json"
    if cfg_path.exists():
        with open(cfg_path) as f:
            defaults.update(json.load(f))
    return defaults

CONFIG = _load_config()

OLLAMA_MODEL = CONFIG["ollama_model"]
OLLAMA_URL = CONFIG["ollama_url"]
REQUEST_DELAY = CONFIG["request_delay"]
REQUEST_TIMEOUT = CONFIG["request_timeout"]
OUTPUT_FILE = REPO_ROOT / "public" / "data" / "shows-dallas.json"
RUN_LOG = SCRAPER_DIR / "runs.jsonl"
VENUES_FILE = SCRAPER_DIR / "venues_dallas.json"
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

# ── robots.txt cache ──────────────────────────────────────────────────────────

_robots_cache: dict[str, urllib.robotparser.RobotFileParser] = {}

def _robots_allows(url: str) -> bool:
    """Return False if robots.txt disallows our UA from this URL. Cached per domain."""
    parsed = urlparse(url)
    root = f"{parsed.scheme}://{parsed.netloc}"
    if root not in _robots_cache:
        rp = urllib.robotparser.RobotFileParser()
        rp.set_url(f"{root}/robots.txt")
        try:
            rp.read()
        except Exception:
            rp.allow_all = True
        _robots_cache[root] = rp
    return _robots_cache[root].can_fetch(HEADERS["User-Agent"], url)


def load_venues(status: str = "active") -> list[dict]:
    with open(VENUES_FILE) as f:
        data = json.load(f)
    return [v for v in data["venues"] if v.get("status") == status]


# ── Fetching ─────────────────────────────────────────────────────────────────

def fetch_page(url: str) -> Optional[str]:
    if not _robots_allows(url):
        log.warning("robots.txt disallows %s — skipping", url)
        return None
    try:
        resp = requests.get(url, headers=HEADERS, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        return resp.text
    except requests.exceptions.HTTPError as e:
        log.warning("HTTP %s fetching %s", e.response.status_code, url)
    except requests.exceptions.ConnectionError:
        log.warning("Connection error fetching %s", url)
    except requests.exceptions.Timeout:
        log.warning("Timeout fetching %s", url)
    except Exception as e:
        log.warning("Error fetching %s: %s", url, e)
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

    offers = item.get("offers", {})
    if isinstance(offers, list):
        offers = offers[0] if offers else {}

    ticket_url = item.get("url", "") or offers.get("url", "")
    if ticket_url and not ticket_url.startswith("http"):
        ticket_url = urljoin(base_url, ticket_url)

    # schema.org price: may be numeric or string; "0" means free
    price = None
    raw_price = offers.get("price")
    currency = offers.get("priceCurrency", "USD")
    if raw_price is not None:
        raw_price = str(raw_price).strip()
        if raw_price in ("0", "0.00", ""):
            price = "Free"
        elif raw_price:
            price = f"${raw_price}" if currency == "USD" else f"{raw_price} {currency}"

    # availability field signals public vs. private
    avail = offers.get("availability", "")
    event_status = item.get("eventStatus", "")
    if "Private" in avail or "Unavailable" in avail:
        public = False
    elif ticket_url or price is not None:
        public = True
    else:
        public = None

    return {
        "title": name,
        "playwright": None,
        "director": _coerce_str(item.get("director")),
        "start_date": _parse_date(start),
        "end_date": _parse_date(end),
        "showtimes": None,
        "ticket_url": ticket_url or None,
        "price": price,
        "public": public,
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

PRICE_SELECTORS = [
    ".tribe-events-cost",
    ".event-cost",
    ".ticket-price",
    ".price",
    "[class*='cost']",
    "[class*='price']",
]

_PRICE_RE = re.compile(r"\$\d+(?:\.\d{2})?(?:\s*[-–]\s*\$\d+(?:\.\d{2})?)?|free|pay what you (?:can|will)|suggested donation", re.IGNORECASE)
_CLOSED_RE = re.compile(r"\binvitation only\b|\bby invitation\b|\bstudent showcase\b|\bfamily and friends\b|\bnot open to the public\b", re.IGNORECASE)

def _extract_price(soup_el) -> Optional[str]:
    for sel in PRICE_SELECTORS:
        el = soup_el.select_one(sel)
        if el:
            text = el.get_text(strip=True)
            m = _PRICE_RE.search(text)
            if m:
                return m.group(0).strip()
    return None

def _infer_public(ticket_url: Optional[str], price: Optional[str], description: Optional[str]) -> Optional[bool]:
    desc = (description or "").lower()
    if _CLOSED_RE.search(desc):
        return False
    if ticket_url or price is not None:
        return True
    return None

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

        price = _extract_price(parent)

        shows.append({
            "title": text,
            "playwright": None,
            "director": None,
            "start_date": None,
            "end_date": None,
            "showtimes": date_text,
            "ticket_url": ticket_url,
            "price": price,
            "public": _infer_public(ticket_url, price, None),
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

    price = _extract_price(art)

    return {
        "title": title,
        "playwright": playwright_text,
        "director": None,
        "start_date": None,
        "end_date": None,
        "showtimes": date_text,
        "ticket_url": ticket_url,
        "price": price,
        "public": _infer_public(ticket_url, price, None),
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
- price (string like "$15", "$10-25", "Free", "Pay what you can" — or null if not mentioned)
- public (true if open to the public, false if invitation-only/student showcase/family only, null if unclear)
- description (brief string or null)

Include only upcoming theatrical productions. Skip past shows, navigation links, staff bios, classes, or events that are not performances.
Set public=false if the page uses language like "invitation only", "student showcase", "family and friends", or "not open to the public".
Set public=true if tickets are available for purchase or the show is clearly advertised to the public.
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
            out = []
            for s in shows:
                if not isinstance(s, dict) or not s.get("title"):
                    continue
                # Normalise public field — model may return string "true"/"false"
                pub = s.get("public")
                if isinstance(pub, str):
                    s["public"] = True if pub.lower() == "true" else (False if pub.lower() == "false" else None)
                out.append(s)
            return out
        return []
    except json.JSONDecodeError as e:
        log.warning("Ollama returned invalid JSON for %s: %s", venue["name"], e)
        return []
    except Exception as e:
        log.warning("Ollama error for %s: %s", venue["name"], e)
        return []


# ── PDF extraction ────────────────────────────────────────────────────────────

# Filenames that are clearly administrative, not show listings
_PDF_SKIP_RE = re.compile(
    r"accessibility|privacy|policy|statement|contract|application|employment"
    r"|donation|sponsor|audition|press.?release|newsletter|map|parking|directions",
    re.IGNORECASE,
)

def _fetch_pdf_bytes(url: str) -> Optional[bytes]:
    if not _robots_allows(url):
        log.warning("robots.txt disallows PDF %s", url)
        return None
    try:
        resp = requests.get(url, headers=HEADERS, timeout=30)
        resp.raise_for_status()
        if "pdf" not in resp.headers.get("content-type", "").lower():
            return None
        return resp.content
    except Exception as e:
        log.warning("Could not fetch PDF %s: %s", url, e)
        return None


def _pdf_to_text(pdf_bytes: bytes) -> Optional[str]:
    if not _PDFPLUMBER_AVAILABLE:
        return None
    import io
    try:
        with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
            pages = [p.extract_text() or "" for p in pdf.pages]
            text = "\n".join(pages).strip()
            return text if len(text) > 50 else None
    except Exception as e:
        log.warning("pdfplumber error: %s", e)
        return None


def extract_from_pdfs(pdf_links: list[str], venue: dict) -> list[dict]:
    """Try each PDF link in order; return first successful extraction."""
    if not _is_ollama_running():
        log.warning("Ollama not running — skipping PDF extraction for %s", venue["name"])
        return []

    for url in pdf_links:
        filename = url.rsplit("/", 1)[-1]
        if _PDF_SKIP_RE.search(filename):
            log.info("  Skipping administrative PDF: %s", filename)
            continue

        log.info("  Trying PDF: %s", filename)
        pdf_bytes = _fetch_pdf_bytes(url)
        if not pdf_bytes:
            continue

        text = _pdf_to_text(pdf_bytes)
        if not text:
            log.info("  PDF appears image-based (no text extracted): %s", filename)
            # TODO: vision model fallback (llava) for image PDFs
            continue

        log.info("  Extracted %d chars from PDF, sending to Ollama", len(text))
        prompt = EXTRACTION_PROMPT.format(
            venue_name=venue["name"],
            url=url,
            html=text[:6000],
        )
        try:
            resp = requests.post(
                OLLAMA_URL,
                json={"model": OLLAMA_MODEL, "prompt": prompt, "stream": False,
                      "options": {"temperature": 0.1}},
                timeout=120,
            )
            resp.raise_for_status()
            raw = resp.json().get("response", "").strip()
            raw = re.sub(r"^```(?:json)?\s*", "", raw)
            raw = re.sub(r"\s*```$", "", raw)
            shows = json.loads(raw)
            if isinstance(shows, list):
                shows = [s for s in shows if isinstance(s, dict) and s.get("title")]
            if shows:
                log.info("  PDF yielded %d show(s)", len(shows))
                return shows
        except Exception as e:
            log.warning("  Ollama error on PDF %s: %s", filename, e)

    return []


# ── PDF detection ─────────────────────────────────────────────────────────────

def _find_pdf_links(html: str, base_url: str) -> list[str]:
    """Return absolute URLs of any .pdf links on the page."""
    soup = BeautifulSoup(html, "html.parser")
    pdfs = []
    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        if href.lower().endswith(".pdf"):
            full = href if href.startswith("http") else urljoin(base_url, href)
            pdfs.append(full)
    return pdfs


# ── Main pipeline ─────────────────────────────────────────────────────────────

def scrape_venue(venue: dict) -> tuple[list[dict], str, list[str]]:
    """Returns (shows, extraction_method, pdf_urls)."""
    html = fetch_page(venue["url"])
    if not html:
        return [], "fetch-failed", []

    # 1. schema.org
    shows = extract_schema_org(html, venue)
    if shows:
        return shows, "schema.org", []

    # 2. CSS heuristics
    shows = extract_css_patterns(html, venue)
    if shows:
        return shows, "css-patterns", []

    # 3. PDF extraction — season brochures often have richer data than the HTML
    pdf_links = _find_pdf_links(html, venue["url"])
    if pdf_links:
        shows = extract_from_pdfs(pdf_links, venue)
        if shows:
            return shows, "pdf", pdf_links
        # PDFs found but extraction failed — log them and fall through
        log.info("  PDF(s) detected but not extracted: %s", pdf_links)

    # 4. Ollama on HTML
    shows = extract_with_ollama(html, venue)
    if shows:
        return shows, "ollama", pdf_links

    if pdf_links:
        return [], "pdf-detected", pdf_links

    return [], "no-match", []


def _append_run_log(entry: dict):
    with open(RUN_LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")


def run(target_venue: Optional[str] = None, dry_run: bool = False):
    venues = load_venues(status="active")
    if target_venue:
        venues = [v for v in venues if target_venue.lower() in v["name"].lower()]
        if not venues:
            all_venues = load_venues(status="active")
            print(f"No active venue matching '{target_venue}'. Known venues:")
            for v in all_venues:
                print(f"  {v['name']}")
            sys.exit(1)

    if dry_run:
        print(f"Would scrape {len(venues)} venues:")
        for v in venues:
            print(f"  [{v['level']}] {v['name']}: {v['url']}")
        return

    all_shows = []
    stats = {"schema.org": 0, "css-patterns": 0, "pdf": 0, "ollama": 0, "pdf-detected": 0, "no-match": 0, "fetch-failed": 0}
    run_ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    log.info("Starting scrape of %d venues", len(venues))
    ollama_ok = _is_ollama_running()
    if not ollama_ok:
        log.warning(
            "Ollama not detected at localhost:11434. "
            "LLM fallback disabled. Run: ollama serve"
        )

    for i, venue in enumerate(venues):
        log.info("[%d/%d] %s", i + 1, len(venues), venue["name"])
        shows, method, pdf_links = scrape_venue(venue)
        stats[method] = stats.get(method, 0) + 1

        is_k12 = venue.get("level") == "k12"
        filtered = []
        for show in shows:
            show["venue"] = venue["name"]
            show["venue_level"] = venue.get("level")
            show["venue_zip"] = venue.get("zip")
            show["source_url"] = venue["url"]
            show["extraction_method"] = method
            show["id"] = _make_id(show["title"], venue["name"])
            pub = show.get("public")
            if pub is False:
                log.info("    Dropping (not public): %s", show["title"])
                continue
            if is_k12 and pub is None:
                log.info("    Dropping k12 (public unconfirmed): %s", show["title"])
                continue
            filtered.append(show)
        all_shows.extend(filtered)

        log.info("  → %d show(s) via %s", len(shows), method)
        log_entry = {
            "ts": run_ts,
            "venue_id": venue["id"],
            "venue": venue["name"],
            "shows": len(filtered),
            "method": method,
            "level": venue.get("level"),
        }
        if pdf_links:
            log_entry["pdf_links"] = pdf_links
        _append_run_log(log_entry)

        if i < len(venues) - 1:
            time.sleep(REQUEST_DELAY)

    output = {
        "city": CITY,
        "scraped_at": run_ts,
        "show_count": len(all_shows),
        "venue_count": len(venues),
        "stats": stats,
        "shows": all_shows,
    }

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"\n✓ {len(all_shows)} shows from {len(venues)} venues → {OUTPUT_FILE}")
    print(f"  schema.org: {stats['schema.org']}  |  "
          f"css-patterns: {stats['css-patterns']}  |  "
          f"pdf: {stats['pdf']}  |  "
          f"ollama: {stats['ollama']}  |  "
          f"pdf-detected: {stats['pdf-detected']}  |  "
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
