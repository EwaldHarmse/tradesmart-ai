// Builds documentation/TradeSmart_AI_Documentation_DRAFT.docx from the
// project's real outputs (model_comparison.json etc.), so every number in the
// document is the number the code produced.
const fs = require("fs");
const path = require("path");
const {
  Document, Packer, Paragraph, TextRun, HeadingLevel, AlignmentType, Table, TableRow, TableCell,
  WidthType, ShadingType, ImageRun, PageBreak, TableOfContents, LevelFormat, Footer, PageNumber,
  BorderStyle,
} = require("docx");

const FINAL = path.resolve(__dirname, "..", "..");  // project root
const ML = `${FINAL}/tradesmart-ml`;
const OUT_DIR = `${FINAL}/documentation`;
const OUT = `${OUT_DIR}/TradeSmart_AI_Documentation_DRAFT.docx`;

const cmp = JSON.parse(fs.readFileSync(`${ML}/outputs/model_comparison.json`, "utf8"));
const tune = JSON.parse(fs.readFileSync(`${ML}/outputs/xgboost_tuning.json`, "utf8"));
const ts = JSON.parse(fs.readFileSync(`${ML}/outputs/time_series_analysis.json`, "utf8"));
const X = JSON.parse(fs.readFileSync(path.join(__dirname, "extra.json"), "utf8"));
const SPL = JSON.parse(fs.readFileSync(`${ML}/outputs/split_experiments.json`, "utf8"));
const S80 = SPL.split_ratio.find((r) => r.train_pct === 80);
const nlp = JSON.parse(fs.readFileSync(`${ML}/outputs/nlp_intent_classifier_report.json`, "utf8"));
const R = cmp.test_results;
const XGB = R["XGBoost"];

// ---------- formatting helpers (brief: Arial 12, 1.5 line spacing, justified) ----------
const FONT = "Arial";
const SIZE = 24;          // half-points -> 12pt
const LINE_15 = 360;      // 1.5 line spacing
const CONTENT_W = 9026;   // A4 width 11906 - 2 x 1440 margins

const rand = (n) => "R" + Math.round(n).toLocaleString("en-ZA").replace(/\u00a0/g, " ").replace(/,/g, " ");
const pct = (x, d = 1) => (100 * x).toFixed(d) + "%";
const words = (s) => s.trim().split(/\s+/).length;
const chg = (after, before) => `${(100 * (after - before) / before).toFixed(1)}%`;

function runs(text, opts = {}) {
  // **bold** and [[placeholder]] (highlighted for the group to fill in)
  const out = [];
  const re = /(\*\*[^*]+\*\*|\[\[[^\]]+\]\])/g;
  let last = 0, m;
  while ((m = re.exec(text))) {
    if (m.index > last) out.push(new TextRun({ text: text.slice(last, m.index), ...opts }));
    if (m[0].startsWith("**")) out.push(new TextRun({ text: m[0].slice(2, -2), bold: true, ...opts }));
    else out.push(new TextRun({ text: m[0].slice(2, -2), highlight: "yellow", ...opts }));
    last = m.index + m[0].length;
  }
  if (last < text.length) out.push(new TextRun({ text: text.slice(last), ...opts }));
  return out;
}
const P = (text, o = {}) => new Paragraph({
  children: runs(text), alignment: o.align || AlignmentType.JUSTIFIED,
  spacing: { line: LINE_15, after: 160 }, ...o.extra,
});
const H1 = (t) => new Paragraph({ text: t, heading: HeadingLevel.HEADING_1, pageBreakBefore: true });
const H2 = (t) => new Paragraph({ text: t, heading: HeadingLevel.HEADING_2 });
const H3 = (t) => new Paragraph({ text: t, heading: HeadingLevel.HEADING_3 });
const B = (text, level = 0) => new Paragraph({
  children: runs(text), numbering: { reference: "bullets", level },
  alignment: AlignmentType.JUSTIFIED, spacing: { line: LINE_15, after: 80 },
});
let listInstance = 0;
const newList = () => { listInstance += 1; };
const N = (text) => new Paragraph({
  children: runs(text), numbering: { reference: "numbers", level: 0, instance: listInstance },
  alignment: AlignmentType.JUSTIFIED, spacing: { line: LINE_15, after: 80 },
});
const caption = (t) => new Paragraph({
  children: [new TextRun({ text: t, italics: true })], alignment: AlignmentType.CENTER,
  spacing: { line: LINE_15, before: 80, after: 240 },
});

function table(headers, rows, widths) {
  const total = widths.reduce((a, b) => a + b, 0);
  const border = { style: BorderStyle.SINGLE, size: 4, color: "999999" };
  const borders = { top: border, bottom: border, left: border, right: border };
  const cell = (text, i, head) => new TableCell({
    width: { size: widths[i], type: WidthType.DXA }, borders,
    shading: head ? { type: ShadingType.CLEAR, fill: "1F2937", color: "auto" } : undefined,
    margins: { top: 60, bottom: 60, left: 100, right: 100 },
    children: [new Paragraph({
      children: runs(String(text), head ? { bold: true, color: "FFFFFF" } : {}),
      alignment: AlignmentType.LEFT,
    })],
  });
  return new Table({
    width: { size: total, type: WidthType.DXA }, columnWidths: widths,
    rows: [new TableRow({ tableHeader: true, children: headers.map((h, i) => cell(h, i, true)) }),
           ...rows.map((r) => new TableRow({ children: r.map((c, i) => cell(c, i, false)) }))],
  });
}
const gap = () => new Paragraph({ text: "", spacing: { after: 120 } });

function image(file, widthPx) {
  const buf = fs.readFileSync(file);
  const w = buf.readUInt32BE(16), h = buf.readUInt32BE(20);  // PNG IHDR
  return new Paragraph({
    alignment: AlignmentType.CENTER, spacing: { before: 120 },
    children: [new ImageRun({ type: "png", data: buf,
      transformation: { width: widthPx, height: Math.round((widthPx * h) / w) } })],
  });
}

