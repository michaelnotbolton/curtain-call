# Discovery Engine — Technical Pitch

Curtain Call's key differentiator is automatic indexing of small, local, and school productions without requiring theaters to sign up or submit anything. This document outlines how we'd build it.

---

## The Core Problem

The hard part isn't scraping public web pages — that's straightforward. The hard parts are:

1. **Venue discovery** — knowing which URLs to even crawl
2. **Data extraction** — parsing unstructured HTML into structured show data
3. **Freshness** — keeping the index current without over-hammering small sites

---

## Stage 1: Venue Discovery (Seed the URL List)

We build the initial venue list through a layered funnel. Each layer adds more venues, with the hardest-to-find ones (the schools and community halls) coming from recursive expansion.

### Tier 1 — Aggregators (Mid-to-Large Venues)
APIs from existing platforms that already aggregate show data:
- **TodayTix** — major market coverage, structured API
- **Eventbrite** — filter by `category=performing_arts`; broad coverage including community events
- **Goldstar** — discount theater tickets, good regional coverage

These handle Broadway, regional touring, and many mid-size houses automatically. We don't need to crawl them — we pull from their APIs.

### Tier 2 — Local Search Directories (Named Venues)
- **Google Places API** — query `type=theater` across every US city/ZIP code. Surfaces named venues that have claimed a Google listing, including small black box theaters, community stages, and dinner theaters.
- **Yelp Fusion API** — `categories=theatercompanies,performingarts`; strong regional coverage, often surfaces venues that don't appear in Places.

These two tiers together yield most named, permanent venues in the US.

### Tier 3 — Association & Council Directories (Community Theater)
Organizations that maintain member directories of community and school theaters:
- **AACT (American Association of Community Theatre)** — member directory of community theaters by state
- **TCG (Theatre Communications Group)** — professional theater member directory
- **State arts councils** — every US state maintains one; many publish venue/company listings (e.g., Illinois Arts Council, Ohio Arts Council). These are often scrapable static pages.
- **University theater departments** — enumerable via Google dork: `site:.edu "department of theatre"` or similar. Most have a season page listing upcoming productions.

### Tier 4 — Recursive Links Graph (Long Tail)
When we crawl a venue's website, we harvest outbound links to:
- "Our Partners" / "Area Productions" pages
- Local theater guild or coalition pages
- "See other shows in our community" link blocks

Each crawled page seeds 2–5 new venues on average. This is how we reach the long tail — the small theater that doesn't have a Google listing but is linked from three others that do.

### Tier 5 — Structured Event Data (Schema.org Sweep)
Many websites — especially those using WordPress + Events Calendar plugin, Squarespace, or Wix — automatically emit `<script type="application/ld+json">` Event objects. A targeted crawl for this structured data can be run against any domain, requiring no AI. We can discover these venues by:
- Following links from Tier 3/4 sources
- Crawling local newspaper arts sections (which often link to theater event pages)

---

## Stage 2: Extraction Pipeline

Once we have a venue URL, we need to extract structured show data from it. The pipeline tries cheap approaches first and escalates only when needed.

```
Venue URL
    │
    ▼
Fetch HTML (Playwright for JS-rendered pages; raw fetch for static)
    │
    ├── schema.org Event detected? ──YES──▶ Parse directly
    │                                        (free, ~100% accuracy)
    │
    └── NO ──▶ CSS selector heuristics
                  Common theater site templates (5–10 patterns cover
                  the majority of WordPress/Squarespace theater sites)
                  │
                  ├── Matched ──▶ Extract structured data
                  │                (free, high accuracy)
                  │
                  └── No match ──▶ LLM-based extraction
                                   (see cost model below)
                                   │
                                   ├── High confidence ──▶ Auto-insert
                                   └── Low confidence  ──▶ Flag for review queue
                                                            ("Suggest a correction"
                                                             user flow can help here)
```

**Target fields per show**: title, playwright, director, venue, address, dates, times, ticket URL, cast notes (where available).

---

## LLM Extraction — Trade-offs

### Option A: No AI (schema.org + CSS heuristics only)
- **Cost**: Free
- **Coverage**: ~50–65% of theater websites (those with structured data or common templates)
- **Accuracy**: Near-perfect where it works
- **Con**: Misses ~35–50% of sites, skewing toward smaller/older venues — exactly the ones we care about most

### Option B: Cloud small model (Haiku 4.5 or equivalent)
- **Cost**: ~$0.0005 per page (at $0.25/1M input tokens)
- **Coverage**: All sites
- **Accuracy**: ~90–95% for simple event extraction from HTML
- **Pro**: Fast (sub-second), scales easily, no infrastructure to manage
- **Realistic weekly cost at 10K venues**: ~$2–5/week (most sites handled free; only ~30–40% reach the LLM)

### Option C: Local model (Ollama / self-hosted Llama 3.2 3B)
- **Cost**: $0 marginal; requires a server ($6–20/mo VPS or existing hardware)
- **Coverage**: All sites
- **Accuracy**: ~75–85% — noticeably weaker on ambiguous or heavily nested HTML
- **Pro**: No per-call cost; good for high-volume steady-state operation
- **Con**: Slower per request; requires model updates and infra management; harder to scale bursts

### Option D: Cloud mid-tier (Claude Sonnet or GPT-4o)
- **Cost**: ~$0.006+ per page (10–15x Option B)
- **Accuracy**: ~97%+ — handles edge cases much better
- **Verdict**: Overkill for straightforward extraction. Reserve for hard cases only (ambiguous HTML, multi-show pages, foreign language listings).

### Recommended approach
**Hybrid**: Free extraction for schema.org + common templates → Haiku 4.5 for remaining sites → Sonnet only for flagged low-confidence cases. Estimated: $2–5/week at 10K venues, scaling roughly linearly.

---

## Stage 3: Freshness & Staleness

- **Re-crawl schedule**: Active venues weekly; dormant venues monthly
- **Change detection**: Hash the extracted data; only re-process if the page meaningfully changed
- **Show expiry**: Auto-archive shows whose closing date has passed; keep in index for personal log lookups
- **robots.txt compliance**: Always respect; set User-Agent to identify the crawler
- **Rate limiting**: Max 1 request/5 seconds per domain; don't compete with a small theater's limited hosting

---

## Open Risks

| Risk | Mitigation |
|---|---|
| Venues with zero web presence (some church halls, community centers) | User "suggest a venue" flow (minimal — just a URL submission, no full show entry) |
| JS-heavy pages that require full browser rendering | Playwright headless browser for Tier 4+ venues; heavier but necessary for some |
| False positive extractions (wrong title, wrong date) | Confidence scoring + review queue; "Suggest a correction" on every show listing |
| Staleness if a theater updates dates post-crawl | Weekly re-crawl cadence for active venues; "Report outdated info" button |
| Legal gray area | Public event information has been aggregated by search engines without issue; robots.txt compliance and rate limiting keeps us in the "good citizen" bucket |
