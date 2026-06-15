#!/usr/bin/env python3
"""
Curtain Call — venue discovery script

Finds theater venue homepages in a geographic area using multiple independent
strategies, classifies each one with Ollama to confirm it's a theater and
locate its shows/productions page, then writes candidates as pending_review
for human approval before they enter the weekly scrape pool.

Each discovery strategy is an independent function: (city, state) → [urls].
Strategy failures are logged and isolated — one broken strategy doesn't
block the others. Add or disable strategies in STRATEGIES without touching
the pipeline.

Usage:
  python3 scraper/discover.py --city dallas --state TX
  python3 scraper/discover.py --city dallas --state TX --limit 40
  python3 scraper/discover.py --city dallas --state TX --strategies ddg,aact
  python3 scraper/discover.py --city dallas --state TX --review
  python3 scraper/discover.py --city dallas --state TX --approve venue-id
  python3 scraper/discover.py --city dallas --state TX --reject venue-id
"""

import json
import re
import sys
import time
import logging
import argparse
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Optional
from urllib.parse import urljoin, urlparse, urlencode

import requests
from bs4 import BeautifulSoup

SCRAPER_DIR = Path(__file__).parent
log = logging.getLogger(__name__)


# ── Config ────────────────────────────────────────────────────────────────────

def _load_config() -> dict:
    defaults = {
        "ollama_model": "qwen2.5:7b",
        "ollama_url": "http://localhost:11434/api/generate",
        "request_delay": 3.0,
        "request_timeout": 15,
        "discovery_min_confidence": 0.6,
    }
    cfg_path = SCRAPER_DIR / "config.json"
    if cfg_path.exists():
        with open(cfg_path) as f:
            defaults.update(json.load(f))
    return defaults

CONFIG = _load_config()

HEADERS = {
    "User-Agent": (
        "CurtainCall/0.1 (theater venue discovery for audience discovery tool; "
        "contact michaelnotbolton@gmail.com)"
    ),
    "Accept": "text/html,application/xhtml+xml,*/*",
    "Accept-Language": "en-US,en;q=0.9",
}

VALID_LEVELS = [
    "k12", "college", "community",
    "small_professional", "regional_professional", "touring",
]

# Domains that are never theater venue homepages
SKIP_DOMAINS = frozenset({
    "facebook.com", "twitter.com", "x.com", "instagram.com", "youtube.com",
    "linkedin.com", "tiktok.com", "pinterest.com",
    "eventbrite.com", "ticketmaster.com", "axs.com", "seatgeek.com",
    "todaytix.com", "goldstar.com",
    "google.com", "apple.com", "yelp.com", "tripadvisor.com",
    "wikipedia.org", "wikimedia.org",
    "amazon.com", "maps.apple.com",
})


# ── Fetch helper ──────────────────────────────────────────────────────────────

def fetch(url: str, extra_headers: Optional[dict] = None) -> Optional[str]:
    headers = {**HEADERS, **(extra_headers or {})}
    try:
        resp = requests.get(url, headers=headers, timeout=CONFIG["request_timeout"])
        resp.raise_for_status()
        return resp.text
    except requests.HTTPError as e:
        log.warning("HTTP %s fetching %s", e.response.status_code, url)
    except Exception as e:
        log.warning("Fetch failed %s: %s", url, e)
    return None


def _root_url(url: str) -> str:
    p = urlparse(url)
    return f"{p.scheme}://{p.netloc}/"


def _domain(url: str) -> str:
    return urlparse(url).netloc.lstrip("www.")


def _is_skippable(url: str) -> bool:
    d = _domain(url)
    return any(d == skip or d.endswith("." + skip) for skip in SKIP_DOMAINS)


# ── Discovery strategies ──────────────────────────────────────────────────────
# Each strategy: (city: str, state: str) -> list[str] of candidate homepage URLs.
# Must handle its own errors and return [] on failure.
# Log what it finds and why it fails so we can iterate.

# Search query templates tried in order. More specific → broader fallback.
_DDG_QUERIES = [
    "{city} {state} theater company",
    "{city} {state} theatre company",
    "{city} {state} community theater",
    "{city} {state} professional theater productions",
    "{city} {state} performing arts organization",
    "{city} {state} musical theater",
    "{city} {state} high school theater productions",
    "{city} {state} college university theater drama department",
    "{city} {state} children youth theater",
]

