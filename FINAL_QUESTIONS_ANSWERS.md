# Official Evaluation Answers: Final 11 Questions

**Dataset:** Test Dataset (600 wells, 7 Operational Areas, 4 Production Teams)
**Effective Date (Today):** 15 Jan 2027
**Generated:** 2026-10-17 17:50:30
**Platform:** Asset Intelligence Copilot with Google A2UI Declarative Interface

---

## Q1. Reservoir Pressure
**Speaker:** `Michael Turner` (Production Supervisor, Northeast Production)
**Query:** *"All our wells feed one reservoir. Map the reservoir pressure across the field from the pressure data."*

### Reservoir Pressure Mapping Assessment

**Notice on Field Telemetry:** **Reservoir pressure cannot be mapped from the dataset.**

- **Available Fleet Telemetry:** Our weekly drone and manual asset inspections monitor **thermal FLIR temperatures** (`wellhead_temp_c`, `ambient_temp_c`, `temp_diff`), **operating production status** (`producing = 1/0`), and **oil spill evidence**.
- **Telemetry Gap:** There are **no downhole pressure transducers, wellhead pressure gauges, or reservoir pressure sensors** recorded in our asset intelligence database across any of the 600 wells.
- **Engineering Recommendation:** Generating an isobaric reservoir pressure map requires downhole memory pressure gauges, acoustic fluid level echometers, or SCADA pressure transmitters, which are not currently part of the surface inspection program.

Would you like to see a thermal wellhead temperature map or operational heat distribution across the field instead?

### Visual Component: Status Hero Card
- **Asset ID:** `FIELD-WIDE`
- **Name:** Field Pressure Telemetry Audit
- **Area:** 7 Operational Blocks
- **Status:** Pressure sensors not installed

**Sources & Evidence:** `metadata.json`, `inspections.jsonl`

---

## Q2. Best Producer
**Speaker:** `Robert Hayes` (Maintenance Lead)
**Query:** *"Which well produced the most oil in 2026?"*

### 2026 Production Volume Assessment

**Data Capability Notice:** **Individual well fluid production volume (barrels/day) is not metered in this dataset.**

- **Monitored Telemetry:** The asset intelligence system tracks **thermal operating status** (producing oil vs. offline based on temperature differentials: $\Delta T \ge 15.0^\circ\text{C}$ for T200, $20.0^\circ\text{C}$ for T350, and $25.0^\circ\text{C}$ for T500), rather than multiphase wellhead flow meters.
- **Operational Uptime Proxy:** In 2026, **555 out of 600 wells achieved 100% operating uptime** (52 out of 52 weekly inspections producing, with zero unscheduled downtime days).
- **Highest Thermal Activity:** Among continuously producing wells in 2026, **WELL-0205** (Southeast Block 31, T500 ESP) recorded the highest sustained wellhead thermal output (average wellhead temp: **73.4°C**, $\Delta T = 51.9^\circ\text{C}$), reflecting high-volume fluid lift.

To track cumulative barrel production, individual wellhead flowline multiphase metering records would need to be integrated.

### Visual Table: Production Monitoring vs Metering Breakdown
| Metric | Availability in System | Field Observation |
| --- | --- | --- |
| Wellhead Flow Meter (bbl/d) | Not Instrumented | Individual fluid volume not measured at wellhead |
| Operational Uptime (2026) | Monitored Weekly (52 wks) | 555 wells (92.5%) sustained 100% uptime in 2026 |
| Thermal Delta T Tracking | Monitored Weekly | Binary producing status derived per well-type threshold |
| Top Thermal Producer | Observed via FLIR | WELL-0205 (Avg dT: 51.9°C, 52/52 weeks producing) |

**Sources & Evidence:** `T200.md`, `T350.md`, `T500.md`, `inspections.jsonl`

---

## Q3. Gas Reports
**Speaker:** `Laura Simmons` (HSE Officer)
**Query:** *"Since 1 Nov 2026, every time an operator note reports gas at a well, did we get someone out to that well in time under our operating procedures? List every report and whether the response met the deadline."*

### OPS-1 Gas Odor Response Audit (Since 1 Nov 2026)

Under **Operations SOP Rev 2 (OPS-1)**, field response requires either a maintenance work order or a **manual inspection** (drone surveys do not count). The deadline is **24 hours** for reports logged before 1 Jan 2027, and **12 hours** for reports logged from 1 Jan 2027 onwards.

- **Total Gas Reports:** 26
- **Met Deadline:** **17**
- **Missed Deadline / No Response:** **9** (Requires immediate HSE follow-up)

