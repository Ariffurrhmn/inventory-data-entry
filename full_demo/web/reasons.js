/* Shared helpers: plain-language wording for contract findings. Used by the dashboard and the PWA. */
(function (root) {
  const TYPE_LABEL = {
    purchase_order: 'Purchase order', receipt: 'Receipt',
    delivery_note: 'Delivery note', customer_copy: 'Customer copy'
  };
  const SOURCE_LABEL = {
    printed_heading: 'a printed heading',
    document_intent_rule: 'wording that shows a purchase request',
    trained_classifier: 'the trained text model (no heading rule matched)'
  };
  const FIELD = (p) => {
    const m = /^\/?line_items\/(\d+)(?:\/(\w+))?$/.exec(p.replace(/^\//, '/'));
    if (m) {
      const row = 'Row ' + (Number(m[1]) + 1);
      const f = { raw_text: 'item name', quantity: 'quantity', unit_price: 'unit price', line_total: 'line total' }[m[2]];
      return f ? row + ' ' + f : row;
    }
    const t = /^\/totals\/(\w+)$/.exec(p);
    if (t) return { grand_total: 'Grand total', subtotal: 'Subtotal', tax: 'Tax', discount: 'Discount' }[t[1]] || t[1];
    return { '/document_number': 'Document number', '/date': 'Date', '/currency': 'Currency' }[p] || p;
  };
  const REASONS = [
    [/^Arithmetic unavailable: subtotal$/, () => 'Subtotal is not printed, so the line items cannot be checked against it.'],
    [/^Arithmetic unavailable: grand_total$/, () => 'Tax and discount are not printed, so the grand total cannot be proven.'],
    [/^Arithmetic unavailable: line_items\/(\d+)\/multiplication$/, (m) => `Row ${+m[1] + 1}: a number is missing, so quantity × price could not be checked.`],
    [/^Arithmetic mismatch: line_items\/(\d+)\/multiplication$/, (m) => `Row ${+m[1] + 1}: quantity × unit price does not equal the line total.`],
    [/^Arithmetic mismatch: subtotal$/, () => 'The line totals do not add up to the printed subtotal.'],
    [/^Arithmetic mismatch: grand_total$/, () => 'Subtotal + tax − discount does not equal the printed grand total.'],
    [/^Arithmetic mismatch: grand_total_vs_line_sum$/, () => 'The line totals do not add up to the printed grand total.'],
    [/^Missing quantity: line_items\/(\d+)$/, (m) => `Row ${+m[1] + 1}: quantity could not be read.`],
    [/^No extracted line items$/, () => 'No item rows could be read from the document.'],
    [/^Required header missing: (.+)$/, (m) => `${m[1][0].toUpperCase() + m[1].slice(1)} was not found on the document.`],
    [/^Evidence (value_not_in_evidence|partial_numeric_token): (\S+)$/, (m) => `${FIELD(m[2])}: the value is not found in the quoted text from the page (for example a changed number or a thousands comma).`],
    [/^Evidence missing: (\S+)$/, (m) => `${FIELD(m[1])}: no quote from the document backs this value.`],
    [/^Evidence not_in_ocr: (\S+)$/, (m) => `${FIELD(m[1])}: the quoted evidence is not in the OCR text.`],
    [/^Evidence unexpected: (\S+)$/, (m) => `${FIELD(m[1])}: evidence was supplied for an empty field.`],
    [/^Evidence supplied for null field (\S+)$/, (m) => `${FIELD(m[1])}: evidence was supplied for an empty field.`],
    [/^Model reported unresolved uncertainties$/, () => 'The extractor reported rows it was not sure about and left them empty.'],
    [/^OCR corrections are unverified proposals$/, () => 'The extractor proposed text corrections that nobody has verified.'],
    [/^Numeric grouping normalization/, () => 'Amounts with thousands commas were accepted under an unverified English-grouping assumption.']
  ];
  function explainReason(text) {
    for (const [rx, fn] of REASONS) {
      const m = rx.exec(text);
      if (m) return fn(m);
    }
    return text;
  }
  function esc(s) {
    return String(s == null ? '' : s).replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  }
  function why(cl) {
    if (!cl) return '';
    const src = SOURCE_LABEL[cl.decision_source] || cl.decision_source;
    const ev = cl.heading_evidence;
    return ev ? `Decided by ${src}: “${ev}”.` : `Decided by ${src}.`;
  }
  root.Docs = { TYPE_LABEL, explainReason, esc, why, FIELD };
})(typeof window !== 'undefined' ? window : self);
