// 3Dmol.js viewer. Two modes:
//  - render(id, sdf): plain ligand preview (kept for compatibility).
//  - renderResult(id, sdf, pdbId): the docked pose shown inside the real protein
//    pocket, with interactive controls (spin, pocket surface, protein, reset, PNG).
const Viewer3D = {
    _viewer: null,
    _lig: null,
    _protein: null,
    _surface: null,
    _spinning: false,
    _proteinHidden: false,

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

    renderResult(containerId, sdf, pdbId) {
        const el = document.getElementById(containerId);
        if (!el || typeof $3Dmol === "undefined") return null;

        const viewer = $3Dmol.createViewer(containerId, { backgroundColor: "#0b1526" });
        this._viewer = viewer;
        this._surface = null;
        this._spinning = false;
        this._proteinHidden = false;
        this._protein = null;

        this._lig = viewer.addModel(sdf, "sdf");
        this._styleLigand();

        if (pdbId) {
            $3Dmol.download("pdb:" + pdbId, viewer, {}, (m) => {
                this._protein = m;
                this._styleProtein();
                const fb = document.getElementById(containerId + "-fallback");
                if (fb) fb.remove();
                viewer.zoomTo({ model: this._lig });
                viewer.zoom(0.7);
                viewer.render();
            });
        } else {
            viewer.zoomTo();
            viewer.render();
        }
        return viewer;
    },

    _styleLigand() {
        this._viewer.setStyle(
            { model: this._lig },
            { stick: { colorscheme: "greenCarbon", radius: 0.2 }, sphere: { scale: 0.28 } }
        );
    },

    _styleProtein() {
        if (this._protein == null) return;
        this._viewer.setStyle(
            { model: this._protein },
            { cartoon: { color: "spectrum", opacity: 0.8 } }
        );
        // Binding-site residues within 4.5 A of the ligand, as thin sticks.
        this._viewer.addStyle(
            { model: this._protein, within: { distance: 4.5, sel: { model: this._lig } } },
            { stick: { colorscheme: "cyanCarbon", radius: 0.12 } }
        );
    },

    toggleSpin() {
        if (!this._viewer) return;
        this._spinning = !this._spinning;
        this._viewer.spin(this._spinning ? "y" : false);
    },

    toggleProtein() {
        if (!this._viewer || this._protein == null) return;
        this._proteinHidden = !this._proteinHidden;
        if (this._proteinHidden) {
            this._viewer.setStyle({ model: this._protein }, {});
        } else {
            this._styleProtein();
        }
        this._viewer.render();
    },

    toggleSurface() {
        if (!this._viewer || this._protein == null) return;
        try {
            if (this._surface != null) {
                this._viewer.removeSurface(this._surface);
                this._surface = null;
                this._viewer.render();
                return;
            }
            this._surface = this._viewer.addSurface(
                $3Dmol.SurfaceType.VDW,
                { opacity: 0.72, color: "#a9c7ff" },
                { model: this._protein, within: { distance: 6, sel: { model: this._lig } } }
            );
            this._viewer.render();
        } catch (e) {
            /* surfaces are optional */
        }
    },

    reset() {
        if (!this._viewer) return;
        this._viewer.zoomTo(this._lig != null ? { model: this._lig } : {});
        this._viewer.zoom(0.7);
        this._viewer.render();
    },

    screenshot() {
        if (!this._viewer) return;
        try {
            const uri = this._viewer.pngURI();
            const a = document.createElement("a");
            a.href = uri;
            a.download = "drugforge-pose.png";
            document.body.appendChild(a);
            a.click();
            a.remove();
        } catch (e) {
            /* ignore */
        }
    },
};
