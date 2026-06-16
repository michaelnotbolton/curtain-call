import { useEffect, useRef } from 'react'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'

// Approx coordinates for all known Dallas-area venues.
// Keyed by the venue name string that appears in shows-dallas.json.
const VENUE_COORDS = {
  'Bishop Arts Theatre Center':  [32.7468, -96.8349],
  'Ochre House Theater':         [32.8098, -96.7516],
  'Rover Dramawerks':            [33.0198, -96.6989],
  'Stage West':                  [32.7264, -97.3321],
  'The Firehouse Theatre':       [32.7767, -96.7970],
  'Uptown Players':              [32.8228, -96.8100],
  'WaterTower Theatre':          [32.9602, -96.8339],
  'Broadway Dallas':             [32.7869, -96.8013],
  'Theatre Three':               [32.8001, -96.7958],
  'Kitchen Dog Theater':         [32.7788, -96.8765],
  'Second Thought Theatre':      [32.7869, -96.8013],
  'Jubilee Theatre':             [32.7551, -97.3307],
  'Undermain Theatre':           [32.7840, -96.7879],
  'Pocket Sandwich Theatre':     [32.8690, -96.7530],
  'Lyric Stage Dallas':          [32.8000, -96.8050],
  'Richardson Theatre Centre':   [32.9483, -96.7298],
  'Garland Civic Theatre':       [32.9126, -96.6389],
  'Casa Mañana':                 [32.7424, -97.3536],
  'Circle Theatre':              [32.7555, -97.3290],
  'Amphibian Stage':             [32.7457, -97.3580],
  'Hip Pocket Theatre':          [32.7830, -97.4230],
}

const PIN = L.divIcon({
  html: '<div style="width:14px;height:14px;border-radius:50%;background:#C9A84C;border:2.5px solid #1A1019;box-shadow:0 0 8px rgba(201,168,76,0.65)"></div>',
  className: '',
  iconSize: [14, 14],
  iconAnchor: [7, 7],
  popupAnchor: [0, -10],
})

function formatDateRange(show) {
  if (!show.start_date) return show.showtimes || null
  const fmt = (d) => new Date(d + 'T12:00:00').toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
  return show.end_date ? `${fmt(show.start_date)} – ${fmt(show.end_date)}` : fmt(show.start_date)
}

function buildPopup(venue, shows) {
  const rows = shows.map((s) => {
    const dates = formatDateRange(s)
    return `
      <div style="padding:6px 0;border-bottom:1px solid #e5e0d8">
        <div style="font-weight:600;font-size:13px;color:#1A1019">${s.title}</div>
        ${s.playwright ? `<div style="font-size:12px;color:#6B1A2A">by ${s.playwright}</div>` : ''}
        ${dates ? `<div style="font-size:11px;color:#888;margin-top:2px">${dates}</div>` : ''}
      </div>`
  }).join('')

  return `
    <div style="font-family:system-ui,sans-serif;min-width:190px;max-width:240px">
      <div style="font-weight:700;font-size:13px;color:#6B1A2A;margin-bottom:4px;padding-bottom:6px;border-bottom:2px solid #C9A84C">${venue}</div>
      ${rows}
    </div>`
}

export default function ShowMap({ shows }) {
  const containerRef = useRef(null)
  const mapRef = useRef(null)
  const layersRef = useRef(null)

  // Init map once
  useEffect(() => {
    if (mapRef.current) return
    const map = L.map(containerRef.current, {
      center: [32.85, -96.97],
      zoom: 10,
      zoomControl: true,
    })
    L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> &copy; <a href="https://carto.com/">CARTO</a>',
      maxZoom: 19,
    }).addTo(map)
    layersRef.current = L.layerGroup().addTo(map)
    mapRef.current = map
    return () => {
      map.remove()
      mapRef.current = null
    }
  }, [])

  // Re-plot markers whenever filtered shows change
  useEffect(() => {
    if (!mapRef.current || !layersRef.current) return
    layersRef.current.clearLayers()

    const byVenue = {}
    shows.forEach((s) => {
      if (!byVenue[s.venue]) byVenue[s.venue] = []
      byVenue[s.venue].push(s)
    })

    const plotted = []
    Object.entries(byVenue).forEach(([venue, venueShows]) => {
      const coords = VENUE_COORDS[venue]
      if (!coords) return
      L.marker(coords, { icon: PIN })
        .bindPopup(buildPopup(venue, venueShows), { maxWidth: 260 })
        .addTo(layersRef.current)
      plotted.push(coords)
    })

    // Fit map to visible pins when there's a meaningful set
    if (plotted.length > 1) {
      mapRef.current.fitBounds(L.latLngBounds(plotted), { padding: [40, 40], maxZoom: 12 })
    } else if (plotted.length === 1) {
      mapRef.current.setView(plotted[0], 13)
    }
  }, [shows])

  return (
    <div
      ref={containerRef}
      style={{
        height: '440px',
        borderRadius: '10px',
        overflow: 'hidden',
        border: '1px solid rgba(255,255,255,0.07)',
      }}
    />
  )
}
