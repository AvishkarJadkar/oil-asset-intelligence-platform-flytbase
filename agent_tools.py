import sqlite3
import json
import re
from datetime import datetime, timedelta

DB_PATH = "copilot.db"

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def execute_query(query, params=()):
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute(query, params)
        return [dict(row) for row in cur.fetchall()]

def execute_commit(query, params=()):
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute(query, params)
        conn.commit()
        return cur.lastrowid

# -----------------
# Core Domain Tools
# -----------------

def get_well_status(asset_id: str):
    """
    Returns latest inspection, computed producing status with corrections applied,
    associated context notes, and active repairs.
    """
    with get_db() as conn:
        cur = conn.cursor()
        # Well metadata
        cur.execute("SELECT * FROM wells WHERE asset_id = ?", (asset_id,))
        well = cur.fetchone()
        if not well:
            return {"error": f"Well {asset_id} not found."}
        well = dict(well)

        # Check for corrections on latest inspection
        cur.execute('''
            SELECT * FROM inspections
            WHERE asset_id = ?
            ORDER BY inspected_at DESC LIMIT 1
        ''', (asset_id,))
        insp = cur.fetchone()
        if not insp:
            return {"well": well, "status": "No inspections found."}
        insp = dict(insp)

        # Check if inspection values were corrected
        cur.execute('''
            SELECT * FROM corrections
            WHERE asset_id = ? AND inspection_id = ?
            ORDER BY created_at DESC
        ''', (asset_id, insp["inspection_id"]))
        corrections = [dict(r) for r in cur.fetchall()]

        effective_wellhead_temp = insp["wellhead_temp_c"]
        effective_ambient_temp = insp["ambient_temp_c"]
        corrected_by = None
        correction_reason = None

        for c in corrections:
            if c["field_name"] == "wellhead_temp_c":
                try:
                    effective_wellhead_temp = float(c["corrected_value"])
                    corrected_by = c["corrected_by"]
                    correction_reason = c["reason"]
                except ValueError:
                    pass

        temp_diff = round(effective_wellhead_temp - effective_ambient_temp, 2)
        threshold = 20.0 if well["well_type"] == "T350" else 15.0
        is_producing = bool(temp_diff >= threshold)

        # Check latest context notes / planned shutdowns
        cur.execute('''
            SELECT * FROM context_notes
            WHERE asset_id = ?
            ORDER BY created_at DESC LIMIT 3
        ''', (asset_id,))
        notes = [dict(r) for r in cur.fetchall()]

        # Check active maintenance
        cur.execute('''
            SELECT * FROM maintenance
            WHERE asset_id = ? AND (completed_at IS NULL OR completed_at > '2026-10-16T23:59:59')
            ORDER BY started_at DESC
        ''', (asset_id,))
        active_repairs = [dict(r) for r in cur.fetchall()]

        # Check shared knowledge
        cur.execute('''
            SELECT * FROM shared_knowledge
            WHERE asset_id = ?
            ORDER BY created_at DESC
        ''', (asset_id,))
        shared_notes = [dict(r) for r in cur.fetchall()]

        return {
            "asset_id": asset_id,
            "name": well["name"],
            "well_type": well["well_type"],
            "area_id": well["area_id"],
            "recorded_status": well["recorded_status"],
            "is_producing": is_producing,
            "latest_inspection": {
                "inspection_id": insp["inspection_id"],
                "inspected_at": insp["inspected_at"],
                "inspector_user_id": insp["inspector_user_id"],
                "method": insp["method"],
                "ambient_temp_c": effective_ambient_temp,
                "wellhead_temp_c": effective_wellhead_temp,
                "temp_diff": temp_diff,
                "threshold": threshold,
                "inspector_notes": insp["notes"],
                "corrected": bool(corrected_by),
                "corrected_by": corrected_by,
                "correction_reason": correction_reason
            },
            "recent_context_notes": notes,
            "shared_knowledge": shared_notes,
            "active_repairs": active_repairs
        }

