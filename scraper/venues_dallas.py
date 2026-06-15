"""
Dallas-area theater venues seed list.
Each entry has a human name and the URL most likely to list their current/upcoming shows.
The scraper handles 404s and timeouts gracefully, so imprecise URLs are OK —
they just produce 0 results for that venue rather than crashing.
"""

VENUES = [
    # ── Major regional theaters ──────────────────────────────────────────
    {"name": "Dallas Theater Center",        "url": "https://www.dallastheatercenter.org/season/"},
    {"name": "WaterTower Theatre",           "url": "https://www.watertowertheatre.org/shows"},
    {"name": "AT&T Performing Arts Center",  "url": "https://www.attpac.org/on-stage/"},

    # ── Mid-size and specialty ───────────────────────────────────────────
    {"name": "Theater Three",                "url": "https://www.theater3dallas.com/shows/"},
    {"name": "Kitchen Dog Theater",          "url": "https://www.kitchendogtheater.org/shows/"},
    {"name": "Second Thought Theatre",       "url": "https://www.secondthoughttheatre.com/productions"},
    {"name": "Jubilee Theatre",              "url": "https://www.jubileetheatre.org/productions"},
    {"name": "Uptown Players",               "url": "https://www.uptownplayers.org/shows"},
    {"name": "Undermain Theatre",            "url": "https://www.undermain.org/productions"},
    {"name": "Bishop Arts Theatre Center",   "url": "https://www.bishopartstheatre.org/performances"},
    {"name": "Ochre House Theater",          "url": "https://www.ochrehouse.org/shows"},
    {"name": "Nouveau 47 Theatre",           "url": "https://www.nouveau47.com/"},
    {"name": "Firehouse Theatre",            "url": "https://www.firehousetheatre.com/productions"},
    {"name": "Theatre Britain",              "url": "https://www.theatrebritain.com/"},
    {"name": "Pocket Sandwich Theatre",      "url": "https://www.pocketsandwich.com/shows/"},

    # ── Community and suburban ───────────────────────────────────────────
    {"name": "Rover Dramawerks",             "url": "https://www.roverdramawerks.com/shows/"},
    {"name": "Richardson Theatre Centre",    "url": "https://www.richardsontheatrecentre.org/"},
    {"name": "Garland Civic Theatre",        "url": "https://www.garlandarts.com/theatre"},
    {"name": "Allen Community Theatre",      "url": "https://www.allencommunitytheatre.org/shows"},
    {"name": "Mesquite Arts Center",         "url": "https://www.mesquitearts.com/shows"},

    # ── Fort Worth area ──────────────────────────────────────────────────
    {"name": "Stage West",                   "url": "https://www.stagewest.org/productions"},
    {"name": "Casa Mañana",                  "url": "https://casamanana.org/shows/"},
    {"name": "Circle Theatre",               "url": "https://www.circletheatre.com/season"},
    {"name": "Lyric Stage Fort Worth",       "url": "https://www.lyricstage.com/season"},
    {"name": "Hip Pocket Theatre",           "url": "https://www.hippocket.org/productions"},
]
