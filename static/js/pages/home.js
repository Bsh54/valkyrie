// Landing page. Grove-inspired clinical light direction: serif display headlines,
// mono eyebrow labels, alternating white/mist sections, soft elevated cards,
// molecular imagery, medical-blue accent used sparingly. Honest wording only.
const HomePage = {
    render(mountEl) {
        mountEl.innerHTML = Layout.shell(`
        ${this.hero()}
        ${this.heritage()}
        ${this.statStrip()}
        ${this.howItWorks()}
        ${this.features()}
        ${this.honesty()}
        `);
        requestAnimationFrame(() => this.initViewer());
    },

    initViewer() {
        if (typeof $3Dmol === "undefined") return;
        const el = document.getElementById("hero-viewer");
        if (!el) return;
        try {
            const viewer = $3Dmol.createViewer(el, { backgroundColor: "#f7f9fb" });
            $3Dmol.download("pdb:1J3I", viewer, {}, () => {
                const fb = document.getElementById("hero-viewer-fallback");
                if (fb) fb.remove();
                viewer.setStyle({}, { cartoon: { color: "spectrum" } });
                viewer.addStyle({ hetflag: true }, { stick: { colorscheme: "Jmol", radius: 0.25 } });
                viewer.zoomTo();
                viewer.spin("y", 0.5);
                viewer.render();
            });
        } catch (e) {
            /* keep the fallback label */
        }
    },

    hero() {
        return `
        <section class="w-full max-w-max-width mx-auto px-margin-mobile md:px-margin-desktop py-16 md:py-24 flex flex-col items-center text-center relative overflow-hidden">
            <div class="absolute inset-0 opacity-[0.07] pointer-events-none z-0" style="background-image:radial-gradient(#00478d 1px, transparent 1px);background-size:26px 26px;"></div>
            <div class="z-10 max-w-3xl space-y-7">
                <h1 class="font-display text-[40px] md:text-[64px] leading-[1.05] text-on-surface tracking-tight">
                    Find medicines for the diseases <span class="text-primary italic">the world forgot.</span>
                </h1>
                <p class="font-body-lg text-body-lg text-on-surface-variant max-w-2xl mx-auto">
                    Africa has healed with its plants for generations. Valkyrie gives that knowledge the
                    molecular proof modern science asks for, screening real compounds against malaria,
                    Chagas, leishmaniasis and sleeping sickness. Every score is in-silico, validated in the lab.
                </p>
                <div class="flex flex-col sm:flex-row gap-4 justify-center pt-2">
                    <a data-link href="/lab" class="bg-primary text-on-primary font-body-md text-body-md px-6 py-3 rounded-xl hover:bg-deep-navy transition-colors font-medium flex items-center justify-center gap-2 shadow-card">
                        Start Docking <span class="material-symbols-outlined">arrow_forward</span>
                    </a>
                    <a data-link href="/library" class="bg-surface-container-lowest text-on-surface border border-outline-variant font-body-md text-body-md px-6 py-3 rounded-xl hover:bg-surface-container-low transition-colors font-medium flex items-center justify-center gap-2">
                        Explore the Library <span class="material-symbols-outlined">auto_stories</span>
                    </a>
                </div>
            </div>
            <div class="w-full mt-16 z-10">${this.preview()}</div>
        </section>`;
    },

    preview() {
        return `
        <div class="bg-surface-container-lowest rounded-2xl border border-outline-variant p-2 shadow-card mx-auto max-w-5xl">
            <div class="bg-surface-container-low rounded-t-xl px-4 py-2 flex items-center gap-2 border-b border-outline-variant">
                <div class="flex gap-1.5">
                    <span class="w-3 h-3 rounded-full bg-error/60"></span>
                    <span class="w-3 h-3 rounded-full bg-warning-energy/60"></span>
                    <span class="w-3 h-3 rounded-full bg-success-docking/60"></span>
                </div>
                <div class="flex-1 mx-4 bg-surface rounded px-3 py-1 font-code-md text-[11px] text-outline text-left truncate">valkyrie / lab / PfDHFR (1J3I)</div>
            </div>
            <div class="grid grid-cols-12 gap-2 p-3 bg-surface rounded-b-xl text-left">
                <div class="hidden md:flex col-span-2 flex-col gap-2">
                    ${["Targets", "Parameters", "Consensus", "ADMET", "Report"].map((s, i) => `<div class="px-2 py-1.5 rounded-lg ${i === 0 ? "bg-primary/10 text-primary" : "text-on-surface-variant"} font-label-caps text-label-caps">${s}</div>`).join("")}
                </div>
                <div id="hero-viewer" class="col-span-12 md:col-span-7 rounded-xl border border-outline-variant relative overflow-hidden bg-surface" style="position:relative;height:300px;">
                    <div id="hero-viewer-fallback" class="absolute inset-0 flex items-center justify-center text-outline font-code-md text-xs pointer-events-none">Loading PfDHFR structure (PDB 1J3I)...</div>
                    <span class="absolute bottom-2 left-2 z-10 font-label-caps text-label-caps text-primary bg-surface/85 px-2 py-1 rounded border border-outline-variant">PfDHFR &middot; malaria target &middot; live 3D</span>
                </div>
                <div class="col-span-12 md:col-span-3 flex flex-col gap-2">
                    <div class="bg-surface-container-lowest border border-outline-variant rounded-xl p-3">
                        <div class="text-[11px] text-on-surface-variant">Best pose</div>
                        <div class="font-code-md text-2xl text-success-docking">-5.56</div>
                        <div class="text-[11px] text-on-surface-variant">kcal/mol vs pyrimethamine</div>
                    </div>
                    <div class="bg-surface-container-lowest border border-outline-variant rounded-xl p-3 space-y-1.5">
                        ${[["Lipinski", "Pass"], ["Veber", "Pass"], ["PAINS", "Clean"]].map(([k, v]) => `<div class="flex justify-between items-center"><span class="text-[11px] text-on-surface-variant">${k}</span><span class="bg-success-docking/10 text-success-docking px-1.5 rounded font-label-caps text-label-caps border border-success-docking/20">${v}</span></div>`).join("")}
                    </div>
                </div>
            </div>
        </div>`;
    },

    statStrip() {
        const stats = [
            ["4", "disease targets"],
            ["Vina 1.2.7", "real docking engine"],
            ["5-stage", "screening funnel"],
            ["CC-BY", "open data"],
        ];
        return `
        <section class="w-full border-y border-outline-variant bg-surface-container-lowest">
            <div class="max-w-max-width mx-auto px-margin-mobile md:px-margin-desktop py-6 grid grid-cols-2 md:grid-cols-4 gap-6">
                ${stats
                    .map(
                        ([n, l]) => `<div class="text-center">
                            <div class="font-code-md text-headline-md text-primary">${n}</div>
                            <div class="font-label-caps text-label-caps text-on-surface-variant uppercase mt-1">${l}</div>
                        </div>`
                    )
                    .join("")}
            </div>
        </section>`;
    },

    howItWorks() {
        const steps = [
            ["labs", "Dock", "AutoDock Vina places your molecule in the target's binding pocket and scores it."],
            ["stacked_line_chart", "Rescore", "Vinardo consensus rescoring re-ranks the top poses for a steadier verdict."],
            ["smart_toy", "Explain", "A grounded, plain-language read of the result, from the computed data."],
            ["filter_alt", "Filter", "ADMET and toxicity alerts decide what earns the word hit."],
        ];
        return `
        <section class="w-full bg-surface-container-low">
            <div class="max-w-max-width mx-auto px-margin-mobile md:px-margin-desktop py-16 md:py-24">
                <div class="text-center max-w-2xl mx-auto mb-12">
                    <h2 class="font-display text-[32px] md:text-[44px] leading-tight text-on-surface">From a molecule to a prioritised lead.</h2>
                    <p class="font-body-md text-body-md text-on-surface-variant mt-3">One transparent pipeline, identical for every disease target. Nothing simulated.</p>
                </div>
                <div class="grid grid-cols-1 md:grid-cols-4 gap-5">
                    ${steps
                        .map(
                            ([icon, title, text], i) => `
                        <div class="bg-surface-container-lowest rounded-2xl border border-outline-variant p-6 shadow-card relative">
                            <div class="font-code-md text-label-caps text-outline mb-4">0${i + 1}</div>
                            <div class="w-11 h-11 bg-primary/10 rounded-xl flex items-center justify-center text-primary mb-4">
                                <span class="material-symbols-outlined" style="font-variation-settings:'FILL' 1;">${icon}</span>
                            </div>
                            <h3 class="font-headline-md text-headline-md text-on-surface mb-2">${title}</h3>
                            <p class="font-body-sm text-body-sm text-on-surface-variant">${text}</p>
                        </div>`
                        )
                        .join("")}
                </div>
            </div>
        </section>`;
    },

    features() {
        const cards = [
            ["bolt", "Real AutoDock Vina", "Docking with Vinardo consensus rescoring, ranked and compared against each target's reference drug. Run on the server, never simulated."],
            ["local_florist", "Ethnobotanical library", "Curated African medicinal-plant compounds, each cited to its traditional use, region, people and preparation method."],
            ["verified_user", "Honest benchmarks", "Reproducibility, positive and negative controls, enrichment AUC, and every skipped case reported in the open."],
        ];
        return `
        <section class="w-full">
            <div class="max-w-max-width mx-auto px-margin-mobile md:px-margin-desktop py-16 md:py-24">
                <div class="max-w-2xl mb-12">
                    <h2 class="font-display text-[32px] md:text-[44px] leading-tight text-on-surface">A complete pipeline, running for real.</h2>
                </div>
                <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
                    ${cards
                        .map(
                            ([icon, title, text]) => `
                        <div class="bg-surface-container-lowest rounded-2xl border border-outline-variant p-7 shadow-card flex flex-col gap-4">
                            <div class="w-12 h-12 bg-primary/10 rounded-xl flex items-center justify-center text-primary">
                                <span class="material-symbols-outlined" style="font-variation-settings:'FILL' 1;">${icon}</span>
                            </div>
                            <h3 class="font-headline-md text-headline-md text-on-surface">${title}</h3>
                            <p class="font-body-md text-body-md text-on-surface-variant">${text}</p>
                        </div>`
                        )
                        .join("")}
                </div>
            </div>
        </section>`;
    },

    heritage() {
        return `
        <section class="w-full bg-deep-navy text-on-primary">
            <div class="max-w-max-width mx-auto px-margin-mobile md:px-margin-desktop py-16 md:py-24 flex flex-col lg:flex-row items-center gap-12">
                <div class="flex-1 space-y-5">
                    <h2 class="font-display text-[32px] md:text-[46px] leading-tight">Traditional knowledge, molecular proof.</h2>
                    <p class="font-body-lg text-body-lg text-primary-fixed-dim/90 max-w-xl">
                        For generations, West African medicine has treated malaria with plants like
                        Cryptolepis sanguinolenta. Valkyrie screens those compounds against validated
                        disease targets, giving traditional knowledge a modern, cited, in-silico check.
                    </p>
                    <a data-link href="/library" class="inline-flex items-center gap-2 bg-surface-container-lowest text-primary font-body-md text-body-md px-6 py-3 rounded-xl hover:bg-surface-container-low transition-colors font-medium mt-2">
                        Explore the library <span class="material-symbols-outlined">arrow_forward</span>
                    </a>
                </div>
                <div class="flex-1 w-full grid grid-cols-2 gap-4">
                    ${[["potted_plant", "Cryptolepis sanguinolenta", "Nibima, Ghana"], ["local_florist", "Artemisia annua", "Sweet wormwood"], ["eco", "Root decoction", "Aqueous preparation"], ["science", "Cryptolepine", "Active compound"]]
                        .map(
                            ([icon, name, sub]) => `
                        <div class="bg-white/5 border border-white/10 rounded-2xl p-5 flex flex-col gap-2">
                            <span class="material-symbols-outlined text-primary-fixed-dim" style="font-size:34px;font-variation-settings:'FILL' 1;">${icon}</span>
                            <div class="font-headline-md text-body-lg italic leading-tight">${name}</div>
                            <div class="font-label-caps text-label-caps text-primary-fixed-dim/80 uppercase">${sub}</div>
                        </div>`
                        )
                        .join("")}
                </div>
            </div>
        </section>`;
    },

    honesty() {
        return `
        <section class="w-full">
            <div class="max-w-max-width mx-auto px-margin-mobile md:px-margin-desktop py-16 text-center">
                <span class="material-symbols-outlined text-primary text-[36px]" style="font-variation-settings:'FILL' 1;">balance</span>
                <h2 class="font-display text-[28px] md:text-[38px] leading-tight text-on-surface mt-4 max-w-2xl mx-auto">Honest by design.</h2>
                <p class="font-body-md text-body-md text-on-surface-variant mt-3 max-w-2xl mx-auto">
                    Valkyrie prioritises candidate molecules. It does not discover or prove drugs, and it
                    never gives clinical advice. Docking is the first step of many, and every result waits
                    for the laboratory.
                </p>
                <div class="flex flex-col sm:flex-row gap-4 justify-center mt-8">
                    <a data-link href="/lab" class="bg-primary text-on-primary font-body-md text-body-md px-6 py-3 rounded-xl hover:bg-deep-navy transition-colors font-medium">Start Docking</a>
                    <a data-link href="/benchmarks" class="bg-surface-container-lowest text-on-surface border border-outline-variant font-body-md text-body-md px-6 py-3 rounded-xl hover:bg-surface-container-low transition-colors font-medium">See the benchmarks</a>
                </div>
            </div>
        </section>`;
    },
};