def get_non_producing_wells_in_area(area_name: str):
    """
    Lists wells in an area not producing right now and gives reasons.
    """
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute('''
            WITH latest AS (
                SELECT i.*, w.well_type, w.recorded_status, w.name as well_name,
                       ROW_NUMBER() OVER (PARTITION BY i.asset_id ORDER BY i.inspected_at DESC) as rn
                FROM inspections i
                JOIN wells w ON i.asset_id = w.asset_id
                JOIN areas a ON w.area_id = a.area_id
                WHERE a.name = ? OR a.area_id = ?
            )
            SELECT * FROM latest WHERE rn = 1
        ''', (area_name, area_name))
        rows = [dict(r) for r in cur.fetchall()]

        non_producing = []
        for r in rows:
            asset_id = r["asset_id"]
            threshold = 20.0 if r["well_type"] == "T350" else 15.0

            # Check corrections on latest inspection
            cur.execute('''
                SELECT * FROM corrections
                WHERE asset_id = ? AND inspection_id = ?
                ORDER BY created_at DESC
            ''', (asset_id, r["inspection_id"]))
            corrections = [dict(c) for c in cur.fetchall()]

            wh = r["wellhead_temp_c"]
            amb = r["ambient_temp_c"]
            for c in corrections:
                if c["field_name"] == "wellhead_temp_c":
                    try:
                        wh = float(c["corrected_value"])
                    except ValueError:
                        pass
            
            diff = round(wh - amb, 2)
            if diff < threshold:
                # Find why: open repair, context note, or no reason recorded
                cur.execute('''
                    SELECT * FROM maintenance
                    WHERE asset_id = ? AND (completed_at IS NULL OR completed_at > '2026-10-16T23:59:59')
                    ORDER BY started_at DESC LIMIT 1
                ''', (asset_id,))
                maint = cur.fetchone()

                cur.execute('''
                    SELECT * FROM context_notes
                    WHERE asset_id = ?
                    ORDER BY created_at DESC LIMIT 1
                ''', (asset_id,))
                note = cur.fetchone()

                cur.execute('''
                    SELECT * FROM shared_knowledge
                    WHERE asset_id = ?
                    ORDER BY created_at DESC LIMIT 1
                ''', (asset_id,))
                sh_note = cur.fetchone()

                reason = "No recorded reason"
                evidence = []
                if maint:
                    maint = dict(maint)
                    reason = f"Repair {maint['maintenance_id']}: {maint['issue']}, started {maint['started_at'][:10]}, still open"
                    evidence.append(maint['maintenance_id'])
                elif note:
                    note = dict(note)
                    reason = f"Note {note['note_id']}: {note['text']}"
                    evidence.append(note['note_id'])
                elif sh_note:
                    sh_note = dict(sh_note)
                    reason = f"Shared note: {sh_note['text']}"
                elif r["notes"]:
                    reason = f"No recorded reason. Inspector noted: \"{r['notes']}\""
                else:
                    reason = "No recorded reason"

                non_producing.append({
                    "asset_id": asset_id,
                    "well_name": r["well_name"],
                    "well_type": r["well_type"],
                    "temp_diff": diff,
                    "recorded_status": r["recorded_status"],
                    "reason": reason,
                    "inspector_notes": r["notes"],
                    "inspection_id": r["inspection_id"]
                })

        return non_producing

def get_wellhead_temp_history(asset_id: str, weeks: int = 13):
    """
    Returns time series of inspections for line chart.
    """
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("SELECT well_type FROM wells WHERE asset_id = ?", (asset_id,))
        w = cur.fetchone()
        threshold = 20.0 if (w and w["well_type"] == "T350") else 15.0

        cur.execute('''
            SELECT inspection_id, inspected_at, ambient_temp_c, wellhead_temp_c, temp_diff, producing, notes
            FROM inspections
            WHERE asset_id = ?
            ORDER BY inspected_at DESC LIMIT ?
        ''', (asset_id, weeks))
        rows = [dict(r) for r in cur.fetchall()]
        rows.reverse()
        for r in rows:
            r["threshold"] = threshold
            r["date"] = r["inspected_at"][:10]
        return rows

