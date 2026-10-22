// TradeSmart AI poster, dark dashboard style - one A1 portrait slide.
// Every number comes from the project's outputs.
const fs = require("fs");
const path = require("path");
const pptxgen = require("pptxgenjs");

const FINAL = path.resolve(__dirname, "..", "..");  // project root
const ML = `${FINAL}/tradesmart-ml`;
const OUT = `${FINAL}/documentation/TradeSmart_AI_Poster.pptx`;
const J = (f) => JSON.parse(fs.readFileSync(f, "utf8"));
const cmp = J(`${ML}/outputs/model_comparison.json`).test_results;
const ts = J(`${ML}/outputs/time_series_analysis.json`);
const nlp = J(`${ML}/outputs/nlp_intent_classifier_report.json`);
const X = J(path.join(__dirname, "extra.json"));
const PX = J(path.join(__dirname, "poster_extra.json"));
const S80 = J(`${ML}/outputs/split_experiments.json`).split_ratio.find((r) => r.train_pct === 80);  // average of 5 random 80/20 splits

// ---------- style ----------
const LIGHT = "Segoe UI Light", BODY = "Segoe UI", BOLD = "Segoe UI Semibold";
const WHITE = "F2F2F2", SECOND = "A3A3A8", MUTED = "6A6A70", FAINT = "45454A";
const CARD = "161618", CARD_LINE = "2C2C30", PANEL = "0F0F11", PANEL_LINE = "242427", CHIP = "2E2E32", BAR_GREY = "5C5C61", BAR_DARK = "2A2A2E";
const rand = (n) => "R" + Math.round(n).toLocaleString("en-ZA").replace(/[,\u00a0]/g, " ");
const pct = (x, d = 1) => (100 * x).toFixed(d) + "%";

const W = 23.39, H = 33.11, M = 1.0;
const pres = new pptxgen();
pres.defineLayout({ name: "A1_PORTRAIT", width: W, height: H });
pres.layout = "A1_PORTRAIT";
pres.title = "TradeSmart AI - Poster";
pres.theme = { headFontFace: LIGHT, bodyFontFace: BODY };
const s = pres.addSlide();
s.background = { path: path.join(__dirname, "poster_bg.jpg") };

let n = 0;
const T = (t, o) => s.addText(t, { isTextBox: true, fontFace: BODY, color: WHITE, margin: 0, valign: "top", objectName: o.objectName || `Text ${++n}`, ...o });
const label = (t, x, y, w, o = {}) => T(t.toUpperCase(), { x, y, w, h: 0.4, fontSize: 15, fontFace: BOLD, color: SECOND, charSpacing: 2, ...o });
const box = (x, y, w, h, fill, line, r, name) => s.addShape(pres.shapes.ROUNDED_RECTANGLE,
  { x, y, w, h, fill: { color: fill }, line: { color: line, width: 1 }, rectRadius: r, objectName: name });
const chip = (t, x, y, name) => {
  const w = 0.16 * t.length + 0.6;
  box(x, y, w, 0.5, CHIP, CHIP, 0.08, `${name} chip`);
  T(t.toUpperCase(), { x, y, w, h: 0.5, fontSize: 13, fontFace: BOLD, color: "D6D6DA", charSpacing: 1.5, align: "center", valign: "middle", objectName: `${name} chip text` });
  return w;
};
const dot = (x, y, on, name) => s.addShape(pres.shapes.OVAL, { x, y, w: 0.22, h: 0.22,
  fill: { color: on ? WHITE : CARD }, line: { color: on ? WHITE : FAINT, width: 1.5 }, objectName: name });

// ---------- top bar ----------
T("TradeSmart AI", { x: M, y: 0.9, w: 8, h: 0.7, fontSize: 32, fontFace: BOLD, objectName: "Wordmark" });
T("Business Analysis 3.2   ·   Vaal University of Technology   ·   2026", {
  x: W - M - 12, y: 1.0, w: 12, h: 0.5, fontSize: 18, color: SECOND, align: "right", objectName: "Course line" });