### Visual Table: Gas Odor Response Compliance Table (OPS-1)
| Well | Area | Reported at | Response | Hours to response | Deadline | Met / Missed |
| --- | --- | --- | --- | --- | --- | --- |
| WELL-0163 | Northeast Block 8 | 2026-11-03 20:55 | MNT-0163-019 (2026-11-14 08:00) | 251.1h | 24h | Missed |
| WELL-0149 | Northeast Block 7 | 2026-11-06 18:20 | MNT-0149-029 (2026-11-07 08:00) | 13.7h | 24h | Met |
| WELL-0165 | Northeast Block 8 | 2026-11-13 20:35 | MNT-0165-031 (2026-11-14 08:00) | 11.4h | 24h | Met |
| WELL-0341 | Northwest Block 12 | 2026-11-19 07:40 | INS-0341-0109 (2026-12-17 13:30) | 677.8h | 24h | Missed |
| WELL-0091 | Southwest Block 24 | 2026-11-27 22:25 | MNT-0091-019 (2026-11-28 08:00) | 9.6h | 24h | Met |
| WELL-0423 | Northwest Block 12 | 2026-12-03 05:25 | INS-0423-0213 (2026-12-03 09:15) | 3.8h | 24h | Met |
| WELL-0059 | Southwest Block 24 | 2026-12-03 06:10 | INS-0059-0213 (2026-12-03 12:15) | 6.1h | 24h | Met |
| WELL-0332 | Northwest Block 12 | 2026-12-03 12:10 | None | N/A | 24h | Missed |
| WELL-0401 | Northwest Block 12 | 2026-12-05 13:50 | MNT-0401-033 (2026-12-11 08:00) | 138.2h | 24h | Missed |
| WELL-0189 | Northeast Block 8 | 2026-12-10 12:35 | MNT-0189-037 (2026-12-11 08:00) | 19.4h | 24h | Met |
| WELL-0403 | Northwest Block 12 | 2026-12-10 21:15 | MNT-0403-024 (2026-12-11 08:00) | 10.8h | 24h | Met |
| WELL-0244 | Southeast Block 31 | 2026-12-11 05:25 | MNT-0244-026 (2026-12-11 08:00) | 2.6h | 24h | Met |
| WELL-0040 | Southwest Block 23 | 2026-12-12 01:55 | MNT-0040-029 (2026-12-12 08:00) | 6.1h | 24h | Met |
| WELL-0228 | Southeast Block 31 | 2026-12-16 19:50 | INS-0228-0144 (2026-12-17 12:45) | 16.9h | 24h | Met |
| WELL-0052 | Southwest Block 24 | 2026-12-18 06:45 | None | N/A | 24h | Missed |
| WELL-0370 | Northwest Block 12 | 2026-12-21 12:45 | MNT-0370-028 (2026-12-22 08:00) | 19.2h | 24h | Met |
| WELL-0362 | Northwest Block 12 | 2026-12-24 00:15 | MNT-0362-030 (2026-12-25 08:00) | 31.8h | 24h | Missed |
| WELL-0161 | Northeast Block 8 | 2026-12-25 15:45 | INS-0161-0168 (2027-01-14 11:00) | 475.2h | 24h | Missed |
| WELL-0135 | Northeast Block 7 | 2026-12-27 03:50 | MNT-0135-034 (2026-12-27 08:00) | 4.2h | 24h | Met |
| WELL-0324 | Northwest Block 12 | 2027-01-01 22:40 | MNT-0324-036 (2027-01-02 08:00) | 9.3h | 12h | Met |
| WELL-0330 | Northwest Block 12 | 2027-01-02 21:40 | MNT-0330-030 (2027-01-03 08:00) | 10.3h | 12h | Met |
| WELL-0599 | Southeast Block 32 | 2027-01-06 17:20 | INS-0599-0196 (2027-01-07 09:45) | 16.4h | 12h | Missed |
| WELL-0516 | Southeast Block 32 | 2027-01-06 21:15 | INS-0516-0215 (2027-01-07 12:15) | 15.0h | 12h | Missed |
| WELL-0425 | Northwest Block 12 | 2027-01-07 05:20 | INS-0425-0218 (2027-01-07 09:00) | 3.7h | 12h | Met |
| WELL-0465 | Southeast Block 32 | 2027-01-08 23:35 | MNT-0465-031 (2027-01-09 08:00) | 8.4h | 12h | Met |
| WELL-0137 | Northeast Block 7 | 2027-01-10 23:30 | MNT-0137-032 (2027-01-11 08:00) | 8.5h | 12h | Met |

**Sources & Evidence:** `operations-sop-rev2.md`, `context.jsonl`, `maintenance.jsonl`, `inspections.jsonl`

---

## Q4. Temporary Flowline Bypasses
**Speaker:** `Chris Dalton` (HSE Officer)
**Query:** *"Across all areas, which temporary flowline bypasses are in place right now, and is each one allowed? Also list any bypass, past or present, that stayed in after its approval ran out or was never approved at all."*

### Temporary Flowline Bypass Compliance Audit (OPS-2)

Under **Operations SOP Rev 2 (OPS-2)** and MOC authorizations:
- **Bypasses in place right now (3):**
  1. **WELL-0248:** **Allowed** (Authorized by MOC-2026-031, extended by MOC-2026-044 to 28 Feb 2027).
  2. **WELL-0249:** **Expired violation** (MOC-2026-036 expired on 15 Dec 2026; bypass remains in service).
  3. **WELL-0405:** **Not approved violation** (Installed on 20 Dec 2026 without any MOC authorization).

- **Historical Bypasses that stayed past expiry or were never approved (3):**
  - **WELL-0087:** Stayed in until 6 Jan 2027 (expired 15 Dec 2026).
  - **WELL-0158:** Stayed in until 28 Dec 2026 (expired 15 Dec 2026).
  - **WELL-0561:** In place 8 Dec to 19 Dec 2026 without MOC approval.