// ---------- content ----------
const problemWhat =
  "Used-vehicle dealerships in South Africa value trade-in vehicles slowly and inconsistently. A " +
  "first-pass appraisal depends on a sales consultant's experience and a manual search of guide prices " +
  "and online listings, so two consultants can value the same vehicle differently. A wrong valuation " +
  "costs the dealership either way: overpaying loses margin, and underpaying loses the deal to a private " +
  "sale or a competitor. Customers also wait for a figure, which delays negotiation, and what they say " +
  "about the car's condition (accidents, dents, modifications) is captured informally and often lost " +
  "before inspection. Because appraisals are not recorded in a structured way, the dealership cannot " +
  "learn from past enquiries. The problem is the lack of a fast, consistent, data-driven way to produce " +
  "a first value estimate and to record a vehicle's reported condition.";
const problemRelevance =
  "This is an operational problem in the automotive retail industry that machine learning and " +
  "conversational AI can address directly, which matches the theme 'an AI Solution for Industries'.";
const problemBenefit =
  "The assistant gives customers and consultants a consistent, data-based starting valuation within " +
  "seconds, saves consultant time, reduces mispriced trade-ins and builds a valuation dataset the " +
  "dealership owns. As this is a business problem it does not involve a local municipality, although " +
  "faster, fairer valuations help local dealerships win more trade-ins.";
const wWhat = words(problemWhat);
const wTotal = wWhat + words(problemRelevance) + words(problemBenefit);
if (wWhat > 190 || wTotal > 250) throw new Error(`Problem definition too long: ${wWhat} / ${wTotal}`);

const order = ["Depreciation baseline", "Linear Regression", "Random Forest", "XGBoost", "Deep Learning (MLP)"];
const resultsRows = order.map((k) => [
  k === "XGBoost" ? "**XGBoost (tuned, used by the app)**" : k,
  rand(R[k].MAE), rand(R[k].RMSE), R[k].R2.toFixed(4),
  R[k].cv10_MAE_mean ? `${rand(R[k].cv10_MAE_mean)} ± ${rand(R[k].cv10_MAE_std)}` : "-",
]);
const retention = Object.entries(ts.value_retained_by_years_older)
  .map(([k, v]) => [`${k}`, pct(v.median), String(v.pairs), pct(Math.exp(-ts.fitted_rate_r * Number(k)))]);
const bodyRows = ts.annual_depreciation_by_body_type.map((b) => [b.body_type, pct(b.annual_depreciation), String(b.model_year_pairs)]);
const fc = ts.example_forecast;
const topFeatures = cmp.top_feature_importance["XGBoost"].slice(0, 6)
  .map((f) => f.feature.replace(/^num__|^cat__/, "").replace(/_/g, " = "));
const nlpTest = Math.round(nlp.n_training_sentences * 0.25);

const sections = [];

// Title page
sections.push(
  new Paragraph({ spacing: { before: 2400 } }),
  new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ text: "TradeSmart AI", bold: true, size: 56 })] }),
  new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 600 }, children: [new TextRun({ text: "An AI-powered vehicle trade-in valuation assistant", size: 32 })] }),
  P("Diploma: Information Technology", { align: AlignmentType.CENTER }),
  P("Business Analysis 3.2 (AIBUY3A) - Project: \"an AI Solution for Industries\"", { align: AlignmentType.CENTER }),
  P("Vaal University of Technology", { align: AlignmentType.CENTER }),
  P("Lecturers: Dr. Sibanda, Mr. Matsela, Mr. Matshego", { align: AlignmentType.CENTER }),
  P("Due date: 02 November 2026", { align: AlignmentType.CENTER }),
  gap(),
  table(["Group member", "Student number"],
    Array.from({ length: 6 }, () => ["[[Name Surname]]", "[[Student number]]"]), [5513, 3513]),
);

// Declaration
sections.push(
  H1("Declaration"),
  P("We, the undersigned members of this group, declare that this project and its documentation are our own work, that all sources we used have been acknowledged and referenced, and that we have not given any other group access to our solution. We understand that plagiarism is a serious offence at the Vaal University of Technology."),
  P("The project builds on open-source software and on a publicly available dataset, both of which are acknowledged in the text and in the reference list: the Autotrader South Africa used-car dataset and the cleaning approach published by Adewoyin (2023) under the MIT licence."),
  gap(),
  table(["Name", "Student number", "Signature", "Date"],
    Array.from({ length: 6 }, () => ["[[Name]]", "[[Number]]", "", "[[Date]]"]), [3000, 2026, 2500, 1500]),
);

// Contents
sections.push(
  H1("Contents"),
  new TableOfContents("Contents", { hyperlink: true, headingStyleRange: "1-2" }),
);

// 1 AI solution
sections.push(
  H1("1. The AI Solution and Its Relevance to the Theme"),
  P(`TradeSmart AI is a conversational assistant built for South African used-vehicle dealerships, an application of AI in the automotive retail industry, one of the sectors named in the project theme "an AI Solution for Industries". The dealership deploys it on its website or on a showroom tablet, and its sales consultants use the result as the starting point for their appraisal. The assistant collects the vehicle's make, model, year and mileage, and an XGBoost machine-learning model trained on 16 453 real Autotrader South Africa listings (model years 2018-2023) predicts its market value range. Natural language processing (NLP) interprets the customer's own description of accidents, dents, windscreen damage, respray work and modifications, and records each issue for the consultant to check at inspection. Every valuation is saved in the dealership's database. In line with the Fourth Industrial Revolution, the solution turns a slow, manual and inconsistent process into a fast, repeatable, data-driven one using locally relevant data and open-source tools. A deep-learning model was also built and evaluated against XGBoost (Section 11).`),
);

