# Feature Specification — Curtain Call v1

## Purpose

This document specifies what Curtain Call v1 builds, what it intentionally doesn't build, and what's on the roadmap.

---

## v1 Scope

### 1. Universal Search

**Search inputs:**
- Play title (text search, partial match OK)
- Playwright name (text search)

**Results:**
- List of productions matching the query
- Per result: title, playwright, venue name, city/state, dates, ticket link (if available)
- Distance/date filter controls
- Map view: pin each venue with a show popover on click

**Data source:**
- Aggregator APIs (TodayTix, Eventbrite) for major/mid-size productions
- Curtain Call's own crawl index for local/small productions

**Not in v1:** actor search, genre filter, "similar shows" recommendations

---

### 2. My Shows (Personal Log)

**Log entry fields:**
- Production title (linked to show record if indexed)
- Venue name
- Date attended
- Specific production run (if multiple exist for the same title)
- Seat section (optional free text)
- Notes (open text field, no character limit)
- Public / private toggle

**Account model:**
- Email + password auth; OAuth (Google) as stretch goal
- No social graph in v1 — accounts are for personal use only
- Log entries are private by default

**Suggest a Correction:**
- Any show listing can have a "Suggest a correction" button
- Submits: user's proposed correction + their contact email (optional)
- Goes to a review queue; no automatic edits

---

### 3. Every Stage, Everywhere (Discovery Index)

See `DISCOVERY_ENGINE.md` for technical detail.

**What the index covers in v1:**
- Major productions (via aggregator APIs)
- Named venues crawled from Google Places and Yelp
- AACT and TCG member theaters
- University/college drama department productions
- Any venue discovered via recursive link crawling from the above

**What may not appear:**
- Venues with no web presence
- Productions at non-theater venues (one-off event spaces, churches)
- Shows announced less than 72 hours in advance of crawl cycle

---

## v2 Roadmap

| Feature | Rationale |
|---|---|
| Actor search | High user demand; requires cast data quality from crawl layer |
| Social sharing of log | Share a "My Shows" page publicly; follow friends' logs |
| Show alerts | Notify when a show matching a saved search has new listings |
| Richer production metadata | Director, cast list, runtime, content notes |
| "Seen it" from search results | Quick-log a show directly from search without navigating to My Shows |
| Mobile app | v1 is web only; native app follows once core product is validated |

---

## Explicitly Out of Scope

These are conscious product decisions, not oversights:

| Feature | Why not |
|---|---|
| Venue management dashboard | We're not a tool for theaters. Theaters don't need to sign up. |
| Ticket purchasing | TodayTix and others do this well; we'd rather link than compete |
| Manual show submission (public) | Reduces data quality; encourages gaming; defeats the automation value prop |
| Social ratings / reviews | Showify and Show-Score exist; we'd start a social cold-start problem |
| Mood tracking | GoSeeAShow has this; not a core differentiator for v1 |
| Digital playbills | StagePass does this; different product category |
| Theater-facing promotion tools | Not our market; keep the product focused on the audience |

**Manual editing (limited):** Users can edit their own log entries freely. "Suggest a correction" on indexed show data goes through a review queue — no direct public editing of the shared index.