def strategy_ddg(city: str, state: str) -> list[str]:
    """
    DuckDuckGo HTML search. Tries multiple query variants and unions results.
    No API key needed. Fragile to DDG HTML changes — isolated failure if it breaks.
    """
    found = set()
    for template in _DDG_QUERIES:
        query = template.format(city=city, state=state)
        url = f"https://html.duckduckgo.com/html/?{urlencode({'q': query})}"
        html = fetch(url, extra_headers={"Accept": "text/html"})
        if not html:
            log.warning("[ddg] Fetch failed for query: %s", query)
            time.sleep(CONFIG["request_delay"])
            continue

        soup = BeautifulSoup(html, "html.parser")

        # DDG HTML result links are in <a class="result__url"> or result__a
        links = soup.select("a.result__url, a.result__a, .result__extras__url")
        extracted = 0
        for a in links:
            href = a.get("href", "").strip()
            if not href:
                continue
            # DDG sometimes wraps in /l/?uddg=<encoded_url>
            if "/l/?" in href:
                m = re.search(r"uddg=([^&]+)", href)
                if m:
                    from urllib.parse import unquote
                    href = unquote(m.group(1))
            if not href.startswith("http"):
                continue
            root = _root_url(href)
            if not _is_skippable(root) and root not in found:
                found.add(root)
                extracted += 1

        log.info("[ddg] '%s' → %d new URLs", query, extracted)
        time.sleep(CONFIG["request_delay"])  # be polite to DDG

    log.info("[ddg] Total: %d candidate URLs", len(found))
    return list(found)


def strategy_aact(city: str, state: str) -> list[str]:
    """
    American Association of Community Theatre member directory.
    Filters by state, extracts member website links.
    """
    url = f"https://aact.org/find-theater?state={state}"
    html = fetch(url)
    if not html:
        log.warning("[aact] Could not fetch directory for state %s", state)
        return []

    soup = BeautifulSoup(html, "html.parser")
    found = set()

    # AACT member links appear as external website links in listings
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if not href.startswith("http"):
            continue
        if "aact.org" in href:
            continue
        root = _root_url(href)
        if not _is_skippable(root):
            found.add(root)

    log.info("[aact] %d candidate URLs from TX member directory", len(found))
    return list(found)


def strategy_tcg(city: str, state: str) -> list[str]:
    """
    Theatre Communications Group member directory.
    Professional and semi-professional companies — skews toward regional theaters.
    """
    url = "https://tcg.org/web/Audience_Resources/Find_Theatre/TCG_Member_Theatre_Page.aspx"
    html = fetch(url)
    if not html:
        log.warning("[tcg] Could not fetch TCG member directory")
        return []

    soup = BeautifulSoup(html, "html.parser")
    found = set()

    state_lower = state.lower()
    city_lower = city.lower()

    # TCG page lists theaters with location info — try to filter to our metro
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if not href.startswith("http") or "tcg.org" in href:
            continue
        # Check if nearby text mentions our state
        context = (a.get_text() + (a.parent.get_text() if a.parent else "")).lower()
        if state_lower not in context and city_lower not in context:
            continue
        root = _root_url(href)
        if not _is_skippable(root):
            found.add(root)

    log.info("[tcg] %d candidate URLs from TCG directory (filtered to %s)", len(found), state)
    return list(found)


def strategy_eventbrite(city: str, state: str) -> list[str]:
    """
    Eventbrite organizer pages for theater events in the metro.
    Eventbrite shows the organizer's website — we extract those as venue candidates.
    """
    # Search Eventbrite for theater events in the city
    url = (
        f"https://www.eventbrite.com/d/{state.lower()}--{city.lower()}/theater/?format=list"
    )
    html = fetch(url)
    if not html:
        log.warning("[eventbrite] Could not fetch Eventbrite search for %s %s", city, state)
        return []

    soup = BeautifulSoup(html, "html.parser")
    found = set()

    # Look for organizer website links in event cards
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if not href.startswith("http") or "eventbrite.com" in href:
            continue
        root = _root_url(href)
        if not _is_skippable(root):
            found.add(root)

    log.info("[eventbrite] %d candidate URLs from Eventbrite theater events", len(found))
    return list(found)


# Registry: name → strategy function. Add new strategies here.
STRATEGIES: dict[str, Callable[[str, str], list[str]]] = {
    "ddg":        strategy_ddg,
    "aact":       strategy_aact,
    "tcg":        strategy_tcg,
    "eventbrite": strategy_eventbrite,
}


