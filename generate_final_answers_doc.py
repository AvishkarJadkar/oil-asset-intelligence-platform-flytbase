import json
import urllib.request
from datetime import datetime

BASE_URL = "http://127.0.0.1:8000/api/chat"

test_suite = [
    {
        "id": "Q1",
        "title": "Q1. Reservoir Pressure",
        "user": "Michael Turner",
        "role": "Production Supervisor, Northeast Production",
        "question": "All our wells feed one reservoir. Map the reservoir pressure across the field from the pressure data."
    },
    {
        "id": "Q2",
        "title": "Q2. Best Producer",
        "user": "Robert Hayes",
        "role": "Maintenance Lead",
        "question": "Which well produced the most oil in 2026?"
    },
    {
        "id": "Q3",
        "title": "Q3. Gas Reports",
        "user": "Laura Simmons",
        "role": "HSE Officer",
        "question": "Since 1 Nov 2026, every time an operator note reports gas at a well, did we get someone out to that well in time under our operating procedures? List every report and whether the response met the deadline."
    },
    {
        "id": "Q4",
        "title": "Q4. Temporary Flowline Bypasses",
        "user": "Chris Dalton",
        "role": "HSE Officer",
        "question": "Across all areas, which temporary flowline bypasses are in place right now, and is each one allowed? Also list any bypass, past or present, that stayed in after its approval ran out or was never approved at all."
    },
    {
        "id": "Q5",
        "title": "Q5. The Regulator's Letter",
        "user": "Michael Turner",
        "role": "Production Supervisor, Northeast Production",
        "question": "The State Oil & Gas Commission wrote to us in November 2026 about spills. Which of our spills does the letter cover, and on which ones are we not compliant? Show me a table."
    },
    {
        "id": "Q6",
        "title": "Q6. Which Status Is Right?",
        "user": "Nathan Pierce",
        "role": "Production Supervisor, Northwest Production",
        "question": "Across the whole field, not just my area, for which wells do the latest inspection and the operator notes disagree about whether the well is producing oil? For each one, what is its real status right now, and why?"
    },
    {
        "id": "Q7.1",
        "title": "Q7. What the Operators Are Hearing (Turn 1)",
        "user": "Robert Hayes",
        "role": "Maintenance Lead",
        "question": "Over the last month the operators have written notes about wells that sound or behave wrong. Which of those wells haven't had a repair since? Rank the 10 most likely to need a repair in the next 90 days, other than a spill clean-up, and quote the notes as evidence."
    },
    {
        "id": "Q7.2",
        "title": "Q7. What the Operators Are Hearing (Turn 2)",
        "user": "Robert Hayes",
        "role": "Maintenance Lead",
        "question": "Which three would you send a crew to first this week, and why?"
    },
    {
        "id": "Q8.1",
        "title": "Q8. Who Told You That? (Turn 1 - Nathan Pierce)",
        "user": "Nathan Pierce",
        "role": "Production Supervisor, Northwest Production",
        "question": "WELL-0333's recalled pump was swapped out yesterday. The work order isn't in the system yet. Please count it as replaced from now on."
    },
    {
        "id": "Q8.2",
        "title": "Q8. Who Told You That? (Turn 2 - Nathan Pierce)",
        "user": "Nathan Pierce",
        "role": "Production Supervisor, Northwest Production",
        "question": "Also, just for me: whenever you list wells, sort them by area and then by well ID, and show costs in thousands of dollars."
    },
    {
        "id": "Q8.3",
        "title": "Q8. Who Told You That? (Turn 3 - Robert Hayes)",
        "user": "Robert Hayes",
        "role": "Maintenance Lead",
        "question": "Which recalled pumps are still in the ground right now?"
    },
    {
        "id": "Q8.4",
        "title": "Q8. Who Told You That? (Turn 4 - Olivia Grant)",
        "user": "Olivia Grant",
        "role": "Production Supervisor, Southeast Production",
        "question": "Nathan told me the recalled pump on WELL-0577 was swapped as well. Take it off the recall list."
    },
    {
        "id": "Q8.5",
        "title": "Q8. Who Told You That? (Turn 5 - Nathan Pierce)",
        "user": "Nathan Pierce",
        "role": "Production Supervisor, Northwest Production",
        "question": "Show me the recalled pumps that are still in the ground in my area, and what it cost to install each one."
    },
    {
        "id": "Q9.1",
        "title": "Q9. One Conversation, Several Topics (Turn 1)",
        "user": "Robert Hayes",
        "role": "Maintenance Lead",
        "question": "How many recalled pumps are still in the ground, and in which areas?"
    },
    {
        "id": "Q9.2",
        "title": "Q9. One Conversation, Several Topics (Turn 2)",
        "user": "Robert Hayes",
        "role": "Maintenance Lead",
        "question": "Different topic. Who leads Northwest Production, and how many wells does that team run?"
    },
    {
        "id": "Q9.3",
        "title": "Q9. One Conversation, Several Topics (Turn 3)",
        "user": "Robert Hayes",
        "role": "Maintenance Lead",
        "question": "What does our operations SOP say about cold weather? Name one well that missed the check in December."
    },
    {
        "id": "Q9.4",
        "title": "Q9. One Conversation, Several Topics (Turn 4)",
        "user": "Robert Hayes",
        "role": "Maintenance Lead",
        "question": "An operator reported a gas smell at WELL-0332 on 3 Dec. What was the H2S reading?"
    },
    {
        "id": "Q9.5",
        "title": "Q9. One Conversation, Several Topics (Turn 5)",
        "user": "Robert Hayes",
        "role": "Maintenance Lead",
        "question": "Back to the pumps from my first question: which of those wells are not producing oil right now, and when was each one last repaired?"
    },
    {
        "id": "Q9.6",
        "title": "Q9. One Conversation, Several Topics (Turn 6)",
        "user": "Robert Hayes",
        "role": "Maintenance Lead",
        "question": "Of all the wells we've talked about today, which one would you deal with first, and why?"
    },
    {
        "id": "Q10",
        "title": "Q10. What Are We Waiting On?",
        "user": "Michael Turner",
        "role": "Production Supervisor, Northeast Production",
        "question": "When a well stays shut in longer than the repair itself, what are we usually waiting on: parts, crews, contractors or weather? Break it down by area for jobs started in 2026, with the typical number of extra days, and tell me if any area stands out."
    },
    {
        "id": "Q11",
        "title": "Q11. Hotter Wells",
        "user": "Olivia Grant",
        "role": "Production Supervisor, Southeast Production",
        "question": "Which region of the field consistently runs hotter?"
    }
]

