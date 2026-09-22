# ORCA — Marine EcOsystem Reasoning with Collaborative Agents
### Smart India Hackathon 2026 - Problem Statement PS 26176

A multi-agent conversational copilot for Indian coastal fishermen and the Coast Guard,
fusing INCOIS Potential Fishing Zone advisories, ISRO Oceansat-3 ocean color/thermal
data, IMD weather bulletins, free Open-Meteo marine telemetry, and Marine Regions
boundary data into a single safety-first split-screen interface — **on one port, with
zero paid APIs, and grounded in your real location.**

---

## Start it (one command)

```bash
python run.py
```

That's it. On first run this will `npm install` and `npm run build` the frontend
automatically (subsequent runs skip straight to serving, since the build is cached),
then start serving the **entire platform on `http://localhost:8000`** — UI and API,
one process, one port.

```bash
# Windows, macOS, Linux — same command everywhere
python run.py

# Options:
python run.py --port 3000     # use a different port
python run.py --rebuild       # force a fresh frontend build (after editing apps/web3)
python run.py --skip-build    # start the API only, skip the frontend build check
```

Requires **Python 3.9+** and **Node.js 18+** (for the one-time frontend build) on
PATH. No API keys, no paid tier, no signup, required for any of it to work —
**except the map**, which now uses Google Maps and needs a free API key (see next
section). Everything else (chat, agents, weather, geofencing) works with zero keys.

---


## What changed in this revision (single-port rebuild)

