"""
A2UI Declarative Component Builder
Implements Google Agent-to-User Interface (A2UI) v0.9.1+ Prompt-First Specification
and OpenUI Generative UI Standard for Oilfield Asset Intelligence.
"""
import uuid
import json

CATALOG_ID = "https://a2ui.org/specification/v0_9_1/catalogs/oilwell_intelligence/catalog.json"

def build_a2ui(visual_type: str = None, visual_data: dict = None, answer: str = "", citations: list = None, query: str = "", metadata: dict = None):
    """
    Constructs an authentic Google A2UI v0.9.1 declarative UI surface payload.
    Emits the official A2UI message sequence:
      1. createSurface
      2. updateComponents (flat adjacency list with property-based discriminators)
      3. updateDataModel (reactive JSON pointer state bindings)
    """
    surface_id = f"surface_{uuid.uuid4().hex[:8]}"
    flat_components = []
    root_children = []
    data_model = {}

    # Domain visual components
    if visual_type == "status_card" and visual_data:
        insp = visual_data.get("latest_inspection") or {}
        aid = visual_data.get("asset_id", "WELL")
        hero_id = f"hero_{aid}"
        
        flat_components.append({
            "id": hero_id,
            "component": {
                "TelemetryHero": {
                    "assetId": aid,
                    "name": visual_data.get("name"),
                    "wellType": visual_data.get("well_type"),
                    "areaId": visual_data.get("area_id"),
                    "isProducing": visual_data.get("is_producing", False),
                    "recordedStatus": visual_data.get("recorded_status"),
                    "wellheadTemp": insp.get("wellhead_temp_c"),
                    "ambientTemp": insp.get("ambient_temp_c"),
                    "deltaTemp": insp.get("temp_diff"),
                    "threshold": insp.get("threshold", 15.0),
                    "inspectionId": insp.get("inspection_id"),
                    "inspectedAt": insp.get("inspected_at"),
                    "inspector": insp.get("inspector_user_id"),
                    "method": insp.get("method"),
                    "inspectorNotes": insp.get("inspector_notes"),
                    "corrected": insp.get("corrected", False),
                    "correctedBy": insp.get("corrected_by")
                }
            }
        })
        root_children.append(hero_id)

        # Contextual follow-up action buttons
        flat_components.append({
            "id": "actions_well",
            "component": {
                "ActionResponseGroup": {
                    "actions": [
                        {"label": "📈 13-Week Trend", "query": f"Show a line chart of {aid} temperature for the last 13 weeks"},
                        {"label": "🛠️ Check Equipment", "query": f"What equipment is installed on {aid}?"},
                        {"label": "⚠️ Spills & Rules", "query": f"Which rules has {aid} broken?"}
                    ]
                }
            }
        })
        root_children.append("actions_well")

        data_model[f"/wells/{aid}"] = {
            "is_producing": visual_data.get("is_producing", False),
            "delta_t": insp.get("temp_diff"),
            "threshold": insp.get("threshold", 15.0)
        }

    elif visual_type == "table" and visual_data:
        flat_components.append({
            "id": "datatable_grid",
            "component": {
                "DataGrid": {
                    "title": visual_data.get("title", "Operational Records Grid"),
                    "headers": visual_data.get("headers", []),
                    "rows": visual_data.get("rows", []),
                    "highlightColumn": "Status"
                }
            }
        })
        root_children.append("datatable_grid")
        data_model["/table/rowCount"] = len(visual_data.get("rows", []))

    elif visual_type == "line_chart" and visual_data:
        flat_components.append({
            "id": "trend_chart",
            "component": {
                "TrendLineChart": {
                    "title": visual_data.get("title", "Temperature Trend"),
                    "xKey": visual_data.get("x_key", "date"),
                    "series": visual_data.get("series", []),
                    "data": visual_data.get("data", []),
                    "threshold": visual_data.get("threshold", 15.0)
                }
            }
        })
        root_children.append("trend_chart")
        data_model["/chart/dataPoints"] = len(visual_data.get("data", []))

    elif visual_type == "bar_chart" and visual_data:
        flat_components.append({
            "id": "ranking_chart",
            "component": {
                "RankingBarChart": {
                    "title": visual_data.get("title", "Comparative Rankings"),
                    "categoryKey": visual_data.get("category_key", "asset_id"),
                    "valueKey": visual_data.get("value_key", "downtime_days"),
                    "data": visual_data.get("data", [])
                }
            }
        })
        root_children.append("ranking_chart")

    elif visual_type == "map" and visual_data:
        flat_components.append({
            "id": "geospatial_view",
            "component": {
                "GeoSpatialMap": {
                    "title": visual_data.get("title", "Field Coordinates"),
                    "center": visual_data.get("center", {"lat": 31.85, "lon": -102.5}),
                    "zoom": visual_data.get("zoom", 12),
                    "pins": visual_data.get("pins", [])
                }
            }
        })
        root_children.append("geospatial_view")

    elif visual_type == "heatmap" and visual_data:
        flat_components.append({
            "id": "density_heatmap",
            "component": {
                "DensityHeatmap": {
                    "title": visual_data.get("title", "Spill Density Matrix"),
                    "months": visual_data.get("months", []),
                    "areas": visual_data.get("areas", []),
                    "data": visual_data.get("data", [])
                }
            }
        })
        root_children.append("density_heatmap")

    else:
        # Generative UI for general queries / document searches:
        # Add dynamic quick actions and executive card
        flat_components.append({
            "id": "general_actions",
            "component": {
                "ActionResponseGroup": {
                    "actions": [
                        {"label": "🔍 Field Downtime Summary", "query": "Which wells in Northeast Block 8 are not producing oil right now?"},
                        {"label": "🗺️ Spill Map", "query": "Show on a map every well in Northeast Block 8 with a real spill in the last 90 days"},
                        {"label": "📊 2026 Heatmap", "query": "Show a heatmap of 2026 spills by geographic area and month"}
                    ]
                }
            }
        })
        root_children.append("general_actions")



    # 4. Root Column Component linking all child components
    flat_components.insert(0, {
        "id": "root",
        "component": {
            "Column": {
                "children": {
                    "explicitList": root_children
                },
                "gap": "md"
            }
        }
    })

    # Prepare standard legacy components list for backward compatibility
    legacy_components = []
    for fc in flat_components:
        cid = fc["id"]
        if cid == "root":
            continue
        c_dict = fc["component"]
        c_type = list(c_dict.keys())[0]
        c_props = c_dict[c_type]
        legacy_components.append({
            "id": cid,
            "type": c_type,
            "props": c_props
        })

    # Official A2UI v0.9.1 Protocol Messages
    create_surface_msg = {
        "version": "v0.9.1",
        "createSurface": {
            "surfaceId": surface_id,
            "catalogId": CATALOG_ID
        }
    }

    update_components_msg = {
        "version": "v0.9.1",
        "updateComponents": {
            "surfaceId": surface_id,
            "components": flat_components
        }
    }

    update_data_model_msg = {
        "version": "v0.9.1",
        "updateDataModel": {
            "surfaceId": surface_id,
            "data": data_model
        }
    }

    return {
        "version": "v0.9.1",
        "protocol": "A2UI",
        "catalogId": CATALOG_ID,
        "surfaceId": surface_id,
        "createSurface": create_surface_msg["createSurface"],
        "updateComponents": update_components_msg["updateComponents"],
        "updateDataModel": update_data_model_msg["updateDataModel"],
        "components": legacy_components,
        "flatComponents": flat_components,
        "messages": [
            create_surface_msg,
            update_components_msg,
            update_data_model_msg
        ]
    }
