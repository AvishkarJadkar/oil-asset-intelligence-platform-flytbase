import sqlite3

conn = sqlite3.connect('copilot.db')
c = conn.cursor()

print("--- Q9.2 Northwest Production Team ---")
c.execute("SELECT u.name, u.role FROM users u WHERE u.team_id = 'TEAM-NW' AND u.role = 'production_supervisor'")
print("Supervisor:", c.fetchall())
c.execute("SELECT COUNT(*) FROM wells WHERE team_id = 'TEAM-NW'")
print("Wells run by TEAM-NW:", c.fetchone()[0])

print("\n--- Q9.3 OPS-5 Cold Weather in December 2026 ---")
c.execute("""
SELECT i.asset_id, a.name, i.inspection_id, i.inspected_at, i.ambient_temp_c, i.producing
FROM inspections i
JOIN wells w ON i.asset_id = w.asset_id
JOIN areas a ON w.area_id = a.area_id
WHERE i.inspected_at >= '2026-12-01' AND i.inspected_at < '2027-01-01'
  AND i.ambient_temp_c <= -5.0
  AND i.producing = 1
ORDER BY i.inspected_at
""")
cold_insps = c.fetchall()
print(f"Total cold producing inspections: {len(cold_insps)}")
for asset_id, area_name, insp_id, insp_at, amb, prod in cold_insps:
    # Check if heat trace check started within 7 days
    c.execute("""
        SELECT maintenance_id, started_at, issue
        FROM maintenance
        WHERE asset_id = ? AND issue LIKE '%Heat trace check%'
          AND started_at >= ? AND started_at <= date(?, '+7 days')
    """, (asset_id, insp_at[:10], insp_at[:10]))
    m = c.fetchone()
    if not m:
        # Check any heat trace check after insp_at
        c.execute("""
            SELECT maintenance_id, started_at, issue
            FROM maintenance
            WHERE asset_id = ? AND issue LIKE '%Heat trace check%' AND started_at >= ?
        """, (asset_id, insp_at[:10]))
        any_m = c.fetchone()
        print(f"MISSED CHECK: Well {asset_id} ({area_name}) on {insp_at[:10]} (amb: {amb}°C). Any later: {any_m}")

print("\n--- Q10 Waiting on reasons in 2026 ---")
c.execute("""
SELECT full_text FROM maintenance_reports
WHERE full_text LIKE '%waiting on%' OR full_text LIKE '%waiting for%' OR full_text LIKE '%delayed by%'
LIMIT 5
""")
sample_reports = c.fetchall()
print(f"Sample delayed reports count: {len(sample_reports)}")
if sample_reports:
    print(sample_reports[0][0][:300])
