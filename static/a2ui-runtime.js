/**
 * Google A2UI (Agent-to-User Interface) & OpenUI Client-Side Runtime v0.9.1
 * Specification: https://a2ui.org / github.com/a2ui-project/a2ui
 * 
 * Features:
 *  - Flat Adjacency Tree Resolution (createSurface, updateComponents, updateDataModel)
 *  - Reactive Data-Binding via JSON Pointers
 *  - Native High-Fidelity Domain Renderers (TelemetryHero, DataGrid, Charts, Maps)
 *  - Action Dispatcher (Two-Way Agent Interaction)
 *  - Live Protocol Stream Inspector & Interactive GenUI Playground
 */

class A2UIRuntime {
    constructor(options = {}) {
        this.surfaces = new Map();
        this.catalogSchema = null;
        this.onActionCallback = options.onAction || null;
        this.charts = new Map();
        this.maps = new Map();

        this.initCatalog();
    }

    async initCatalog() {
        try {
            const res = await fetch("/static/a2ui-catalog.json");
            if (res.ok) {
                this.catalogSchema = await res.json();
                console.log("[A2UI Runtime] Initialized with catalog:", this.catalogSchema.catalogId);
            }
        } catch (e) {
            console.warn("[A2UI Runtime] Catalog schema fetch failed, using built-in defaults.", e);
        }
    }

    /**
     * Process an A2UI payload containing v0.9.1 messages:
     *   - createSurface
     *   - updateComponents
     *   - updateDataModel
     */
    renderPayload(container, a2uiPayload) {
        if (!a2uiPayload) return;

        const surfaceId = a2uiPayload.surfaceId || (a2uiPayload.createSurface && a2uiPayload.createSurface.surfaceId) || `surf_${Date.now()}`;
        
        // 1. Initialize Surface
        const surfaceContainer = document.createElement("div");
        surfaceContainer.className = "a2ui-surface-root";
        surfaceContainer.setAttribute("data-a2ui-surface-id", surfaceId);
        container.appendChild(surfaceContainer);

        const surface = {
            id: surfaceId,
            catalogId: a2uiPayload.catalogId || (a2uiPayload.createSurface && a2uiPayload.createSurface.catalogId),
            components: new Map(),
            dataModel: (a2uiPayload.updateDataModel && a2uiPayload.updateDataModel.data) || {},
            container: surfaceContainer
        };
        this.surfaces.set(surfaceId, surface);

        // 2. Process Components (Support both flatComponents and legacy components)
        const flatList = (a2uiPayload.updateComponents && a2uiPayload.updateComponents.components) || a2uiPayload.flatComponents;

        if (flatList && flatList.length > 0) {
            flatList.forEach(item => {
                surface.components.set(item.id, item.component);
            });

            // Find root component (defaults to id "root")
            const rootNode = surface.components.get("root");
            if (rootNode) {
                const renderedDom = this.resolveComponent(surface, "root", rootNode);
                if (renderedDom) {
                    surfaceContainer.appendChild(renderedDom);
                }
            } else {
                // Render all components sequentially if no explicit root
                surface.components.forEach((comp, id) => {
                    const dom = this.resolveComponent(surface, id, comp);
                    if (dom) surfaceContainer.appendChild(dom);
                });
            }
        } else if (a2uiPayload.components) {
            // Fallback for legacy format
            a2uiPayload.components.forEach(comp => {
                const dom = this.renderLegacyComponent(surface, comp);
                if (dom) surfaceContainer.appendChild(dom);
            });
        }

        return surfaceContainer;
    }

