# Dataset acquisition handoff — 2026-10-19

- Ready for bounded future acquisition: Company Documents v2 English synthetic purchase orders and packing slips; ExpressExpense SRD photographs with manual receipt/customer-copy review. Retain licenses and parent/template IDs. Neither is a complete balanced real-data solution.
- Confirmed overlap: five byte-identical ExpressExpense images already in Customer_Copy; one CORD train-8 visual derivative in Receipt. Exclude/group these during future intake. See overlap_matches.csv.
- Clarify before acquisition: DocILE access/dataset terms; SROIE original image rights/version; WildReceipt dataset license; Roboflow full-resolution examples/source provenance; Senga authorized availability (401). No access requests were submitted.
- Resolve mapping: copy-marked PO/delivery precedence; goods received notes; combined invoice/delivery notes. Preserve current Office Copy, Guest Copy and Duplicate handling.
- Gap: real English delivery-note/challan photographs and independent copy-marked layouts. Proposed 40-per-class collection goals are not verified public yields.

Full evidence: DATASET_SEARCH.md and sources.csv. Samples and annotations remain quarantined under Dataset/external_candidates/. No models trained or candidates merged; existing labels, splits, images and results preserved.
