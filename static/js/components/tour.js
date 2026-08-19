// Lightweight guided product tour. No dependency. A dimmed overlay with a
// spotlight cut around the target element and a bubble that explains it. Steps
// can be informational (advance with Next) or actions that also advance when
// the user actually clicks or changes the highlighted element. Skip always
// available. The overlay lives on document.body so it survives page repaints,
// and a rAF loop keeps the spotlight glued to its target while things move.
const Tour = {
    steps: [],
    i: -1,
    active: false,
    els: {},
    _raf: null,
    _action: null,
    _onKey: null,

    start(steps) {
        if (this.active) this.end();
        this.steps = (steps || []).slice();
        if (!this.steps.length) return;
        this.active = true;
        this._build();
        this._onKey = (e) => {
            if (e.key === "Escape") this.end();
        };
        document.addEventListener("keydown", this._onKey);
        this.go(0);
        this._loop();
    },

    _build() {
        if (!document.getElementById("tour-style")) {
            const s = document.createElement("style");
            s.id = "tour-style";
            s.textContent = `
            #tour-root{position:fixed;inset:0;z-index:9999;pointer-events:none;font-family:Inter,sans-serif;}
            #tour-spot{position:absolute;border-radius:12px;box-shadow:0 0 0 9999px rgba(9,16,28,.62);transition:left .2s,top .2s,width .2s,height .2s;pointer-events:none;}
            #tour-bubble{position:absolute;width:310px;max-width:calc(100vw - 24px);background:#fff;border-radius:16px;padding:18px;box-shadow:0 12px 44px rgba(0,0,0,.28);pointer-events:auto;}
            #tour-bubble .tour-eyebrow{font-size:11px;letter-spacing:.08em;text-transform:uppercase;color:#00478d;font-weight:700;margin-bottom:6px;}
            #tour-bubble .tour-title{font-size:16px;font-weight:600;color:#191c1e;margin-bottom:4px;}
            #tour-bubble .tour-body{font-size:14px;line-height:1.55;color:#43474b;}
            #tour-bubble .tour-hint{margin-top:10px;font-size:13px;color:#00478d;background:#eef4fb;border:1px solid #cfe0f2;border-radius:10px;padding:8px 10px;}
            #tour-bubble .tour-foot{display:flex;align-items:center;justify-content:space-between;margin-top:14px;gap:8px;}
            #tour-bubble .tour-dots{display:flex;gap:5px;}
            #tour-bubble .tour-dots i{width:6px;height:6px;border-radius:9px;background:#d5dbe1;transition:all .2s;}
            #tour-bubble .tour-dots i.on{background:#00478d;width:16px;}
            #tour-bubble .tour-btns{display:flex;gap:8px;}
            #tour-bubble button{font-size:13px;font-weight:600;border-radius:10px;padding:7px 13px;cursor:pointer;border:1px solid transparent;transition:background .15s;}
            #tour-bubble .t-skip{background:none;color:#70757a;padding:7px 4px;}
            #tour-bubble .t-skip:hover{color:#191c1e;}
            #tour-bubble .t-back{background:#fff;border-color:#d5dbe1;color:#43474b;}
            #tour-bubble .t-back:hover{background:#f2f4f7;}
            #tour-bubble .t-next{background:#00478d;color:#fff;}
            #tour-bubble .t-next:hover{background:#00325f;}`;
            document.head.appendChild(s);
        }
        const o = document.createElement("div");
        o.id = "tour-root";
        o.innerHTML = `<div id="tour-spot"></div><div id="tour-bubble"></div>`;
        document.body.appendChild(o);
        this.els.root = o;
        this.els.spot = o.querySelector("#tour-spot");
        this.els.bubble = o.querySelector("#tour-bubble");
    },

    go(i) {
        if (i < 0) return;
        if (i >= this.steps.length) return this.end();
        this.i = i;
        const step = this.steps[i];
        const last = i === this.steps.length - 1;
        const dots = this.steps.map((_, k) => `<i class="${k === i ? "on" : ""}"></i>`).join("");
        const hint = step.action
            ? `<div class="tour-hint">${step.action === "change" ? "Choose from the highlighted menu" : "Click the highlighted element"}${step.hint ? " to " + step.hint : ""}, or press Next.</div>`
            : "";
        this.els.bubble.innerHTML = `
            <div class="tour-eyebrow">Guide &middot; ${i + 1}/${this.steps.length}</div>
            ${step.title ? `<div class="tour-title">${step.title}</div>` : ""}
            <div class="tour-body">${step.text}</div>
            ${hint}
            <div class="tour-foot">
                <div class="tour-dots">${dots}</div>
                <div class="tour-btns">
                    <button class="t-skip" onclick="Tour.end()">Skip</button>
                    ${i > 0 ? `<button class="t-back" onclick="Tour.prev()">Back</button>` : ""}
                    <button class="t-next" onclick="Tour.next()">${last ? "Done" : "Next"}</button>
                </div>
            </div>`;
        this._detachAction();
        if (step.action) this._attachAction(step);
        this._position();
    },

    next() {
        this.go(this.i + 1);
    },
    prev() {
        this.go(this.i - 1);
    },

    _attachAction(step) {
        const type = step.action === "change" ? "change" : "click";
        this._action = {
            type,
            fn: (e) => {
                if (e.target.closest && e.target.closest(step.selector)) {
                    setTimeout(() => this.next(), type === "change" ? 180 : 60);
                }
            },
        };
        document.addEventListener(type, this._action.fn, true);
    },
    _detachAction() {
        if (this._action) {
            document.removeEventListener(this._action.type, this._action.fn, true);
            this._action = null;
        }
    },

    _loop() {
        if (!this.active) return;
        this._position();
        this._raf = requestAnimationFrame(() => this._loop());
    },

    _position() {
        const step = this.steps[this.i];
        const spot = this.els.spot;
        const bubble = this.els.bubble;
        if (!step || !spot || !bubble) return;
        let rect = null;
        if (step.selector) {
            const el = document.querySelector(step.selector);
            if (el) rect = el.getBoundingClientRect();
        }
        if (rect && rect.width) {
            const pad = 6;
            spot.style.left = rect.left - pad + "px";
            spot.style.top = rect.top - pad + "px";
            spot.style.width = rect.width + pad * 2 + "px";
            spot.style.height = rect.height + pad * 2 + "px";
            const bw = bubble.offsetWidth;
            const bh = bubble.offsetHeight;
            let top = rect.bottom + 12;
            if (top + bh > window.innerHeight - 8) top = Math.max(8, rect.top - bh - 12);
            let left = Math.min(Math.max(8, rect.left), window.innerWidth - bw - 8);
            bubble.style.transform = "none";
            bubble.style.left = left + "px";
            bubble.style.top = top + "px";
        } else {
            // No target: fully dim and centre the bubble.
            spot.style.left = "50%";
            spot.style.top = "50%";
            spot.style.width = "0px";
            spot.style.height = "0px";
            bubble.style.left = "50%";
            bubble.style.top = "50%";
            bubble.style.transform = "translate(-50%,-50%)";
        }
    },

    end() {
        this.active = false;
        if (this._raf) cancelAnimationFrame(this._raf);
        this._detachAction();
        if (this._onKey) document.removeEventListener("keydown", this._onKey);
        if (this.els.root) this.els.root.remove();
        this.els = {};
        this.i = -1;
    },
};
