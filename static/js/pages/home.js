// Landing page. Design lifted from stitch_drugforge_molecular_docking_lab/drugforge_home.
const HomePage = {
    render(mountEl) {
        mountEl.innerHTML = Layout.shell(`
        <section class="w-full max-w-max-width px-margin-mobile md:px-margin-desktop py-16 md:py-24 flex flex-col items-center text-center relative overflow-hidden mx-auto">
            <div class="absolute inset-0 opacity-10 pointer-events-none z-0" style="background-image:radial-gradient(#00478d 1px, transparent 1px);background-size:24px 24px;"></div>
            <div class="z-10 max-w-3xl space-y-6">
                <h1 class="font-headline-xl text-headline-xl text-on-surface leading-tight">
                    Forge better leads for <span class="text-primary">neglected diseases.</span>
                </h1>
                <p class="font-body-lg text-body-lg text-on-surface-variant max-w-2xl mx-auto">
                    Real AutoDock Vina docking, consensus rescoring, ADMET filtering and grounded
                    AI explanation &mdash; run against validated targets for malaria, Chagas disease,
                    leishmaniasis and sleeping sickness. Every score is in-silico and requires lab validation.
                </p>
                <div class="flex flex-col sm:flex-row gap-4 justify-center pt-4">
                    <a data-link href="/lab" class="bg-primary text-on-primary font-body-md text-body-md px-6 py-3 rounded-lg hover:bg-deep-navy transition-colors font-medium flex items-center justify-center gap-2 shadow-sm">
                        Start Docking <span class="material-symbols-outlined">arrow_forward</span>
                    </a>
                    <a data-link href="/library" class="bg-surface-container-lowest text-primary border border-primary font-body-md text-body-md px-6 py-3 rounded-lg hover:bg-surface-container-low transition-colors font-medium flex items-center justify-center gap-2">
                        Explore the Library <span class="material-symbols-outlined">auto_stories</span>
                    </a>
                </div>
            </div>
        </section>

        <section class="w-full px-margin-mobile md:px-margin-desktop py-16 bg-surface-container-low">
            <div class="max-w-max-width mx-auto">
                <div class="mb-12 text-center max-w-2xl mx-auto">
                    <h2 class="font-headline-lg text-headline-lg text-on-surface mb-4">A complete pipeline, running for real.</h2>
                    <p class="font-body-md text-body-md text-on-surface-variant">From a SMILES string to a validated docking pose, ADMET filter and AI-grounded explanation.</p>
                </div>
                <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
                    <div class="bg-surface-container-lowest rounded-xl border border-outline-variant p-6 flex flex-col gap-4 shadow-sm">
                        <div class="w-12 h-12 bg-primary-fixed/20 rounded-lg flex items-center justify-center text-primary">
                            <span class="material-symbols-outlined" style="font-variation-settings:'FILL' 1;">bolt</span>
                        </div>
                        <h3 class="font-headline-md text-headline-md text-on-surface">Real Vina Docking</h3>
                        <p class="font-body-md text-body-md text-on-surface-variant">AutoDock Vina and Vinardo rescoring, consensus-ranked, compared against the target's reference drug.</p>
                    </div>
                    <div class="bg-surface-container-lowest rounded-xl border border-outline-variant p-6 flex flex-col gap-4 shadow-sm">
                        <div class="w-12 h-12 bg-molecular-green/10 rounded-lg flex items-center justify-center text-molecular-green">
                            <span class="material-symbols-outlined" style="font-variation-settings:'FILL' 1;">local_florist</span>
                        </div>
                        <h3 class="font-headline-md text-headline-md text-on-surface">Ethnobotanical Library</h3>
                        <p class="font-body-md text-body-md text-on-surface-variant">Curated African medicinal-plant compounds, each cited to its traditional use and source.</p>
                    </div>
                    <div class="bg-surface-container-lowest rounded-xl border border-outline-variant p-6 flex flex-col gap-4 shadow-sm">
                        <div class="w-12 h-12 bg-structural-blue/10 rounded-lg flex items-center justify-center text-structural-blue">
                            <span class="material-symbols-outlined" style="font-variation-settings:'FILL' 1;">biotech</span>
                        </div>
                        <h3 class="font-headline-md text-headline-md text-on-surface">AI Confirmation</h3>
                        <p class="font-body-md text-body-md text-on-surface-variant">Optional Boltz-2 binding confirmation and a DeepSeek explanation grounded only in the computed data.</p>
                    </div>
                </div>
            </div>
        </section>
        `);
    },
};