def get_well_spills(asset_id: str, days: int = None, years: int = None):
    """
    Returns spills filtered for corrections (e.g. rainwater).
    """
    with get_db() as conn:
        cur = conn.cursor()
        query = '''
            SELECT i.inspection_id, i.asset_id, i.inspected_at, i.spill_est_volume_bbl, i.spill_area_pct, i.notes
            FROM inspections i
            WHERE i.asset_id = ? AND i.spill_detected = 1
        '''
        params = [asset_id]

        if days:
            cutoff = (datetime.fromisoformat("2026-10-16T23:59:59") - timedelta(days=days)).isoformat()
            query += " AND i.inspected_at >= ?"
            params.append(cutoff)
        elif years:
            cutoff = (datetime.fromisoformat("2026-10-16T23:59:59") - timedelta(days=years*365)).isoformat()
            query += " AND i.inspected_at >= ?"
            params.append(cutoff)

        query += " ORDER BY i.inspected_at ASC"
        cur.execute(query, params)
        raw_spills = [dict(r) for r in cur.fetchall()]

        # Filter out corrected false positives
        cur.execute('''
            SELECT inspection_id, corrected_value, field_name
            FROM corrections
            WHERE asset_id = ?
        ''', (asset_id,))
        corrections = {c["inspection_id"]: dict(c) for c in cur.fetchall()}

        valid_spills = []
        for s in raw_spills:
            insp_id = s["inspection_id"]
            if insp_id in corrections:
                c = corrections[insp_id]
                if c.get("field_name") == "spill_detected" and c.get("corrected_value") in ("false", "0"):
                    continue # Discarded as false positive
                if c.get("field_name") == "spill_est_volume_bbl":
                    try:
                        s["spill_est_volume_bbl"] = float(c["corrected_value"])
                        s["volume_corrected"] = True
                    except ValueError:
                        pass
            valid_spills.append(s)

        total_bbl = sum(s["spill_est_volume_bbl"] or 0.0 for s in valid_spills)
        return {
            "spills": valid_spills,
            "count": len(valid_spills),
            "total_bbl": round(total_bbl, 2)
        }

def get_well_downtime_days(asset_id: str, year: int = None, start_date: str = None, end_date: str = None):
    """
    Computes downtime days = non-producing inspections * 7 days.
    """
    with get_db() as conn:
        cur = conn.cursor()
        query = '''
            SELECT i.inspection_id, i.inspected_at, i.ambient_temp_c, i.wellhead_temp_c, i.temp_diff, i.producing
            FROM inspections i
            WHERE i.asset_id = ? AND i.producing = 0
        '''
        params = [asset_id]
        if year:
            query += " AND i.inspected_at >= ? AND i.inspected_at <= ?"
            params.extend([f"{year}-01-01", f"{year}-12-31T23:59:59"])
        if start_date and end_date:
            query += " AND i.inspected_at >= ? AND i.inspected_at <= ?"
            params.extend([start_date, end_date])

        query += " ORDER BY i.inspected_at ASC"
        cur.execute(query, params)
        non_producing = [dict(r) for r in cur.fetchall()]
        downtime_days = len(non_producing) * 7
        return {
            "asset_id": asset_id,
            "non_producing_weeks": len(non_producing),
            "downtime_days": downtime_days,
            "inspections": non_producing
        }

def get_area_downtime_ranking(area_name: str, start_date: str = "2026-06-16", end_date: str = "2026-10-16T23:59:59", limit: int = 5):
    """
    Top wells by downtime in an area.
    """
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute('''
            SELECT w.asset_id, w.name, w.well_type, COUNT(*) as down_weeks, COUNT(*) * 7 as downtime_days
            FROM inspections i
            JOIN wells w ON i.asset_id = w.asset_id
            JOIN areas a ON w.area_id = a.area_id
            WHERE (a.name = ? OR a.area_id = ?)
              AND i.inspected_at >= ? AND i.inspected_at <= ?
              AND i.producing = 0
            GROUP BY w.asset_id
            ORDER BY downtime_days DESC
            LIMIT ?
        ''', (area_name, area_name, start_date, end_date, limit))
        return [dict(r) for r in cur.fetchall()]

def get_area_real_spills_map(area_name: str, days: int = 90):
    """
    Returns real spills in an area with coordinates for map visual.
    """
    with get_db() as conn:
        cur = conn.cursor()
        cutoff = (datetime.fromisoformat("2026-10-16T23:59:59") - timedelta(days=days)).isoformat()
        cur.execute('''
            SELECT i.inspection_id, i.asset_id, w.name as well_name, w.lat, w.lon,
                   i.inspected_at, i.spill_est_volume_bbl, i.spill_area_pct, i.notes
            FROM inspections i
            JOIN wells w ON i.asset_id = w.asset_id
            JOIN areas a ON w.area_id = a.area_id
            WHERE (a.name = ? OR a.area_id = ?)
              AND i.spill_detected = 1
              AND i.inspected_at >= ?
            ORDER BY i.inspected_at DESC
        ''', (area_name, area_name, cutoff))
        rows = [dict(r) for r in cur.fetchall()]

        # Filter out corrections
        cur.execute("SELECT inspection_id, field_name, corrected_value FROM corrections")
        corrs = {c["inspection_id"]: dict(c) for c in cur.fetchall()}

        valid = []
        for r in rows:
            insp_id = r["inspection_id"]
            if insp_id in corrs:
                c = corrs[insp_id]
                if c.get("field_name") == "spill_detected" and c.get("corrected_value") in ("false", "0"):
                    continue
                if c.get("field_name") == "spill_est_volume_bbl":
                    r["spill_est_volume_bbl"] = float(c["corrected_value"])
            valid.append(r)
        return valid

