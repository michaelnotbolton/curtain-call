const C = {
  gold: '#C9A84C',
  cream: '#F5F0E8',
  ink2: '#231A22',
  burgundy: '#6B1A2A',
}

export default function Footer() {
  return (
    <footer
      style={{
        backgroundColor: C.ink2,
        borderTop: `1px solid rgba(201,168,76,0.15)`,
        padding: 'clamp(48px, 6vw, 72px) clamp(24px, 6vw, 80px)',
      }}
    >
      <div
        style={{
          maxWidth: '1100px',
          margin: '0 auto',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          gap: '20px',
          textAlign: 'center',
        }}
      >
        {/* Wordmark */}
        <div
          className="font-display"
          style={{
            fontSize: '28px',
            color: C.gold,
            fontWeight: 700,
            letterSpacing: '-0.01em',
          }}
        >
          Curtain Call
        </div>

        {/* Tagline */}
        <p
          className="font-display"
          style={{
            margin: 0,
            color: `${C.cream}55`,
            fontStyle: 'italic',
            fontSize: '15px',
          }}
        >
          Find the show. Remember the night.
        </p>

        {/* Thin divider */}
        <div
          aria-hidden="true"
          style={{
            width: '40px',
            height: '1px',
            backgroundColor: `${C.gold}40`,
          }}
        />

        {/* Disclaimer */}
        <p
          style={{
            margin: 0,
            fontSize: '13px',
            color: `${C.cream}45`,
            maxWidth: '480px',
            lineHeight: 1.65,
          }}
        >
          Curtain Call is a concept pitch. The app is not yet built. This page
          is not accepting show submissions and is not a tool for venues or
          theater companies.
        </p>

        {/* GitHub link */}
        <a
          href="https://github.com/michaelnotbolton/curtain-call"
          target="_blank"
          rel="noopener noreferrer"
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: '8px',
            color: C.gold,
            fontSize: '13px',
            textDecoration: 'none',
            opacity: 0.7,
            transition: 'opacity 0.2s',
            letterSpacing: '0.04em',
          }}
          onMouseEnter={(e) => (e.currentTarget.style.opacity = 1)}
          onMouseLeave={(e) => (e.currentTarget.style.opacity = 0.7)}
        >
          <GithubIcon />
          michaelnotbolton/curtain-call
        </a>

        <p
          style={{
            margin: 0,
            fontSize: '11px',
            color: `${C.cream}25`,
            letterSpacing: '0.06em',
          }}
        >
          © 2026 Curtain Call
        </p>
      </div>
    </footer>
  )
}

function GithubIcon() {
  return (
    <svg
      width="16"
      height="16"
      viewBox="0 0 24 24"
      fill="currentColor"
      aria-hidden="true"
    >
      <path d="M12 2C6.477 2 2 6.484 2 12.017c0 4.425 2.865 8.18 6.839 9.504.5.092.682-.217.682-.483 0-.237-.008-.868-.013-1.703-2.782.605-3.369-1.343-3.369-1.343-.454-1.158-1.11-1.466-1.11-1.466-.908-.62.069-.608.069-.608 1.003.07 1.531 1.032 1.531 1.032.892 1.53 2.341 1.088 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.988 1.029-2.688-.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.026A9.564 9.564 0 0112 6.844c.85.004 1.705.115 2.504.337 1.909-1.296 2.747-1.027 2.747-1.027.546 1.379.202 2.398.1 2.651.64.7 1.028 1.595 1.028 2.688 0 3.848-2.339 4.695-4.566 4.943.359.309.678.92.678 1.855 0 1.338-.012 2.419-.012 2.747 0 .268.18.58.688.482A10.019 10.019 0 0022 12.017C22 6.484 17.522 2 12 2z" />
    </svg>
  )
}
