// Thin wrapper around 3Dmol.js for the docked-pose viewport.
const Viewer3D = {
    render(containerId, sdf) {
        const el = document.getElementById(containerId);
        if (!el || typeof $3Dmol === "undefined") return null;

        const viewer = $3Dmol.createViewer(containerId, { backgroundColor: "white" });
        if (sdf) {
            viewer.addModel(sdf, "sdf");
            viewer.setStyle({}, { stick: { colorscheme: "Jmol", radius: 0.15 } });
            viewer.zoomTo();
        }
        viewer.render();
        return viewer;
    },
};
