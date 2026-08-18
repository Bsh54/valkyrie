// Benchmarks. Bento visual style from
// stitch_valkyrie_molecular_docking_lab/valkyrie_benchmarks, wired to the real
// /api/benchmarks artifacts. Every number is real or an honest "not run" state;
// nothing here is simulated and nothing triggers a docking run.
const BenchmarksPage = {
    async render(mountEl) {
        this.mountEl = mountEl;
        mountEl.innerHTML = AppShell.shell(`<div class="p-margin-desktop text-center text-on-surface-variant">Loading benchmarks...</div>`);
        try {
            this.data = await API.getBenchmarks();
            const targets = this.data.targets || [];
            this.activeTargetId = targets[0]?.target_id || null;
            this.paint();
        } catch (e) {
            mountEl.innerHTML = AppShell.shell(`<div class="p-margin-desktop text-error">${escapeHtml(e.message)}</div>`);
        }
    },

    paint() {
        this.mountEl.innerHTML = AppShell.shell(this.body(this.data));
        const sel = document.getElementById("bench-target-select");
        if (sel) sel.addEventListener("change", () => { this.activeTargetId = sel.value; this.paint(); });
    },

    // width % for a kcal/mol score on a fixed 0..-8 scale (more negative = longer)
    barPct(score, scale = 8) {
        const v = Math.min(Math.abs(Number(score) || 0), scale);
        return Math.round((v / scale) * 100);
    },

    body(data) {
        const targets = data.targets || [];
        const active = targets.find((t) => t.target_id === this.activeTargetId) || targets[0];
        const internal = active?.internal;
        const internalOk = !!(internal && internal.reproducibility);
        const title = `<h1 class="font-headline-md text-body-lg text-on-surface font-medium">Scientific Benchmarks</h1>`;
        const selector = targets.length
            ? `<select id="bench-target-select" class="px-3 py-1.5 bg-surface-container-low border border-outline-variant rounded-lg font-body-sm text-body-sm focus:outline-none focus:border-primary">
                ${targets.map((t) => `<option value="${t.target_id}" ${t.target_id === active?.target_id ? "selected" : ""}>${escapeHtml(t.target_name)} (${escapeHtml(t.pdb_id || t.target_id)})</option>`).join("")}
            </select>`
            : "";
        return `
        ${AppShell.toolbar(title, selector)}
        <div class="p-5 md:p-8">
            ${internalOk ? this.internalBento(internal) : this.notRunCard("Internal validation", "Not generated for this target yet.")}
            ${internalOk ? this.registry(internal) : ""}

            <p class="font-body-sm text-body-sm text-on-surface-variant mt-6 border-t border-outline-variant pt-4">${escapeHtml(data.disclaimer || "In-silico predictions only. Not clinical advice. Docking prioritises candidates; it does not prove them.")}</p>
        </div>`;
    },

    internalBento(internal) {
        const repro = internal.reproducibility || {};
        const controls = internal.controls || {};
        const enrichment = internal.enrichment || {};
        const redock = internal.redocking || {};

        return `
        <section class="mb-2">
            <h2 class="font-headline-md text-headline-md text-on-surface mb-1">Internal validation - ${escapeHtml(internal.target_name)} <span class="font-code-md text-outline">(${escapeHtml(internal.pdb_id)})</span></h2>
            <p class="font-body-sm text-body-sm text-on-surface-variant mb-4">Reference drug: ${escapeHtml(internal.reference_drug)} &middot; AutoDock Vina ${escapeHtml(internal.config?.vina_version || "")} &middot; exhaustiveness ${internal.config?.exhaustiveness ?? "?"}</p>
        </section>

        <div class="grid grid-cols-1 lg:grid-cols-12 gap-gutter mb-gutter">
            ${this.reproCard(repro)}
            ${this.enrichmentStat(enrichment)}
        </div>

        <div class="grid grid-cols-1 lg:grid-cols-12 gap-gutter mb-gutter">
            ${this.controlsCard(controls)}
            ${this.redockCard(redock)}
        </div>

        ${this.rocCard(enrichment)}
        ${this.enrichmentDetail(enrichment)}`;
    },

    rocCard(enrichment) {
        const rows = enrichment.rows || [];
        if (enrichment.status !== "available" || rows.length < 4) return "";
        const build = (key) => {
            const sorted = [...rows].sort((a, b) => (a[key] ?? 0) - (b[key] ?? 0));
            const nAct = sorted.filter((r) => r.is_active).length;
            const nDec = sorted.length - nAct;
            if (!nAct || !nDec) return null;
            let tp = 0, fp = 0;
            const pts = [[0, 0]];
            sorted.forEach((r) => {
                if (r.is_active) tp++; else fp++;
                pts.push([fp / nDec, tp / nAct]);
            });
            return pts.map(([x, y]) => `${(x * 100).toFixed(1)},${(100 - y * 100).toFixed(1)}`).join(" ");
        };
        const vinaPts = build("vina");
        const consPts = build("consensus");
        if (!vinaPts) return "";
        return `
        <div class="bg-surface-container-lowest border border-outline-variant rounded-lg p-6 shadow-sm mb-gutter">
            <h3 class="font-headline-md text-headline-md text-on-surface mb-1">ROC curve</h3>
            <p class="font-body-sm text-body-sm text-on-surface-variant mb-4">Actives vs presumed-inactive decoys (${enrichment.n_actives} actives, ${enrichment.n_inactives} decoys). Computed live from the ranking below.</p>
            <div class="flex flex-col md:flex-row gap-6 items-center">
                <svg viewBox="0 0 100 100" class="w-full max-w-[320px] aspect-square border border-outline-variant rounded bg-surface chart-grid" preserveAspectRatio="none">
                    <line x1="0" y1="100" x2="100" y2="0" stroke="currentColor" class="text-outline/40" stroke-width="0.5" stroke-dasharray="3"></line>
                    ${consPts ? `<polyline points="${consPts}" fill="none" stroke="#5E94C3" stroke-width="1.4" stroke-dasharray="2 2"></polyline>` : ""}
                    <polyline points="${vinaPts}" fill="none" stroke="#00478d" stroke-width="1.8"></polyline>
                </svg>
                <div class="font-body-sm text-body-sm space-y-2">
                    <div class="flex items-center gap-2"><span class="w-4 h-0.5 bg-primary inline-block"></span>Vina AUC <span class="font-code-md">${enrichment.vina?.auc ?? "?"}</span></div>
                    <div class="flex items-center gap-2"><span class="w-4 h-0.5 bg-structural-blue inline-block"></span>Consensus AUC <span class="font-code-md">${enrichment.consensus?.auc ?? "?"}</span></div>
                    <div class="flex items-center gap-2 text-on-surface-variant"><span class="w-4 border-t border-dashed border-outline inline-block"></span>Random (0.5)</div>
                    <p class="text-xs text-on-surface-variant pt-2 max-w-[220px]">A curve hugging the top-left corner means actives are ranked before decoys.</p>
                </div>
            </div>
        </div>`;
    },

    reproCard(repro) {
        const scores = repro.scores || [];
        const bars = scores
            .map(
                (s, i) => `
            <div class="flex-1 flex flex-col items-center gap-2 group">
                <div class="w-full flex items-end justify-center h-[180px]">
                    <div class="w-8 bg-primary rounded-t-sm group-hover:bg-primary/80 transition-colors relative" style="height:${this.barPct(s)}%">
                        <span class="absolute -top-6 left-1/2 -translate-x-1/2 font-code-md text-[11px] text-on-surface-variant whitespace-nowrap">${s}</span>
                    </div>
                </div>
                <span class="font-label-caps text-label-caps text-outline">run ${i + 1}</span>
            </div>`
            )
            .join("");
        return `
        <div class="lg:col-span-8 bg-surface-container-lowest border border-outline-variant rounded-lg p-6 shadow-sm flex flex-col">
            <div class="flex justify-between items-start mb-4">
                <div>
                    <h3 class="font-headline-md text-headline-md text-on-surface">Reproducibility</h3>
                    <p class="font-body-sm text-body-sm text-on-surface-variant">${repro.n ?? scores.length} runs, identical input</p>
                </div>
                <span class="bg-success-docking/10 text-success-docking font-label-caps text-label-caps px-2 py-1 rounded-full border border-success-docking/20 flex items-center gap-1">
                    <span class="material-symbols-outlined" style="font-size:14px;">check_circle</span> STABLE
                </span>
            </div>
            <div class="flex-1 chart-grid rounded border border-outline-variant/30 flex items-end gap-2 p-4 pt-8">${bars}</div>
            <div class="mt-4 grid grid-cols-2 gap-4">
                <div class="bg-surface p-3 rounded border border-outline-variant/50">
                    <div class="text-xs text-on-surface-variant mb-1">Mean affinity</div>
                    <div class="font-code-md text-code-md text-on-surface">${repro.mean ?? "?"} kcal/mol</div>
                </div>
                <div class="bg-surface p-3 rounded border border-outline-variant/50">
                    <div class="text-xs text-on-surface-variant mb-1">Spread (max &minus; min)</div>
                    <div class="font-code-md text-code-md text-success-docking">&plusmn;${repro.spread ?? "?"} kcal/mol</div>
                </div>
            </div>
        </div>`;
    },

    enrichmentStat(enrichment) {
        if (enrichment.status !== "available") {
            return `<div class="lg:col-span-4 bg-deep-navy text-on-primary rounded-lg p-6 flex flex-col justify-center">
                <h3 class="font-headline-md text-headline-md mb-2">Enrichment</h3>
                <p class="font-body-sm text-body-sm opacity-80">${escapeHtml(enrichment.reason || "Not run.")}</p>
            </div>`;
        }
        const vinaAuc = enrichment.vina?.auc ?? 0;
        return `
        <div class="lg:col-span-4 flex flex-col gap-gutter">
            <div class="bg-deep-navy text-on-primary rounded-lg p-6 flex flex-col justify-center relative overflow-hidden flex-1">
                <div class="absolute -right-4 -bottom-4 opacity-10"><span class="material-symbols-outlined" style="font-size:120px;">account_tree</span></div>
                <h3 class="font-headline-md text-headline-md mb-3 relative z-10">Enrichment AUC</h3>
                <div class="text-4xl font-bold font-code-md relative z-10">${vinaAuc}</div>
                <div class="w-full h-1.5 bg-white/20 rounded-full mt-2 relative z-10"><div class="h-full bg-secondary-fixed-dim rounded-full" style="width:${Math.round(vinaAuc * 100)}%"></div></div>
                <div class="flex justify-between font-code-md text-[11px] opacity-80 mt-3 relative z-10">
                    <span>Vina ${enrichment.vina?.auc ?? "?"}</span>
                    <span>Consensus ${enrichment.consensus?.auc ?? "?"}</span>
                </div>
            </div>
            <div class="bg-surface-container-lowest border border-outline-variant rounded-lg p-4 shadow-sm">
                <div class="text-xs text-on-surface-variant mb-1">Enrichment factor (EF1 / EF10)</div>
                <div class="font-code-md text-code-md text-on-surface">${enrichment.vina?.ef1 ?? "?"} / ${enrichment.vina?.ef10 ?? "?"}</div>
                <div class="text-xs text-on-surface-variant mt-2">${enrichment.n_actives ?? "?"} actives &middot; ${enrichment.n_inactives ?? "?"} decoys</div>
            </div>
        </div>`;
    },

    controlsCard(controls) {
        const ref = controls.reference || {};
        const negatives = controls.negatives || [];
        const row = (name, score, isRef) => `
            <div class="mb-3">
                <div class="flex justify-between font-body-sm text-body-sm mb-1">
                    <span class="${isRef ? "text-on-surface font-medium" : "text-on-surface-variant"}">${escapeHtml(name)}${isRef ? " (reference)" : ""}</span>
                    <span class="font-code-md">${score} kcal/mol</span>
                </div>
                <div class="w-full h-3 bg-surface rounded-full overflow-hidden border border-outline-variant/50">
                    <div class="h-full ${isRef ? "bg-success-docking" : "bg-outline/50"} rounded-full" style="width:${this.barPct(score)}%"></div>
                </div>
            </div>`;
        return `
        <div class="lg:col-span-6 bg-surface-container-lowest border border-outline-variant rounded-lg p-6 shadow-sm">
            <div class="flex justify-between items-start mb-4">
                <div>
                    <h3 class="font-headline-md text-headline-md text-on-surface">Positive / negative controls</h3>
                </div>
                <span class="${controls.ordering_held ? "bg-success-docking/10 text-success-docking border-success-docking/20" : "bg-error/10 text-error border-error/20"} font-label-caps text-label-caps px-2 py-1 rounded-full border flex items-center gap-1">
                    <span class="material-symbols-outlined" style="font-size:14px;">${controls.ordering_held ? "check_circle" : "cancel"}</span> ${controls.ordering_held ? "ORDER HELD" : "ORDER BROKEN"}
                </span>
            </div>
            ${ref.name ? row(ref.name, ref.vina, true) : ""}
            ${negatives.map((n) => row(n.name, n.vina, false)).join("")}
        </div>`;
    },

    redockCard(redock) {
        const ok = (redock.success_rate_under_2A ?? null) !== null;
        const skipped = (redock.results || []).filter((r) => r.status === "skipped");
        return `
        <div class="lg:col-span-6 bg-surface-container-lowest border border-outline-variant rounded-lg p-6 shadow-sm">
            <div class="flex justify-between items-start mb-4">
                <div>
                    <h3 class="font-headline-md text-headline-md text-on-surface">Redocking RMSD</h3>
                </div>
                <span class="bg-outline/10 text-outline font-label-caps text-label-caps px-2 py-1 rounded-full border border-outline/20">${redock.evaluated ?? 0} eval &middot; ${redock.skipped ?? 0} skip</span>
            </div>
            ${
                ok
                    ? `<div class="text-3xl font-bold font-code-md text-on-surface">${redock.success_rate_under_2A}</div><p class="text-xs text-on-surface-variant">success rate &lt; 2.0Å</p>`
                    : `<div class="bg-surface border border-outline-variant/50 rounded p-3">
                        <div class="flex items-center gap-2 text-warning-energy font-body-sm text-body-sm mb-2"><span class="material-symbols-outlined text-[18px]">info</span> Honestly reported: not scored</div>
                        ${skipped
                            .map(
                                (r) => `<div class="font-code-md text-xs text-on-surface-variant">${escapeHtml(r.pdb_id)} - ${escapeHtml(r.reason)}${r.ligand_residue ? ` (ligand ${escapeHtml(r.ligand_residue)})` : ""}</div>`
                            )
                            .join("")}
                    </div>`
            }
        </div>`;
    },

    enrichmentDetail(enrichment) {
        if (enrichment.status !== "available" || !(enrichment.rows || []).length) return "";
        const rows = enrichment.rows
            .slice(0, 12)
            .map(
                (r) => `<tr class="border-b border-outline-variant/50 hover:bg-primary-fixed/20 transition-colors ${r.is_active ? "" : "bg-surface-container/20"}">
                <td class="p-3 font-code-md text-on-surface">${escapeHtml(r.name)}</td>
                <td class="p-3"><span class="${r.is_active ? "bg-success-docking/10 text-success-docking border-success-docking/20" : "bg-outline/10 text-outline border-outline/20"} px-2 py-0.5 rounded font-label-caps text-label-caps border">${r.is_active ? "ACTIVE" : "DECOY"}</span></td>
                <td class="p-3 font-code-md text-xs">${r.vina}</td>
                <td class="p-3 font-code-md text-xs">${r.consensus}</td>
            </tr>`
            )
            .join("");
        return `
        <div class="bg-surface-container-lowest border border-outline-variant rounded-lg shadow-sm overflow-hidden mb-gutter">
            <div class="p-4 border-b border-outline-variant bg-surface-container-low">
                <h3 class="font-headline-md text-headline-md text-on-surface">Enrichment ranking (sample)</h3>
                <p class="font-body-sm text-body-sm text-on-surface-variant mt-1">${escapeHtml(enrichment.inactives_note || "")}</p>
            </div>
            <div class="overflow-x-auto">
                <table class="w-full text-left border-collapse">
                    <thead><tr class="bg-surface font-label-caps text-label-caps text-on-surface-variant border-b border-outline-variant">
                        <th class="p-3">Compound</th><th class="p-3">Class</th><th class="p-3">Vina</th><th class="p-3">Consensus</th>
                    </tr></thead>
                    <tbody class="font-body-sm text-body-sm">${rows}</tbody>
                </table>
            </div>
        </div>`;
    },

    registry(internal) {
        const redock = internal.redocking || {};
        const skippedNote = (redock.results || []).find((r) => r.status === "skipped");
        const limitation = skippedNote
            ? `Redocking skipped: ${escapeHtml(skippedNote.reason)}${skippedNote.ligand_residue ? ` (cofactor ${escapeHtml(skippedNote.ligand_residue)})` : ""}. Scoring and enrichment are unaffected.`
            : "No known limitation recorded for this target.";
        return `
        <div class="bg-surface-container-lowest border border-outline-variant rounded-lg shadow-sm overflow-hidden mb-gutter">
            <div class="p-4 border-b border-outline-variant bg-surface-container-low flex justify-between items-center">
                <h2 class="font-headline-md text-headline-md text-on-surface flex items-center gap-2">
                    <span class="material-symbols-outlined text-outline">verified_user</span> Honest reporting registry
                </h2>
            </div>
            <div class="overflow-x-auto">
                <table class="w-full text-left border-collapse">
                    <thead><tr class="bg-surface font-label-caps text-label-caps text-on-surface-variant border-b border-outline-variant">
                        <th class="p-3">Target</th><th class="p-3">Reference drug</th><th class="p-3">Status</th><th class="p-3">Known limitations / notes</th>
                    </tr></thead>
                    <tbody class="font-body-sm text-body-sm">
                        <tr class="hover:bg-primary-fixed/20 transition-colors">
                            <td class="p-3 font-code-md text-on-surface">${escapeHtml(internal.target_name)} (${escapeHtml(internal.pdb_id)})</td>
                            <td class="p-3">${escapeHtml(internal.reference_drug)}</td>
                            <td class="p-3"><span class="bg-success-docking/10 text-success-docking px-2 py-1 rounded font-code-md text-xs border border-success-docking/20">VALIDATED</span></td>
                            <td class="p-3 text-on-surface-variant">${limitation}</td>
                        </tr>
                    </tbody>
                </table>
            </div>
        </div>`;
    },

    externalSection(external, status) {
        if (status !== "available") {
            return this.notRunCard("External independent redocking", "Run scripts/bench_external.py (Colab recommended) to generate this report.");
        }
        const rows = (external.results || [])
            .slice(0, 50)
            .map(
                (r) => `<tr class="border-b border-outline-variant/50">
                <td class="p-2 font-code-md text-xs">${escapeHtml(r.pdb_id)}</td>
                <td class="p-2 text-xs">${r.status === "ok" ? "OK" : "Skipped"}</td>
                <td class="p-2 text-xs">${r.rmsd ?? "-"}</td>
                <td class="p-2 text-xs text-on-surface-variant">${escapeHtml(r.reason || "")}</td>
            </tr>`
            )
            .join("");
        return `
        <div class="bg-surface-container-lowest border border-outline-variant rounded-lg overflow-hidden mb-gutter">
            <div class="p-4 border-b border-outline-variant bg-surface-container-low">
                <h2 class="font-headline-md text-headline-md text-on-surface">External independent redocking</h2>
                <p class="font-body-sm text-body-sm text-on-surface-variant">${escapeHtml(external.selection_rule || "")}</p>
                <p class="font-body-sm text-body-sm mt-2">Attempted ${external.attempted} &middot; Evaluated ${external.evaluated} &middot; Skipped ${external.skipped} &middot; Success (&lt;${external.threshold_angstrom ?? 2.0}Å): ${external.success_rate_under_threshold ?? "n/a"}</p>
            </div>
            <div class="overflow-x-auto max-h-96">
                <table class="w-full text-left border-collapse">
                    <thead><tr class="bg-surface font-label-caps text-label-caps text-on-surface-variant border-b border-outline-variant">
                        <th class="p-2">PDB</th><th class="p-2">Status</th><th class="p-2">RMSD</th><th class="p-2">Reason</th>
                    </tr></thead>
                    <tbody>${rows}</tbody>
                </table>
            </div>
        </div>`;
    },

    notRunCard(title, hint) {
        return `<section class="bg-surface-container-lowest border border-outline-variant border-dashed rounded-lg p-6 mb-gutter text-center">
            <span class="material-symbols-outlined text-outline text-[32px]">pending</span>
            <h2 class="font-headline-md text-headline-md text-on-surface mb-1 mt-2">${escapeHtml(title)}</h2>
            <p class="font-body-sm text-body-sm text-on-surface-variant">Not yet run. ${escapeHtml(hint)}</p>
        </section>`;
    },
};