def get_spills_heatmap(year: int = 2026):
    """
    Spills by geographic area and month.
    """
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute('''
            SELECT a.name as area_name, strftime('%m', i.inspected_at) as month, COUNT(*) as count
            FROM inspections i
            JOIN wells w ON i.asset_id = w.asset_id
            JOIN areas a ON w.area_id = a.area_id
            WHERE i.spill_detected = 1
              AND strftime('%Y', i.inspected_at) = ?
              AND i.inspection_id NOT IN (
                  SELECT inspection_id FROM corrections WHERE field_name = 'spill_detected' AND corrected_value IN ('false', '0')
              )
            GROUP BY a.name, month
            ORDER BY a.name, month
        ''', (str(year),))
        rows = [dict(r) for r in cur.fetchall()]

        # Areas
        cur.execute("SELECT name FROM areas ORDER BY area_id")
        areas = [r["name"] for r in cur.fetchall()]
        months = ["01", "02", "03", "04", "05", "06", "07", "08", "09", "10"]
        month_names = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct"]

        matrix = {a: {m: 0 for m in month_names} for a in areas}
        for r in rows:
            m_idx = int(r["month"]) - 1
            if 0 <= m_idx < len(month_names):
                m_name = month_names[m_idx]
                if r["area_name"] in matrix:
                    matrix[r["area_name"]][m_name] = r["count"]

        # format for heatmap component
        formatted = []
        for a in areas:
            row = {"area": a, **matrix[a], "Total": sum(matrix[a].values())}
            formatted.append(row)
        return {"title": f"Spill Incident Density Matrix ({year})", "months": month_names, "areas": areas, "data": formatted}

def get_well_rule_breaches(asset_id: str, months: int = 12):
    """
    Identifies SOP breaches and open items for an asset (e.g. WELL-0001).
    """
    with get_db() as conn:
        cur = conn.cursor()
        cutoff = (datetime.fromisoformat("2026-10-16T23:59:59") - timedelta(days=months*30)).isoformat()

        # Regulatory events
        cur.execute('''
            SELECT * FROM regulatory_events
            WHERE asset_id = ? AND date >= ?
            ORDER BY date DESC
        ''', (asset_id, cutoff))
        reg_events = [dict(r) for r in cur.fetchall()]

        # Reports with containment hours > 4
        cur.execute('''
            SELECT mr.*, m.started_at, m.issue, m.maintenance_id
            FROM maintenance_reports mr
            JOIN maintenance m ON mr.report_file = m.report_file
            WHERE mr.asset_id = ? AND m.started_at >= ?
        ''', (asset_id, cutoff))
        reports = [dict(r) for r in cur.fetchall()]

        breaches = []
        # Check SR-01 (>24h to report)
        for re_ev in reg_events:
            if re_ev.get("hours_to_report") and re_ev["hours_to_report"] > 24:
                breaches.append({
                    "rule": "SR-01",
                    "description": f"Reported after {re_ev['hours_to_report']} hours (limit 24h). Notice of violation {re_ev['event_id']}, fine USD {re_ev['fine_usd']}, status {re_ev['status']}.",
                    "status": re_ev["status"],
                    "event_id": re_ev["event_id"]
                })
            elif re_ev["event_type"] == "notice_of_violation" and re_ev["status"] == "open":
                breaches.append({
                    "rule": "RC-04",
                    "description": f"Notice of violation {re_ev['event_id']} requiring response within 30 days is still open.",
                    "status": "open",
                    "event_id": re_ev["event_id"]
                })

        # Check SR-02 (containment > 4h)
        for rep in reports:
            if rep.get("containment_hours") and rep["containment_hours"] > 4:
                breaches.append({
                    "rule": "SR-02",
                    "description": f"Spill containment took ~{rep['containment_hours']} hours, exceeding 4-hour limit. (Report: {rep['report_file']})",
                    "status": "violated",
                    "report_file": rep["report_file"]
                })

        # Corrective repairs count on pump jack / flowline for RCA
        cur.execute('''
            SELECT equipment_kind, COUNT(*) as cnt
            FROM maintenance
            WHERE asset_id = ? AND maintenance_type = 'corrective' AND started_at >= ?
            GROUP BY equipment_kind
            HAVING cnt >= 3
        ''', (asset_id, cutoff))
        rca_candidates = [dict(r) for r in cur.fetchall()]

        # Context notes
        cur.execute('''
            SELECT * FROM context_notes
            WHERE asset_id = ? AND created_at >= ?
            ORDER BY created_at DESC
        ''', (asset_id, cutoff))
        notes = [dict(r) for r in cur.fetchall()]

        return {
            "breaches": breaches,
            "rca_candidates": rca_candidates,
            "regulatory_events": reg_events,
            "recent_notes": notes
        }

