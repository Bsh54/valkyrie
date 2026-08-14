// Docking lab, built as an application workbench inside AppShell: a command run-bar,
// a central 3D workspace, and a right inspector. Wired to POST /api/screenings and
// GET /api/screenings/:id. Live target structure before a run, docked pose after.
const LabPage = {
    state: { targets: [], compounds: [], activeTargetId: null, result: null, loading: false, error: null },

    async render(mountEl, params) {
        this.mountEl = mountEl;
        this.state.result = null;
        this.state.loading = true;
        this.paint();
        try {
            this.state.targets = await API.getTargets();
            this.state.compounds = await API.getCompounds();
            this.state.activeTargetId = this.state.targets[0]?.id ?? null;
        } catch (e) {
            this.state.error = e.message;
        }
        this.state.loading = false;
        if (params.resultId) {
            await this.loadResult(params.resultId);
        } else {
            this.paint();
        }
    },

    async loadResult(id) {
        this.state.loading = true;
        this.paint();
        try {
            this.state.result = await API.getScreening(id);
            this.state.error = null;
        } catch (e) {
            this.state.error = e.message;
            this.state.result = null;
        }
        this.state.loading = false;
        this.paint();
    },

    async submit() {
        const molecule = document.getElementById("molecule-input").value.trim();
        const exhaustiveness = parseInt(document.getElementById("exhaustiveness-input").value, 10) || 8;
        if (!molecule) {
            this.state.error = "Enter a molecule name or SMILES.";
            this.paint();
            return;
        }
        this.state.loading = true;
        this.state.error = null;
        this.paint();
        try {
            const result = await API.submitScreening(molecule, this.state.activeTargetId, exhaustiveness);
            Router.navigate(`/result/${result.result_id}`);
        } catch (e) {
            this.state.error = e.message;
            this.state.loading = false;
            this.paint();
        }
    },

    selectTarget(id) {
        this.state.activeTargetId = id;
        this.paint();
    },

    pickCompound(smiles) {
        const input = document.getElementById("molecule-input");
        if (input) {
            input.value = smiles;
            input.focus();
        }
    },

    paint() {
        this.mountEl.innerHTML = AppShell.shell(this.body());
        this.wireEvents();
        if (this.state.result?.pose_sdf) {
            const t = this.state.targets.find((x) => x.id === this.state.result.target_id);
            Viewer3D.renderResult("viewer-3d", this.state.result.pose_sdf, t?.pdb_id);
        } else if (!this.state.loading) {
            this.previewTarget();
        }
    },

    previewTarget() {
        if (typeof $3Dmol === "undefined") return;
        const active = this.state.targets.find((t) => t.id === this.state.activeTargetId);
        const el = document.getElementById("viewer-3d");
        if (!el || !active) return;
        try {
            const viewer = $3Dmol.createViewer(el, { backgroundColor: "#f7f9fb" });
            $3Dmol.download(`pdb:${active.pdb_id}`, viewer, {}, () => {
                const fb = document.getElementById("viewer-3d-fallback");
                if (fb) fb.remove();
                viewer.setStyle({}, { cartoon: { color: "spectrum" } });
                viewer.addStyle({ hetflag: true }, { stick: { colorscheme: "Jmol", radius: 0.25 } });
                viewer.zoomTo();
                viewer.spin("y", 0.4);
                viewer.render();
            });
        } catch (e) {
            /* keep fallback */
        }
    },

    wireEvents() {
        const btn = document.getElementById("run-docking-btn");
        if (btn) btn.addEventListener("click", () => this.submit());
        const sel = document.getElementById("target-select");
        if (sel) sel.addEventListener("change", () => this.selectTarget(sel.value));
        const input = document.getElementById("molecule-input");
        if (input) input.addEventListener("keydown", (e) => { if (e.key === "Enter") this.submit(); });
        document.querySelectorAll("[data-compound-smiles]").forEach((el) => {
            el.addEventListener("click", () => this.pickCompound(el.dataset.compoundSmiles));
        });
    },

    body() {
        const active = this.state.targets.find((t) => t.id === this.state.activeTargetId);
        const r = this.state.result;
        const title = `
            <h1 class="font-headline-md text-body-lg text-on-surface font-medium">Docking Lab</h1>
            ${active ? `<span class="font-code-md text-xs text-on-surface-variant bg-surface-container-low border border-outline-variant rounded-full px-2.5 py-1">${escapeHtml(active.name)} &middot; ${escapeHtml(active.pdb_id)}</span>` : ""}`;
        const actions = r
            ? `<a href="${API.reportUrl(r.result_id)}" class="inline-flex items-center gap-1.5 bg-surface-container-low border border-outline-variant text-on-surface px-3 py-1.5 rounded-lg font-body-sm text-body-sm hover:bg-surface-container transition-colors">
                <span class="material-symbols-outlined text-[18px]">download</span> PDF</a>`
            : "";

        return `
        ${AppShell.toolbar(title, actions)}
        ${this.runBar(active)}
        ${this.state.error ? `<div class="mx-5 mt-4 p-3 bg-error-container text-on-error-container rounded-xl font-body-sm text-body-sm">${escapeHtml(this.state.error)}</div>` : ""}
        <div class="flex-1 grid grid-cols-1 lg:grid-cols-[1fr_360px] min-h-0">
            <section class="flex flex-col gap-5 p-5 min-w-0 border-b lg:border-b-0 lg:border-r border-outline-variant">
                ${this.state.loading && !r ? this.loadingBlock() : this.workspace(active, r)}
            </section>
            <aside class="p-5 flex flex-col gap-5 bg-surface-container-lowest">
                ${r ? this.inspector(r) : this.inspectorEmpty(active)}
            </aside>
        </div>`;
    },

    runBar(active) {
        const options = this.state.targets
            .map((t) => `<option value="${t.id}" ${t.id === this.state.activeTargetId ? "selected" : ""}>${escapeHtml(t.name)} (${escapeHtml(t.disease)})</option>`)
            .join("");
        const chips = this.state.compounds
            .slice(0, 5)
            .map(
                (c) => `<button data-compound-smiles="${escapeHtml(c.smiles)}" class="shrink-0 inline-flex items-center gap-1 font-body-sm text-body-sm text-on-surface-variant hover:text-primary bg-surface border border-outline-variant rounded-full px-2.5 py-1 transition-colors">
                    <span class="material-symbols-outlined text-[15px] text-molecular-green">local_florist</span>${escapeHtml(c.compound_name)}</button>`
            )
            .join("");
        return `
        <div class="border-b border-outline-variant bg-surface px-5 py-4">
            <div class="flex flex-col md:flex-row gap-3 md:items-end">
                <div class="md:w-56">
                    <label class="font-label-caps text-label-caps text-on-surface-variant uppercase block mb-1.5">Target</label>
                    <select id="target-select" class="w-full px-3 py-2.5 bg-surface-container-low border border-outline-variant rounded-xl font-body-md text-body-md focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary">${options}</select>
                </div>
                <div class="flex-1">
                    <label class="font-label-caps text-label-caps text-on-surface-variant uppercase block mb-1.5">Molecule (name or SMILES)</label>
                    <input id="molecule-input" type="text" placeholder="e.g. artemisinin, quinine, or a SMILES string"
                        class="w-full px-4 py-2.5 bg-surface-container-low border border-outline-variant rounded-xl font-code-md text-code-md focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary" />
                </div>
                <div class="w-full md:w-28">
                    <label class="font-label-caps text-label-caps text-on-surface-variant uppercase block mb-1.5">Exhaust.</label>
                    <input id="exhaustiveness-input" type="number" min="1" max="16" value="8"
                        class="w-full px-3 py-2.5 bg-surface-container-low border border-outline-variant rounded-xl font-code-md text-code-md focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary" />
                </div>
                <button id="run-docking-btn" ${this.state.loading ? "disabled" : ""}
                    class="bg-primary text-on-primary py-2.5 px-6 rounded-xl hover:bg-deep-navy transition-colors font-medium flex items-center justify-center gap-2 disabled:opacity-60">
                    <span class="material-symbols-outlined text-[20px]">play_arrow</span>${this.state.loading ? "Running" : "Run"}
                </button>
            </div>
            ${chips ? `<div class="flex items-center gap-2 mt-3 overflow-x-auto"><span class="font-label-caps text-label-caps text-on-surface-variant uppercase shrink-0">Try</span>${chips}</div>` : ""}
        </div>`;
    },

    workspace(active, r) {
        return `
        ${this.viewport(r ? "Docked pose in the pocket" : active ? `${escapeHtml(active.name)} &middot; ${escapeHtml(active.pdb_id)} &middot; live 3D` : "3D structure", !!r)}
        ${r ? this.funnelCard(r) : ""}
        ${r ? this.explanationBlock(r.explanation) : ""}`;
    },

    viewport(label, controls = false) {
        const btn = (icon, title, action) =>
            `<button title="${title}" onclick="${action}" class="w-8 h-8 rounded-lg bg-white/10 hover:bg-white/25 text-white flex items-center justify-center transition-colors backdrop-blur-sm"><span class="material-symbols-outlined text-[18px]">${icon}</span></button>`;
        const bar = controls
            ? `<div class="absolute top-3 right-3 z-10 flex gap-1.5">
                ${btn("360", "Spin", "Viewer3D.toggleSpin()")}
                ${btn("blur_on", "Pocket surface", "Viewer3D.toggleSurface()")}
                ${btn("visibility", "Show / hide protein", "Viewer3D.toggleProtein()")}
                ${btn("recenter", "Reset view", "Viewer3D.reset()")}
                ${btn("photo_camera", "Save PNG", "Viewer3D.screenshot()")}
            </div>`
            : "";
        return `
        <div id="viewer-3d" class="relative w-full rounded-2xl border border-outline-variant ${controls ? "bg-[#0b1526]" : "bg-surface"} overflow-hidden" style="height:${controls ? 420 : 380}px;">
            <div id="viewer-3d-fallback" class="absolute inset-0 flex items-center justify-center ${controls ? "text-primary-fixed-dim" : "text-outline"} font-code-md text-xs pointer-events-none">Loading structure...</div>
            ${bar}
            <span class="absolute bottom-3 left-3 z-10 font-label-caps text-label-caps ${controls ? "text-white bg-black/30 border-white/20" : "text-primary bg-surface/85 border-outline-variant"} px-2 py-1 rounded border">${label}</span>
        </div>`;
    },

    stepsCard() {
        return `
        <div class="grid grid-cols-1 sm:grid-cols-3 gap-4">
            ${[["labs", "1. Dock", "Vina places the molecule in the pocket."], ["stacked_line_chart", "2. Rescore", "Vinardo consensus re-ranks the pose."], ["filter_alt", "3. Filter", "ADMET and toxicity set the verdict."]]
                .map(
                    ([icon, t, d]) => `
                <div class="bg-surface-container-lowest border border-outline-variant rounded-2xl p-4">
                    <span class="material-symbols-outlined text-primary" style="font-variation-settings:'FILL' 1;">${icon}</span>
                    <h4 class="font-headline-md text-body-md text-on-surface mt-1.5">${t}</h4>
                    <p class="font-body-sm text-body-sm text-on-surface-variant mt-1">${d}</p>
                </div>`
                )
                .join("")}
        </div>`;
    },

    funnelCard(r) {
        return `
        <div class="bg-surface-container-lowest border border-outline-variant rounded-2xl p-5">
            <h4 class="font-label-caps text-label-caps text-on-surface uppercase mb-3 flex items-center gap-2">
                <span class="material-symbols-outlined text-[18px]">filter_alt</span> Pipeline funnel
            </h4>
            ${this.funnel(r)}
        </div>`;
    },

    loadingBlock() {
        return `<div class="flex-1 flex items-center justify-center py-20 bg-surface-container-lowest border border-outline-variant rounded-2xl">
            <div class="text-center">
                <span class="material-symbols-outlined animate-spin text-primary text-4xl">progress_activity</span>
                <p class="mt-3 font-body-md text-body-md text-on-surface">Docking in progress</p>
                <p class="mt-1 font-body-sm text-body-sm text-on-surface-variant">A real Vina run takes one to two minutes.</p>
            </div>
        </div>`;
    },

    inspectorEmpty(active) {
        return `
        <div class="bg-surface-container-lowest border border-outline-variant rounded-2xl p-5">
            <h3 class="font-label-caps text-label-caps text-on-surface-variant uppercase mb-3">Selected target</h3>
            ${active
                ? `<div class="space-y-2 font-body-sm text-body-sm">
                    <div class="flex justify-between"><span class="text-on-surface-variant">Name</span><span class="text-on-surface font-medium">${escapeHtml(active.name)}</span></div>
                    <div class="flex justify-between"><span class="text-on-surface-variant">Disease</span><span class="text-on-surface capitalize">${escapeHtml(active.disease)}</span></div>
                    <div class="flex justify-between"><span class="text-on-surface-variant">PDB</span><span class="font-code-md">${escapeHtml(active.pdb_id)}</span></div>
                    <div class="flex justify-between"><span class="text-on-surface-variant">Reference</span><span class="text-on-surface">${escapeHtml(active.reference_drug)}</span></div>
                </div>`
                : `<p class="font-body-sm text-body-sm text-on-surface-variant">No target loaded.</p>`}
        </div>
        <div class="bg-primary-fixed/20 border border-primary-fixed rounded-2xl p-5">
            <p class="font-body-sm text-body-sm text-on-surface-variant">Pick a target, enter a molecule, and press Run. The result appears here: score, drug-likeness, comparison to the reference drug, ADMET and an AI explanation.</p>
        </div>
        <div class="bg-surface-container-lowest border border-outline-variant rounded-2xl p-4 text-center">
            <p class="font-body-sm text-body-sm text-on-surface-variant">Or browse the <a data-link href="/library" class="text-primary underline">ethnobotanical library</a>.</p>
        </div>`;
    },

    inspector(r) {
        const verdictColor = { Promising: "success-docking", Comparable: "structural-blue", Weak: "warning-energy", Discard: "error" }[r.verdict] || "outline";
        return `
        <div class="flex items-center justify-between">
            <span class="font-label-caps text-label-caps text-on-surface-variant uppercase">Result</span>
            <span class="bg-${verdictColor}/10 text-${verdictColor} px-3 py-1 rounded-full font-label-caps text-label-caps border border-${verdictColor}/30">${escapeHtml(r.verdict)}</span>
        </div>
        <div class="bg-surface-container-lowest border border-outline-variant rounded-2xl shadow-card p-5">
            <div class="text-on-surface-variant font-label-caps text-label-caps uppercase mb-1">Vina affinity</div>
            <div class="font-code-md text-[36px] font-bold leading-none text-primary flex items-baseline gap-2 tabular-nums">${r.affinity_kcal_mol}<span class="font-body-sm text-body-sm text-on-surface-variant font-normal">kcal/mol</span></div>
            <div class="grid grid-cols-2 gap-2 mt-4">
                <div class="bg-surface p-2.5 rounded-xl text-center border border-outline-variant/50"><div class="text-xs text-on-surface-variant mb-1">Vinardo</div><div class="font-code-md text-code-md">${r.vinardo_score}</div></div>
                <div class="bg-surface p-2.5 rounded-xl text-center border border-outline-variant/50"><div class="text-xs text-on-surface-variant mb-1">Consensus</div><div class="font-code-md text-code-md">${r.consensus_score}</div></div>
            </div>
        </div>
        <div class="bg-surface-container-lowest border border-outline-variant rounded-2xl p-5">
            <h4 class="font-label-caps text-label-caps text-on-surface uppercase mb-3 flex items-center justify-between">Drug-likeness
                <span class="bg-${r.is_hit ? "molecular-green" : "error"}/10 text-${r.is_hit ? "molecular-green" : "error"} px-2 py-0.5 rounded font-label-caps text-[10px] border border-${r.is_hit ? "molecular-green" : "error"}/20">${r.is_hit ? "HIT" : "FILTERED"}</span>
            </h4>
            ${this.druglikeness(r.drug_likeness)}
            ${!r.is_hit && r.hit_failure_reasons?.length ? `<p class="text-xs text-error mt-2">${r.hit_failure_reasons.map(escapeHtml).join("; ")}</p>` : ""}
        </div>
        <div class="bg-surface-container-lowest border border-outline-variant rounded-2xl p-5">
            <h4 class="font-label-caps text-label-caps text-on-surface uppercase mb-3">Compared to reference</h4>
            ${this.comparisonTable(r.comparisons)}
        </div>
        ${this.admetBlock(r.admet)}
        <div class="bg-surface-container-low p-3 rounded-xl font-code-md text-xs text-on-surface-variant break-all border border-outline-variant/50">${escapeHtml(r.molecule_smiles)}</div>`;
    },

    funnel(r) {
        const admetOk = r.admet?.passes_filter !== false;
        const stages = [
            { label: "Vina docking", value: `${r.affinity_kcal_mol} kcal/mol`, ok: true },
            { label: "Vinardo rescore", value: `${r.vinardo_score} kcal/mol`, ok: true },
            { label: "Consensus", value: r.consensus_score, ok: true },
            { label: "Drug-likeness", value: `${r.drug_likeness?.lipinski_violations ?? "?"} violations`, ok: r.is_hit },
            { label: "ADMET filter", value: admetOk ? "clean" : "flagged", ok: admetOk },
        ];
        return `<div class="flex flex-wrap gap-2.5">${stages
            .map(
                (s) => `<div class="flex items-center gap-2 px-3 py-2 rounded-xl border ${s.skipped ? "border-outline-variant text-on-surface-variant" : s.ok ? "border-success-docking/40 text-success-docking" : "border-error/40 text-error"} bg-surface">
                <span class="material-symbols-outlined text-[18px]">${s.skipped ? "remove_circle" : s.ok ? "check_circle" : "cancel"}</span>
                <span class="font-body-sm text-body-sm text-on-surface">${s.label}</span>
                <span class="font-code-md text-xs text-on-surface-variant">${escapeHtml(String(s.value))}</span>
            </div>`
            )
            .join("")}</div>`;
    },

    druglikeness(d) {
        if (!d) return "";
        const rows = [
            ["Molecular weight", d.molecular_weight],
            ["LogP", d.logp],
            ["H-donors", d.hbd],
            ["H-acceptors", d.hba],
            ["TPSA", d.tpsa],
            ["Rotatable bonds", d.rotatable_bonds],
        ];
        return `<ul class="flex flex-col gap-0.5 font-body-sm text-body-sm">${rows
            .map(
                ([label, value]) => `<li class="flex items-center justify-between p-1.5 hover:bg-surface-container-low rounded-lg"><span class="text-on-surface-variant">${label}</span><span class="font-code-md">${value}</span></li>`
            )
            .join("")}</ul>`;
    },

    comparisonTable(comparisons) {
        if (!comparisons?.length) return `<p class="font-body-sm text-body-sm text-on-surface-variant">No comparison available.</p>`;
        return `<div class="grid grid-cols-3 gap-2 text-xs">
            <div class="text-on-surface-variant font-medium pb-1 border-b border-outline-variant">Metric</div>
            <div class="text-on-surface-variant font-medium pb-1 border-b border-outline-variant">Molecule</div>
            <div class="text-on-surface-variant font-medium pb-1 border-b border-outline-variant">Reference</div>
            ${comparisons
                .map(
                    (c) => `<div class="py-1">${escapeHtml(c.metric)}</div>
                <div class="py-1 font-code-md ${c.verdict === "better" ? "text-success-docking" : ""}">${c.molecule_value}</div>
                <div class="py-1 font-code-md text-on-surface-variant">${c.reference_value}</div>`
                )
                .join("")}
        </div>`;
    },

    admetBlock(admet) {
        if (!admet) return "";
        const alerts = [...(admet.pains_alerts || []), ...(admet.brenk_alerts || []), ...(admet.reactive_groups || [])];
        return `<div class="bg-surface-container-lowest border border-outline-variant rounded-2xl p-5">
            <h4 class="font-label-caps text-label-caps text-on-surface uppercase mb-2">ADMET</h4>
            <p class="font-body-sm text-body-sm text-on-surface-variant">Predicted logS: <span class="font-code-md">${admet.esol_logs}</span> &middot; GI absorption: ${escapeHtml(admet.gi_absorption)}</p>
            ${alerts.length ? `<p class="text-xs text-error mt-1">${alerts.map(escapeHtml).join(", ")}</p>` : `<p class="text-xs text-success-docking mt-1">No structural alerts.</p>`}
        </div>`;
    },

    explanationBlock(explanation) {
        if (!explanation || explanation.status !== "success") return "";
        return `<div class="bg-primary-fixed/20 border border-primary-fixed rounded-2xl p-5">
            <h4 class="font-label-caps text-label-caps text-primary uppercase mb-2 flex items-center gap-1"><span class="material-symbols-outlined text-[18px]">smart_toy</span> AI explanation</h4>
            <p class="font-body-sm text-body-sm text-on-surface-variant whitespace-pre-line">${escapeHtml(explanation.text)}</p>
        </div>`;
    },
};
