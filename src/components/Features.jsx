const C = {
  gold: '#C9A84C',
  goldLight: '#E2C46A',
  cream: '#F5F0E8',
  ink: '#1A1019',
  burgundy: '#6B1A2A',
}

const features = [
  {
    icon: '🔍',
    label: 'Universal Search',
    heading: 'Find any show, anywhere in the US.',
    body: "Search by play title or playwright — and soon, by actor. Get real-time showtime results across the country. Filter by distance, date, or genre. See everything on a map so you can discover what’s playing near you right now.",
    tags: ['Title search', 'Playwright search', 'Date & distance filters', 'Map view'],
    roadmap: 'Actor search coming in v2',
  },
  {
    icon: '📓',
    label: 'My Shows',
    heading: 'Your theater history, finally in one place.',
    body: 'Log every production you see — the specific venue, the run dates, your seat, your notes. Each entry captures a particular production, not just a title. Build a personal archive of your nights at the theater, as detailed or as brief as you like.',
    tags: ['Per-production logging', 'Venue & date tracking', 'Personal notes', 'Private or shareable'],
    roadmap: 'Social sharing in v2',
  },
  {
    icon: '📍',
    label: 'Every Stage, Everywhere',
    heading: 'Shows appear automatically — no sign-up required from the theater.',
    body: "Community productions, school musicals, regional houses, college shows — indexed automatically. You don't need to hope that a theater claimed a listing or that someone submitted it. If it's playing anywhere, it should be findable here.",
    tags: ['Community theater', 'School productions', 'College shows', 'Regional houses'],
    roadmap: null,
    highlight: true,
  },
]

export default function Features() {
  return (
    <section
      style={{
        backgroundColor: C.ink,
        padding: 'clamp(72px, 10vw, 120px) clamp(24px, 6vw, 80px)',
      }}
    >
      <div style={{ maxWidth: '1200px', margin: '0 auto' }}>
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
          What We're Building
        </p>
        <h2
          className="fade-in delay-100 font-display"
          style={{
            textAlign: 'center',
            fontSize: 'clamp(30px, 4.5vw, 48px)',
            color: C.cream,
            fontWeight: 700,
            margin: '0 auto 64px',
            maxWidth: '600px',
            lineHeight: 1.15,
          }}
        >
          Three features that fix what's missing.
        </h2>

        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))',
            gap: '28px',
          }}
        >
          {features.map((f, i) => (
            <FeatureCard key={f.label} feature={f} delay={`delay-${(i + 1) * 100}`} />
          ))}
        </div>
      </div>
    </section>
  )
}

function FeatureCard({ feature, delay }) {
  const { icon, label, heading, body, tags, roadmap, highlight } = feature
  return (
    <div
      className={`fade-in ${delay}`}
      style={{
        backgroundColor: highlight ? C.burgundy : 'rgba(255,255,255,0.04)',
        border: highlight
          ? `1.5px solid ${C.gold}50`
          : '1.5px solid rgba(255,255,255,0.08)',
        borderRadius: '14px',
        padding: '36px 32px',
        display: 'flex',
        flexDirection: 'column',
        position: 'relative',
        overflow: 'hidden',
      }}
    >
      {highlight && (
        <div
          aria-hidden="true"
          style={{
            position: 'absolute',
            top: 0,
            right: 0,
            width: '180px',
            height: '180px',
            background: `radial-gradient(circle at top right, ${C.gold}18, transparent 70%)`,
            pointerEvents: 'none',
          }}
        />
      )}

      {/* Icon + label */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: '10px',
          marginBottom: '20px',
        }}
      >
        <span style={{ fontSize: '28px' }}>{icon}</span>
        <span
          style={{
            fontSize: '11px',
            letterSpacing: '0.14em',
            textTransform: 'uppercase',
            color: C.gold,
            fontWeight: 600,
          }}
        >
          {label}
        </span>
      </div>

      <h3
        className="font-display"
        style={{
          fontSize: 'clamp(18px, 2vw, 22px)',
          color: C.cream,
          fontWeight: 700,
          margin: '0 0 14px',
          lineHeight: 1.25,
        }}
      >
        {heading}
      </h3>

      <p
        style={{
          fontSize: '15px',
          lineHeight: 1.75,
          color: highlight ? `${C.cream}cc` : `${C.cream}88`,
          margin: '0 0 24px',
          flexGrow: 1,
        }}
      >
        {body}
      </p>

      {/* Tag chips */}
      <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
        {tags.map((tag) => (
          <span
            key={tag}
            style={{
              fontSize: '12px',
              padding: '4px 10px',
              borderRadius: '100px',
              backgroundColor: 'rgba(201,168,76,0.12)',
              color: C.gold,
              border: `1px solid rgba(201,168,76,0.25)`,
              letterSpacing: '0.02em',
            }}
          >
            {tag}
          </span>
        ))}
      </div>

      {roadmap && (
        <p
          style={{
            marginTop: '16px',
            fontSize: '12px',
            color: `${C.cream}50`,
            fontStyle: 'italic',
          }}
        >
          ✦ {roadmap}
        </p>
      )}
    </div>
  )
}