// 2 Problem definition
sections.push(
  H1("2. Problem Definition"),
  H2("2.1 What is the problem?"),
  P(problemWhat),
  H2("2.2 Relevance to the theme"),
  P(problemRelevance),
  H2("2.3 Benefits of solving it with AI"),
  P(problemBenefit),
  P(`[[Word count: ${wWhat} words for 2.1 (limit 190) and ${wTotal} words for the whole problem definition (limit 250). Re-check after editing.]]`),
);

// 3 Main objective and how AI is applied
sections.push(
  H1("3. Main Objective and How AI Is Applied"),
  H2("3.1 Main objective"),
  P("To develop a conversational AI assistant for dealerships that collects a vehicle's details, records its reported condition using NLP, and produces a data-driven market value range for the consultant."),
  H2("3.2 How AI is applied"),
  B("**Chatbot** to collect the vehicle's details and the customer's answers (Section 12)."),
  B("**XGBoost regression** to predict the vehicle's value from its make, model, year and mileage (Sections 6 and 8)."),
  B("**NLP** (TF-IDF and Logistic Regression) to turn free-text condition descriptions into categorised findings (Section 10)."),
  B("**Deep learning:** a neural network (MLP) trained on the same data and compared with XGBoost (Section 11)."),
  B("**Time series analysis** of how vehicle values change with age (Section 8.3)."),
  B("**Hyperparameter tuning** to improve the model's accuracy (Section 9.2)."),
);

// 4 Business objectives
sections.push(
  H1("4. Business Objectives"),
  H2("4.1 Business background"),
  P("The solution is designed for a medium-sized used-vehicle dealership, referred to in this document as AutoValue Motors, a fictitious dealership in Vanderbijlpark. Like most dealerships, it accepts customers' current vehicles as trade-ins when they buy another vehicle. Trade-in values are decided manually by individual sales consultants, who compare guide prices and similar cars advertised online. This is slow and inconsistent: two consultants can value the same car differently, and a wrong valuation either costs the dealership margin (overpaying) or loses the deal (underpaying). Customers expect quick answers, and the dealership keeps no structured record of its valuations. [[Add any real background your group has, e.g. from an interview with a dealership, with a reference.]]"),
  H2("4.2 Business objectives"),
  (newList(), N("Reduce the time and staff effort needed for a first-pass appraisal: customers get a first estimate in one chat conversation, at any time, without logging in.")),
  N("Standardise valuations so that similar vehicles get similar estimates, and the same details always give the same estimate."),
  N("Give consultants an accurate, data-driven starting value range to support negotiation."),
  N("Record the vehicle's reported condition with each valuation, as structured, categorised findings for inspection."),
  N("Build a valuation dataset, owned by the dealership, for future model improvement."),
  N("Protect customers' personal information in line with the Protection of Personal Information Act (POPIA)."),
  H2("4.3 Business success criteria"),
  P("The first six criteria were measured on the finished solution. The last two can only be measured once the dealership is using it, so they are targets for after deployment."),
  table(["Criterion", "Measure", "Target", "Result"],
    [
      ["Estimate accuracy", "Unseen test vehicles whose estimate is within ±15% of the actual listing price (average of 5 random 80/20 splits)", "≥ 80%", `Achieved: ${pct(S80.within_15pct.mean)} (${pct(S80.within_10pct.mean)} within ±10%)`],
      ["Overall accuracy", "R² on unseen test vehicles (average of 5 random 80/20 splits)", "≥ 0.90 and better than the depreciation baseline", `Achieved: ${S80.R2.mean.toFixed(3)} on average (range ${S80.R2.min.toFixed(3)}-${S80.R2.max.toFixed(3)}); baseline ${R["Depreciation baseline"].R2.toFixed(3)}`],
      ["Response speed", "Time to show the estimate after the last answer", "< 3 seconds", `Achieved: ${X.speed_median_ms} ms typical, ${X.speed_max_ms} ms slowest (${X.speed_runs} runs, excluding the database save)`],
      ["NLP accuracy", "Condition classifier on labelled held-out statements", "≥ 85%", `Achieved: ${pct(nlp.held_out_accuracy, 0)} on ${nlpTest} statements`],
      ["POPIA compliance", "Contact details stored only with consent", "100%", "Achieved: enforced in the database and in the log file"],
      ["Consistency", "Same vehicle details give the same estimate", "100%", "Achieved: the trained model is deterministic"],
      ["Appraisal time", "First-pass appraisal time compared with the manual method", "60% reduction", "After deployment"],
      ["Valuation complaints", "Valuation complaints recorded by the dealership", "30% reduction", "After deployment"],
    ], [1700, 3026, 1900, 2400]),
);