// ---------- hero ----------
const chipText = "16 453 listings · 2 393 models · 2018–2023";
const chipW = 0.16 * chipText.length + 0.6;
box((W - chipW) / 2, 2.7, chipW, 0.55, "1C1C1F", "38383C", 0.08, "Hero chip");
T(chipText.toUpperCase(), { x: (W - chipW) / 2, y: 2.7, w: chipW, h: 0.55, fontSize: 14, fontFace: BOLD, color: "CFCFD3",
  charSpacing: 1.5, align: "center", valign: "middle", objectName: "Hero chip text" });
T([{ text: "Clarity on every", options: { breakLine: true } }, { text: "trade-in you value", options: { color: "BDBDC2" } }], {
  x: M, y: 3.55, w: W - 2 * M, h: 3.9, fontSize: 118, fontFace: LIGHT, align: "center", lineSpacingMultiple: 0.95, objectName: "Headline" });
T("TradeSmart AI gives South African used-car dealerships an instant, data-driven market value for every trade-in, without the guesswork.", {
  x: 4.2, y: 7.6, w: W - 8.4, h: 1.2, fontSize: 26, color: SECOND, align: "center", objectName: "Subheadline" });
const PILL_Y = 9.1, PILL_H = 0.85;
box(W / 2 - 6.4, PILL_Y, 6.0, PILL_H, WHITE, WHITE, 0.08, "Pill 1");
T("An AI Solution for Industries", { x: W / 2 - 6.4, y: PILL_Y, w: 6.0, h: PILL_H, fontSize: 20, fontFace: BOLD, color: "111113", align: "center", valign: "middle", objectName: "Pill 1 text" });
box(W / 2 + 0.4, PILL_Y, 6.0, PILL_H, "111113", "3A3A3E", 0.08, "Pill 2");
T("XGBoost · NLP · Deep learning", { x: W / 2 + 0.4, y: PILL_Y, w: 6.0, h: PILL_H, fontSize: 20, fontFace: BOLD, align: "center", valign: "middle", objectName: "Pill 2 text" });

// ---------- dashboard panel ----------
const PY = 10.55, PAD = 0.5, GAP = 0.4;
const ROW = [6.1, 6.9, 3.3];
const PH = PAD * 2 + ROW.reduce((a, b) => a + b, 0) + GAP * (ROW.length - 1);
box(M, PY, W - 2 * M, PH, PANEL, PANEL_LINE, 0.35, "Dashboard panel");
const IX = M + PAD, IW = W - 2 * M - 2 * PAD, CW = (IW - 2 * GAP) / 3;
const col = (i) => IX + i * (CW + GAP);
const rowY = (r) => PY + PAD + ROW.slice(0, r).reduce((a, b) => a + b, 0) + GAP * r;
const card = (c, r, name, span = 1) => {
  const w = CW * span + GAP * (span - 1);
  box(col(c), rowY(r), w, ROW[r], CARD, CARD_LINE, 0.25, name);
  return { x: col(c) + 0.45, y: rowY(r) + 0.45, w: w - 0.9, h: ROW[r] - 0.9 };
};

