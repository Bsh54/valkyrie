// Ethnobotanical library. Layout lifted from
// stitch_drugforge_molecular_docking_lab/drugforge_ethnobotanical_library.
const LibraryPage = {
    state: { compounds: [], query: "", diseaseFilter: "", error: null },

    async render(mountEl) {
        this.mountEl = mountEl;
        try {
            this.state.compounds = await API.getCompounds();
        } catch (e) {
            this.state.error = e.message;
        }
        this.paint();
    },

    paint() {
        this.mountEl.innerHTML = Layout.shell(this.body());
        this.wireEvents();
    },

    wireEvents() {
        const search = document.getElementById("library-search");
        if (search) {
            search.addEventListener("input", () => {
                this.state.query = search.value;
                this.updateGrid();
            });
        }
        const filter = document.getElementById("disease-filter");
        if (filter) {
            filter.addEventListener("change", () => {
                this.state.diseaseFilter = filter.value;
                this.updateGrid();
            });
        }
        document.querySelectorAll("[data-dock-smiles]").forEach((el) => {
            el.addEventListener("click", () => {
                sessionStorage.setItem("drugforge:prefill", el.dataset.dockSmiles);
                Router.navigate("/lab");
            });
        });
    },

    updateGrid() {
        const grid = document.getElementById("library-grid");
        if (grid) grid.outerHTML = this.grid();
        this.wireEvents();
    },

    filtered() {
        const q = this.state.query.toLowerCase();
        return this.state.compounds.filter((c) => {
            const matchesQuery =
                !q ||
                c.compound_name.toLowerCase().includes(q) ||
                c.plant.scientific_name.toLowerCase().includes(q) ||
                c.plant.local_name.toLowerCase().includes(q);
            const matchesDisease =
                !this.state.diseaseFilter ||
                c.traditional_use.disease.toLowerCase().includes(this.state.diseaseFilter);
            return matchesQuery && matchesDisease;
        });
    },

    body() {
        return `
        <div class="max-w-max-width mx-auto w-full px-margin-mobile md:px-margin-desktop py-8 flex flex-col gap-8">
            <section class="bg-surface-container-lowest border border-outline-variant rounded-xl p-6 md:p-8">
                <span class="inline-block bg-primary-container/10 text-primary px-3 py-1 rounded-full font-label-caps text-label-caps uppercase mb-3">Ethnobotanical Library</span>
                <h1 class="font-headline-lg text-headline-lg text-on-surface mb-2">Traditional knowledge, in-silico validation.</h1>
                <p class="font-body-md text-body-md text-on-surface-variant max-w-2xl">
                    Curated African medicinal-plant compounds, each cited to its traditional use, region and
                    preparation. Dock any compound directly against a target.
                </p>
            </section>

            <section class="bg-surface-container-lowest border border-outline-variant rounded-lg p-4 flex flex-col md:flex-row gap-4 items-center sticky top-16 z-40">
                <input id="library-search" type="text" placeholder="Search by plant, local name or compound..."
                    class="flex-1 w-full px-4 py-2 bg-surface-container-low border border-outline-variant rounded-lg font-body-md text-body-md focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary" />
                <select id="disease-filter" class="w-full md:w-56 px-4 py-2 bg-surface-container-low border border-outline-variant rounded-lg font-body-md text-body-md">
                    <option value="">All diseases</option>
                    <option value="malaria">Malaria</option>
                    <option value="fever">Fever</option>
                </select>
            </section>

            ${this.state.error ? `<div class="p-3 bg-error-container text-on-error-container rounded font-body-sm text-body-sm">${escapeHtml(this.state.error)}</div>` : ""}

            ${this.grid()}
        </div>`;
    },

    grid() {
        const items = this.filtered();
        if (!items.length) {
            return `<div id="library-grid" class="text-center py-12 text-on-surface-variant">No compounds match your search.</div>`;
        }
        return `<section id="library-grid" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            ${items.map((c) => this.card(c)).join("")}
        </section>`;
    },

    card(c) {
        return `
        <div class="bg-surface-container-lowest border border-outline-variant rounded-lg overflow-hidden flex flex-col hover:shadow-[0px_8px_24px_rgba(0,0,0,0.08)] transition-shadow">
            <div class="p-4 flex-1 flex flex-col gap-2">
                <div class="flex justify-between items-start">
                    <div>
                        <h3 class="font-headline-md text-headline-md text-on-surface italic">${escapeHtml(c.plant.scientific_name)}</h3>
                        <p class="font-body-sm text-body-sm text-on-surface-variant">${escapeHtml(c.plant.local_name)}</p>
                    </div>
                    <span class="bg-molecular-green/10 text-molecular-green px-2 py-1 rounded font-label-caps text-label-caps border border-molecular-green/20 shrink-0">${escapeHtml(c.traditional_use.disease)}</span>
                </div>
                <div class="mt-2 space-y-1.5">
                    <div class="flex items-center gap-2 text-body-sm font-body-sm text-on-surface-variant">
                        <span class="material-symbols-outlined text-[16px]">public</span><span>${escapeHtml(c.traditional_use.region)}</span>
                    </div>
                    <div class="flex items-center gap-2 text-body-sm font-body-sm text-on-surface-variant">
                        <span class="material-symbols-outlined text-[16px]">groups</span><span>${escapeHtml(c.traditional_use.people)}</span>
                    </div>
                    <div class="flex items-center gap-2 text-body-sm font-body-sm text-on-surface-variant">
                        <span class="material-symbols-outlined text-[16px]">science</span><span>${escapeHtml(c.compound_name)} (active)</span>
                    </div>
                    <div class="flex items-center gap-2 text-body-sm font-body-sm text-on-surface-variant">
                        <span class="material-symbols-outlined text-[16px]">water_drop</span><span>${escapeHtml(c.traditional_use.preparation)}</span>
                    </div>
                </div>
                <p class="text-xs text-on-surface-variant mt-2 border-t border-outline-variant pt-2">${escapeHtml(c.source)}</p>
                <div class="mt-auto pt-4 flex gap-2">
                    <button data-dock-smiles="${escapeHtml(c.smiles)}" class="flex-1 bg-primary text-on-primary font-body-sm text-body-sm px-4 py-2 rounded flex items-center justify-center gap-2 hover:bg-deep-navy transition-colors">
                        <span class="material-symbols-outlined text-[18px]">biotech</span> Dock this compound
                    </button>
                </div>
            </div>
        </div>`;
    },
};