// 5 Requirements, constraints, risks, tools
sections.push(
  H1("5. Requirements, Constraints, Risks and Tools"),
  H2("5.1 Functional requirements"),
  B("**FR1** A chat interface where the customer finds their vehicle by typing its make and model and choosing from matching vehicles."),
  B("**FR2** The customer enters the vehicle's year and mileage; unreadable values are rejected with a clear message on the same step."),
  B("**FR3** The customer can describe accidents, damage and modifications in free text, or skip the question."),
  B("**FR4** NLP interprets the condition answer and stores each issue as a condition finding, flagging uncertain or contradictory ones."),
  B("**FR5** The customer can optionally add a cash deposit towards another vehicle."),
  B("**FR6** POPIA consent is required before phone and email are stored."),
  B("**FR7** The system shows a value estimate with a low and high range and the model's measured accuracy, and flags vehicles whose year is outside 2018-2023."),
  B("**FR8** Every session is saved in the database and appended to logs/customer_submissions.csv, which opens in Excel."),
  P("The estimate is a starting point, not an offer: a consultant confirms the final figure when the vehicle is inspected."),
  H2("5.2 Non-functional requirements"),
  B("**Performance:** the estimate is shown in under 3 seconds after the last answer."),
  B("**Usability:** easy to use without a login or any training; works in any modern web browser."),
  B("**Privacy and security:** minimal personal data, consent-based storage of contact details, and no personal data in the source-code repository."),
  B("**Reliability:** if the database is unavailable the customer still receives the estimate, and a locked log file never interrupts the chat."),
  B("**Scalability:** able to grow from one branch to many; the database separates customers, vehicles, models and valuation sessions."),
  B("**Maintainability:** the model can be retrained with a short sequence of documented scripts, and package versions are pinned."),
  H2("5.3 Constraints"),
  B("**No real trade-in records:** the model is trained on public Autotrader asking prices, which are normally higher than trade-in offers."),
  B("**Model years 2018-2023 only:** the data cannot reliably value older vehicles."),
  B("**No condition information in the data:** so condition is recorded for inspection but does not change the price."),
  B("**No price history:** the data is a single snapshot (April 2023), which limits the time series analysis (Section 8.3)."),
  B("**Limited time and budget:** an academic timeline and only free, open-source tools."),
  B("**A consultant must make the final decision:** the estimate supports the appraisal but does not replace it."),
  H2("5.4 Risks and mitigations"),
  table(["Risk", "Impact", "Mitigation"],
    [
      ["Asking prices are higher than trade-in prices, so the dealership could overpay", "High", "The output is a market value range; the consultant sets the offer after inspection; later calibration against real agreed prices (Section 9.2)"],
      ["The estimate is treated as a firm offer", "Medium", "A disclaimer is shown with every range"],
      ["Estimates for vehicles outside 2018-2023 are unreliable", "High", "Low-confidence warning in the chat; OutsideTrainingYears flag in the database"],
      ["NLP misreads a vague answer", "Low", "Confidence score and NeedsReview flag stored; findings never change the price"],
      ["Errors in the source data", "High", "Three cleaning errors were found and corrected before training (Section 7.3)"],
      ["Personal information is leaked", "High", "POPIA consent tick box, minimal fields, customer log excluded from version control"],
      ["The model becomes outdated as prices change", "Medium", "Documented retraining pipeline (Section 9.2)"],
      ["A package update breaks the saved model", "Medium", "Exact package versions are pinned"],
    ], [3300, 1000, 4726]),
  H2("5.5 Initial assessment of tools and techniques"),
  table(["Tool / technique", "Used for", "Why it was chosen"],
    [
      ["Python 3.12", "All code", "The language required by the module; strong data-science libraries"],
      ["pandas, NumPy", "Data loading, cleaning, feature engineering", "Standard, well-documented tools for tabular data"],
      ["scikit-learn", "Linear Regression, Random Forest, preprocessing, cross-validation, tuning, TF-IDF + Logistic Regression", "One consistent API for many models and for fair evaluation"],
      ["XGBoost", "Final valuation model", "Best accuracy on tabular data in our comparison; fast; small model file"],
      ["TensorFlow / Keras", "Deep learning (MLP) model", "Industry-standard deep learning library"],
      ["Flask, Jinja2, htmx", "Web chatbot", "Lightweight Python web framework; the chat needs no hand-written JavaScript"],
      ["Microsoft SQL Server", "Database", "Available at VUT; relational design with enforced relationships"],
      ["matplotlib", "Figures for the time series analysis", "Standard Python plotting library"],
      ["GitHub", "Version control and project management", "Required by the brief"],
    ], [2300, 3363, 3363]),
);

// 6 ML approach
sections.push(
  H1("6. Machine Learning Approach"),
  P("Estimating a car's value is a **supervised regression** problem: the model learns from thousands of cars whose price is known and predicts a number (the price) for a car it has not seen. Each car is described by its make and model specifications (engine size, power, torque, fuel consumption, body type, drive type and so on), its age and its mileage."),
  P("Five approaches were trained on exactly the same data and compared on the same unseen test cars:"),
  B("**Depreciation baseline:** the rule of thumb that the AI must beat. It takes the price of the newest examples of a model and reduces it by a fixed percentage per year of age."),
  B("**Linear Regression:** a simple model that assumes price changes in straight lines with each feature."),
  B("**Random Forest:** many decision trees trained on random samples of the data, whose predictions are averaged (Breiman, 2001)."),
  B("**XGBoost:** gradient-boosted decision trees, where each new tree corrects the errors of the previous ones (Chen and Guestrin, 2016)."),
  B("**Deep learning (MLP):** a multi-layer neural network (Section 11)."),
  P("Tree-based ensembles were expected to perform best because the value of a car depends on interactions between features: an extra 50 000 km matters far more on a sports car than on a bakkie, which a straight-line model cannot express. XGBoost was selected for the application because it had the lowest RMSE and highest R² (it makes the fewest large mistakes) and its saved model is small enough to load quickly; the Random Forest model file is about 100 MB."),
  P("A customer does not know their car's torque or CO2 rating, so the application uses the **typical specification of the exact model** they choose: the median of each numeric specification and the most common value of each category across all listings of that model. This is stored in the VEHICLE_MODEL table, summarised from the 16 453 listings in the VEHICLE table. Only the customer's own year and mileage are entered per valuation, which is how a human consultant would reason about a car."),
);

