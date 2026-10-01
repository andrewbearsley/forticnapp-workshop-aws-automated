#!/usr/bin/env python3
"""Build the whole workshop as one PDF, for students who want to read offline.

Renders README.md and every lab-NN/README.md in order, with a cover, a contents
page with page numbers, PDF bookmarks, and links between labs that jump inside
the PDF instead of out to GitHub.

Usage:
    build_pdf.py            # write forticnapp-workshop-aws.pdf at the repo root
    build_pdf.py --check    # exit 1 if the PDF is older than the labs

Run it after any change to a lab, and commit the PDF with the change. --check
compares a hash of the READMEs and images against the one stored in the PDF,
so it belongs in the preflight.

Needs markdown-it-py, pygments, Pillow, pypdf, playwright and Google Chrome,
plus network access: mermaid renders from its CDN.
"""
import datetime
import hashlib
import html
import logging
import pathlib
import re
import subprocess
import sys
import tempfile

from markdown_it import MarkdownIt
from PIL import Image
from playwright.sync_api import sync_playwright
from pygments import highlight
from pygments.formatters import HtmlFormatter
from pygments.lexers import get_lexer_by_name
from pygments.util import ClassNotFound
from pypdf import PdfReader, PdfWriter

# Chrome's PDFs trip a harmless pypdf warning about the trailer size.
logging.getLogger("pypdf").setLevel(logging.ERROR)

ROOT = pathlib.Path(__file__).resolve().parent.parent
PDF = ROOT / "forticnapp-workshop-aws.pdf"
TITLE = "FortiCNAPP Workshop: AWS Integration"
HASH_KEY = "/SourceHash"
# A4 at 18mm margins leaves about 174mm. 1600px keeps screenshots sharp when
# zoomed, and anything wider only adds bytes.
MAX_IMAGE_WIDTH = 1600
# Chrome embeds a JPEG as is but re-encodes a PNG, which doubles the PDF.
# Full chroma at this quality keeps console text clean.
JPEG_QUALITY = 88

ALERTS = {
    "NOTE": ("Note", "#0969da"),
    "TIP": ("Tip", "#1a7f37"),
    "IMPORTANT": ("Important", "#8250df"),
    "WARNING": ("Warning", "#9a6700"),
    "CAUTION": ("Caution", "#d1242f"),
}


def sources():
    return [ROOT / "README.md"] + sorted(ROOT.glob("lab-*/README.md"))


def source_hash():
    h = hashlib.sha256()
    files = sources() + sorted(ROOT.glob("lab-*/images/*"))
    for f in files:
        h.update(str(f.relative_to(ROOT)).encode())
        h.update(f.read_bytes())
    return h.hexdigest()


def repo_url():
    url = subprocess.run(
        ["git", "-C", str(ROOT), "remote", "get-url", "origin"],
        capture_output=True, text=True, check=True,
    ).stdout.strip()
    return re.sub(r"\.git$", "", url.replace("git@github.com:", "https://github.com/"))


def section_id(md):
    # README.md is the overview, lab-NN/README.md is lab-NN.
    return "overview" if md.parent == ROOT else md.parent.name


def slugify(text, seen):
    # GitHub's heading anchors: lowercase, drop punctuation, spaces to hyphens.
    slug = re.sub(r"[^\w\- ]", "", text.lower()).replace(" ", "-")
    n = seen.get(slug, 0)
    seen[slug] = n + 1
    return slug if n == 0 else f"{slug}-{n}"


def highlight_code(code, lang, _attrs):
    if lang == "mermaid":
        return f'<pre class="mermaid">{html.escape(code)}</pre>'
    try:
        lexer = get_lexer_by_name(lang) if lang else None
    except ClassNotFound:
        lexer = None
    if lexer is None:
        return ""
    return highlight(code, lexer, HtmlFormatter(nowrap=True))


def render(md, base, images):
    """Render one README to HTML with ids and links rewritten for one document."""
    sid = section_id(md)
    text = md.read_text()
    if sid == "overview":
        # The cover carries the title, and the download line points at this PDF.
        text = re.sub(r"\A# .*\n", "# Overview\n", text)
        text = "\n".join(l for l in text.splitlines() if PDF.name not in l)

    parser = MarkdownIt("commonmark", {"html": True, "highlight": highlight_code})
    parser.enable(["table", "strikethrough"])
    tokens = parser.parse(text)

    seen = {}
    for i, tok in enumerate(tokens):
        if tok.type == "heading_open":
            title = tokens[i + 1].content
            if tok.tag == "h1":
                tok.attrSet("id", sid)
            else:
                tok.attrSet("id", f"{sid}--{slugify(title, seen)}")
        for child in tok.children or []:
            if child.type == "link_open":
                child.attrSet("href", rewrite_link(child.attrGet("href"), md, base))
            elif child.type == "image":
                child.attrSet("src", images(md.parent / child.attrGet("src")))

    out = parser.renderer.render(tokens, parser.options, {})
    # Raw <a> tags in the markdown point outside the repo. Open them normally.
    out = out.replace(' target="_blank"', "")
    out = alerts(out)
    return f'<section class="part" data-section="{sid}">\n{out}</section>\n'


def rewrite_link(href, md, base):
    if re.match(r"^[a-z]+:", href):
        return href
    if href.startswith("#"):
        return f"#{section_id(md)}--{href[1:]}"
    path, _, frag = href.partition("#")
    target = (md.parent / path).resolve()
    if target.name == "README.md" and target in [s.resolve() for s in sources()]:
        sid = section_id(target)
        return f"#{sid}--{frag}" if frag else f"#{sid}"
    # Anything else in the repo, such as a script, lives on GitHub.
    return f"{base}/blob/main/{target.relative_to(ROOT)}"


