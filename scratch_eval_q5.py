import sqlite3

conn = sqlite3.connect('copilot.db')
c = conn.cursor()

c.execute('''
SELECT i.asset_id, a.name, i.inspection_id, i.inspected_at, i.spill_est_volume_bbl
FROM inspections i
JOIN wells w ON i.asset_id = w.asset_id
JOIN areas a ON w.area_id = a.area_id
WHERE (a.name LIKE '%Northeast%' OR a.area_id IN ('AREA-NE-07', 'AREA-NE-08'))
  AND i.inspected_at >= '2026-06-01'
  AND i.spill_detected = 1
  AND i.spill_est_volume_bbl >= 5.0
ORDER BY i.inspected_at
''')
spills = c.fetchall()
print(f"Total qualifying spills: {len(spills)}")
for s in spills:
    asset_id, area_name, insp_id, insp_at, vol = s
    # check if false alarm
    c.execute("SELECT text FROM context_notes WHERE asset_id = ? AND text LIKE '%not crude oil%' AND text LIKE ?", (asset_id, f"%{insp_id}%"))
    false_alarm = c.fetchone()
    
    # find cleanup maint
    c.execute("SELECT maintenance_id, report_file FROM maintenance WHERE asset_id = ? AND issue LIKE '%spill%' AND started_at >= ? ORDER BY started_at LIMIT 1", (asset_id, insp_at[:10]))
    m = c.fetchone()
    m_id = m[0] if m else 'None'
    report_file = m[1] if m else None
    
    has_sample = False
    content_snippet = ""
    if report_file:
        c.execute("SELECT full_text FROM maintenance_reports WHERE asset_id = ? AND report_file = ?", (asset_id, report_file))
        rc = c.fetchone()
        if rc:
            content_snippet = rc[0]
            if "Soil samples sent to the lab." in rc[0]:
                has_sample = True
    
    compliant = "Yes" if has_sample else "No"
    reason = "Lab soil samples confirmed in clean-up report" if has_sample else "Missing 'Soil samples sent to the lab.' in clean-up report"
    if false_alarm:
        compliant = "N/A"
        reason = "Confirmed not crude oil (exempt per SOP)"
        
    print(f"Well: {asset_id} | {area_name} | {insp_id} ({insp_at[:10]}) | Vol: {vol} bbl | Job: {m_id} | Compliant: {compliant} | {reason}")
