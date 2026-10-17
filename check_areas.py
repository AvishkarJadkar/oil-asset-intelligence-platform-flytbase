import agent_tools
rows = agent_tools.execute_query("SELECT area_id, name FROM areas ORDER BY area_id")
for r in rows:
    print(r)
