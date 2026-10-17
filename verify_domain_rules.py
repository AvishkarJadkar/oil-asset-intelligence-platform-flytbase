import sqlite3

conn = sqlite3.connect("copilot.db")
cur = conn.cursor()

print("--- Testing Q1: WELL-0001 Latest Inspection ---")
cur.execute('''
    SELECT i.inspection_id, i.inspected_at, i.ambient_temp_c, i.wellhead_temp_c, i.temp_diff, i.producing, w.recorded_status
    FROM inspections i
    JOIN wells w ON i.asset_id = w.asset_id
    WHERE i.asset_id = 'WELL-0001'
    ORDER BY i.inspected_at DESC LIMIT 1
''')
print("Q1 latest:", cur.fetchone())

print("\n--- Testing Q2: Northeast Block 8 not producing right now ---")
cur.execute('''
    WITH latest AS (
        SELECT i.*, ROW_NUMBER() OVER (PARTITION BY i.asset_id ORDER BY i.inspected_at DESC) as rn
        FROM inspections i
        JOIN wells w ON i.asset_id = w.asset_id
        JOIN areas a ON w.area_id = a.area_id
        WHERE a.name = 'Northeast Block 8'
    )
    SELECT asset_id, inspected_at, temp_diff, producing, notes
    FROM latest
    WHERE rn = 1 AND producing = 0
    ORDER BY asset_id
''')
for r in cur.fetchall():
    print("Q2 non-producing:", r)

print("\n--- Testing Q4: WELL-0001 Spills in last 4 years (minus corrected) ---")
cur.execute('''
    SELECT i.inspection_id, i.inspected_at, i.spill_est_volume_bbl
    FROM inspections i
    WHERE i.asset_id = 'WELL-0001'
      AND i.spill_detected = 1
      AND i.inspection_id NOT IN (
          SELECT inspection_id FROM corrections WHERE asset_id = 'WELL-0001' AND corrected_value = 'false'
      )
    ORDER BY i.inspected_at ASC
''')
rows = cur.fetchall()
total_bbl = sum(r[2] for r in rows if r[2] is not None)
print(f"Q4 Spills count: {len(rows)}, Total volume: {total_bbl:.1f} bbl")
for r in rows:
    print(" ", r)

print("\n--- Testing Q5: WELL-0001 Downtime in 2025 ---")
cur.execute('''
    SELECT inspection_id, inspected_at, ambient_temp_c, wellhead_temp_c, temp_diff, producing
    FROM inspections
    WHERE asset_id = 'WELL-0001'
      AND inspected_at >= '2025-01-01' AND inspected_at <= '2025-12-31'
      AND producing = 0
''')
down_rows = cur.fetchall()
print(f"Q5 non-producing weeks: {len(down_rows)} (= {len(down_rows)*7} days downtime)")
for r in down_rows:
    print(" ", r)

print("\n--- Testing Q6: Top 3 wells in Northeast Block 7 downtime (2026-06-16 to 2026-10-16) ---")
cur.execute('''
    SELECT w.asset_id, w.well_type, COUNT(*) as down_weeks, COUNT(*) * 7 as downtime_days
    FROM inspections i
    JOIN wells w ON i.asset_id = w.asset_id
    JOIN areas a ON w.area_id = a.area_id
    WHERE a.name = 'Northeast Block 7'
      AND i.inspected_at >= '2026-06-16' AND i.inspected_at <= '2026-10-16T23:59:59'
      AND i.producing = 0
    GROUP BY w.asset_id
    ORDER BY downtime_days DESC
    LIMIT 4
''')
for r in cur.fetchall():
    print("Q6 top downtime:", r)

print("\n--- Testing Q10: Southwest Block 24 containment > 4h in last 90 days ---")
cur.execute('''
    SELECT mr.asset_id, mr.report_file, mr.containment_hours
    FROM maintenance_reports mr
    JOIN wells w ON mr.asset_id = w.asset_id
    JOIN areas a ON w.area_id = a.area_id
    WHERE a.name = 'Southwest Block 24'
      AND mr.containment_hours > 4
''')
for r in cur.fetchall():
    print("Q10 containment violation:", r)

conn.close()
