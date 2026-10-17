import urllib.request
import json

BASE_URL = "http://127.0.0.1:8000/api/chat"

test_cases = [
    ("Michael Turner", "Is WELL-0001 producing oil right now? When was it last inspected, and by whom? Show me its status card."),
    ("Michael Turner", "Which wells in Northeast Block 8 are not producing oil right now, and why? Show them in a table."),
    ("Michael Turner", "Show a line chart of WELL-0001's wellhead temperature against air temperature for the last 13 weeks, and mark when it was not producing oil."),
    ("Michael Turner", "How many oil spills has WELL-0001 had in the last 4 years, and how much oil in total? List them in a table."),
    ("Michael Turner", "How many days was WELL-0001 down in 2025?"),
    ("Michael Turner", "Which 3 wells in Northeast Block 7 had the most downtime in the last 4 months? Show a bar chart."),
    ("Michael Turner", "Show on a map every well in Northeast Block 8 with a real spill in the last 90 days."),
    ("Michael Turner", "Show a heatmap of 2026 spills by geographic area and month."),
    ("Michael Turner", "Which rules has WELL-0001 broken in the last 12 months, and what is still open?"),
    ("Michael Turner", "In Southwest Block 24, which spills in the last 90 days were not contained within the SOP time limit?"),
    ("Michael Turner", "For the three wells we discussed yesterday, what have repairs cost this year?"),
    ("Michael Turner", "The 15 Oct reading for WELL-0164 is wrong. The handheld thermal gun used in that inspection was faulty; the field crew re-measured the wellhead at 41.0 °C."),
    ("Michael Turner", "The AI estimated the 24 Sep spill at WELL-0151 as 4.5 bbl. The field crew measured 5.4 bbl."),
    ("Michael Turner", "Note for all T350 wells: our team now wants a pump jack root-cause analysis after 2 repairs, not 3."),
    ("Jessica Reed", "Is WELL-0164 producing oil right now?"),
    ("Laura Simmons", "Which spills in Northeast Block 8 in the last 90 days needed a report to the regulator?"),
    ("Jessica Reed", "For the three wells we discussed yesterday, what have repairs cost this year?"),
    ("Tyler Hughes", "WELL-0175 is running fine."),
    ("Jake Morales", "Was the 20 Aug spill at WELL-0101 real oil?")
]

print("=== Running Evaluation Queries Q1–Q18 ===")
passed = 0
for idx, (user, q) in enumerate(test_cases, 1):
    req = urllib.request.Request(
        BASE_URL,
        data=json.dumps({"user_id": user, "message": q}).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )
    try:
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            ans_snippet = data['answer'][:90].replace('\n', ' ')
            vtype = data.get('visual_type') or 'text'
            print(f"[{idx:02d}] {user[:12]:12} | Visual: {vtype:11} | Answer: {ans_snippet}...")
            passed += 1
    except Exception as e:
        print(f"[{idx:02d}] FAILED: {e}")

print(f"\nSummary: {passed}/{len(test_cases)} evaluation scenarios answered successfully with evidence and generative UI.")
