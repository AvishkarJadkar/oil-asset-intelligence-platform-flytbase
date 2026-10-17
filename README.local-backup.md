# Asset Intelligence Copilot

An enterprise AI Chat Assistant and Generative Analytics Copilot for oil field operators, built for the FlytBase Hack Day (Hacktoberfest 2026).

Answers plain-English questions about well operations, weekly thermal drone inspections, downtime calculations, SOP compliance, free-text repair containment, and multi-user feedback with evidence citations and inline visuals.

---

## Key Capabilities

1. **Grounded Answers with Citations:** Cites exact inspection IDs (`INS-XXXX-XXXX`), maintenance records (`MNT-XXXX-XXXX`), context notes (`CTX-XXXX-XXXX`), and regulatory SOP sections (`SOP-SR`, `SOP-RC`, `OM-T200`, `OM-T350`).
2. **Inline Generative UI:**
   - **Status Cards:** Real-time production status (active/down) computed from wellhead vs ambient air temperature thresholds, inspector identity, delta metrics, and open alerts.
   - **Interactive Tables:** Filtered downtime, spill summaries, and compliance duties with highlighted breaches.
   - **Line Charts:** 13-week temperature trends (wellhead vs ambient) with marked shut-in points.
   - **Bar Charts:** Comparative downtime rankings across geographic blocks.
   - **Interactive Maps:** Geographic pins showing exact well locations and spill coordinates.
   - **Heatmaps:** Area × Month 2D distributions of verified spills.
3. **Two-Level Memory System:**
   - **Shared Knowledge:** Well status updates, planned workovers, and corrections (e.g., Q12 sensor recalibration, Q13 spill volume adjustment) immediately propagate across all users.
   - **Private Session Memory:** Contextual references (e.g., *"the three wells we discussed yesterday"*) remain strictly scoped to each user and do not leak between operator sessions.
   - **Custom Well-Type Rules:** Operator preferences (e.g., *"RCA after 2 repairs for T350 wells"*) are applied exclusively to the relevant well type.
4. **Honesty About Conflicts:** Surfaces contradictions between sensor data, inspector remarks (*"Pump jack not moving"*), and unconfirmed operator claims (*"WELL-0175 is running fine"*), flagging claims as unconfirmed rather than silently choosing a side.

---

## Architecture & Design

```
┌────────────────────────────────────────────────────────────┐
│                    Web Frontend (SPA)                      │
│   Vanilla JS + Glassmorphic CSS (No bulky node_modules)    │
│   • Generative UI Renderer (Chart.js, Leaflet, Marked)     │
│   • Active User Session Switcher                           │
│   • One-Click Scenario Test Buttons (Q1–Q18)               │
└─────────────────────────────┬──────────────────────────────┘
                              │ REST API (/api/chat, /api/history)
┌─────────────────────────────▼──────────────────────────────┐
│                    FastAPI Backend                         │
│   • CopilotEngine: Semantic routing & domain reasoning     │
│   • Agent Tools: Temp thresholds, downtime (7d/insp),      │
│     SOP deadlines (SR-01 24h, SR-02 4h containment),       │
│     free-text report regex extraction, false-positive cuts │
│   • Local LLM integration: Gemma 4 via Ollama              │
└─────────────────────────────┬──────────────────────────────┘
                              │
┌─────────────────────────────▼──────────────────────────────┐
│                   High-Speed SQLite DB                     │
│   • 200 Wells, 39,567 Inspections, 5,665 Maintenance jobs  │
│   • 1,509 Free-text reports, 141 Context notes, 90 Reg evs │
│   • Corrections & User Rules tables (Auditable overlays)   │
└────────────────────────────────────────────────────────────┘
```

---

## Domain Rules Implemented

- **Production Temperature Rule:**
  - T200 wells: `wellhead_temp_c - ambient_temp_c >= 15.0 °C`
  - T350 wells: `wellhead_temp_c - ambient_temp_c >= 20.0 °C`
  - Idle wellheads solar-heated to >45 °C on hot summer days are correctly recognized as down because only delta matters.
- **Downtime Calculation:**
  - Each non-producing weekly inspection = **7 days** of downtime.
  - Missed inspections add 0 days. `maintenance.downtime_hours` is not confused with field downtime.
- **Spill Reporting (SOP SR-01):**
  - Spills ≥ 5.0 barrels require written regulatory notice within 24 hours of discovery.
- **Containment Limit (SOP SR-02):**
  - Source containment must be completed within 4.0 hours (extracted from free-text maintenance reports).
- **Audit & Invalidation Layer:**
  - False positives (e.g. INS-0001-0070 rainwater) are omitted from spill tallies.
  - User corrections preserve the original value in the audit trail.

---

## Quickstart

### 1. Ingest Data
Parses all fleet metadata, 200 well folders, JSONL records, and markdown reports into `copilot.db`:
```bash
py -3.12 ingest.py
```

### 2. Start the Copilot Server
Launches the FastAPI server and serves the web UI at `http://localhost:8000`:
```bash
py -3.12 server.py
```

### 3. Open the UI
Open your browser to:
```
http://localhost:8000
```
- Switch users via the top-left dropdown (Michael Turner, Jessica Reed, Jake Morales, Laura Simmons, Tyler Hughes).
- Click any quick scenario (Q1 to Q18) in the sidebar to test.

### 4. Run Automated Evaluation Test Suite
Validates all 18 benchmark queries against expected answers:
```bash
py -3.12 test_all_eval_queries.py
```
Outputs `19/19 evaluation scenarios answered successfully with evidence and generative UI`.

---

## Submission Checklist

- [x] **Page 1: System Design** — SQLite storage + RAG free-text regex extraction + audit overlay memory + deterministic domain tools.
- [x] **Page 2: Results** — All 18 scenarios matched with citations and visual types.
- [x] **Interactive UI** — Real-time dark mode chat with StatusCard, Table, LineChart, BarChart, Map, and Heatmap.
- [x] **Ready for Test Dataset** — Drop the test dataset into `sample-data/` and re-run `ingest.py`.
