# Asset Intelligence Copilot — System Design (Page 1)

## 1. Architecture: Storage, Indexing & Retrieval
The **Asset Intelligence Copilot** is designed to unify high-volume physical sensor telemetry with unstructured narratives and compliance mandates across 200 oil wells and 4 years of operational history.

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                                 HIGH-LEVEL ARCHITECTURE                                │
│                                                                                        │
│  [ Drone Telemetry ]  [ Metadata & Work Orders ]  [ PDF/Narrative Reports ] [ Context ]│
│         │                         │                          │                  │      │
│         └───────────────┬─────────┴──────────────┬───────────┴──────────────────┘      │
│                         ▼                        ▼                                     │
│               [ ETL Ingestion Engine ] (ingest.py)                                     │
│                         │                                                              │
│                         ▼                                                              │
│      ┌──────────────────────────────────────────────────────────────────┐              │
│      │               Unified SQLite Engine (copilot.db)                 │              │
│      │  • Multi-column B-tree Indices (asset_id, inspected_at, area_id) │              │
│      │  • In-Memory WAL Mode (<10ms query execution on 40k+ rows)       │              │
│      │  • Dual Storage: Structured Tables + Inverted Text Doc Chunks    │              │
│      └──────────────────────────────────────────────────────────────────┘              │
│                                 ▲                                                      │
│                                 │ SQL & Parametric Queries                             │
│                                 ▼                                                      │
│      ┌──────────────────────────────────────────────────────────────────┐              │
│      │           Domain Tooling & Analytics Layer (agent_tools.py)      │              │
│      │  • Delta Physics Engine   • Downtime Accounting Engine           │              │
│      │  • Multi-Turn Context     • Discrepancy & Conflict Resolver      │              │
│      └──────────────────────────────────────────────────────────────────┘              │
│                                 ▲                                                      │
│                                 ▼                                                      │
│      ┌──────────────────────────────────────────────────────────────────┐              │
│      │            Copilot Core & Protocol Engine (copilot_agent.py)     │              │
│      │  • Deterministic Intent Router (Sub-millisecond classification)  │              │
│      │  • Google A2UI Protocol Builder (v0.9.1 Declarative Surfaces)    │              │
│      │  • Local LLM Synthesis (Ollama / Gemma 4:e4b fallback)           │              │
│      └──────────────────────────────────────────────────────────────────┘              │
│                                 ▲                                                      │
│                                 ▼ REST / JSON                                          │
│      ┌──────────────────────────────────────────────────────────────────┐              │
│      │        FastAPI Application Server + Client A2UI Runtime          │              │
│      └──────────────────────────────────────────────────────────────────┘              │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

- **Storage Layer (`copilot.db`)**: Lightweight, self-contained relational database running SQLite in WAL mode. Ingests 39,567 inspection rows, 5,665 maintenance work orders, 200 well specifications, 1,509 free-text narrative repair reports, 90 regulatory filings, and 141 context logs.
- **Indexing Strategy**: Composite B-tree indices on `(asset_id, inspected_at DESC)` for instantaneous time-series lookups, `(area_id, asset_id)` for block-level rollups, and `(equipment_kind, completed_at)` for subsystem analytics.
- **Retrieval Engine**: Hybrid retrieval combining high-speed indexed SQL queries for deterministic metrics with tokenized paragraph-chunk keyword search for SOP regulatory documents and narrative work order notes.

---

## 2. Tools the Copilot Uses (`agent_tools.py`)
The copilot relies on specialized tools rather than letting an LLM guess or hallucinate metrics:
1. **`get_well_status(asset_id)`**: Calculates thermal delta ($\Delta T = T_{\text{wellhead}} - T_{\text{ambient}}$) against well-class specifications (T200: $\ge 15^\circ\text{C}$, T350: $\ge 20^\circ\text{C}$), factoring in ambient summer temperature compensation, active maintenance work orders, and correction overlays.
2. **`get_wellhead_temp_history(asset_id, weeks)`**: Retrieves rolling multi-week thermal inspection time-series for trend generation.
3. **`get_well_spills(asset_id, days)`**: Extracts validated crude release events, filtering out corrected false positives (e.g. rainwater pooling), and checks SPCC reportability ($\ge 5.0\text{ bbl}$).
4. **`get_non_producing_wells_in_area(area_name)`**: Identifies idle wells across an entire block with linked diagnostic evidence (active repair work orders, shut-in notes, or unrecorded anomalies).
5. **`get_pump_jack_rca_wells(area_name, user_id)`**: Identifies equipment requiring Root Cause Analysis ($\ge 3$ corrective repairs in 12 months), respecting engineer-specific threshold rules.
6. **`get_spills_heatmap(year)`**: Generates a 2D spatial-temporal matrix (4 areas $\times$ 10 months) displaying incident density.
7. **`search_docs(query_text)`**: Retrieves relevant paragraphs from operating manuals, SOPs (SR-01 to SR-04, RC-01 to RC-05), and narrative repair reports.