// 7 Data
sections.push(
  H1("7. Data"),
  H2("7.1 Source"),
  P("The model is trained on **Autotrader South Africa** used-car listings. The data was collected by Adewoyin (2023), who scraped the website between 23 and 24 April 2023 and published the cleaned dataset and code under the MIT licence. It contains listings for model years 2018 to 2023. After our corrections (Section 7.3) it holds **16 453 listings** of **2 393 makes and models** from 53 brands, priced from R59 000 to R12 million (median R379 900)."),
  H2("7.2 Forms of data used"),
  table(["Form", "Examples", "Where it is used"],
    [
      ["Structured numerical", "Price, mileage, year, engine capacity, power (kW), torque (Nm), fuel consumption, CO2", "Model features and target (price)"],
      ["Structured categorical", "Brand, transmission, fuel type, body type, driven wheels, cylinder layout", "Model features (one-hot encoded)"],
      ["Text (free text)", "Customer answers such as \"small dent about the size of a golf ball on the door\"", "NLP condition findings"],
      ["Labelled text", `${nlp.n_training_sentences} example customer answers, each labelled with one of 8 categories`, "Training the NLP classifier"],
      ["Personal data", "Customer name, phone, email (with consent)", "CUSTOMER table"],
    ], [2200, 4126, 2700]),
  gap(),
  P("Example listings from the dataset (a subset of the 26 columns):"),
  table(["Make and model", "Year", "Mileage", "Body", "Power", "Price"],
    [
      ["Toyota Hilux 2.4GD-6 Double Cab Raider", "2023", "5 500 km", "Double cab", "110 kW", "R529 900"],
      ["Volkswagen Polo Vivo Hatch 1.4 Trendline", "2023", "5 500 km", "Hatchback", "55 kW", "R259 900"],
      ["BMW X5 xDrive30d M Sport", "2022", "30 000 km", "SUV", "195 kW", "R1 339 900"],
    ], [3226, 900, 1300, 1300, 1000, 1300]),
  H2("7.3 Data quality: errors found and corrected"),
  P("While building the solution we found three errors that the published cleaning step had introduced, and we corrected them before any model was trained (tradesmart-ml/src/fix_dataset.py):"),
  B("**Split brand names (316 listings).** The brand was taken as the first word of the advert title, so \"Land Rover Defender\" became brand \"Land\", model \"Rover Defender\". The same happened to Alfa Romeo and Aston Martin."),
  B("**Fuel consumption missing its leading \"1\" (405 listings restored, 179 removed).** A text-stripping step removed the characters 1, 0, k and m from both ends of each value, so 11.5 L/100 km became 0.5. No listing in the published data had a value between 10 and 19.9. We restored each value where the tank size and driving range confirmed it, and blanked those that could not be confirmed."),
  B("**Impossible mileages (3 listings removed),** for example 990 000 km on a 2018 vehicle."),
  H2("7.4 Database"),
  P("The data and every valuation are stored in Microsoft SQL Server in six related tables (Figure 1). VEHICLE holds the full dataset: all 16 453 Autotrader listings, each linked to its make and model in VEHICLE_MODEL, which holds one row per make and model (2 393) with the typical specifications the model uses. CUSTOMER records who asked for a valuation; VALUATION_SESSION records the customer's car (which make and model, its year and mileage) and the predicted price; CONDITION_FINDING stores each condition issue the NLP model found; CONDITION_CATEGORY lists the eight categories it can assign. A check in SQL confirms that every VEHICLE_MODEL row's listing count matches the number of VEHICLE listings linked to it."),
  new Paragraph({ children: [new PageBreak()] }),
  image(path.join(__dirname, "erd_rotated.png"), 428),
  caption("Figure 1: Entity relationship diagram (rotated to fit the page)"),
);

