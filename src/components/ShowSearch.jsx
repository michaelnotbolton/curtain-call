import { useState, useEffect, useMemo } from 'react'

const C = {
  gold: '#C9A84C',
  goldLight: '#E2C46A',
  cream: '#F5F0E8',
  ink: '#1A1019',
  ink2: '#231A22',
  burgundy: '#6B1A2A',
}

export default function ShowSearch() {
  const [data, setData] = useState(null)     // null = loading, false = error
  const [query, setQuery] = useState('')

  useEffect(() => {
    const url = `${import.meta.env.BASE_URL}data/shows-dallas.json`
    fetch(url)
      .then((r) => r.json())
      .then(setData)
      .catch(() => setData(false))
  }, [])

  const shows = useMemo(() => {
    if (!data?.shows?.length) return []
    const q = query.trim().toLowerCase()
    if (!q) return data.shows
    return data.shows.filter(
      (s) =>
        s.title?.toLowerCase().includes(q) ||
        s.playwright?.toLowerCase().includes(q) ||
        s.venue?.toLowerCase().includes(q)
    )
  }, [data, query])

  const scraped = data?.scraped_at
    ? new Date(data.scraped_at).toLocaleDateString('en-US', {
        month: 'long',
        day: 'numeric',
        year: 'numeric',
      })
    : null

  return (
    <section
      id="search"
      style={{
        backgroundColor: C.ink2,
        padding: 'clamp(72px, 10vw, 120px) clamp(24px, 6vw, 80px)',
        borderTop: `1px solid rgba(201,168,76,0.15)`,
      }}
    >
      <div style={{ maxWidth: '860px', margin: '0 auto' }}>
        {/* Section label */}
        <p
          className="fade-in"
          style={{
            textAlign: 'center',
            fontSize: '11px',
            letterSpacing: '0.18em',
            textTransform: 'uppercase',
            color: C.gold,
            fontWeight: 600,
            marginBottom: '16px',
          }}
        >
          Live Demo · Dallas, TX
        </p>

        <h2
          className="fade-in delay-100 font-display"
          style={{
            textAlign: 'center',
            fontSize: 'clamp(28px, 4vw, 44px)',
            color: C.cream,
            fontWeight: 700,
            margin: '0 auto 12px',
            lineHeight: 1.15,
          }}
        >
          See it in action.
        </h2>
        <p
          className="fade-in delay-200"
          style={{
            textAlign: 'center',
            color: `${C.cream}70`,
            fontSize: '16px',
            margin: '0 auto 40px',
            lineHeight: 1.6,
          }}
        >
          Real data from Dallas-area theaters — auto-indexed, no manual submissions.
        </p>

        {/* Search input */}
        <div className="fade-in delay-300" style={{ position: 'relative', marginBottom: '32px' }}>
          <span
            aria-hidden="true"
            style={{
              position: 'absolute',
              left: '18px',
              top: '50%',
              transform: 'translateY(-50%)',
              color: `${C.cream}40`,
              fontSize: '18px',
              pointerEvents: 'none',
            }}
          >
            🔍
          </span>
          <input
            type="search"
            placeholder="Search by title, playwright, or venue…"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            style={{
              width: '100%',
              padding: '16px 20px 16px 50px',
              backgroundColor: 'rgba(255,255,255,0.05)',
              border: `1.5px solid rgba(201,168,76,0.3)`,
              borderRadius: '10px',
              color: C.cream,
              fontSize: '16px',
              fontFamily: 'var(--font-body)',
              outline: 'none',
              transition: 'border-color 0.2s',
              boxSizing: 'border-box',
            }}
            onFocus={(e) => (e.target.style.borderColor = C.gold)}
            onBlur={(e) => (e.target.style.borderColor = 'rgba(201,168,76,0.3)')}
          />
        </div>

        {/* Results area */}
        {data === null && <LoadingState />}
        {data === false && <ErrorState />}
        {data && data.show_count === 0 && <EmptyDataState />}
        {data && data.show_count > 0 && (
          <>
            {shows.length === 0 ? (
              <NoResultsState query={query} onClear={() => setQuery('')} />
            ) : (
              <ResultsList shows={shows} query={query} total={data.show_count} />
            )}
            {scraped && (
              <p
                style={{
                  marginTop: '24px',
                  textAlign: 'right',
                  fontSize: '12px',
                  color: `${C.cream}30`,
                  fontStyle: 'italic',
                }}
              >
                Data indexed {scraped} · {data.show_count} shows from {data.venue_count} venues
              </p>
            )}
          </>
        )}
      </div>
    </section>
  )
}

function ResultsList({ shows, query, total }) {
  const displayed = shows.slice(0, 20)
  return (
    <div>
      <p
        style={{
          fontSize: '13px',
          color: `${C.cream}50`,
          marginBottom: '16px',
        }}
      >
        {query
          ? `${shows.length} result${shows.length !== 1 ? 's' : ''} for "${query}"`
          : `${total} shows indexed`}
      </p>
      <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
        {displayed.map((show) => (
          <ShowCard key={show.id || show.title + show.venue} show={show} />
        ))}
      </div>
      {shows.length > 20 && (
        <p style={{ textAlign: 'center', marginTop: '20px', fontSize: '13px', color: `${C.cream}40` }}>
          Showing 20 of {shows.length} results. Refine your search to narrow down.
        </p>
      )}
    </div>
  )
}