**Latest fix (this pass): replaced the map entirely.** The Leaflet + OpenStreetMap
map would visibly "go crazy" — panning wildly across the whole country and briefly
shrinking to a small floating tile block — on almost any re-render. The root cause
was Leaflet's `flyTo()`, which deliberately zooms *way* out and back in for any
long-distance camera move (it's designed to mimic a "flying" transition), combined
with container-resize/transform edge cases in Leaflet's tile-pane positioning. Per
your request, the map now uses the **Google Maps JavaScript API** instead:
`map.panTo()` + `map.setZoom()` do a clean smooth pan for nearby moves and a direct
instant jump for far ones, with none of the zoom-out arc or positioning glitches.
This does mean a free API key is now required for the map specifically — see
"Getting a free Google Maps API key" above for the two-minute setup and exactly
where the key goes. Every other part of the platform (chat, all 5 agents, weather,
geofencing, multilingual support) still needs zero keys.

This is a from-scratch architectural rebuild of the previous two-port version
(`:8000` FastAPI + `:3002` Next.js dev server), per the new non-negotiable
requirements. Concretely:

1. **Single-port (Option B — FastAPI static mount).** `apps/web3` is now built with
   Next.js `output: "export"` (static HTML/JS/CSS, no Node server needed at
   runtime) and served directly by FastAPI via `StaticFiles(html=True)` mounted at
   `/`, with the API staying at `/api/v1/*` on the exact same process and port. No
   proxy, no `concurrently`, no second terminal. `run.py` is the one-command
   orchestrator that builds-if-needed and then launches this single process.
2. **Real geolocation grounding, not simulated coordinates.**
   `components/providers/LocationProvider.tsx` calls
   `navigator.geolocation.getCurrentPosition` on first load. Every chat query and
   every diagnostic-dashboard "Use my location" button sends that REAL `(lat, lon)`
   to the backend (`user_lat`/`user_lon` on `/api/v1/chat`), which
   `orchestration/intent.py` prioritizes correctly:
   explicit coordinates typed in the query → a named place mentioned in the query →
   the user's real grounded position → a last-resort default (Kochi) only if truly
   nothing else is available. If geolocation is denied or unsupported, a persistent
   harbour selector (top-right, `LocationBadge`) lets the user pick Kochi,
   Visakhapatnam, Chennai, Veraval, Mangalore, or Rameswaram instead — never a
   silently-hallucinated position.
3. **Genuinely free, zero-key live weather.** Added
   `data_sources/open_meteo_client.py` (Open-Meteo's Forecast + Marine APIs, no API
   key, ever) as the **primary** live telemetry source for the Weather Intelligence
   Agent, replacing the previous hard dependency on an `OPENWEATHERMAP_API_KEY` for
   live data. OpenWeatherMap is kept only as an optional secondary cross-check,
   used solely if a key happens to be configured — never required.
4. **Map provider history.** Started on CartoDB dark tiles (hit a licensing
   watermark requiring a key), moved to plain OpenStreetMap tiles with a CSS dark
   filter (hit the Leaflet `flyTo()` jumpiness described above), and now uses the
   Google Maps JavaScript API, which resolved both issues at once — see "Getting a
   free Google Maps API key" above.
5. **No dead UI elements.** Every map layer toggle (PFZ / IMBL / MPA), every
   species filter, and every "Use my location" button was click-tested against the
   live backend during this rebuild (see "What was tested" below) — none of them
   were already fake, but this was explicitly re-verified rather than assumed.
   [open_mateo_client](https://github.com/techiedanish/ORCA-marine-intelligence/blob/main/apps/api/data_sources/open_meteo_client.py)

---

## Repository layout

```
SIH26/
├── run.py                    # the one command — builds + serves everything
├── package.json, turbo.json   # npm workspace root (optional, for `npm run dev:web3` iteration)
├── apps/
│   ├── api/                    # FastAPI backend (Python) — also serves the built UI
│   │   ├── main.py                        # mounts apps/web3/out at "/", API at "/api/v1"
│   │   ├── core/                          # Settings, CitationTracker
│   │   ├── data_sources/
│   │   │   ├── open_meteo_client.py        # NEW — free, zero-key primary weather/marine telemetry
│   │   │   ├── openweather_client.py       # optional secondary, key-gated
│   │   │   ├── imd_client.py, incois_client.py, eez_boundaries.py
│   │   ├── geo/                           # geofence.py (IMBL/MPA), route_planner.py
│   │   ├── agents/                        # the 5 domain agents
│   │   ├── orchestration/                 # supervisor.py, intent.py (location priority), language.py, gemini_engine.py
│   │   ├── data/                          # embedded GeoJSON (13-pt IMBL, EEZ, 4 MPAs), harbours, snapshots
│   │   └── api/v1/endpoints/              # health, system, marine, weather, geospatial, orca, chat
│   └── web3/                    # Next.js 14 App Router frontend (statically exported)
│       ├── next.config.mjs                # output: "export", trailingSlash: true
│       ├── app/
│       │   ├── layout.tsx, page.tsx        # split-screen copilot (no build-time font network calls)
│       │   └── agents/{discovery,analytics,weather,risk}/page.tsx
│       ├── components/
│       │   ├── chat/    (ChatInterface, ThoughtAccordion, VoiceInput, ResponseCards)
│       │   ├── map/     (MarineMap — Google Maps JS API, dark theme, GeoJSON overlays)
│       │   ├── nav/     (TopNav, LocationBadge)
│       │   └── providers/ (LocationProvider — real geolocation + harbour fallback)
│       └── lib/         (api.ts, i18n.ts, types.ts, harbours.ts)
```

---

## Known simplifications (given demo scope)

- IMBL/EEZ/MPA coordinates in `apps/api/data/eez/india_eez.json` are
  illustrative-fidelity, not the certified survey-grade Marine Regions dataset —
  swap the file for a real one and everything downstream (distance calc,
  containment, map rendering) works unchanged.
- Open-Meteo's marine (wave height) grid doesn't cover every point right up
  against the coastline; when it returns nothing for a given coordinate, wave
  height is shown as unavailable rather than fabricated, while wind/pressure
  (from the separate, broader-coverage forecast endpoint) still populate normally.
- Route planning (`geo/route_planner.py`) uses a fast waypoint-nudging heuristic
  rather than a full visibility-graph/A* solver — adequate for demo purposes, not
  for operational navigation.
- The rule-based intent parser (`orchestration/intent.py`) handles the quick-starter
  question shapes well; `gemini_engine.extract_intent_llm` is available as a
  drop-in upgrade for novel phrasings once a real `GEMINI_API_KEY` is configured,
  but isn't called by default so the demo stays fast and fully offline-capable.

