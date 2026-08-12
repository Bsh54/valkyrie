// Minimal History API router. Real paths (/lab, /library, /benchmarks,
// /result/:id), no hash fragments and no per-page HTML files: every route
// renders into the same shell via JS.
const Router = {
    routes: [],
    mountEl: null,

    init(mountEl) {
        this.mountEl = mountEl;
        document.body.addEventListener("click", (event) => {
            const link = event.target.closest("[data-link]");
            if (!link) return;
            event.preventDefault();
            this.navigate(link.getAttribute("href"));
        });
        window.addEventListener("popstate", () => this.render());
    },

    register(pattern, handler) {
        const paramNames = [];
        const regex = new RegExp(
            "^" +
                pattern.replace(/:[a-zA-Z]+/g, (match) => {
                    paramNames.push(match.slice(1));
                    return "([^/]+)";
                }) +
                "$"
        );
        this.routes.push({ regex, paramNames, handler });
    },

    navigate(path) {
        if (path === location.pathname + location.search) return;
        history.pushState({}, "", path);
        this.render();
    },

    render() {
        const path = location.pathname;
        for (const route of this.routes) {
            const match = path.match(route.regex);
            if (!match) continue;
            const params = {};
            route.paramNames.forEach((name, i) => (params[name] = match[i + 1]));
            this.mountEl.innerHTML = "";
            route.handler(params, new URLSearchParams(location.search));
            this.updateNavHighlight(path);
            return;
        }
        this.mountEl.innerHTML = `<div class="p-margin-desktop text-center text-on-surface-variant">Page not found.</div>`;
    },

    updateNavHighlight(path) {
        document.querySelectorAll("[data-nav-link]").forEach((el) => {
            const active = el.getAttribute("href") === path;
            el.classList.toggle("text-primary", active);
            el.classList.toggle("border-primary", active);
            el.classList.toggle("text-on-surface-variant", !active);
            el.classList.toggle("border-transparent", !active);
        });
    },
};

function escapeHtml(value) {
    return String(value ?? "").replace(/[&<>"']/g, (c) => ({
        "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
    }[c]));
}