    /**
     * Recursively resolves an A2UI component definition from the flat adjacency list.
     */
    resolveComponent(surface, id, compDef) {
        if (!compDef) return null;
        const compType = Object.keys(compDef)[0];
        const props = compDef[compType];

        switch (compType) {
            case "Column":
                return this.renderColumn(surface, id, props);
            case "Row":
                return this.renderRow(surface, id, props);
            case "Card":
                return this.renderCard(surface, id, props);
            case "Text":
                return this.renderText(surface, id, props);
            case "Button":
                return this.renderButton(surface, id, props);
            case "TelemetryHero":
                return this.renderTelemetryHero(surface, id, props);
            case "DataGrid":
                return this.renderDataGrid(surface, id, props);
            case "TrendLineChart":
                return this.renderTrendLineChart(surface, id, props);
            case "RankingBarChart":
                return this.renderRankingBarChart(surface, id, props);
            case "GeoSpatialMap":
                return this.renderGeoSpatialMap(surface, id, props);
            case "DensityHeatmap":
                return this.renderDensityHeatmap(surface, id, props);
            case "ComplianceCallout":
                return this.renderComplianceCallout(surface, id, props);
            case "ActionResponseGroup":
                return this.renderActionGroup(surface, id, props);
            case "CitationBadges":
                return this.renderCitationBadges(surface, id, props);
            default:
                console.warn(`[A2UI Runtime] Unknown component type: ${compType}`);
                return null;
        }
    }

    renderColumn(surface, id, props) {
        const col = document.createElement("div");
        col.className = `a2ui-column a2ui-gap-${props.gap || 'md'}`;
        const childIds = (props.children && props.children.explicitList) || [];
        childIds.forEach(childId => {
            const childDef = surface.components.get(childId);
            if (childDef) {
                const childDom = this.resolveComponent(surface, childId, childDef);
                if (childDom) col.appendChild(childDom);
            }
        });
        return col;
    }

    renderRow(surface, id, props) {
        const row = document.createElement("div");
        row.className = `a2ui-row a2ui-gap-${props.gap || 'md'}`;
        if (props.wrap) row.style.flexWrap = "wrap";
        const childIds = (props.children && props.children.explicitList) || [];
        childIds.forEach(childId => {
            const childDef = surface.components.get(childId);
            if (childDef) {
                const childDom = this.resolveComponent(surface, childId, childDef);
                if (childDom) row.appendChild(childDom);
            }
        });
        return row;
    }

    renderCard(surface, id, props) {
        const card = document.createElement("div");
        card.className = "a2ui-card card-glass";
        
        let headerHtml = "";
        if (props.title) {
            const badgeHtml = props.badge 
                ? `<span class="a2ui-badge variant-${props.badgeVariant || 'info'}">${props.badge}</span>` 
                : "";
            headerHtml = `
                <div class="a2ui-card-header">
                    <div>
                        <h4 class="a2ui-card-title">${props.title}</h4>
                        ${props.subtitle ? `<div class="a2ui-card-subtitle">${props.subtitle}</div>` : ""}
                    </div>
                    ${badgeHtml}
                </div>
            `;
        }
        card.innerHTML = headerHtml;

        if (props.child) {
            const childDef = surface.components.get(props.child);
            if (childDef) {
                const childDom = this.resolveComponent(surface, props.child, childDef);
                if (childDom) card.appendChild(childDom);
            }
        }
        return card;
    }

    renderText(surface, id, props) {
        const div = document.createElement("div");
        div.className = `a2ui-text usage-${props.usageHint || 'body'}`;
        let content = (props.text && props.text.literalString) || "";
        if (typeof marked !== "undefined") {
            div.innerHTML = marked.parse(content);
        } else {
            div.textContent = content;
        }
        return div;
    }

    renderButton(surface, id, props) {
        const btn = document.createElement("button");
        btn.className = `a2ui-btn variant-${props.variant || 'secondary'}`;
        btn.textContent = props.label || "Action";

        btn.addEventListener("click", () => {
            if (props.action && this.onActionCallback) {
                this.onActionCallback(props.action.name, props.action.context || {});
            }
        });
        return btn;
    }

    // =========================================================================
    // Native Domain Components
    // =========================================================================

