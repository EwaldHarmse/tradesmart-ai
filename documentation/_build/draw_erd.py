from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

OUT = Path(__file__).resolve().parents[2] / "database" / "TradeSmartAI_ERD.png"

HEADER_BG = "#1f2937"
PK_BG = "#fef3c7"
FK_BG = "#dbeafe"
LINE = "#475569"
ROW_H = 26
HEAD_H = 40
FONT = "Arial"

# name: (x, y_top, width, subtitle, rows[(column, type, kind)])
TABLES = {
    "VEHICLE": (40, 60, 330, "the dataset: 16,453 Autotrader listings", [
        ("VehicleID", "INT", "pk"),
        ("ModelID (FK)", "INT", "fk"),
        ("Make", "NVARCHAR(50)", ""),
        ("Model", "NVARCHAR(150)", ""),
        ("VehicleYear", "SMALLINT", ""),
        ("Mileage", "INT", ""),
        ("Price", "DECIMAL(12,2)", ""),
        ("Transmission", "NVARCHAR(20)", ""),
        ("FuelType", "NVARCHAR(20)", ""),
        ("BodyType", "NVARCHAR(30)", ""),
        ("Colour", "NVARCHAR(60)", ""),
        ("PreviousOwners", "NVARCHAR(10)", ""),
        ("EngineCapacityL", "DECIMAL(3,1)", ""),
        ("CylinderLayout", "NVARCHAR(20)", ""),
        ("DrivenWheels", "NVARCHAR(30)", ""),
        ("PowerKW", "DECIMAL(6,1)", ""),
        ("TorqueNm", "DECIMAL(6,1)", ""),
        ("Acceleration0To100Sec", "DECIMAL(4,1)", ""),
        ("TopSpeedKmh", "DECIMAL(5,1)", ""),
        ("FuelConsumptionL100km", "DECIMAL(4,1)", ""),
        ("CO2EmissionsGKm", "DECIMAL(5,1)", ""),
        ("Seats", "DECIMAL(3,1)", ""),
        ("Doors", "DECIMAL(3,1)", ""),
    ]),
    "CUSTOMER": (570, 60, 330, "who requested the valuation (no login)", [
        ("CustomerID", "INT", "pk"),
        ("FullName", "NVARCHAR(100)", ""),
        ("ContactNumber", "NVARCHAR(20)", ""),
        ("Email", "NVARCHAR(100)", ""),
        ("POPIAConsentGiven", "BIT", ""),
        ("CreatedAt", "DATETIME2", ""),
    ]),
    "VEHICLE_MODEL": (570, 330, 330, "one row per make + model (2,393): model inputs", [
        ("ModelID", "INT", "pk"),
        ("Make", "NVARCHAR(50)", ""),
        ("Model", "NVARCHAR(150)", ""),
        ("BodyType", "NVARCHAR(30)", ""),
        ("Transmission", "NVARCHAR(20)", ""),
        ("FuelType", "NVARCHAR(20)", ""),
        ("DrivenWheels", "NVARCHAR(30)", ""),
        ("EnginePosition", "NVARCHAR(20)", ""),
        ("CylinderLayout", "NVARCHAR(20)", ""),
        ("TypicalPreviousOwners", "NVARCHAR(10)", ""),
        ("EngineCapacityL", "DECIMAL(3,1)", ""),
        ("PowerKW", "DECIMAL(6,1)", ""),
        ("TorqueNm", "DECIMAL(6,1)", ""),
        ("Acceleration0To100Sec", "DECIMAL(4,1)", ""),
        ("TopSpeedKmh", "DECIMAL(5,1)", ""),
        ("FuelConsumptionL100km", "DECIMAL(4,1)", ""),
        ("FuelCapacityL", "DECIMAL(5,1)", ""),
        ("CO2EmissionsGKm", "DECIMAL(5,1)", ""),
        ("Seats", "DECIMAL(3,1)", ""),
        ("Doors", "DECIMAL(3,1)", ""),
        ("ListingCount", "INT", ""),
    ]),
    "VALUATION_SESSION": (1100, 200, 340, "the customer's car + the predicted price", [
        ("SessionID", "INT", "pk"),
        ("CustomerID (FK)", "INT", "fk"),
        ("ModelID (FK)", "INT", "fk"),
        ("VehicleYear", "SMALLINT", ""),
        ("Mileage", "INT", ""),
        ("EstimatedValue", "DECIMAL(12,2)", ""),
        ("EstimatedValueLow", "DECIMAL(12,2)", ""),
        ("EstimatedValueHigh", "DECIMAL(12,2)", ""),
        ("ValuationModelUsed", "NVARCHAR(50)", ""),
        ("OutsideTrainingYears", "BIT", ""),
        ("DesiredCashDeposit", "DECIMAL(12,2)", ""),
        ("CreatedAt", "DATETIME2", ""),
    ]),
    "CONDITION_CATEGORY": (1640, 60, 300, "NLP category lookup (8 rows)", [
        ("CategoryCode", "NVARCHAR(30)", "pk"),
        ("DisplayName", "NVARCHAR(50)", ""),
        ("Description", "NVARCHAR(200)", ""),
    ]),
    "CONDITION_FINDING": (1640, 300, 300, "one row per condition mention (NLP)", [
        ("FindingID", "INT", "pk"),
        ("SessionID (FK)", "INT", "fk"),
        ("CategoryCode (FK)", "NVARCHAR(30)", "fk"),
        ("CustomerText", "NVARCHAR(500)", ""),
        ("ExtractedDetail", "NVARCHAR(200)", ""),
        ("DetectedBy", "NVARCHAR(10)", ""),
        ("Confidence", "DECIMAL(4,3)", ""),
        ("NeedsReview", "BIT", ""),
        ("ReviewReason", "NVARCHAR(300)", ""),
        ("CreatedAt", "DATETIME2", ""),
    ]),
}