# ── Ollama classification ──────────────────────────────────────────────────────

def _is_ollama_running() -> bool:
    try:
        return requests.get("http://localhost:11434/api/tags", timeout=3).status_code == 200
    except Exception:
        return False


def _ollama(prompt: str) -> Optional[str]:
    try:
        resp = requests.post(
            CONFIG["ollama_url"],
            json={
                "model": CONFIG["ollama_model"],
                "prompt": prompt,
                "stream": False,
                "options": {"temperature": 0.1},
            },
            timeout=120,
        )
        resp.raise_for_status()
        raw = resp.json().get("response", "").strip()
        raw = re.sub(r"^```(?:json)?\s*", "", raw)
        raw = re.sub(r"\s*```$", "", raw)
        return raw
    except Exception as e:
        log.warning("Ollama error: %s", e)
        return None


CLASSIFY_PROMPT = """You are classifying a webpage to determine if it belongs to a theater or performing arts venue.

URL: {url}
Page text (truncated to 5000 chars):
{text}

Return a JSON object only. Fields:
- "is_theater": true/false
- "name": official name of the venue or company
- "level": one of ["k12", "college", "community", "small_professional", "regional_professional", "touring"]
    k12 = elementary/middle/high school production group
    college = university or community college theater program
    community = volunteer/amateur company
    small_professional = paid artists, small local productions
    regional_professional = larger regional company, equity or near-equity
    touring = primarily hosts touring/Broadway productions
- "show_url": the URL most likely to list UPCOMING shows or productions (may differ from the homepage; null if unclear)
- "address": street address if visible, else null
- "zip": zip code if visible, else null
- "city": city name, else null
- "state": 2-letter state code, else null
- "confidence": float 0.0–1.0

Return only valid JSON. No explanation, no markdown."""


def classify(url: str, html: str) -> Optional[dict]:
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "nav", "footer", "head", "noscript", "svg"]):
        tag.decompose()
    text = soup.get_text(" ", strip=True)[:5000]

    raw = _ollama(CLASSIFY_PROMPT.format(url=url, text=text))
    if not raw:
        return None
    try:
        result = json.loads(raw)
        return result if isinstance(result, dict) else None
    except json.JSONDecodeError as e:
        log.warning("Invalid JSON from Ollama for %s: %s", url, e)
        return None


# ── Venue JSON helpers ────────────────────────────────────────────────────────

def _venues_path(city: str) -> Path:
    return SCRAPER_DIR / f"venues_{city.lower()}.json"


def load_venues_json(city: str) -> dict:
    path = _venues_path(city)
    if path.exists():
        with open(path) as f:
            return json.load(f)
    return {"meta": {"city": city, "state": "", "updated": ""}, "venues": []}


def save_venues_json(city: str, data: dict):
    data["meta"]["updated"] = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    path = _venues_path(city)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    log.info("Saved %d total venues to %s", len(data["venues"]), path)


