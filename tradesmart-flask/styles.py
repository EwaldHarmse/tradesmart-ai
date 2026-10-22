"""
TradeSmart AI - the whole stylesheet, stored as a Python string constant
instead of a separate .css file.

Same reasoning as templates_content.py: this is still one, plain,
hand-written CSS file - nothing about the rules themselves changed -
just where the text lives. static/css/style.css used to be served by
Flask's automatic static-file handler; now app.py serves this exact
string at /assets/style.css via an ordinary route (see style_css() in
app.py), with the right Content-Type set explicitly. Browsers can't
tell the difference: it's requested once, cached like any stylesheet,
and behaves identically either way.
"""

STYLE_CSS = """\
/* =========================================================================
   TradeSmart AI — hand-written stylesheet (no build step required).

   This replaces the original Tailwind CSS + Framer Motion setup from the
   React version with plain, ordinary CSS: one file, semantic class names,
   readable rules. The visual design (colours, the "liquid glass" panels,
   the pricing watermark, the shiny gradient headline) is carried over
   as-is; the various fade/slide entrances that used to run through the
   Framer Motion JavaScript library now run as CSS `@keyframes` instead.
   ========================================================================= */

@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap');

:root {
  --color-brand: #3D81E3;
  --font-sans: 'Inter', system-ui, sans-serif;
  --bg: #0c0c0c;
}

* { box-sizing: border-box; }

html, body {
  font-family: var(--font-sans);
  -webkit-font-smoothing: antialiased;
  margin: 0;
  padding: 0;
}

.page-body {
  position: relative;
  min-height: 100vh;
  overflow-x: hidden;
  background: var(--bg);
  color: #fff;
}

::selection { background-color: rgba(61, 129, 227, 0.3); }

a { color: inherit; text-decoration: none; }
button { font-family: inherit; cursor: pointer; }
ul { list-style: none; margin: 0; padding: 0; }

/* ---------- background layer (video + ambient fallback) ---------- */
.bg-layer {
  position: fixed;
  inset: 0;
  z-index: 0;
  pointer-events: none;
  overflow: hidden;
  background: var(--bg);
}
.ambient-bg {
  position: absolute;
  inset: 0;
  background: radial-gradient(ellipse 80% 60% at 50% 30%, rgba(20, 60, 140, 0.35), transparent 70%), var(--bg);
}
.bg-video {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  object-fit: cover;
  pointer-events: none;
}

.divider {
  display: none;
  position: fixed;
  top: 0;
  bottom: 0;
  width: 1px;
  background: rgba(255, 255, 255, 0.1);
  pointer-events: none;
  z-index: 5;
}
.divider-left { left: calc(50% - 36rem); }
.divider-right { left: calc(50% + 36rem); }
@media (min-width: 768px) {
  .divider { display: block; }
}

/* ---------- liquid glass (used by the chat card, result card, etc.) ---------- */
.liquid-glass,
.chat-card,
.result-card,
.input,
.final-cta__card {
  background: rgba(255, 255, 255, 0.01);
  background-blend-mode: luminosity;
  backdrop-filter: blur(4px);
  -webkit-backdrop-filter: blur(4px);
  border: none;
  box-shadow: inset 0 1px 1px rgba(255, 255, 255, 0.1);
  position: relative;
  overflow: hidden;
}
.liquid-glass::before,
.chat-card::before,
.result-card::before,
.final-cta__card::before {
  content: '';
  position: absolute;
  inset: 0;
  border-radius: inherit;
  padding: 1.4px;
  background: linear-gradient(180deg,
    rgba(255,255,255,0.45) 0%, rgba(255,255,255,0.15) 20%,
    rgba(255,255,255,0) 40%, rgba(255,255,255,0) 60%,
    rgba(255,255,255,0.15) 80%, rgba(255,255,255,0.45) 100%);
  -webkit-mask: linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0);
  -webkit-mask-composite: xor;
  mask-composite: exclude;
  pointer-events: none;
}

/* ---------- entrance animations (replace Framer Motion) ---------- */
@keyframes fadeUp {
  from { opacity: 0; transform: translateY(20px); }
  to   { opacity: 1; transform: translateY(0); }
}
@keyframes fadeIn {
  from { opacity: 0; transform: translateY(10px); }
  to   { opacity: 1; transform: translateY(0); }
}
.fade-up {
  opacity: 0;
  animation: fadeUp 0.8s cubic-bezier(0.22, 1, 0.36, 1) forwards;
}
.fade-in {
  opacity: 0;
  animation: fadeIn 0.35s cubic-bezier(0.2, 0.8, 0.2, 1) forwards;
}

@keyframes shiny {
  0% { background-position: -200% center; }
  100% { background-position: 200% center; }
}
.animate-shiny { animation: shiny 6s linear infinite; }

/* =========================================================================
   Layout sections
   ========================================================================= */
section, nav, .menu-strip, .live-demo, .final-cta {
  position: relative;
  z-index: 10;
}

.hero, .live-demo, .final-cta {
  max-width: 72rem;
  margin: 0 auto;
  padding-left: 1.5rem;
  padding-right: 1.5rem;
}

/* ---------- buttons ---------- */
.btn {
  display: inline-flex; align-items: center; justify-content: center; gap: 0.5rem;
  border-radius: 9999px; font-size: 0.875rem; font-weight: 500;
  padding: 0.75rem 1.5rem; border: none; transition: all 0.2s;
}
.btn:active { transform: scale(0.98); }
.btn--white { background: #fff; color: #000; }
.btn--white:hover { background: rgba(255,255,255,0.9); }
.btn--ghost { background: transparent; color: rgba(255,255,255,0.7); }
.btn--ghost:hover { color: #fff; }
.btn--block { width: 100%; padding-top: 0.875rem; padding-bottom: 0.875rem; font-size: 1rem; }
.btn--block:hover { transform: translateY(-2px); }
.btn--sm { padding: 0.45rem 1rem; font-size: 0.8rem; }
.btn[disabled] { opacity: 0.4; cursor: not-allowed; }

.icon { width: 1rem; height: 1rem; }
.icon--tiny { width: 0.875rem; height: 0.875rem; }

/* ---------- hero ---------- */
.hero {
  padding-top: 4rem; padding-bottom: 5rem;
  text-align: center;
  display: flex; flex-direction: column; align-items: center;
}
.hero__title {
  font-size: 2.5rem; font-weight: 600; letter-spacing: -0.02em; line-height: 0.9; margin: 0;
}
.hero__title-line { display: block; color: #fff; }
.hero__title-line--shiny {
  background-image: linear-gradient(to right, #091020 0%, #0B2551 12.5%, #A4F4FD 32.5%, #00d2ff 50%, #0B2551 67.5%, #091020 87.5%, #091020 100%);
  background-size: 200% auto;
  -webkit-background-clip: text; background-clip: text;
  color: transparent; -webkit-text-fill-color: transparent;
  filter: url(#c3-noise);
  animation: shiny 6s linear infinite;
}
.hero__lead { margin-top: 2rem; color: rgba(255,255,255,0.6); max-width: 28rem; font-size: 1rem; line-height: 1.5; }
.hero__actions { margin-top: 2rem; display: flex; flex-direction: column; align-items: center; gap: 0.75rem; }
@media (min-width: 768px) {
  .hero { padding-top: 7rem; }
  .hero__title { font-size: 4.5rem; }
}

/* ---------- menu bar strip ---------- */
.menu-strip {
  width: 100%; height: 2.5rem;
  background: rgba(0,0,0,0.4); backdrop-filter: blur(6px);
  border-top: 1px solid rgba(255,255,255,0.1); border-bottom: 1px solid rgba(255,255,255,0.1);
}
.menu-strip__inner {
  max-width: 72rem; margin: 0 auto; padding: 0 1.5rem; height: 100%;
  display: flex; align-items: center; justify-content: space-between; font-size: 0.75rem;
}
.menu-strip__left { display: flex; align-items: center; gap: 1rem; }
.menu-strip__brand { font-weight: 700; color: #fff; }
.menu-strip__right { display: flex; align-items: center; gap: 1rem; color: rgba(255,255,255,0.7); }

/* ---------- live demo window ---------- */
/* The chat card is what actually needs to be ~15% bigger, but it lives in
   the right-hand column of a 2-col grid, so widening the card alone does
   nothing until the column itself has room to give - hence live-demo gets
   its own, wider max-width (72rem * 1.15) instead of sharing the 72rem
   used by the other sections. */
.live-demo { padding-top: 4rem; padding-bottom: 4rem; max-width: 83rem; }
.live-demo__window {
  border-radius: 1rem; overflow: hidden;
  border: 1px solid rgba(255,255,255,0.1);
  background: rgba(14,16,20,0.9); backdrop-filter: blur(24px);
}
.live-demo__titlebar {
  position: relative; display: flex; align-items: center; height: 2.5rem; padding: 0 1rem;
  border-bottom: 1px solid rgba(255,255,255,0.1);
}
.live-demo__dots { display: flex; align-items: center; gap: 0.5rem; }
.dot { width: 0.75rem; height: 0.75rem; border-radius: 9999px; }
.dot--red { background: #ff5f57; }
.dot--yellow { background: #febc2e; }
.dot--green { background: #28c840; }
.live-demo__title {
  position: absolute; left: 50%; transform: translateX(-50%);
  font-size: 0.75rem; color: rgba(255,255,255,0.5);
}
.live-demo__body {
  display: grid; gap: 2.5rem; align-items: center; padding: 2rem; min-height: 600px;
}
.live-demo__heading { margin-top: 1.25rem; font-size: 1.875rem; font-weight: 600; letter-spacing: -0.02em; line-height: 1.05; }
.live-demo__text { margin-top: 1.5rem; color: rgba(255,255,255,0.6); max-width: 28rem; font-size: 1rem; line-height: 1.6; }
.live-demo__list { margin-top: 1.5rem; }
.live-demo__list li {
  display: flex; align-items: center; gap: 0.6rem;
  font-size: 0.875rem; color: rgba(255,255,255,0.6); margin-bottom: 0.5rem;
}
.live-demo__list li::before {
  content: ''; flex-shrink: 0; width: 0.375rem; height: 0.375rem;
  border-radius: 9999px; background: rgba(255,255,255,0.5);
}
.live-demo__chat-wrap { display: flex; justify-content: center; }
@media (min-width: 768px) {
  .live-demo__body { grid-template-columns: 1fr 1fr; padding: 3.5rem; }
  .live-demo__heading { font-size: 2.25rem; }
  .live-demo__chat-wrap { justify-content: flex-end; }
}

/* =========================================================================
   Chat demo
   ========================================================================= */
.chat-card {
  width: 100%; max-width: 48rem; border-radius: 1.5rem; overflow: hidden; color: rgba(255,255,255,0.7);
}
.chat-card__header { display: flex; align-items: center; gap: 0.75rem; border-bottom: 1px solid rgba(255,255,255,0.1); padding: 1.25rem 1.75rem; }
.chat-card__title { font-size: 1.125rem; font-weight: 500; color: #fff; line-height: 1; }
.chat-card__status { margin-top: 0.5rem; display: flex; align-items: center; gap: 0.5rem; font-size: 0.875rem; opacity: 0.6; }

.ping { position: relative; display: inline-flex; width: 0.5rem; height: 0.5rem; }
.ping__ring {
  position: absolute; inset: 0; border-radius: 9999px; background: rgba(255,255,255,0.6);
  animation: ping 1.4s cubic-bezier(0, 0, 0.2, 1) infinite;
}
.ping__dot { position: relative; display: inline-flex; width: 0.5rem; height: 0.5rem; border-radius: 9999px; background: #fff; }
@keyframes ping {
  0% { transform: scale(1); opacity: 1; }
  75%, 100% { transform: scale(2.2); opacity: 0; }
}

.chat-card__progress { padding: 1rem 1.75rem 0; }
.progress-track { height: 0.375rem; width: 100%; overflow: hidden; border-radius: 9999px; background: rgba(255,255,255,0.1); }
.progress-fill { height: 100%; border-radius: 9999px; background: #fff; transition: width 0.5s cubic-bezier(0.2, 0.8, 0.2, 1); }
.progress-labels { margin-top: 0.5rem; display: flex; justify-content: space-between; font-size: 0.75rem; opacity: 0.5; }

.chat-card__messages {
  display: flex; flex-direction: column; gap: 1rem;
  max-height: 505px; min-height: 460px; overflow-y: auto;
  padding: 1.5rem 1.75rem; text-align: left;
}
.msg-row { display: flex; flex-shrink: 0; }
.msg-row--bot { justify-content: flex-start; }
.msg-row--user { justify-content: flex-end; }
.bubble { max-width: 80%; padding: 0.875rem 1.25rem; font-size: 1rem; line-height: 1.6; border-radius: 1rem; }
.bubble--bot { border-bottom-left-radius: 0.25rem; color: rgba(255,255,255,0.8); }
.bubble--user { border-bottom-right-radius: 0.25rem; background: #fff; color: #000; font-weight: 500; }
.bubble--error { background: rgba(239,68,68,0.15); border: 1px solid rgba(248,113,113,0.3); color: #fecaca; border-radius: 1rem; border-bottom-left-radius: 0.25rem; max-width: 85%; }
.bubble--typing { display: flex; align-items: center; gap: 0.4rem; border-bottom-left-radius: 0.25rem; padding: 1rem 1.25rem; }
.typing-dot {
  width: 0.5rem; height: 0.5rem; border-radius: 9999px; background: rgba(255,255,255,0.5);
  animation: typingBounce 1.1s ease-in-out infinite;
}
@keyframes typingBounce {
  0%, 100% { opacity: 0.25; transform: translateY(0); }
  50% { opacity: 1; transform: translateY(-3px); }
}

.chat-card__input-area { border-top: 1px solid rgba(255,255,255,0.1); padding: 1rem 1.5rem; }

.input {
  color: #fff; outline: none; border: none;
}
.input::placeholder { color: rgba(255,255,255,0.4); }
.input--box, .input--box-sm {
  border: 1px solid rgba(255,255,255,0.1); border-radius: 0.5rem; font-size: 0.875rem; text-align: left;
  transition: border-color 0.2s;
}
.input--box:focus, .input--box-sm:focus { border-color: rgba(255,255,255,0.35); }
.input--box { width: 100%; padding: 0.75rem 1rem; }
.input--box-sm { padding: 0.625rem 0.875rem; }
.input--grow { flex: 1; min-width: 0; }
.input--year { width: 6rem; flex: none; }

.vehicle-step { position: relative; }
.vehicle-results {
  /* Solid, not glass: it floats over the chat messages, and the glass
     border (a ::before layer) would scroll along with the list. */
  position: absolute; bottom: 100%; margin-bottom: 0.5rem; left: 0; right: 0; z-index: 10;
  max-height: 14rem; overflow-y: auto; border-radius: 0.5rem; padding: 0.375rem;
  background: #16171b; border: 1px solid rgba(255,255,255,0.12);
  box-shadow: 0 12px 32px rgba(0,0,0,0.5);
  scrollbar-width: thin; scrollbar-color: rgba(255,255,255,0.2) transparent;
}
.vehicle-results::-webkit-scrollbar { width: 6px; }
.vehicle-results::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.2); border-radius: 3px; }
.vehicle-results:empty { display: none; }
.vehicle-results__item {
  display: block; width: 100%; border-radius: 0.5rem; padding: 0.5rem 0.75rem; text-align: left;
  font-size: 0.875rem; color: rgba(255,255,255,0.8); background: transparent; border: none; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}
.vehicle-results__item:hover { background: rgba(255,255,255,0.1); }

.details-step, .deposit-step { display: flex; align-items: center; gap: 0.75rem; }
.condition-step { display: flex; flex-direction: column; gap: 0.625rem; }
.condition-step__row { display: flex; align-items: center; gap: 1rem; font-size: 0.8rem; color: rgba(255,255,255,0.6); padding-left: 0.25rem; }
.condition-step__label { flex: none; }
.radio-pill { display: flex; align-items: center; gap: 0.35rem; font-size: 0.8rem; color: rgba(255,255,255,0.7); }
.radio-pill input { width: 0.875rem; height: 0.875rem; accent-color: #fff; }
.condition-step__actions { display: flex; justify-content: flex-end; gap: 0.5rem; }
.contact-step { display: flex; flex-direction: column; gap: 0.625rem; }
.contact-step__row { display: flex; align-items: center; gap: 0.75rem; }
.contact-step__consent { display: flex; align-items: center; gap: 0.5rem; padding-left: 0.5rem; font-size: 0.75rem; color: rgba(255,255,255,0.5); }
.consent-checkbox { width: 0.875rem; height: 0.875rem; }
.contact-step__extra { display: none; align-items: center; gap: 0.75rem; }
.contact-step__consent:has(.consent-checkbox:checked) ~ .contact-step__extra { display: flex; }

/* ---------- result card ---------- */
.result-card { border-radius: 0.75rem; padding: 1.75rem; flex-shrink: 0; }
.result-card__warning {
  margin-bottom: 1.25rem; border-radius: 0.5rem; background: rgba(239,68,68,0.15);
  border: 1px solid rgba(248,113,113,0.3); padding: 0.625rem 0.875rem; font-size: 0.75rem; line-height: 1.5; color: #fecaca;
}
.result-card__warning-label { font-weight: 600; }
.result-card__eyebrow { font-size: 0.75rem; font-weight: 500; text-transform: uppercase; letter-spacing: 0.05em; opacity: 0.5; }
.result-card__price {
  margin-top: 0.5rem; font-size: 2.25rem; font-weight: 500; letter-spacing: -0.02em; color: #fff;
  animation: priceIn 0.6s cubic-bezier(0.2, 0.8, 0.2, 1) both;
}
@keyframes priceIn {
  from { opacity: 0; transform: scale(0.92); }
  to   { opacity: 1; transform: scale(1); }
}
.result-card__range { margin-top: 0.5rem; font-size: 0.875rem; font-weight: 400; color: rgba(255,255,255,0.5); }
.result-card__confidence { margin-top: 1.5rem; display: flex; align-items: center; gap: 1.25rem; }
.confidence-ring { width: 5rem; height: 5rem; flex-shrink: 0; }
.confidence-ring__track { stroke: rgba(255,255,255,0.15); }
.confidence-ring__value {
  stroke: #fff;
  animation: ringSweep 1.3s 0.15s cubic-bezier(0.2, 0.8, 0.2, 1) both;
}
@keyframes ringSweep {
  to { stroke-dashoffset: var(--ring-target); }
}
.result-card__confidence-text { font-size: 0.875rem; opacity: 0.6; }
.result-card__confidence-pct { font-weight: 500; color: #fff; }
.result-card__factors { margin-top: 1.5rem; display: flex; flex-wrap: wrap; gap: 0.5rem; }
.factor-chip { border-radius: 9999px; padding: 0.375rem 0.875rem; font-size: 0.875rem; font-weight: 500; color: rgba(255,255,255,0.8); }
.result-card__adjustments {
  margin-top: 1.25rem; border-radius: 0.5rem; background: rgba(255,255,255,0.04);
  border: 1px solid rgba(255,255,255,0.08); padding: 0.875rem 1rem;
}
.result-card__adjustments-label { font-size: 0.8rem; color: rgba(255,255,255,0.7); line-height: 1.5; }
.adjustments-list { margin-top: 0.5rem; display: flex; flex-direction: column; gap: 0.3rem; }
.adjustments-list li { font-size: 0.8rem; color: rgba(255,255,255,0.6); }
.adjustments-list__pct { color: rgba(255,255,255,0.4); }
.result-card__adjustments-note { margin-top: 0.6rem; font-size: 0.7rem; line-height: 1.5; opacity: 0.5; }
.result-card__adjustments-none { margin-top: 1.25rem; font-size: 0.75rem; line-height: 1.5; opacity: 0.5; }
.result-card__disclaimer { margin-top: 1.25rem; font-size: 0.75rem; line-height: 1.5; opacity: 0.5; }
.result-card__db-warning {
  margin-top: 0.75rem; border-radius: 0.5rem; background: rgba(245,158,11,0.15);
  border: 1px solid rgba(251,191,36,0.3); padding: 0.625rem 0.875rem; font-size: 0.75rem; line-height: 1.5; color: #fde68a;
}
.result-card button { margin-top: 1.5rem; }

/* =========================================================================
   Final CTA
   ========================================================================= */
.eyebrow { display: flex; align-items: center; gap: 0.75rem; }
.eyebrow__label { display: inline-flex; align-items: center; gap: 0.5rem; color: rgba(255,255,255,0.7); font-size: 0.875rem; font-weight: 500; }
.eyebrow__dot { width: 0.375rem; height: 0.375rem; border-radius: 9999px; background: #fff; }


.final-cta { padding-top: 5rem; padding-bottom: 5rem; }
.final-cta__card { border-radius: 1.5rem; padding: 4rem 2rem; text-align: center; }
.final-cta__glow {
  position: absolute; inset: 0; pointer-events: none; opacity: 0.3;
  background: radial-gradient(600px circle at 50% 0%, rgba(255,255,255,0.15), transparent 70%);
}
.final-cta__inner { position: relative; }
.final-cta__heading { font-size: 2.5rem; font-weight: 600; letter-spacing: -0.02em; line-height: 1.02; margin: 0; }
.final-cta__text { margin-top: 1.5rem; color: rgba(255,255,255,0.6); max-width: 28rem; margin-left: auto; margin-right: auto; font-size: 0.875rem; line-height: 1.6; }
.final-cta__actions { margin-top: 2.5rem; display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 1rem; }
@media (min-width: 640px) {
  .final-cta__actions { flex-direction: row; }
  .final-cta__card { padding: 6rem 2rem; }
}
@media (min-width: 768px) {
  .final-cta__heading { font-size: 3.75rem; }
}
"""
