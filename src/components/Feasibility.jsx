const C = {
  gold: '#C9A84C',
  cream: '#F5F0E8',
  ink: '#1A1019',
}

const items = [
  {
    title: 'Show search & showtimes',
    confidence: 'Proven',
    color: '#4ade80',
    body: 'Existing APIs and data sources already aggregate major and mid-size venue listings. Integration is standard — this is solved technology.',
  },
  {
    title: 'Playwright & title search',
    confidence: 'Achievable in v1',
    color: '#86efac',
    body: 'Requires a clean production data model with playwright as a first-class field. Technically straightforward once show data is structured correctly.',
  },
  {
    title: 'Map view',
    confidence: 'Standard',
    color: '#4ade80',
    body: 'Leaflet or Mapbox free tier. Any venue with a known address can be pinned. No novel technical work required.',
  },
  {
    title: 'Personal show log',
    confidence: 'Standard',
    color: '#4ade80',
    body: 'User accounts, a log table, and a notes field. No harder than any journaling app. Can be built as a lightweight first feature.',
  },
  {
    title: 'Automated local discovery',
    confidence: 'Novel · Tractable',
    color: C.gold,
    body: 'The interesting engineering challenge. Similar in kind to how search engines index small business sites — layered approach using public directories, structured data, and targeted extraction for sites that need it. Affordable at scale.',
  },
  {
    title: 'Actor search',
    confidence: 'v2 Roadmap',
    color: '#c084fc',
    body: 'Requires per-production cast data. Feasible once a large enough show index exists, but dependent on data quality from the discovery layer.',
  },
]

export default function Feasibility() {
  return (
    <section
      style={{
        backgroundColor: C.ink,
        padding: 'clamp(72px, 10vw, 120px) clamp(24px, 6vw, 80px)',
        borderTop: `1px solid rgba(201,168,76,0.15)`,
      }}
    >
      <div style={{ maxWidth: '1100px', margin: '0 auto' }}>
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
          Technical Confidence
        </p>
        <h2
          className="fade-in delay-100 font-display"
          style={{
            textAlign: 'center',
            fontSize: 'clamp(28px, 4vw, 44px)',
            color: C.cream,
            fontWeight: 700,
            margin: '0 auto 16px',
            lineHeight: 1.15,
          }}
        >
          We can build this.
        </h2>
        <p
          className="fade-in delay-200"
          style={{
            textAlign: 'center',
            color: `${C.cream}70`,
            fontSize: '16px',
            maxWidth: '540px',
            margin: '0 auto 64px',
            lineHeight: 1.7,
          }}
        >
          Most of these features are standard engineering work. One is genuinely novel — and that novelty is the competitive moat.
        </p>

        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))',
            gap: '20px',
          }}
        >
          {items.map((item, i) => (
            <FeasibilityCard
              key={item.title}
              item={item}
              delay={`delay-${Math.min((i + 1) * 100, 400)}`}
            />
          ))}
        </div>
      </div>
    </section>
  )
}

function FeasibilityCard({ item, delay }) {
  const { title, confidence, color, body } = item
  return (
    <div
      className={`fade-in ${delay}`}
      style={{
        backgroundColor: 'rgba(255,255,255,0.03)',
        border: '1px solid rgba(255,255,255,0.07)',
        borderRadius: '12px',
        padding: '28px 24px',
      }}
    >
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'flex-start',
          gap: '12px',
          marginBottom: '12px',
        }}
      >
        <h3
          style={{
            margin: 0,
            fontSize: '15px',
            fontWeight: 600,
            color: `${C.cream}ee`,
            lineHeight: 1.3,
          }}
        >
          {title}
        </h3>
        <span
          style={{
            fontSize: '11px',
            fontWeight: 700,
            color,
            whiteSpace: 'nowrap',
            letterSpacing: '0.06em',
            flexShrink: 0,
            marginTop: '2px',
          }}
        >
          {confidence}
        </span>
      </div>
      <p
        style={{
          margin: 0,
          fontSize: '14px',
          lineHeight: 1.7,
          color: `${C.cream}60`,
        }}
      >
        {body}
      </p>
    </div>
  )
}