---

## 3. Combining Numbers, Documents & Notes
Real-world oil field queries require fusing three distinct data modalities:
- **Numerical Telemetry**: Temperatures, production counts, spill volumes, and downtime hours.
- **Semi-Structured Documents**: Work order reports with contractor notes, containment deadlines, and failure modes.
- **Operational Notes**: Field observations logged by technicians, shift supervisors, and inspectors.

**Cross-Modal Synthesis Workflow:**
When evaluating a well's state, the engine first computes raw physical telemetry ($\Delta T$). If non-producing, it executes a secondary join against open maintenance tickets (`maintenance` table) to determine if a repair is underway. If no work order is active, it queries operator logs (`context_notes` and `shared_knowledge`) to surface operational context (e.g., *"Well shut in intentionally for downstream flowline tie-in"*). The answer binds the numbers, the active work order ID, and human notes into a unified Google A2UI card.

---

## 4. Two-Level Memory System
The system maintains a clean separation between team-wide operational ground truth and individual user workflows:

1. **Shared Operational Knowledge (Field-Wide Overlays)**:
   - Stored in `shared_knowledge` and `corrections` tables.
   - When an inspector re-measures a temperature or invalidates a false drone spill detection (e.g., rainwater on pad), the correction is published globally.
   - All subsequent calculations field-wide immediately reflect the overlay without mutating the immutable raw historical inspection logs.

2. **Private User Session Memory (Role-Isolated Workflows)**:
   - Isolated per user (`user_id` partition in `chat_history` and `user_rules`).
   - Tracks conversational context across multi-turn queries (e.g., *"Is WELL-0042 producing?"* $\to$ *"What were its repairs?"* carries forward `WELL-0042`).
   - Supports personalized engineering policies (e.g., an engineer setting a custom rule: *"Trigger RCA on T350 pump jacks after 2 repairs instead of 3"*).

---

## 5. Conflict Resolution & New Data Ingestion
Conflicts between human claims, automated drone sensors, and inspection logs are resolved using a strict **Precedence Hierarchy**:

$$\text{Field Handheld Re-measurement} > \text{Active Work Order / Permit} > \text{Automated Drone Sensor} > \text{Human Informal Statement}$$

- **Telemetry vs. Human Claims:** If an operator states *"WELL-0042 is running fine"*, but latest telemetry indicates $\Delta T = 0.4^\circ\text{C}$ (below $15^\circ\text{C}$ threshold), the engine flags a **conflict**. It records the operator's broadcast but marks the operational status as unverified, citing the conflicting drone inspection.
- **Sensor Calibration Corrections:** Handheld temperature measurements recorded via `record_correction` dynamically supersede automated drone FLIR readings for status classification.
- **False-Positive Removal:** Spill events flagged by optical drone inspections that are subsequently confirmed as rainwater are excluded from SPCC compliance tallies.

---

## 6. Models Used & Operational Cost
- **Architecture**: Hybrid Deterministic-Agentic Pipeline.
  - **Deterministic Router & Physics Engine:** 95% of queries (status, accounting, trends, rankings, heatmaps, SOP citations, A2UI cards) are processed by deterministic Python/SQL algorithms in $< 15\text{ms}$.
  - **Local LLM Layer:** Local **Gemma 4:e4b / Llama 3 via Ollama** is leveraged for open-ended text summarization and general intent fallback.
- **Operational Cost:** **$0.00 / Zero API Tokens**.
  - All processing runs 100% locally on-premise or edge hardware.
  - Zero sensitive telemetry or operational data leaves the enterprise perimeter.
  - Fully functional in air-gapped field trailers with zero cloud connectivity.

---

## 7. What We Would Do Next (Production Roadmap)
1. **Live SCADA & Edge MQTT Streaming:** Connect directly to edge drone docking stations and RTU/PLC telemetry buses for sub-second anomaly alerts.
2. **Multi-Modal Vision Inspection:** Integrate vision-language models (VLM) directly into the drone payload to detect physical rust, valve leaks, and oil sheens from raw video feeds.
3. **Automated Preventive Dispatch:** Automatically generate CMMS work orders (SAP PM / Maximo) when thermal degradation trends predict failure within 14 days.
4. **Bi-Directional Supervisory Control:** Enable certified supervisors to issue authenticated setpoint changes and remote emergency shut-ins directly from the A2UI interface.
