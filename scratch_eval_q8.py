import sqlite3
import re

conn = sqlite3.connect('copilot.db')
c = conn.cursor()

# Lots: LOT-2409-A, LOT-2409-C, LOT-2410-B
recalled_lots = ['LOT-2409-A', 'LOT-2409-C', 'LOT-2410-B']

c.execute("""
SELECT asset_id, maintenance_id, report_file, full_text
FROM maintenance_reports
WHERE full_text LIKE '%LOT-2409-A%' OR full_text LIKE '%LOT-2409-C%' OR full_text LIKE '%LOT-2410-B%'
""")
reports = c.fetchall()
print(f"Total reports mentioning recalled lots: {len(reports)}")

pump_installs = {}
for asset_id, m_id, r_file, text in reports:
    # check if installed on this job
    # e.g. **Parts installed:** Highline RP-175 ... LOT-2409-A
    for lot in recalled_lots:
        if lot in text:
            # find install date and cost
            c.execute("SELECT started_at, total_cost FROM maintenance WHERE maintenance_id = ?", (m_id,))
            m_row = c.fetchone()
            started_at = m_row[0] if m_row else "unknown"
            cost = m_row[1] if m_row else 0.0
            
            # Check if there is a later maintenance job that replaced the pump
            c.execute("""
                SELECT maintenance_id, started_at, issue, action_taken
                FROM maintenance
                WHERE asset_id = ? AND started_at > ? AND (
                    issue LIKE '%pump%' OR action_taken LIKE '%pump%' OR action_taken LIKE '%replaced%'
                )
                ORDER BY started_at
            """, (asset_id, started_at))
            later_maint = c.fetchall()
            
            pump_installs[asset_id] = {
                "lot": lot,
                "installed_job": m_id,
                "installed_at": started_at,
                "cost": cost,
                "later_maint": later_maint
            }

print(f"Distinct wells with recalled lots installed: {len(pump_installs)}")
for well, data in sorted(pump_installs.items()):
    c.execute("SELECT w.area_id, a.name FROM wells w JOIN areas a ON w.area_id = a.area_id WHERE w.asset_id = ?", (well,))
    ar = c.fetchone()
    area_name = ar[1] if ar else "Unknown"
    has_later = len(data['later_maint']) > 0
    print(f"Well: {well} ({area_name}) | Lot: {data['lot']} | Job: {data['installed_job']} ({data['installed_at'][:10]}) | Cost: ${data['cost']:,.2f} | Replaced later in DB: {has_later}")
    if has_later:
        for lm in data['later_maint']:
            print(f"   -> Later job: {lm[0]} ({lm[1][:10]}): {lm[2]} | {lm[3]}")
