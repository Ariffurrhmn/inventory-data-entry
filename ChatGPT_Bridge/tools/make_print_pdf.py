"""Lay out the synthetic documents for printing on A4 paper, as few sheets as possible
while keeping each document close to a realistic size:

- Formal letterhead POs/invoices: 2 per A4 sheet (half-A4 is a normal invoice size).
- Everything else (challan/cash-memo books, order pads, notebook pages, dot-matrix
  printouts, cropped packing slips): 4 per A4 sheet (~9 x 14 cm, memo-pad size).

Dashed lines show where to cut. No labels are printed on the documents (they'd end up
in the photos); the index of what is where is a separate PDF that you don't print.

Run from the project root:  python ChatGPT_Bridge/tools/make_print_pdf.py
"""
import glob
import os
import tempfile

from PIL import Image, ImageOps
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
APPROVED = os.path.join(ROOT, "ChatGPT_Bridge", "4_approved")
DATASET = os.path.join(ROOT, "Dataset")
OUT = os.path.join(ROOT, "ChatGPT_Bridge", "print")

HALF_DOCS = {"PO_01", "PO_02", "PO_03", "PO_06", "CC_01", "CC_02", "CC_06", "CC_09"}  # formal letterhead
CLASS_FOLDER = {"PO": "Purchase_Order", "DN": "Delivery_Note", "CC": "Customer_Copy"}

W, H = A4
MARGIN = 6 * mm   # most printers can't print to the edge
GAP = 4 * mm      # space between documents for cutting
PAD = 1.5 * mm    # cut line distance from the document
TMP = tempfile.mkdtemp()


def as_jpeg(path, crop=False):
    """Big ChatGPT PNGs make a huge PDF; high-quality JPEG looks the same in print.
    crop=True trims the blank bottom of mostly-empty pages (packing slips)."""
    im = Image.open(path).convert("RGB")
    if crop:
        box = ImageOps.invert(im.convert("L")).point(lambda v: 255 if v > 40 else 0).getbbox()
        im = im.crop((0, 0, im.width, min(im.height, box[3] + 60)))
    out = os.path.join(TMP, os.path.basename(path) + ".jpg")
    im.save(out, quality=92)
    return ImageReader(out)


def fit(img_w, img_h, box_w, box_h):
    s = min(box_w / img_w, box_h / img_h)
    return img_w * s, img_h * s


def slots(per_page):
    """(centre x, centre y, width, height) of each slot on the page."""
    aw, ah = W - 2 * MARGIN, H - 2 * MARGIN
    if per_page == 2:   # stacked halves
        sh = (ah - GAP) / 2
        return [(W / 2, H - MARGIN - sh / 2, aw, sh), (W / 2, MARGIN + sh / 2, aw, sh)]
    sw, sh = (aw - GAP) / 2, (ah - GAP) / 2   # 2 x 2 grid
    xs = (MARGIN + sw / 2, W - MARGIN - sw / 2)
    ys = (H - MARGIN - sh / 2, MARGIN + sh / 2)
    return [(x, y, sw, sh) for y in ys for x in xs]


def draw(c, path, cx, cy, sw, sh):
    """Draw a document centred in a slot, rotating it 90 degrees if that fits it bigger."""
    img = as_jpeg(path, crop="packing-slip" in path)
    iw, ih = img.getSize()
    bw, bh = sw - 2 * PAD - 1 * mm, sh - 2 * PAD - 1 * mm
    upright = fit(iw, ih, bw, bh)
    turned = fit(iw, ih, bh, bw)
    c.saveState()
    c.translate(cx, cy)
    if turned[0] * turned[1] > upright[0] * upright[1] * 1.05:
        c.rotate(90)
        w, h = turned
    else:
        w, h = upright
    c.drawImage(img, -w / 2, -h / 2, w, h)
    c.setDash(3, 3)
    c.setLineWidth(0.4)
    c.setStrokeGray(0.6)
    c.rect(-w / 2 - PAD, -h / 2 - PAD, w + 2 * PAD, h + 2 * PAD)
    c.restoreState()


def build(filename, title, groups):
    """groups: list of (per_page, [(label, path, dataset folder), ...])."""
    pages = []
    for per_page, items in groups:
        for i in range(0, len(items), per_page):
            pages.append((per_page, items[i:i + per_page]))

    c = canvas.Canvas(os.path.join(OUT, filename), pagesize=A4)
    c.setTitle(title)
    rows = []
    for n, (per_page, items) in enumerate(pages, 1):
        names = ["top", "bottom"] if per_page == 2 else ["top-left", "top-right", "bottom-left", "bottom-right"]
        for k, ((label, path, folder), slot) in enumerate(zip(items, slots(per_page))):
            draw(c, path, *slot)
            rows.append((n, names[k], label, f"Dataset/{folder}/"))
        c.showPage()
    c.save()

    # Separate index (view on screen, don't print)
    idx = canvas.Canvas(os.path.join(OUT, filename.replace(".pdf", "_INDEX_dont_print.pdf")), pagesize=A4)
    idx.setFont("Helvetica-Bold", 13)
    idx.drawString(15 * mm, H - 18 * mm, f"Index for {filename} (don't print this)")
    idx.setFont("Helvetica", 9)
    idx.drawString(15 * mm, H - 25 * mm, "Print the other PDF on A4, colour, 100% / Actual size. Cut along the dashed lines.")
    y = H - 34 * mm
    idx.setFont("Helvetica-Bold", 9)
    for x, t in ((0, "Sheet"), (15, "Position"), (40, "Document"), (80, "Save the photo in")):
        idx.drawString((15 + x) * mm, y, t)
    idx.setFont("Helvetica", 9)
    for row in rows:
        y -= 5 * mm
        if y < 15 * mm:
            idx.showPage()
            idx.setFont("Helvetica", 9)
            y = H - 20 * mm
        for x, t in zip((0, 15, 40, 80), map(str, row)):
            idx.drawString((15 + x) * mm, y, t)
    idx.save()
    print(f"{filename}: {len(pages)} sheets")


os.makedirs(OUT, exist_ok=True)
for old in glob.glob(os.path.join(OUT, "*.pdf")):
    os.remove(old)

# 1) Must print: the 29 ChatGPT documents + 5 packing slips
half, quarter = [], []
for p in sorted(glob.glob(os.path.join(APPROVED, "*.png"))):
    doc = os.path.splitext(os.path.basename(p))[0]
    (half if doc in HALF_DOCS else quarter).append((doc, p, CLASS_FOLDER[doc[:2]]))
for p in sorted(glob.glob(os.path.join(DATASET, "Delivery_Note", "packing-slip-*.png"))):
    quarter.append((os.path.splitext(os.path.basename(p))[0], p, "Delivery_Note"))
build("1_MUST_PRINT.pdf", "Must print", [(2, half), (4, quarter)])

# 2) Optional: the earlier template-made POs and challans already in Dataset/ (A4 printed
#    documents in real life, laid out 2 per sheet)
opt = [(os.path.basename(p), p, "Purchase_Order")
       for p in sorted(glob.glob(os.path.join(DATASET, "Purchase_Order", "*.jpg")))]
opt += [(os.path.basename(p), p, "Delivery_Note")
        for p in sorted(glob.glob(os.path.join(DATASET, "Delivery_Note", "delivery-challan-*.jpg")))]
build("2_OPTIONAL.pdf", "Optional", [(2, opt)])
