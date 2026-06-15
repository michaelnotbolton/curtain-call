const C = {
  ink: '#1A1019',
  gold: '#C9A84C',
  goldLight: '#E2C46A',
  cream: '#F5F0E8',
  burgundy: '#6B1A2A',
}

export default function Hero() {
  return (
    <section
      style={{
        minHeight: '100vh',
        backgroundColor: C.ink,
        position: 'relative',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        overflow: 'hidden',
        padding: '80px 24px',
      }}
    >
      {/* Spotlight glow from above */}
      <div
        aria-hidden="true"
        style={{
          position: 'absolute',
          top: 0,
          left: '50%',
          transform: 'translateX(-50%)',
          width: '700px',
          height: '500px',
          background:
            'radial-gradient(ellipse at top, rgba(201,168,76,0.07) 0%, transparent 68%)',
          pointerEvents: 'none',
        }}
      />

      {/* Left curtain edge */}
      <div
        aria-hidden="true"
        style={{
          position: 'absolute',
          top: 0,
          left: 0,
          width: '100px',
          height: '100%',
          background: `linear-gradient(to right, ${C.burgundy}99, transparent)`,
          pointerEvents: 'none',
        }}
      />
      {/* Right curtain edge */}
      <div
        aria-hidden="true"
        style={{
          position: 'absolute',
          top: 0,
          right: 0,
          width: '100px',
          height: '100%',
          background: `linear-gradient(to left, ${C.burgundy}99, transparent)`,
          pointerEvents: 'none',
        }}
      />

      {/* Content */}
      <div
        style={{
          position: 'relative',
          zIndex: 1,
          textAlign: 'center',
          maxWidth: '760px',
          width: '100%',
        }}
      >
        {/* Badge */}
        <div className="fade-in" style={{ marginBottom: '36px' }}>
          <span
            style={{
              border: `1px solid ${C.gold}`,
              color: C.gold,
              padding: '5px 16px',
              borderRadius: '100px',
              fontSize: '11px',
              letterSpacing: '0.14em',
              textTransform: 'uppercase',
              fontFamily: 'var(--font-body)',
              fontWeight: 600,
            }}
          >
            Concept Pitch · In Development
          </span>
        </div>

        {/* Gold rule */}
        <div
          aria-hidden="true"
          style={{
            width: '48px',
            height: '2px',
            backgroundColor: C.gold,
            margin: '0 auto 28px',
          }}
        />

        {/* Title */}
        <h1
          className="fade-in delay-100 font-display"
          style={{
            margin: 0,
            fontSize: 'clamp(52px, 9vw, 100px)',
            lineHeight: 1.02,
            letterSpacing: '-0.02em',
            color: C.cream,
            fontWeight: 700,
          }}
        >
          Curtain Call
        </h1>

        {/* Tagline */}
        <p
          className="fade-in delay-200 font-display"
          style={{
            marginTop: '20px',
            fontSize: 'clamp(18px, 2.5vw, 24px)',
            color: `${C.cream}b3`,
            fontStyle: 'italic',
            fontWeight: 400,
            letterSpacing: '0.02em',
          }}
        >
          Find the show. Remember the night.
        </p>

        {/* Gold rule */}
        <div
          aria-hidden="true"
          style={{
            width: '48px',
            height: '2px',
            backgroundColor: C.gold,
            margin: '28px auto 52px',
          }}
        />

        {/* CTA buttons — disabled / blurred */}
        <div
          className="fade-in delay-300"
          style={{
            display: 'flex',
            gap: '16px',
            justifyContent: 'center',
            flexWrap: 'wrap',
            opacity: 0.45,
            filter: 'blur(0.6px)',
            userSelect: 'none',
            pointerEvents: 'none',
          }}
        >
          <button
            type="button"
            style={{
              backgroundColor: C.gold,
              color: C.ink,
              border: 'none',
              borderRadius: '6px',
              padding: '14px 32px',
              fontSize: '15px',
              fontWeight: 600,
              fontFamily: 'var(--font-body)',
              cursor: 'default',
              letterSpacing: '0.02em',
            }}
          >
            Find a Show
          </button>
          <button
            type="button"
            style={{
              backgroundColor: 'transparent',
              color: C.cream,
              border: `1.5px solid ${C.cream}80`,
              borderRadius: '6px',
              padding: '14px 32px',
              fontSize: '15px',
              fontWeight: 500,
              fontFamily: 'var(--font-body)',
              cursor: 'default',
              letterSpacing: '0.02em',
            }}
          >
            My Shows
          </button>
        </div>

        <p
          className="fade-in delay-400"
          style={{
            marginTop: '20px',
            fontSize: '12px',
            color: `${C.cream}55`,
            letterSpacing: '0.05em',
          }}
        >
          App not yet built — this page pitches the concept
        </p>
      </div>

      {/* Scroll cue */}
      <div
        aria-hidden="true"
        style={{
          position: 'absolute',
          bottom: '36px',
          left: '50%',
          transform: 'translateX(-50%)',
          color: `${C.gold}80`,
          fontSize: '20px',
          animation: 'bounce 2s ease-in-out infinite',
        }}
      >
        ↓
      </div>

      <style>{`
        @keyframes bounce {
          0%, 100% { transform: translateX(-50%) translateY(0); }
          50% { transform: translateX(-50%) translateY(8px); }
        }
      `}</style>
    </section>
  )
}