// A: live valuation
let k = card(0, 0, "Valuation card");
dot(k.x, k.y + 0.09, true, "Valuation live dot");
label("Live valuation", k.x + 0.4, k.y, k.w - 0.4);
T("2019 VW Polo Vivo 1.4 Trendline · 85 000 km", { x: k.x, y: k.y + 0.7, w: k.w, h: 0.45, fontSize: 17, color: SECOND });
T(rand(PX.polo.point_estimate), { x: k.x, y: k.y + 1.25, w: k.w, h: 1.2, fontSize: 64, fontFace: LIGHT, objectName: "Valuation number" });
chip(PX.polo.spec_source === "exact_model" ? "Exact model match" : "Brand average", k.x, k.y + 2.6, "Valuation");
T(`Range ${rand(PX.polo.estimated_low)} – ${rand(PX.polo.estimated_high)}`, { x: k.x, y: k.y + 3.25, w: k.w, h: 0.45, fontSize: 17, color: MUTED });
[[true, `Estimate in ${X.speed_median_ms} ms`], [false, "Saved to SQL Server"], [false, "Logged to Excel"]].forEach(([on, t], i) => {
  dot(k.x, k.y + 3.95 + i * 0.5 + 0.08, on, `Valuation step dot ${i + 1}`);
  T(t.toUpperCase(), { x: k.x + 0.4, y: k.y + 3.95 + i * 0.5, w: k.w - 0.4, h: 0.4, fontSize: 14, fontFace: BOLD, color: on ? WHITE : MUTED, charSpacing: 1.5 });
});

// B: model accuracy
k = card(1, 0, "Accuracy card");
label("Model accuracy", k.x, k.y, k.w);
const acc = [[pct(S80.R2.mean), "R² explained"], [pct(S80.within_15pct.mean), "within ±15%"], [`R${Math.round(S80.MAE.mean / 1000)}k`, "avg error"]];
const aw = k.w / 3;
acc.forEach(([v, t], i) => {
  T(v, { x: k.x + i * aw, y: k.y + 0.8, w: aw, h: 1.0, fontSize: 42, fontFace: LIGHT });
  T(t, { x: k.x + i * aw, y: k.y + 1.8, w: aw, h: 0.45, fontSize: 17, color: SECOND });
});
const segY = k.y + 2.75, segH = 0.75;
const BAND_10 = S80.within_10pct.mean, BAND_10_15 = S80.within_15pct.mean - S80.within_10pct.mean, BAND_OVER = 1 - S80.within_15pct.mean;
const segs = [[BAND_10, WHITE], [BAND_10_15, BAR_GREY], [BAND_OVER, BAR_DARK]];
let sx = k.x;
segs.forEach(([f, c], i) => {
  const w = k.w * f - (i < 2 ? 0.08 : 0);
  s.addShape(pres.shapes.RECTANGLE, { x: sx, y: segY, w, h: segH, fill: { color: c }, line: { color: c }, objectName: `Accuracy segment ${i + 1}` });
  sx += k.w * f;
});
T(`${pct(BAND_10, 0)} within ±10%   ·   ${pct(BAND_10_15, 0)} within ±15%   ·   ${pct(BAND_OVER, 0)} further`, {
  x: k.x, y: segY + 0.95, w: k.w, h: 0.45, fontSize: 15, color: SECOND });
label("Average of 5 random 80/20 test splits", k.x, k.y + k.h - 0.4, k.w, { color: WHITE, fontSize: 14 });

// C: NLP condition digest
k = card(2, 0, "Condition card");
label("NLP condition digest", k.x, k.y, k.w);
chip("Needs review", k.x, k.y + 0.7, "Condition");
const flagged = PX.findings.find((f) => f.needs_review);
T("Respray mentioned after \"no accidents\"", { x: k.x, y: k.y + 1.45, w: k.w, h: 0.9, fontSize: 21, fontFace: BOLD, objectName: "Condition headline" });
const lines = PX.findings.filter((f) => !f.needs_review).map((f) =>
  `- ${f.category === "dent_description" ? "Dent" : "Aftermarket mods"}: ${f.detail} (${pct(f.confidence, 0)})`);
lines.push(`- Respray flagged at ${pct(flagged.confidence, 0)} confidence`);
lines.push("- \"Windscreen is fine\" ignored");
T(lines.join("\n"), { x: k.x, y: k.y + 2.55, w: k.w, h: 2.0, fontSize: 16, color: SECOND, lineSpacingMultiple: 1.25, objectName: "Condition findings" });
label(`${pct(nlp.held_out_accuracy, 0)} classifier accuracy · 8 categories`, k.x, k.y + k.h - 0.4, k.w, { color: WHITE, fontSize: 14 });

