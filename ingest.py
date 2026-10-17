import os
import json
import sqlite3
import glob
import re
from datetime import datetime

DB_PATH = "copilot.db"

def init_db(db_path=DB_PATH):
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    
    cur.executescript('''
    DROP TABLE IF EXISTS wells;
    DROP TABLE IF EXISTS inspections;
    DROP TABLE IF EXISTS maintenance;
    DROP TABLE IF EXISTS maintenance_reports;
    DROP TABLE IF EXISTS regulatory_events;
    DROP TABLE IF EXISTS context_notes;
    DROP TABLE IF EXISTS areas;
    DROP TABLE IF EXISTS teams;
    DROP TABLE IF EXISTS users;
    DROP TABLE IF EXISTS docs;
    DROP TABLE IF EXISTS corrections;
    DROP TABLE IF EXISTS shared_knowledge;
    DROP TABLE IF EXISTS user_rules;
    DROP TABLE IF EXISTS chat_history;

    CREATE TABLE wells (
        asset_id TEXT PRIMARY KEY,
        name TEXT,
        asset_category TEXT,
        well_type TEXT,
        area_id TEXT,
        team_id TEXT,
        in_charge_user_id TEXT,
        lat REAL,
        lon REAL,
        installed_on TEXT,
        recorded_status TEXT,
        last_inspection_id TEXT,
        last_inspection_at TEXT,
        last_inspector_id TEXT,
        equipment_json TEXT,
        status TEXT,
        decommissioned_on TEXT,
        type_history_json TEXT,
        team_history_json TEXT
    );

    CREATE TABLE inspections (
        inspection_id TEXT PRIMARY KEY,
        asset_id TEXT,
        inspected_at TEXT,
        inspector_user_id TEXT,
        method TEXT,
        ambient_temp_c REAL,
        wellhead_temp_c REAL,
        temp_diff REAL,
        producing INTEGER,
        spill_detected INTEGER,
        spill_area_pct REAL,
        spill_est_volume_bbl REAL,
        evidence_images_json TEXT,
        notes TEXT,
        recorded_at TEXT
    );

    CREATE INDEX idx_inspections_asset ON inspections(asset_id);
    CREATE INDEX idx_inspections_date ON inspections(inspected_at);
    CREATE INDEX idx_inspections_spill ON inspections(spill_detected);

    CREATE TABLE maintenance (
        maintenance_id TEXT PRIMARY KEY,
        asset_id TEXT,
        started_at TEXT,
        completed_at TEXT,
        maintenance_type TEXT,
        equipment_kind TEXT,
        issue TEXT,
        action_taken TEXT,
        technician_user_id TEXT,
        contractor TEXT,
        downtime_hours REAL,
        labor_cost REAL,
        parts_cost REAL,
        total_cost REAL,
        triggered_by_inspection_id TEXT,
        report_file TEXT,
        recorded_at TEXT,
        cost_revision_json TEXT
    );

    CREATE INDEX idx_maint_asset ON maintenance(asset_id);
    CREATE INDEX idx_maint_start ON maintenance(started_at);
    CREATE INDEX idx_maint_equip ON maintenance(equipment_kind);

    CREATE TABLE maintenance_reports (
        asset_id TEXT,
        maintenance_id TEXT,
        report_file TEXT PRIMARY KEY,
        containment_hours REAL,
        full_text TEXT
    );

    CREATE INDEX idx_reports_asset ON maintenance_reports(asset_id);

    CREATE TABLE regulatory_events (
        event_id TEXT PRIMARY KEY,
        asset_id TEXT,
        date TEXT,
        agency TEXT,
        event_type TEXT,
        protocol_id TEXT,
        related_inspection_id TEXT,
        hours_to_report REAL,
        detail TEXT,
        fine_usd REAL,
        status TEXT
    );

    CREATE INDEX idx_reg_asset ON regulatory_events(asset_id);
    CREATE INDEX idx_reg_date ON regulatory_events(date);

    CREATE TABLE context_notes (
        note_id TEXT PRIMARY KEY,
        asset_id TEXT,
        created_at TEXT,
        author_user_id TEXT,
        note_type TEXT,
        inspection_id TEXT,
        text TEXT,
        valid_from TEXT,
        valid_to TEXT
    );

    CREATE INDEX idx_notes_asset ON context_notes(asset_id);

    CREATE TABLE areas (
        area_id TEXT PRIMARY KEY,
        name TEXT,
        team_id TEXT,
        center_lat REAL,
        center_lon REAL,
        asset_ids_json TEXT
    );

    CREATE TABLE teams (
        team_id TEXT PRIMARY KEY,
        name TEXT,
        lead_user_id TEXT
    );

    CREATE TABLE users (
        user_id TEXT PRIMARY KEY,
        name TEXT,
        role TEXT,
        team_id TEXT
    );

    CREATE TABLE docs (
        doc_id TEXT PRIMARY KEY,
        category TEXT,
        title TEXT,
        content TEXT
    );

    CREATE TABLE corrections (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        asset_id TEXT,
        inspection_id TEXT,
        field_name TEXT,
        original_value TEXT,
        corrected_value TEXT,
        corrected_by TEXT,
        reason TEXT,
        scope TEXT,
        created_at TEXT
    );

    CREATE TABLE shared_knowledge (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        asset_id TEXT,
        author_user_id TEXT,
        note_type TEXT,
        text TEXT,
        valid_from TEXT,
        valid_to TEXT,
        status TEXT DEFAULT 'confirmed',
        created_at TEXT
    );

    CREATE TABLE user_rules (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT,
        well_type TEXT,
        rule_name TEXT,
        rule_value TEXT,
        description TEXT,
        created_at TEXT
    );

    CREATE TABLE chat_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT,
        role TEXT,
        content TEXT,
        visual_type TEXT,
        visual_data_json TEXT,
        created_at TEXT
    );
    ''')
    conn.commit()
    return conn