def get_uncontained_spills_in_area(area_name: str, days: int = 90):
    """
    Finds spills in an area where containment took > 4 hours in the last N days.
    """
    with get_db() as conn:
        cur = conn.cursor()
        cutoff = (datetime.fromisoformat("2026-10-16T23:59:59") - timedelta(days=days)).isoformat()
        cur.execute('''
            SELECT mr.asset_id, mr.maintenance_id, mr.report_file, mr.containment_hours,
                   m.started_at, m.triggered_by_inspection_id, m.issue
            FROM maintenance_reports mr
            JOIN maintenance m ON mr.report_file = m.report_file
            JOIN wells w ON mr.asset_id = w.asset_id
            JOIN areas a ON w.area_id = a.area_id
            WHERE (a.name = ? OR a.area_id = ?)
              AND m.started_at >= ?
              AND mr.containment_hours > 4.0
            ORDER BY m.started_at DESC
        ''', (area_name, area_name, cutoff))
        return [dict(r) for r in cur.fetchall()]

# --------------------------
# Memory & Correction Tools
# --------------------------

def record_correction(user_id: str, asset_id: str, inspection_id: str, field_name: str, corrected_value: str, reason: str, scope: str = "well"):
    """
    Records a user correction to raw data or AI analysis.
    """
    with get_db() as conn:
        cur = conn.cursor()
        # Find original value
        orig_val = None
        cur.execute(f"SELECT {field_name} FROM inspections WHERE inspection_id = ?", (inspection_id,))
        r = cur.fetchone()
        if r:
            orig_val = str(r[0])

        cur.execute('''
            INSERT INTO corrections (
                asset_id, inspection_id, field_name, original_value,
                corrected_value, corrected_by, reason, scope, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            asset_id, inspection_id, field_name, orig_val,
            corrected_value, user_id, reason, scope,
            datetime.now().isoformat()
        ))
        conn.commit()
        return {"status": "success", "message": f"Correction recorded for {inspection_id}."}

def record_shared_fact(user_id: str, asset_id: str, text: str, note_type: str = "operator_feedback", valid_from: str = None, valid_to: str = None, status: str = "confirmed"):
    """
    Saves a shared note visible to all users.
    """
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute('''
            INSERT INTO shared_knowledge (
                asset_id, author_user_id, note_type, text, valid_from, valid_to, status, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (asset_id, user_id, note_type, text, valid_from, valid_to, status, datetime.now().isoformat()))
        conn.commit()
        return {"status": "success", "message": "Shared knowledge saved."}

def record_user_rule(user_id: str, well_type: str, rule_name: str, rule_value: str, description: str):
    """
    Saves a custom rule (e.g. T350 RCA after 2 repairs instead of 3).
    """
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute('''
            INSERT INTO user_rules (user_id, well_type, rule_name, rule_value, description, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (user_id, well_type, rule_name, rule_value, description, datetime.now().isoformat()))
        conn.commit()
        return {"status": "success", "message": f"Rule registered for {well_type}."}

def get_pump_jack_rca_wells(area_name: str, user_id: str = None):
    """
    Finds wells in an area needing pump jack RCA.
    Checks if user has set a custom rule for well types (e.g. T350 threshold = 2).
    """
    with get_db() as conn:
        cur = conn.cursor()
        # Default threshold is 3
        t200_threshold = 3
        t350_threshold = 3
        rule_applied = False

        if user_id:
            cur.execute("SELECT * FROM user_rules WHERE user_id = ? ORDER BY created_at DESC", (user_id,))
            for r in cur.fetchall():
                if r["well_type"] == "T350" and r["rule_name"] == "rca_repair_threshold":
                    t350_threshold = int(r["rule_value"])
                    rule_applied = True
                elif r["well_type"] == "T200" and r["rule_name"] == "rca_repair_threshold":
                    t200_threshold = int(r["rule_value"])
                    rule_applied = True

        cutoff = (datetime.fromisoformat("2026-10-16T23:59:59") - timedelta(days=365)).isoformat()
        cur.execute('''
            SELECT w.asset_id, w.name, w.well_type, COUNT(*) as repair_count
            FROM maintenance m
            JOIN wells w ON m.asset_id = w.asset_id
            JOIN areas a ON w.area_id = a.area_id
            WHERE (a.name = ? OR a.area_id = ?)
              AND m.maintenance_type = 'corrective'
              AND m.equipment_kind = 'pump_jack'
              AND m.started_at >= ?
            GROUP BY w.asset_id
        ''', (area_name, area_name, cutoff))
        rows = [dict(r) for r in cur.fetchall()]

        qualifying = []
        for r in rows:
            thresh = t350_threshold if r["well_type"] == "T350" else t200_threshold
            if r["repair_count"] >= thresh:
                r["threshold"] = thresh
                qualifying.append(r)

        return {
            "qualifying_wells": qualifying,
            "rule_applied": rule_applied,
            "t350_threshold": t350_threshold,
            "t200_threshold": t200_threshold
        }

def get_repair_costs_this_year(asset_ids: list):
    """
    Calculates 2026 repair costs for a list of wells.
    """
    with get_db() as conn:
        cur = conn.cursor()
        results = {}
        for aid in asset_ids:
            cur.execute('''
                SELECT SUM(total_cost) as total
                FROM maintenance
                WHERE asset_id = ? AND strftime('%Y', started_at) = '2026'
            ''', (aid,))
            r = cur.fetchone()
            results[aid] = round(r["total"] or 0.0, 2)
        return results

def get_user_chat_history(user_id: str, limit: int = 10):
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute('''
            SELECT role, content, visual_type, visual_data_json, created_at
            FROM chat_history
            WHERE user_id = ?
            ORDER BY id DESC LIMIT ?
        ''', (user_id, limit))
        rows = [dict(r) for r in cur.fetchall()]
        rows.reverse()
        return rows

def save_chat_message(user_id: str, role: str, content: str, visual_type: str = None, visual_data: dict = None):
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute('''
            INSERT INTO chat_history (user_id, role, content, visual_type, visual_data_json, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            user_id, role, content, visual_type,
            json.dumps(visual_data) if visual_data else None,
            datetime.now().isoformat()
        ))
        conn.commit()

def search_docs(query_text: str):
    """
    Searches SOPs, manuals, and free-text reports for keywords and extracts relevant sections.
    """
    # Clean and extract meaningful keywords (ignore common stop words)
    stop_words = {"what", "is", "the", "for", "a", "an", "in", "on", "of", "and", "or", "to", "how", "many", "show", "me", "which"}
    words = [re.sub(r'[^a-zA-Z0-9_-]', '', w).lower() for w in query_text.split()]
    keywords = [w for w in words if w and w not in stop_words and len(w) > 2]

    if not keywords:
        keywords = [query_text.strip()]

    with get_db() as conn:
        cur = conn.cursor()
        
        # Search docs
        cur.execute("SELECT doc_id, category, title, content FROM docs")
        all_docs = [dict(r) for r in cur.fetchall()]

        matching_docs = []
        for d in all_docs:
            content_lower = d["content"].lower()
            score = sum(1 for kw in keywords if kw in content_lower)
            if score > 0:
                # Find the most relevant paragraph
                paragraphs = d["content"].split("\n\n")
                best_para = max(paragraphs, key=lambda p: sum(1 for kw in keywords if kw in p.lower()))
                matching_docs.append({
                    "doc_id": d["doc_id"],
                    "category": d["category"],
                    "title": d["title"],
                    "content": best_para.strip(),
                    "score": score
                })

        matching_docs.sort(key=lambda x: x["score"], reverse=True)

        # Search reports if any
        matching_reports = []
        for kw in keywords[:2]:
            cur.execute('''
                SELECT asset_id, maintenance_id, report_file, full_text
                FROM maintenance_reports
                WHERE full_text LIKE ?
                LIMIT 3
            ''', (f"%{kw}%",))
            for r in cur.fetchall():
                matching_reports.append(dict(r))

        return {"docs": matching_docs[:3], "reports": matching_reports[:2]}