// D: value over time
k = card(0, 1, "Value over time card");
label("Value over time", k.x, k.y, k.w);
T([{ text: `−${pct(ts.annual_depreciation)}`, options: {} }, { text: "  / year", options: { fontSize: 26, color: SECOND } }], {
  x: k.x, y: k.y + 0.7, w: k.w, h: 1.2, fontSize: 60, fontFace: LIGHT, objectName: "Depreciation number" });
T("Average car, like-for-like across model years", { x: k.x, y: k.y + 1.95, w: k.w, h: 0.45, fontSize: 16, color: SECOND });
const ret = [1, ...Object.values(ts.value_retained_by_years_older).map((v) => v.median)];
s.addChart(pres.charts.LINE, [{ name: "Value retained", labels: ret.map((_, i) => `${i}y`), values: ret.map((v) => Math.round(v * 1000)) }], {  // tenths of a percent
  x: k.x - 0.15, y: k.y + 2.55, w: k.w + 0.3, h: k.h - 2.55, chartColors: ["E6E6EA"], lineSize: 3, lineDataSymbol: "circle", lineDataSymbolSize: 9,
  showLegend: false, showValue: true, dataLabelPosition: "t", dataLabelColor: WHITE, dataLabelFontSize: 14, dataLabelFontFace: BODY, dataLabelFormatCode: "0\".\"0\"%\"",
  catAxisLabelColor: MUTED, catAxisLabelFontSize: 14, catAxisLabelFontFace: BODY, catAxisLineShow: false,
  valAxisHidden: true, valAxisMinVal: 500, valAxisMaxVal: 1080, valGridLine: { style: "none" }, catGridLine: { style: "none" },
  plotArea: { fill: { color: CARD } }, objectName: "Value retained chart",
});

// E: depreciation by body type (radar)
k = card(1, 1, "Body type card");
label("Depreciation by body type", k.x, k.y, k.w);
const bodies = ts.annual_depreciation_by_body_type;
s.addChart(pres.charts.RADAR, [{ name: "Annual depreciation", labels: bodies.map((b) => b.body_type), values: bodies.map((b) => Math.round(b.annual_depreciation * 1000) / 10) }], {
  x: k.x - 0.2, y: k.y + 0.55, w: k.w + 0.4, h: k.h - 1.3, radarStyle: "marker", chartColors: ["E6E6EA"], lineSize: 3, lineDataSymbolSize: 8,
  showLegend: false, catAxisLabelColor: SECOND, catAxisLabelFontSize: 14, catAxisLabelFontFace: BODY,
  valAxisHidden: true, valAxisMinVal: 0, valAxisMaxVal: 12, valGridLine: { color: "3A3A3E", size: 1 }, objectName: "Body type radar",
});
T(`Bakkies hold value best (${pct(bodies[0].annual_depreciation)} a year), sedans worst (${pct(bodies[bodies.length - 1].annual_depreciation)})`, {
  x: k.x, y: k.y + k.h - 0.65, w: k.w, h: 0.65, fontSize: 15, color: SECOND, objectName: "Body type caption" });

