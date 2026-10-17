import sqlite3

conn = sqlite3.connect('copilot.db')
c = conn.cursor()

c.execute("SELECT text FROM context_notes WHERE text LIKE '%wait%' LIMIT 10")
notes = c.fetchall()
print(f"Context notes with 'wait': {len(notes)}")
for n in notes:
    print("Note:", n[0])

c.execute("SELECT full_text FROM maintenance_reports WHERE full_text LIKE '%waiting%' OR full_text LIKE '%delayed%' OR full_text LIKE '%delay%' LIMIT 5")
reps = c.fetchall()
print(f"Reports with wait/delay: {len(reps)}")
for r in reps:
    print("Report:", r[0][:200])

# Check downtime vs duration in maintenance
c.execute("""
SELECT asset_id, started_at, completed_at, downtime_hours, issue
FROM maintenance
WHERE started_at >= '2026-01-01' AND started_at < '2027-01-01' AND downtime_hours > 0
LIMIT 10
""")
m_rows = c.fetchall()
print("Sample maintenance downtime:")
for m in m_rows[:5]:
    print(m)
