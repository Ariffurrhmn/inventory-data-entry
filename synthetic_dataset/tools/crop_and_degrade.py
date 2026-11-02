"""
Post-process synthetic document screenshots:
1. Auto-crop the grey page background down to the white/cream "sheet" content + a small margin.
2. Apply degradation effects (blur, rotation w/ fill, brightness/contrast fade) per manifest.json,
   matching what the CSS degrade-* classes intended (headless Chrome screenshot doesn't apply CSS
   filter to the full composited page consistently, so we do it here instead as ground truth).
3. Save final images as JPEG (mimics a phone-camera capture better than lossless PNG) into
   synthetic_dataset/images/, replacing the raw screenshots.
"""
import json
import os
from PIL import Image, ImageFilter, ImageEnhance
import random

BASE = r"E:\.shortcut-targets-by-id\1yOBXNuSORBcOSWDhEg-YF1MEWIDvc8J2\Capstone- Inventory Management System\synthetic_dataset"
IMG_DIR = os.path.join(BASE, "images")
MANIFEST = os.path.join(BASE, "manifest.json")

random.seed(20260928)

def autocrop(img, bg_tolerance=10):
    """Crop away the uniform grey page background, keeping the sheet + small margin."""
    gray = img.convert("L")
    w, h = img.size
    bg = gray.getpixel((2, 2))  # corner pixel = background color
    px = gray.load()

    def row_is_bg(y):
        for x in range(0, w, 4):
            if abs(px[x, y] - bg) > bg_tolerance:
                return False
        return True

    def col_is_bg(x):
        for y in range(0, h, 4):
            if abs(px[x, y] - bg) > bg_tolerance:
                return False
        return True

    top = 0
    while top < h and row_is_bg(top):
        top += 1
    bottom = h - 1
    while bottom > top and row_is_bg(bottom):
        bottom -= 1
    left = 0
    while left < w and col_is_bg(left):
        left += 1
    right = w - 1
    while right > left and col_is_bg(right):
        right -= 1

    margin = 20
    top = max(0, top - margin)
    left = max(0, left - margin)
    bottom = min(h - 1, bottom + margin)
    right = min(w - 1, right + margin)
    if right <= left or bottom <= top:
        return img
    return img.crop((left, top, right + 1, bottom + 1))


def apply_degradation(img, degrade_type):
    if not degrade_type:
        return img
    if degrade_type == "degrade-blur":
        return img.filter(ImageFilter.GaussianBlur(radius=1.1))
    if degrade_type == "degrade-rotate":
        angle = random.uniform(-3.5, 3.5)
        rotated = img.rotate(angle, expand=True, fillcolor=(233, 233, 233), resample=Image.BICUBIC)
        return rotated
    if degrade_type == "degrade-fade":
        img = ImageEnhance.Contrast(img).enhance(0.75)
        img = ImageEnhance.Brightness(img).enhance(1.12)
        img = ImageEnhance.Color(img).enhance(0.6)
        return img
    if degrade_type == "degrade-lowcontrast":
        img = ImageEnhance.Contrast(img).enhance(0.65)
        img = ImageEnhance.Brightness(img).enhance(1.08)
        return img
    return img


def main():
    with open(MANIFEST, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    ok, failed = 0, []
    for entry in manifest:
        name = entry["file"]
        png_path = os.path.join(IMG_DIR, f"{name}.png")
        jpg_path = os.path.join(IMG_DIR, f"{name}.jpg")
        if not os.path.exists(png_path):
            failed.append(name)
            continue
        try:
            img = Image.open(png_path).convert("RGB")
            img = autocrop(img)
            img = apply_degradation(img, entry.get("degrade_type"))
            img.save(jpg_path, "JPEG", quality=88)
            os.remove(png_path)
            ok += 1
        except Exception as e:
            failed.append(f"{name}: {e}")

    print(f"Processed {ok} images.")
    if failed:
        print(f"Failed ({len(failed)}):")
        for f_ in failed[:20]:
            print(" -", f_)


if __name__ == "__main__":
    main()
