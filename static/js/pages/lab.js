// Docking lab. Layout lifted from stitch_drugforge_molecular_docking_lab/drugforge_docking_lab,
// wired to POST /api/screenings and GET /api/screenings/:id.
const LabPage = {
    state: { targets: [], compounds: [], activeTargetId: null, result: null, loading: false, error: null },

    async render(mountEl, params) {
        this.mountEl = mountEl;
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
        Router.navigate("/lab");
        setTimeout(() => {
            const input = document.getElementById("molecule-input");
            if (input) input.value = smiles;
        }, 0);
    },

    paint() {
        this.mountEl.innerHTML = Layout.shell(this.body());
        this.wireEvents();
        if (this.state.result?.pose_sdf) {
            Viewer3D.render("viewer-3d", this.state.result.pose_sdf);
        }
    },

    wireEvents() {
        const btn = document.getElementById("run-docking-btn");
        if (btn) btn.addEventListener("click", () => this.submit());

        document.querySelectorAll("[data-target-id]").forEach((el) => {
            el.addEventListener("click", () => this.selectTarget(el.dataset.targetId));
        });
        document.querySelectorAll("[data-compound-smiles]").forEach((el) => {
            el.addEventListener("click", () => this.pickCompound(el.dataset.compoundSmiles));
        });
    },

    body() {
        const active = this.state.targets.find((t) => t.id === this.state.activeTargetId);

        return `
        <div class="flex flex-1 overflow-hidden max-w-max-width mx-auto w-full">
            <aside class="hidden lg:flex flex-col shrink-0 p-4 gap-2 bg-surface-container-low border-r border-outline-variant w-64">
                <div class="mb-4 px-2">
                    <h2 class="font-headline-md text-headline-md text-primary">Targets</h2>
                    <p class="text-on-surface-variant text-sm mt-1">${active ? active.disease : ""}</p>
                </div>
                ${this.targetList()}
                <div class="mt-6 px-2">
                    <h3 class="font-label-caps text-label-caps text-on-surface-variant mb-2">Quick pick</h3>
                    ${this.compoundQuickPicks()}
                </div>
            </aside>

            <main class="flex-1 flex flex-col overflow-y-auto bg-background">
                <div class="h-auto min-h-16 border-b border-outline-variant flex flex-wrap items-center justify-between gap-3 px-4 py-3 bg-surface">
                    <div class="flex-1 min-w-[220px]">
                        <label class="font-label-caps text-label-caps text-on-surface-variant block mb-1">Molecule (name or SMILES)</label>
                        <input id="molecule-input" type="text" placeholder="e.g. artemisinin"
                            class="w-full px-3 py-2 bg-surface-container-low border border-outline-variant rounded font-code-md text-code-md focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary" />
                    </div>
                    <div class="w-28">
                        <label class="font-label-caps text-label-caps text-on-surface-variant block mb-1">Exhaustiveness</label>
                        <input id="exhaustiveness-input" type="number" min="1" max="32" value="8"
                            class="w-full px-3 py-2 bg-surface-container-low border border-outline-variant rounded font-code-md text-code-md focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary" />
                    </div>
                    <button id="run-docking-btn" ${this.state.loading ? "disabled" : ""}
                        class="bg-primary text-on-primary py-2.5 px-5 rounded hover:bg-deep-navy transition-colors font-label-caps text-label-caps flex items-center justify-center gap-2 disabled:opacity-60">
                        <span class="material-symbols-outlined text-sm">play_arrow</span>
                        ${this.state.loading ? "Running..." : "Run Docking"}
                    </button>
                </div>

                ${this.state.error ? `<div class="m-4 p-3 bg-error-container text-on-error-container rounded font-body-sm text-body-sm">${escapeHtml(this.state.error)}</div>` : ""}

                ${this.state.loading && !this.state.result ? this.loadingBlock() : ""}
                ${this.state.result ? this.resultBlock() : this.emptyBlock()}
            </main>
        </div>`;
    },

    targetList() {
        return this.state.targets
            .map(
                (t) => `
            <div data-target-id="${t.id}" class="cursor-pointer bg-surface-container-lowest border ${t.id === this.state.activeTargetId ? "border-primary" : "border-outline-variant"} rounded p-3 relative hover:bg-surface transition-colors">
                <h4 class="font-label-caps text-label-caps ${t.id === this.state.activeTargetId ? "text-primary" : "text-on-surface"} mb-1">${escapeHtml(t.name)}</h4>
                <p class="font-code-md text-code-md text-on-surface-variant">PDB: ${escapeHtml(t.pdb_id)}</p>
                <div class="mt-1 text-xs text-on-surface-variant">Ref: <span class="font-medium text-on-surface">${escapeHtml(t.reference_drug)}</span></div>
            </div>`
            )
            .join("");
    },

    compoundQuickPicks() {
        return `<div class="flex flex-col gap-1">${this.state.compounds
            .slice(0, 8)
            .map(
                (c) => `<button data-compound-smiles="${escapeHtml(c.smiles)}"
                class="text-left font-body-sm text-body-sm text-on-surface-variant hover:text-primary hover:bg-surface-container-low rounded px-2 py-1.5 transition-colors">
                ${escapeHtml(c.compound_name)}</button>`
            )
            .join("")}</div>`;
    },

    loadingBlock() {
        return `<div class="flex-1 flex items-center justify-center p-12">
            <div class="text-center">
                <span class="material-symbols-outlined animate-spin text-primary text-4xl">progress_activity</span>
                <p class="mt-3 font-body-sm text-body-sm text-on-surface-variant">Docking usually takes one to two minutes.</p>
            </div>
        </div>`;
    },

    emptyBlock() {
        return `<div class="flex-1 flex items-center justify-center p-12 text-center">
            <p class="font-body-md text-body-md text-on-surface-variant max-w-md">
                Enter a molecule and click Run Docking, or pick a compound from the ethnobotanical
                <a data-link href="/library" class="text-primary underline">library</a>.
            </p>
        </div>`;
    },

    resultBlock() {
        const r = this.state.result;
        const verdictColor = { Promising: "success-docking", Comparable: "structural-blue", Weak: "warning-energy", Discard: "error" }[r.verdict] || "outline";

        return `
        <div class="flex flex-col lg:flex-row flex-1">
            <div class="flex-1 flex flex-col">
                <div class="h-12 border-b border-outline-variant flex items-center justify-between px-4 bg-surface">
                    <span class="font-body-md text-body-md font-medium">${escapeHtml(r.target_id)} &mdash; <span class="font-code-md text-code-md">${escapeHtml(r.molecule_smiles)}</span></span>
                    <span class="bg-${verdictColor}/10 text-${verdictColor} px-3 py-1 rounded-full font-label-caps text-label-caps border border-${verdictColor}/30">${escapeHtml(r.verdict)}</span>
                </div>
                <div id="viewer-3d" class="flex-1 min-h-[320px] bg-surface-container-low shadow-[inset_0_2px_10px_rgba(0,0,0,0.05)]"></div>
                <div class="border-t border-outline-variant bg-surface p-4">
                    <h4 class="font-label-caps text-label-caps text-on-surface mb-3 flex items-center gap-2">
                        <span class="material-symbols-outlined text-sm">compare_arrows</span> Pipeline funnel
                    </h4>
                    ${this.funnel(r)}
                </div>
            </div>

            <div class="w-full lg:w-96 bg-surface-container-lowest border-l border-outline-variant overflow-y-auto p-4 flex flex-col gap-6">
                <div>
                    <h3 class="font-headline-md text-body-lg font-bold text-on-surface border-b border-outline-variant pb-2 mb-3">Scores</h3>
                    <div class="bg-surface border border-outline-variant rounded p-4 mb-3">
                        <div class="text-on-surface-variant text-xs mb-1 uppercase tracking-wider">Vina affinity</div>
                        <div class="font-headline-xl text-headline-xl text-primary flex items-baseline gap-1">
                            ${r.affinity_kcal_mol} <span class="font-body-sm text-sm text-on-surface-variant font-normal">kcal/mol</span>
                        </div>
                    </div>
                    <div class="grid grid-cols-2 gap-2">
                        <div class="bg-surface-container-low p-2 rounded text-center border border-outline-variant/50">
                            <div class="text-xs text-on-surface-variant mb-1">Vinardo</div>
                            <div class="font-code-md text-code-md">${r.vinardo_score}</div>
                        </div>
                        <div class="bg-surface-container-low p-2 rounded text-center border border-outline-variant/50">
                            <div class="text-xs text-on-surface-variant mb-1">Consensus</div>
                            <div class="font-code-md text-code-md">${r.consensus_score}</div>
                        </div>
                    </div>
                </div>

                <div>
                    <h4 class="font-label-caps text-label-caps text-on-surface mb-3 flex items-center justify-between">
                        Drug-likeness
                        <span class="bg-${r.is_hit ? "molecular-green" : "error"}/10 text-${r.is_hit ? "molecular-green" : "error"} px-2 py-0.5 rounded font-label-caps text-[10px]">${r.is_hit ? "HIT" : "FILTERED"}</span>
                    </h4>
                    ${this.druglikeness(r.drug_likeness)}
                    ${!r.is_hit && r.hit_failure_reasons?.length ? `<p class="text-xs text-error mt-2">${r.hit_failure_reasons.map(escapeHtml).join("; ")}</p>` : ""}
                </div>

                <div>
                    <h4 class="font-label-caps text-label-caps text-on-surface mb-3">Comparison to reference</h4>
                    ${this.comparisonTable(r.comparisons)}
                </div>

                ${this.admetBlock(r.admet)}
                ${this.explanationBlock(r.explanation)}

                <div class="mt-auto pt-4 border-t border-outline-variant flex flex-col gap-2">
                    <div class="bg-[#F1F5F9] p-3 rounded font-code-md text-xs text-on-surface-variant break-all">${escapeHtml(r.molecule_smiles)}</div>
                    <a href="${API.reportUrl(r.result_id)}" class="text-center bg-primary text-on-primary py-2 rounded font-label-caps text-label-caps hover:bg-deep-navy transition-colors">Download PDF report</a>
                </div>
            </div>
        </div>`;
    },

    funnel(r) {
        const admetOk = r.admet?.passes_filter !== false;
        const boltzStatus = r.boltz?.status;
        const stages = [
            { label: "Vina docking", value: `${r.affinity_kcal_mol} kcal/mol`, ok: true },
            { label: "Vinardo rescore", value: `${r.vinardo_score} kcal/mol`, ok: true },
            { label: "Consensus", value: r.consensus_score, ok: true },
            { label: "Drug-likeness", value: `${r.drug_likeness?.lipinski_violations ?? "?"} violations`, ok: r.is_hit },
            { label: "ADMET filter", value: admetOk ? "clean" : "flagged", ok: admetOk },
            { label: "Boltz-2 AI", value: boltzStatus === "success" ? `${r.boltz.predicted_affinity} kcal/mol` : (boltzStatus || "not invoked"), ok: boltzStatus === "success", skipped: boltzStatus !== "success" },
        ];
        return `<div class="flex flex-wrap gap-3">${stages
            .map(
                (s) => `<div class="flex items-center gap-2 px-3 py-2 rounded border ${s.skipped ? "border-outline-variant text-on-surface-variant" : s.ok ? "border-success-docking/40 text-success-docking" : "border-error/40 text-error"} bg-surface-container-lowest">
                <span class="material-symbols-outlined text-sm">${s.skipped ? "remove_circle" : s.ok ? "check_circle" : "cancel"}</span>
                <span class="font-body-sm text-body-sm text-on-surface">${s.label}</span>
                <span class="font-code-md text-code-md text-on-surface-variant">${escapeHtml(String(s.value))}</span>
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
        return `<ul class="flex flex-col gap-1 font-body-sm text-body-sm">${rows
            .map(
                ([label, value]) => `<li class="flex items-center justify-between p-1.5 hover:bg-surface-container-low rounded">
                <span class="text-on-surface-variant">${label}</span><span class="font-code-md">${value}</span>
            </li>`
            )
            .join("")}</ul>`;
    },

    comparisonTable(comparisons) {
        if (!comparisons?.length) return `<p class="text-sm text-on-surface-variant">No comparison available.</p>`;
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
        return `<div>
            <h4 class="font-label-caps text-label-caps text-on-surface mb-2">ADMET</h4>
            <p class="font-body-sm text-body-sm text-on-surface-variant">Predicted logS: <span class="font-code-md">${admet.esol_logs}</span> &middot; GI absorption: ${escapeHtml(admet.gi_absorption)}</p>
            ${alerts.length ? `<p class="text-xs text-error mt-1">${alerts.map(escapeHtml).join(", ")}</p>` : `<p class="text-xs text-success-docking mt-1">No structural alerts.</p>`}
        </div>`;
    },

    explanationBlock(explanation) {
        if (!explanation || explanation.status !== "success") return "";
        return `<div class="bg-surface-container-low border border-outline-variant rounded p-3">
            <h4 class="font-label-caps text-label-caps text-on-surface mb-2 flex items-center gap-1">
                <span class="material-symbols-outlined text-sm">smart_toy</span> AI explanation
            </h4>
            <p class="font-body-sm text-body-sm text-on-surface-variant whitespace-pre-line">${escapeHtml(explanation.text)}</p>
        </div>`;
    },
};
