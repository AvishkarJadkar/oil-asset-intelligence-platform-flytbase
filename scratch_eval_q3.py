import sqlite3
import datetime

conn = sqlite3.connect('copilot.db')
c = conn.cursor()

def eval_q3():
    c.execute('''
    SELECT n.asset_id, a.name, n.text, n.created_at
    FROM context_notes n
    JOIN wells w ON n.asset_id = w.asset_id
    JOIN areas a ON w.area_id = a.area_id
    WHERE n.created_at >= '2026-11-01'
    ORDER BY n.created_at
    ''')
    notes = c.fetchall()
    gas_keywords = ['gas smell', 'rotten-egg', 'gas odor', 'h2s monitor', 'alarmed', 'smelled gas']
    rows = []
    for asset_id, area_name, text, created_at in notes:
        if not any(k in text.lower() for k in gas_keywords):
            continue
        dt_report = datetime.datetime.fromisoformat(created_at.replace('Z', '+00:00'))
        deadline_hrs = 12 if created_at >= '2027-01-01' else 24

        c.execute('SELECT maintenance_id, started_at FROM maintenance WHERE asset_id = ? AND started_at > ? ORDER BY started_at LIMIT 1', (asset_id, created_at))
        maint = c.fetchone()

        c.execute("SELECT inspection_id, inspected_at FROM inspections WHERE asset_id = ? AND inspected_at > ? AND method = 'manual' ORDER BY inspected_at LIMIT 1", (asset_id, created_at))
        insp = c.fetchone()

        first_resp = None
        if maint and insp:
            if maint[1] <= insp[1]:
                first_resp = (maint[0], maint[1])
            else:
                first_resp = (insp[0], insp[1])
        elif maint:
            first_resp = (maint[0], maint[1])
        elif insp:
            first_resp = (insp[0], insp[1])

        if first_resp:
            resp_id, resp_at = first_resp
            dt_resp = datetime.datetime.fromisoformat(resp_at.replace('Z', '+00:00'))
            delta_hrs = (dt_resp - dt_report).total_seconds() / 3600.0
            status = 'Met' if delta_hrs <= deadline_hrs else 'Missed'
            resp_str = f"{resp_id} ({resp_at[:16].replace('T', ' ')})"
            hrs_str = f"{delta_hrs:.1f}"
        else:
            resp_str = 'None'
            hrs_str = 'N/A'
            status = 'Missed'

        rows.append({
            'Well': asset_id,
            'Area': area_name,
            'Reported at': created_at[:16].replace('T', ' '),
            'Response': resp_str,
            'Hours to response': hrs_str,
            'Deadline': f"{deadline_hrs}h",
            'Met / Missed': status
        })
    return rows

rows = eval_q3()
print(f"Q3 Gas Reports Count: {len(rows)}")
for r in rows:
    print(r)