# (parent, parent row, child, child row, label)
RELATIONS = [
    ("CUSTOMER", "CustomerID", "VALUATION_SESSION", "CustomerID (FK)", "1 customer ->\nmany sessions"),
    ("VEHICLE_MODEL", "ModelID", "VALUATION_SESSION", "ModelID (FK)", "1 model ->\nmany sessions"),
    ("VEHICLE_MODEL", "ModelID", "VEHICLE", "ModelID (FK)", "1 model ->\nmany listings"),
    ("VALUATION_SESSION", "SessionID", "CONDITION_FINDING", "SessionID (FK)", "1 session ->\nmany findings"),
    ("CONDITION_CATEGORY", "CategoryCode", "CONDITION_FINDING", "CategoryCode (FK)", "1 category -> many findings"),
]

W, H = 1980, 960
fig = plt.figure(figsize=(W / 100, H / 100), dpi=100)
ax = fig.add_axes([0, 0, 1, 1])
ax.set_xlim(0, W)
ax.set_ylim(H, 0)
ax.axis("off")
fig.patch.set_facecolor("white")


def row_y(name, column):
    x, y, w, _, rows = TABLES[name]
    i = [r[0] for r in rows].index(column)
    return y + HEAD_H + i * ROW_H + ROW_H / 2


