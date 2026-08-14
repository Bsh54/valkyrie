const API = {
    async _get(path) {
        const response = await fetch(path);
        if (!response.ok) throw new Error(await this._message(response));
        return response.json();
    },

    async _message(response) {
        try {
            const body = await response.json();
            const detail = body.detail;
            if (typeof detail === "string") return detail;
            if (detail && detail.detail) return detail.detail;
            return `Request failed (${response.status})`;
        } catch {
            return `Request failed (${response.status})`;
        }
    },

    getTargets() {
        return this._get("/api/targets");
    },

    getTarget(id) {
        return this._get(`/api/targets/${encodeURIComponent(id)}`);
    },

    async getCompounds() {
        const body = await this._get("/api/compounds");
        return body.compounds || [];
    },

    getBenchmarks() {
        return this._get("/api/benchmarks");
    },

    getScreening(id) {
        return this._get(`/api/screenings/${encodeURIComponent(id)}`);
    },

    getJob(jobId) {
        return this._get(`/api/jobs/${encodeURIComponent(jobId)}`);
    },

    async submitScreening(molecule, targetId, exhaustiveness) {
        const response = await fetch("/api/screenings", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ molecule, target_id: targetId, exhaustiveness }),
        });
        if (!response.ok) throw new Error(await this._message(response));
        return response.json();
    },

    reportUrl(id) {
        return `/api/screenings/${encodeURIComponent(id)}/report`;
    },
};