    renderTelemetryHero(surface, id, props) {
        const isProd = props.isProducing;
        const delta = props.deltaTemp !== undefined && props.deltaTemp !== null ? props.deltaTemp : 0;
        const thresh = props.threshold || 15.0;
        const pct = Math.min(100, Math.max(0, (delta / thresh) * 100));

        const heroEl = document.createElement("div");
        heroEl.className = "a2ui-hero-card";

        const badgeHtml = isProd
            ? `<div class="sc-badge producing"><span class="pulse-dot"></span> PRODUCING OIL</div>`
            : `<div class="sc-badge down"><span class="pulse-dot"></span> NOT PRODUCING (DOWN)</div>`;

        let alertHtml = "";
        if (props.inspectorNotes) {
            alertHtml = `<div class="a2ui-inspector-note-box">
                <strong>Field Inspector Note:</strong> "${props.inspectorNotes}"
            </div>`;
        }

        let correctedHtml = "";
        if (props.corrected) {
            correctedHtml = `<div class="a2ui-correction-stamp">
                ✓ Corrected in field memory by ${props.correctedBy || 'Field Crew'}
            </div>`;
        }

        heroEl.innerHTML = `
            <div class="a2ui-hero-top">
                <div class="a2ui-hero-title">
                    <h3>${props.assetId} <span class="a2ui-hero-name">(${props.name || ''})</span></h3>
                    <div class="a2ui-hero-sub">Class: <strong>${props.wellType || 'T200'}</strong> | Block: <strong>${props.areaId || ''}</strong> | Record Status: <strong>${props.recordedStatus || 'unknown'}</strong></div>
                </div>
                ${badgeHtml}
            </div>
            
            <div class="a2ui-hero-grid">
                <div class="a2ui-gauge-box">
                    <div class="a2ui-gauge-header">
                        <span>Thermal Delta (ΔT)</span>
                        <span class="a2ui-threshold-label">Threshold: ≥ ${thresh} °C</span>
                    </div>
                    <div class="a2ui-gauge-val ${delta >= thresh ? 'text-emerald' : 'text-rose'}">
                        ${delta.toFixed(1)} °C
                    </div>
                    <div class="a2ui-gauge-bar">
                        <div class="a2ui-gauge-fill" style="width: ${pct}%; background: ${delta >= thresh ? 'var(--accent-emerald)' : 'var(--accent-rose)'};"></div>
                    </div>
                    <div class="a2ui-gauge-labels">
                        <span>Ambient: ${props.ambientTemp !== undefined ? props.ambientTemp + ' °C' : 'N/A'}</span>
                        <span>Wellhead: ${props.wellheadTemp !== undefined ? props.wellheadTemp + ' °C' : 'N/A'}</span>
                    </div>
                </div>

                <div class="a2ui-meta-box">
                    <div class="a2ui-meta-item">
                        <span class="lbl">Last Inspected:</span>
                        <span class="val">${props.inspectedAt || 'Unknown'}</span>
                    </div>
                    <div class="a2ui-meta-item">
                        <span class="lbl">Inspector:</span>
                        <span class="val">${props.inspector || 'System'}</span>
                    </div>
                    <div class="a2ui-meta-item">
                        <span class="lbl">Inspection ID:</span>
                        <span class="val mono">${props.inspectionId || 'N/A'}</span>
                    </div>
                    <div class="a2ui-meta-item">
                        <span class="lbl">Method:</span>
                        <span class="val">${props.method || 'Drone FLIR'}</span>
                    </div>
                </div>
            </div>
            ${alertHtml}
            ${correctedHtml}
        `;
        return heroEl;
    }

    renderDataGrid(surface, id, props) {
        const wrap = document.createElement("div");
        wrap.className = "a2ui-table-wrapper";

        if (props.title) {
            const heading = document.createElement("div");
            heading.className = "a2ui-table-header-title";
            heading.innerHTML = `<span>📋</span> ${props.title}`;
            wrap.appendChild(heading);
        }

        const table = document.createElement("table");
        table.className = "a2ui-datatable";

        const thead = document.createElement("thead");
        const hRow = document.createElement("tr");
        (props.headers || []).forEach(h => {
            const th = document.createElement("th");
            th.textContent = h;
            hRow.appendChild(th);
        });
        thead.appendChild(hRow);
        table.appendChild(thead);

        const tbody = document.createElement("tbody");
        (props.rows || []).forEach(r => {
            const tr = document.createElement("tr");
            r.forEach((cell, idx) => {
                const td = document.createElement("td");
                const str = String(cell);
                
                // Intelligent status badge highlighting
                if (str.toLowerCase().includes("down") || str.toLowerCase().includes("not producing") || str.toLowerCase().includes("exceeded")) {
                    td.innerHTML = `<span class="badge-status-danger">${cell}</span>`;
                } else if (str.toLowerCase().includes("producing") || str.toLowerCase().includes("contained") || str.toLowerCase().includes("verified")) {
                    td.innerHTML = `<span class="badge-status-success">${cell}</span>`;
                } else if (str.startsWith("WELL-") || str.startsWith("INS-") || str.startsWith("MNT-")) {
                    td.className = "mono-cell";
                    td.textContent = cell;
                } else {
                    td.textContent = cell;
                }
                tr.appendChild(td);
            });
            tbody.appendChild(tr);
        });
        table.appendChild(tbody);
        wrap.appendChild(table);
        return wrap;
    }

