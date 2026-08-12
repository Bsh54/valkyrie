// Shared chrome: top nav and footer, lifted from the Stitch design pages.
const Layout = {
    navLinks: [
        { href: "/lab", label: "Lab" },
        { href: "/library", label: "Library" },
        { href: "/benchmarks", label: "Benchmarks" },
    ],

    header() {
        const links = this.navLinks
            .map(
                (l) => `<a data-link data-nav-link href="${l.href}"
                    class="text-on-surface-variant hover:text-primary transition-colors font-body-md text-body-md py-5 border-b-2 border-transparent">${l.label}</a>`
            )
            .join("");

        return `
        <header class="bg-surface sticky top-0 z-50 flex justify-between items-center w-full px-margin-mobile md:px-margin-desktop max-w-max-width mx-auto h-16 border-b border-outline-variant">
            <div class="flex items-center gap-8">
                <a data-link href="/" class="font-headline-md text-headline-md font-bold text-primary flex items-center gap-2">
                    <span class="material-symbols-outlined" style="font-variation-settings:'FILL' 1;">science</span>
                    DrugForge
                </a>
                <nav class="hidden md:flex gap-6">${links}</nav>
            </div>
        </header>
        <div class="bg-primary-fixed/40 text-on-primary-fixed-variant text-center py-1.5 px-4 text-body-sm font-medium border-b border-outline-variant">
            In-silico predictions only &mdash; not clinical advice. Every result requires laboratory validation.
        </div>`;
    },

    footer() {
        return `
        <footer class="bg-surface-container-highest w-full py-8 px-margin-mobile md:px-margin-desktop mt-auto border-t border-outline-variant">
            <div class="max-w-max-width mx-auto flex flex-col md:flex-row justify-between items-center gap-4">
                <div class="font-headline-md text-headline-md text-primary flex items-center gap-2">
                    <span class="material-symbols-outlined" style="font-variation-settings:'FILL' 1;">science</span>
                    DrugForge
                </div>
                <nav class="flex flex-wrap gap-6 justify-center">
                    <a class="font-body-sm text-body-sm text-on-surface-variant hover:text-primary hover:underline" href="https://github.com" target="_blank" rel="noopener">GitHub</a>
                    <a data-link class="font-body-sm text-body-sm text-on-surface-variant hover:text-primary hover:underline" href="/library">Citations</a>
                </nav>
                <div class="font-body-sm text-body-sm text-on-surface">DrugForge Lab. CC-BY 4.0 for data.</div>
            </div>
        </footer>`;
    },

    shell(bodyHtml) {
        return `${this.header()}<main class="flex-1 w-full flex flex-col">${bodyHtml}</main>${this.footer()}`;
    },
};
