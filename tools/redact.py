#!/usr/bin/env python3
"""Black out sensitive text in workshop screenshots.

Takes the same target syntax as annotate.py, plus two extras:

    #x0,y0,x1,y1   a literal box, for anything OCR cannot read
    ~SUBSTRING     every OCR word containing SUBSTRING, blacking only that part

The ~ form is what you want for an account ID buried inside an ARN: it keeps
the surrounding ARN readable, which is the part that teaches something.

Usage:
    redact.py IMAGE "911167906565" "~471112613268" "#1480,268,1300,292"

Writes in place. Run it before committing any capture of a live console.
"""
import re
import sys
from PIL import Image, ImageDraw

sys.path.insert(0, __file__.rsplit("/", 1)[0])
import annotate

BLEED = 3


def main():
    path, targets = sys.argv[1], sys.argv[2:]
    im = Image.open(path).convert("RGB")
    draw = ImageDraw.Draw(im)
    # OCR is slow on large captures, so skip it when every target is literal.
    words = [] if all(t.startswith("#") for t in targets) else annotate.ocr_words(path)
    missing = []

    for spec in targets:
        if spec.startswith("~"):
            needle = spec[1:]
            found = False
            for w in words:
                start = w["text"].find(needle)
                if start < 0:
                    continue
                # Map the substring onto the word box by character position.
                # Close enough on a proportional font, and we bleed outwards.
                per = w["w"] / max(1, len(w["text"]))
                x0 = w["left"] + per * start
                x1 = w["left"] + per * (start + len(needle))
                draw.rectangle(
                    (x0 - BLEED, w["top"] - BLEED, x1 + BLEED, w["top"] + w["h"] + BLEED),
                    fill="black",
                )
                found = True
            if not found:
                missing.append(spec)
            continue

        if spec.startswith("#"):
            draw.rectangle(tuple(int(v) for v in spec[1:].split(",")), fill="black")
            continue

        constraint = None
        occurrence = 1
        if ":" in spec:
            spec, constraint = spec.split(":", 1)
        if m := re.search(r"@(\d+)$", spec):
            occurrence, spec = int(m.group(1)), spec[: m.start()]

        box = annotate.find(words, spec, constraint, occurrence)
        if not box:
            missing.append(spec)
            continue
        draw.rectangle(
            (box[0] - BLEED, box[1] - BLEED, box[2] + BLEED, box[3] + BLEED),
            fill="black",
        )

    im.save(path)
    print(f"{path}: {len(targets) - len(missing)}/{len(targets)} redacted")
    if missing:
        print(f"  NOT FOUND: {missing}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