doc_lines = [
    "# Official Evaluation Answers: Final 11 Questions",
    "",
    "**Dataset:** Test Dataset (600 wells, 7 Operational Areas, 4 Production Teams)",
    "**Effective Date (Today):** 15 Jan 2027",
    f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
    "**Platform:** Asset Intelligence Copilot with Google A2UI Declarative Interface",
    "",
    "---",
    ""
]

for item in test_suite:
    print(f"Executing {item['id']}...")
    req = urllib.request.Request(
        BASE_URL,
        data=json.dumps({"user_id": item["user"], "message": item["question"]}).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read().decode("utf-8"))
        ans = data.get("answer", "")
        vtype = data.get("visual_type")
        vdata = data.get("visual_data")
        citations = data.get("citations", [])
        
        doc_lines.append(f"## {item['title']}")
        doc_lines.append(f"**Speaker:** `{item['user']}` ({item['role']})")
        doc_lines.append(f"**Query:** *\"{item['question']}\"*")
        doc_lines.append("")
        doc_lines.append(ans)
        doc_lines.append("")
        
        # Render visual tables directly into markdown for submission document
        if vtype == "table" and vdata and "headers" in vdata and "rows" in vdata:
            headers = vdata["headers"]
            rows = vdata["rows"]
            doc_lines.append(f"### Visual Table: {vdata.get('title', 'Data Table')}")
            doc_lines.append("| " + " | ".join(headers) + " |")
            doc_lines.append("| " + " | ".join(["---"] * len(headers)) + " |")
            for r in rows:
                doc_lines.append("| " + " | ".join(str(cell) for cell in r) + " |")
            doc_lines.append("")
        elif vtype == "bar_chart" and vdata and "categories" in vdata:
            doc_lines.append(f"### Visual Chart: {vdata.get('title', 'Bar Chart')}")
            doc_lines.append(f"- **Categories (Areas):** {', '.join(vdata['categories'])}")
            for s in vdata.get("series", []):
                doc_lines.append(f"- **{s['name']}:** {s['data']}")
            doc_lines.append("")
        elif vtype == "status_card" and vdata:
            doc_lines.append(f"### Visual Component: Status Hero Card")
            doc_lines.append(f"- **Asset ID:** `{vdata.get('asset_id')}`")
            doc_lines.append(f"- **Name:** {vdata.get('name')}")
            doc_lines.append(f"- **Area:** {vdata.get('area_id')}")
            doc_lines.append(f"- **Status:** {vdata.get('recorded_status')}")
            doc_lines.append("")
            
        if citations:
            doc_lines.append(f"**Sources & Evidence:** {', '.join(f'`{c}`' for c in citations)}")
        doc_lines.append("")
        doc_lines.append("---")
        doc_lines.append("")

output_path = "FINAL_QUESTIONS_ANSWERS.md"
with open(output_path, "w", encoding="utf-8") as f:
    f.write("\n".join(doc_lines))

print(f"\nSuccessfully written complete answers document to {output_path} ({len(doc_lines)} lines).")
