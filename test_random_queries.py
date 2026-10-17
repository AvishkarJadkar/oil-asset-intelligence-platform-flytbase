"""
Test script for verifying that the Copilot handles arbitrary/random English queries
accurately and generates relevant answers with Generative UI components.
"""
test_queries = [
    ("Michael Turner", "How many wells are producing oil right now across the entire field?"),
    ("Michael Turner", "Who is Tyler Hughes?"),
    ("Michael Turner", "List all field inspectors"),
    ("Michael Turner", "List all wells in Southwest Block 23"),
    ("Michael Turner", "What is WELL-0025?"),
    ("Michael Turner", "What equipment is installed on WELL-0010?"),
    ("Michael Turner", "Show me the latest 5 repairs across the field"),
    ("Michael Turner", "Which well had the most expensive repair?"),
    ("Michael Turner", "What is the operating threshold for T350 wells?"),
    ("Michael Turner", "How many total inspections have been performed?"),
    ("Michael Turner", "Did WELL-0050 have any repairs this year?"),
    ("Michael Turner", "Which area has the most spills?"),
    ("Michael Turner", "What does rule SR-01 require?"),
    ("Michael Turner", "Show me the top 5 wells with the highest wellhead temperature"),
    ("Michael Turner", "How much total money was spent on maintenance in 2025?")
]

if __name__ == "__main__":
    import copilot_agent
    engine = copilot_agent.CopilotEngine()
    print("Testing random queries...")
    for uid, q in test_queries:
        res = engine.handle_query(uid, q)
        ans = res["answer"]
        vtype = res.get("visual_type")
        a2ui_type = res.get("a2ui", {}).get("protocol")
        print(f"\nQ: {q}")
        print(f"Visual: {vtype} | A2UI: {a2ui_type}")
        safe_ans = ans[:150].encode('ascii', 'replace').decode()
        print(f"Answer: {safe_ans}...")