def _make_id(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")[:60]


def _known_domains(data: dict) -> set[str]:
    return {_domain(v["url"]) for v in data["venues"] if v.get("url")}


# ── Discovery pipeline ────────────────────────────────────────────────────────

def discover(city: str, state: str, strategy_names: list[str], limit: Optional[int]):
    if not _is_ollama_running():
        print("Ollama is not running — start it with: ollama serve")
        print("Discovery requires Ollama to classify venue pages.")
        sys.exit(1)

    data = load_venues_json(city)
    known = _known_domains(data)

    # Collect candidates from all requested strategies, deduped
    candidates: dict[str, str] = {}  # root_url → strategy that found it
    for name in strategy_names:
        fn = STRATEGIES.get(name)
        if not fn:
            log.warning("Unknown strategy '%s' — skipping", name)
            continue
        log.info("Running strategy: %s", name)
        try:
            urls = fn(city, state)
        except Exception as e:
            log.error("Strategy '%s' crashed: %s", name, e)
            urls = []
        for url in urls:
            if url not in candidates:
                candidates[url] = name

    log.info("Total unique candidates: %d  |  Already known: %d",
             len(candidates), sum(1 for u in candidates if _domain(u) in known))

    added = 0
    checked = 0

    for url, found_by in candidates.items():
        if limit and checked >= limit:
            break
        if _domain(url) in known:
            log.info("Skip (known): %s", url)
            continue

        log.info("[%s] Classifying: %s", found_by, url)
        html = fetch(url)
        checked += 1
        if not html:
            time.sleep(CONFIG["request_delay"])
            continue

        result = classify(url, html)
        time.sleep(CONFIG["request_delay"])

        if not result:
            log.warning("Classification failed: %s", url)
            continue

        confidence = float(result.get("confidence", 0))
        if not result.get("is_theater"):
            log.info("Not a theater (conf=%.2f): %s", confidence, url)
            continue
        if confidence < CONFIG.get("discovery_min_confidence", 0.6):
            log.info("Low confidence %.2f, skipping: %s", confidence, url)
            continue

        name = result.get("name") or _domain(url)
        level = result.get("level", "community")
        if level not in VALID_LEVELS:
            level = "community"

        show_url = result.get("show_url") or url

        venue = {
            "id": _make_id(name),
            "name": name,
            "url": show_url,
            "homepage": url,
            "level": level,
            "city": result.get("city") or city.title(),
            "state": result.get("state") or state,
            "zip": result.get("zip"),
            "address": result.get("address"),
            "status": "pending_review",
            "source": f"discovered:{found_by}",
            "added": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
            "discovery_confidence": confidence,
            "selectors": None,
            "selector_updated": None,
        }

        data["venues"].append(venue)
        known.add(_domain(url))
        added += 1
        log.info("✓ pending_review: %s [%s] conf=%.2f  show_url=%s",
                 name, level, confidence, show_url)

    save_venues_json(city, data)
    print(f"\n✓ {added} new venues added as pending_review ({checked} candidates checked)")
    print(f"  Run --review to inspect, --approve <id> or --reject <id> to act.")


# ── Review / approve / reject ──────────────────────────────────────────────────

def review(city: str):
    data = load_venues_json(city)
    pending = [v for v in data["venues"] if v.get("status") == "pending_review"]
    if not pending:
        print("No venues pending review.")
        return
    print(f"\n{len(pending)} venue(s) pending review:\n")
    for v in pending:
        print(f"  id:         {v['id']}")
        print(f"  name:       {v['name']}")
        print(f"  level:      {v['level']}")
        print(f"  show_url:   {v['url']}")
        print(f"  homepage:   {v.get('homepage', v['url'])}")
        print(f"  location:   {v.get('city')}, {v.get('state')} {v.get('zip') or ''}")
        print(f"  confidence: {v.get('discovery_confidence', '?')}")
        print(f"  source:     {v.get('source')}")
        print()


def approve(city: str, venue_id: str):
    data = load_venues_json(city)
    for v in data["venues"]:
        if v["id"] == venue_id and v.get("status") == "pending_review":
            v["status"] = "active"
            save_venues_json(city, data)
            print(f"✓ Approved: {v['name']}")
            return
    print(f"No pending_review venue with id '{venue_id}' found.")


def reject(city: str, venue_id: str):
    data = load_venues_json(city)
    before = len(data["venues"])
    data["venues"] = [v for v in data["venues"] if v["id"] != venue_id]
    if len(data["venues"]) < before:
        save_venues_json(city, data)
        print(f"✓ Removed: '{venue_id}'")
    else:
        print(f"No venue with id '{venue_id}' found.")


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s  %(levelname)-7s  %(message)s",
        datefmt="%H:%M:%S",
    )

    all_strategy_names = list(STRATEGIES.keys())

    parser = argparse.ArgumentParser(description="Curtain Call venue discovery")
    parser.add_argument("--city",  default="dallas", help="City to discover (default: dallas)")
    parser.add_argument("--state", default="TX",     help="State code (default: TX)")
    parser.add_argument(
        "--strategies",
        default=",".join(all_strategy_names),
        help=f"Comma-separated strategies to run. Available: {', '.join(all_strategy_names)}"
    )
    parser.add_argument("--limit",   type=int, help="Max candidates to classify per run")
    parser.add_argument("--review",  action="store_true", help="List pending_review venues")
    parser.add_argument("--approve", metavar="ID", help="Approve a venue by id")
    parser.add_argument("--reject",  metavar="ID", help="Remove a venue by id")
    args = parser.parse_args()

    if args.review:
        review(args.city)
    elif args.approve:
        approve(args.city, args.approve)
    elif args.reject:
        reject(args.city, args.reject)
    else:
        strategy_names = [s.strip() for s in args.strategies.split(",") if s.strip()]
        discover(args.city, args.state, strategy_names, args.limit)