// F: five models compared (bars)
k = card(2, 1, "Models card");
label("Models compared", k.x, k.y, k.w * 0.55);
chip("Avg error, R k", k.x + k.w - (0.16 * 14 + 0.6), k.y - 0.05, "Models");
const models = [["XGBoost", "XGBoost"], ["Random Forest", "Random Forest"], ["Deep Learning (MLP)", "MLP"], ["Depreciation baseline", "Baseline"], ["Linear Regression", "Linear"]];
const maxE = Math.max(...models.map(([key]) => cmp[key].MAE));
const barArea = { top: k.y + 1.6, bottom: k.y + k.h - 0.6 };
const bw = (k.w - 4 * 0.3) / 5;
models.forEach(([key, name], i) => {
  const v = cmp[key].MAE / 1000;
  const h = (barArea.bottom - barArea.top) * (v * 1000 / maxE);
  const x = k.x + i * (bw + 0.3), y = barArea.bottom - h;
  const best = i === 0;
  box(x, y, bw, h, best ? WHITE : "3A3A3E", best ? WHITE : "5A5A5F", 0.12, `${name} bar`);
  T(v.toFixed(1), { x: x - 0.2, y: y - 0.55, w: bw + 0.4, h: 0.45, fontSize: 18, fontFace: BOLD, align: "center", objectName: `${name} value` });
  T(name, { x: x - 0.3, y: barArea.bottom + 0.15, w: bw + 0.6, h: 0.4, fontSize: 14, color: SECOND, align: "center", objectName: `${name} label` });
});

// G: problem + how it works
k = card(0, 2, "Problem and steps card", 3);
const half = (k.w - 0.8) * 0.36;
label("The problem", k.x, k.y, half);
T("Dealerships value trade-ins by hand: slow, inconsistent between consultants, and never recorded. Overpaying loses margin; underpaying loses the deal.", {
  x: k.x, y: k.y + 0.65, w: half, h: k.h - 0.65, fontSize: 19, color: WHITE, lineSpacingMultiple: 1.2, objectName: "Problem text" });
const sx0 = k.x + half + 0.8, sw = (k.w - half - 0.8 - 3 * 0.35) / 4;
label("How it works", sx0, k.y, sw * 2);
[["01", "Chat", "Customer picks their car, year and mileage"], ["02", "Understand", "NLP turns their words into condition findings"],
 ["03", "Predict", "XGBoost estimates the value and a range"], ["04", "Record", "Saved to SQL Server and an Excel log"]].forEach(([num, t, d], i) => {
  const x = sx0 + i * (sw + 0.35);
  T(num, { x, y: k.y + 0.65, w: sw, h: 0.75, fontSize: 36, fontFace: LIGHT, color: MUTED, objectName: `Step ${num} number` });
  T(t, { x, y: k.y + 1.45, w: sw, h: 0.5, fontSize: 21, fontFace: BOLD, objectName: `Step ${num} title` });
  T(d, { x, y: k.y + 2.0, w: sw, h: 0.9, fontSize: 15, color: SECOND, objectName: `Step ${num} text` });
});

// ---------- footer ----------
const FY = PY + PH + 0.55;
T("Every car, every customer, one clear value", { x: M, y: FY, w: W - 2 * M, h: 0.8, fontSize: 40, fontFace: LIGHT, color: "CFCFD3", align: "center", objectName: "Tagline" });
label("Built with", M, FY + 1.15, W - 2 * M, { align: "center", color: MUTED, fontSize: 14 });
T("Python     XGBoost     scikit-learn     TensorFlow     Flask     SQL Server     GitHub", {
  x: M, y: FY + 1.6, w: W - 2 * M, h: 0.55, fontSize: 24, fontFace: BOLD, color: "8C8C92", align: "center", objectName: "Tech row" });
T([{ text: "Group: ", options: { color: SECOND } }, { text: "Name Surname · Name Surname · Name Surname · Name Surname", options: { highlight: "FFFF00", color: "111113" } }], {
  x: M, y: FY + 2.35, w: W - 2 * M, h: 0.45, fontSize: 17, align: "center", objectName: "Group members" });
T("Data: Autotrader South Africa listings, published by Adewoyin (2023), MIT licence", {
  x: M, y: FY + 2.85, w: W - 2 * M, h: 0.4, fontSize: 14, color: MUTED, align: "center", objectName: "Data credit" });

pres.writeFile({ fileName: OUT }).then(() => console.log(`Wrote ${OUT}; content ends at ${(FY + 3.25).toFixed(2)} in of ${H}`));