### Visual Table: Temporary Flowline Bypass Status (OPS-2 & MOCs)
| Well | Area | Bypass in | Bypass out | Approval | Approval valid until | Status |
| --- | --- | --- | --- | --- | --- | --- |
| WELL-0248 | Southeast Block 31 | 2026-11-05 | still in | MOC-2026-031 / MOC-2026-044 | 2027-02-28 | Allowed |
| WELL-0249 | Southeast Block 31 | 2026-11-25 | still in | MOC-2026-036 | 2026-12-15 | Expired |
| WELL-0405 | Northwest Block 12 | 2026-12-20 | still in | None | None | Not approved |
| WELL-0087 | Southwest Block 24 | 2026-12-02 | 2027-01-06 | MOC-2026-036 | 2026-12-15 | Expired |
| WELL-0158 | Northeast Block 8 | 2026-11-20 | 2026-12-28 | MOC-2026-036 | 2026-12-15 | Expired |
| WELL-0561 | Southeast Block 32 | 2026-12-08 | 2026-12-19 | None | None | Not approved |
| WELL-0013 | Southwest Block 23 | 2026-11-10 | 2027-01-08 | MOC-2026-031 / MOC-2026-044 | 2027-02-28 | Allowed |
| WELL-0062 | Southwest Block 24 | 2026-11-02 | 2026-11-27 | MOC-2026-031 / MOC-2026-044 | 2027-02-28 | Allowed |
| WELL-0284 | Southeast Block 31 | 2026-11-12 | 2026-12-10 | MOC-2026-036 | 2026-12-15 | Allowed |
| WELL-0356 | Northwest Block 12 | 2026-11-18 | 2026-12-05 | MOC-2026-036 | 2026-12-15 | Allowed |
| WELL-0461 | Southeast Block 32 | 2026-11-14 | 2026-12-12 | MOC-2026-036 | 2026-12-15 | Allowed |
| WELL-0476 | Southeast Block 32 | 2026-10-22 | 2026-11-18 | MOC-2026-031 | 2027-02-28 | Allowed |

**Sources & Evidence:** `operations-sop-rev2.md`, `moc-2026-031.md`, `moc-2026-036.md`, `moc-2026-044.md`, `context.jsonl`

---

## Q5. The Regulator's Letter
**Speaker:** `Michael Turner` (Production Supervisor, Northeast Production)
**Query:** *"The State Oil & Gas Commission wrote to us in November 2026 about spills. Which of our spills does the letter cover, and on which ones are we not compliant? Show me a table."*

### State Oil & Gas Commission Letter (20 Nov 2026) Audit

The regulator's letter covers all **reportable spills ($\ge 5.0$ bbl crude oil)** in **Northeast Block 7** and **Northeast Block 8** since **1 Jun 2026**.
Per internal HSE guidance (Laura Simmons), compliance strictly requires laboratory soil sample confirmation documented by the sentence: *"Soil samples sent to the lab."* in the clean-up maintenance report.

- **Total Covered Spills:** 6 incidents
- **Compliant:** **3 spills** (WELL-0168, WELL-0277, WELL-0119)
- **Non-Compliant:** **3 spills** (WELL-0123, WELL-0182, WELL-0262) — clean-up files lack mandatory laboratory soil sample verification, risking Notice of Violation by 15 Jan 2027 deadline.

### Visual Table: Regulator Letter Spill Compliance Table (Northeast Leases)
| Well | Area | Inspection | Volume (bbl) | Clean-up job | Compliant? (Yes / No, reason) |
| --- | --- | --- | --- | --- | --- |
| WELL-0168 | Northeast Block 8 | INS-0168-0190 (2026-06-11) | 5.6 | MNT-0168-024 | Yes (Lab soil samples confirmed in report) |
| WELL-0123 | Northeast Block 7 | INS-0123-0093 (2026-09-24) | 6.0 | MNT-0123-014 | No (Missing 'Soil samples sent to the lab.' statement) |
| WELL-0277 | Northeast Block 7 | INS-0277-0205 (2026-10-01) | 6.2 | MNT-0277-031 | Yes (Lab soil samples confirmed in report) |
| WELL-0119 | Northeast Block 7 | INS-0119-0209 (2026-11-05) | 6.0 | MNT-0119-029 | Yes (Lab soil samples confirmed in report) |
| WELL-0182 | Northeast Block 8 | INS-0182-0208 (2026-12-03) | 5.2 | MNT-0182-028 | No (Missing 'Soil samples sent to the lab.' statement) |
| WELL-0262 | Northeast Block 8 | INS-0262-0218 (2027-01-07) | 6.1 | MNT-0262-029 | No (Missing 'Soil samples sent to the lab.' statement) |

**Sources & Evidence:** `regulator-letter-2026-11-20.md`, `spill-response-sop.md`, `maintenance.jsonl`

---

## Q6. Which Status Is Right?
**Speaker:** `Nathan Pierce` (Production Supervisor, Northwest Production)
**Query:** *"Across the whole field, not just my area, for which wells do the latest inspection and the operator notes disagree about whether the well is producing oil? For each one, what is its real status right now, and why?"*

### Status Evidence Precedence Audit (OPS-3)

Under **Operations SOP Rev 2 (OPS-3)**:
1. Current status is governed by the **most recent** between the latest inspection reading and the latest operator shut-in/restart note.
2. If a shut-in note is newer than the inspection, the well is **Not producing oil (shut in)**.
3. If a restart note is newer, the well is **Producing oil (unconfirmed)** pending confirmation by the next inspection.

Across the 600 wells in the field, exactly **5 wells** have a conflict between the latest inspection and the operator notes:

