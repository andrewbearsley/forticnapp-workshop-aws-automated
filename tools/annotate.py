#!/usr/bin/env python3
"""Draw callout boxes on workshop screenshots.

Finds a label with OCR, then draws a magenta box around it. Magenta appears
nowhere in the FortiCNAPP or AWS palette, so a box can never be mistaken for a
severity colour or a selection state.

Usage:
    annotate.py IMAGE "Cloud accounts" "Next"
    annotate.py IMAGE "Alerts@2"          # second match, top to bottom
    annotate.py IMAGE "Alerts:x<180"      # only matches left of x=180
    annotate.py IMAGE "Simulate IAM permissions<32"   # widen left to take in the toggle
    annotate.py IMAGE --no-numbers "Next"
    annotate.py IMAGE "#1497,719,1550,746"   # literal box, for what OCR cannot read

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
MARGIN = 10  # tesseract drops text that touches the edge, such as a Next button


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
                "left": int(f[6]) // SCALE - MARGIN,
                "top": int(f[7]) // SCALE - MARGIN,
                "w": int(f[8]) // SCALE,
                "h": int(f[9]) // SCALE,
                "line": (tag,) + tuple(f[2:5]),
            }
        )
    return rows


def ocr_words(path):
    """OCR upscaled, then again inverted.

    Upscaling fixes small console type. The inverted pass reads white text on
    the blue Next and Deploy buttons, which the normal pass misses. The margin
    keeps a button sitting on the bottom edge from being dropped.
    """
    from PIL import ImageOps

    im = Image.open(path).convert("RGB")
    big = im.resize((im.width * SCALE, im.height * SCALE), Image.LANCZOS)
    normal = ImageOps.expand(big, MARGIN * SCALE, fill="white")
    inverted = ImageOps.expand(ImageOps.invert(big), MARGIN * SCALE, fill="black")
    return _tsv(normal, "n") + _tsv(inverted, "i")


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


def badge(draw, rect, n, font, scale):
    """Number the box, diagonally off its top-left corner.

    Off the corner rather than on it, so the badge never covers the label it
    points at or the row that label sits in.
    """
    r = int(13 * scale)
    cx = max(r + 1, rect[0] - r)
    cy = max(r + 1, rect[1] - r)
    draw.ellipse((cx - r, cy - r, cx + r, cy + r), fill=PINK)
    draw.text((cx, cy), str(n), fill="white", font=font, anchor="mm")


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
        if spec.startswith("#"):
            # Literal box. Some console buttons, notably white text on the blue
            # Next, defeat tesseract at every psm and threshold we tried.
            rect = tuple(int(v) for v in spec[1:].split(","))
            draw.rounded_rectangle(rect, radius=5, outline=PINK, width=WIDTH)
            if numbers and len(targets) > 1:
                badge(draw, rect, n, font, scale)
            continue

        constraint = None
        occurrence = 1
        grow = 0
        if ":" in spec:
            spec, constraint = spec.split(":", 1)
        if m := re.search(r"<(\d+)$", spec):
            # Widen left to enclose the row's own radio, checkbox or toggle, so
            # the box covers the whole click target and the badge clears it.
            grow, spec = int(m.group(1)), spec[: m.start()]
        if m := re.search(r"@(\d+)$", spec):
            occurrence, spec = int(m.group(1)), spec[: m.start()]

        box = find(words, spec, constraint, occurrence)
        if not box:
            missing.append(spec)
            continue

        x0, y0, x1, y1 = box
        rect = (x0 - PAD - grow, y0 - PAD, x1 + PAD, y1 + PAD)
        draw.rounded_rectangle(rect, radius=5, outline=PINK, width=WIDTH)

        if numbers and len(targets) > 1:
            badge(draw, rect, n, font, scale)

    im.save(path)
    print(f"{path}: {len(targets) - len(missing)}/{len(targets)} boxed")
    if missing:
        print(f"  NOT FOUND: {missing}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
