const C = {
  gold: '#C9A84C',
  cream: '#F5F0E8',
  ink: '#1A1019',
  ink2: '#231A22',
  burgundy: '#6B1A2A',
}

const CHECK = (
  <span title="Yes" style={{ color: '#4ade80', fontSize: '18px', fontWeight: 700 }}>
    ✓
  </span>
)
const CROSS = (
  <span title="No" style={{ color: 'rgba(245,240,232,0.25)', fontSize: '18px' }}>
    ✗
  </span>
)
const ROADMAP = (
  <span
    style={{
      color: C.gold,
      fontSize: '13px',
      fontStyle: 'italic',
      opacity: 0.85,
    }}
  >
    Roadmap
  </span>
)

const dim = (text) => (
  <span style={{ color: 'rgba(245,240,232,0.45)', fontSize: '13px', fontStyle: 'italic' }}>
    {text}
  </span>
)

const rows = [
  {
    group: 'Discovery',
    features: [
      { label: 'Search by play title',             cc: CHECK,   gsaw: CHECK,            showify: CHECK,  sp: CHECK },
      { label: 'Search by playwright',             cc: CHECK,   gsaw: CROSS,            showify: CROSS,  sp: CROSS },
      { label: 'Search by actor',                  cc: ROADMAP, gsaw: CROSS,            showify: CROSS,  sp: CROSS },
      { label: 'Location / distance filter',       cc: CHECK,   gsaw: dim('City / ZIP'), showify: CROSS,  sp: dim('Limited') },
      { label: 'Map view',                         cc: CHECK,   gsaw: CROSS,            showify: CROSS,  sp: CROSS },
    ],
  },
  {
    group: 'Coverage',
    features: [
      { label: 'Small & local venue coverage',     cc: <Pill>Automated</Pill>, gsaw: dim('Community submitted'), showify: CROSS, sp: CROSS },
      { label: 'School / community productions',   cc: <Pill>Automated</Pill>, gsaw: dim('If submitted'),         showify: CROSS, sp: CROSS },
    ],
  },
  {
    group: 'Personal Tracking',
    features: [
      { label: 'Personal show log',                cc: CHECK,   gsaw: CHECK,            showify: dim('Social only'), sp: dim('Playbill') },
      { label: 'Per-production notes & venue',     cc: CHECK,   gsaw: CHECK,            showify: dim('Limited'),     sp: CROSS },
      { label: 'Suggest a correction',             cc: CHECK,   gsaw: CROSS,            showify: CROSS,             sp: CROSS },
    ],
  },
  {
    group: 'Out of Scope',
    features: [
      { label: 'Venue management tools',           cc: dim('By design'), gsaw: CHECK,  showify: CROSS,             sp: CROSS },
      { label: 'Ticket purchasing',                cc: dim('By design'), gsaw: dim('3rd-party links'), showify: CROSS, sp: CROSS },
      { label: 'Social ratings / reviews',         cc: dim('v1'),        gsaw: CROSS,  showify: CHECK,             sp: CROSS },
      { label: 'Digital playbills',                cc: CROSS,            gsaw: CROSS,  showify: CROSS,             sp: CHECK },
    ],
  },
]

function Pill({ children }) {
  return (
    <span
      style={{
        backgroundColor: 'rgba(201,168,76,0.15)',
        border: '1px solid rgba(201,168,76,0.35)',
        color: C.gold,
        fontSize: '12px',
        padding: '3px 10px',
        borderRadius: '100px',
        fontWeight: 600,
        letterSpacing: '0.04em',
        whiteSpace: 'nowrap',
      }}
    >
      {children}
    </span>
  )
}

export default function ComparisonTable() {
  return (
    <section
      style={{
        backgroundColor: C.ink2,
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
          How We Compare
        </p>
        <h2
          className="fade-in delay-100 font-display"
          style={{
            textAlign: 'center',
            fontSize: 'clamp(28px, 4vw, 44px)',
            color: C.cream,
            fontWeight: 700,
            margin: '0 auto 56px',
            lineHeight: 1.15,
          }}
        >
          What the others don't do.
        </h2>

        <div className="fade-in delay-200" style={{ overflowX: 'auto' }}>
          <table
            style={{
              width: '100%',
              borderCollapse: 'collapse',
              fontSize: '14px',
              minWidth: '640px',
            }}
          >
            <thead>
              <tr>
                <th
                  style={{
                    textAlign: 'left',
                    padding: '12px 16px 20px 0',
                    color: `${C.cream}55`,
                    fontWeight: 500,
                    fontSize: '12px',
                    letterSpacing: '0.08em',
                    borderBottom: `1px solid rgba(255,255,255,0.1)`,
                    width: '40%',
                  }}
                >
                  Feature
                </th>
                {['Curtain Call', 'GoSeeAShow', 'Showify', 'StagePass'].map((col) => (
                  <th
                    key={col}
                    style={{
                      textAlign: 'center',
                      padding: '12px 12px 20px',
                      fontWeight: 700,
                      fontSize: '13px',
                      borderBottom: `1px solid rgba(255,255,255,0.1)`,
                      color: col === 'Curtain Call' ? C.gold : `${C.cream}70`,
                      backgroundColor:
                        col === 'Curtain Call' ? 'rgba(201,168,76,0.06)' : 'transparent',
                      borderRadius: col === 'Curtain Call' ? '6px 6px 0 0' : '0',
                    }}
                  >
                    {col}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {rows.map((group) => (
                <>
                  <tr key={group.group + '-header'}>
                    <td
                      colSpan={5}
                      style={{
                        padding: '24px 0 8px',
                        fontSize: '10px',
                        letterSpacing: '0.16em',
                        textTransform: 'uppercase',
                        color: `${C.cream}40`,
                        fontWeight: 700,
                      }}
                    >
                      {group.group}
                    </td>
                  </tr>
                  {group.features.map((row, ri) => (
                    <tr
                      key={row.label}
                      style={{
                        backgroundColor:
                          ri % 2 === 0 ? 'rgba(255,255,255,0.015)' : 'transparent',
                      }}
                    >
                      <td
                        style={{
                          padding: '13px 16px 13px 0',
                          color: `${C.cream}cc`,
                          borderBottom: `1px solid rgba(255,255,255,0.05)`,
                        }}
                      >
                        {row.label}
                      </td>
                      {[row.cc, row.gsaw, row.showify, row.sp].map((val, ci) => (
                        <td
                          key={ci}
                          style={{
                            textAlign: 'center',
                            padding: '13px 12px',
                            borderBottom: `1px solid rgba(255,255,255,0.05)`,
                            backgroundColor:
                              ci === 0 ? 'rgba(201,168,76,0.04)' : 'transparent',
                          }}
                        >
                          {val}
                        </td>
                      ))}
                    </tr>
                  ))}
                </>
              ))}
            </tbody>
          </table>
        </div>

        <p
          className="fade-in"
          style={{
            marginTop: '24px',
            fontSize: '12px',
            color: `${C.cream}35`,
            textAlign: 'right',
            fontStyle: 'italic',
          }}
        >
          Competitor features based on public documentation, June 2026.
        </p>
      </div>
    </section>
  )
}
