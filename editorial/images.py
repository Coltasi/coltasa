#!/usr/bin/env python3
"""Build optimised, metadata-tagged images for coltasa.com.

Usage (repo root): python3 editorial/images.py

Post photos: the master for each post lives in editorial/photos/<post-id>.jpg (not deployed).
For every entry in editorial/images.json this writes to deploy/assets/insights/:
  <id>-640.webp, <id>-960.webp, <id>-1280.webp   responsive WebP, 3:2 crop (what browsers load)
  <id>.jpg                                       1280px 3:2 JPEG fallback, also used in structured data
  <id>-og.jpg                                    1200x630 crop for LinkedIn / X / Slack link previews
Site images (headshot, logos) are resized to what the layout needs, recompressed and tagged.
Every output carries EXIF + XMP: description, title, creator, credit, copyright, licence URL.
Then run `python3 editorial/publish.py images` and `refresh` so pages and structured data pick them up.
"""
import io, json, os
from xml.sax.saxutils import escape
from PIL import Image, ImageOps

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PHOTOS = os.path.join(ROOT, "editorial", "photos")
OUT = os.path.join(ROOT, "deploy", "assets", "insights")
ASSETS = os.path.join(ROOT, "deploy", "assets")
IMAGES = os.path.join(ROOT, "editorial", "images.json")
LICENCES = {"Pexels": "https://www.pexels.com/license/", "Unsplash": "https://unsplash.com/license"}
WIDTHS = (640, 960, 1280)


def xmp(title, desc, creator, credit, rights, licence=None, source=None):
    e = lambda s: escape(s or "")
    alt = lambda s: f'<rdf:Alt><rdf:li xml:lang="x-default">{e(s)}</rdf:li></rdf:Alt>'
    extra = ""
    if licence:
        extra += f"<xmpRights:WebStatement>{e(licence)}</xmpRights:WebStatement>"
    if source:
        extra += f"<photoshop:Source>{e(source)}</photoshop:Source>"
    return (
        '<?xpacket begin="﻿" id="W5M0MpCehiHzreSzNTczkc9d"?>'
        '<x:xmpmeta xmlns:x="adobe:ns:meta/"><rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">'
        '<rdf:Description rdf:about="" xmlns:dc="http://purl.org/dc/elements/1.1/" '
        'xmlns:photoshop="http://ns.adobe.com/photoshop/1.0/" xmlns:xmpRights="http://ns.adobe.com/xap/1.0/rights/">'
        f"<dc:title>{alt(title)}</dc:title><dc:description>{alt(desc)}</dc:description>"
        f"<dc:creator><rdf:Seq><rdf:li>{e(creator)}</rdf:li></rdf:Seq></dc:creator>"
        f"<dc:rights>{alt(rights)}</dc:rights><photoshop:Credit>{e(credit)}</photoshop:Credit>{extra}"
        '</rdf:Description></rdf:RDF></x:xmpmeta><?xpacket end="w"?>').encode("utf-8")


def tags(desc, creator, rights):
    ex = Image.Exif()
    ex[0x010E] = desc      # ImageDescription
    ex[0x013B] = creator   # Artist
    ex[0x8298] = rights    # Copyright
    return ex


def save(im, path, meta, **kw):
    ex, xp = meta
    if path.endswith(".webp"):
        im.save(path, "WEBP", quality=kw.get("q", 78), method=6, exif=ex, xmp=xp)
    elif path.endswith(".png"):
        im.save(path, "PNG", optimize=True, exif=ex)  # PNG: EXIF chunk (Pillow writes no XMP to PNG)
    else:
        im.convert("RGB").save(path, "JPEG", quality=kw.get("q", 80), optimize=True, progressive=True, exif=ex, xmp=xp)


def crop(im, w, h):
    return ImageOps.fit(im, (w, h), Image.LANCZOS, centering=(0.5, 0.5))


def build_posts():
    imgs = json.loads(open(IMAGES).read())
    os.makedirs(OUT, exist_ok=True)
    for pid, m in imgs.items():
        src = Image.open(os.path.join(PHOTOS, pid + ".jpg"))
        src = ImageOps.exif_transpose(src).convert("RGB")
        rights = f"Photo by {m['credit']} on {m['source']}, used under the {m['source']} License"
        meta = (tags(m["alt"], m["credit"], rights),
                xmp(m.get("title") or m["alt"], m["alt"], m["credit"], f"{m['credit']} / {m['source']}",
                    rights, LICENCES.get(m["source"]), m["url"]))
        base = crop(src, 1280, 853)
        for w in WIDTHS:
            save(base if w == 1280 else base.resize((w, round(w * 853 / 1280)), Image.LANCZOS),
                 os.path.join(OUT, f"{pid}-{w}.webp"), meta)
        save(base, os.path.join(OUT, f"{pid}.jpg"), meta, q=80)
        save(crop(src, 1200, 630), os.path.join(OUT, f"{pid}-og.jpg"), meta, q=82)
    print(f"Built {len(imgs)} post images")


def tagged(path):
    return bool(Image.open(path).getexif().get(0x010E))


def build_site():
    """One-off: skips any file already tagged, so re-running never recompresses twice."""
    rights = "Copyright Coltasa"
    # Headshot: shown at most 340px wide (4:5 box), so 680px covers 2x screens.
    p = os.path.join(ASSETS, "colin.jpg")
    if tagged(p) and os.path.exists(p[:-4] + ".webp"):
        im = None
    else:
        im = ImageOps.exif_transpose(Image.open(p)).convert("RGB")
    if im is not None:
        if im.width > 680:
            im = im.resize((680, round(680 * im.height / im.width)), Image.LANCZOS)
        d = "Colin Constantine, Principal at Coltasa, B2B sales strategy and execution"
        meta = (tags(d, "Coltasa", rights), xmp("Colin Constantine", d, "Coltasa", "Coltasa", rights))
        save(im, p, meta, q=82)
        im.save(p[:-4] + ".webp", "WEBP", quality=80, method=6, exif=meta[0], xmp=meta[1])
    # Logos: shown in a ~300x66px box, so 600px wide is plenty.
    for f in sorted(os.listdir(os.path.join(ASSETS, "logos"))):
        if not f.endswith(".png"):
            continue
        p = os.path.join(ASSETS, "logos", f)
        if tagged(p):
            continue
        im = Image.open(p)
        im = im.convert("RGBA") if im.mode in ("P", "LA", "RGBA") or "transparency" in im.info else im.convert("RGB")
        if im.width > 600:
            im = im.resize((600, round(600 * im.height / im.width)), Image.LANCZOS)
        name = f[:-4]
        d = f"{name} logo: a company Colin Constantine has worked at"
        ex = tags(d, name, f"{name} logo, trademark of its owner")
        best = None
        for v in (im, im.convert("RGBA").quantize(256, method=Image.Quantize.FASTOCTREE)):
            b = io.BytesIO(); v.save(b, "PNG", optimize=True, exif=ex)
            best = b.getvalue() if best is None or len(b.getvalue()) < len(best) else best
        open(p, "wb").write(best)  # keep whichever is smaller
    # Social share image
    p = os.path.join(ASSETS, "og-image.png")
    if not tagged(p):
        d = "Coltasa: B2B sales strategy and execution"
        save(Image.open(p), p, (tags(d, "Coltasa", rights), None))
    print("Built site images")


if __name__ == "__main__":
    build_posts()
    build_site()
