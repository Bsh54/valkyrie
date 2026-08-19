// Route table. Real paths only, no hash fragments and no per-page HTML files.
document.addEventListener("DOMContentLoaded", () => {
    const mountEl = document.getElementById("app");
    Router.init(mountEl);

    Router.register("/", () => HomePage.render(mountEl));

    Router.register("/lab", () => {
        const prefill = sessionStorage.getItem("valkyrie:prefill");
        sessionStorage.removeItem("valkyrie:prefill");
        LabPage.render(mountEl, { prefill });
    });

    Router.register("/result/:resultId", (params) => LabPage.render(mountEl, params));

    Router.register("/learn", () => LearnPage.render(mountEl));
    Router.register("/library", () => LibraryPage.render(mountEl));
    Router.register("/benchmarks", () => BenchmarksPage.render(mountEl));

    Router.render();
});