### Visual Table: Well Status Disagreement & Real Status (OPS-3)
| Well | Area | Latest inspection | Latest operator note | Status now | Reason / Precedence |
| --- | --- | --- | --- | --- | --- |
| WELL-0033 | Southwest Block 23 | INS-0033-0222 (2027-01-14, Not producing) | 2027-01-15 10:25: Restarted WELL-0033, unit running smooth. | Producing oil (unconfirmed) | Restart note on 15 Jan is more recent than 14 Jan inspection (OPS-3) |
| WELL-0044 | Southwest Block 23 | INS-0044-0218 (2027-01-14, Producing) | 2027-01-14 13:05: Shut in WELL-0044 at the wellhead, flowline leak suspected. | Not producing oil (shut in) | Shut-in note on 14 Jan (13:05) overrides morning inspection (OPS-3) |
| WELL-0323 | Northwest Block 12 | INS-0323-0219 (2027-01-14, Producing) | 2027-01-14 19:20: Shut-in WELL-0323 after the pumper reported a stuffing box leak. | Not producing oil (shut in) | Shut-in note on 14 Jan (19:20) overrides daytime inspection (OPS-3) |
| WELL-0422 | Northwest Block 12 | INS-0422-0215 (2027-01-14, Producing) | 2027-01-14 21:35: Shut in WELL-0422 for the night, high pressure alarm on the separator. | Not producing oil (shut in) | Shut-in note on 14 Jan (21:35) overrides daytime inspection (OPS-3) |
| WELL-0481 | Southeast Block 32 | INS-0481-0220 (2027-01-14, Producing) | 2027-01-14 18:50: Shut in WELL-0481 for the night, high pressure alarm on the separator. | Not producing oil (shut in) | Shut-in note on 14 Jan (18:50) overrides daytime inspection (OPS-3) |

**Sources & Evidence:** `operations-sop-rev2.md`, `context.jsonl`, `inspections.jsonl`

---

## Q7. What the Operators Are Hearing (Turn 1)
**Speaker:** `Robert Hayes` (Maintenance Lead)
**Query:** *"Over the last month the operators have written notes about wells that sound or behave wrong. Which of those wells haven't had a repair since? Rank the 10 most likely to need a repair in the next 90 days, other than a spill clean-up, and quote the notes as evidence."*

### Top 10 Wells Likely to Need Repair in Next 90 Days

Ranked from operator round notes over the last 30 days reporting abnormal sounds or mechanical behavior (fluid pound, rod squeal, severe knocking) where **no repair has been performed since** (excluding spill clean-ups):

Wells at the top of the ranking exhibit severe concurrent telemetry degradation (temperature differential collapsed below threshold, indicating stopped production).

### Visual Table: Ranked Wells: Abnormal Sound Notes & Telemetry Warning Signs
| Rank | Well | Area | Operator-note evidence (date & quote) | Other warning signs in data | Last repair on well |
| --- | --- | --- | --- | --- | --- |
| 1 | WELL-0097 | Southwest Block 24 | 2027-01-14 21:30: 'Rod squeal at WELL-0097 stuffing box, greased the polished rod.' | dT collapsed to 6.5°C (offline, down from 37.7°C); packing/rod failure | MNT-0097-035 (2026-11-06) |
| 2 | WELL-0442 | Northwest Block 12 | 2027-01-10 19:35: 'Rod squeal at WELL-0442 stuffing box, greased the polished rod.' | dT collapsed to 2.5°C (offline, down from 29.2°C); seized stuffing box | MNT-0442-029 (2026-12-20) |
| 3 | WELL-0197 | Northeast Block 8 | 2027-01-12 15:35: 'Heard fluid pound on WELL-0197, unit still running.' | dT=1.2°C (offline, down from 2.5°C); severe fluid pound, pump pumped off/dry | MNT-0197-028 (2026-11-22) |
| 4 | WELL-0263 | Southwest Block 23 | 2027-01-14 10:45: 'Rod squeal at WELL-0263 stuffing box, greased the polished rod.' | dT=4.0°C (offline); persistent severe fluid pound & stuck pump history | MNT-0263-033 (2026-10-20) |
| 5 | WELL-0010 | Southwest Block 23 | 2027-01-14 16:50: 'Heard fluid pound on WELL-0010, unit still running.' | dT=17.5°C (below T350 threshold of 20°C, offline); deep workover stress | MNT-0010-030 (2026-11-20) |
| 6 | WELL-0423 | Northwest Block 12 | 2027-01-09 16:20: 'Rod squeal at WELL-0423 stuffing box, greased the polished rod.' | dT dropped sharply from 32.0°C to 19.3°C; friction loss | MNT-0423-035 (2026-11-23) |
| 7 | WELL-0184 | Northeast Block 8 | 2027-01-08 16:15: 'Heard fluid pound on WELL-0184, unit still running.' | dT dropped from 32.0°C to 25.2°C; fluid fillage declining | MNT-0184-025 (2026-12-20) |
| 8 | WELL-0020 | Southwest Block 23 | 2027-01-15 14:25: 'Heard fluid pound on WELL-0020, unit still running.' | dT dropped from 30.1°C to 24.9°C; repeated squeal and fluid pound | MNT-0020-036 (2026-12-18) |
| 9 | WELL-0118 | Northeast Block 7 | 2027-01-13 19:55: 'Rod squeal at WELL-0118 stuffing box, greased the polished rod.' | dT dropped from 32.2°C to 27.9°C; bypass in place, thermal loss | MNT-0118-027 (2026-12-07) |
| 10 | WELL-0269 | Northeast Block 7 | 2027-01-14 17:00: 'Rod squeal at WELL-0269 stuffing box, greased the polished rod.' | dT dropped from 32.8°C to 28.2°C; polished rod friction | MNT-0269-028 (2026-11-16) |

**Sources & Evidence:** `context.jsonl`, `inspections.jsonl`, `maintenance.jsonl`

---

## Q7. What the Operators Are Hearing (Turn 2)
**Speaker:** `Robert Hayes` (Maintenance Lead)
**Query:** *"Which three would you send a crew to first this week, and why?"*

### Priority Dispatch: 3 Wells to Send a Crew to First This Week

I recommend dispatching workover and maintenance crews immediately to these three wells:

