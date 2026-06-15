#!/usr/bin/env python3
"""
Curtain Call — venue discovery script

Finds new theater venues in a metro area and classifies them for human review.
Writes candidates to venues_<city>.json with status "pending_review".
Run separately from the weekly scraper; intended for monthly or on-demand use.

Pipeline:
  1. Crawl known discovery seed pages (directories, arts councils, aggregators)
  2. Extract candidate venue URLs from each seed
  3. For each candidate not already in venues JSON:
     a. Fetch homepage
     b. Use Ollama to classify: is this a theater? what level? extract metadata.
     c. Write to venues JSON as pending_review
  4. Human reviews pending_review entries and promotes to active (or deletes)

Usage:
  python3 scraper/discover.py --city dallas        # discover new venues
  python3 scraper/discover.py --city dallas --review  # list pending_review venues
  python3 scraper/discover.py --approve venue-id   # promote to active
  python3 scraper/discover.py --reject venue-id    # remove from list
"""

import json
import re
import sys
import time
import logging
import argparse
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

SCRAPER_DIR = Path(__file__).parent

log = logging.getLogger(__name__)


# ── Config ────────────────────────────────────────────────────────────────────

def _load_config() -> dict:
    defaults = {
        "ollama_model": "qwen2.5:7b",
        "ollama_url": "http://localhost:11434/api/generate",
        "request_delay": 2.5,
        "request_timeout": 15,
    }
    cfg_path = SCRAPER_DIR / "config.json"
    if cfg_path.exists():
        with open(cfg_path) as f:
            defaults.update(json.load(f))
    return defaults

CONFIG = _load_config()

HEADERS = {
    "User-Agent": (
        "CurtainCall/0.1 (theater venue discovery; "
        "contact michaelnotbolton@gmail.com)"
    ),
    "Accept": "text/html,application/xhtml+xml",
    "Accept-Language": "en-US,en;q=0.9",
}

VALID_LEVELS = [
    "k12", "college", "community",
    "small_professional", "regional_professional", "touring",
]


# ── Discovery seeds ───────────────────────────────────────────────────────────
# Each entry is a page known to list theater venues in a metro area.
# The discover_links() function crawls these for venue homepage URLs.

SEEDS = {
    "dallas": [
        # AACT (American Association of Community Theatre) Texas members
        {"url": "https://aact.org/find-theater?state=TX", "note": "AACT TX members"},
        # TCG (Theatre Communications Group) member directory
        {"url": "https://tcg.org/web/Audience_Resources/Find_Theatre/TCG_Member_Theatre_Page.aspx",
         "note": "TCG member theatres"},
        # Texas Commission on the Arts funded orgs
        {"url": "https://www.arts.texas.gov/", "note": "Texas Commission on the Arts"},
        # DFW-specific aggregators
        {"url": "https://www.dallasartsdistrict.org/", "note": "Dallas Arts District"},
        {"url": "https://www.dfwchild.com/arts-entertainment/theater-for-kids/", "note": "DFW family theater"},
        # University/college theater programs in DFW
        {"url": "https://udallas.edu/academics/programs/drama/upcomingproductions/index.php",
         "note": "University of Dallas Drama"},
        {"url": "https://www.smu.edu/meadows/newsandevents/season-performances",
         "note": "SMU Meadows"},
    ],
}


# ── Ollama helpers ────────────────────────────────────────────────────────────

def _is_ollama_running() -> bool:
    try:
        resp = requests.get("http://localhost:11434/api/tags", timeout=3)
        return resp.status_code == 200
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

Venue page URL: {url}
Page text (truncated):
{text}

Respond with a JSON object only. Fields:
- "is_theater": true/false — is this a theater, performing arts company, or drama program?
- "name": string — official name of the venue or company
- "level": one of ["k12", "college", "community", "small_professional", "regional_professional", "touring"]
  k12 = elementary/middle/high school production
  college = university or community college theater program
  community = volunteer/amateur theater company
  small_professional = paid artists, small budget, local productions
  regional_professional = larger regional company, equity or near-equity
  touring = primarily hosts touring/Broadway shows
- "show_url": string or null — the URL most likely to list upcoming shows or productions (may differ from the homepage)
- "address": string or null — street address if visible on the page
- "zip": string or null — zip code if visible
- "city": string or null
- "state": string or null — 2-letter state code
- "confidence": 0.0–1.0 — how confident are you in this classification?

