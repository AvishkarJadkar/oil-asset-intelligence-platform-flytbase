import sqlite3

conn = sqlite3.connect('copilot.db')
c = conn.cursor()

c.execute("""
SELECT n.asset_id, a.name, n.text, n.created_at
FROM context_notes n
JOIN wells w ON n.asset_id = w.asset_id
JOIN areas a ON w.area_id = a.area_id
WHERE n.created_at >= '2026-12-15'
ORDER BY n.created_at
""")
notes = c.fetchall()
keywords = ['sound', 'noise', 'vibrat', 'knock', 'squeal', 'grind', 'behave', 'rough', 'groan', 'rattle', 'clunk', 'pound', 'shak', 'sluggish', 'hesitat']

candidates = []
for asset_id, area_name, text, created_at in notes:
    t_lower = text.lower()
    if any(k in t_lower for k in keywords):
        # Check if repaired since created_at (excluding spill cleanup)
        c.execute("""
            SELECT maintenance_id, started_at, issue, action_taken
            FROM maintenance
            WHERE asset_id = ? AND started_at > ? AND issue NOT LIKE '%spill%'
            ORDER BY started_at
        """, (asset_id, created_at))
        maint = c.fetchall()
        if len(maint) == 0:
            # Last repair on the well prior to this
            c.execute("""
                SELECT maintenance_id, completed_at, issue
                FROM maintenance
                WHERE asset_id = ? AND completed_at <= ? AND issue NOT LIKE '%spill%'
                ORDER BY completed_at DESC LIMIT 1
            """, (asset_id, created_at))
            last_m = c.fetchone()
            last_m_str = f"{last_m[0]} ({last_m[1][:10]}): {last_m[2]}" if last_m else "None"
            
            # Telemetry warning signs (e.g. temp diff trend, producing status)
            c.execute("""
                SELECT inspected_at, temp_diff, producing
                FROM inspections WHERE asset_id = ?
                ORDER BY inspected_at DESC LIMIT 2
            """, (asset_id,))
            insps = c.fetchall()
            warn = []
            if insps:
                curr = insps[0]
                warn.append(f"dT={curr[1]}°C, Prod={curr[2]}")
                if len(insps) > 1:
                    prev = insps[1]
                    if curr[1] < prev[1]:
                        warn.append(f"dT dropped from {prev[1]}°C")
            
            candidates.append({
                "well": asset_id,
                "area": area_name,
                "note_at": created_at[:16].replace('T', ' '),
                "quote": text,
                "last_repair": last_m_str,
                "warning_signs": ", ".join(warn)
            })

print(f"Total candidates: {len(candidates)}")
for idx, cand in enumerate(candidates, 1):
    print(f"[{idx}] {cand['well']} ({cand['area']}) | {cand['note_at']} | \"{cand['quote']}\" | Signs: {cand['warning_signs']} | Last: {cand['last_repair']}")