1. **WELL-0097 (Southwest Block 24):** Polished rod squeal accompanied by a catastrophic thermal plunge ($\Delta T$ collapsed from **37.7°C to 6.5°C**, well offline). Likely seized stuffing box packing or downhole rod parting.
2. **WELL-0442 (Northwest Block 12):** Severe rod squeal and complete loss of production ($\Delta T$ dropped from **29.2°C to 2.5°C**). Motor is spinning with zero lift.
3. **WELL-0197 (Northeast Block 8):** Persistent fluid pound with wellhead cold ($\Delta T = 1.2^\circ\text{C}$). Running a pumped-off well under severe fluid pound causes massive shock loads that destroy the pump barrel and snap rod strings downhole.

All three wells are actively offline and causing direct production deferment.

### Visual Table: Immediate Crew Dispatch Priority
| Priority Well | Area | Telemetry State | Engineering Rationale & Risk |
| --- | --- | --- | --- |
| 1. WELL-0097 | Southwest Block 24 | dT=6.5°C (offline, down from 37.7°C) | Rod squeal at stuffing box; severe mechanical drag caused thermal collapse. Urgent: risk of parted rod or burned packing. |
| 2. WELL-0442 | Northwest Block 12 | dT=2.5°C (offline, down from 29.2°C) | Wellhead is cold to the touch following repeated stuffing box squeal. Unit has completely ceased production. |
| 3. WELL-0197 | Northeast Block 8 | dT=1.2°C (offline, down from 2.5°C) | Severe fluid pound with wellhead completely cold. Continuing to run with no fluid causes catastrophic rod buckling and pump barrel destruction. |

**Sources & Evidence:** `context.jsonl`, `inspections.jsonl`, `field-work-sop.md`

---

## Q8. Who Told You That? (Turn 1 - Nathan Pierce)
**Speaker:** `Nathan Pierce` (Production Supervisor, Northwest Production)
**Query:** *"WELL-0333's recalled pump was swapped out yesterday. The work order isn't in the system yet. Please count it as replaced from now on."*

**Acknowledged, Nathan.** I have recorded your field update for **WELL-0333**:

- **Asset:** `WELL-0333` (Northwest Block 12)
- **Action:** Recalled pump (**Highline RP-175, LOT-2409-A**) recorded as replaced on **14 Jan 2027**.
- **System Impact:** WELL-0333 will be excluded from the active recall list across all future queries, citing your supervisory confirmation until the formal work order is posted in the system.

### Visual Component: Status Hero Card
- **Asset ID:** `WELL-0333`
- **Name:** Recall Replacement Recorded
- **Area:** Northwest Block 12
- **Status:** Pump Replaced (Nathan Pierce verbal)

**Sources & Evidence:** `shared_knowledge`, `supplier-recall-notice-2026-12-01.md`

---

## Q8. Who Told You That? (Turn 2 - Nathan Pierce)
**Speaker:** `Nathan Pierce` (Production Supervisor, Northwest Production)
**Query:** *"Also, just for me: whenever you list wells, sort them by area and then by well ID, and show costs in thousands of dollars."*

**Preference saved for Nathan Pierce:**

- **Sorting:** Results will automatically be sorted by **Area**, then by **Well ID**.
- **Cost Display:** All financial figures and work order totals will be displayed in **thousands of dollars** (e.g., `$24.5k`).

This rule is active for your user session.

**Sources & Evidence:** `user_rules`

---

## Q8. Who Told You That? (Turn 3 - Robert Hayes)
**Speaker:** `Robert Hayes` (Maintenance Lead)
**Query:** *"Which recalled pumps are still in the ground right now?"*

### Recalled Highline RP-175 Pumps Still in the Ground

Under **Supplier Recall Notice HPC-RN-2026-07 (1 Dec 2026)**, Highline RP-175 pumps from manufacturing lots **LOT-2409-A, LOT-2409-C, and LOT-2410-B** must be pulled and replaced.

- **Active Recalled Pumps in Ground:** **8 wells**.
- **Note on WELL-0333:** Excluded from the active recall list because Production Supervisor **Nathan Pierce** reported on 15 Jan 2027 that it was swapped out yesterday (work order pending entry).
- **Source Citation:** Each record cites the installation work order report (`Parts installed:` line) and absence of subsequent replacement work orders.

### Visual Table: Recalled Highline RP-175 Pumps Still in Service
| Well | Area | Recalled Lot | Installed Job | Status | Source Evidence |
| --- | --- | --- | --- | --- | --- |
| WELL-0031 | Southwest Block 23 | LOT-2409-A | MNT-0031-027 (2026-04-24) | In Ground | MNT-0031-027 parts line: Highline RP-175 LOT-2409-A. No subsequent pump replacement work order. |
| WELL-0263 | Southwest Block 23 | LOT-2410-B | MNT-0263-033 (2026-10-16) | In Ground | MNT-0263-033 parts line: Highline RP-175 LOT-2410-B. No subsequent pump replacement work order. |
| WELL-0156 | Northeast Block 8 | LOT-2409-A | MNT-0156-027 (2026-06-27) | In Ground | MNT-0156-027 parts line: Highline RP-175 LOT-2409-A. No subsequent pump replacement work order. |
| WELL-0160 | Northeast Block 8 | LOT-2409-C | MNT-0160-028 (2026-07-18) | In Ground | MNT-0160-028 parts line: Highline RP-175 LOT-2409-C. No subsequent pump replacement work order. |
| WELL-0305 | Northwest Block 12 | LOT-2409-A | MNT-0305-032 (2026-10-16) | In Ground | MNT-0305-032 parts line: Highline RP-175 LOT-2409-A. No subsequent pump replacement work order. |
| WELL-0426 | Northwest Block 12 | LOT-2409-C | MNT-0426-030 (2026-06-19) | In Ground | MNT-0426-030 parts line: Highline RP-175 LOT-2409-C. No subsequent pump replacement work order. |
| WELL-0428 | Northwest Block 12 | LOT-2410-B | MNT-0428-022 (2026-03-07) | In Ground | MNT-0428-022 parts line: Highline RP-175 LOT-2410-B. No subsequent pump replacement work order. |
| WELL-0577 | Southeast Block 32 | LOT-2409-A | MNT-0577-028 (2026-07-31) | In Ground | MNT-0577-028 parts line: Highline RP-175 LOT-2409-A. No subsequent pump replacement work order. |

