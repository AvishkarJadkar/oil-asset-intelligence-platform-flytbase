document.addEventListener("DOMContentLoaded", () => {
    const chatStream = document.getElementById("chat-stream");
    const chatForm = document.getElementById("chat-form");
    const userInput = document.getElementById("user-input");
    const userSelect = document.getElementById("user-select");
    const userRoleBadge = document.getElementById("user-role-badge");
    const userTeamBadge = document.getElementById("user-team-badge");
    const btnClearChat = document.getElementById("btn-clear-chat");
    const btnToggleA2UI = document.getElementById("btn-toggle-a2ui-inspector");
    const scenarioButtons = document.querySelectorAll(".btn-scenario");

    let currentUserId = userSelect.value;
    let globalShowA2UISchema = false;
    let sessionHistory = [];

    const userRoles = {
        "Michael Turner": { role: "Prod. Supervisor", team: "Northeast Prod" },
        "Jessica Reed": { role: "Field Inspector", team: "Northeast Prod" },
        "Jake Morales": { role: "Field Operator", team: "Southwest Prod" },
        "Laura Simmons": { role: "HSE Officer", team: "HSE Dept" },
        "Tyler Hughes": { role: "Field Operator", team: "Northeast Prod" }
    };

    function updateUserBadge() {
        const info = userRoles[currentUserId] || { role: "Operator", team: "Field Ops" };
        userRoleBadge.textContent = info.role;
        userTeamBadge.textContent = info.team;
    }

    userSelect.addEventListener("change", () => {
        currentUserId = userSelect.value;
        sessionHistory = [];
        updateUserBadge();
        loadHistory(currentUserId);
    });

    btnClearChat.addEventListener("click", () => {
        chatStream.innerHTML = "";
        sessionHistory = [];
    });

    // Initialize Google A2UI & OpenUI Client-Side Runtime
    let lastReceivedA2UI = null;
    const a2uiRuntime = new A2UIRuntime({
        onAction: (actionName, context) => {
            if (context && context.query) {
                submitDirectQuery(context.query);
            }
        }
    });

    // Modal & Playground elements
    const modalOverlay = document.getElementById("a2ui-inspector-modal");
    const btnCloseModal = document.getElementById("btn-close-modal");
    const streamOutput = document.getElementById("a2ui-stream-output");
    const playgroundInput = document.getElementById("a2ui-playground-input");
    const playgroundPreview = document.getElementById("a2ui-playground-preview");
    const btnRenderPlayground = document.getElementById("btn-render-playground");
    const btnCopyStream = document.getElementById("btn-copy-stream");
    const catalogOutput = document.getElementById("a2ui-catalog-output");
    const tabButtons = document.querySelectorAll(".a2ui-tab-btn");
    const tabPanels = document.querySelectorAll(".a2ui-tab-panel");

    function submitDirectQuery(q) {
        userInput.value = q;
        userInput.style.height = "auto";
        chatForm.dispatchEvent(new Event("submit"));
    }

    // Modal tab switching
    tabButtons.forEach(btn => {
        btn.addEventListener("click", () => {
            tabButtons.forEach(b => b.classList.remove("active"));
            tabPanels.forEach(p => p.classList.remove("active"));
            btn.classList.add("active");
            const target = btn.getAttribute("data-tab");
            const panel = document.getElementById(target);
            if (panel) panel.classList.add("active");
        });
    });

    if (btnCloseModal) {
        btnCloseModal.addEventListener("click", () => {
            modalOverlay.style.display = "none";
        });
    }

    if (modalOverlay) {
        modalOverlay.addEventListener("click", (e) => {
            if (e.target === modalOverlay) modalOverlay.style.display = "none";
        });
    }

    // Copy stream button
    if (btnCopyStream) {
        btnCopyStream.addEventListener("click", () => {
            navigator.clipboard.writeText(streamOutput.value);
            const orig = btnCopyStream.textContent;
            btnCopyStream.textContent = "✓ Copied!";
            setTimeout(() => { btnCopyStream.textContent = orig; }, 1500);
        });
    }

    // Live GenUI Playground Renderer
    if (btnRenderPlayground) {
        btnRenderPlayground.addEventListener("click", () => {
            try {
                const parsed = JSON.parse(playgroundInput.value);
                playgroundPreview.innerHTML = "";
                a2uiRuntime.renderPayload(playgroundPreview, parsed);
            } catch (err) {
                playgroundPreview.innerHTML = `<div style="color:var(--accent-rose); font-family:var(--font-mono); font-size:0.8rem;">
                    Invalid A2UI JSON payload: ${err.message}
                </div>`;
            }
        });
    }

    function openA2UIInspector(payload) {
        if (!modalOverlay) return;
        const targetPayload = payload || lastReceivedA2UI || {
            version: "v0.9.1",
            protocol: "A2UI",
            createSurface: { surfaceId: "demo_surface", catalogId: "https://a2ui.org/specification/v0_9_1/catalogs/oilwell_intelligence/catalog.json" },
            updateComponents: {
                surfaceId: "demo_surface",
                components: [
                    { id: "root", component: { Column: { children: { explicitList: ["hdr", "btn"] } } } },
                    { id: "hdr", component: { Text: { text: { literalString: "### ⚡ Google A2UI Declarative Surface" }, usageHint: "h2" } } },
                    { id: "btn", component: { ActionResponseGroup: { actions: [{ label: "🔍 Check Wells", query: "Which wells are down?" }] } } }
                ]
            }
        };

        // Tab 1: Protocol messages (JSON Lines stream)
        if (targetPayload.messages && targetPayload.messages.length > 0) {
            streamOutput.value = targetPayload.messages.map(m => JSON.stringify(m, null, 2)).join("\n\n---\n\n");
        } else {
            streamOutput.value = JSON.stringify(targetPayload, null, 2);
        }

        // Tab 2: Playground input
        playgroundInput.value = JSON.stringify(targetPayload, null, 2);
        playgroundPreview.innerHTML = "";
        try {
            a2uiRuntime.renderPayload(playgroundPreview, targetPayload);
        } catch (e) {
            console.warn(e);
        }

        // Tab 3: Catalog schema
        if (a2uiRuntime.catalogSchema) {
            catalogOutput.value = JSON.stringify(a2uiRuntime.catalogSchema, null, 2);
        } else {
            fetch("/static/a2ui-catalog.json")
                .then(r => r.json())
                .then(sc => { catalogOutput.value = JSON.stringify(sc, null, 2); })
                .catch(() => { catalogOutput.value = "// Catalog schema loaded internally."; });
        }

        modalOverlay.style.display = "flex";
    }

    if (btnToggleA2UI) {
        btnToggleA2UI.addEventListener("click", () => {
            openA2UIInspector(lastReceivedA2UI);
        });
    }

    // Auto-expand textarea
    userInput.addEventListener("input", () => {
        userInput.style.height = "auto";
        userInput.style.height = Math.min(userInput.scrollHeight, 120) + "px";
    });

    // Enter to submit (Shift+Enter for newline)
    userInput.addEventListener("keydown", (e) => {
        if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            chatForm.dispatchEvent(new Event("submit"));
        }
    });

    // Scenario buttons
    scenarioButtons.forEach(btn => {
        btn.addEventListener("click", () => {
            const query = btn.getAttribute("data-query");
            userInput.value = query;
            userInput.style.height = "auto";
            chatForm.dispatchEvent(new Event("submit"));
        });
    });

    chatForm.addEventListener("submit", async (e) => {
        e.preventDefault();
        const text = userInput.value.trim();
        if (!text) return;

        appendMessage("user", currentUserId, text);
        userInput.value = "";
        userInput.style.height = "auto";

        const loadingId = appendLoadingIndicator();
        const payloadHistory = sessionHistory.slice(-8);
        sessionHistory.push({ role: "user", content: text });

        try {
            const res = await fetch("/api/chat", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ user_id: currentUserId, message: text, history: payloadHistory })
            });

            removeLoadingIndicator(loadingId);

            if (!res.ok) {
                appendMessage("assistant", "Copilot Intelligence", "Error processing request. Please try again.");
                return;
            }

            const data = await res.json();
            sessionHistory.push({ role: "assistant", content: data.answer });
            appendMessage("assistant", "Copilot Intelligence", data.answer, data.visual_type, data.visual_data, data.citations, data.a2ui, data.context_meta);
        } catch (err) {
            removeLoadingIndicator(loadingId);
            appendMessage("assistant", "Copilot Intelligence", "Network connection error: " + err.message);
        }
    });

    function appendMessage(role, senderName, text, visualType = null, visualData = null, citations = [], a2ui = null, contextMeta = null) {
        if (a2ui) {
            lastReceivedA2UI = a2ui;
        }

        const wrapper = document.createElement("div");
        wrapper.className = `message-wrapper ${role}`;

        const avatar = document.createElement("div");
        avatar.className = "message-avatar";
        avatar.innerHTML = role === "assistant" 
            ? `<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"></polygon></svg>`
            : `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path><circle cx="12" cy="7" r="4"></circle></svg>`;

        const content = document.createElement("div");
        content.className = "message-content card-glass";

        const header = document.createElement("div");
        header.className = "message-header";
        header.innerHTML = `
            <div style="display:flex; align-items:center; gap:8px;">
                <span class="sender-name">${senderName}</span>
                ${role === "assistant" && a2ui ? '<span class="badge-a2ui" style="font-size:0.6rem; padding:1px 5px;">A2UI v0.9.1</span>' : ''}
            </div>
            <span class="msg-time">Today, 16 Oct</span>
        `;

        content.appendChild(header);

        // Visual Context Pill showing conversational context carryover
        if (contextMeta && (contextMeta.inferred_well || contextMeta.inferred_area)) {
            const ctxBadge = document.createElement("div");
            ctxBadge.className = "context-pill";
            const target = contextMeta.inferred_well || contextMeta.inferred_area;
            const icon = contextMeta.inferred_well ? "🛢️" : "🗺️";
            ctxBadge.innerHTML = `<span class="context-icon">🔗 Context:</span> ${icon} Continuing discussion on <strong>${target}</strong>`;
            content.appendChild(ctxBadge);
        }

        const textDiv = document.createElement("div");
        textDiv.className = "message-text";
        textDiv.innerHTML = typeof marked !== "undefined" ? marked.parse(text) : text;
        content.appendChild(textDiv);

        // Render Google A2UI Generative UI Component Root via A2UIRuntime
        if (a2ui) {
            const a2uiRoot = document.createElement("div");
            a2uiRoot.className = "a2ui-component-root";
            a2uiRuntime.renderPayload(a2uiRoot, a2ui);
            content.appendChild(a2uiRoot);

            // A2UI Declarative Schema Inspector button on message
            const inspector = document.createElement("div");
            inspector.className = "a2ui-inspector-drawer";
            const inspectBtn = document.createElement("button");
            inspectBtn.className = "a2ui-inspector-toggle";
            inspectBtn.innerHTML = `<span>⚙️</span> Inspect A2UI Stream & Playground`;

            inspectBtn.addEventListener("click", () => {
                openA2UIInspector(a2ui);
            });

            inspector.appendChild(inspectBtn);
            content.appendChild(inspector);

        } else if (visualType && visualData) {
            // Traditional fallback visual container
            const visualWrapper = document.createElement("div");
            visualWrapper.className = "visual-container";
            renderLegacyVisual(visualWrapper, visualType, visualData);
            content.appendChild(visualWrapper);
        }

        // Render Citations
        if (citations && citations.length > 0) {
            const citTray = document.createElement("div");
            citTray.className = "citations-tray";
            citations.forEach(c => {
                const pill = document.createElement("span");
                pill.className = "citation-pill";
                pill.textContent = "📄 " + c;
                citTray.appendChild(pill);
            });
            content.appendChild(citTray);
        }

        wrapper.appendChild(avatar);
        wrapper.appendChild(content);
        chatStream.appendChild(wrapper);
        chatStream.scrollTop = chatStream.scrollHeight;
    }

    // =========================================================================
    // Google A2UI (Agent-to-User Interface) Component Trust Catalog Renderer
    // =========================================================================
    function renderA2UIComponents(container, a2ui) {
        (a2ui.components || []).forEach(cmp => {
            if (cmp.type === "WellTelemetryHero") {
                renderA2UIHero(container, cmp.props);
            } else if (cmp.type === "ActionResponseGroup") {
                renderA2UIActions(container, cmp.props);
            } else if (cmp.type === "DataTable") {
                renderA2UITable(container, cmp.props);
            } else if (cmp.type === "TrendLineChart") {
                renderA2UILineChart(container, cmp.props);
            } else if (cmp.type === "RankingBarChart") {
                renderA2UIBarChart(container, cmp.props);
            } else if (cmp.type === "GeoSpatialMap") {
                renderA2UIMap(container, cmp.props);
            } else if (cmp.type === "DensityHeatmap") {
                renderA2UIHeatmap(container, cmp.props);
            }
        });
    }

    function renderA2UIHero(container, props) {
        const isProd = props.isProducing;
        const delta = props.deltaTemp !== undefined ? props.deltaTemp : 0;
        const thresh = props.threshold || 15.0;
        const pct = Math.min(100, Math.max(0, (delta / thresh) * 100));

        const heroEl = document.createElement("div");
        heroEl.className = "a2ui-hero-card";

        const badgeHtml = isProd
            ? `<div class="sc-badge producing"><span class="pulse-dot"></span> PRODUCING OIL</div>`
            : `<div class="sc-badge down"><span class="pulse-dot"></span> NOT PRODUCING (DOWN)</div>`;

        let alertHtml = "";
        if (props.inspectorNotes) {
            alertHtml = `<div style="background:rgba(244,63,94,0.1); border-left:3px solid var(--accent-rose); padding:8px 12px; border-radius:4px; font-size:0.8rem; color:#fca5a5;">
                <strong>Field Inspector Note:</strong> "${props.inspectorNotes}"
            </div>`;
        }

        heroEl.innerHTML = `
            <div class="a2ui-hero-top">
                <div class="a2ui-hero-title">
                    <h3>${props.assetId} <span style="font-size:0.85rem; font-weight:400; color:var(--text-secondary);">(${props.name || ''})</span></h3>
                    <div class="a2ui-hero-sub">Class: <strong>${props.wellType || 'T200'}</strong> | Block: <strong>${props.areaId || ''}</strong> | Record Status: <strong>${props.recordedStatus || 'unknown'}</strong></div>
                </div>
                ${badgeHtml}
            </div>

            <div class="a2ui-hero-grid">
                <div class="a2ui-gauge-box">
                    <div class="a2ui-gauge-header">
                        <span style="font-size:0.75rem; color:var(--text-muted);">Production Delta</span>
                        <span class="a2ui-gauge-val" style="color:${isProd ? '#10b981' : '#f43f5e'};">+${delta} °C</span>
                    </div>
                    <div class="a2ui-gauge-bar">
                        <div class="a2ui-gauge-fill" style="width:${pct}%; background:${isProd ? '#10b981' : '#f43f5e'};"></div>
                    </div>
                    <div style="font-size:0.68rem; color:var(--text-muted); margin-top:4px;">Required Threshold: ≥ ${thresh} °C</div>
                </div>

                <div class="a2ui-meta-box">
                    <div style="font-family:var(--font-mono); font-size:1.25rem; font-weight:700; color:#f97316;">${props.wellheadTemp !== undefined ? props.wellheadTemp + ' °C' : 'N/A'}</div>
                    <div style="font-size:0.7rem; color:var(--text-muted);">Wellhead Sensor</div>
                </div>

                <div class="a2ui-meta-box">
                    <div style="font-family:var(--font-mono); font-size:1.25rem; font-weight:700; color:#06b6d4;">${props.ambientTemp !== undefined ? props.ambientTemp + ' °C' : 'N/A'}</div>
                    <div style="font-size:0.7rem; color:var(--text-muted);">Ambient Air Temp</div>
                </div>
            </div>

            ${alertHtml}

            <div style="font-size:0.75rem; color:var(--text-muted); border-top:1px solid rgba(255,255,255,0.06); padding-top:8px; display:flex; justify-content:space-between;">
                <span>Latest Inspection: <strong>${props.inspectionId || ''}</strong> (${props.inspectedAt ? props.inspectedAt.slice(0, 10) : ''})</span>
                <span>Inspector: <strong>${props.inspector || 'Drone Telemetry'}</strong> (${props.method || 'drone'})</span>
            </div>
        `;

        container.appendChild(heroEl);
    }

    function renderA2UIActions(container, props) {
        const group = document.createElement("div");
        group.className = "a2ui-action-group";

        (props.actions || []).forEach(act => {
            const btn = document.createElement("button");
            btn.className = "a2ui-action-btn";
            btn.textContent = act.label;
            btn.title = `A2UI Two-Way Action: "${act.query}"`;

            // Interactive A2UI two-way action response
            btn.addEventListener("click", () => {
                userInput.value = act.query;
                userInput.style.height = "auto";
                chatForm.dispatchEvent(new Event("submit"));
            });

            group.appendChild(btn);
        });

        container.appendChild(group);
    }

    function renderA2UITable(container, props) {
        const wrapper = document.createElement("div");
        wrapper.className = "data-table-wrapper";
        const headers = props.headers || [];
        const rows = props.rows || [];

        let thHtml = headers.map(h => `<th>${h}</th>`).join("");
        let trHtml = rows.map(row => {
            const tds = row.map(cell => {
                let colorStyle = "";
                const s = String(cell);
                if (s.includes("BREACH") || s.includes("OVERDUE") || s.includes("NOT PRODUCING")) {
                    colorStyle = 'style="color:var(--accent-rose); font-weight:600;"';
                } else if (s.includes("PRODUCING") || s.includes("COMPLIANT")) {
                    colorStyle = 'style="color:var(--accent-emerald); font-weight:600;"';
                }
                return `<td ${colorStyle}>${cell}</td>`;
            }).join("");
            return `<tr>${tds}</tr>`;
        }).join("");

        wrapper.innerHTML = `
            <table class="copilot-table">
                <thead><tr>${thHtml}</tr></thead>
                <tbody>${trHtml}</tbody>
            </table>
        `;
        container.appendChild(wrapper);
    }

    function renderA2UILineChart(container, props) {
        const box = document.createElement("div");
        box.className = "chart-box";
        const chartId = "chart-" + Math.random().toString(36).substring(2, 9);
        box.innerHTML = `<canvas id="${chartId}"></canvas>`;
        container.appendChild(box);

        setTimeout(() => {
            const el = document.getElementById(chartId);
            if (!el) return;
            const ctx = el.getContext("2d");
            const labels = (props.data || []).map(d => d[props.xKey] || d.date);
            const wh = (props.data || []).map(d => d.wellhead_temp_c);
            const amb = (props.data || []).map(d => d.ambient_temp_c);

            new Chart(ctx, {
                type: 'line',
                data: {
                    labels: labels,
                    datasets: [
                        {
                            label: 'Wellhead Temp (°C)',
                            data: wh,
                            borderColor: '#f97316',
                            backgroundColor: 'rgba(249, 115, 22, 0.1)',
                            borderWidth: 2.5,
                            tension: 0.2,
                            pointRadius: 4
                        },
                        {
                            label: 'Ambient Air Temp (°C)',
                            data: amb,
                            borderColor: '#06b6d4',
                            borderWidth: 2,
                            borderDash: [4, 4],
                            tension: 0.2,
                            pointRadius: 3
                        }
                    ]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        title: { display: !!props.title, text: props.title || '', color: '#f3f4f6' },
                        legend: { labels: { color: '#9ca3af' } }
                    },
                    scales: {
                        x: { grid: { color: 'rgba(255,255,255,0.05)' }, ticks: { color: '#9ca3af' } },
                        y: { grid: { color: 'rgba(255,255,255,0.05)' }, ticks: { color: '#9ca3af' } }
                    }
                }
            });
        }, 60);
    }

    function renderA2UIBarChart(container, props) {
        const box = document.createElement("div");
        box.className = "chart-box";
        const chartId = "chart-" + Math.random().toString(36).substring(2, 9);
        box.innerHTML = `<canvas id="${chartId}"></canvas>`;
        container.appendChild(box);

        setTimeout(() => {
            const el = document.getElementById(chartId);
            if (!el) return;
            const ctx = el.getContext("2d");
            const labels = (props.data || []).map(d => d[props.categoryKey] || d.asset_id);
            const values = (props.data || []).map(d => d[props.valueKey] || d.downtime_days);

            new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: labels,
                    datasets: [{
                        label: 'Downtime (Days)',
                        data: values,
                        backgroundColor: 'rgba(244, 63, 94, 0.7)',
                        borderColor: '#f43f5e',
                        borderWidth: 1.5,
                        borderRadius: 6
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: { display: false },
                        title: { display: !!props.title, text: props.title || '', color: '#f3f4f6' }
                    },
                    scales: {
                        x: { grid: { display: false }, ticks: { color: '#9ca3af' } },
                        y: { grid: { color: 'rgba(255,255,255,0.05)' }, ticks: { color: '#9ca3af' } }
                    }
                }
            });
        }, 60);
    }

    function renderA2UIMap(container, props) {
        const box = document.createElement("div");
        box.className = "map-box";
        const mapId = "map-" + Math.random().toString(36).substring(2, 9);
        box.id = mapId;
        container.appendChild(box);

        setTimeout(() => {
            const el = document.getElementById(mapId);
            if (!el) return;
            const center = props.center || { lat: 32.16, lon: -102.16 };
            const zoom = props.zoom || 12;

            const map = L.map(mapId).setView([center.lat, center.lon], zoom);
            L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
                attribution: '&copy; OpenStreetMap &copy; CARTO',
                maxZoom: 19
            }).addTo(map);

            (props.pins || []).forEach(p => {
                const marker = L.circleMarker([p.lat, p.lon], {
                    radius: 8,
                    fillColor: "#f97316",
                    color: "#fff",
                    weight: 2,
                    fillOpacity: 0.85
                }).addTo(map);
                marker.bindPopup(`<strong>${p.title}</strong><br>${p.description}`);
            });
        }, 80);
    }

    function renderA2UIHeatmap(container, props) {
        const wrapper = document.createElement("div");
        wrapper.className = "a2ui-heatmap-container";
        const months = props.months || ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct"];
        const rows = props.data || [];

        let thCols = months.map(m => `<th>${m}</th>`).join("");
        let trHtml = rows.map((r, rIdx) => {
            const areaName = r.area || (props.areas && props.areas[rIdx]) || `Area ${rIdx + 1}`;
            let calcTotal = 0;
            const cells = months.map((m, mIdx) => {
                let count = 0;
                if (Array.isArray(r)) {
                    count = r[mIdx] || 0;
                } else if (typeof r === "object" && r !== null) {
                    count = r[m] !== undefined ? r[m] : (r[String(mIdx + 1).padStart(2, '0')] || 0);
                }
                const num = Number(count) || 0;
                calcTotal += num;

                let bg = "rgba(255,255,255,0.02)";
                let color = "#64748b";
                let weight = "400";
                if (num >= 6) { bg = "rgba(244, 63, 94, 0.75)"; color = "#fff"; weight = "700"; }
                else if (num >= 4) { bg = "rgba(249, 115, 22, 0.55)"; color = "#fff"; weight = "600"; }
                else if (num >= 2) { bg = "rgba(245, 158, 11, 0.35)"; color = "#fff"; }
                else if (num > 0) { bg = "rgba(6, 182, 212, 0.22)"; color = "#e2e8f0"; }

                return `<td style="background:${bg}; color:${color}; font-weight:${weight}; font-family:var(--font-mono); text-align:center;">${num}</td>`;
            }).join("");

            const total = r.Total !== undefined ? r.Total : calcTotal;

            return `
                <tr>
                    <td class="area-label-cell">${areaName}</td>
                    ${cells}
                    <td class="heatmap-total-cell">${total}</td>
                </tr>
            `;
        }).join("");

        wrapper.innerHTML = `
            <div class="chart-header">
                <h4>🔥 ${props.title || 'Spill Density Matrix (Areas × Months)'}</h4>
                <span class="chart-badge">Spatial-Temporal Risk</span>
            </div>
            <div class="a2ui-heatmap-scroll">
                <table class="a2ui-heatmap-table">
                    <thead>
                        <tr><th>Geographic Area</th>${thCols}<th class="th-total">Total</th></tr>
                    </thead>
                    <tbody>${trHtml}</tbody>
                </table>
            </div>
            <div class="heatmap-legend">
                <span class="legend-item"><span class="legend-box" style="background:rgba(255,255,255,0.04); border:1px solid rgba(255,255,255,0.1);"></span> 0 (Zero)</span>
                <span class="legend-item"><span class="legend-box" style="background:rgba(6, 182, 212, 0.4);"></span> 1 (Low)</span>
                <span class="legend-item"><span class="legend-box" style="background:rgba(245, 158, 11, 0.55);"></span> 2–3 (Moderate)</span>
                <span class="legend-item"><span class="legend-box" style="background:rgba(249, 115, 22, 0.7);"></span> 4–5 (Elevated)</span>
                <span class="legend-item"><span class="legend-box" style="background:rgba(244, 63, 94, 0.85);"></span> 6+ (Critical)</span>
            </div>
        `;
        container.appendChild(wrapper);
    }

    function renderLegacyVisual(container, type, data) {
        if (type === "table") renderA2UITable(container, data);
        else if (type === "line_chart") renderA2UILineChart(container, data);
        else if (type === "bar_chart") renderA2UIBarChart(container, data);
        else if (type === "map") renderA2UIMap(container, data);
        else if (type === "heatmap") renderA2UIHeatmap(container, data);
    }

    function appendLoadingIndicator() {
        const id = "loading-" + Date.now();
        const wrapper = document.createElement("div");
        wrapper.className = "message-wrapper assistant";
        wrapper.id = id;
        wrapper.innerHTML = `
            <div class="message-avatar" style="background:#374151;">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"></circle><polyline points="12 6 12 12 14 14"></polyline></svg>
            </div>
            <div class="message-content card-glass" style="display:flex; align-items:center; gap:8px; color:var(--text-muted); font-size:0.85rem;">
                <span class="pulse-dot" style="background:var(--accent-orange);"></span>
                Synthesizing A2UI declarative payload & telemetry...
            </div>
        `;
        chatStream.appendChild(wrapper);
        chatStream.scrollTop = chatStream.scrollHeight;
        return id;
    }

    function removeLoadingIndicator(id) {
        const el = document.getElementById(id);
        if (el) el.remove();
    }

    async function loadHistory(userId) {
        chatStream.innerHTML = "";
        try {
            const res = await fetch(`/api/history?user_id=${encodeURIComponent(userId)}`);
            if (res.ok) {
                const data = await res.json();
                if (data.history && data.history.length > 0) {
                    sessionHistory = data.history.map(m => ({ role: m.role, content: m.content }));
                    data.history.forEach(m => {
                        appendMessage(m.role, m.role === "user" ? userId : "Copilot Intelligence", m.content, m.visual_type, m.visual_data);
                    });
                    return;
                }
            }
        } catch (e) {}

        appendMessage("assistant", "Copilot Intelligence", `Welcome, **${userId}**! Active session initialized with Google A2UI protocol. You can ask any question, inspect telemetry, or click quick actions on cards.`);
    }

    async function fetchFieldStats() {
        try {
            const res = await fetch('/api/stats');
            if (res.ok) {
                const s = await res.json();
                const elWells = document.getElementById('stat-wells');
                const elInsp = document.getElementById('stat-inspections');
                const elMaint = document.getElementById('stat-maint');
                const elSpills = document.getElementById('stat-spills');

                if (elWells && s.wells != null) elWells.textContent = s.wells.toLocaleString();
                if (elInsp && s.inspections != null) elInsp.textContent = (s.inspections >= 1000 ? (s.inspections / 1000).toFixed(1) + 'k' : s.inspections);
                if (elMaint && s.maintenance_jobs != null) elMaint.textContent = (s.maintenance_jobs >= 1000 ? (s.maintenance_jobs / 1000).toFixed(1) + 'k' : s.maintenance_jobs);
                if (elSpills && s.spills_detected != null) elSpills.textContent = s.spills_detected.toLocaleString();
            }
        } catch (e) {
            console.warn("Failed to fetch live field stats:", e);
        }
    }

    updateUserBadge();
    fetchFieldStats();
});
