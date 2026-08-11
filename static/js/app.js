const App = {
    root: document.getElementById('app'),
    state: { targets: [], compounds: [] },

    async init() {
        window.addEventListener('hashchange', () => this.route());
        try {
            this.state.targets = await API.getTargets();
            this.state.compounds = await API.getCompounds();
        } catch (e) {
            console.error('Init failed:', e);
        }
        this.route();
    },

    route() {
        const hash = location.hash || '#/';
        if (hash.startsWith('#/result/')) {
            this.showResult(hash.replace('#/result/', ''));
        } else if (hash === '#/library') {
            this.showLibrary();
        } else if (hash === '#/benchmarks') {
            this.showBenchmarks();
        } else {
            this.showSubmit();
        }
    },

    async showBenchmarks() {
        document.title = 'DrugForge — Benchmarks';
        this.root.innerHTML = '<div class="loading">Loading benchmarks...</div>';

        let data;
        try {
            data = await API.getBenchmarks();
        } catch (e) {
            this.root.innerHTML = `<div class="card"><h2>Benchmarks</h2>
                <div class="error-box">${e.message}</div></div>`;
            return;
        }

        this.root.innerHTML = `
            <h1>Benchmarks</h1>
            <div class="scope-box" role="note">
                <strong>Scope.</strong> ${data.scope_statement}
            </div>
            ${this.renderInternalBench(data)}
            ${this.renderExternalBench(data)}
            <div class="card" style="font-size:0.85rem;color:var(--text-muted)">
                <strong>Reproduce these numbers</strong>
                <pre style="white-space:pre-wrap;margin-top:0.5rem">python scripts/bench_internal.py
python scripts/bench_external.py</pre>
                ${data.disclaimer}
            </div>
        `;
    },

    renderInternalBench(data) {
        if (data.internal_status !== 'available') {
            return `<div class="card"><h2>Internal validation</h2>
                <p style="color:var(--text-muted)">Not yet run.</p></div>`;
        }
        const b = data.internal;
        const rd = b.redocking || {};
        const rp = b.reproducibility || {};
        const ct = b.controls || {};
        const en = b.enrichment || {};

        const rdRows = (rd.results || []).map(r => `<tr>
            <td>${r.pdb_id}</td>
            <td>${r.rmsd !== undefined ? r.rmsd + ' Å' : '—'}</td>
            <td>${r.status}</td>
            <td>${r.reason || ''}</td></tr>`).join('');

        const negRows = (ct.negatives || []).map(n => `<tr>
            <td>${n.name}</td>
            <td>${n.vina !== undefined ? n.vina : '—'}</td>
            <td>${n.reason || 'ok'}</td></tr>`).join('');

        const enrichBlock = en.status === 'available' ? `
            <table>
                <thead><tr><th>Score</th><th>AUC</th><th>EF 1%</th><th>EF 10%</th></tr></thead>
                <tbody>
                    <tr><td>Vina</td><td>${this.fmt(en.vina?.auc)}</td>
                        <td>${this.fmt(en.vina?.ef1)}</td><td>${this.fmt(en.vina?.ef10)}</td></tr>
                    <tr><td>Consensus</td><td>${this.fmt(en.consensus?.auc)}</td>
                        <td>${this.fmt(en.consensus?.ef1)}</td><td>${this.fmt(en.consensus?.ef10)}</td></tr>
                </tbody>
            </table>
            <p style="margin-top:0.5rem">
                ${en.n_actives} actives / ${en.n_inactives} inactives,
                ${(en.skipped || []).length} skipped.
                Consensus improves AUC: <strong>${en.consensus_improves === null ? 'undetermined' : (en.consensus_improves ? 'yes' : 'no')}</strong>
            </p>
            ${en.inactives_note ? `<p style="font-size:0.8rem;color:var(--text-muted)">${en.inactives_note}</p>` : ''}
        ` : `<p style="color:var(--text-muted)">Not run (${en.reason || 'no data'}).</p>`;

        return `
            <div class="card">
                <h2>Internal validation — ${b.target_name} (${b.pdb_id})</h2>
                <p style="color:var(--text-muted);font-size:0.9rem">
                    Reference drug: ${b.reference_drug} ·
                    exhaustiveness ${b.config?.exhaustiveness} ·
                    Vina ${b.config?.vina_version} ·
                    generated ${(b.generated_at || '').slice(0, 10)}
                </p>

                <h3>Redocking RMSD</h3>
                <p>Evaluated ${rd.evaluated ?? 0} · skipped ${rd.skipped ?? 0} ·
                   RMSD &lt; 2.0 Å: ${rd.success_rate_under_2A === null || rd.success_rate_under_2A === undefined ? '—' : (rd.success_rate_under_2A * 100).toFixed(0) + '%'}</p>
                <table><thead><tr><th>PDB</th><th>RMSD</th><th>Status</th><th>Reason</th></tr></thead>
                    <tbody>${rdRows}</tbody></table>
                ${rd.note ? `<p style="font-size:0.8rem;color:var(--text-muted);margin-top:0.5rem">${rd.note}</p>` : ''}

                <h3 style="margin-top:1.25rem">Reproducibility</h3>
                <p>n=${rp.n} · mean ${this.fmt(rp.mean)} kcal/mol ·
                   spread ±${this.fmt(rp.spread)} · std ${this.fmt(rp.std)}</p>

                <h3 style="margin-top:1.25rem">Controls</h3>
                <p>Reference ${ct.reference?.name}: <strong>${this.fmt(ct.reference?.vina)}</strong> kcal/mol ·
                   expected ordering held:
                   <strong>${ct.ordering_held === null ? 'undetermined' : (ct.ordering_held ? 'yes' : 'no')}</strong></p>
                <table><thead><tr><th>Negative control</th><th>Vina</th><th>Status</th></tr></thead>
                    <tbody>${negRows}</tbody></table>

                <h3 style="margin-top:1.25rem">Enrichment</h3>
                ${enrichBlock}
            </div>
        `;
    },

    renderExternalBench(data) {
        if (data.external_status !== 'available') {
            return `<div class="card"><h2>External independent redocking</h2>
                <p style="color:var(--text-muted)">Not yet run.</p></div>`;
        }
        const b = data.external;
        const breakdown = Object.entries(b.skip_reasons || {})
            .map(([k, v]) => `${k}: ${v}`).join(' · ') || 'none';

        const rows = (b.results || []).map(r => `<tr>
            <td>${r.pdb_id}</td>
            <td>${r.ligand_residue || ''}</td>
            <td>${r.rmsd !== undefined ? r.rmsd : '—'}</td>
            <td>${r.status}</td>
            <td>${r.reason || ''}</td></tr>`).join('');

        return `
            <div class="card">
                <h2>External independent redocking</h2>
                <p style="color:var(--text-muted);font-size:0.9rem">
                    ${b.set_name} · exhaustiveness ${b.config?.exhaustiveness} ·
                    generated ${(b.generated_at || '').slice(0, 10)}
                </p>
                <p style="font-size:0.85rem"><strong>Selection rule.</strong> ${b.selection_rule}</p>
                <p><strong>Attempted ${b.attempted}</strong> ·
                   evaluated ${b.evaluated} · skipped ${b.skipped}</p>
                <p>RMSD &lt; 2.0 Å: ${b.success_rate_under_2A === null ? '—' : (b.success_rate_under_2A * 100).toFixed(0) + '%'} ·
                   median RMSD ${this.fmt(b.median_rmsd)} Å ·
                   mean ${this.fmt(b.mean_rmsd)} Å</p>
                <p style="font-size:0.85rem"><strong>Skipped breakdown.</strong> ${breakdown}</p>
                <p style="font-size:0.8rem;color:var(--text-muted)">${b.denominator_note || ''}</p>
                <div style="overflow-x:auto;max-height:420px;overflow-y:auto;margin-top:0.75rem">
                    <table><thead><tr><th>PDB</th><th>Ligand</th><th>RMSD</th><th>Status</th><th>Reason</th></tr></thead>
                        <tbody>${rows}</tbody></table>
                </div>
                <p style="font-size:0.8rem;color:var(--text-muted);margin-top:0.5rem">${b.citation || ''}</p>
            </div>
        `;
    },

    fmt(v) {
        return v === null || v === undefined ? '—' : v;
    },

    showSubmit() {
        document.title = 'DrugForge — Screen';
        const targetOpts = this.state.targets.map(t =>
            `<option value="${t.id}">${t.name} (${t.disease})</option>`
        ).join('');

        const compoundCards = this.state.compounds.map(c => `
            <div class="compound-card" data-smiles="${c.smiles}" tabindex="0" role="button"
                 aria-label="Select ${c.compound_name}">
                <div class="name">${c.compound_name}</div>
                <div class="plant">${c.plant.scientific_name}</div>
            </div>
        `).join('');

        this.root.innerHTML = `
            <h1>Virtual Screening</h1>
            <p style="color:var(--text-muted);margin-bottom:1.5rem">
                Enter a molecule or pick from the medicinal-plant library.
            </p>

            <div class="card">
                <label for="mol-input">Molecule (name or SMILES)</label>
                <input type="text" id="mol-input" placeholder="e.g. artemisinin, or Cn1c2ccccc2c2...">
                <div style="margin-top:1rem">
                    <label for="target-select">Disease Target</label>
                    <select id="target-select">${targetOpts}</select>
                </div>
                <div style="margin-top:1rem">
                    <label for="exh-range">Exhaustiveness: <span id="exh-val">8</span></label>
                    <input type="range" id="exh-range" min="1" max="32" value="8">
                </div>
                <div style="margin-top:1.25rem">
                    <button class="btn" id="dock-btn">Dock</button>
                    <span id="loading-msg" class="loading" style="display:none;padding:0;margin-left:1rem;">
                        Docking in progress (~30-60s)...
                    </span>
                </div>
                <div id="error-box"></div>
            </div>

            <h2>Medicinal-Plant Compounds</h2>
            <p style="color:var(--text-muted);margin-bottom:0.5rem;font-size:0.9rem">
                Traditional knowledge → molecular validation (in silico)
            </p>
            <div class="compound-grid">${compoundCards}</div>
        `;

        const exh = this.root.querySelector('#exh-range');
        exh.oninput = () => this.root.querySelector('#exh-val').textContent = exh.value;

        this.root.querySelector('#dock-btn').onclick = () => this.submitDock();

        this.root.querySelectorAll('.compound-card').forEach(card => {
            const handler = () => {
                this.root.querySelector('#mol-input').value = card.dataset.smiles;
            };
            card.onclick = handler;
            card.onkeydown = (e) => { if (e.key === 'Enter') handler(); };
        });
    },

    async submitDock() {
        const mol = this.root.querySelector('#mol-input').value.trim();
        const target = this.root.querySelector('#target-select').value;
        const exh = parseInt(this.root.querySelector('#exh-range').value);
        const btn = this.root.querySelector('#dock-btn');
        const loading = this.root.querySelector('#loading-msg');
        const errorBox = this.root.querySelector('#error-box');

        if (!mol) { errorBox.innerHTML = '<div class="error-box">Enter a molecule.</div>'; return; }

        btn.disabled = true;
        loading.style.display = 'inline';
        errorBox.innerHTML = '';

        try {
            const data = await API.dock(mol, target, exh);
            location.hash = `#/result/${data.result_id}`;
        } catch (e) {
            errorBox.innerHTML = `<div class="error-box">${e.message}</div>`;
        } finally {
            btn.disabled = false;
            loading.style.display = 'none';
        }
    },

    async showResult(id) {
        document.title = 'DrugForge — Result';
        this.root.innerHTML = '<div class="loading">Loading result...</div>';

        let data;
        try {
            data = await API.getResult(id);
        } catch (e) {
            this.root.innerHTML = `
                <div class="card">
                    <h2>Result Not Found</h2>
                    <p>This result may have expired or the ID is invalid.</p>
                    <div class="actions"><a href="#/" class="btn">New Screening</a></div>
                </div>`;
            return;
        }

        const verdict = data.verdict || 'Unknown';
        const badgeClass = verdict.toLowerCase().replace(' ', '');
        const affinity = data.affinity_kcal_mol?.toFixed(2) || 'N/A';
        const vinardo = data.vinardo_score?.toFixed(2) || 'N/A';
        const consensus = data.consensus_score?.toFixed(3) || 'N/A';

        const funnel = this.renderFunnel(data);
        const comparison = this.renderComparison(data.comparisons || []);
        const admetHtml = this.renderAdmet(data.admet || {}, data.is_hit);
        const explanationHtml = this.renderExplanation(data.explanation);

        this.root.innerHTML = `
            <div class="card">
                <div style="display:flex;align-items:center;gap:1rem;flex-wrap:wrap">
                    <h1 style="margin:0">Result</h1>
                    <span class="badge badge-${badgeClass}">${verdict}</span>
                </div>
                <p style="color:var(--text-muted);margin-top:0.5rem">
                    ${data.molecule_smiles} → ${data.target_id}
                </p>
                <div style="margin-top:1rem;display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:1rem;">
                    <div><strong>Vina</strong><br>${affinity} kcal/mol</div>
                    <div><strong>Vinardo</strong><br>${vinardo} kcal/mol</div>
                    <div><strong>Consensus</strong><br>${consensus}</div>
                    <div><strong>Hit</strong><br>${data.is_hit ? '✓ Yes' : '✗ Filtered'}</div>
                </div>
            </div>

            <div class="card">
                <h2>Pipeline Funnel</h2>
                <ul class="funnel">${funnel}</ul>
            </div>

            <div class="card">
                <h2>3D Binding Pose</h2>
                <div class="viewer-container" id="viewer-3d"
                     aria-label="Interactive 3D view of docked molecule in protein pocket"></div>
            </div>

            <div class="card">
                <h2>Comparison to Reference</h2>
                ${comparison}
            </div>

            <div class="card">
                <h2>ADMET Profile</h2>
                ${admetHtml}
            </div>

            ${explanationHtml}

            <div class="actions">
                <a href="${API.reportUrl(id)}" class="btn" download>Download PDF</a>
                <button class="btn btn-sm" onclick="navigator.clipboard.writeText(location.href)">Copy Link</button>
                <a href="#/" class="btn btn-sm" style="background:var(--text-muted)">New Screening</a>
            </div>
        `;

        if (data.pose_sdf) {
            const viewer = $3Dmol.createViewer('viewer-3d', { backgroundColor: 'white' });
            viewer.addModel(data.pose_sdf, 'sdf');
            viewer.setStyle({}, { stick: { colorscheme: 'Jmol' } });
            viewer.zoomTo();
            viewer.render();
        }
    },

    renderFunnel(data) {
        const admet = data.admet || {};
        const boltz = data.boltz;
        const stages = [
            { name: 'Vina Docking', value: `${data.affinity_kcal_mol?.toFixed(2)} kcal/mol`, pass: true },
            { name: 'Vinardo Rescore', value: `${data.vinardo_score?.toFixed(2)} kcal/mol`, pass: true },
            { name: 'Consensus', value: data.consensus_score?.toFixed(3), pass: true },
            { name: 'Drug-likeness', value: `${data.drug_likeness?.lipinski_violations || 0} violations`, pass: (data.drug_likeness?.lipinski_violations || 0) <= 1 },
            { name: 'ADMET/Tox', value: admet.passes_filter ? 'Clean' : (admet.failure_reasons || []).join('; '), pass: admet.passes_filter !== false },
            { name: 'Boltz-2 AI', value: boltz?.status === 'success' ? `${boltz.predicted_affinity} kcal/mol` : (boltz?.status || 'Not invoked'), pass: boltz?.status === 'success', skip: !boltz || boltz.status !== 'success' },
        ];

        return stages.map(s => {
            const icon = s.skip ? '⏭' : s.pass ? '✅' : '❌';
            return `<li>
                <span class="stage-icon" aria-label="${s.skip ? 'skipped' : s.pass ? 'passed' : 'failed'}">${icon}</span>
                <span class="stage-name">${s.name}</span>
                <span class="stage-value">${s.value}</span>
            </li>`;
        }).join('');
    },

    renderComparison(comparisons) {
        if (!comparisons.length) return '<p>No comparison data.</p>';
        const rows = comparisons.map(c => `
            <tr>
                <td>${c.metric}</td>
                <td>${typeof c.molecule_value === 'number' ? c.molecule_value.toFixed(2) : c.molecule_value}</td>
                <td>${typeof c.reference_value === 'number' ? c.reference_value.toFixed(2) : c.reference_value}</td>
                <td>${typeof c.delta === 'number' ? c.delta.toFixed(2) : c.delta}</td>
                <td>${c.verdict}</td>
            </tr>`).join('');

        return `<table>
            <thead><tr><th>Metric</th><th>Molecule</th><th>Reference</th><th>Delta</th><th>Verdict</th></tr></thead>
            <tbody>${rows}</tbody>
        </table>`;
    },

    renderAdmet(admet, isHit) {
        const pains = (admet.pains_alerts || []).join(', ') || 'None';
        const brenk = (admet.brenk_alerts || []).join(', ') || 'None';
        const reactive = (admet.reactive_groups || []).join(', ') || 'None';
        const reasons = (admet.failure_reasons || []).join('; ') || 'None';

        return `
            <table>
                <tr><td><strong>ESOL logS</strong></td><td>${admet.esol_logs ?? 'N/A'}</td></tr>
                <tr><td><strong>GI Absorption</strong></td><td>${admet.gi_absorption || 'N/A'}</td></tr>
                <tr><td><strong>PAINS</strong></td><td>${pains}</td></tr>
                <tr><td><strong>Brenk</strong></td><td>${brenk}</td></tr>
                <tr><td><strong>Reactive Groups</strong></td><td>${reactive}</td></tr>
                <tr><td><strong>Status</strong></td><td>${isHit ? '<strong style="color:var(--promising)">✓ HIT</strong>' : '<strong style="color:var(--weak)">✗ FILTERED</strong> — ' + reasons}</td></tr>
            </table>
            <p style="margin-top:0.75rem;font-size:0.8rem;color:var(--text-muted)">${admet.disclaimer || ''}</p>
        `;
    },

    renderExplanation(explanation) {
        if (!explanation || explanation.status !== 'success') return '';
        return `
            <div class="card">
                <h2>AI Explanation</h2>
                <p>${explanation.text}</p>
                <p style="margin-top:0.75rem;font-size:0.8rem;color:var(--text-muted);font-style:italic">
                    ${explanation.disclaimer || ''}
                </p>
            </div>`;
    },

    showLibrary() {
        document.title = 'DrugForge — Library';
        const compounds = this.state.compounds;

        const rows = compounds.map(c => `
            <tr>
                <td><strong>${c.compound_name}</strong></td>
                <td><em>${c.plant.scientific_name}</em><br><small>${c.plant.local_name}</small></td>
                <td>${c.traditional_use.disease}</td>
                <td>${c.traditional_use.region}</td>
                <td><button class="btn btn-sm" data-smiles="${c.smiles}">Dock</button></td>
            </tr>
            <tr>
                <td colspan="5">
                    <div class="ethno-record">
                        <span class="label">Traditional Knowledge → Molecular Validation</span><br>
                        <strong>People:</strong> ${c.traditional_use.people}<br>
                        <strong>Preparation:</strong> ${c.traditional_use.preparation} (${c.traditional_use.part_used})<br>
                        <strong>Source:</strong> ${c.source}<br>
                        <small style="color:var(--text-muted)">In-silico prediction. Not clinical evidence.</small>
                    </div>
                </td>
            </tr>
        `).join('');

        this.root.innerHTML = `
            <h1>Ethnobotanical Screening Library</h1>
            <p style="color:var(--text-muted);margin-bottom:1.5rem">
                African medicinal-plant compounds — traditional knowledge bridged to in-silico molecular validation.
            </p>

            <div class="card" style="overflow-x:auto">
                <table>
                    <thead>
                        <tr><th>Compound</th><th>Plant</th><th>Disease</th><th>Region</th><th>Action</th></tr>
                    </thead>
                    <tbody>${rows}</tbody>
                </table>
            </div>

            <div class="card" style="font-size:0.85rem;color:var(--text-muted)">
                <strong>Note:</strong> Every entry cites its ethnobotanical source.
                DrugForge prioritizes candidate molecules — it does not discover or prove drugs.
                All results are computational predictions requiring laboratory validation.
            </div>
        `;

        this.root.querySelectorAll('[data-smiles]').forEach(btn => {
            btn.onclick = () => {
                location.hash = '#/';
                setTimeout(() => {
                    const input = document.querySelector('#mol-input');
                    if (input) input.value = btn.dataset.smiles;
                }, 50);
            };
        });
    }
};

document.addEventListener('DOMContentLoaded', () => App.init());
