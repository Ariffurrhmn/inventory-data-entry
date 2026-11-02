"""Write one ChatGPT image prompt per document into 1_prompts/, plus the
correct answers (ground truth) into answers.csv. Numbers are computed here,
so the totals in each prompt are always right.

Run from the ChatGPT_Bridge folder:  python tools/make_prompts.py
"""
import csv
import os
import random

random.seed(2026)
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROMPTS = os.path.join(HERE, "1_prompts")

COUNTS = {"PO": 10, "DN": 10, "CC": 9}

SHOPS = ["Rahim General Store", "Al-Madina Traders", "Nabil Departmental Store",
         "Shapla Grocery", "Bismillah Store", "Kashem Enterprise", "Green Leaf Mart",
         "Hasan Brothers", "Meghna Store", "Ruposhi Bazar", "Tazin Super Shop",
         "Amin Stationery & Store"]
SUPPLIERS = ["Padma Distribution Ltd.", "Jamuna Wholesale", "Karnaphuli Traders",
             "Dhaka Trade House", "Surma Food Supply", "Teesta Enterprise",
             "Bengal Consumer Goods", "Sonar Bangla Distributors"]
AREAS = ["Mirpur-10, Dhaka", "Uttara Sector 7, Dhaka", "Dhanmondi 27, Dhaka",
         "Badda, Dhaka", "Mohammadpur, Dhaka", "Tongi, Gazipur",
         "Chashara, Narayanganj", "Jatrabari, Dhaka", "Savar, Dhaka"]
ITEMS = [("Miniket Rice 25kg", 1850), ("Soybean Oil 5L", 960), ("Sugar 1kg", 135),
         ("Red Lentils 1kg", 110), ("Atta 2kg", 130), ("Salt 1kg", 42),
         ("Tea 400g", 240), ("Biscuits carton", 720), ("Instant Noodles 8-pack", 160),
         ("Detergent 500g", 95), ("Bath Soap 100g", 55), ("Toothpaste 100g", 120),
         ("Shampoo 340ml", 450), ("Milk Powder 500g", 420), ("Onion 1kg", 65),
         ("Mustard Oil 1L", 290), ("Exercise Book", 45), ("Ball Pen box", 100),
         ("Mineral Water 1.5L", 30), ("Hand Wash 200ml", 140)]

STYLES = {
    "PO": [("printed", "simple black-and-white printed form, plain table with thin borders"),
           ("printed", "company letterhead with a small colored logo at the top, clean modern table"),
           ("printed", "table with a dark colored header row and light grey alternating rows"),
           ("printed", "old-style printed form from a dot-matrix printer, monospace font"),
           ("handwritten", "pre-printed purchase order book page filled in by hand with a blue ballpoint pen")],
    "DN": [("handwritten", "page from a carbon-copy challan book, filled in by hand with a blue ballpoint pen, slight carbon smudges"),
           ("handwritten", "pre-printed challan form with the company name in red, filled in by hand"),
           ("handwritten", "handwritten on plain ruled paper with a rubber stamp of the supplier"),
           ("printed", "simple printed challan from an office printer, black-and-white"),
           ("handwritten", "handwritten in a small spiral notebook page, messy but readable"),
           ("printed", "printed challan with a colored company header and a signature line"),
           ("printed", "old-style dot-matrix printout on continuous paper, monospace font, faint uneven ink")],
    "CC": [("printed", "printed A4 invoice, black-and-white, plain table"),
           ("printed", "printed A4 invoice with a colored company logo and header"),
           ("handwritten", "pre-printed cash memo book page filled in by hand with a blue pen"),
           ("printed", "printed half-page invoice from a dot-matrix printer, monospace font")],
}
COPY_MARKS = [("CUSTOMER COPY", "a red rubber stamp, slightly tilted, in the top-right corner"),
              ("DUPLICATE", "a red rubber stamp near the bottom"),
              ("OFFICE COPY", "printed in small bold capitals under the title"),
              ("CUSTOMER COPY", "printed in bold capitals at the very bottom")]

COMMON = ("The image must show ONLY the document: flat, straight, filling the whole frame, "
          "no table, no hands, no background, no shadows. It will be printed and photographed later. "
          "All text and every number must be spelled exactly as given and be clearly readable. "
          "Do not add any items, numbers, or totals that are not listed here.")


def pick_items():
    rows = []
    for name, price in random.sample(ITEMS, random.randint(2, 5)):
        qty = random.choice([1, 2, 3, 4, 5, 6, 10, 12, 20, 24])
        rows.append((name, qty, price, qty * price))
    return rows


def date():
    return f"{random.randint(1, 28):02d}/{random.randint(7, 10):02d}/2026"


# Title mix agreed in round 1 (review 3_reviews/round_1_PO_02-04.md + ChatGPT reply):
# not every document announces its type. No new random calls here, so PO_01-04
# (already approved) keep exactly the same values.
PO_TITLES = {6: "Order Form", 7: "Order Slip", 8: "Order", 9: None, 10: None}
DN_TITLES = {6: "Challan", 7: "Delivery Note", 8: "Challan", 9: "Delivery Note", 10: None}


COMPACT = "Use normal document-size text (not huge headings), thin lines, a compact practical layout."


def plus_days(d, n):
    day, month, year = map(int, d.split("/"))
    day += n
    if day > 28:
        day, month = day - 28, month + 1
    return f"{day:02d}/{month:02d}/{year}"


def title_line(title, fallback_hint):
    if title is None:
        return f"NO title or heading of any kind. {fallback_hint}"
    return f"Title: \"{title}\"."