// 8 Model evaluation + time series
sections.push(
  H1("8. Model Evaluation and Time Series Analysis"),
  H2("8.1 How accuracy is evaluated"),
  P("The data was split into **80% for training (13 162 cars) and 20% for testing (3 291 cars)**. The test cars are never used for training or tuning, so they show how the model performs on vehicles it has not seen. On the training data, **10-fold cross-validation** (training on nine tenths and testing on the remaining tenth, ten times) checks that the result is stable rather than lucky. Three measures are reported:"),
  B("**MAE (mean absolute error):** the average difference between predicted and actual price, in rand."),
  B("**RMSE (root mean squared error):** like MAE but punishes large mistakes more heavily."),
  B("**R² (coefficient of determination):** the share of the variation in prices that the model explains (1.0 is perfect)."),
  H2("8.2 Results"),
  table(["Model", "MAE", "RMSE", "R²", "10-fold CV MAE"], resultsRows, [2826, 1400, 1500, 1000, 2300]),
  gap(),
  P(`The table shows each model on the main test split. Every model except Linear Regression beats the depreciation baseline; Linear Regression cannot capture the fact that cheap and expensive cars lose value very differently, which supports the choice of non-linear models. The features XGBoost relies on most are: ${topFeatures.join(", ")}.`),
  P("**How reliable is this result?** One split can be lucky or unlucky, so the XGBoost model was retrained and tested on different splits of the data (tradesmart-ml/src/split_experiments.py): four train/test ratios, each with five different random shuffles of the 16 453 cars."),
  table(["Train / test", "Training cars", "Test cars", "R² average (range)", "Average error (MAE)", "Within ±15%"],
    SPL.split_ratio.map((r) => [`${r.train_pct} / ${r.test_pct}`, r.train_cars.toLocaleString("en-ZA").replace(/[, ]/g, " "), r.test_cars.toLocaleString("en-ZA").replace(/[, ]/g, " "),
      `${r.R2.mean.toFixed(3)} (${r.R2.min.toFixed(3)}-${r.R2.max.toFixed(3)})`, `${rand(r.MAE.mean)} ± ${rand(r.MAE.std)}`, pct(r.within_15pct.mean)]),
    [1050, 1150, 1050, 1950, 2626, 1200]),
  gap(),
  P(`The average error is consistent: about ${rand(Math.min(...SPL.split_ratio.map((r) => r.MAE.mean)))} to ${rand(Math.max(...SPL.split_ratio.map((r) => r.MAE.mean)))} in every split, with around ${pct(S80.within_15pct.mean, 0)} of estimates within 15% of the real price. R² varies more, from ${S80.R2.min.toFixed(2)} to ${S80.R2.max.toFixed(2)} across 80/20 shuffles, because it is dominated by a handful of very expensive vehicles (up to R12 million): when one of them lands in the test set and is mispredicted, R² drops noticeably. The main split (R² ${XGB.R2.toFixed(3)}) is at the favourable end of that range, so the figure we report, and the one the application shows customers, is the average over five random 80/20 splits: **R² ${S80.R2.mean.toFixed(2)}, average error ${rand(S80.MAE.mean)}**.`),
  P(`**How much training data is needed?** The model was also trained on random samples of 1 000 to 13 162 cars, always tested on the same 3 291 unseen cars (Figure 2). Accuracy rises from R² ${SPL.learning_curve[0].R2.mean.toFixed(2)} with 1 000 cars to ${SPL.learning_curve[SPL.learning_curve.length - 1].R2.mean.toFixed(2)} with all 13 162, and the average error falls from ${rand(SPL.learning_curve[0].MAE.mean)} to ${rand(SPL.learning_curve[SPL.learning_curve.length - 1].MAE.mean)}. With only 3 000 training cars the model would reach R² ${SPL.learning_curve.find((r) => r.train_cars === 3000).R2.mean.toFixed(2)}, which shows why the full training set matters and suggests that more data would improve it further (Section 9.2).`),
  image(`${ML}/outputs/figures/learning_curve.png`, 600),
  caption("Figure 2: Accuracy by amount of training data"),
  H2("8.3 Time series analysis: how a car's value changes over time"),
  P("A car's value over time is the core of any trade-in estimate. The dataset is a single snapshot (April 2023) rather than prices recorded month by month, but each listing has a model year, so the same model appears at several ages at once: a 2023, a 2021 and a 2019 Polo Vivo listed side by side. Comparing these gives the value-over-time curve that a price history would show (tradesmart-ml/src/time_series_analysis.py)."),
  P(`Overall averages would be misleading: the median price of all 2021 cars (${rand(ts.raw_median_price_by_model_year["2021"])}) is lower than that of all 2020 cars (${rand(ts.raw_median_price_by_model_year["2020"])}), only because a different mix of models was listed for each year. The analysis therefore compares each model only with itself: for each of ${ts.models_with_several_years.toLocaleString("en-ZA").replace(/,/g, " ")} models listed in more than one year, the median price for each older year is divided by the median price for its newest year. An exponential depreciation curve, value(t) = value(0) × e^(−rt), was then fitted to these ${ts.model_year_pairs_used.toLocaleString("en-ZA").replace(/,/g, " ")} comparisons.`),
  table(["Years older", "Value retained (observed median)", "Comparisons", "Fitted curve"], retention, [1600, 3226, 2000, 2200]),
  gap(),
  P(`Cars lose about **${pct(ts.annual_depreciation)} of their value per year**, and the fitted curve stays within ${pct(ts.max_gap_fit_vs_observed)} of the observed values at every age (Figure 3).`),
  image(`${ML}/outputs/figures/depreciation_curve.png`, 600),
  caption("Figure 3: Value retained by age, observed and fitted"),
  P(`Depreciation differs by body type (Figure 4): bakkies hold their value best (extended cab ${pct(ts.annual_depreciation_by_body_type[0].annual_depreciation)} a year, double cab ${pct(ts.annual_depreciation_by_body_type.find((b) => b.body_type === "Double cab").annual_depreciation)}), while sedans lose value fastest (${pct(ts.annual_depreciation_by_body_type.find((b) => b.body_type === "Sedan").annual_depreciation)}). This is useful to the dealership when deciding which trade-ins to accept and how long to keep them in stock.`),
  table(["Body type", "Annual depreciation", "Comparisons"], bodyRows, [3526, 3000, 2500]),
  image(`${ML}/outputs/figures/depreciation_by_body_type.png`, 600),
  caption("Figure 4: Annual depreciation by body type"),
  P(`The fitted rate can forecast a vehicle's value in future years. For example, a ${fc.vehicle} had a median listing price of ${rand(fc.median_price_2023)} in 2023 (${fc.listings} listings); Figure 5 projects its value to ${rand(fc.projection[fc.projection.length - 1].projected_value)} by ${fc.projection[fc.projection.length - 1].year}.`),
  image(`${ML}/outputs/figures/value_forecast_example.png`, 600),
  caption("Figure 5: Value forecast for an example vehicle"),
  P("**Limitations.** The curve is measured for ages up to five years only, and the forecast assumes depreciation continues at the same rate. Collecting the same listings repeatedly over time would allow a true time series model such as ARIMA or Prophet, which could also detect seasonal effects and market shifts (Section 9.2)."),
);

