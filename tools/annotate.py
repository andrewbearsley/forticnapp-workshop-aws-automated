#!/usr/bin/env python3
"""Draw callout boxes on workshop screenshots.

Finds a label with OCR, then draws a magenta box around it. Magenta appears
nowhere in the FortiCNAPP or AWS palette, so a box can never be mistaken for a
severity colour or a selection state.

Usage:
    annotate.py IMAGE "Cloud accounts" "Next"
    annotate.py IMAGE "Alerts@2"          # second match, top to bottom
    annotate.py IMAGE "Alerts:x<180"      # only matches left of x=180
    annotate.py IMAGE --no-numbers "Next"

Writes in place. Keep the source capture, this is destructive.
"""
import re
import subprocess
import sys
from PIL import Image, ImageDraw, ImageFont

PINK = (255, 45, 149)
PAD = 6
WIDTH = 3
FONTS = [
    "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
    "/System/Library/Fonts/Helvetica.ttc",
]


SCALE = 3  # tesseract wants roughly 300 DPI; console captures are about 96


def _tsv(img, tag):
    import tempfile

    with tempfile.NamedTemporaryFile(suffix=".png") as tmp:
        img.save(tmp.name)
        tsv = subprocess.run(
            ["tesseract", tmp.name, "stdout", "tsv"], capture_output=True, text=True
        ).stdout
    rows = []
    for line in tsv.splitlines()[1:]:
        f = line.split("\t")
        if len(f) < 12 or not f[11].strip():
            continue
        rows.append(
            {
                "text": f[11].strip(),
                "left": int(f[6]) // SCALE,
                "top": int(f[7]) // SCALE,
                "w": int(f[8]) // SCALE,
                "h": int(f[9]) // SCALE,
                "line": (tag,) + tuple(f[2:5]),
            }
        )
    return rows


def ocr_words(path):
    """OCR upscaled, then again inverted.

    Upscaling fixes small console type. The inverted pass reads white text on
    the blue Next and Deploy buttons, which the normal pass misses.
    """
    from PIL import ImageOps

    im = Image.open(path).convert("RGB")
    big = im.resize((im.width * SCALE, im.height * SCALE), Image.LANCZOS)
    return _tsv(big, "n") + _tsv(ImageOps.invert(big), "i")


OPS = {
    "<": lambda a, b: a < b,
    ">": lambda a, b: a > b,
    "<=": lambda a, b: a <= b,
    ">=": lambda a, b: a >= b,
}


def passes(constraint, box):
    """Check a position constraint such as x<180 or y>=400."""
    m = re.fullmatch(r"\s*([xy])\s*(<=|>=|<|>)\s*(\d+)\s*", constraint)
    if not m:
        raise ValueError(f"bad constraint: {constraint!r}, expected e.g. x<180")
    axis, op, value = m.groups()
    return OPS[op](box[0] if axis == "x" else box[1], int(value))


def find(words, phrase, constraint, occurrence):
    """Match a phrase across consecutive words on one OCR line."""
    wanted = phrase.split()
    hits = []
    for i in range(len(words)):
        run = words[i : i + len(wanted)]
        if len(run) < len(wanted):
            continue
        if any(w["line"] != run[0]["line"] for w in run):
            continue
        got = [w["text"].strip(".,:") for w in run]
        if [g.lower() for g in got] != [x.lower() for x in wanted]:
            continue
        box = (
            min(w["left"] for w in run),
            min(w["top"] for w in run),
            max(w["left"] + w["w"] for w in run),
            max(w["top"] + w["h"] for w in run),
        )
        if constraint and not passes(constraint, box):
            continue
        hits.append(box)
    hits.sort(key=lambda b: (b[1], b[0]))
    if not hits:
        return None
    return hits[occurrence - 1] if occurrence <= len(hits) else None


def load_font(size):
    for p in FONTS:
        try:
            return ImageFont.truetype(p, size)
        except OSError:
            continue
    return ImageFont.load_default()


def main():
    args = sys.argv[1:]
    numbers = True
    if "--no-numbers" in args:
        numbers = False
        args.remove("--no-numbers")
    path, targets = args[0], args[1:]

    im = Image.open(path).convert("RGB")
    draw = ImageDraw.Draw(im)
    words = ocr_words(path)
    scale = max(1.0, im.width / 1400)
    font = load_font(int(19 * scale))
    missing = []

    for n, spec in enumerate(targets, 1):
        constraint = None
        occurrence = 1
        if ":" in spec:
            spec, constraint = spec.split(":", 1)
        if m := re.search(r"@(\d+)$", spec):
            occurrence, spec = int(m.group(1)), spec[: m.start()]

        box = find(words, spec, constraint, occurrence)
        if not box:
            missing.append(spec)
            continue

        x0, y0, x1, y1 = box
        rect = (x0 - PAD, y0 - PAD, x1 + PAD, y1 + PAD)
        draw.rounded_rectangle(rect, radius=5, outline=PINK, width=WIDTH)

        if numbers and len(targets) > 1:
            r = int(13 * scale)
            # Diagonally off the top-left corner, so the badge never sits over
            # the boxed label or the row it belongs to.
            cx = max(r + 1, rect[0] - r)
            cy = max(r + 1, rect[1] - r)
            draw.ellipse((cx - r, cy - r, cx + r, cy + r), fill=PINK)
            draw.text((cx, cy), str(n), fill="white", font=font, anchor="mm")

    im.save(path)
    print(f"{path}: {len(targets) - len(missing)}/{len(targets)} boxed")
    if missing:
        print(f"  NOT FOUND: {missing}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
