import sqlite3

conn = sqlite3.connect('copilot.db')
c = conn.cursor()

# Check context notes by area for weather vs parts in 2026
c.execute("""
SELECT a.name, n.text, COUNT(*)
FROM context_notes n
JOIN wells w ON n.asset_id = w.asset_id
JOIN areas a ON w.area_id = a.area_id
WHERE n.created_at >= '2026-01-01' AND n.created_at < '2027-01-01'
  AND (n.text LIKE '%weather%' OR n.text LIKE '%parts%' OR n.text LIKE '%rig delayed%')
GROUP BY a.name, n.text
ORDER BY a.name, COUNT(*) DESC
""")
rows = c.fetchall()
print("Context notes delay reasons by area:")
for r in rows:
    print(r)

# Check downtime hours in maintenance by area
c.execute("""
SELECT a.name,
       COUNT(*) as job_count,
       AVG(m.downtime_hours) as avg_downtime_h,
       AVG((julianday(m.completed_at) - julianday(m.started_at)) * 24.0) as avg_job_duration_h
FROM maintenance m
JOIN wells w ON m.asset_id = w.asset_id
JOIN areas a ON w.area_id = a.area_id
WHERE m.started_at >= '2026-01-01' AND m.started_at < '2027-01-01'
GROUP BY a.name
""")
stats = c.fetchall()
print("\nMaintenance stats by area:")
for s in stats:
    print(s)
