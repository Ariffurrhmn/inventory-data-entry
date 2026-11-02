// Synthetic document dataset generator.
// Produces N randomized documents per type (purchase_order, receipt, delivery_note, customer_copy)
// as both a ground-truth JSON record and a standalone HTML file (rendered to PNG separately).

const fs = require('fs');
const path = require('path');

const OUT_DIR = path.join(__dirname, 'out');
const HTML_DIR = path.join(OUT_DIR, 'html');
const JSON_DIR = path.join(OUT_DIR, 'json');
[OUT_DIR, HTML_DIR, JSON_DIR].forEach(d => fs.mkdirSync(d, { recursive: true }));

// ---------- deterministic PRNG (seeded, reproducible) ----------
function mulberry32(seed) {
  return function () {
    seed |= 0; seed = (seed + 0x6D2B79F5) | 0;
    let t = Math.imul(seed ^ (seed >>> 15), 1 | seed);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}
const rand = mulberry32(20260928);
const pick = (arr) => arr[Math.floor(rand() * arr.length)];
const randInt = (min, max) => Math.floor(rand() * (max - min + 1)) + min;
const shuffle = (arr) => { const a = [...arr]; for (let i = a.length - 1; i > 0; i--) { const j = Math.floor(rand() * (i + 1));[a[i], a[j]] = [a[j], a[i]]; } return a; };

// ---------- reference data ----------
const SUPPLIERS = [
  'ACME Beverage Distributors', 'Green Valley Foodstuffs Ltd.', 'Rahman & Sons Trading',
  'Dhaka Wholesale Mart', 'Bengal Snacks & Confectionery', 'Padma Distribution House',
  'Sonar Bangla Grocers Supply', 'Karim Enterprise', 'Nabila Foods Ltd.', 'Chittagong Import Co.',
  'Farida Household Goods', 'Meghna Beverages', 'Star Trading Corporation', 'Prime Foods Distributors',
];
const SHOPS = [
  'Corner Store Mart', 'Al-Amin General Store', 'City Grocery', 'Bismillah Store',
  'New Market Traders', 'Sultana Variety Store', 'Green Leaf Grocers', 'Mamun Store',
];
const ADDRESSES = [
  '123 Market Road, Dhaka', '45 Station Bazar, Chattogram', '9 College Road, Sylhet',
  '78 Cantonment Road, Rajshahi', '12 New Market, Khulna', '221 Motijheel C/A, Dhaka',
];
const ITEMS = [
  { name: 'Coca-Cola 500ml can', price: 15 }, { name: 'Sprite 500ml can', price: 15 },
  { name: 'Mineral Water 1L', price: 20 }, { name: 'Pran Mango Juice 250ml', price: 12 },
  { name: 'Basmati Rice 5kg bag', price: 650 }, { name: 'Fresh Milk 1L carton', price: 85 },
  { name: 'Lux Soap 100g', price: 35 }, { name: 'Tibet Toothpaste 100g', price: 60 },
  { name: 'Pran Biscuit Pack', price: 18 }, { name: 'Cooking Oil 1L bottle', price: 175 },
  { name: 'Lipton Tea 100g box', price: 95 }, { name: 'Fresh Eggs (dozen)', price: 140 },
  { name: 'Detergent Powder 1kg', price: 110 }, { name: 'Instant Noodles pack', price: 20 },
  { name: 'Sugar 1kg pack', price: 130 }, { name: 'Salt 1kg pack', price: 40 },
  { name: 'Potato Chips 60g', price: 25 }, { name: 'Chocolate Bar 45g', price: 30 },
  { name: 'Bottled Soda Water 1L', price: 22 }, { name: 'Wheat Flour 2kg bag', price: 150 },
];

const DOC_TYPES = [
  { key: 'purchase_order', label: 'PURCHASE ORDER', numPrefix: 'PO' },
  { key: 'receipt', label: 'RECEIPT', numPrefix: 'RCPT' },
  { key: 'delivery_note', label: 'DELIVERY NOTE', numPrefix: 'DN' },
  { key: 'customer_copy', label: 'CUSTOMER COPY', numPrefix: 'CC' },
];

// production-method mix per type, matching report Table 3.1 (majority/some/some pattern)
const PRODUCTION_MIX = {
  purchase_order: ['printed', 'printed', 'printed', 'handwritten'],
  delivery_note: ['handwritten', 'handwritten', 'printed', 'thermal'],
  customer_copy: ['printed', 'printed', 'thermal', 'handwritten'],
  receipt: ['thermal', 'thermal', 'thermal', 'printed'],
};

function randDate() {
  const y = 2026, m = randInt(1, 9), d = randInt(1, 28);
  return `${y}-${String(m).padStart(2, '0')}-${String(d).padStart(2, '0')}`;
}

function buildDocument(docType, index, seedNoise) {
  const supplier = pick(SUPPLIERS);
  const shop = pick(SHOPS);
  const address = pick(ADDRESSES);
  const lineCount = randInt(2, 6);
  const chosenItems = shuffle(ITEMS).slice(0, lineCount);
  const production = pick(PRODUCTION_MIX[docType.key]);

  // decide if this record is a "flagged" case (~20%) with one injected arithmetic error
  const isFlagged = rand() < 0.2;
  const errorLineIdx = isFlagged ? randInt(0, lineCount - 1) : -1;

  let grandTotal = 0;
  const lineItems = chosenItems.map((item, i) => {
    const qty = randInt(1, 30);
    const unitPrice = item.price;
    let lineTotal = qty * unitPrice;
    let arithmetic_check = 'passed';
    let printedQty = qty;
    if (i === errorLineIdx) {
      // simulate an OCR misread: printed/true qty differs from what the total reflects
      printedQty = qty - randInt(1, 3);
      if (printedQty < 1) printedQty = qty + 1;
      arithmetic_check = 'failed';
    }
    grandTotal += lineTotal;
    return {
      raw_text: item.name,
      quantity: printedQty,
      unit_price: unitPrice,
      line_total: Number(lineTotal.toFixed(2)),
      arithmetic_check,
      _true_quantity: qty,
    };
  });

  const docNumber = `${docType.numPrefix}-${randInt(10000, 99999)}`;
  const submissionId = `${Date.now().toString(16)}-${index}-${randInt(1000, 9999)}`;

  const record = {
    submission_id: submissionId,
    document_type: docType.key,
    document_type_confidence: Number((0.9 + rand() * 0.09).toFixed(2)),
    supplier_name: supplier,
    supplier_address: address,
    shop_name: shop,
    document_date: randDate(),
    document_number: docNumber,
    production_method: production,
    line_items: lineItems.map(({ _true_quantity, ...rest }) => rest),
    grand_total: Number(grandTotal.toFixed(2)),
    review_required: isFlagged,
    _synthetic: true,
    _note: 'Synthetic ground-truth record generated as a stand-in for real vendor/customer documents. Not real data.',
  };

  return { record, production, isFlagged };
}

// ---------- HTML rendering per production method ----------
function escapeHtml(s) { return String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;'); }

function renderPrinted(doc, record) {
  const rows = record.line_items.map(li => `
    <tr>
      <td>${escapeHtml(li.raw_text)}</td>
      <td class="num">${li.quantity}</td>
      <td class="num">${li.unit_price.toFixed(2)}</td>
      <td class="num">${li.line_total.toFixed(2)}</td>
    </tr>`).join('');
  return `
  <div class="sheet printed">
    <div class="doc-header">
      <div class="supplier-name">${escapeHtml(record.supplier_name)}</div>
      <div class="supplier-addr">${escapeHtml(record.supplier_address)}</div>
    </div>
    <div class="doc-title">${escapeHtml(doc.label)}</div>
    <div class="meta-row">
      <span>Date: ${record.document_date}</span>
      <span>${doc.numPrefix} No: ${record.document_number}</span>
    </div>
    <div class="meta-row"><span>Bill To: ${escapeHtml(record.shop_name)}</span></div>
    <table>
      <thead><tr><th>Item</th><th class="num">Qty</th><th class="num">Unit Price</th><th class="num">Line Total</th></tr></thead>
      <tbody>${rows}</tbody>
    </table>
    <div class="totals-row">Grand Total: <span class="num">${record.grand_total.toFixed(2)}</span></div>
  </div>`;
}

function renderThermal(doc, record) {
  const rows = record.line_items.map(li => `
    <div class="t-line">
      <div class="t-name">${escapeHtml(li.raw_text)}</div>
      <div class="t-qtyprice">${li.quantity} x ${li.unit_price.toFixed(2)} = ${li.line_total.toFixed(2)}</div>
    </div>`).join('');
  return `
  <div class="sheet thermal">
    <div class="t-center t-bold">${escapeHtml(record.supplier_name).toUpperCase()}</div>
    <div class="t-center">${escapeHtml(record.supplier_address)}</div>
    <div class="t-dash">------------------------------</div>
    <div class="t-center t-bold">${escapeHtml(doc.label)}</div>
    <div>Date: ${record.document_date}</div>
    <div>No: ${record.document_number}</div>
    <div>Shop: ${escapeHtml(record.shop_name)}</div>
    <div class="t-dash">------------------------------</div>
    ${rows}
    <div class="t-dash">------------------------------</div>
    <div class="t-bold">TOTAL: ${record.grand_total.toFixed(2)}</div>
    <div class="t-center">Thank you!</div>
  </div>`;
}

function renderHandwritten(doc, record) {
  const rows = record.line_items.map(li => `
    <tr>
      <td>${escapeHtml(li.raw_text)}</td>
      <td class="num">${li.quantity}</td>
      <td class="num">${li.unit_price.toFixed(2)}</td>
      <td class="num">${li.line_total.toFixed(2)}</td>
    </tr>`).join('');
  return `
  <div class="sheet handwritten">
    <div class="hw-title">${escapeHtml(doc.label)}</div>
    <div class="hw-meta">${escapeHtml(record.supplier_name)} — ${record.document_date} — ${record.document_number}</div>
    <div class="hw-meta">To: ${escapeHtml(record.shop_name)}</div>
    <table class="hw-table">
      <thead><tr><th>Item</th><th class="num">Qty</th><th class="num">Price</th><th class="num">Total</th></tr></thead>
      <tbody>${rows}</tbody>
    </table>
    <div class="hw-total">Total: ${record.grand_total.toFixed(2)}</div>
  </div>`;
}

const CSS = `
@import url('https://fonts.googleapis.com/css2?family=Caveat:wght@500;600&family=Courier+Prime:wght@400;700&family=Inter:wght@400;500;600;700&display=swap');
* { box-sizing: border-box; }
body { margin: 0; padding: 24px; background: #e9e9e9; font-family: Inter, sans-serif; }
.sheet { width: 720px; margin: 0 auto; background: #fff; padding: 40px 48px; box-shadow: 0 2px 12px rgba(0,0,0,0.15); }

/* printed */
.sheet.printed { font-family: 'Inter', Arial, sans-serif; color: #1a1a1a; }
.sheet.printed .supplier-name { font-size: 20px; font-weight: 700; letter-spacing: 0.5px; }
.sheet.printed .supplier-addr { font-size: 13px; color: #444; margin-bottom: 14px; }
.sheet.printed .doc-title { font-size: 16px; font-weight: 700; text-align: center; border-top: 2px solid #222; border-bottom: 2px solid #222; padding: 6px 0; margin: 12px 0; letter-spacing: 1px; }
.sheet.printed .meta-row { display: flex; justify-content: space-between; font-size: 13px; margin-bottom: 4px; color: #333; }
.sheet.printed table { width: 100%; border-collapse: collapse; margin-top: 16px; font-size: 13px; }
.sheet.printed th { text-align: left; border-bottom: 1.5px solid #222; padding: 6px 4px; font-weight: 700; }
.sheet.printed td { padding: 6px 4px; border-bottom: 1px solid #ccc; }
.sheet.printed .num { text-align: right; }
.sheet.printed .totals-row { text-align: right; font-weight: 700; font-size: 14px; margin-top: 14px; border-top: 2px solid #222; padding-top: 8px; }

/* thermal */
.sheet.thermal { font-family: 'Courier Prime', monospace; width: 380px; padding: 24px 20px; color: #111; font-size: 13px; background: #fdfdf7; }
.sheet.thermal .t-center { text-align: center; }
.sheet.thermal .t-bold { font-weight: 700; }
.sheet.thermal .t-dash { letter-spacing: 1px; margin: 6px 0; }
.sheet.thermal .t-line { display: flex; justify-content: space-between; margin: 4px 0; }
.sheet.thermal .t-name { flex: 1; }
.sheet.thermal .t-qtyprice { white-space: nowrap; margin-left: 8px; }

/* handwritten */
.sheet.handwritten { font-family: 'Caveat', cursive; color: #16305c; font-size: 22px; background: #fffef2; background-image: repeating-linear-gradient(#fffef2, #fffef2 34px, #d9d9c8 35px); }
.sheet.handwritten .hw-title { font-size: 28px; font-weight: 600; text-decoration: underline; margin-bottom: 8px; }
.sheet.handwritten .hw-meta { font-size: 20px; margin-bottom: 4px; }
.sheet.handwritten table.hw-table { width: 100%; margin-top: 10px; border-collapse: collapse; font-size: 20px; }
.sheet.handwritten th { text-align: left; border-bottom: 2px solid #16305c; padding: 4px; }
.sheet.handwritten td { padding: 4px; }
.sheet.handwritten .num { text-align: right; }
.sheet.handwritten .hw-total { margin-top: 10px; font-size: 24px; font-weight: 600; }

/* degradation overlays */
.degrade-blur { filter: blur(0.6px) contrast(0.95); }
.degrade-rotate { transform: rotate(var(--rot, -1.5deg)); }
.degrade-fade { filter: contrast(0.8) brightness(1.08) saturate(0.7); }
.degrade-lowcontrast { filter: contrast(0.72) brightness(1.05); }
`;

function renderHtml(doc, record, production, degradeClass, rotDeg) {
  let body;
  if (production === 'thermal') body = renderThermal(doc, record);
  else if (production === 'handwritten') body = renderHandwritten(doc, record);
  else body = renderPrinted(doc, record);

  const wrapClass = ['wrap', degradeClass].filter(Boolean).join(' ');
  return `<!DOCTYPE html>
<html><head><meta charset="utf-8"><style>${CSS}
.wrap { --rot: ${rotDeg || 0}deg; }
</style></head>
<body><div class="${wrapClass}">${body}</div></body></html>`;
}

// ---------- generate ----------
const PER_TYPE = 30;
const manifest = [];

DOC_TYPES.forEach(doc => {
  for (let i = 0; i < PER_TYPE; i++) {
    const { record, production } = buildDocument(doc, i);
    // ~25% of images get a degradation treatment (mostly clean, per plan)
    const degradeRoll = rand();
    let degradeClass = '';
    let rotDeg = 0;
    if (degradeRoll < 0.10) { degradeClass = 'degrade-blur'; }
    else if (degradeRoll < 0.17) { degradeClass = 'degrade-rotate'; rotDeg = (rand() * 4 - 2).toFixed(2); }
    else if (degradeRoll < 0.22 && production === 'thermal') { degradeClass = 'degrade-fade'; }
    else if (degradeRoll < 0.25) { degradeClass = 'degrade-lowcontrast'; }

    const fname = `${doc.key}_${String(i + 1).padStart(2, '0')}`;
    const html = renderHtml(doc, record, production, degradeClass, rotDeg);
    fs.writeFileSync(path.join(HTML_DIR, `${fname}.html`), html, 'utf-8');
    fs.writeFileSync(path.join(JSON_DIR, `${fname}.json`), JSON.stringify(record, null, 2), 'utf-8');
    manifest.push({
      file: fname,
      document_type: doc.key,
      production_method: production,
      degraded: !!degradeClass,
      degrade_type: degradeClass || null,
      review_required: record.review_required,
    });
  }
});

fs.writeFileSync(path.join(OUT_DIR, 'manifest.json'), JSON.stringify(manifest, null, 2), 'utf-8');
console.log(`Generated ${manifest.length} documents (${PER_TYPE} per type x ${DOC_TYPES.length} types).`);
console.log(`HTML: ${HTML_DIR}`);
console.log(`JSON: ${JSON_DIR}`);
