const C = {
  gold: '#C9A84C',
  cream: '#F5F0E8',
  ink2: '#231A22',
}

export default function TheGap() {
  return (
    <section
      style={{
        backgroundColor: C.ink2,
        padding: 'clamp(72px, 10vw, 120px) clamp(24px, 6vw, 80px)',
        borderTop: `1px solid rgba(201,168,76,0.15)`,
        borderBottom: `1px solid rgba(201,168,76,0.15)`,
      }}
    >
      <div style={{ maxWidth: '1100px', margin: '0 auto' }}>
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
          The Problem
        </p>

        <h2
          className="fade-in delay-100 font-display"
          style={{
            textAlign: 'center',
            fontSize: 'clamp(32px, 5vw, 52px)',
            color: C.cream,
            fontWeight: 700,
            margin: '0 auto 64px',
            maxWidth: '680px',
            lineHeight: 1.15,
          }}
        >
          Theater discovery is broken.
        </h2>

        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))',
            gap: '48px',
          }}
        >
          <ProblemCard
            delay="delay-200"
            icon="🎭"
            heading="Small and local theaters are often left out."
            body="The big platforms spotlight Broadway and major venues. Independent productions, school shows, and community theater are rarely discoverable — even if they're happening right around the corner. You find out about them from flyers at coffee shops, if at all."
          />
          <ProblemCard
            delay="delay-300"
            icon="📖"
            heading="Your theater life has no home."
            body="There's nowhere to keep a real record of what you've seen — which production, which cast, which venue, what struck you. Theater fans keep notes in journals, spreadsheets, or nowhere at all. The memory of a great night fades with nothing to anchor it."
          />
        </div>
      </div>
    </section>
  )
}

function ProblemCard({ delay, icon, heading, body }) {
  return (
    <div
      className={`fade-in ${delay}`}
      style={{
        borderLeft: `3px solid rgba(201,168,76,0.35)`,
        paddingLeft: '28px',
      }}
    >
      <div style={{ fontSize: '32px', marginBottom: '16px' }}>{icon}</div>
      <h3
        className="font-display"
        style={{
          fontSize: 'clamp(20px, 2.5vw, 26px)',
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
          fontSize: '16px',
          lineHeight: 1.75,
          color: `${C.cream}99`,
          margin: 0,
        }}
      >
        {body}
      </p>
    </div>
  )
}