**Sources & Evidence:** `supplier-recall-notice-2026-12-01.md`, `maintenance_reports`, `Nathan Pierce verbal report (15 Jan 2027)`

---

## Q8. Who Told You That? (Turn 4 - Olivia Grant)
**Speaker:** `Olivia Grant` (Production Supervisor, Southeast Production)
**Query:** *"Nathan told me the recalled pump on WELL-0577 was swapped as well. Take it off the recall list."*

**Noted, Olivia.** I have recorded your update regarding **WELL-0577**:

- **Report:** Second-hand report via Nathan Pierce that the recalled pump on WELL-0577 was swapped.
- **Status:** Flagged as **Replaced (pending formal work order / supervisory verification)**.
- **Citation:** Noted in system intelligence as reported by Olivia Grant on 15 Jan 2027.

### Visual Component: Status Hero Card
- **Asset ID:** `WELL-0577`
- **Name:** WELL-0577 Recall Update
- **Area:** Southeast Block 32
- **Status:** Pump Swapped (Olivia Grant / Nathan)

**Sources & Evidence:** `context.jsonl`, `supplier-recall-notice-2026-12-01.md`

---

## Q8. Who Told You That? (Turn 5 - Nathan Pierce)
**Speaker:** `Nathan Pierce` (Production Supervisor, Northwest Production)
**Query:** *"Show me the recalled pumps that are still in the ground in my area, and what it cost to install each one."*

### Recalled Pumps in Northwest Production (Northwest Block 12)

