// Shared chrome: classic clean top nav and multi-column footer.
const Layout = {
    navLinks: [
        { href: "/lab", label: "Lab" },
        { href: "/library", label: "Library" },
        { href: "/benchmarks", label: "Benchmarks" },
    ],

    header() {
        const desktopLinks = this.navLinks
            .map(
                (l) => `<a data-link data-nav-link href="${l.href}"
                    class="text-on-surface-variant hover:text-primary transition-colors font-body-md text-body-md font-medium border-b-2 border-transparent pb-1">${l.label}</a>`
            )
            .join("");
        const mobileLinks = this.navLinks
            .map(
                (l) => `<a data-link data-nav-link href="${l.href}"
                    class="text-on-surface-variant hover:text-primary transition-colors font-body-md text-body-md py-2 border-b-2 border-transparent">${l.label}</a>`
            )
            .join("");

        return `
        <header class="bg-surface/90 backdrop-blur sticky top-0 z-50 border-b border-outline-variant">
            <div class="flex justify-between items-center w-full px-margin-mobile md:px-margin-desktop max-w-max-width mx-auto h-16">
                <div class="flex items-center gap-10">
                    <a data-link href="/" class="font-headline-md text-headline-md font-bold text-primary flex items-center gap-2">
                        <img src="/img/logo-mark.png" alt="Valkyrie" class="h-7 w-7 object-contain" />
                        Valkyrie
                    </a>
                    <nav class="hidden md:flex gap-8 items-center h-16">${desktopLinks}</nav>
                </div>
                <div class="flex items-center gap-4">
                    <a href="https://github.com/Bsh54/valkyrie" target="_blank" rel="noopener" class="hidden sm:flex items-center gap-1.5 text-on-surface-variant hover:text-primary transition-colors font-body-md text-body-md">
                        <span class="material-symbols-outlined text-[20px]">code</span> GitHub
                    </a>
                    <a data-link href="/lab" class="hidden sm:inline-flex bg-primary text-on-primary font-body-md text-body-md px-4 py-2 rounded-xl hover:bg-deep-navy transition-colors font-medium">Start Docking</a>
                    <button type="button" aria-label="Menu" onclick="document.getElementById('mobile-nav').classList.toggle('hidden')"
                        class="md:hidden inline-flex items-center justify-center w-10 h-10 rounded-lg text-on-surface hover:bg-surface-container-low transition-colors">
                        <span class="material-symbols-outlined">menu</span>
                    </button>
                </div>
            </div>
            <div id="mobile-nav" class="hidden md:hidden border-t border-outline-variant bg-surface">
                <nav class="flex flex-col px-margin-mobile py-3 gap-1">
                    ${mobileLinks}
                    <a data-link href="/lab" class="mt-2 bg-primary text-on-primary text-center font-body-md text-body-md px-4 py-2.5 rounded-xl hover:bg-deep-navy transition-colors font-medium">Start Docking</a>
                </nav>
            </div>
        </header>`;
    },

    footer() {
        const col = (title, items) => `
            <div>
                <div class="font-label-caps text-label-caps text-on-surface-variant uppercase mb-3">${title}</div>
                <div class="flex flex-col gap-2">${items.join("")}</div>
            </div>`;
        const link = (href, label, ext) =>
            ext
                ? `<a href="${href}" target="_blank" rel="noopener" class="font-body-sm text-body-sm text-on-surface-variant hover:text-primary transition-colors">${label}</a>`
                : `<a data-link href="${href}" class="font-body-sm text-body-sm text-on-surface-variant hover:text-primary transition-colors">${label}</a>`;

        return `
        <footer class="bg-surface-container-lowest border-t border-outline-variant mt-auto">
            <div class="max-w-max-width mx-auto px-margin-mobile md:px-margin-desktop py-12">
                <div class="grid grid-cols-2 md:grid-cols-4 gap-8">
                    <div class="col-span-2 md:col-span-1">
                        <div class="font-headline-md text-headline-md text-primary flex items-center gap-2 mb-3">
                            <img src="/img/logo-mark.png" alt="Valkyrie" class="h-7 w-7 object-contain" />
                            Valkyrie
                        </div>
                        <p class="font-body-sm text-body-sm text-on-surface-variant max-w-xs">
                            Open molecular docking for neglected tropical diseases. Bridging African plant
                            medicine and in-silico validation.
                        </p>
                    </div>
                    ${col("Product", [link("/lab", "Docking Lab"), link("/library", "Ethnobotanical Library"), link("/benchmarks", "Benchmarks")])}
                    ${col("Open", [link("https://github.com/Bsh54/valkyrie", "GitHub", true), link("/api/dataset.csv", "Open dataset (CC-BY)", true), link("/benchmarks", "Validation")])}
                    ${col("Diseases", [link("/lab", "Malaria"), link("/lab", "Chagas disease"), link("/lab", "Leishmaniasis")])}
                </div>
                <div class="border-t border-outline-variant mt-10 pt-6 flex flex-col md:flex-row justify-between items-center gap-3">
                    <div class="font-body-sm text-body-sm text-on-surface-variant">Valkyrie Lab. Code Apache-2.0, data CC-BY-4.0.</div>
                    <div class="font-body-sm text-body-sm text-on-surface-variant flex items-center gap-2">
                        <span class="material-symbols-outlined text-[16px] text-primary">info</span>
                        In-silico predictions only, not clinical advice.
                    </div>
                </div>
            </div>
        </footer>`;
    },

    shell(bodyHtml) {
        return `${this.header()}<main class="flex-1 w-full flex flex-col">${bodyHtml}</main>${this.footer()}`;
    },
};

