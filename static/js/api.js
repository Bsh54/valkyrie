const API = {
    async getTargets() {
        const r = await fetch('/api/targets');
        if (!r.ok) throw new Error('Failed to load targets');
        return r.json();
    },

    async getCompounds() {
        const r = await fetch('/api/compounds');
        if (!r.ok) throw new Error('Failed to load compounds');
        return r.json();
    },

    async dock(molecule, targetId, exhaustiveness = 8) {
        const r = await fetch('/api/dock', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ molecule, target_id: targetId, exhaustiveness }),
        });
        if (!r.ok) {
            const err = await r.json();
            throw new Error(err.detail?.detail || err.detail || 'Docking failed');
        }
        return r.json();
    },

    async getResult(id) {
        const r = await fetch(`/api/result/${id}`);
        if (!r.ok) throw new Error('Result not found');
        return r.json();
    },

    reportUrl(id) {
        return `/api/result/${id}/report`;
    }
};
