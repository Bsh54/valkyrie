// Concept explainer for a reader with no science background. Framing: the
// African plant knowledge comes first. People already know these plants work;
// Valkyrie looks for the molecular reason why, so the knowledge can leave the
// village and become a documented lead others can build on. Plain sans-serif
// typography, full-width layout with a sticky table of contents. Honest wording
// only, no em dashes.
const LearnPage = {
    sections: [
        ["knowledge", "The knowledge came first"],
        ["local", "Why it stayed in the village"],
        ["precedent", "It has happened before"],
        ["why", "What Valkyrie looks for"],
        ["parasite", "What the plant is really fighting"],
        ["molecule", "The molecule, and how a computer reads it"],
        ["docking", "Docking: testing the fit"],
        ["score", "Reading the score"],
        ["medicine", "From a good fit to a real lead"],
        ["ai", "Explained in plain words"],
        ["resource", "A resource others can build on"],
        ["limits", "What this can, and cannot, tell you"],
    ],

    render(mountEl) {
        mountEl.innerHTML = Layout.shell(`
        <div class="w-full max-w-max-width mx-auto px-margin-mobile md:px-margin-desktop">
            ${this.header()}
            <div class="grid lg:grid-cols-[240px_minmax(0,1fr)] gap-10 xl:gap-16 pb-24">
                ${this.toc()}
                <div class="min-w-0">${this.content()}</div>
            </div>
        </div>`);
        window.scrollTo(0, 0);
        this.wireScrollSpy();
    },

    header() {
        return `
        <header class="py-12 md:py-16 border-b border-outline-variant">
            <div class="font-label-caps text-label-caps text-primary uppercase tracking-wider mb-3">A plain-language guide</div>
            <h1 class="text-[32px] md:text-[44px] font-bold leading-[1.1] text-on-surface tracking-tight max-w-4xl">
                The plants already work. We look for the reason why.
            </h1>
            <p class="font-body-lg text-body-lg text-on-surface-variant mt-4 leading-relaxed max-w-3xl">
                No background in biology or chemistry needed. This explains, in order and in plain words, what
                Valkyrie is really about: taking medicinal plants that African communities have trusted for
                generations, and searching for the molecular reason they work, so that knowledge can travel.
            </p>
        </header>`;
    },

    toc() {
        const links = this.sections
            .map(
                ([id, label], i) => `
            <a href="#${id}" data-toc="${id}" class="block px-3 py-2 rounded-lg font-body-sm text-body-sm text-on-surface-variant hover:bg-surface-container-low hover:text-on-surface transition-colors border-l-2 border-transparent">
                <span class="font-code-md text-outline mr-2">${String(i + 1).padStart(2, "0")}</span>${label}
            </a>`
            )
            .join("");
        return `
        <aside class="hidden lg:block">
            <div class="sticky top-24">
                <div class="font-label-caps text-label-caps text-on-surface-variant uppercase mb-3 px-3">Contents</div>
                <nav class="flex flex-col gap-0.5">${links}</nav>
            </div>
        </aside>`;
    },

    h2(id, t) {
        return `<h2 id="${id}" class="scroll-mt-24 text-[24px] md:text-[30px] font-semibold leading-tight text-on-surface">${t}</h2>`;
    },
    p(html) {
        return `<p class="font-body-lg text-body-lg text-on-surface leading-[1.75] mt-4 max-w-[68ch]">${html}</p>`;
    },
    b(t) {
        return `<strong class="font-semibold">${t}</strong>`;
    },
    code(t) {
        return `<code class="font-code-md text-[0.9em] bg-surface-container-low text-primary px-1.5 py-0.5 rounded">${t}</code>`;
    },

    split(id, title, prose, figure) {
        return `
        <section class="py-10 md:py-12 border-t border-outline-variant first:border-t-0">
            ${this.h2(id, title)}
            <div class="grid lg:grid-cols-2 gap-8 lg:gap-12 items-center mt-2">
                <div>${prose}</div>
                <div>${figure}</div>
            </div>
        </section>`;
    },
    block(id, title, prose) {
        return `
        <section class="py-10 md:py-12 border-t border-outline-variant first:border-t-0">
            ${this.h2(id, title)}
            ${prose}
        </section>`;
    },

    content() {
        const b = (t) => this.b(t);
        return `
        ${this.block(
            "knowledge",
            "The knowledge came first",
            this.p(`Long before laboratories existed, communities across Africa learned which plants heal. A
                root that breaks a fever, a bark that settles the gut, a leaf boiled for malaria. This knowledge was
                not guessed. It was earned over generations, watched, corrected and passed down, and it still works
                today in the villages and homes that hold it.`) +
                this.p(`Valkyrie starts from respect for that. The premise is not that the plants might work. It is
                that ${b("they already do")}, and the people who use them know it. The question we ask is a
                different one: ${b("why")}?`)
        )}

        ${this.block(
            "local",
            "Why it stayed in the village",
            this.p(`Knowing that a plant works is not the same as knowing ${b("how")} it works. For most
                traditional remedies, no one has ever pinned down the exact substance in the plant, or the exact
                part of the parasite it acts on. Without that explanation, modern medicine cannot check it, dose it
                safely, or build on it.`) +
                this.p(`So the knowledge stays local. It heals the people nearby, but it never travels, never
                enters a textbook, never becomes a medicine that reaches the next country. A working remedy remains
                invisible to the wider world simply because its reason has never been written down.`)
        )}

        ${this.block(
            "precedent",
            "It has happened before",
            this.p(`This is not a dream. It is the exact path that two of the world's most important medicines
                already walked. ${b("Quinine")} came from the bark of the cinchona tree, a traditional fever
                remedy, before science isolated it and turned it into the first real antimalarial.
                ${b("Artemisinin")}, today a global standard against malaria and worth a Nobel Prize, came straight
                from a plant used in traditional Chinese medicine.`) +
                this.p(`In both cases the sequence was the same: the plant worked first, and worked for a long
                time. Science came later, found the reason, and let the remedy travel the world. Valkyrie tries to
                shorten the first, slowest step of that journey for the plants of Africa.`)
        )}

        ${this.split(
            "why",
            "What Valkyrie looks for",
            this.p(`The reason a plant heals usually comes down to one thing: a substance inside it grabs hold of
                a specific part of whatever is making you sick, and jams it. Find that grip, and you have found the
                ${b("why")}.`) +
                this.p(`That is Valkyrie's whole job. It takes compounds from traditional plants and looks, on the
                computer, for exactly where and how tightly they latch onto the parasite. When it finds a strong
                grip, it has a molecular explanation for a remedy that people already trusted, written in the
                language modern science understands. The rest of this page is simply how it does that.`),
            this.figurePocket()
        )}

        ${this.block(
            "parasite",
            "What the plant is really fighting",
            this.p(`The diseases Valkyrie focuses on, ${b("malaria")}, ${b("Chagas disease")},
                ${b("leishmaniasis")} and ${b("sleeping sickness")}, are all caused by a ${b("parasite")}: a living
                thing far too small to see, that lives inside the body and feeds off it while doing harm. A single
                mosquito bite can inject the malaria parasite into your blood.`) +
                this.p(`Every parasite is run by ${b("proteins")}, tiny machines that keep it alive. Most have a
                small hollow on their surface, a ${b("pocket")}, where they grab what they need to work. Plug that
                pocket and the machine stops. That protein is the ${b("target")}, and its exact shape has already
                been measured by scientists and stored in public databases. This is what a healing plant's molecule
                is quietly doing inside the parasite.`)
        )}

        ${this.block(
            "molecule",
            "The molecule, and how a computer reads it",
            this.p(`A plant is a mixture of many ${b("molecules")}, each one a specific arrangement of atoms. One
                of them is usually the real actor, the substance responsible for the healing. Caffeine is a
                molecule, aspirin is a molecule, and so is the active compound in a medicinal root.`) +
                this.p(`To hand a molecule to a computer, we write it as a short line of text called a
                ${b("SMILES")} string, ${this.code("CCO")} for ordinary alcohol, for instance. It looks cryptic but
                it is just a precise way of spelling out which atoms are joined to which, and it is enough for the
                software to rebuild the whole molecule.`)
        )}

        ${this.block(
            "docking",
            "Docking: testing the fit",
            this.p(`${b("Molecular docking")} is the computer trying to fit the plant's molecule into the
                target's pocket. It turns and nudges it through thousands of positions, looking for the one where it
                sits most comfortably, the best fit. Valkyrie runs this with AutoDock Vina, a real and widely used
                scientific engine, not an animation or a guess. The three dimensional view you see afterwards is the
                exact pose the software settled on.`)
        )}

        ${this.split(
            "score",
            "Reading the score",
            this.p(`Docking scores the best fit with a single number, the ${b("affinity")}, in units called
                kcal/mol. It estimates how strongly the molecule would cling to the pocket. One rule surprises
                people: ${b("more negative is better")}. Minus nine means a tighter grip than minus five, because
                the negative sign just means the molecule releases energy when it binds, which is what makes it hold
                on.`) +
                this.p(`A number alone is easy to misread, so Valkyrie scores each molecule a second way, blends
                the two into a ${b("consensus")}, and compares it against the drug already used for that disease.
                The short summary is the ${b("verdict")}.`),
            this.figureScale()
        )}

        ${this.split(
            "medicine",
            "From a good fit to a real lead",
            this.p(`A strong grip is a beginning, not an ending. A substance can bind beautifully and still fail
                as a medicine, because the body cannot absorb it, or it barely dissolves, or it is simply too big
                for a pill. So after docking, Valkyrie runs more checks, and only what passes every stage earns the
                word ${b("hit")}.`) +
                this.p(`${b("Drug-likeness")} weighs basic properties against the rules most oral drugs obey.
                ${b("ADMET")} asks what the body would do with the substance and whether it is toxic, and a scan
                flags known troublemaker chemical patterns. A molecule has to clear all of it to count as a real
                lead worth chasing.`),
            this.figureFunnel()
        )}

        ${this.block(
            "ai",
            "Explained in plain words",
            this.p(`All of this comes out as a pile of numbers, which is little use to someone who is not a
                specialist, and much of the point here is to make the knowledge accessible. So Valkyrie asks an
                ${b("AI assistant")} to read those numbers back in plain sentences: what the score means, the
                molecule's biggest strength and weakness, and what a researcher might do next. The assistant may
                only reason from the numbers Valkyrie actually computed. It cannot invent facts or claim a plant
                cures anything. It interprets, it does not embellish.`)
        )}

        ${this.block(
            "resource",
            "A resource others can build on",
            this.p(`When Valkyrie finds a plant compound with a strong, well behaved grip on a disease target, it
                has produced something that did not exist before: a written, molecular reason for a traditional
                remedy, with a score, a comparison to a known drug, a 3D pose and a downloadable record.`) +
                this.p(`That is exactly the kind of starting point a laboratory or a research group needs to
                justify testing a plant seriously. Catalogues of African plant compounds already exist. What Valkyrie
                adds on top is the ${b("reasoning")}: not just that a compound exists, but where it might act and
                why, laid out so others can pick it up and carry it further. A remedy that once healed only a village
                becomes a documented lead the wider world can follow.`)
        )}

        ${this.block(
            "limits",
            "What this can, and cannot, tell you",
            this.p(`It is worth being plain about the limits, because honesty is what makes this useful. Valkyrie
                is a very fast first filter. It points to which plant compounds are worth a closer look, which saves
                an enormous amount of time at the start of a long road. But a computer prediction is a hypothesis,
                not a proof. Valkyrie does not discover a drug, prove a cure, or give medical advice. A promising
                score is a reason to test a plant in a real laboratory, and the laboratory always has the last
                word.`) +
                `<div class="mt-8 flex flex-col sm:flex-row gap-4">
                    <a data-link href="/lab" class="bg-primary text-on-primary font-body-md text-body-md px-6 py-3 rounded-xl hover:bg-deep-navy transition-colors font-medium inline-flex items-center justify-center gap-2">
                        See it run in the lab <span class="material-symbols-outlined">arrow_forward</span>
                    </a>
                    <a data-link href="/library" class="bg-surface-container-lowest text-on-surface border border-outline-variant font-body-md text-body-md px-6 py-3 rounded-xl hover:bg-surface-container-low transition-colors font-medium inline-flex items-center justify-center">
                        Browse the plant library
                    </a>
                </div>`
        )}`;
    },

    wireScrollSpy() {
        const links = new Map(
            [...document.querySelectorAll("[data-toc]")].map((el) => [el.getAttribute("data-toc"), el])
        );
        if (!links.size || !("IntersectionObserver" in window)) return;
        const setActive = (id) => {
            links.forEach((el, key) => {
                const on = key === id;
                el.classList.toggle("text-primary", on);
                el.classList.toggle("border-primary", on);
                el.classList.toggle("bg-surface-container-low", on);
                el.classList.toggle("border-transparent", !on);
            });
        };
        const obs = new IntersectionObserver(
            (entries) => {
                const visible = entries.filter((e) => e.isIntersecting).sort((a, b) => a.boundingClientRect.top - b.boundingClientRect.top);
                if (visible[0]) setActive(visible[0].target.id);
            },
            { rootMargin: "-20% 0px -70% 0px" }
        );
        this.sections.forEach(([id]) => {
            const el = document.getElementById(id);
            if (el) obs.observe(el);
        });
    },

    figure(svg, caption) {
        return `
        <figure>
            <div class="bg-surface-container-low border border-outline-variant rounded-2xl p-6 md:p-8 flex justify-center">${svg}</div>
            <figcaption class="font-body-sm text-body-sm text-on-surface-variant mt-3 italic">${caption}</figcaption>
        </figure>`;
    },

    figurePocket() {
        const svg = `
        <svg viewBox="0 0 420 200" width="100%" style="max-width:420px" role="img" aria-label="A plant molecule fitting into a parasite protein pocket">
            <path d="M40 150 Q30 60 120 55 Q150 52 160 80 L175 80 Q185 55 200 55 Q290 55 300 120 Q305 165 250 170 L70 170 Q42 168 40 150 Z"
                  fill="#cfe0f2" stroke="#00478d" stroke-width="2"/>
            <text x="105" y="130" font-family="Inter,sans-serif" font-size="12" fill="#00478d" font-weight="600">parasite protein</text>
            <g transform="translate(163 74)">
                <circle cx="0" cy="0" r="7" fill="#1f8a5b"/>
                <circle cx="14" cy="-4" r="7" fill="#1f8a5b"/>
                <circle cx="7" cy="10" r="7" fill="#1f8a5b"/>
                <line x1="0" y1="0" x2="14" y2="-4" stroke="#1f8a5b" stroke-width="3"/>
                <line x1="0" y1="0" x2="7" y2="10" stroke="#1f8a5b" stroke-width="3"/>
            </g>
            <text x="322" y="70" font-family="Inter,sans-serif" font-size="12" fill="#1f8a5b" font-weight="600">plant molecule</text>
            <path d="M325 74 Q200 60 190 74" fill="none" stroke="#1f8a5b" stroke-width="1.5" stroke-dasharray="3 3"/>
        </svg>`;
        return this.figure(svg, "The plant's molecule acts like a key plugging the parasite's pocket. Finding that grip is the reason we are after.");
    },

    figureScale() {
        const svg = `
        <svg viewBox="0 0 440 130" width="100%" style="max-width:440px" role="img" aria-label="Affinity scale, more negative is stronger">
            <defs><marker id="arr" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0 0 L6 3 L0 6 Z" fill="#00478d"/></marker></defs>
            <line x1="30" y1="70" x2="410" y2="70" stroke="#5b6b7c" stroke-width="2"/>
            ${[["-12", 30], ["-9", 125], ["-6", 220], ["-3", 315], ["0", 410]]
                .map(([lab, x]) => `<line x1="${x}" y1="64" x2="${x}" y2="76" stroke="#5b6b7c" stroke-width="2"/><text x="${x}" y="92" font-family="JetBrains Mono,monospace" font-size="11" fill="#5b6b7c" text-anchor="middle">${lab}</text>`)
                .join("")}
            <line x1="250" y1="40" x2="60" y2="40" stroke="#00478d" stroke-width="2" marker-end="url(#arr)"/>
            <text x="255" y="44" font-family="Inter,sans-serif" font-size="12" fill="#00478d" font-weight="600">stronger binding</text>
            <circle cx="125" cy="70" r="5" fill="#1f8a5b"/><text x="125" y="118" font-family="Inter,sans-serif" font-size="11" fill="#1f8a5b" text-anchor="middle" font-weight="600">plant compound</text>
            <circle cx="220" cy="70" r="5" fill="#b26a00"/><text x="220" y="118" font-family="Inter,sans-serif" font-size="11" fill="#b26a00" text-anchor="middle" font-weight="600">reference drug</text>
        </svg>`;
        return this.figure(svg, "Affinity in kcal/mol. The further left, the tighter the grip. Here the plant compound outbinds the reference drug.");
    },

    figureFunnel() {
        const stages = [
            ["Docking", 360, "#00478d"],
            ["Rescore + consensus", 300, "#1f6fc0"],
            ["Drug-likeness", 230, "#2f8fd0"],
            ["ADMET + toxicity", 160, "#4aa3d8"],
            ["Lead", 95, "#1f8a5b"],
        ];
        const rows = stages
            .map(([label, w, c], i) => {
                const x = (420 - w) / 2;
                const y = 10 + i * 34;
                return `<rect x="${x}" y="${y}" width="${w}" height="26" rx="6" fill="${c}"/><text x="210" y="${y + 17}" font-family="Inter,sans-serif" font-size="12" fill="#ffffff" text-anchor="middle" font-weight="600">${label}</text>`;
            })
            .join("");
        const svg = `<svg viewBox="0 0 420 190" width="100%" style="max-width:420px" role="img" aria-label="Screening funnel">${rows}</svg>`;
        return this.figure(svg, "Every plant compound passes through the same funnel. Only what survives each stage becomes a documented lead.");
    },
};
