// Ethnobotanical library. Visual style from
// stitch_valkyrie_molecular_docking_lab/valkyrie_ethnobotanical_library,
// wired to real /api/compounds data. No stock photos, no simulated entries.
const LibraryPage = {
    state: { compounds: [], query: "", diseaseFilter: "", error: null },

    images: {
        cryptolepine: "https://upload.wikimedia.org/wikipedia/commons/thumb/e/e9/COI00077101_-_Cryptolepis_sanguinolenta_-_Welwitsch%2C_Friedrich_-_5993.jpg/500px-COI00077101_-_Cryptolepis_sanguinolenta_-_Welwitsch%2C_Friedrich_-_5993.jpg",
        artemisinin: "https://upload.wikimedia.org/wikipedia/commons/thumb/d/db/Artemisia_annua.jpeg/500px-Artemisia_annua.jpeg",
        "khaya-limonoid": "https://upload.wikimedia.org/wikipedia/commons/thumb/a/a8/Jeune_ca%C3%AFlc%C3%A9drat.jpg/500px-Jeune_ca%C3%AFlc%C3%A9drat.jpg",
        reserpine: "https://upload.wikimedia.org/wikipedia/commons/thumb/5/5f/Rauvolfia_vomitoria-Jardin_botanique_Meise_%284%29.jpg/500px-Rauvolfia_vomitoria-Jardin_botanique_Meise_%284%29.jpg",
        strictosamide: "https://upload.wikimedia.org/wikipedia/commons/thumb/4/49/Nauclea_latifolia_.jpg/500px-Nauclea_latifolia_.jpg",
        harmine: "https://upload.wikimedia.org/wikipedia/commons/thumb/7/7c/Peganum_harmala_MHNT.BOT.2015.34.29.jpg/500px-Peganum_harmala_MHNT.BOT.2015.34.29.jpg",
        thymoquinone: "https://upload.wikimedia.org/wikipedia/commons/thumb/8/89/Nigella_sativa_MHNT.BOT.2015.34.22.jpg/500px-Nigella_sativa_MHNT.BOT.2015.34.22.jpg",
        lapachol: "https://commons.wikimedia.org/wiki/Special:FilePath/Handroanthus_impetiginosus.jpg?width=500",
    },

    async render(mountEl) {
        this.mountEl = mountEl;
        try {
            this.state.compounds = await API.getCompounds();
        } catch (e) {
            this.state.error = e.message;
        }
        this.paint();
        if (!sessionStorage.getItem("valkyrie:tour-library") && !this.state.error) {
            sessionStorage.setItem("valkyrie:tour-library", "1");
            requestAnimationFrame(() => this.startTour());
        }
    },

    // Interactive walkthrough of the library, launched from the Guide button and
    // once automatically per session.
    startTour() {
        Tour.start([
            {
                title: "The plant library",
                text: "This is the collection of traditional medicinal plants Valkyrie can screen. Every entry is real and cited.",
            },
            {
                selector: "#library-search",
                title: "Search",
                text: "Look up a plant by its botanical name, its local name, the active compound, or even a SMILES string.",
            },
            {
                selector: "#disease-filter",
                title: "Filter by disease",
                text: "Narrow the list to the plants traditionally used against a given disease.",
            },
            {
                selector: "#library-grid > div",
                title: "A plant, documented",
                text: "Each card shows the plant, its active compound, the region and people who use it, the preparation, and the source it is cited from.",
            },
            {
                selector: "[data-dock-smiles]",
                title: "Send it to the lab",
                text: "Click Dock this compound on any card to load that molecule straight into the lab and screen it against a disease target.",
            },
            {
                selector: 'a[href="/api/dataset.csv"]',
                title: "Open data",
                text: "The whole library is downloadable as an open dataset, in CSV or JSON, for anyone to reuse. That is the end of the tour, enjoy.",
            },
        ]);
    },

    paint() {
        this.mountEl.innerHTML = AppShell.shell(this.body());
        this.wireEvents();
    },

    diseases() {
        const set = new Set();
        this.state.compounds.forEach((c) =>
            (c.traditional_use.disease || "")
                .split(/[,/]/)
                .map((d) => d.trim())
                .filter(Boolean)
                .forEach((d) => set.add(d))
        );
        return [...set].sort();
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
        this.wireCards();
    },

    wireCards() {
        document.querySelectorAll("[data-dock-smiles]").forEach((el) => {
            el.addEventListener("click", () => {
                sessionStorage.setItem("valkyrie:prefill", el.dataset.dockSmiles);
                Router.navigate("/lab");
            });
        });
    },

    updateGrid() {
        const grid = document.getElementById("library-grid");
        if (grid) grid.outerHTML = this.grid();
        this.wireCards();
    },

    filtered() {
        const q = this.state.query.toLowerCase();
        const d = this.state.diseaseFilter.toLowerCase();
        return this.state.compounds.filter((c) => {
            const matchesQuery =
                !q ||
                c.compound_name.toLowerCase().includes(q) ||
                c.plant.scientific_name.toLowerCase().includes(q) ||
                c.plant.local_name.toLowerCase().includes(q) ||
                (c.smiles || "").toLowerCase().includes(q);
            const matchesDisease = !d || (c.traditional_use.disease || "").toLowerCase().includes(d);
            return matchesQuery && matchesDisease;
        });
    },

    body() {
        const diseaseOptions = this.diseases()
            .map((d) => `<option value="${escapeHtml(d)}">${escapeHtml(d)}</option>`)
            .join("");
        const title = `
            <h1 class="font-headline-md text-body-lg text-on-surface font-medium">Ethnobotanical Library</h1>
            <span class="font-code-md text-xs text-on-surface-variant bg-surface-container-low border border-outline-variant rounded-full px-2.5 py-1">${this.state.compounds.length} compounds</span>`;
        const actions = `
            <button onclick="LibraryPage.startTour()" class="inline-flex items-center gap-1.5 bg-surface-container-low border border-outline-variant text-on-surface px-3 py-1.5 rounded-lg font-body-sm text-body-sm hover:bg-surface-container transition-colors"><span class="material-symbols-outlined text-[18px]">help</span> Guide</button>
            <a href="/api/dataset.csv" class="inline-flex items-center gap-1.5 bg-surface-container-low border border-outline-variant text-on-surface px-3 py-1.5 rounded-lg font-body-sm text-body-sm hover:bg-surface-container transition-colors"><span class="material-symbols-outlined text-[18px]">download</span> Dataset (CSV)</a>
            <a href="/api/dataset" target="_blank" rel="noopener" class="inline-flex items-center px-2 py-1.5 font-body-sm text-body-sm text-on-surface-variant hover:text-primary">JSON</a>`;
        return `
        ${AppShell.toolbar(title, actions)}
        <div class="border-b border-outline-variant bg-surface px-5 py-4 flex flex-col md:flex-row gap-3 items-center">
            <div class="flex-1 relative w-full">
                <span class="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 text-outline">search</span>
                <input id="library-search" type="text" placeholder="Search by botanical name, local name, compound or SMILES..."
                    class="w-full pl-10 pr-4 py-2.5 bg-surface-container-low border border-outline-variant rounded-xl font-body-md text-body-md focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary" />
            </div>
            <div class="relative w-full md:w-56">
                <select id="disease-filter" class="w-full appearance-none bg-surface-container-low border border-outline-variant rounded-xl px-4 py-2.5 pr-10 font-body-md text-body-md focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary">
                    <option value="">Filter by disease</option>
                    ${diseaseOptions}
                </select>
                <span class="material-symbols-outlined absolute right-3 top-1/2 -translate-y-1/2 text-outline pointer-events-none">arrow_drop_down</span>
            </div>
        </div>
        <div class="p-5 flex flex-col gap-5">
            ${this.state.error ? `<div class="p-3 bg-error-container text-on-error-container rounded-xl font-body-sm text-body-sm">${escapeHtml(this.state.error)}</div>` : ""}
            ${this.grid()}
        </div>`;
    },

    grid() {
        const items = this.filtered();
        if (!items.length) {
            return `<section id="library-grid" class="text-center py-16 text-on-surface-variant font-body-md text-body-md">No compounds match your search.</section>`;
        }
        return `<section id="library-grid" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            ${items.map((c) => this.card(c)).join("")}
        </section>`;
    },

    card(c) {
        const primaryDisease = (c.traditional_use.disease || "").split(/[,/]/)[0].trim();
        const detail = (icon, text) =>
            text
                ? `<div class="flex items-center gap-2 text-body-sm font-body-sm text-on-surface-variant">
                    <span class="material-symbols-outlined text-[16px]">${icon}</span><span>${escapeHtml(text)}</span>
                </div>`
                : "";
        return `
        <div class="bg-surface-container-lowest border border-outline-variant rounded-lg overflow-hidden flex flex-col group hover:shadow-[0px_8px_24px_rgba(0,0,0,0.08)] transition-shadow">
            <div class="h-44 relative border-b border-outline-variant bg-surface-container-low overflow-hidden">
                ${this.images[c.id] ? `<img src="${this.images[c.id]}" alt="${escapeHtml(c.plant.scientific_name)}" loading="lazy" class="w-full h-full object-cover" onerror="this.style.display='none';this.nextElementSibling.style.display='flex';" />` : ""}
                <div class="absolute inset-0 items-center justify-center bg-deep-navy ${this.images[c.id] ? "hidden" : "flex"}">
                    <div class="absolute inset-0 opacity-20" style="background-image:radial-gradient(#a9c7ff 1px, transparent 1px);background-size:14px 14px;"></div>
                    <span class="material-symbols-outlined text-primary-fixed-dim relative z-10" style="font-size:72px;font-variation-settings:'FILL' 1;">potted_plant</span>
                </div>
                <span class="absolute top-2 right-2 z-10 bg-molecular-green/90 text-white px-2 py-1 rounded font-label-caps text-label-caps">${escapeHtml(primaryDisease || "compound")}</span>
            </div>
            <div class="p-4 flex-1 flex flex-col gap-2">
                <div>
                    <h3 class="font-headline-md text-headline-md text-on-surface italic leading-tight">${escapeHtml(c.plant.scientific_name)}</h3>
                    <p class="font-body-sm text-body-sm text-on-surface-variant">${escapeHtml(c.plant.local_name)}${c.plant.family ? ` &middot; ${escapeHtml(c.plant.family)}` : ""}</p>
                </div>
                <div class="mt-2 space-y-1.5">
                    ${detail("science", `${c.compound_name} (active)`)}
                    ${detail("public", c.traditional_use.region)}
                    ${detail("groups", c.traditional_use.people)}
                    ${detail("water_drop", c.traditional_use.preparation)}
                </div>
                <p class="text-xs text-on-surface-variant mt-2 border-t border-outline-variant pt-2 line-clamp-3">${escapeHtml(c.source)}</p>
                <div class="mt-auto pt-4 flex gap-2">
                    <button data-dock-smiles="${escapeHtml(c.smiles)}" class="flex-1 bg-primary text-on-primary font-body-sm text-body-sm px-4 py-2 rounded flex items-center justify-center gap-2 hover:bg-deep-navy transition-colors">
                        <span class="material-symbols-outlined text-[18px]">biotech</span> Dock this compound
                    </button>
                    <span class="px-3 py-2 border border-outline-variant rounded text-outline font-code-md text-xs flex items-center" title="SMILES">${escapeHtml((c.smiles || "").slice(0, 10))}${(c.smiles || "").length > 10 ? "…" : ""}</span>
                </div>
            </div>
        </div>`;
    },
};