for name, (x, y, w, sub, rows) in TABLES.items():
    ax.add_patch(Rectangle((x, y), w, HEAD_H, facecolor=HEADER_BG, edgecolor=HEADER_BG))
    ax.text(x + w / 2, y + 15, name, ha="center", va="center", color="white", fontsize=12, fontweight="bold", family=FONT)
    ax.text(x + w / 2, y + 31, sub, ha="center", va="center", color="#e5e7eb", fontsize=7.5, family=FONT)
    split = x + w * 0.56
    for i, (col, typ, kind) in enumerate(rows):
        ry = y + HEAD_H + i * ROW_H
        bg = PK_BG if kind == "pk" else FK_BG if kind == "fk" else "white"
        ax.add_patch(Rectangle((x, ry), w, ROW_H, facecolor=bg, edgecolor="none"))
        ax.text(x + 8, ry + ROW_H / 2, col, va="center", fontsize=10, family=FONT,
                fontweight="bold" if kind == "pk" else "normal", color="#111827")
        ax.text(split, ry + ROW_H / 2, typ, va="center", fontsize=10, family=FONT, color="#111827")
    ax.add_patch(Rectangle((x, y), w, HEAD_H + len(rows) * ROW_H, fill=False, edgecolor=HEADER_BG, linewidth=1.2))


def crow_foot(xe, ye, direction):
    """Three prongs meeting at the line, opening toward the child box edge at xe."""
    d = 12 * direction
    for dy in (-7, 0, 7):
        ax.plot([xe - d, xe], [ye, ye + dy], color=LINE, linewidth=1.2)
    ax.plot([xe - d - 5 * direction] * 2, [ye - 6, ye + 6], color=LINE, linewidth=1.2)  # "many, mandatory" bar


def one_bars(xs, ys, direction):
    for off in (6, 11):
        ax.plot([xs + off * direction] * 2, [ys - 6, ys + 6], color=LINE, linewidth=1.2)


for parent, pcol, child, ccol, label in RELATIONS:
    px, _, pw, _, _ = TABLES[parent]
    cx, _, cw, _, _ = TABLES[child]
    py, cy = row_y(parent, pcol), row_y(child, ccol)
    if cx > px:
        xs, xe = px + pw, cx
    else:
        xs, xe = px, cx + cw
    direction = 1 if xe > xs else -1
    if parent == "CONDITION_CATEGORY":
        # Category sits directly above Finding: a straight vertical line from
        # Category's bottom edge into Finding's top edge
        _, ptop, _, _, prows = TABLES[parent]
        _, ctop, _, _, _ = TABLES[child]
        x = px + pw / 2
        y1, y2 = ptop + HEAD_H + len(prows) * ROW_H, ctop
        ax.plot([x, x], [y1, y2], color=LINE, linewidth=1.2)
        for off in (6, 11):
            ax.plot([x - 6, x + 6], [y1 + off] * 2, color=LINE, linewidth=1.2)
        for dx in (-7, 0, 7):
            ax.plot([x, x + dx], [y2 - 12, y2], color=LINE, linewidth=1.2)
        ax.plot([x - 6, x + 6], [y2 - 17] * 2, color=LINE, linewidth=1.2)
        ax.text(x + 10, (y1 + y2) / 2, label, ha="left", va="center",
                fontsize=8, family=FONT, color="#334155")
        continue
    mid = (xs + xe) / 2
    ax.plot([xs, mid, mid, xe], [py, py, cy, cy], color=LINE, linewidth=1.2)
    one_bars(xs, py, direction)
    crow_foot(xe, cy, direction)
    # Label in the gap between the vertical segment and the child box
    # (below the line when the line comes up from below, so neighbouring labels don't collide)
    lx, ha = (mid + 10, "left") if direction > 0 else (mid - 10, "right")
    if py > cy:
        ax.text(lx, cy + 5, label, ha=ha, va="top", fontsize=8, family=FONT, color="#334155")
    else:
        ax.text(lx, cy - 5, label, ha=ha, va="bottom", fontsize=8, family=FONT, color="#334155")

ax.text(40, 30, "TradeSmart AI - Entity Relationship Diagram", fontsize=15, fontweight="bold", family=FONT, color="#111827")
ax.text(W - 40, 30, "PK = yellow   FK = blue   crow's foot = many", ha="right", fontsize=9, family=FONT, color="#475569")

fig.savefig(OUT, dpi=100, facecolor="white")
print("saved", OUT)