// Application shell for the tool section (Lab, Library, Benchmarks): a persistent
// left rail, a mobile top bar, and a workspace with no marketing chrome.
const AppShell = {
    railLinks: [
        { href: "/lab", icon: "labs", label: "Lab" },
        { href: "/library", icon: "local_florist", label: "Library" },
        { href: "/benchmarks", icon: "insights", label: "Benchmarks" },
    ],

    rail() {
        const path = location.pathname;
        const items = this.railLinks
            .map((l) => {
                const on = path === l.href || (l.href === "/lab" && path.startsWith("/result"));
                return `<a data-link href="${l.href}"
                    class="flex items-center gap-3 px-3 py-2 rounded-lg font-body-md text-body-md transition-colors ${on ? "bg-primary/10 text-primary font-medium" : "text-on-surface-variant hover:bg-surface-container-low hover:text-on-surface"}">
                    <span class="material-symbols-outlined text-[20px]" style="font-variation-settings:'FILL' ${on ? 1 : 0};">${l.icon}</span>${l.label}
                </a>`;
            })
            .join("");
        return `
        <aside class="hidden md:flex flex-col w-56 shrink-0 border-r border-outline-variant bg-surface-container-lowest sticky top-0 h-screen">
            <a data-link href="/" class="flex items-center gap-2 h-16 px-4 border-b border-outline-variant font-headline-md text-headline-md font-bold text-primary shrink-0">
                <img src="/img/logo-mark.png" alt="Valkyrie" class="h-7 w-7 object-contain" />Valkyrie
            </a>
            <nav class="flex flex-col gap-1 p-3">${items}</nav>
            <div class="mt-auto p-3 border-t border-outline-variant flex flex-col gap-1">
                <a href="https://github.com/Bsh54/valkyrie" target="_blank" rel="noopener" class="flex items-center gap-3 px-3 py-2 rounded-lg text-on-surface-variant hover:bg-surface-container-low hover:text-on-surface font-body-md text-body-md">
                    <span class="material-symbols-outlined text-[20px]">code</span>GitHub
                </a>
                <a data-link href="/" class="flex items-center gap-3 px-3 py-2 rounded-lg text-on-surface-variant hover:bg-surface-container-low hover:text-on-surface font-body-md text-body-md">
                    <span class="material-symbols-outlined text-[20px]">home</span>Back to site
                </a>
            </div>
        </aside>`;
    },

    mobileBar() {
        const path = location.pathname;
        const items = this.railLinks
            .map((l) => {
                const on = path === l.href || (l.href === "/lab" && path.startsWith("/result"));
                return `<a data-link href="${l.href}" class="flex items-center gap-1.5 px-3 py-1.5 rounded-lg font-body-sm text-body-sm ${on ? "bg-primary/10 text-primary" : "text-on-surface-variant"}">
                    <span class="material-symbols-outlined text-[18px]">${l.icon}</span>${l.label}
                </a>`;
            })
            .join("");
        return `
        <div class="md:hidden flex items-center gap-2 h-14 px-4 border-b border-outline-variant bg-surface-container-lowest overflow-x-auto">
            <a data-link href="/" class="font-headline-md text-body-lg font-bold text-primary flex items-center gap-1 shrink-0 mr-2">
                <img src="/img/logo-mark.png" alt="Valkyrie" class="h-6 w-6 object-contain" />
            </a>
            ${items}
        </div>`;
    },

    // Sticky workspace toolbar. left = title area, right = contextual actions.
    toolbar(left, right = "") {
        return `
        <div class="h-14 shrink-0 border-b border-outline-variant bg-surface/90 backdrop-blur sticky top-0 z-30 flex items-center justify-between gap-3 px-5">
            <div class="flex items-center gap-3 min-w-0">${left}</div>
            <div class="flex items-center gap-2 shrink-0">${right}</div>
        </div>`;
    },

    shell(bodyHtml) {
        return `
        <div class="flex min-h-screen w-full">
            ${this.rail()}
            <div class="flex-1 flex flex-col min-w-0 bg-background">
                ${this.mobileBar()}
                ${bodyHtml}
            </div>
        </div>`;
    },
};
