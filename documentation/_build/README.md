# Document build scripts (not part of the submission)

These regenerate the documentation draft, the poster and the ERD from the
project's real results (tradesmart-ml/outputs). They are only needed if the
numbers change; the finished files are one folder up.

- `build_doc.js`     -> ../TradeSmart_AI_Documentation_DRAFT.docx  (`npm install docx` first)
- `build_poster2.js` -> ../TradeSmart_AI_Poster.pptx               (`npm install pptxgenjs` first)
- `draw_erd.py`      -> ../../database/TradeSmartAI_ERD.png        (needs matplotlib)

Warning: rebuilding the .docx overwrites any edits made in Word.