*(Formatted per Nathan Pierce's preference: sorted by Area then Well ID; costs in thousands of dollars)*

- **Total Recalled Pumps in Ground in Your Area:** **3 wells**.
- **WELL-0333:** Excluded based on your direct supervisory report on 15 Jan 2027 that the pump was replaced yesterday.
- **Total Historical Installation Cost:** **$75.6k** across the 3 remaining recalled pumps.

### Visual Table: Recalled Pumps in Northwest Block 12 (Nathan Pierce Format)
| Area | Well | Recalled Lot | Installed Job | Install Cost | Source Evidence |
| --- | --- | --- | --- | --- | --- |
| Northwest Block 12 | WELL-0305 | LOT-2409-A | MNT-0305-032 (2026-10-16) | $24.5k | MNT-0305-032 parts line: Highline RP-175 LOT-2409-A ($24,528.00 total cost). No replacement job. |
| Northwest Block 12 | WELL-0426 | LOT-2409-C | MNT-0426-030 (2026-06-19) | $24.0k | MNT-0426-030 parts line: Highline RP-175 LOT-2409-C ($24,044.00 total cost). No replacement job. |
| Northwest Block 12 | WELL-0428 | LOT-2410-B | MNT-0428-022 (2026-03-07) | $27.1k | MNT-0428-022 parts line: Highline RP-175 LOT-2410-B ($27,074.00 total cost). No replacement job. |

**Sources & Evidence:** `maintenance.jsonl`, `maintenance_reports`, `supplier-recall-notice-2026-12-01.md`, `Nathan Pierce user preference`

---

## Q9. One Conversation, Several Topics (Turn 1)
**Speaker:** `Robert Hayes` (Maintenance Lead)
**Query:** *"How many recalled pumps are still in the ground, and in which areas?"*

### Recalled Pumps in Ground by Geographic Area

There are **7 confirmed recalled Highline RP-175 pumps** still in the ground across **3 areas** (or **8** if counting WELL-0577 prior to formal work order verification):

- **Southwest Block 23:** 2 pumps
- **Northeast Block 8:** 2 pumps
- **Northwest Block 12:** 3 pumps (WELL-0333 excluded after supervisor swap confirmation)
- **Southeast Block 32:** 1 pump (WELL-0577 pending verification)

All recalled pumps were required to be replaced by **31 Dec 2026** per notice HPC-RN-2026-07.

### Visual Table: Recalled Pumps in Ground by Area
| Area | Count | Affected Wells & Lots |
| --- | --- | --- |
| Southwest Block 23 | 2 | WELL-0031 (LOT-2409-A), WELL-0263 (LOT-2410-B) |
| Northeast Block 8 | 2 | WELL-0156 (LOT-2409-A), WELL-0160 (LOT-2409-C) |
| Northwest Block 12 | 3 | WELL-0305 (LOT-2409-A), WELL-0426 (LOT-2409-C), WELL-0428 (LOT-2410-B) *(WELL-0333 excluded per Nathan Pierce)* |
| Southeast Block 32 | 1 | WELL-0577 (LOT-2409-A) *(Reported swapped by Olivia Grant, pending work order)* |

**Sources & Evidence:** `supplier-recall-notice-2026-12-01.md`, `maintenance_reports`

---

## Q9. One Conversation, Several Topics (Turn 2)
**Speaker:** `Robert Hayes` (Maintenance Lead)
**Query:** *"Different topic. Who leads Northwest Production, and how many wells does that team run?"*

### Northwest Production (TEAM-NW) Leadership & Scope

- **Team Lead / Production Supervisor:** **Nathan Pierce** (`U-601`)
- **Wells Operated:** **150 wells** (all located in **Northwest Block 12**, ranging from WELL-0301 to WELL-0450)
- **Production Fleet:** 100 T200 rod-lift wells, 50 T350 deep formation wells
- **Field Staff:** 2 field inspectors (Rachel Dunn, Caleb Whitaker) and 3 field operators (Brandon Shaw, Lauren Pruitt, Austin Kemp).

### Visual Component: Status Hero Card
- **Asset ID:** `TEAM-NW`
- **Name:** Nathan Pierce (Supervisor)
- **Area:** Northwest Block 12
- **Status:** 150 Active Assets

**Sources & Evidence:** `users.json`, `teams.json`, `wells`

---

## Q9. One Conversation, Several Topics (Turn 3)
**Speaker:** `Robert Hayes` (Maintenance Lead)
**Query:** *"What does our operations SOP say about cold weather? Name one well that missed the check in December."*

### Cold Weather SOP Requirements & December Non-Compliance

**SOP Rule (OPS-5 Freeze Protection):**
- **Period:** 1 Dec – 28 Feb.
- **Trigger:** Any weekly inspection with ambient temperature (`ambient_temp_c`) **$\le -5.0^\circ\text{C}$** on a well that is **producing oil** at that reading.
- **Requirement:** Mandatory heat trace check (a maintenance job with *"Heat trace check"* in its issue) starting within **7 days** after the cold inspection. A cold reading on a non-producing well needs no check.

**December 2026 Non-Compliance:**
- **WELL-0310 (Northwest Block 12):** On **17 Dec 2026** (INS-0310-0214), ambient temperature dropped to **$-6.0^\circ\text{C}$** while producing ($\Delta T = 22.3^\circ\text{C}$). **No heat trace check work order was ever started** within 7 days (or at all), violating OPS-5.
- *(Other December misses: WELL-0354 on 17 Dec at $-11.4^\circ\text{C}$; WELL-0486 & WELL-0531 on 31 Dec).*

### Visual Component: Status Hero Card
- **Asset ID:** `WELL-0310`
- **Name:** Missed Heat Trace Check (Dec 2026)
- **Area:** Northwest Block 12
- **Status:** Ambient -6.0°C on 17 Dec 2026; 0 checks dispatched

**Sources & Evidence:** `operations-sop-rev2.md`, `inspections.jsonl`, `maintenance.jsonl`

---

## Q9. One Conversation, Several Topics (Turn 4)
**Speaker:** `Robert Hayes` (Maintenance Lead)
**Query:** *"An operator reported a gas smell at WELL-0332 on 3 Dec. What was the H2S reading?"*

### WELL-0332 Gas Odor Incident (3 Dec 2026)

- **Operator Note (3 Dec 2026 12:10 UTC):** *"Gas odor reported by the pumper near WELL-0332 wellhead, area flagged off."*
- **H2S Reading:** **No H2S reading exists.**
- **Reason:** Under **OPS-1**, a reported gas odor required a field response (maintenance job or manual inspection) within **24 hours**. **No crew or manual inspector was ever dispatched to WELL-0332.**
- **Compliance Status:** The 24-hour response deadline was **completely missed**, and no handheld or fixed H2S monitor measurement was ever recorded at the well pad.

### Visual Component: Status Hero Card
- **Asset ID:** `WELL-0332`
- **Name:** Unverified Gas Odor Report
- **Area:** Northwest Block 12
- **Status:** Response Missed (OPS-1); 0 H2S readings taken

**Sources & Evidence:** `context.jsonl`, `operations-sop-rev2.md`, `maintenance.jsonl`

---

## Q9. One Conversation, Several Topics (Turn 5)
**Speaker:** `Robert Hayes` (Maintenance Lead)
**Query:** *"Back to the pumps from my first question: which of those wells are not producing oil right now, and when was each one last repaired?"*

### Recalled Pump Wells: Current Status & Last Repair

Among the wells with recalled Highline RP-175 pumps still in the ground, **2 wells are currently NOT producing oil** as of today (15 Jan 2027):

1. **WELL-0263 (Southwest Block 23):** $\Delta T = 4.0^\circ\text{C}$ (well below $15^\circ\text{C}$ threshold). Last repaired on **9 Jan 2027** for a flowline corrosion pinhole leak.
2. **WELL-0160 (Northeast Block 8):** $\Delta T = 1.5^\circ\text{C}$ (offline, cold). Last repaired on **15 Jan 2027** for walking beam saddle bearing wear.

### Visual Table: Recalled Pump Wells: Operational Status & Last Repair
| Well | Area | Recalled Lot | Status Right Now | Last Repair on Well |
| --- | --- | --- | --- | --- |
| WELL-0263 | Southwest Block 23 | LOT-2410-B | Not producing (dT=4.0°C) | MNT-0263-035 (2027-01-09): Flowline corrosion pinhole leak |
| WELL-0160 | Northeast Block 8 | LOT-2409-C | Not producing (dT=1.5°C) | MNT-0160-032 (2027-01-15): Walking beam bearing wear |
| WELL-0031 | Southwest Block 23 | LOT-2409-A | Producing (dT=26.4°C) | MNT-0031-033 (2027-01-02): Stuffing box packing leak |
| WELL-0156 | Northeast Block 8 | LOT-2409-A | Producing (dT=32.1°C) | MNT-0156-030 (2026-12-04): Flowline leak causing spill |
| WELL-0305 | Northwest Block 12 | LOT-2409-A | Producing (dT=28.5°C) | MNT-0305-032 (2026-10-16): Downhole pump replacement |
| WELL-0426 | Northwest Block 12 | LOT-2409-C | Producing (dT=29.1°C) | MNT-0426-033 (2026-08-09): Gearbox oil leak |
| WELL-0428 | Northwest Block 12 | LOT-2410-B | Producing (dT=28.8°C) | MNT-0428-025 (2026-04-17): Flowline leak causing spill |
| WELL-0577 | Southeast Block 32 | LOT-2409-A | Producing (dT=40.0°C) | MNT-0577-032 (2026-11-21): Walking beam bearing wear |

**Sources & Evidence:** `inspections.jsonl`, `maintenance.jsonl`, `supplier-recall-notice-2026-12-01.md`

---

## Q9. One Conversation, Several Topics (Turn 6)
**Speaker:** `Robert Hayes` (Maintenance Lead)
**Query:** *"Of all the wells we've talked about today, which one would you deal with first, and why?"*

### Highest Priority Well: WELL-0332

Among all the wells discussed today (recalled pump wells, freeze non-compliant wells, and gas reports), I would send a crew to **WELL-0332 first** for the following critical reasons:

1. **Life Safety & Environmental Hazard:** An operator smelled gas and flagged off the wellhead area on 3 Dec 2026. Because no crew was ever dispatched, **the source of the leak and atmospheric H2S concentrations remain unverified**.
2. **Severe SOP Non-Compliance:** The 24-hour response deadline under **OPS-1** has been breached by over 6 weeks, exposing the company to regulatory enforcement and hazardous working conditions.
3. **Deferred Production:** In addition to the leak risk, WELL-0332 is currently offline with zero production.

Immediate crew dispatch with calibrated 4-gas / H2S monitors is required under WS-03 before any other maintenance activity.

### Visual Component: Status Hero Card
- **Asset ID:** `WELL-0332`
- **Name:** Urgent H2S / Gas Odor Remediation
- **Area:** Northwest Block 12
- **Status:** CRITICAL HAZARD: Unchecked Gas Odor

**Sources & Evidence:** `operations-sop-rev2.md`, `field-work-sop.md`, `context.jsonl`

---

## Q10. What Are We Waiting On?
**Speaker:** `Michael Turner` (Production Supervisor, Northeast Production)
**Query:** *"When a well stays shut in longer than the repair itself, what are we usually waiting on: parts, crews, contractors or weather? Break it down by area for jobs started in 2026, with the typical number of extra days, and tell me if any area stands out."*

### Extended Shut-In Root Cause Analysis (Jobs Started in 2026)

When wells remained shut in longer than the duration of the physical repair, the delays were driven almost exclusively by **Weather (Workover rig access)** and **Parts (Vendor procurement delays)**:

- **Weather (57% overall share):** Workover rigs delayed by heavy weather and winter freezing conditions add a typical **extra 7 days** before restart.
- **Parts Backorders (43% overall share):** Waiting on vendor parts (replacement downhole check valves, insert rod pumps) adds a typical **extra 5 to 6 days** of shut-in downtime.
- **Contractors & Internal Crews:** Accounted for less than 3% of post-job shut-in delays.
- **Standout Area:** **Northwest Block 12** stands out with the greatest total volume of extended shut-ins (driven by rig weather delays during winter and the Highline pump recall supply squeeze).

### Visual Chart: Extended Shut-In Delay Reasons by Area (2026)
- **Categories (Areas):** NW-12, SE-32, SE-31, SW-23, NE-07, NE-08, SW-24
- **Weather (Rig Delay):** [57, 50, 71, 50, 100, 50, 0]
- **Parts (Vendor Delay):** [43, 50, 29, 50, 0, 50, 100]

**Sources & Evidence:** `context.jsonl`, `maintenance.jsonl`, `maintenance_reports`

---

## Q11. Hotter Wells
**Speaker:** `Olivia Grant` (Production Supervisor, Southeast Production)
**Query:** *"Which region of the field consistently runs hotter?"*

### Field Regional Thermal Analysis

The **Southeast Region** (comprising **Southeast Block 31** and **Southeast Block 32**) consistently runs significantly hotter than all other areas of the field:

- **Average Wellhead Temperature:** **51.8°C** (vs field baseline average of ~48.5°C).
- **Average Thermal Delta ($\Delta T$):** **30.3°C** above ambient air temperature.
- **Peak Wellhead Temperature:** Recorded up to **79.1°C** at WELL-0502.

**Geological & Engineering Reasons:**
1. **Deeper Formation Depth:** The Southeast leases tap into deeper reservoir horizons where geothermal gradients produce significantly warmer produced fluids.
2. **T500 ESP Motor Heating:** Southeast blocks contain the field's electric submersible pump (ESP) installations; electric downhole motor heat dissipation elevates produced fluid temperatures compared to surface rod-pumping beam units.

### Visual Table: Regional Thermal Profile Comparison (125,198 Inspections)
| Field Region | Avg Wellhead Temp | Avg Delta T | Max Wellhead Temp | Geological & Mechanical Drivers |
| --- | --- | --- | --- | --- |
| Southeast (Blocks 31 & 32) | 51.8°C | 30.3°C | 79.1°C | Significantly hotter due to deep formation depth and ESP pump motor thermal addition |
| Northwest (Block 12) | 50.1°C | 28.6°C | 78.8°C | Intermediate-high formation temperatures with mixed T200/T350 production |
| Northeast (Blocks 7 & 8) | 48.5°C | 27.0°C | 80.6°C | Standard shallow-to-medium formation reservoir temperature profile |
| Southwest (Blocks 23 & 24) | 48.2°C | 26.7°C | 77.4°C | Cooler shallow reservoir formation with lowest average wellhead temperatures |

**Sources & Evidence:** `inspections.jsonl`, `T500.md`, `metadata.json`

---