// 9 Solution techniques & improving accuracy
sections.push(
  H1("9. Solution Techniques and Improving Accuracy"),
  H2("9.1 Techniques used"),
  B("**Feature engineering:** vehicle age is derived from the model year, and a model-popularity feature counts how often each exact model is listed (there are too many distinct model names to use them directly)."),
  B("**Preprocessing pipeline:** missing values are filled (median or most common value), numbers are scaled and categories one-hot encoded, fitted on training data only so that no information leaks from the test set."),
  B("**Typical-specification lookup:** fills in the specifications a customer cannot be expected to know (Section 6)."),
  B("**Cross-validation and a fixed test set:** for fair comparison of all models."),
  B("**Hyperparameter tuning:** see below."),
  B("**Honest uncertainty:** the estimate is shown as a range based on the measured error, and vehicles outside the 2018-2023 training years are flagged as low-confidence instead of being presented as normal results."),
  H2("9.2 How the model's accuracy is improved"),
  P(`**1. Hyperparameter tuning (done).** The first XGBoost model used hand-picked settings. A randomized search tried ${tune.method.match(/(\d+) candidates/)[1]} combinations of settings (number of trees, tree depth, learning rate, sampling rates and regularisation), each evaluated by 5-fold cross-validation on the training data only (Bergstra and Bengio, 2012). The best combination was then tested once on the unseen cars of the main test split:`),
  table(["", "MAE", "RMSE", "R²"],
    [
      ["Original settings", rand(tune.test_before.MAE), rand(tune.test_before.RMSE), tune.test_before.R2.toFixed(4)],
      ["Tuned settings (model used by the app)", rand(XGB.MAE), rand(XGB.RMSE), XGB.R2.toFixed(4)],
      ["Change", chg(XGB.MAE, tune.test_before.MAE), chg(XGB.RMSE, tune.test_before.RMSE), ""],
    ], [2826, 2100, 2100, 2000]),
  gap(),
  P("The tuned settings are now part of the training script, so the model the application uses is the tuned one."),
  P("**2. Correcting the data (done).** Fixing the three data errors in Section 7.3 gave the model correct fuel-consumption and brand information to learn from."),
  P("**3. Regular retraining (process in place).** Car prices change over time. The documented pipeline (correct the data, train, copy the model into the application) can be rerun on newly collected listings, for example every quarter, so that the model keeps up with the market."),
  P("**4. Learning from real outcomes (next step).** Each valuation session is stored in the database. Adding the price actually agreed with each customer would allow the model to be calibrated from advertised prices to real trade-in values, and to be measured against real outcomes rather than listings."),
  P("**5. Using condition data (future).** Once enough sessions have both NLP condition findings and agreed prices, the findings can become model features, so that condition affects the estimate based on evidence rather than guesswork."),
  P("**6. Price history and time series models (future).** Collecting listings repeatedly over time would turn the snapshot into a true time series (Section 8.3)."),
  P("**7. Growing the NLP training data (future).** Real, anonymised customer answers can be labelled and added to the NLP classifier's training examples."),
);

// 10 NLP
sections.push(
  H1("10. Natural Language Processing"),
  P("The chatbot asks whether the car has been in an accident and whether it has dents, windscreen damage, respray work or aftermarket modifications. Customers answer in their own words. NLP turns those answers into structured findings in four steps (tradesmart-flask/condition_nlp.py):"),
  (newList(), N("**Splitting:** the answer is split into separate mentions (\"dent on the bonnet and a chip in the windscreen\" becomes two), and negative mentions such as \"windscreen is fine\" are ignored.")),
  N(`**Intent classification:** each mention is classified into one of eight categories by a model trained with TF-IDF text features and Logistic Regression on ${nlp.n_training_sentences} labelled example answers. It scored ${pct(nlp.held_out_accuracy, 0)} accuracy on ${nlpTest} held-out examples. The examples were written by the group because no real customer answers exist yet; this small test set makes the accuracy indicative only.`),
  N("**Entity extraction:** rules extract useful details, such as dent size (\"about the size of a golf ball\" is small, \"4 cm\" is medium), the type of modification, and whether it was fitted by a reputable installer or by the owner."),
  N("**Consistency checks:** a finding is flagged for review when the model's confidence is low, the answer is vague (\"not sure\"), or the answer contradicts itself, for example \"no accidents\" followed by \"resprayed after a crash\"."),
  P("Examples from testing the application:"),
  table(["Customer wrote", "Category", "Detail extracted", "Confidence / flag"],
    [
      ["small dent about the size of a golf ball on the door", "Dents / scratches", "small, about the size of a golf ball", "87%"],
      ["aftermarket rims fitted by a professional shop", "Aftermarket modifications", "wheels; reputable installer", "82%"],
      ["bumper resprayed after a crash (customer said: no accidents)", "Respray / paintwork", "-", "40%, flagged: contradiction"],
      ["windscreen is fine", "(ignored: negative mention)", "-", "-"],
    ], [3100, 2100, 2326, 1500]),
  gap(),
  P("The findings are shown to the customer and stored in the CONDITION_FINDING table, but they **do not change the price**: the dataset contains no information about condition, so there is no evidence of how much a dent should reduce the value. Using condition in the price is part of the improvement plan (Section 9.2). Speech recognition was not implemented; letting customers speak their answers would be a natural extension, as the same NLP steps could process the transcribed text."),
);

// 11 Deep learning
sections.push(
  H1("11. Deep Learning"),
  P(`A **multi-layer perceptron (MLP)**, a feed-forward deep neural network, was trained with TensorFlow/Keras on exactly the same features and data split as the other models (tradesmart-ml/src/train_deep_learning.py). Its architecture is: ${R["Deep Learning (MLP)"].architecture}.`),
  B("**Target scaling:** prices range from about R59 000 to R12 million, so they are standardised before training to keep the learning stable."),
  B("**Batch normalisation and dropout** reduce overfitting to the roughly 13 000 training cars."),
  B(`**Early stopping and learning-rate reduction:** training stops when the error on a validation split stops improving (it stopped after ${R["Deep Learning (MLP)"].epochs_trained} epochs) and keeps the best weights.`),
  P(`The MLP reached R² ${R["Deep Learning (MLP)"].R2.toFixed(3)} (MAE ${rand(R["Deep Learning (MLP)"].MAE)}). It clearly beats Linear Regression but not the tree ensembles. This is a common result for structured, tabular data of this size, where gradient-boosted trees usually outperform neural networks; deep learning tends to lead on large volumes of unstructured data. That is where it fits a future version of TradeSmart AI: a **convolutional neural network (CNN)** could assess damage from photos of the car, and a **speech-recognition** model could let customers speak their answers.`),
);

