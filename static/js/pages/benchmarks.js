// Benchmarks. Layout lifted from stitch_drugforge_molecular_docking_lab/drugforge_benchmarks.
// Serves offline-generated artifacts only; nothing here triggers a docking run.
const BenchmarksPage = {
    async render(mountEl) {
        this.mountEl = mountEl;
        mountEl.innerHTML = Layout.shell(`<div class="p-margin-desktop text-center text-on-surface-variant">Loading benchmarks...</div>`);
        try {
            const data = await API.getBenchmarks();
            mountEl.innerHTML = Layout.shell(this.body(data));
        } catch (e) {
            mountEl.innerHTML = Layout.shell(`<div class="p-margin-desktop text-error">${escapeHtml(e.message)}</div>`);
        }
    },

    body(data) {
        return `
        <div class="max-w-max-width mx-auto w-full px-margin-mobile md:px-margin-desktop py-8">
            <header class="mb-8">
                <h1 class="font-headline-xl text-headline-xl text-primary mb-2">Scientific Benchmarks</h1>
                <p class="font-body-lg text-body-lg text-on-surface-variant max-w-3xl">${escapeHtml(data.scope_statement)}</p>
            </header>

            ${this.internalSection(data.internal, data.internal_status)}
            ${this.externalSection(data.external, data.external_status)}

            <p class="font-body-sm text-body-sm text-on-surface-variant mt-6">${escapeHtml(data.disclaimer)}</p>
        </div>`;
    },

    internalSection(internal, status) {
        if (status !== "available") {
            return this.notRunCard("Internal validation", "Run scripts/bench_internal.py to generate this report.");
        }

        const redocking = internal.redocking || {};
        const reproducibility = internal.reproducibility || {};
        const controls = internal.controls || {};
        const enrichment = internal.enrichment || {};

        return `
        <section class="bg-surface-container-lowest border border-outline-variant rounded-lg p-6 mb-gutter">
            <h2 class="font-headline-md text-headline-md text-on-surface mb-1">Internal validation &mdash; ${escapeHtml(internal.target_name)} (${escapeHtml(internal.pdb_id)})</h2>
            <p class="font-body-sm text-body-sm text-on-surface-variant mb-4">Reference: ${escapeHtml(internal.reference_drug)} &middot; exhaustiveness ${internal.config?.exhaustiveness}</p>

            <div class="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
                <div class="bg-surface p-3 rounded border border-outline-variant/50">
                    <div class="text-xs text-on-surface-variant mb-1">Redocking</div>
                    <div class="font-code-md text-code-md">${redocking.evaluated ?? 0} evaluated, ${redocking.skipped ?? 0} skipped</div>
                </div>
                <div class="bg-surface p-3 rounded border border-outline-variant/50">
                    <div class="text-xs text-on-surface-variant mb-1">Reproducibility spread</div>
                    <div class="font-code-md text-code-md">&plusmn;${reproducibility.spread ?? "?"} kcal/mol (n=${reproducibility.n ?? "?"})</div>
                </div>
                <div class="bg-surface p-3 rounded border border-outline-variant/50">
                    <div class="text-xs text-on-surface-variant mb-1">Controls ordering held</div>
                    <div class="font-code-md text-code-md ${controls.ordering_held ? "text-success-docking" : "text-error"}">${controls.ordering_held === null || controls.ordering_held === undefined ? "n/a" : controls.ordering_held}</div>
                </div>
            </div>

            ${
                enrichment.status === "available"
                    ? `<div class="grid grid-cols-2 gap-4">
                        <div class="bg-surface p-3 rounded border border-outline-variant/50">
                            <div class="text-xs text-on-surface-variant mb-1">Vina AUC</div>
                            <div class="font-code-md text-code-md">${enrichment.vina?.auc ?? "?"}</div>
                        </div>
                        <div class="bg-surface p-3 rounded border border-outline-variant/50">
                            <div class="text-xs text-on-surface-variant mb-1">Consensus AUC</div>
                            <div class="font-code-md text-code-md">${enrichment.consensus?.auc ?? "?"}</div>
                        </div>
                    </div>
                    <p class="text-xs text-on-surface-variant mt-2">Consensus improves ranking: ${enrichment.consensus_improves === null ? "n/a" : enrichment.consensus_improves}</p>`
                    : `<p class="text-sm text-on-surface-variant">Enrichment: ${escapeHtml(enrichment.reason || "not run")}</p>`
            }
        </section>`;
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
                <td class="p-2 text-xs">${r.rmsd ?? "&mdash;"}</td>
                <td class="p-2 text-xs text-on-surface-variant">${escapeHtml(r.reason || "")}</td>
            </tr>`
            )
            .join("");

        return `
        <section class="bg-surface-container-lowest border border-outline-variant rounded-lg overflow-hidden mb-gutter">
            <div class="p-4 border-b border-outline-variant bg-surface-container-low">
                <h2 class="font-headline-md text-headline-md text-on-surface">External independent redocking</h2>
                <p class="font-body-sm text-body-sm text-on-surface-variant">${escapeHtml(external.selection_rule || "")}</p>
                <p class="font-body-sm text-body-sm mt-2">
                    Attempted ${external.attempted} &middot; Evaluated ${external.evaluated} &middot; Skipped ${external.skipped} &middot;
                    Success rate (&lt;${external.threshold_angstrom ?? 2.0}&Aring;): ${external.success_rate_under_threshold ?? "n/a"}
                </p>
            </div>
            <div class="overflow-x-auto max-h-96">
                <table class="w-full text-left border-collapse">
                    <thead><tr class="bg-surface font-label-caps text-label-caps text-on-surface-variant border-b border-outline-variant">
                        <th class="p-2">PDB</th><th class="p-2">Status</th><th class="p-2">RMSD</th><th class="p-2">Reason</th>
                    </tr></thead>
                    <tbody>${rows}</tbody>
                </table>
            </div>
        </section>`;
    },

    notRunCard(title, hint) {
        return `<section class="bg-surface-container-lowest border border-outline-variant rounded-lg p-6 mb-gutter">
            <h2 class="font-headline-md text-headline-md text-on-surface mb-1">${escapeHtml(title)}</h2>
            <p class="font-body-sm text-body-sm text-on-surface-variant">Not yet run. ${escapeHtml(hint)}</p>
        </section>`;
    },
};
