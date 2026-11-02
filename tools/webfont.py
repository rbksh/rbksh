"""Embed a subset of an OFL font into an SVG as a base64 @font-face, so the
text renders identically everywhere (SVGs inside <img> can't load web fonts)."""
import base64
import io
import os
from fontTools import subset
from fontTools.ttLib import TTFont

FONTS = os.path.join(os.path.dirname(__file__), "..", "fonts")


def face(family, filename, text, weight=400):
    font = TTFont(os.path.join(FONTS, filename))
    missing = sorted({c for c in text if ord(c) not in font.getBestCmap() and c.strip()})
    if missing:
        print(f"  [{filename}] no glyph for: {[hex(ord(c)) for c in missing]}")
    opts = subset.Options()
    opts.layout_features = ["kern", "liga"]
    opts.name_IDs, opts.hinting, opts.notdef_outline = [], False, True
    sub = subset.Subsetter(opts)
    sub.populate(text=text + " ")
    sub.subset(font)
    buf = io.BytesIO()
    font.save(buf)
    b64 = base64.b64encode(buf.getvalue()).decode()
    return (f"@font-face{{font-family:'{family}';font-weight:{weight};"
            f"src:url(data:font/ttf;base64,{b64}) format('truetype')}}")