def load_json(path):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def load_jsonl(path):
    rows = []
    if not os.path.exists(path):
        return rows
    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows

def parse_containment_hours(text):
    matches = re.findall(r'contain(?:ed|ment).*?(\d+(?:\.\d+)?)\s*(?:hours|hrs|h)', text, re.IGNORECASE)
    if matches:
        try:
            return float(matches[0])
        except ValueError:
            pass
    matches2 = re.findall(r'(\d+(?:\.\d+)?)\s*(?:hours|hrs|h).*?contain', text, re.IGNORECASE)
    if matches2:
        try:
            return float(matches2[0])
        except ValueError:
            pass
    return None

def ingest_all(data_dir="sample-data", db_path=DB_PATH):
    print(f"Initializing database {db_path}...")
    conn = init_db(db_path)
    cur = conn.cursor()

    fleet_dir = os.path.join(data_dir, "fleet")
    assets_dir = os.path.join(data_dir, "assets")

    # 1. Areas and Teams
    areas_path = os.path.join(fleet_dir, "areas.json")
    if os.path.exists(areas_path):
        areas_data = load_json(areas_path)
        for a in areas_data.get("areas", []):
            cur.execute('''
                INSERT INTO areas (area_id, name, team_id, center_lat, center_lon, asset_ids_json)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (a["area_id"], a["name"], a.get("team_id"), a["center"]["lat"], a["center"]["lon"], json.dumps(a.get("asset_ids", []))))
        
        for t in areas_data.get("teams", []):
            cur.execute('''
                INSERT INTO teams (team_id, name, lead_user_id)
                VALUES (?, ?, ?)
            ''', (t["team_id"], t["name"], t.get("lead_user_id")))

    # 2. Users
    users_path = os.path.join(fleet_dir, "users.json")
    if os.path.exists(users_path):
        users_data = load_json(users_path)
        for u in users_data.get("users", []):
            cur.execute('''
                INSERT INTO users (user_id, name, role, team_id)
                VALUES (?, ?, ?, ?)
            ''', (u["user_id"], u["name"], u.get("role"), u.get("team_id")))

    # 3. SOPs and Manuals (docs)
    for sop_file in glob.glob(os.path.join(fleet_dir, "sops", "*.md")):
        doc_id = os.path.splitext(os.path.basename(sop_file))[0]
        with open(sop_file, "r", encoding="utf-8") as f:
            content = f.read()
        cur.execute('INSERT INTO docs (doc_id, category, title, content) VALUES (?, ?, ?, ?)',
                    (doc_id, "sop", doc_id.replace("-", " ").title(), content))

    for manual_file in glob.glob(os.path.join(fleet_dir, "well-types", "*.md")):
        doc_id = os.path.splitext(os.path.basename(manual_file))[0]
        with open(manual_file, "r", encoding="utf-8") as f:
            content = f.read()
        cur.execute('INSERT INTO docs (doc_id, category, title, content) VALUES (?, ?, ?, ?)',
                    (doc_id, "manual", f"{doc_id} Manual", content))

    # Well types threshold map: T200=15, T350=20, T500=15 (default)
    well_types_map = {}

    # 4. Wells metadata
    well_dirs = sorted(glob.glob(os.path.join(assets_dir, "WELL-*")))
    print(f"Found {len(well_dirs)} well directories. Ingesting metadata...")
    
    for wdir in well_dirs:
        asset_id = os.path.basename(wdir)
        meta_path = os.path.join(wdir, "metadata.json")
        if not os.path.exists(meta_path):
            continue
        meta = load_json(meta_path)
        well_types_map[asset_id] = meta.get("well_type", "T200")
        
        last_insp = meta.get("last_inspection") or {}
        loc = meta.get("location") or {}
        cur.execute('''
            INSERT INTO wells (
                asset_id, name, asset_category, well_type, area_id, team_id,
                in_charge_user_id, lat, lon, installed_on, recorded_status,
                last_inspection_id, last_inspection_at, last_inspector_id, equipment_json,
                status, decommissioned_on, type_history_json, team_history_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            meta["asset_id"], meta.get("name"), meta.get("asset_category"), meta.get("well_type"),
            meta.get("area_id"), meta.get("team_id"), meta.get("in_charge_user_id"),
            loc.get("lat"), loc.get("lon"), meta.get("installed_on"), meta.get("recorded_status"),
            last_insp.get("inspection_id"), last_insp.get("inspected_at"), last_insp.get("inspector_user_id"),
            json.dumps(meta.get("equipment", [])),
            meta.get("status"),
            meta.get("decommissioned_on"),
            json.dumps(meta.get("type_history")) if meta.get("type_history") else None,
            json.dumps(meta.get("team_history")) if meta.get("team_history") else None
        ))

    # 5. Inspections, Maintenance, Reports, Regulatory, Context
    print("Ingesting inspections, maintenance, reports, and notes...")
    total_inspections = 0
    total_maintenance = 0
    total_reports = 0
    total_regulatory = 0
    total_notes = 0

    insp_batch = []
    maint_batch = []
    reg_batch = []
    note_batch = []
    report_batch = []

    for wdir in well_dirs:
        asset_id = os.path.basename(wdir)
        wtype = well_types_map.get(asset_id, "T200")
        temp_threshold = 20.0 if wtype == "T350" else 15.0  # T200 and T500 use 15°C

        # Inspections
        inspections = load_jsonl(os.path.join(wdir, "inspections.jsonl"))
        for insp in inspections:
            amb = insp.get("ambient_temp_c")
            wh = insp.get("wellhead_temp_c")
            diff = None
            producing = 0
            if amb is not None and wh is not None:
                diff = round(wh - amb, 2)
                if diff >= temp_threshold:
                    producing = 1
            
            spill = 1 if insp.get("spill_detected") else 0
            insp_batch.append((
                insp["inspection_id"],
                asset_id,
                insp.get("inspected_at"),
                insp.get("inspector_user_id"),
                insp.get("method"),
                amb,
                wh,
                diff,
                producing,
                spill,
                insp.get("spill_area_pct"),
                insp.get("spill_est_volume_bbl"),
                json.dumps(insp.get("evidence_images") or []),
                insp.get("notes") or "",
                insp.get("recorded_at")
            ))
        total_inspections += len(inspections)

        # Maintenance
        maint_list = load_jsonl(os.path.join(wdir, "maintenance.jsonl"))
        for m in maint_list:
            cost = m.get("cost_usd") or {}
            maint_batch.append((
                m["maintenance_id"],
                asset_id,
                m.get("started_at"),
                m.get("completed_at"),
                m.get("maintenance_type"),
                m.get("equipment_kind"),
                m.get("issue"),
                m.get("action_taken"),
                m.get("technician_user_id"),
                m.get("contractor"),
                m.get("downtime_hours"),
                cost.get("labor"),
                cost.get("parts"),
                cost.get("total"),
                m.get("triggered_by_inspection_id"),
                m.get("report_file"),
                m.get("recorded_at"),
                json.dumps(m.get("cost_revision")) if m.get("cost_revision") else None
            ))
        total_maintenance += len(maint_list)

        # Free-text reports
        report_files = glob.glob(os.path.join(wdir, "maintenance-reports", "*.md"))
        for rf in report_files:
            rel_name = os.path.join("maintenance-reports", os.path.basename(rf)).replace("\\", "/")
            try:
                with open(rf, "r", encoding="utf-8") as f:
                    txt = f.read()
                chours = parse_containment_hours(txt)
                m_id = None
                m_match = re.search(r'MNT-\d+-\d+', txt)
                if m_match:
                    m_id = m_match.group(0)
                report_batch.append((asset_id, m_id, rel_name, chours, txt))
                total_reports += 1
            except Exception as e:
                print(f"Error reading report {rf}: {e}")

        # Regulatory events
        reg_list = load_jsonl(os.path.join(wdir, "regulatory-events.jsonl"))
        for r in reg_list:
            reg_batch.append((
                r["event_id"],
                asset_id,
                r.get("date"),
                r.get("agency"),
                r.get("event_type"),
                r.get("protocol_id"),
                r.get("related_inspection_id"),
                r.get("hours_to_report"),
                r.get("detail"),
                r.get("fine_usd"),
                r.get("status")
            ))
        total_regulatory += len(reg_list)

        # Context notes
        notes_list = load_jsonl(os.path.join(wdir, "context.jsonl"))
        for n in notes_list:
            note_batch.append((
                n["note_id"],
                asset_id,
                n.get("created_at"),
                n.get("author_user_id"),
                n.get("note_type"),
                n.get("inspection_id"),
                n.get("text"),
                n.get("valid_from"),
                n.get("valid_to")
            ))
            # If it's a correction or data_correction, seed it into corrections table
            if n.get("note_type") in ("correction", "data_correction") and n.get("inspection_id"):
                field_name = n.get("field", "spill_detected")
                original_val = n.get("original_value", "true")
                corrected_val = n.get("corrected_value", "false")
                cur.execute('''
                    INSERT INTO corrections (
                        asset_id, inspection_id, field_name, original_value,
                        corrected_value, corrected_by, reason, scope, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    asset_id,
                    n["inspection_id"],
                    field_name,
                    original_val,
                    corrected_val,
                    n.get("author_user_id"),
                    n.get("text"),
                    "well",
                    n.get("created_at")
                ))
        total_notes += len(notes_list)

    print("Inserting batches into SQLite...")
    cur.executemany('''
        INSERT INTO inspections VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', insp_batch)

    cur.executemany('''
        INSERT INTO maintenance VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', maint_batch)

    cur.executemany('''
        INSERT OR REPLACE INTO maintenance_reports VALUES (?, ?, ?, ?, ?)
    ''', report_batch)

    cur.executemany('''
        INSERT INTO regulatory_events VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', reg_batch)

    cur.executemany('''
        INSERT INTO context_notes VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', note_batch)

    conn.commit()
    conn.close()

    print(f"Ingestion Complete!")
    print(f"- Wells: {len(well_dirs)}")
    print(f"- Inspections: {total_inspections}")
    print(f"- Maintenance records: {total_maintenance}")
    print(f"- Free-text reports: {total_reports}")
    print(f"- Regulatory events: {total_regulatory}")
    print(f"- Context notes: {total_notes}")

if __name__ == "__main__":
    import sys
    data_dir = sys.argv[1] if len(sys.argv) > 1 else "sample-data"
    ingest_all(data_dir=data_dir)