def table(rows, prices=True):
    if prices:
        return "\n".join(f"- {n} | Qty {q} | Unit Price Tk {p:,} | Amount Tk {a:,}" for n, q, p, a in rows)
    return "\n".join(f"- {i}. {n} | Qty {q}" for i, (n, q, _, _) in enumerate(rows, 1))


def make(kind, i):
    method, style = STYLES[kind][(i - 1) % len(STYLES[kind])]
    rows = pick_items()
    total = sum(r[3] for r in rows)
    shop, area = random.choice(SHOPS), random.choice(AREAS)
    supplier, d = random.choice(SUPPLIERS), date()
    copy_mark = ""

    if kind == "PO":
        number = f"PO-{random.randint(1000, 9999)}"
        title = PO_TITLES.get(i, "Purchase Order")
        if i <= 4:  # approved in round 1, keep prompt unchanged
            body = (f"Create an image of a PURCHASE ORDER from a Bangladeshi shop to its supplier.\n"
                    f"Style: {style}.\n"
                    f"Title: \"Purchase Order\". P.O. No: {number}. Order Date: {d}.\n"
                    f"Bill To / Ship To: {shop}, {area}.\nSupplier: {supplier}.\n"
                    f"Table columns: Item, Qty, Unit Price (Tk), Amount (Tk). Rows:\n{table(rows)}\n"
                    f"Grand Total: Tk {total:,}.\nAn 'Authorized Signature' line at the bottom.")
        else:
            if title != "Purchase Order":
                style = style.replace("purchase order book", "order pad")
                number = number.replace("PO-", "ORD-")  # "PO-" would give the type away
            body = (f"Create an image of an order sent by a Bangladeshi shop (the buyer) to its supplier, "
                    f"asking the supplier to supply goods.\n"
                    f"Style: {style}.\n"
                    f"{title_line(title, 'The page starts directly with the buyer and supplier details.')}\n"
                    f"Order No: {number}. Order Date: {d}. Required By: {plus_days(d, 5)}.\n"
                    f"From (buyer): {shop}, {area}.\nTo (supplier): {supplier}.\n"
                    f"Line above the table: \"Please supply the following goods:\"\n"
                    f"Table columns: Item, Qty, Rate (Tk), Amount (Tk). Rows:\n{table(rows)}\n"
                    f"Total: Tk {total:,}.\n"
                    f"At the bottom: 'Authorized by' with a signature, for {shop}.\n"
                    f"{COMPACT}")
    elif kind == "DN":
        number = f"DC-{random.randint(100, 999)}"
        title = DN_TITLES.get(i, "Delivery Challan")
        body = (f"Create an image of a DELIVERY CHALLAN (delivery note) from a Bangladeshi wholesaler.\n"
                f"Style: {style}.\n"
                f"{title_line(title, 'Above the signatures write: Received the above goods in good condition.')}\n"
                f"Challan No: {number}. Date: {d}.\n"
                f"From: {supplier}.\nTo: {shop}, {area}.\n"
                f"Table columns: Sl, Item Description, Qty. NO prices anywhere. Rows:\n{table(rows, prices=False)}\n"
                f"At the bottom: a 'Received By' line with a signature and a 'Delivered By' line.\n"
                f"{COMPACT}")
        total = ""
    else:
        number = f"INV-{random.randint(1000, 9999)}"
        copy_mark, where = random.choice(COPY_MARKS)
        title = "Invoice"
        body = (f"Create an image of a sales invoice / cash memo from a Bangladeshi shop that is clearly a COPY.\n"
                f"Style: {style}.\n"
                f"The words \"{copy_mark}\" must appear as {where}, clearly visible.\n"
                + (f"Shop: {supplier}. Customer: {shop}, {area}.\n" if i == 1 else  # CC_01 approved as-is
                   f"Seller: {supplier}, shown as the letterhead/name at the top (no \"Shop:\" label).\n"
                   f"Bill To / Customer: {shop}, {area}.\n")
                + f"At the bottom: an 'Authorised Signature' line with a signature (new signer name).\n"
                f"Invoice No: {number}. Date: {d}.\n"
                f"Table columns: Item, Qty, Rate (Tk), Amount (Tk). Rows:\n{table(rows)}\n"
                f"Total: Tk {total:,}.\n"
                f"{COMPACT}")

    doc_id = f"{kind}_{i:02d}"
    with open(os.path.join(PROMPTS, f"{doc_id}.txt"), "w", encoding="utf-8") as f:
        f.write(body.replace("Ltd..", "Ltd.") + "\n\n" + COMMON + "\n")
    items = "; ".join(f"{n} x{q} @{p}" if kind != "DN" else f"{n} x{q}" for n, q, p, _ in rows)
    return {"doc_id": doc_id, "class": {"PO": "purchase_order", "DN": "delivery_note",
            "CC": "customer_copy"}[kind], "method": method, "title": title or "(none)", "number": number, "date": d,
            "shop": shop, "supplier": supplier, "copy_mark": copy_mark, "items": items,
            "total_tk": total, "status": "waiting"}


rows = [make(k, i) for k, n in COUNTS.items() for i in range(1, n + 1)]
ANSWERS = os.path.join(HERE, "answers.csv")
if os.path.exists(ANSWERS):
    old = {r["doc_id"]: r["status"] for r in csv.DictReader(open(ANSWERS, encoding="utf-8"))}
    for r in rows:
        r["status"] = old.get(r["doc_id"], r["status"])
with open(ANSWERS, "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=rows[0].keys())
    w.writeheader()
    w.writerows(rows)
print(f"{len(rows)} prompts written")
