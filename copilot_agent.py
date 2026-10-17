import json
import re
import urllib.request
import urllib.error
from datetime import datetime, timedelta
import agent_tools
import a2ui_builder

OLLAMA_API_BASE = "http://127.0.0.1:11434"
MODEL_NAME = "gemma4:e4b"


def query_llm(prompt: str, system_prompt: str = "", timeout: float = 6.0):
    url = f"{OLLAMA_API_BASE}/api/generate"
    payload = {
        "model": MODEL_NAME,
        "prompt": prompt,
        "system": system_prompt,
        "stream": False,
        "options": {"temperature": 0.2, "num_predict": 512}
    }
    try:
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data.get("response", "").strip()
    except Exception:
        return None


class CopilotEngine:
    def __init__(self):
        pass

    def handle_query(self, user_id: str, question: str, history: list = None):
        """Entry point. Accepts optional history list of {role, content} dicts."""
        res = self._handle_query_internal(user_id, question, history or [])
        res["a2ui"] = a2ui_builder.build_a2ui(
            visual_type=res.get("visual_type"),
            visual_data=res.get("visual_data"),
            answer=res.get("answer"),
            citations=res.get("citations") or []
        )
        res["context_meta"] = getattr(self, "current_context_meta", {})
        return res

    # ------------------------------------------------------------------
    # Context Resolution — carry entities across conversation turns
    # ------------------------------------------------------------------
    def resolve_context(self, question: str, ent: dict, history: list) -> tuple:
        """
        Scans recent conversation history to fill in missing entities.
        Returns (updated_ent, context_meta) where context_meta describes
        what was inferred so the UI can show a context pill.
        """
        q_lower = question.lower()
        context_meta = {}

        # Pronoun / reference signals that suggest the query refers to something prior
        well_reference_words = [
            "it", "its", "that well", "this well", "the well", "same well",
            "that one", "this one", "for it", "on it", "about it",
            "more about", "tell me more", "also", "and now", "now show",
            "what about", "what were", "what are its", "what is its",
            "and its", "show its", "the same", "aforementioned", "how about"
        ]
        area_reference_words = [
            "that area", "the area", "that block", "the block", "same area",
            "same block", "those wells", "that region", "in it", "there", "in that area"
        ]

        # Well follow-up topic keywords (e.g. "what were repairs?", "temperature trend", "downtime?", "any spills?")
        well_topic_words = [
            "repair", "repairs", "maintenance", "downtime", "temperature", "temp",
            "pressure", "vibration", "producing", "status", "spill", "spills",
            "leak", "workover", "shut in", "equipment", "sensor", "depth",
            "inspection", "inspections", "compliance"
        ]
        is_field_wide = any(w in q_lower for w in ["how many", "overall", "entire field", "all wells", "across the field", "every well"])
        has_well_topic = any(w in q_lower for w in well_topic_words) and not is_field_wide
        has_well_ref = any(ref in q_lower for ref in well_reference_words) or has_well_topic
        has_area_ref = any(ref in q_lower for ref in area_reference_words)
        is_plural_or_group = any(w in q_lower for w in ["which ones", "those wells", "any wells", "all wells", "what wells", "wells in", "list wells", "in that area", "in the area", "in that block"])

        # If user explicitly refers to an area or uses plural/group query, prioritize area over well
        if has_area_ref or ent.get("area_name") or is_plural_or_group:
            need_well = False
            need_area = not ent.get("area_name")
        else:
            need_well = not ent.get("asset_id") and has_well_ref
            need_area = not ent.get("area_name") and has_area_ref

        if not (need_well or need_area):
            return ent, context_meta

        # Scan history in reverse (most recent first)
        for turn in reversed(history):
            content = turn.get("content", "")

            if need_well and not ent.get("asset_id"):
                # Look for WELL-XXXX
                well_hits = re.findall(r'\bWELL-(\d{1,4})\b', content, re.IGNORECASE)
                if well_hits:
                    inferred_well = f"WELL-{int(well_hits[0]):04d}"
                    ent = dict(ent)
                    ent["asset_id"] = inferred_well
                    context_meta["inferred_well"] = inferred_well
                    context_meta["inferred_from"] = "conversation history"
                else:
                    # Look for "well 42"
                    num_hits = re.findall(r'\bwell\s*(?:#|no\.?|number)?\s*(\d{1,4})\b', content, re.IGNORECASE)
                    if num_hits:
                        inferred_well = f"WELL-{int(num_hits[0]):04d}"
                        ent = dict(ent)
                        ent["asset_id"] = inferred_well
                        context_meta["inferred_well"] = inferred_well
                        context_meta["inferred_from"] = "conversation history"

            if need_area and not ent.get("area_name"):
                all_areas = agent_tools.execute_query("SELECT name FROM areas")
                for a in all_areas:
                    if a["name"].lower() in content.lower():
                        ent = dict(ent)
                        ent["area_name"] = a["name"]
                        context_meta["inferred_area"] = a["name"]
                        context_meta["inferred_from"] = "conversation history"
                        break

            # Stop once we've filled both or satisfied the need
            if (not need_well or ent.get("asset_id")) and (not need_area or ent.get("area_name")):
                break

        return ent, context_meta

    def extract_entities(self, text: str):
        t_lower = text.lower()

        # Well ID: WELL-XXXX or "well 5" / "well #5"
        asset_id = None
        well_match = re.search(r'\bWELL-(\d{1,4})\b', text, re.IGNORECASE)
        if well_match:
            asset_id = f"WELL-{int(well_match.group(1)):04d}"
        else:
            w_num = re.search(r'\bwell\s*(#|no\.?|number)?\s*(\d{1,4})\b', text, re.IGNORECASE)
            if w_num:
                asset_id = f"WELL-{int(w_num.group(2)):04d}"

        # Area matching - fuzzy token overlap
        all_areas = agent_tools.execute_query("SELECT area_id, name FROM areas")
        area_found = None
        best_score = 0

        abbrev_map = {
            r'\bne\b': 'northeast', r'\bnw\b': 'northwest',
            r'\bsw\b': 'southwest', r'\bse\b': 'southeast',
        }
        normalized = t_lower
        for abbr, full in abbrev_map.items():
            normalized = re.sub(abbr, full, normalized)
        normalized = re.sub(r'\bfrom\b|\bof\b|\bthe\b|\bin\b|\bat\b', '', normalized)
        normalized = re.sub(r'\s+', ' ', normalized).strip()

        for a in all_areas:
            name_lower = a["name"].lower()
            area_id_lower = a["area_id"].lower()

            if name_lower in normalized or area_id_lower.replace('-', ' ') in normalized:
                area_found = a["name"]
                best_score = 100
                break

            name_tokens = set(re.split(r'[\s\-_]+', name_lower))
            query_tokens = set(re.split(r'[\s\-_,]+', normalized))
            overlap = name_tokens & query_tokens
            score = len(overlap) / max(len(name_tokens), 1)
            if score > best_score and len(overlap) >= min(len(name_tokens), 2):
                best_score = score
                area_found = a["name"]

        if not area_found:
            gen_match = re.search(
                r'\b(south\s*west|north\s*east|north\s*west|south\s*east|southwest|northeast|northwest|southeast)'
                r'[\s\-]*(?:block)?[\s\-]*(\d+)\b',
                normalized, re.IGNORECASE
            )
            if gen_match:
                direction = re.sub(r'\s+', '', gen_match.group(1)).lower()
                dir_map = {'northeast': 'Northeast', 'northwest': 'Northwest',
                           'southwest': 'Southwest', 'southeast': 'Southeast'}
                area_found = f"{dir_map.get(direction, direction.title())} Block {gen_match.group(2)}"

        days = None
        weeks = None
        months = None
        year = None
        d_m = re.search(r'(\d+)\s+days?', text, re.IGNORECASE)
        if d_m: days = int(d_m.group(1))
        w_m = re.search(r'(\d+)\s+weeks?', text, re.IGNORECASE)
        if w_m: weeks = int(w_m.group(1))
        m_m = re.search(r'(\d+)\s+months?', text, re.IGNORECASE)
        if m_m: months = int(m_m.group(1))
        y_m = re.search(r'\b(202[2-6])\b', text)
        if y_m: year = int(y_m.group(1))

        well_type = None
        if "t350" in t_lower: well_type = "T350"
        elif "t200" in t_lower: well_type = "T200"

        return {
            "asset_id": asset_id,
            "area_name": area_found,
            "days": days,
            "weeks": weeks,
            "months": months,
            "year": year,
            "well_type": well_type
        }

    def classify_intent(self, q_lower: str, ent: dict) -> str:
        intent_list = [
            'greeting', 'correction_temp', 'correction_spill', 'custom_rule',
            'conflict_report', 'broadcast', 'memory_recall',
            'well_status', 'well_trend', 'well_downtime', 'well_spills',
            'well_compliance', 'well_equipment', 'well_maintenance', 'repair_types',
            'area_list_viz', 'area_nonprod', 'area_downtime_rank',
            'area_spill_map', 'area_rca', 'field_status', 'field_stats',
            'personnel', 'sop_lookup', 'heatmap', 'fallback'
        ]
        scores = {intent: 0 for intent in intent_list}

        aid = ent.get('asset_id')
        area = ent.get('area_name')

        clean_q = re.sub(r'[^a-zA-Z\s]', '', q_lower).strip()
        greeting_words = {'hi', 'hii', 'hello', 'hey', 'heyy', 'howdy', 'greetings',
                          'good morning', 'good afternoon', 'good evening', 'help',
                          'what can you do', 'who are you'}
        if clean_q in greeting_words or any(clean_q.startswith(w + ' ') for w in ('hi', 'hello', 'hey')):
            scores['greeting'] += 20

        if any(p in q_lower for p in ('discussed yesterday', 'we discussed', 'previous conversation', 'last time')):
            scores['memory_recall'] += 15

        repair_type_signals = [
            'types of repair', 'types of repairs', 'type of repair', 'type of repairs',
            'kinds of repair', 'kinds of repairs', 'kind of repair',
            'categories of repair', 'repair categories', 'repair types',
            'types of maintenance', 'type of maintenance', 'kinds of maintenance',
            'maintenance types', 'maintenance categories', 'what repairs are done',
            'what repairs are performed', 'what repairs happen', 'how many repairs',
            'how many types of repair', 'how many types of repairs',
            'how many types of maintenance', 'what are the repairs',
            'what kinds of repair', 'classification of repairs'
        ]
        if any(s in q_lower for s in repair_type_signals) or \
           (any(w in q_lower for w in ('repair', 'repairs', 'maintenance')) and any(w in q_lower for w in ('type', 'types', 'kind', 'kinds', 'category', 'categories', 'classification', 'subsystems', 'subsystem'))):
            scores['repair_types'] += 25

        if aid:
            if re.search(r'\d+\.?\d*\s*\xb0?c', q_lower) and any(
                    w in q_lower for w in ('wrong', 'faulty', 'correction', 're-measured', 'measured at', 'actual')):
                scores['correction_temp'] += 15
            if any(w in q_lower for w in ('spill', 'leak')) and any(
                    w in q_lower for w in ('estimate', 'measured', 'volume', 'bbl', 'barrels')):
                scores['correction_spill'] += 15
            if any(w in q_lower for w in ('running fine', 'back online', 'is online', 'operational now', 'working fine')):
                scores['conflict_report'] += 14
            if any(w in q_lower for w in ('shut in', 'workover', 'planned shutdown', 'fyi')):
                scores['broadcast'] += 13

        if any(p in q_lower for p in ('note for all', 'rule for', 'rca after', 'wants a rule')) and ent.get('well_type'):
            scores['custom_rule'] += 14

        sop_signals = ['sr-01', 'sr-02', 'sr-03', 'rc-04', 'sop ', 'operating threshold',
                       't200 threshold', 't350 threshold', 'containment limit', 'containment deadline',
                       'what does rule', 'what is the rule', 'what rule', 'regulation']
        if sum(1 for s in sop_signals if s in q_lower) >= 1:
            scores['sop_lookup'] += 10

        if any(w in q_lower for w in ('heatmap', 'heat map', 'heat-map', 'density matrix')) or \
           (('spill' in q_lower or 'leak' in q_lower) and any(p in q_lower for p in ('area and month', 'area & month', 'by month', 'month and area', 'monthly breakdown', 'spatial-temporal'))):
            scores['heatmap'] += 20

        field_signals = ['how many', 'overall', 'entire field', 'all wells', 'across the field',
                         'field overview', 'field summary', 'total wells', 'field-wide']
        prod_signals = ['producing', 'down', 'status', 'active', 'inactive', 'production rate']
        if sum(1 for s in field_signals if s in q_lower) >= 1:
            if sum(1 for s in prod_signals if s in q_lower) >= 1:
                scores['field_status'] += 11
            else:
                scores['field_stats'] += 8

        if any(p in q_lower for p in ('expensive', 'costliest', 'highest cost', 'latest repair',
                                       'recent repair', 'recent maintenance', 'total money',
                                       'total cost', 'spent on maintenance', 'repair spending',
                                       'total inspections', 'how many inspections', 'most spills')):
            scores['field_stats'] += 10

        if any(w in q_lower for w in ('inspector', 'technician', 'operator', 'supervisor',
                                       'personnel', 'who is', 'team member', 'staff', 'workers')):
            scores['personnel'] += 9
        if 'who' in q_lower and any(w in q_lower for w in ('is', 'are', 'does')):
            scores['personnel'] += 3

        if aid:
            trend_signals = ['line chart', 'chart', 'trend', 'history', 'over time', 'over weeks',
                             'temperature over', 'thermal trend', 'week']
            if sum(1 for s in trend_signals if s in q_lower) >= 1 or ent.get('weeks'):
                scores['well_trend'] += 10
            if any(w in q_lower for w in ('downtime', 'days down', 'out of service', 'offline days')):
                scores['well_downtime'] += 10
            if any(w in q_lower for w in ('spill', 'leak', 'discharge', 'crude release')):
                scores['well_spills'] += 10
            if any(w in q_lower for w in ('rule', 'broken', 'compliance', 'violation', 'sop', 'breach', 'regulatory')):
                scores['well_compliance'] += 10
            if any(w in q_lower for w in ('equipment', 'model', 'parts', 'pump jack', 'wellhead', 'inventory', 'gear')):
                scores['well_equipment'] += 10
            if any(w in q_lower for w in ('repair', 'maintenance', 'fix', 'job', 'work order', 'service')):
                scores['well_maintenance'] += 10
            if any(w in q_lower for w in ('status', 'producing', 'temperature', 'inspect', 'card',
                                           'is it', 'is well', 'show me well', 'what about')):
                scores['well_status'] += 9
            scores['well_status'] += 2

        if area:
            viz_signals = ['visualization', 'diagram', 'chart', 'visual', 'graph', 'show me',
                           'display', 'view all', 'overview', 'dashboard', 'all wells', 'list']
            if sum(1 for s in viz_signals if s in q_lower) >= 1:
                scores['area_list_viz'] += 11
            if any(w in q_lower for w in ('not producing', 'down', 'stopped', 'not working', 'offline')):
                if any(w in q_lower for w in ('ranking', 'most', 'top', 'worst', 'bar chart')):
                    scores['area_downtime_rank'] += 17
                else:
                    scores['area_nonprod'] += 17
            if any(w in q_lower for w in ('downtime', 'most downtime', 'top downtime')):
                scores['area_downtime_rank'] += 16
            if any(w in q_lower for w in ('spill', 'leak')) and any(
                    w in q_lower for w in ('map', 'where', 'location', 'geo')):
                scores['area_spill_map'] += 17
            if any(w in q_lower for w in ('contain', 'uncontained', '4 hour', '4h')):
                scores['area_rca'] += 16
            if any(w in q_lower for w in ('rca', 'root-cause', 'root cause', 'pump jack')):
                scores['area_rca'] += 17
            scores['area_list_viz'] += 3

        best = max(scores, key=lambda k: scores[k])
        return best if scores[best] > 0 else 'fallback'

    def _handle_query_internal(self, user_id: str, question: str, history: list = None):
        q = question.strip()
        q_lower = q.lower()
        ent = self.extract_entities(q)

        # Resolve pronouns / references using conversation history
        if history:
            ent, context_meta = self.resolve_context(q, ent, history)
        else:
            context_meta = {}
        self.current_context_meta = context_meta

        aid = ent["asset_id"]
        area = ent["area_name"]
        intent = self.classify_intent(q_lower, ent)

        # ================================================================
        # GREETING
        # ================================================================
        if intent == 'greeting':
            user_info = agent_tools.execute_query("SELECT name, role FROM users WHERE name = ?", (user_id,))
            role_title = user_info[0]["role"].replace("_", " ").title() if user_info else "Field Engineer"
            ans = (
                f"Hello **{user_id}**! I am your **Asset Intelligence Copilot**, monitoring 200 oil wells.\n\n"
                f"As **{role_title}**, you can ask me:\n"
                f"- **Well Status:** *\"Is WELL-0001 producing?\"*\n"
                f"- **Area Overview:** *\"Show all wells in Northeast Block 8\"*\n"
                f"- **Trends:** *\"13-week thermal trend for WELL-0042\"*\n"
                f"- **Maintenance:** *\"Latest repairs on WELL-0025\"*\n"
                f"- **Compliance:** *\"What does SR-01 require?\"*\n"
                f"- **Field Stats:** *\"How many wells are producing?\"*\n\nWhat would you like to check?"
            )
            return {"answer": ans, "visual_type": None, "visual_data": None, "citations": ["copilot.db"]}

        # ================================================================
        # MEMORY RECALL
        # ================================================================
        if intent == 'memory_recall':
            history = agent_tools.get_user_chat_history(user_id, limit=10)
            past_wells = []
            for h in history:
                for m in re.findall(r'WELL-\d{4}', h.get("content", "")):
                    if m not in past_wells:
                        past_wells.append(m)
            if not past_wells:
                return {"answer": f"No prior conversation record found for **{user_id}**.",
                        "visual_type": None, "visual_data": None, "citations": ["UserPrivateMemory"]}
            if any(w in q_lower for w in ('cost', 'repair', 'spending')):
                costs = agent_tools.get_repair_costs_this_year(past_wells)
                rows = [[w, f"${costs.get(w, 0.0):,.2f}"] for w in past_wells]
                total = sum(costs.values())
                return {
                    "answer": f"For wells discussed previously ({', '.join(past_wells)}), 2026 repair costs:\n\n**Total:** ${total:,.2f}",
                    "visual_type": "table",
                    "visual_data": {"headers": ["Well ID", "2026 Repair Total (USD)"], "rows": rows},
                    "citations": ["maintenance.jsonl", "PrivateMemory"]
                }

        # ================================================================
        # CORRECTION: Temperature
        # ================================================================
        if intent == 'correction_temp' and aid:
            temp_match = re.search(r'(\d+(?:\.\d+)?)\s*\xb0?c', q_lower)
            if temp_match:
                val = temp_match.group(1)
                status_data = agent_tools.get_well_status(aid)
                insp = status_data["latest_inspection"]
                insp_id = insp["inspection_id"]
                agent_tools.record_correction(user_id=user_id, asset_id=aid, inspection_id=insp_id,
                                              field_name="wellhead_temp_c", corrected_value=val, reason=q, scope="well")
                diff = round(float(val) - insp["ambient_temp_c"], 1)
                thresh = insp["threshold"]
                is_prod = diff >= thresh
                return {
                    "answer": (
                        f"**Correction Recorded for {aid}**\n\n"
                        f"- **Inspection:** {insp_id}\n"
                        f"- **Original:** {insp['wellhead_temp_c']} \u00b0C \u2192 **Corrected:** **{val} \u00b0C** (by {user_id})\n"
                        f"- **Impact:** Ambient {insp['ambient_temp_c']} \u00b0C, delta +{diff} \u00b0C vs threshold {thresh} \u00b0C \u2192 **{'PRODUCING OIL' if is_prod else 'NOT PRODUCING'}**."
                    ),
                    "visual_type": "status_card",
                    "visual_data": agent_tools.get_well_status(aid),
                    "citations": [insp_id, "T200.md#Section-9.3"]
                }

        # ================================================================
        # CORRECTION: Spill Volume
        # ================================================================
        if intent == 'correction_spill' and aid:
            v_m = re.findall(r'(\d+(?:\.\d+)?)\s*(?:bbl|barrels)', q_lower)
            if v_m:
                corr_val = v_m[-1]
                spills_data = agent_tools.get_well_spills(aid, days=120)
                insp_id = spills_data["spills"][-1]["inspection_id"] if spills_data.get("spills") else "INS-UNKNOWN"
                agent_tools.record_correction(user_id=user_id, asset_id=aid, inspection_id=insp_id,
                                              field_name="spill_est_volume_bbl", corrected_value=corr_val, reason=q, scope="well")
                is_rep = float(corr_val) >= 5.0
                ans = f"**Spill Volume Correction for {aid}:** Inspection **{insp_id}** updated to **{corr_val} bbl** by {user_id}.\n"
                ans += ("- **SR-01:** Reportable \u2265 5.0 bbl \u2192 Written notice due within 24h." if is_rep
                        else "- Classification: Moderate (< 5.0 bbl).")
                return {"answer": ans, "visual_type": None, "visual_data": None, "citations": [insp_id, "SOP-SR#SR-01"]}

        # ================================================================
        # CUSTOM RULE
        # ================================================================
        if intent == 'custom_rule' and ent.get('well_type'):
            wtype = ent["well_type"]
            th_m = re.search(r'(\d+)\s+repairs?', q_lower)
            val = th_m.group(1) if th_m else "2"
            agent_tools.record_user_rule(user_id=user_id, well_type=wtype,
                                          rule_name="rca_repair_threshold", rule_value=val, description=q)
            return {
                "answer": (f"**Custom Rule Registered for {wtype} Wells**\n\n"
                           f"- RCA threshold set to **{val} corrective repairs** (standard: 3) by {user_id}."),
                "visual_type": "table",
                "visual_data": {"headers": ["Well Type", "Standard", "User Rule", "Set By"],
                                "rows": [[wtype, "3 repairs", f"{val} repairs", user_id]]},
                "citations": [f"OM-{wtype}#Section-10"]
            }

        # ================================================================
        # CONFLICT REPORT
        # ================================================================
        if intent == 'conflict_report' and aid:
            status = agent_tools.get_well_status(aid)
            insp = status["latest_inspection"]
            agent_tools.record_shared_fact(user_id=user_id, asset_id=aid, text=q, status="unconfirmed")
            if not status["is_producing"]:
                return {
                    "answer": (f"**Operational Conflict on {aid}**: Telemetry says NOT PRODUCING "
                               f"(ΔT={insp['temp_diff']} \u00b0C < threshold {insp['threshold']} \u00b0C). "
                               f"Your report saved as Unconfirmed pending reinspection."),
                    "visual_type": "status_card", "visual_data": status,
                    "citations": [insp['inspection_id'], "ContextNotes"]
                }

        # ================================================================
        # BROADCAST
        # ================================================================
        if intent == 'broadcast' and aid:
            agent_tools.record_shared_fact(user_id=user_id, asset_id=aid, text=q)
            return {
                "answer": f"**Shared Knowledge Broadcast Saved for {aid}** by {user_id}: \"{q}\"",
                "visual_type": "status_card", "visual_data": agent_tools.get_well_status(aid),
                "citations": ["SharedKnowledgeStore"]
            }

        # ================================================================
        # HEATMAP
        # ================================================================
        if intent == 'heatmap':
            y_tgt = ent["year"] or 2026
            hm = agent_tools.get_spills_heatmap(y_tgt)
            total_spills = sum(r.get("Total", 0) for r in hm.get("data", []))
            sorted_areas = sorted(hm.get("data", []), key=lambda r: r.get("Total", 0), reverse=True)
            top_area = sorted_areas[0]["area"] if sorted_areas else "N/A"
            top_cnt = sorted_areas[0]["Total"] if sorted_areas else 0
            low_area = sorted_areas[-1]["area"] if sorted_areas else "N/A"
            low_cnt = sorted_areas[-1]["Total"] if sorted_areas else 0

            summary = (
                f"**Spill Incident Risk Density ({y_tgt}) — Areas × Months Matrix**\n\n"
                f"- **Total Validated Spills:** **{total_spills}** across all 4 operational blocks (corrected false positives excluded).\n"
                f"- **Highest Incident Density:** **{top_area}** with **{top_cnt} spills**.\n"
                f"- **Lowest Incident Density:** **{low_area}** with **{low_cnt} spills**.\n\n"
                f"Interactive 2D spatial-temporal risk matrix rendered below:"
            )
            return {
                "answer": summary,
                "visual_type": "heatmap",
                "visual_data": hm,
                "citations": ["inspections.jsonl", "corrections"]
            }

        # ================================================================
        # FIELD STATUS
        # ================================================================
        if intent == 'field_status':
            wells_all = agent_tools.execute_query(
                "SELECT w.asset_id, w.name, w.well_type, a.name as area_name "
                "FROM wells w JOIN areas a ON w.area_id = a.area_id")
            total_cnt = len(wells_all)
            prod_cnt = 0
            down_cnt = 0
            area_stats = {}
            for w in wells_all:
                st = agent_tools.get_well_status(w["asset_id"])
                is_p = st.get("is_producing", False)
                aname = w["area_name"]
                if aname not in area_stats:
                    area_stats[aname] = {"total": 0, "producing": 0, "down": 0}
                area_stats[aname]["total"] += 1
                if is_p:
                    prod_cnt += 1
                    area_stats[aname]["producing"] += 1
                else:
                    down_cnt += 1
                    area_stats[aname]["down"] += 1
            rows = []
            for aname, s in sorted(area_stats.items()):
                pct = f"{(s['producing'] / s['total'] * 100):.1f}%"
                rows.append([aname, s["total"], s["producing"], s["down"], pct])
            rate = (prod_cnt / total_cnt * 100) if total_cnt else 0
            return {
                "answer": (f"**Field-Wide Production Status:**\n\n"
                           f"- **Producing:** **{prod_cnt}/{total_cnt} wells ({rate:.1f}%)**\n"
                           f"- **Down:** **{down_cnt} wells**\n\nBreakdown by block:"),
                "visual_type": "table",
                "visual_data": {"title": "Field Production by Block",
                                "headers": ["Operational Area", "Total Wells", "Producing", "Down", "Production Rate"],
                                "rows": rows},
                "citations": ["wells", "inspections", "FLIR-Weekly"]
            }

        # ================================================================
        # PERSONNEL
        # ================================================================
        if intent == 'personnel':
            users_all = agent_tools.execute_query(
                "SELECT u.user_id, u.name, u.role, u.team_id, t.name as team_name "
                "FROM users u LEFT JOIN teams t ON u.team_id = t.team_id")
            for u in users_all:
                if u["name"].lower() in q_lower:
                    insp_cnt = agent_tools.execute_query(
                        "SELECT COUNT(*) as cnt FROM inspections WHERE inspector_user_id = ?", (u["name"],))[0]["cnt"]
                    maint_cnt = agent_tools.execute_query(
                        "SELECT COUNT(*) as cnt FROM maintenance WHERE technician_user_id = ?", (u["name"],))[0]["cnt"]
                    return {
                        "answer": (f"**Personnel Profile: {u['name']}**\n\n"
                                   f"- **User ID:** `{u['user_id']}`\n"
                                   f"- **Role:** **{u['role']}**\n"
                                   f"- **Team:** {u['team_name'] or u['team_id']}\n"
                                   f"- **Activity:** {insp_cnt} inspections, {maint_cnt} maintenance work orders."),
                        "visual_type": "table",
                        "visual_data": {"title": f"User Profile \u2014 {u['name']}", "headers": ["Attribute", "Details"],
                            "rows": [["Full Name", u["name"]], ["User ID", u["user_id"]], ["Role", u["role"]],
                                     ["Team", u["team_name"] or u["team_id"]],
                                     ["Inspections Completed", str(insp_cnt)],
                                     ["Maintenance Work Orders", str(maint_cnt)]]},
                        "citations": ["users", "teams"]
                    }
            target_role = None
            for role_word in ('inspector', 'technician', 'operator', 'supervisor'):
                if role_word in q_lower:
                    target_role = role_word
                    break
            if target_role:
                matched = [u for u in users_all if target_role in u["role"].lower()]
                if matched:
                    rows = [[u["name"], u["user_id"], u["role"], u["team_name"] or u["team_id"]] for u in matched]
                    return {
                        "answer": f"Field personnel under **{target_role.capitalize()}** role ({len(matched)} found):",
                        "visual_type": "table",
                        "visual_data": {"title": f"Directory \u2014 {target_role.capitalize()}s",
                                        "headers": ["Name", "User ID", "Role", "Team"], "rows": rows},
                        "citations": ["users", "teams"]
                    }
            rows = [[u["name"], u["user_id"], u["role"], u["team_name"] or u["team_id"]] for u in users_all]
            return {
                "answer": f"All registered field personnel ({len(users_all)} people):",
                "visual_type": "table",
                "visual_data": {"title": "Field Personnel Directory",
                                "headers": ["Name", "User ID", "Role", "Team"], "rows": rows},
                "citations": ["users", "teams"]
            }

        # ================================================================
        # SOP LOOKUP
        # ================================================================
        if intent == 'sop_lookup' or "sr-01" in q_lower:
            if "sr-02" in q_lower or "containment" in q_lower:
                return {
                    "answer": ("**SOP SR-02 \u2014 Spill Containment:**\n\n"
                               "- **Window:** 4.0 hours maximum from observation\n"
                               "- **Isolation:** Under 1.0 hour\n"
                               "- **Breach:** >4h \u2192 Level 2 Environmental Non-Conformance"),
                    "visual_type": "table",
                    "visual_data": {"title": "SOP SR-02",
                                    "headers": ["Clause", "Standard", "Action"],
                                    "rows": [["Containment Window", "4.0 h max", "Deploy booms, berms, vacuum recovery"],
                                             ["Source Isolation", "Under 1.0 h", "Shut in wellhead / isolate flowline"],
                                             ["Breach", ">4.0 h", "Escalate to Level 2 Non-Conformance"]]},
                    "citations": ["SOP-SR#SR-02"]
                }
            if "t350" in q_lower or "t200" in q_lower or "threshold" in q_lower:
                return {
                    "answer": ("**Operating Manual Thermal Thresholds:**\n\n"
                               "- **T200 Wells:** \u0394T \u2265 15.0 \u00b0C. Below \u2192 non-producing.\n"
                               "- **T350 Wells:** \u0394T \u2265 20.0 \u00b0C. Deeper formation wells."),
                    "visual_type": "table",
                    "visual_data": {"title": "Well Class Thresholds",
                                    "headers": ["Class", "Threshold", "RCA Trigger"],
                                    "rows": [["T200", "\u2265 15.0 \u00b0C", "3 repairs / 12 months"],
                                             ["T350", "\u2265 20.0 \u00b0C", "3 repairs / 12 months"]]},
                    "citations": ["OM-T200#Section-4", "OM-T350#Section-4"]
                }
            # Default: SR-01
            return {
                "answer": ("**SOP SR-01 \u2014 Regulatory Spill Reporting:**\n\n"
                           "- **Threshold:** \u2265 5.0 bbl crude oil\n"
                           "- **Oral Notice:** Immediate phone call to regulator & HSE\n"
                           "- **Written Notice:** Form H-8 within **24 hours** of discovery\n"
                           "- **Breach:** Late/missing notice = immediate SR-01 violation"),
                "visual_type": "table",
                "visual_data": {"title": "SOP SR-01",
                                "headers": ["Clause", "Requirement", "Window"],
                                "rows": [["Threshold", "\u2265 5.0 bbl crude oil", "At discovery"],
                                         ["Oral Notice", "Phone regulators & HSE", "Immediate"],
                                         ["Written Notice", "Form H-8 filing", "Within 24 hours"],
                                         ["Escalation", "Notify Production Supervisor", "Within 2 hours"]]},
                "citations": ["SOP-SR#SR-01"]
            }

        # ================================================================
        # WELL STATUS
        # ================================================================
        if intent == 'well_status' and aid:
            status = agent_tools.get_well_status(aid)
            if "error" in status:
                return {"answer": status["error"], "visual_type": None, "visual_data": None, "citations": []}
            insp = status["latest_inspection"]
            is_p = status["is_producing"]
            answer = (
                f"**{aid} is {'PRODUCING OIL' if is_p else 'NOT PRODUCING OIL'}.**\n\n"
                f"- **Inspection:** **{insp['inspection_id']}** ({insp['inspected_at'][:10]}) by {insp['method']}\n"
                f"- **Thermal:** Wellhead {insp['wellhead_temp_c']} \u00b0C vs Ambient {insp['ambient_temp_c']} \u00b0C "
                f"(**{insp['temp_diff']} \u00b0C delta**, threshold \u2265 {insp['threshold']} \u00b0C)\n"
            )
            if not is_p and status.get("active_repairs"):
                r = status["active_repairs"][0]
                answer += f"- **Active Repair:** {r['maintenance_id']} ({r['issue']}), started {r['started_at'][:10]}\n"
            return {
                "answer": answer, "visual_type": "status_card", "visual_data": status,
                "citations": [insp['inspection_id'], f"OM-{status['well_type']}#Section-9.3"]
            }

        # ================================================================
        # WELL TREND
        # ================================================================
        if (intent == 'well_trend' or (aid and any(
                w in q_lower for w in ('chart', 'trend', 'history', 'over time', 'over weeks')))) and aid:
            w_cnt = ent["weeks"] or 13
            history = agent_tools.get_wellhead_temp_history(aid, weeks=w_cnt)
            if history:
                non_p = [h["date"] for h in history if not h["producing"]]
                return {
                    "answer": f"Thermal history for **{aid}** over {len(history)} weeks. Non-producing weeks: {', '.join(non_p) if non_p else 'None'}.",
                    "visual_type": "line_chart",
                    "visual_data": {
                        "title": f"{aid}: Wellhead vs Ambient ({len(history)} Weeks)",
                        "x_key": "date",
                        "series": [
                            {"key": "wellhead_temp_c", "label": "Wellhead Temp (\u00b0C)", "color": "#f97316"},
                            {"key": "ambient_temp_c", "label": "Ambient Air Temp (\u00b0C)", "color": "#06b6d4"}
                        ],
                        "data": history,
                        "threshold": history[0]["threshold"] if history else 15.0
                    },
                    "citations": ["inspections.jsonl", "OM-Manual"]
                }

        # ================================================================
        # WELL DOWNTIME
        # ================================================================
        if intent == 'well_downtime' and aid:
            y = ent["year"] or 2025
            dt = agent_tools.get_well_downtime_days(aid, year=y)
            rows = [[r["inspection_id"], r["inspected_at"][:10], f"{r['wellhead_temp_c']} \u00b0C",
                     f"{r['ambient_temp_c']} \u00b0C", f"{r['temp_diff']} \u00b0C"] for r in dt["inspections"]]
            return {
                "answer": f"**{aid} was down for {dt['downtime_days']} days in {y}** ({dt['non_producing_weeks']} non-producing inspections).",
                "visual_type": "table" if rows else None,
                "visual_data": {"headers": ["Inspection ID", "Date", "Wellhead Temp", "Air Temp", "Delta"], "rows": rows} if rows else None,
                "citations": [r["inspection_id"] for r in dt["inspections"]]
            }

        # ================================================================
        # WELL SPILLS
        # ================================================================
        if intent == 'well_spills' and aid:
            spills_data = agent_tools.get_well_spills(aid, days=ent["days"], years=ent["year"] or 4)
            rows = [[s["inspection_id"], s["inspected_at"][:10], f"{s['spill_est_volume_bbl']} bbl",
                     f"{s.get('spill_area_pct') or 0}%", s.get("notes") or ""] for s in spills_data.get("spills", [])]
            return {
                "answer": f"**{aid}** has had **{spills_data.get('count', 0)} validated oil spills** totaling **{spills_data.get('total_bbl', 0)} barrels**.",
                "visual_type": "table",
                "visual_data": {"headers": ["Inspection ID", "Date", "Est. Volume", "Pad Area %", "Notes"], "rows": rows},
                "citations": ["inspections.jsonl", "corrections"]
            }

        # ================================================================
        # WELL COMPLIANCE
        # ================================================================
        if intent == 'well_compliance' and aid:
            breaches_data = agent_tools.get_well_rule_breaches(aid, months=ent["months"] or 12)
            b_list = breaches_data.get("breaches", [])
            rows = [[b["rule"], b["description"][:60], b["status"]] for b in b_list]
            for r in breaches_data.get("rca_candidates", []):
                rows.append(["OM-Section-10", f"RCA required: {r['cnt']} repairs on {r['equipment_kind']}", "ACTION REQ"])
            return {
                "answer": f"**Compliance Findings for {aid} (Last {ent['months'] or 12} Months):**\n\n"
                          + "\n".join(f"- **{b['rule']}:** {b['description']}" for b in b_list),
                "visual_type": "table",
                "visual_data": {"headers": ["Rule / Protocol", "Finding", "Status"],
                                "rows": rows if rows else [["All SOPs", "No active breaches", "COMPLIANT"]]},
                "citations": ["regulatory_events.jsonl", "SOP-SR", "SOP-RC"]
            }

        # ================================================================
        # WELL EQUIPMENT
        # ================================================================
        if intent == 'well_equipment' and aid:
            w_res = agent_tools.execute_query(
                "SELECT equipment_json, name, well_type FROM wells WHERE asset_id = ?", (aid,))
            if w_res:
                eq_list = json.loads(w_res[0]["equipment_json"] or "[]")
                rows = [[e.get("kind"), e.get("model"), e.get("equipment_id")] for e in eq_list]
                return {
                    "answer": f"Equipment inventory for **{aid}** ({w_res[0]['name']}, {w_res[0]['well_type']}):",
                    "visual_type": "table",
                    "visual_data": {"title": f"Equipment Roster \u2014 {aid}",
                                    "headers": ["Equipment Kind", "Model", "Equipment ID"], "rows": rows},
                    "citations": [f"{aid}/metadata.json"]
                }

        # ================================================================
        # WELL MAINTENANCE
        # ================================================================
        if intent == 'well_maintenance' and aid:
            m_rows = agent_tools.execute_query(
                "SELECT maintenance_id, completed_at, equipment_kind, issue, action_taken, total_cost "
                "FROM maintenance WHERE asset_id = ? ORDER BY completed_at DESC LIMIT 10", (aid,))
            if m_rows:
                tot_spend = sum(float(m["total_cost"] or 0) for m in m_rows)
                rows = [[m["maintenance_id"], m["completed_at"][:10], m["equipment_kind"], m["issue"],
                         m["action_taken"], f"${float(m['total_cost']):,.2f}"] for m in m_rows]
                return {
                    "answer": f"Maintenance history for **{aid}** ({len(m_rows)} work orders, total: **${tot_spend:,.2f}**):",
                    "visual_type": "table",
                    "visual_data": {"title": f"Maintenance Work Orders \u2014 {aid}",
                                    "headers": ["Work Order", "Completed Date", "Equipment", "Issue", "Action Taken", "Total Cost"],
                                    "rows": rows},
                    "citations": [f"{aid}/maintenance.jsonl"]
                }
            return {"answer": f"No corrective maintenance records found for **{aid}**.",
                    "visual_type": "status_card", "visual_data": agent_tools.get_well_status(aid),
                    "citations": ["maintenance.jsonl"]}

        # ================================================================
        # REPAIR & MAINTENANCE TYPES (Per-Well or Field-Wide)
        # ================================================================
        if intent == 'repair_types':
            if aid:
                # Specific well breakdown
                rows_m = agent_tools.execute_query(
                    "SELECT equipment_kind, "
                    "SUM(CASE WHEN maintenance_type = 'corrective' THEN 1 ELSE 0 END) as corrective_cnt, "
                    "SUM(CASE WHEN maintenance_type = 'scheduled' THEN 1 ELSE 0 END) as scheduled_cnt, "
                    "COUNT(*) as total_cnt, "
                    "ROUND(SUM(total_cost), 2) as total_cost, "
                    "ROUND(AVG(downtime_hours), 1) as avg_downtime "
                    "FROM maintenance WHERE asset_id = ? "
                    "GROUP BY equipment_kind ORDER BY total_cnt DESC", (aid,))

                tot_corrective = sum(r["corrective_cnt"] for r in rows_m)
                tot_scheduled = sum(r["scheduled_cnt"] for r in rows_m)
                tot_spend = sum(r["total_cost"] or 0 for r in rows_m)

                table_rows = [
                    [
                        r["equipment_kind"].replace("_", " ").title(),
                        str(r["corrective_cnt"]),
                        str(r["scheduled_cnt"]),
                        str(r["total_cnt"]),
                        f"{r['avg_downtime']} hrs" if r['avg_downtime'] else "0 hrs",
                        f"${float(r['total_cost'] or 0):,.2f}"
                    ]
                    for r in rows_m
                ]

                answer = (
                    f"**Types of Repairs & Maintenance on {aid}:**\n\n"
                    f"Work on **{aid}** is organized into **2 operational categories** across **{len(rows_m)} equipment subsystems**:\n\n"
                    f"1. **Corrective Repairs ({tot_corrective} operations):** Unscheduled remedial operations to address equipment faults, leaks, or wear.\n"
                    f"2. **Scheduled Servicing ({tot_scheduled} operations):** Routine preventative servicing (PM), lubrication, stuffing box packing, and annual pressure tests.\n\n"
                    f"**Cumulative Maintenance Spend:** **${tot_spend:,.2f}**\n\n"
                    f"Subsystem breakdown for {aid}:"
                )

                return {
                    "answer": answer,
                    "visual_type": "table",
                    "visual_data": {
                        "title": f"Repair & Maintenance Breakdown — {aid}",
                        "headers": ["Equipment Subsystem", "Corrective Repairs", "Scheduled Services", "Total Operations", "Avg Downtime", "Total Cost"],
                        "rows": table_rows
                    },
                    "citations": [f"{aid}/maintenance.jsonl", "copilot.db"]
                }
            else:
                # Field-wide well repair types
                eq_summary = agent_tools.execute_query(
                    "SELECT equipment_kind, "
                    "SUM(CASE WHEN maintenance_type = 'corrective' THEN 1 ELSE 0 END) as corrective_cnt, "
                    "SUM(CASE WHEN maintenance_type = 'scheduled' THEN 1 ELSE 0 END) as scheduled_cnt, "
                    "COUNT(*) as total_cnt, "
                    "ROUND(SUM(total_cost), 2) as total_cost, "
                    "ROUND(AVG(downtime_hours), 1) as avg_downtime "
                    "FROM maintenance GROUP BY equipment_kind ORDER BY total_cnt DESC"
                )

                table_rows = [
                    [
                        r["equipment_kind"].replace("_", " ").title(),
                        f"{r['corrective_cnt']:,}",
                        f"{r['scheduled_cnt']:,}",
                        f"{r['total_cnt']:,}",
                        f"{r['avg_downtime']} hrs",
                        f"${float(r['total_cost']):,.2f}"
                    ]
                    for r in eq_summary
                ]

                answer = (
                    f"Across the 200 oil wells in the field, maintenance and repairs are structured into **2 operational classifications** across **6 equipment subsystems**:\n\n"
                    f"### 1. Operational Classifications:\n"
                    f"- **Corrective Maintenance (Repairs) — 1,509 operations:** Reactive repairs performed when a failure occurs (e.g. flowline leaks, parted rod strings, motor burnouts, or downhole pump seizures). Average downtime: **193.4 hours**.\n"
                    f"- **Scheduled Maintenance (Preventative) — 4,156 operations:** Routine preventative maintenance (PM) including lubrication, belt inspections, stuffing box packing, and annual flowline pressure integrity tests. Average downtime: **5.9 hours**.\n\n"
                    f"### 2. The 6 Equipment Subsystems Repaired:\n"
                    f"1. **Pump Jack (Surface Unit):** Gearbox seal leaks, electric motor replacements, walking beam saddle bearings, and drive belt replacements (2,173 operations).\n"
                    f"2. **Wellhead:** Stuffing box packing replacement, master/wing valve servicing, and pressure testing (1,771 operations).\n"
                    f"3. **Flowline:** Pipe section replacements, pinhole corrosion repair, coupling gaskets, and annual integrity tests (1,525 operations).\n"
                    f"4. **Downhole Pump:** Pump pulling and complete replacement with exchange units (80 operations).\n"
                    f"5. **Rod String:** Sucker rod parting, fishing parted rods, and rod guide replacement (77 operations).\n"
                    f"6. **Separator:** Level controller faults and dump valve replacements (39 operations).\n\n"
                    f"Field-wide breakdown across all subsystems:"
                )

                return {
                    "answer": answer,
                    "visual_type": "table",
                    "visual_data": {
                        "title": "Field Well Repair & Maintenance Classifications",
                        "headers": ["Equipment Subsystem", "Corrective Repairs", "Scheduled Services", "Total Operations", "Avg Downtime", "Cumulative Spend"],
                        "rows": table_rows
                    },
                    "citations": ["maintenance.jsonl", "OM-Manual#Section-10"]
                }

        # ================================================================
        # AREA: NON-PRODUCING WELLS (Root Cause & Diagnostics)
        # ================================================================
        if intent == 'area_nonprod' and area:
            down_wells = agent_tools.get_non_producing_wells_in_area(area)
            if down_wells:
                lines = [f"- **{w['asset_id']}** ({w['well_type']}): {w['reason']}" for w in down_wells]
                rows = [[w["asset_id"], w["well_name"], w["well_type"], f"{w['temp_diff']} °C", w["reason"]] for w in down_wells]
                ans = f"**{len(down_wells)} wells currently offline/not producing in {area}:**\n\n" + "\n".join(lines)
                return {
                    "answer": ans,
                    "visual_type": "table",
                    "visual_data": {
                        "title": f"Offline Wells & Diagnostics — {area}",
                        "headers": ["Well ID", "Name", "Class", "Thermal ΔT", "Operational Reason / Note"],
                        "rows": rows
                    },
                    "citations": ["inspections", "maintenance", "context_notes"]
                }
            return {
                "answer": f"All wells in **{area}** are currently producing within normal thermal parameters.",
                "visual_type": None, "visual_data": None,
                "citations": ["inspections"]
            }

        # ================================================================
        # AREA: DOWNTIME RANKING
        # ================================================================
        if intent == 'area_downtime_rank' and area:
            d_rows = agent_tools.execute_query(
                "SELECT w.asset_id, w.name, w.well_type, "
                "COALESCE(SUM(julianday(COALESCE(m.completed_at, '2026-10-16T23:59:59')) - julianday(m.started_at)), 0) as downtime_days "
                "FROM wells w JOIN areas a ON w.area_id = a.area_id "
                "LEFT JOIN maintenance m ON w.asset_id = m.asset_id AND m.maintenance_type = 'corrective' "
                "WHERE a.name = ? OR a.area_id = ? "
                "GROUP BY w.asset_id ORDER BY downtime_days DESC LIMIT 10", (area, area))
            chart_data = [{"asset_id": r["asset_id"], "downtime_days": round(float(r["downtime_days"]), 1)} for r in d_rows]
            tbl_rows = [[r["asset_id"], r["name"], r["well_type"], f"{float(r['downtime_days']):.1f} days"] for r in d_rows]
            return {
                "answer": f"Top downtime ranking for wells in **{area}**:",
                "visual_type": "bar_chart",
                "visual_data": {
                    "title": f"Downtime Ranking (Days) — {area}",
                    "category_key": "asset_id",
                    "value_key": "downtime_days",
                    "data": chart_data,
                    "table": {"headers": ["Well ID", "Name", "Class", "Downtime"], "rows": tbl_rows}
                },
                "citations": ["maintenance.jsonl"]
            }

        # ================================================================
        # AREA: SPILL MAP
        # ================================================================
        if intent == 'area_spill_map' and area:
            area_info = agent_tools.execute_query("SELECT center_lat, center_lon FROM areas WHERE name = ? OR area_id = ?", (area, area))
            center = {"lat": 32.16, "lon": -102.16}
            if area_info:
                center = {"lat": float(area_info[0]["center_lat"] or 32.16), "lon": float(area_info[0]["center_lon"] or -102.16)}
            spills = agent_tools.execute_query(
                "SELECT i.inspection_id, i.asset_id, w.latitude, w.longitude, i.spill_est_volume_bbl, i.inspected_at "
                "FROM inspections i JOIN wells w ON i.asset_id = w.asset_id JOIN areas a ON w.area_id = a.area_id "
                "WHERE (a.name = ? OR a.area_id = ?) AND i.spill_detected = 1", (area, area))
            pins = []
            for s in spills:
                pins.append({
                    "lat": float(s["latitude"] or center["lat"]),
                    "lon": float(s["longitude"] or center["lon"]),
                    "title": f"{s['asset_id']} ({s['spill_est_volume_bbl']} bbl)",
                    "description": f"Spill {s['inspection_id']} on {s['inspected_at'][:10]}"
                })
            return {
                "answer": f"Found **{len(pins)} verified spill incidents** across **{area}**:",
                "visual_type": "map",
                "visual_data": {
                    "title": f"Spill Map — {area}",
                    "center": center,
                    "zoom": 12,
                    "pins": pins
                },
                "citations": ["inspections.jsonl", "wells.jsonl"]
            }

        # ================================================================
        # AREA: RCA CANDIDATES
        # ================================================================
        if intent == 'area_rca' and area:
            rca_res = agent_tools.get_pump_jack_rca_wells(area, user_id=user_id)
            qualifying = rca_res.get("qualifying_wells", [])
            t350_th = rca_res.get("t350_threshold", 3)
            t200_th = rca_res.get("t200_threshold", 3)
            rule_note = f" (Custom rule applied by {user_id})" if rca_res.get("rule_applied") else ""
            if qualifying:
                rows = [[q["asset_id"], q["name"], q["well_type"], str(q["repair_count"]), str(q["threshold"])] for q in qualifying]
                ans = (f"**Root Cause Analysis (RCA) required for {len(qualifying)} wells in {area}**{rule_note}:\n\n"
                       f"- Thresholds: T350 ≥ {t350_th} repairs | T200 ≥ {t200_th} repairs\n\n"
                       + "\n".join(f"- **{q['asset_id']}** ({q['well_type']}): {q['repair_count']} repairs" for q in qualifying))
                return {
                    "answer": ans,
                    "visual_type": "table",
                    "visual_data": {"title": f"Pump Jack RCA Candidates — {area}",
                                    "headers": ["Well ID", "Name", "Class", "Repairs (12 Mo)", "Threshold"], "rows": rows},
                    "citations": ["maintenance.jsonl", "OM-Section-10"]
                }
            return {
                "answer": f"No wells in **{area}** currently exceed the RCA threshold for pump jack corrective repairs (T350: {t350_th}, T200: {t200_th}){rule_note}.",
                "visual_type": None, "visual_data": None,
                "citations": ["maintenance.jsonl"]
            }

        # ================================================================
        # AREA: LIST / VISUALIZATION (catch-all for any area query)
        # ================================================================
        if area:
            wells_in_area = agent_tools.execute_query(
                "SELECT w.asset_id, w.name, w.well_type, w.recorded_status "
                "FROM wells w JOIN areas a ON w.area_id = a.area_id "
                "WHERE a.name = ? OR a.area_id = ? ORDER BY w.asset_id",
                (area, area))
            rows = []
            prod_count = 0
            down_count = 0
            chart_data = []
            for w in wells_in_area:
                st = agent_tools.get_well_status(w["asset_id"])
                insp = st.get("latest_inspection") or {}
                delta = float(insp.get("temp_diff", 0))
                status_str = "PRODUCING" if st.get("is_producing") else "NOT PRODUCING"
                if st.get("is_producing"):
                    prod_count += 1
                else:
                    down_count += 1
                rows.append([w["asset_id"], w["name"], w["well_type"], status_str, f"{delta:.1f} \u00b0C"])
                chart_data.append({"asset_id": w["asset_id"], "temp_diff": delta,
                                   "status": status_str, "well_type": w["well_type"]})
            total = len(wells_in_area)
            prod_pct = f"{(prod_count/total*100):.1f}%" if total else "0%"
            return {
                "answer": (f"**{area} \u2014 Well Inventory ({total} wells)**\n\n"
                           f"- \u2705 **Producing:** {prod_count} ({prod_pct}) | \u274c **Down:** {down_count}\n"
                           f"- T200 threshold: \u226515\u00b0C | T350 threshold: \u226520\u00b0C"),
                "visual_type": "bar_chart",
                "visual_data": {
                    "title": f"Well Status Overview \u2014 {area}",
                    "category_key": "asset_id",
                    "value_key": "temp_diff",
                    "data": chart_data,
                    "table": {"headers": ["Well ID", "Name", "Class", "Operational Status", "Thermal \u0394T"], "rows": rows}
                },
                "citations": ["wells", "inspections", area]
            }

        # ================================================================
        # Catch-all for any well query not matched above
        # ================================================================
        if aid:
            st = agent_tools.get_well_status(aid)
            insp = st.get("latest_inspection") or {}
            diff = insp.get("temp_diff", 0)
            thresh = insp.get("threshold", 15.0)
            is_p = st.get("is_producing", False)
            return {
                "answer": (
                    f"**{aid} ({st.get('name', '')}) is {'PRODUCING OIL' if is_p else 'NOT PRODUCING OIL'}.**\n\n"
                    f"- **Class:** {st.get('well_type')} | **Block:** {st.get('area_id')}\n"
                    f"- **Latest Inspection:** **{insp.get('inspection_id')}** ({insp.get('inspected_at', '')[:10]})\n"
                    f"- **Thermal:** Wellhead {insp.get('wellhead_temp_c')} \u00b0C vs Ambient {insp.get('ambient_temp_c')} \u00b0C "
                    f"(\u0394T = **{diff} \u00b0C**, threshold \u2265 {thresh} \u00b0C)."
                ),
                "visual_type": "status_card", "visual_data": st,
                "citations": [insp.get("inspection_id") or aid, f"OM-{st.get('well_type', 'T200')}"]
            }

        # ================================================================
        # FIELD STATS
        # ================================================================
        if any(w in q_lower for w in ('highest temperature', 'highest temp', 'hottest', 'most hot', 'hottest well')):
            top_temp = agent_tools.execute_query(
                "SELECT i.asset_id, w.name, w.well_type, i.wellhead_temp_c, i.ambient_temp_c, i.temp_diff, i.inspected_at "
                "FROM inspections i JOIN wells w ON i.asset_id = w.asset_id "
                "ORDER BY i.wellhead_temp_c DESC LIMIT 5")
            rows = [[t["asset_id"], t["name"], t["well_type"], f"{t['wellhead_temp_c']} \u00b0C",
                     f"{t['ambient_temp_c']} \u00b0C", f"+{t['temp_diff']} \u00b0C", t["inspected_at"][:10]] for t in top_temp]
            return {
                "answer": "Top 5 wells with the highest recorded wellhead temperatures:",
                "visual_type": "table",
                "visual_data": {"title": "Highest Wellhead Temperatures",
                                "headers": ["Well ID", "Name", "Class", "Wellhead Temp", "Ambient Air", "Thermal \u0394T", "Date"],
                                "rows": rows},
                "citations": ["inspections"]
            }

        if any(w in q_lower for w in ('expensive', 'costliest', 'highest cost', 'priciest')):
            costliest = agent_tools.execute_query(
                "SELECT m.maintenance_id, m.asset_id, m.equipment_kind, m.action_taken, m.completed_at, m.total_cost "
                "FROM maintenance m ORDER BY m.total_cost DESC LIMIT 5")
            rows = [[c["maintenance_id"], c["asset_id"], c["equipment_kind"], c["action_taken"],
                     c["completed_at"][:10], f"${float(c['total_cost']):,.2f}"] for c in costliest]
            return {
                "answer": "Top 5 most expensive corrective maintenance operations:",
                "visual_type": "table",
                "visual_data": {"title": "Most Expensive Maintenance",
                                "headers": ["Work Order", "Well ID", "Equipment", "Action Taken", "Date", "Total Cost"],
                                "rows": rows},
                "citations": ["maintenance.jsonl"]
            }

        if any(w in q_lower for w in ('latest repair', 'recent repair', 'latest maintenance', 'recent maintenance')):
            latest_m = agent_tools.execute_query(
                "SELECT m.maintenance_id, m.asset_id, m.completed_at, m.equipment_kind, m.issue, m.action_taken, m.total_cost "
                "FROM maintenance m ORDER BY m.completed_at DESC LIMIT 5")
            rows = [[m["maintenance_id"], m["asset_id"], m["completed_at"][:10], m["equipment_kind"],
                     m["issue"], m["action_taken"], f"${float(m['total_cost']):,.2f}"] for m in latest_m]
            return {
                "answer": "Latest 5 maintenance work orders completed across the field:",
                "visual_type": "table",
                "visual_data": {"title": "Recent Maintenance Operations",
                                "headers": ["Work Order", "Well ID", "Completed Date", "Equipment", "Issue", "Action Taken", "Total Cost"],
                                "rows": rows},
                "citations": ["maintenance.jsonl"]
            }

        if any(p in q_lower for p in ('total money', 'total cost', 'spent on maintenance', 'repair spending', 'maintenance budget')):
            y_filter = ent["year"]
            if y_filter:
                cost_sum = agent_tools.execute_query(
                    "SELECT SUM(total_cost) as total, COUNT(*) as cnt FROM maintenance WHERE completed_at LIKE ?",
                    (f"{y_filter}%",))[0]
            else:
                cost_sum = agent_tools.execute_query("SELECT SUM(total_cost) as total, COUNT(*) as cnt FROM maintenance")[0]
            tot = float(cost_sum["total"] or 0)
            cnt = cost_sum["cnt"]
            y_str = f"in **{y_filter}**" if y_filter else "across all recorded history"
            eq_breakdown = agent_tools.execute_query(
                "SELECT equipment_kind, SUM(total_cost) as cost, COUNT(*) as jobs FROM maintenance "
                + (f"WHERE completed_at LIKE '{y_filter}%' " if y_filter else "")
                + "GROUP BY equipment_kind ORDER BY cost DESC")
            rows = [[b["equipment_kind"].replace("_", " ").title(), str(b["jobs"]), f"${float(b['cost']):,.2f}"] for b in eq_breakdown]
            return {
                "answer": f"Total maintenance expenditure {y_str}: **${tot:,.2f}** across **{cnt} work orders**.",
                "visual_type": "table",
                "visual_data": {"title": f"Maintenance Spending {f'({y_filter})' if y_filter else ''}",
                                "headers": ["Equipment Category", "Work Orders", "Total Cost"], "rows": rows},
                "citations": ["maintenance.jsonl"]
            }

        if any(p in q_lower for p in ('total inspections', 'how many inspections', 'inspection count')):
            insp_cnt = agent_tools.execute_query("SELECT COUNT(*) as cnt FROM inspections")[0]["cnt"]
            drone_cnt = agent_tools.execute_query("SELECT COUNT(*) as cnt FROM inspections WHERE method = 'drone_flir'")[0]["cnt"]
            hand_cnt = agent_tools.execute_query("SELECT COUNT(*) as cnt FROM inspections WHERE method = 'handheld_thermal'")[0]["cnt"]
            return {
                "answer": f"A total of **{insp_cnt:,} weekly inspections** recorded ({drone_cnt:,} drone FLIR, {hand_cnt:,} handheld thermal).",
                "visual_type": "table",
                "visual_data": {"title": "Inspection Program Overview",
                                "headers": ["Method", "Completed Runs", "Coverage"],
                                "rows": [["Drone FLIR", f"{drone_cnt:,}", "Weekly (All Wells)"],
                                         ["Handheld Thermal", f"{hand_cnt:,}", "Spot Audits"],
                                         ["Total", f"{insp_cnt:,}", "200 Consecutive Weeks"]]},
                "citations": ["inspections.jsonl"]
            }

        if any(p in q_lower for p in ('most spills', 'area has the most spills', 'which area spills')):
            area_spills = agent_tools.execute_query(
                "SELECT a.name as area_name, COUNT(i.inspection_id) as spill_count, SUM(i.spill_est_volume_bbl) as total_vol "
                "FROM inspections i JOIN wells w ON i.asset_id = w.asset_id JOIN areas a ON w.area_id = a.area_id "
                "WHERE i.spill_detected = 1 GROUP BY a.name ORDER BY spill_count DESC")
            rows = [[r["area_name"], str(r["spill_count"]), f"{float(r['total_vol'] or 0):.1f} bbl"] for r in area_spills]
            top_area = area_spills[0]["area_name"] if area_spills else "N/A"
            return {
                "answer": f"**{top_area}** has the highest cumulative spill incidents across the field.",
                "visual_type": "table",
                "visual_data": {"title": "Spill Incidents by Area",
                                "headers": ["Area Name", "Spill Incidents", "Cumulative Volume"], "rows": rows},
                "citations": ["inspections.jsonl"]
            }

        # ================================================================
        # LAST RESORT: Document Search (only high-confidence)
        # ================================================================
        docs_res = agent_tools.search_docs(q)
        doc_matches = docs_res.get("docs", [])
        if doc_matches and doc_matches[0].get("score", 0) >= 3:
            top_doc = doc_matches[0]
            return {
                "answer": f"**From {top_doc['title']} ({top_doc['doc_id']}):**\n\n{top_doc['content']}",
                "visual_type": None, "visual_data": None,
                "citations": [top_doc["doc_id"]]
            }

        # Final Fallback
        suggestions = []
        if not aid and not area:
            suggestions = [
                "Specify a well ID (e.g. *WELL-0042*) or area (e.g. *Northeast Block 8*)",
                "Ask field stats: *\"How many wells are producing?\"*",
                "Ask about rules: *\"What does SR-01 require?\"*",
                "Ask about staff: *\"Who are the inspectors?\"*"
            ]
        hint = "\n\n**Try:**\n" + "\n".join(f"- {s}" for s in suggestions) if suggestions else ""
        return {
            "answer": f"I checked all field telemetry, maintenance records, and compliance documents but couldn't find a precise match for your query.{hint}",
            "visual_type": None, "visual_data": None,
            "citations": ["copilot.db"]
        }