// 12 Chatbot
sections.push(
  H1("12. Chatbot"),
  P("The customer-facing part of TradeSmart AI is a guided chatbot on the dealership's website. It replaces the first conversation with a sales consultant and works at any time, without a login. The conversation has five steps:"),
  (newList(), N("**Vehicle:** the customer starts typing a make and model, and matching vehicles from the 2 393 known models appear as they type.")),
  N("**Year and mileage:** checked immediately; common formats such as \"85 000\", \"85,000\" and \"85k\" are understood, and unreadable values get a clear request to try again."),
  N("**Condition:** the customer describes the car in their own words or skips; the bot replies with what the NLP model noted."),
  N("**Deposit:** an optional cash deposit towards another vehicle."),
  N("**Contact details:** the customer's name, plus phone and email only if they tick the POPIA consent box."),
  P("The bot then shows the estimate, its range, the model's measured accuracy and any low-confidence warning, and saves the session to the database. Every submission is also appended to a log file that opens in Excel, giving the dealership a simple record of every enquiry without customers needing an account. The chatbot is built with Flask (Python) and htmx, so all logic runs on the server in Python."),
);

// 13 Practical solution
sections.push(
  H1("13. Practical Solution"),
  P("The working solution consists of three parts, each in its own folder:"),
  B("**tradesmart-flask:** the web application and chatbot; started with a one-click launcher that installs everything it needs on first run."),
  B("**tradesmart-ml:** data correction, training and evaluation of all models, the NLP classifier and the time series analysis."),
  B("**database:** the SQL Server script that creates the six tables and loads their data (including all 16 453 listings), and the ERD."),
  P("[[Add screenshots of the chatbot (vehicle search, condition step, result card) and of the database tables in SSMS here.]]"),
  P("[[Add the GitHub repository and GitHub Project board links here.]]"),
);

// References
sections.push(
  H1("References"),
  ...[
    "Adewoyin, V. (2023) used-car-price-prediction [Source code and dataset]. GitHub. Available at: https://github.com/vaadewoyin/used-car-price-prediction (MIT licence).",
    "AutoTrader South Africa (2023) Used cars for sale. Available at: https://www.autotrader.co.za (data collected 23-24 April 2023 by Adewoyin, 2023).",
    "Bergstra, J. and Bengio, Y. (2012) 'Random search for hyper-parameter optimization', Journal of Machine Learning Research, 13, pp. 281-305.",
    "Breiman, L. (2001) 'Random forests', Machine Learning, 45(1), pp. 5-32.",
    "Chen, T. and Guestrin, C. (2016) 'XGBoost: A scalable tree boosting system', Proceedings of the 22nd ACM SIGKDD International Conference on Knowledge Discovery and Data Mining, pp. 785-794.",
    "Pedregosa, F. et al. (2011) 'Scikit-learn: Machine learning in Python', Journal of Machine Learning Research, 12, pp. 2825-2830.",
    "Abadi, M. et al. (2016) 'TensorFlow: A system for large-scale machine learning', 12th USENIX Symposium on Operating Systems Design and Implementation, pp. 265-283.",
    "Republic of South Africa (2013) Protection of Personal Information Act 4 of 2013. Pretoria: Government Printer.",
    "[[Add any other sources the group used, in the same style.]]",
  ].map((t) => new Paragraph({ children: runs(t), alignment: AlignmentType.LEFT, spacing: { line: LINE_15, after: 120 }, indent: { left: 720, hanging: 720 } })),
  H1("Appendix: Grammarly Report"),
  P("[[Insert the Grammarly report or certificate here, as required by the brief.]]"),
);

// ---------- document ----------
const doc = new Document({
  creator: "TradeSmart AI group",
  title: "TradeSmart AI - Project Documentation (draft)",
  styles: {
    default: { document: { run: { font: FONT, size: SIZE } } },
    paragraphStyles: [
      { id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { font: FONT, size: 32, bold: true, color: "1F2937" },
        paragraph: { spacing: { before: 240, after: 240 }, outlineLevel: 0, keepNext: true } },
      { id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { font: FONT, size: 28, bold: true, color: "1F2937" },
        paragraph: { spacing: { before: 240, after: 120 }, outlineLevel: 1, keepNext: true } },
      { id: "Heading3", name: "Heading 3", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { font: FONT, size: SIZE, bold: true },
        paragraph: { spacing: { before: 200, after: 100 }, outlineLevel: 2, keepNext: true } },
      // Contents entries: single-spaced so the list fits on one page
      { id: "TOC1", name: "toc 1", basedOn: "Normal", next: "Normal",
        paragraph: { spacing: { line: 240, before: 60, after: 0 } } },
      { id: "TOC2", name: "toc 2", basedOn: "Normal", next: "Normal",
        paragraph: { spacing: { line: 240, before: 0, after: 0 }, indent: { left: 240 } } },
    ],
  },
  numbering: {
    config: [
      { reference: "bullets", levels: [{ level: 0, format: LevelFormat.BULLET, text: "\u2022", alignment: AlignmentType.LEFT,
        style: { paragraph: { indent: { left: 720, hanging: 360 } } } }] },
      { reference: "numbers", levels: [{ level: 0, format: LevelFormat.DECIMAL, text: "%1.", alignment: AlignmentType.LEFT,
        style: { paragraph: { indent: { left: 720, hanging: 360 } } } }] },
    ],
  },
  features: { updateFields: true },
  sections: [{
    properties: { page: { size: { width: 11906, height: 16838 }, margin: { top: 1440, bottom: 1440, left: 1440, right: 1440 } } },
    footers: { default: new Footer({ children: [new Paragraph({ alignment: AlignmentType.CENTER,
      children: [new TextRun({ children: ["Page ", PageNumber.CURRENT] })] })] }) },
    children: sections,
  }],
});

fs.mkdirSync(OUT_DIR, { recursive: true });
Packer.toBuffer(doc).then((buf) => {
  fs.writeFileSync(OUT, buf);
  console.log(`Wrote ${OUT}`);
  console.log(`Problem definition: ${wWhat} words (2.1, limit 190), ${wTotal} total (limit 250)`);
});