Return only valid JSON. No explanation."""


def classify_venue(url: str, html: str) -> Optional[dict]:
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "nav", "footer", "head", "noscript"]):
        tag.decompose()
    text = soup.get_text(" ", strip=True)[:5000]

    raw = _ollama(CLASSIFY_PROMPT.format(url=url, text=text))
    if not raw:
        return None
    try:
        result = json.loads(raw)
        if not isinstance(result, dict):
            return None
        return result
    except json.JSONDecodeError as e:
        log.warning("Ollama returned invalid JSON for %s: %s", url, e)
        return None


# ── Link extraction from seed pages ──────────────────────────────────────────

def fetch(url: str) -> Optional[str]:
    try:
        resp = requests.get(url, headers=HEADERS, timeout=CONFIG["request_timeout"])
        resp.raise_for_status()
        return resp.text
    except Exception as e:
        log.warning("Fetch failed %s: %s", url, e)
        return None


def extract_venue_links(seed_url: str, html: str) -> list[str]:
    """
    Pull candidate venue homepage URLs from a directory/listing page.
    Heuristic: external links that look like organization homepages
    (not social media, not the seed domain itself, not file downloads).
    """
    soup = BeautifulSoup(html, "html.parser")
    seed_domain = urlparse(seed_url).netloc
    seen = set()
    links = []

    skip_domains = {
        "facebook.com", "twitter.com", "instagram.com", "youtube.com",
        "linkedin.com", "tiktok.com", "eventbrite.com", "ticketmaster.com",
        "google.com", "apple.com", "maps.google.com",
    }
    skip_extensions = {".pdf", ".jpg", ".jpeg", ".png", ".gif", ".zip", ".mp4"}

    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        if not href or href.startswith("#") or href.startswith("mailto:"):
            continue

        full = urljoin(seed_url, href)
        parsed = urlparse(full)

        if parsed.scheme not in ("http", "https"):
            continue
        if parsed.netloc == seed_domain:
            continue
        if any(d in parsed.netloc for d in skip_domains):
            continue
        if any(parsed.path.lower().endswith(ext) for ext in skip_extensions):
            continue

        # Normalize to homepage (strip deep paths from directory links)
        root = f"{parsed.scheme}://{parsed.netloc}/"
        if root not in seen:
            seen.add(root)
            links.append(root)

    return links


# ── Venue JSON helpers ────────────────────────────────────────────────────────

def _venues_path(city: str) -> Path:
    return SCRAPER_DIR / f"venues_{city.lower()}.json"


def load_venues_json(city: str) -> dict:
    path = _venues_path(city)
    if path.exists():
        with open(path) as f:
            return json.load(f)
    return {"meta": {"city": city, "updated": ""}, "venues": []}


def save_venues_json(city: str, data: dict):
    data["meta"]["updated"] = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    path = _venues_path(city)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    log.info("Saved %d venues to %s", len(data["venues"]), path)


def _make_id(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")[:60]


def _known_urls(data: dict) -> set[str]:
    return {
        urlparse(v["url"]).netloc
        for v in data["venues"]
        if v.get("url")
    }


# ── Discovery run ─────────────────────────────────────────────────────────────

def discover(city: str, limit: Optional[int] = None):
    seeds = SEEDS.get(city.lower())
    if not seeds:
        print(f"No seeds defined for city '{city}'. Add entries to SEEDS in discover.py.")
        sys.exit(1)

    if not _is_ollama_running():
        print("Ollama is not running. Start it with: ollama serve")
        print("Discovery requires Ollama for venue classification.")
        sys.exit(1)

    data = load_venues_json(city)
    known = _known_urls(data)
    added = 0
    checked = 0

    for seed in seeds:
        log.info("Crawling seed: %s", seed["url"])
        html = fetch(seed["url"])
        if not html:
            log.warning("Could not fetch seed: %s", seed["url"])
            continue

        candidates = extract_venue_links(seed["url"], html)
        log.info("  Found %d candidate links", len(candidates))

        for url in candidates:
            if limit and checked >= limit:
                break
            domain = urlparse(url).netloc
            if domain in known:
                log.info("  Skipping known: %s", url)
                continue

            log.info("  Checking: %s", url)
            html = fetch(url)
            if not html:
                checked += 1
                continue

            classification = classify_venue(url, html)
            checked += 1

            if not classification:
                log.warning("  Classification failed for %s", url)
                time.sleep(CONFIG["request_delay"])
                continue

            if not classification.get("is_theater"):
                log.info("  Not a theater: %s (confidence %.2f)",
                         url, classification.get("confidence", 0))
                time.sleep(CONFIG["request_delay"])
                continue

            confidence = classification.get("confidence", 0)
            name = classification.get("name") or domain
            level = classification.get("level", "community")
            if level not in VALID_LEVELS:
                level = "community"

            venue = {
                "id": _make_id(name),
                "name": name,
                "url": classification.get("show_url") or url,
                "homepage": url,
                "level": level,
                "city": classification.get("city") or city.title(),
                "state": classification.get("state") or "TX",
                "zip": classification.get("zip"),
                "address": classification.get("address"),
                "status": "pending_review",
                "source": f"discovered:{seed['note']}",
                "added": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
                "discovery_confidence": confidence,
                "selectors": None,
                "selector_updated": None,
            }

            data["venues"].append(venue)
            known.add(domain)
            added += 1
            log.info("  ✓ Added as pending_review: %s [%s] (confidence %.2f)",
                     name, level, confidence)

            time.sleep(CONFIG["request_delay"])

        if limit and checked >= limit:
            break

    save_venues_json(city, data)
    print(f"\n✓ Discovery complete: {added} new venues added as pending_review")
    print(f"  Run with --review to inspect them, --approve/--reject to act on them.")


# ── Review / approve / reject ─────────────────────────────────────────────────

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
        print(f"  url:        {v['url']}")
        print(f"  city/zip:   {v.get('city')}, {v.get('state')} {v.get('zip') or ''}")
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
        print(f"✓ Removed venue '{venue_id}'")
    else:
        print(f"No venue with id '{venue_id}' found.")


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s  %(levelname)-7s  %(message)s",
        datefmt="%H:%M:%S",
    )

    parser = argparse.ArgumentParser(description="Curtain Call venue discovery")
    parser.add_argument("--city", default="dallas", help="Metro area to discover (default: dallas)")
    parser.add_argument("--review", action="store_true", help="List pending_review venues")
    parser.add_argument("--approve", metavar="ID", help="Approve a pending venue by id")
    parser.add_argument("--reject", metavar="ID", help="Remove a venue by id")
    parser.add_argument("--limit", type=int, help="Max candidate URLs to check per run")
    args = parser.parse_args()

    if args.review:
        review(args.city)
    elif args.approve:
        approve(args.city, args.approve)
    elif args.reject:
        reject(args.city, args.reject)
    else:
        discover(args.city, limit=args.limit)
