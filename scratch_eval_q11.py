import sqlite3

conn = sqlite3.connect('copilot.db')
c = conn.cursor()

c.execute("""
SELECT a.name,
       COUNT(*) as inspection_count,
       AVG(i.ambient_temp_c) as avg_ambient,
       AVG(i.wellhead_temp_c) as avg_wellhead,
       AVG(i.temp_diff) as avg_delta_t,
       MAX(i.wellhead_temp_c) as max_wellhead
FROM inspections i
JOIN wells w ON i.asset_id = w.asset_id
JOIN areas a ON w.area_id = a.area_id
GROUP BY a.name
ORDER BY avg_wellhead DESC
""")
rows = c.fetchall()
print("Temperature stats by area:")
for r in rows:
    print(f"Area: {r[0]:20} | Inspections: {r[1]:6} | Avg Ambient: {r[2]:.2f}°C | Avg Wellhead: {r[3]:.2f}°C | Avg dT: {r[4]:.2f}°C | Max Wellhead: {r[5]:.2f}°C")