def alerts(out):
    """Turn GitHub alert blockquotes into styled boxes, as GitHub renders them."""
    def box(m):
        label, colour = ALERTS[m[1]]
        body = m[2].lstrip("\n")
        if not body.startswith("<"):
            body = "<p>" + body
        return (
            f'<div class="alert" style="--alert:{colour}">'
            f'<p class="alert-title">{label}</p>\n{body}</div>'
        )
    return re.sub(
        r"<blockquote>\s*<p>\[!(NOTE|TIP|IMPORTANT|WARNING|CAUTION)\]\s*(?:</p>)?(.*?)</blockquote>",
        box, out, flags=re.S,
    )


def image_store(tmp):
    """Downscale screenshots and store them as JPEG, to keep the PDF small."""
    cache = {}

    def get(path):
        path = path.resolve()
        if path not in cache:
            im = Image.open(path).convert("RGB")
            if im.width > MAX_IMAGE_WIDTH:
                im = im.resize(
                    (MAX_IMAGE_WIDTH, round(im.height * MAX_IMAGE_WIDTH / im.width)),
                    Image.LANCZOS,
                )
            dest = tmp / f"{len(cache):03d}-{path.stem}.jpg"
            im.save(dest, quality=JPEG_QUALITY, subsampling=0, optimize=True)
            cache[path] = dest.as_uri()
        return cache[path]

    return get


def contents(pages):
    rows = []
    for md in sources():
        sid = section_id(md)
        if sid == "overview":
            title = "Overview"
        else:
            title = md.read_text().splitlines()[0].lstrip("# ").strip()
        num, _, rest = title.partition(": ")
        label = f'<span class="toc-num">{num}</span>{html.escape(rest)}' if rest else html.escape(title)
        if sid == "lab-11":
            rows.append('<li class="toc-group">Optional: integrate AWS via infrastructure as code</li>')
        rows.append(
            f'<li><a href="#{sid}">{label}<span class="toc-dots"></span>'
            f'<span class="toc-page">{pages.get(sid, "")}</span></a></li>'
        )
    return '<section class="contents"><h1>Contents</h1><ol>' + "".join(rows) + "</ol></section>"


def document(body, pages, base, built):
    css = (ROOT / "tools" / "pdf.css").read_text()
    css += HtmlFormatter(style="default").get_style_defs("pre code")
    cover = f"""
<section class="cover">
  <p class="cover-kicker">Hands-on labs</p>
  <p class="cover-title">{TITLE}</p>
  <div class="cover-rule"></div>
  <p class="cover-meta">Built {built}<br><a href="{base}">{base.removeprefix("https://")}</a></p>
  <p class="cover-note">The labs need a live AWS account and the FortiCNAPP console. Use this
  copy to read ahead and follow along. The GitHub repository always has the latest version.</p>
</section>"""
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><title>{TITLE}</title>
<style>{css}</style></head>
<body>{cover}{contents(pages)}{body}
<script type="module">
import mermaid from "https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.esm.min.mjs";
mermaid.initialize({{ startOnLoad: false, theme: "default", flowchart: {{ htmlLabels: true }} }});
await mermaid.run({{ querySelector: "pre.mermaid" }});
document.body.dataset.ready = "1";
</script>
</body></html>"""


def print_pdf(page, html_path, pdf_path):
    page.goto(html_path.as_uri())
    page.wait_for_selector("body[data-ready='1']", timeout=60000)
    page.pdf(path=str(pdf_path), prefer_css_page_size=True, print_background=True,
             outline=True, tagged=True)


def section_pages(pdf_path):
    """Map each section id to its 1-based page, from the PDF's named destinations."""
    reader = PdfReader(pdf_path)
    ids = {section_id(md) for md in sources()}
    return {
        name.lstrip("/"): reader.get_destination_page_number(dest) + 1
        for name, dest in reader.named_destinations.items()
        if name.lstrip("/") in ids
    }


def main():
    if "--check" in sys.argv[1:]:
        if not PDF.exists():
            sys.exit(f"missing {PDF.name}: run tools/build_pdf.py")
        stored = PdfReader(PDF).metadata.get(HASH_KEY)
        if stored != source_hash():
            sys.exit(f"{PDF.name} is stale: run tools/build_pdf.py and commit it")
        print(f"{PDF.name} is current")
        return

    base = repo_url()
    built = datetime.date.today().strftime("%-d %B %Y")
    with tempfile.TemporaryDirectory() as tmp:
        tmp = pathlib.Path(tmp)
        images = image_store(tmp)
        body = "".join(render(md, base, images) for md in sources())
        html_path, draft = tmp / "workshop.html", tmp / "draft.pdf"

        with sync_playwright() as p:
            browser = p.chromium.launch(channel="chrome")
            page = browser.new_page()
            # Pass 1 finds where each lab starts. Pass 2 prints those numbers in
            # the contents. The placeholders hold the same width, so nothing moves.
            html_path.write_text(document(body, {}, base, built))
            print_pdf(page, html_path, draft)
            pages = section_pages(draft)
            html_path.write_text(document(body, pages, base, built))
            print_pdf(page, html_path, draft)
            browser.close()

        if section_pages(draft) != pages:
            sys.exit("contents page numbers moved between passes")
        writer = PdfWriter(clone_from=draft)
        writer.add_metadata({"/Title": TITLE, HASH_KEY: source_hash()})
        writer.write(PDF)

    n = len(PdfReader(PDF).pages)
    print(f"wrote {PDF.name}: {n} pages, {PDF.stat().st_size / 1e6:.1f} MB")


if __name__ == "__main__":
    main()