    renderTrendLineChart(surface, id, props) {
        const wrap = document.createElement("div");
        wrap.className = "a2ui-chart-box";
        wrap.innerHTML = `<div class="chart-header">
            <h4>📈 ${props.title || 'Trend Line Chart'}</h4>
            <span class="chart-badge">Time Series (13 Weeks)</span>
        </div>`;

        const canvas = document.createElement("canvas");
        canvas.style.maxHeight = "280px";
        wrap.appendChild(canvas);

        setTimeout(() => {
            if (typeof Chart === "undefined") return;
            const labels = (props.data || []).map(d => d[props.xKey || "date"]);
            const seriesDefs = props.series || ["wellhead_temp_c", "ambient_temp_c"];

            const datasets = [];
            const colors = ["#8b5cf6", "#38bdf8", "#10b981", "#f59e0b"];

            seriesDefs.forEach((sName, sIdx) => {
                const labelMap = {
                    "wellhead_temp_c": "Wellhead Temp (°C)",
                    "ambient_temp_c": "Ambient Air (°C)",
                    "temp_diff": "Delta T (°C)"
                };
                datasets.push({
                    label: labelMap[sName] || sName,
                    data: (props.data || []).map(d => d[sName]),
                    borderColor: colors[sIdx % colors.length],
                    backgroundColor: colors[sIdx % colors.length] + "22",
                    borderWidth: 2.5,
                    tension: 0.35,
                    fill: false,
                    pointRadius: 4,
                    pointHoverRadius: 6
                });
            });

            // Operating manual threshold line
            if (props.threshold) {
                datasets.push({
                    label: `OM Limit (${props.threshold} °C)`,
                    data: (props.data || []).map(() => props.threshold),
                    borderColor: "rgba(244, 63, 94, 0.75)",
                    borderWidth: 1.5,
                    borderDash: [6, 4],
                    pointRadius: 0,
                    fill: false
                });
            }

            new Chart(canvas, {
                type: "line",
                data: { labels, datasets },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: { labels: { color: "#94a3b8", font: { family: "Outfit" } } },
                        tooltip: { backgroundColor: "#1e293b", titleColor: "#f8fafc", bodyColor: "#cbd5e1" }
                    },
                    scales: {
                        x: { grid: { color: "rgba(255,255,255,0.05)" }, ticks: { color: "#64748b" } },
                        y: { grid: { color: "rgba(255,255,255,0.05)" }, ticks: { color: "#64748b" } }
                    }
                }
            });
        }, 50);

        return wrap;
    }

    renderRankingBarChart(surface, id, props) {
        const wrap = document.createElement("div");
        wrap.className = "a2ui-chart-box";
        wrap.innerHTML = `<div class="chart-header">
            <h4>📊 ${props.title || 'Comparative Ranking'}</h4>
            <span class="chart-badge">Top Assets</span>
        </div>`;

        const canvas = document.createElement("canvas");
        canvas.style.maxHeight = "280px";
        wrap.appendChild(canvas);

        setTimeout(() => {
            if (typeof Chart === "undefined") return;
            const labels = (props.data || []).map(d => d[props.categoryKey || "asset_id"]);
            const values = (props.data || []).map(d => d[props.valueKey || "downtime_days"]);

            new Chart(canvas, {
                type: "bar",
                data: {
                    labels,
                    datasets: [{
                        label: props.valueKey ? props.valueKey.replace("_", " ").toUpperCase() : "VALUE",
                        data: values,
                        backgroundColor: "rgba(139, 92, 246, 0.75)",
                        borderColor: "#8b5cf6",
                        borderWidth: 1,
                        borderRadius: 6
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: { labels: { color: "#94a3b8" } }
                    },
                    scales: {
                        x: { grid: { display: false }, ticks: { color: "#cbd5e1", font: { weight: "600" } } },
                        y: { grid: { color: "rgba(255,255,255,0.05)" }, ticks: { color: "#64748b" } }
                    }
                }
            });
        }, 50);

        return wrap;
    }

    renderGeoSpatialMap(surface, id, props) {
        const wrap = document.createElement("div");
        wrap.className = "a2ui-map-wrapper";
        wrap.innerHTML = `<div class="map-header">
            <h4>🗺️ ${props.title || 'Field Map Coordinates'}</h4>
            <span class="map-badge">${(props.pins || []).length} Verified Wells</span>
        </div>`;

        const mapDiv = document.createElement("div");
        mapDiv.style.height = "320px";
        mapDiv.style.borderRadius = "8px";
        wrap.appendChild(mapDiv);

        setTimeout(() => {
            if (typeof L === "undefined") return;
            const center = props.center || { lat: 31.85, lon: -102.5 };
            const map = L.map(mapDiv).setView([center.lat, center.lon], props.zoom || 12);

            // Dark Matter tiles for ultra-modern aesthetic
            L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
                attribution: '&copy; CartoDB',
                maxZoom: 19
            }).addTo(map);

            (props.pins || []).forEach(p => {
                const marker = L.circleMarker([p.lat, p.lon], {
                    radius: 7,
                    fillColor: p.status === "producing" ? "#10b981" : "#f43f5e",
                    color: "#ffffff",
                    weight: 1.5,
                    opacity: 1,
                    fillOpacity: 0.85
                }).addTo(map);

                marker.bindPopup(`
                    <div style="color:#0f172a; font-family:'Outfit', sans-serif;">
                        <h4 style="margin:0 0 4px 0; font-weight:700;">${p.label}</h4>
                        <div style="font-size:12px; margin-bottom:4px;">Status: <strong>${p.status}</strong></div>
                        <div style="font-size:11px; color:#475569;">${p.details || ''}</div>
                    </div>
                `);
            });
        }, 50);

        return wrap;
    }

    renderDensityHeatmap(surface, id, props) {
        const wrap = document.createElement("div");
        wrap.className = "a2ui-heatmap-container";
        wrap.innerHTML = `<div class="chart-header">
            <h4>🔥 ${props.title || 'Spill Density Matrix (Areas × Months)'}</h4>
            <span class="chart-badge">Spatial-Temporal Risk</span>
        </div>`;

        const scrollWrap = document.createElement("div");
        scrollWrap.className = "a2ui-heatmap-scroll";

        const table = document.createElement("table");
        table.className = "a2ui-heatmap-table";

        const thead = document.createElement("thead");
        const hRow = document.createElement("tr");
        hRow.innerHTML = "<th>Geographic Area</th>";
        const months = props.months || ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct"];
        months.forEach(m => {
            const th = document.createElement("th");
            th.textContent = m;
            hRow.appendChild(th);
        });
        const thTot = document.createElement("th");
        thTot.textContent = "Total";
        thTot.className = "th-total";
        hRow.appendChild(thTot);
        thead.appendChild(hRow);
        table.appendChild(thead);

        const tbody = document.createElement("tbody");
        (props.areas || []).forEach((area, aIdx) => {
            const tr = document.createElement("tr");
            const tdArea = document.createElement("td");
            tdArea.className = "area-label-cell";
            tdArea.textContent = area;
            tr.appendChild(tdArea);

            const rowObj = (props.data && props.data[aIdx]) ? props.data[aIdx] : {};
            let calcTotal = 0;

            months.forEach((m, mIdx) => {
                let val = 0;
                if (Array.isArray(rowObj)) {
                    val = rowObj[mIdx] !== undefined ? rowObj[mIdx] : 0;
                } else if (typeof rowObj === "object" && rowObj !== null) {
                    val = rowObj[m] !== undefined ? rowObj[m] : (rowObj[String(mIdx + 1).padStart(2, '0')] || 0);
                } else {
                    val = Number(rowObj) || 0;
                }
                const numVal = Number(val) || 0;
                calcTotal += numVal;

                const td = document.createElement("td");
                td.className = "heatmap-data-cell";
                td.textContent = numVal;

                if (numVal >= 6) {
                    td.style.backgroundColor = "rgba(244, 63, 94, 0.75)";
                    td.style.color = "#ffffff";
                    td.style.fontWeight = "700";
                } else if (numVal >= 4) {
                    td.style.backgroundColor = "rgba(249, 115, 22, 0.55)";
                    td.style.color = "#ffffff";
                    td.style.fontWeight = "600";
                } else if (numVal >= 2) {
                    td.style.backgroundColor = "rgba(245, 158, 11, 0.35)";
                    td.style.color = "#ffffff";
                } else if (numVal > 0) {
                    td.style.backgroundColor = "rgba(6, 182, 212, 0.22)";
                    td.style.color = "#e2e8f0";
                } else {
                    td.style.backgroundColor = "rgba(255, 255, 255, 0.02)";
                    td.style.color = "#64748b";
                }
                tr.appendChild(td);
            });

            const tdTotal = document.createElement("td");
            tdTotal.className = "heatmap-total-cell";
            const displayTotal = (typeof rowObj === "object" && rowObj.Total !== undefined) ? rowObj.Total : calcTotal;
            tdTotal.textContent = displayTotal;
            tr.appendChild(tdTotal);

            tbody.appendChild(tr);
        });

        table.appendChild(tbody);
        scrollWrap.appendChild(table);
        wrap.appendChild(scrollWrap);

        const legend = document.createElement("div");
        legend.className = "heatmap-legend";
        legend.innerHTML = `
            <span class="legend-item"><span class="legend-box" style="background:rgba(255,255,255,0.04); border:1px solid rgba(255,255,255,0.1);"></span> 0 (Zero)</span>
            <span class="legend-item"><span class="legend-box" style="background:rgba(6, 182, 212, 0.4);"></span> 1 (Low)</span>
            <span class="legend-item"><span class="legend-box" style="background:rgba(245, 158, 11, 0.55);"></span> 2–3 (Moderate)</span>
            <span class="legend-item"><span class="legend-box" style="background:rgba(249, 115, 22, 0.7);"></span> 4–5 (Elevated)</span>
            <span class="legend-item"><span class="legend-box" style="background:rgba(244, 63, 94, 0.85);"></span> 6+ (Critical)</span>
        `;
        wrap.appendChild(legend);

        return wrap;
    }

    renderComplianceCallout(surface, id, props) {
        const callout = document.createElement("div");
        callout.className = `a2ui-callout severity-${props.severity || 'warning'}`;
        callout.innerHTML = `
            <div class="a2ui-callout-icon">⚠️</div>
            <div class="a2ui-callout-body">
                <div class="a2ui-callout-title">${props.title} <span class="rule-id-tag">${props.ruleId || ''}</span></div>
                <div class="a2ui-callout-desc">${props.description}</div>
                ${props.actionRequired ? `<div class="a2ui-callout-action"><strong>Required Action:</strong> ${props.actionRequired}</div>` : ''}
            </div>
        `;
        return callout;
    }

    renderActionGroup(surface, id, props) {
        const group = document.createElement("div");
        group.className = "a2ui-action-group";

        (props.actions || []).forEach(act => {
            const btn = document.createElement("button");
            btn.className = "a2ui-action-btn";
            btn.innerHTML = act.label;

            btn.addEventListener("click", () => {
                if (this.onActionCallback) {
                    this.onActionCallback("submit_query", { query: act.query });
                }
            });
            group.appendChild(btn);
        });

        return group;
    }

    renderCitationBadges(surface, id, props) {
        const tray = document.createElement("div");
        tray.className = "citations-tray";
        (props.citations || []).forEach(c => {
            const pill = document.createElement("span");
            pill.className = "citation-pill";
            pill.textContent = "📄 " + c;
            tray.appendChild(pill);
        });
        return tray;
    }

    renderLegacyComponent(surface, comp) {
        if (!comp) return null;
        const fakeDef = {};
        fakeDef[comp.type] = comp.props || {};
        return this.resolveComponent(surface, comp.id || `cmp_${Date.now()}`, fakeDef);
    }
}

window.A2UIRuntime = A2UIRuntime;
