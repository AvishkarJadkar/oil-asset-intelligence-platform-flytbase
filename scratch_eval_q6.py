import sqlite3

conn = sqlite3.connect('copilot.db')
c = conn.cursor()

def eval_q6():
    c.execute("SELECT asset_id, area_id FROM wells")
    wells = c.fetchall()
    disagreements = []
    
    for asset_id, area_id in wells:
        # Latest inspection
        c.execute("""
            SELECT inspection_id, inspected_at, producing, ambient_temp_c, wellhead_temp_c, temp_diff
            FROM inspections WHERE asset_id = ?
            ORDER BY inspected_at DESC LIMIT 1
        """, (asset_id,))
        insp = c.fetchone()
        if not insp:
            continue
        insp_id, insp_at, insp_prod, amb, wh, diff = insp
        
        # Check latest shut in or restart operator note
        c.execute("""
            SELECT text, created_at FROM context_notes
            WHERE asset_id = ? AND (
                text LIKE '%shut in%' OR text LIKE '%shut-in%' OR
                text LIKE '%restarted%' OR text LIKE '%started back up%' or text LIKE '%brought back online%'
            )
            ORDER BY created_at DESC LIMIT 1
        """, (asset_id,))
        note = c.fetchone()
        if not note:
            continue
        
        note_text, note_at = note
        is_shut_in = any(k in note_text.lower() for k in ['shut in', 'shut-in'])
        is_restart = any(k in note_text.lower() for k in ['restart', 'started back up', 'brought back online'])
        
        # Compare dates and status
        # If note is more recent than inspection
        if note_at > insp_at:
            if is_shut_in and insp_prod == 1:
                # Disagreement! Insp says producing, note says shut in
                c.execute("SELECT name FROM areas WHERE area_id = ?", (area_id,))
                area_name = c.fetchone()[0]
                disagreements.append({
                    "well": asset_id,
                    "area": area_name,
                    "insp": f"{insp_id} ({insp_at[:10]}, Producing)",
                    "note": f"{note_at[:16].replace('T', ' ')}: \"{note_text}\"",
                    "status_now": "Not producing oil (shut in)",
                    "why": f"Operator shut-in note on {note_at[:10]} is more recent than latest inspection ({insp_at[:10]}) per OPS-3"
                })
            elif is_restart and insp_prod == 0:
                # Disagreement! Insp says not producing, note says restart
                c.execute("SELECT name FROM areas WHERE area_id = ?", (area_id,))
                area_name = c.fetchone()[0]
                disagreements.append({
                    "well": asset_id,
                    "area": area_name,
                    "insp": f"{insp_id} ({insp_at[:10]}, Not producing)",
                    "note": f"{note_at[:16].replace('T', ' ')}: \"{note_text}\"",
                    "status_now": "Producing oil (unconfirmed)",
                    "why": f"Operator restart note on {note_at[:10]} is more recent than latest inspection ({insp_at[:10]}) per OPS-3"
                })
        else:
            # Inspection is more recent than note. If note said shut in, but insp is producing
            # Or note said restarted, but insp is not producing
            pass
            
    return disagreements

res = eval_q6()
print(f"Total disagreements: {len(res)}")
for d in res:
    print(d)