function ShowCard({ show }) {
  const dateRange = show.start_date
    ? [
        new Date(show.start_date + 'T12:00:00').toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
        show.end_date
          ? ' – ' + new Date(show.end_date + 'T12:00:00').toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
          : '',
      ].join('')
    : show.showtimes || null

  return (
    <div
      style={{
        backgroundColor: 'rgba(255,255,255,0.03)',
        border: '1px solid rgba(255,255,255,0.07)',
        borderRadius: '10px',
        padding: '18px 20px',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'flex-start',
        gap: '16px',
        flexWrap: 'wrap',
      }}
    >
      <div style={{ flexGrow: 1, minWidth: '200px' }}>
        <div
          style={{
            fontSize: '16px',
            fontWeight: 600,
            color: C.cream,
            marginBottom: '4px',
            fontFamily: 'var(--font-display)',
          }}
        >
          {show.title}
        </div>
        {show.playwright && (
          <div style={{ fontSize: '13px', color: C.gold, marginBottom: '4px' }}>
            by {show.playwright}
          </div>
        )}
        <div style={{ fontSize: '13px', color: `${C.cream}60` }}>
          {show.venue}
          {dateRange && (
            <>
              <span style={{ margin: '0 8px', opacity: 0.4 }}>·</span>
              {dateRange}
            </>
          )}
        </div>
      </div>
      {show.ticket_url && (
        <a
          href={show.ticket_url}
          target="_blank"
          rel="noopener noreferrer"
          style={{
            flexShrink: 0,
            fontSize: '13px',
            color: C.gold,
            border: `1px solid rgba(201,168,76,0.35)`,
            borderRadius: '6px',
            padding: '7px 14px',
            textDecoration: 'none',
            whiteSpace: 'nowrap',
            transition: 'background-color 0.15s',
          }}
          onMouseEnter={(e) => (e.currentTarget.style.backgroundColor = 'rgba(201,168,76,0.1)')}
          onMouseLeave={(e) => (e.currentTarget.style.backgroundColor = 'transparent')}
        >
          Tickets ↗
        </a>
      )}
      <ExtractionBadge method={show.extraction_method} />
    </div>
  )
}

function ExtractionBadge({ method }) {
  if (!method) return null
  const labels = {
    'schema.org': { text: 'Structured data', color: '#4ade80' },
    'css-patterns': { text: 'Pattern match', color: '#60a5fa' },
    'ollama': { text: 'Local AI', color: '#c084fc' },
  }
  const info = labels[method]
  if (!info) return null
  return (
    <span
      title={`Extracted via: ${method}`}
      style={{
        fontSize: '10px',
        color: info.color,
        opacity: 0.6,
        whiteSpace: 'nowrap',
        alignSelf: 'flex-start',
        marginTop: '2px',
      }}
    >
      ● {info.text}
    </span>
  )
}

function LoadingState() {
  return (
    <div style={{ textAlign: 'center', padding: '48px 0', color: `${C.cream}40` }}>
      <div style={{ fontSize: '24px', marginBottom: '12px' }}>⧖</div>
      <p style={{ margin: 0, fontSize: '14px' }}>Loading show data…</p>
    </div>
  )
}

function ErrorState() {
  return (
    <div
      style={{
        textAlign: 'center',
        padding: '48px 24px',
        border: '1px dashed rgba(255,255,255,0.1)',
        borderRadius: '10px',
        color: `${C.cream}50`,
      }}
    >
      <p style={{ margin: 0, fontSize: '14px' }}>
        Could not load show data. Run the scraper first.
      </p>
    </div>
  )
}

function EmptyDataState() {
  return (
    <div
      style={{
        textAlign: 'center',
        padding: '56px 24px',
        border: '1px dashed rgba(201,168,76,0.2)',
        borderRadius: '12px',
      }}
    >
      <div style={{ fontSize: '32px', marginBottom: '16px' }}>🎭</div>
      <p
        style={{
          margin: '0 0 8px',
          fontSize: '16px',
          fontWeight: 600,
          color: `${C.cream}cc`,
        }}
      >
        No data yet — scraper hasn't run.
      </p>
      <p style={{ margin: 0, fontSize: '14px', color: `${C.cream}50` }}>
        Run{' '}
        <code
          style={{
            backgroundColor: 'rgba(255,255,255,0.08)',
            padding: '2px 6px',
            borderRadius: '4px',
            fontSize: '12px',
          }}
        >
          python3 -m scraper.scrape
        </code>{' '}
        then rebuild to see live Dallas shows here.
      </p>
    </div>
  )
}

function NoResultsState({ query, onClear }) {
  return (
    <div style={{ textAlign: 'center', padding: '40px 0', color: `${C.cream}50` }}>
      <p style={{ margin: '0 0 12px', fontSize: '15px' }}>
        No shows match <em>"{query}"</em>
      </p>
      <button
        onClick={onClear}
        style={{
          background: 'none',
          border: `1px solid rgba(201,168,76,0.3)`,
          color: C.gold,
          borderRadius: '6px',
          padding: '6px 14px',
          fontSize: '13px',
          cursor: 'pointer',
          fontFamily: 'var(--font-body)',
        }}
      >
        Clear search
      </button>
    </div>
  )
}
