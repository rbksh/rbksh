"""Generate assets/fourier.svg: a chain of rotating circles (a truncated
Fourier series) that writes the name, then keeps re-tracing it forever.

Pure SVG + SMIL, no JS, so it animates inside a GitHub README <img>.
"""
import sys
import numpy as np
from fontTools.ttLib import TTFont
from fontTools.pens.basePen import BasePen
from webfont import face

TEXT = sys.argv[1] if len(sys.argv) > 1 else "Shesh Shiromani"
import os
FONT = os.environ.get("NAME_FONT", os.path.join(os.path.dirname(__file__), "..", "fonts", "InstrumentSerif-Italic.ttf"))
OUT = sys.argv[2] if len(sys.argv) > 2 else "assets/fourier.svg"

W, H = 1000, 380
N = 4096          # samples along the closed curve
K = 260           # epicycles kept
T = 30.0          # seconds per full revolution of the series
BOX = (60, 80, 940, 270)   # where the lettering is fitted


class FlattenPen(BasePen):
    def __init__(self, glyphset, dx):
        super().__init__(glyphset)
        self.dx, self.contours, self.cur = dx, [], None

    def _moveTo(self, p):
        self.cur = [self._p(p)]

    def _lineTo(self, p):
        self.cur.append(self._p(p))

    def _qCurveToOne(self, p1, p2):
        p0 = np.array(self.cur[-1]); a = np.array(self._p(p1)); b = np.array(self._p(p2))
        for t in np.linspace(0, 1, 9)[1:]:
            self.cur.append(tuple((1 - t) ** 2 * p0 + 2 * (1 - t) * t * a + t * t * b))

    def _curveToOne(self, p1, p2, p3):
        p0 = np.array(self.cur[-1]); a, b, c = (np.array(self._p(q)) for q in (p1, p2, p3))
        for t in np.linspace(0, 1, 11)[1:]:
            self.cur.append(tuple((1 - t) ** 3 * p0 + 3 * (1 - t) ** 2 * t * a + 3 * (1 - t) * t * t * b + t ** 3 * c))

    def _closePath(self):
        if self.cur and len(self.cur) > 2:
            self.contours.append(np.array(self.cur))
        self.cur = None

    _endPath = _closePath

    def _p(self, p):
        return (p[0] + self.dx, -p[1])


def glyph_contours(text):
    font = TTFont(FONT)
    gs, cmap, hmtx = font.getGlyphSet(), font.getBestCmap(), font["hmtx"]
    x, out = 0, []
    for ch in text:
        name = cmap[ord(ch)]
        pen = FlattenPen(gs, x)
        gs[name].draw(pen)
        out += pen.contours
        x += hmtx[name][0]
    return out


def fit(contours):
    allp = np.vstack(contours)
    lo, hi = allp.min(0), allp.max(0)
    s = min((BOX[2] - BOX[0]) / (hi - lo)[0], (BOX[3] - BOX[1]) / (hi - lo)[1])
    off = np.array([(BOX[0] + BOX[2]) / 2, (BOX[1] + BOX[3]) / 2]) - (lo + hi) / 2 * s
    return [c * s + off for c in contours]


def order(contours):
    """Greedy left-to-right-ish tour so the pen-up jumps stay short."""
    rest = sorted(contours, key=lambda c: c[:, 0].min())
    tour, pos = [], rest[0][np.argmin(rest[0][:, 0])]
    while rest:
        best = min(range(len(rest)), key=lambda i: np.min(np.linalg.norm(rest[i] - pos, axis=1)) + 0.15 * (rest[i][:, 0].min() - pos[0]) ** 2 / 50)
        c = rest.pop(best)
        j = np.argmin(np.linalg.norm(c - pos, axis=1))
        c = np.vstack([c[j:], c[:j], c[j:j + 1]])     # start at nearest point, close loop
        tour.append(c)
        pos = c[-1]
    return tour


def build_path(tour):
    pts, label = [], []
    for i, c in enumerate(tour):
        pts.append(c); label += [1] * len(c)
        nxt = tour[(i + 1) % len(tour)][0]
        pts.append(np.linspace(c[-1], nxt, 12)[1:-1]); label += [0] * 10
    return np.vstack(pts), np.array(label)


def resample(pts, label, n):
    closed = np.vstack([pts, pts[:1]])
    seg = np.linalg.norm(np.diff(closed, axis=0), axis=1)
    cum = np.concatenate([[0], np.cumsum(seg)])
    s = np.linspace(0, cum[-1], n, endpoint=False)
    idx = np.clip(np.searchsorted(cum, s, side="right") - 1, 0, len(seg) - 1)
    t = (s - cum[idx]) / np.where(seg[idx] == 0, 1, seg[idx])
    p = closed[idx] + (closed[idx + 1] - closed[idx]) * t[:, None]
    lab = label[idx] & label[(idx + 1) % len(label)]
    return p[:, 0] + 1j * p[:, 1], lab


def f(v):
    return f"{v:.2f}".rstrip("0").rstrip(".")


def main():
    tour = order(fit(glyph_contours(TEXT)))
    pts, label = build_path(tour)
    z, lab = resample(pts, label, N)

    c = np.fft.fft(z) / N
    freqs = np.fft.fftfreq(N, 1 / N).astype(int)
    dc = c[0]
    terms = sorted([(abs(c[i]), freqs[i], np.angle(c[i])) for i in range(1, N)], reverse=True)[:K]

    # reconstruction = exactly what the tip of the chain draws
    tt = np.arange(N) / N
    rec = dc + sum(a * np.exp(1j * (ph + 2 * np.pi * n * tt)) for a, n, ph in terms)

    # split trace into ink runs / pen-up runs so jumps can be drawn faintly
    runs, start = [], 0
    for i in range(1, N + 1):
        if i == N or lab[i] != lab[start]:
            runs.append((start, i, lab[start])); start = i

    def seg_d(a, b):
        idx = list(range(a, min(b + 1, N + 1)))
        q = [rec[i % N] for i in idx]
        return "M" + " ".join(f"{f(p.real)},{f(p.imag)}" for p in q)

    def poly_len(a, b):
        q = np.array([rec[i % N] for i in range(a, min(b + 1, N + 1))])
        return float(np.sum(np.abs(np.diff(q))))

    INK, EMBER, BG = "#ece6d9", "#ff6a3d", "#0a0a0b"
    cap_top = f"{K} spinning circles"
    cap_who = "Computer Science @ BITS Pilani  ·  DPS RK Puram"
    cap_int = "Machine Learning  ·  Competitive Programming  ·  Calculus  ·  Theoretical Physics"
    css = (face("Plex", "IBMPlexMono-Regular.ttf", cap_top + cap_int)
           + face("StixI", "STIXTwoText-Italic.ttf", "zctnieω")
           + face("Stix", "STIXTwoText.ttf", "()=Σ")
           + ".si{font-family:StixI,'Cambria Math',serif;font-style:italic}.sr{font-family:Stix,'Cambria Math',serif}"
           + face("PlexM", "IBMPlexMono-Medium.ttf", cap_who, 500)
           + ".m{font-family:Plex,ui-monospace,Menlo,Consolas,monospace}"
           + ".mm{font-family:PlexM,ui-monospace,Menlo,Consolas,monospace;font-weight:500}")

    o = []
    o.append(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}">')
    o.append(f"""<defs><style>{css}</style>
<radialGradient id="bg" cx=".5" cy=".42" r=".8"><stop offset="0" stop-color="#141413"/><stop offset="1" stop-color="{BG}"/></radialGradient>
<filter id="soft" x="-5%" y="-30%" width="110%" height="160%"><feGaussianBlur stdDeviation="1.6" result="b"/><feComponentTransfer in="b" result="b2"><feFuncA type="linear" slope=".55"/></feComponentTransfer><feMerge><feMergeNode in="b2"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
<filter id="ember" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="2.2" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
<radialGradient id="tipg"><stop offset="0" stop-color="{EMBER}" stop-opacity=".55"/><stop offset="1" stop-color="{EMBER}" stop-opacity="0"/></radialGradient>
<pattern id="dots" width="20" height="20" patternUnits="userSpaceOnUse"><circle cx="10" cy="10" r=".7" fill="#2a2926"/></pattern>
</defs>""")
    o.append(f'<rect width="{W}" height="{H}" rx="14" fill="url(#bg)"/><rect width="{W}" height="{H}" rx="14" fill="url(#dots)"/>')
    # drafting frame: corner ticks + axes through the series' centre
    m, t_ = 16, 14
    for x, y, dx, dy in [(m, m, 1, 1), (W - m, m, -1, 1), (m, H - m, 1, -1), (W - m, H - m, -1, -1)]:
        o.append(f'<path d="M{x} {y + dy * t_}V{y}H{x + dx * t_}" fill="none" stroke="#4a4740" stroke-width="1"/>')
    o.append(f'<path d="M{m + 24} {f(dc.imag)}H{W - m - 24}M{f(dc.real)} {m + 24}V{H - m - 24}" stroke="#2a2824" stroke-width=".8" stroke-dasharray="1 5"/>')

    # trace: ink strokes revealed exactly as the tip passes; pen-up moves stay faint
    o.append('<g fill="none" stroke-linecap="round" stroke-linejoin="round">')
    for a, b, l in runs:
        L = poly_len(a, b) + 0.5
        t0, dur = a / N * T, max((b - a) / N * T, 0.01)
        style = f'stroke="{INK}" stroke-width="1.7" filter="url(#soft)"' if l else 'stroke="#6b665c" stroke-width=".7" stroke-opacity=".35" stroke-dasharray="2 4"'
        if l:
            o.append(f'<path d="{seg_d(a, b)}" {style} stroke-dasharray="{f(L)} {f(L + 5)}" stroke-dashoffset="{f(L)}">'
                     f'<animate attributeName="stroke-dashoffset" from="{f(L)}" to="0" begin="{t0:.3f}s" dur="{dur:.3f}s" fill="freeze"/></path>')
        else:
            o.append(f'<path d="{seg_d(a, b)}" {style} opacity="0"><set attributeName="opacity" to="1" begin="{t0 + dur:.3f}s" fill="freeze"/></path>')
    # once written, the letters take on a faint fill, like ink settling into paper
    glyph_d = "".join("M" + " ".join(f"{f(x)},{f(y)}" for x, y in c) + "Z" for c in tour)
    o.append(f'<path d="{glyph_d}" fill="{INK}" stroke="none" opacity="0"><animate attributeName="opacity" from="0" to=".13" begin="{T:.1f}s" dur="3s" fill="freeze"/></path>')
    # ember comet riding the curve forever
    full = "M" + " ".join(f"{f(p.real)},{f(p.imag)}" for p in np.append(rec, rec[0]))
    Lf = float(np.sum(np.abs(np.diff(np.append(rec, rec[0])))))
    for seg, w, op in [(90, 2.2, .35), (34, 2.4, .95)]:
        o.append(f'<path d="{full}" stroke="{EMBER}" stroke-width="{w}" stroke-opacity="{op}" stroke-dasharray="{seg} {f(Lf + seg)}" stroke-dashoffset="{seg}" filter="url(#ember)">'
                 f'<animate attributeName="stroke-dashoffset" from="{seg}" to="{f(seg - Lf)}" dur="{T}s" repeatCount="indefinite"/></path>')
    o.append("</g>")

    # the machine: nested rotating frames, one per Fourier term
    chain = []
    prev_n, prev_ph = 0, 0.0
    for k, (a, n, ph) in enumerate(terms):
        dn, dph = n - prev_n, np.degrees(ph - prev_ph)
        prev_n, prev_ph = n, ph
        op = max(0.05, 0.32 * (a / terms[0][0]) ** 0.3)
        circ = f'<circle r="{f(a)}" stroke-opacity="{op:.2f}"/>' if a > 1.2 else ""
        arm = f'<path d="M0 0H{f(a)}" stroke-opacity="{min(.7, op + .25):.2f}"/>' if a > 0.4 else ""
        chain.append(f'<g><animateTransform attributeName="transform" type="rotate" from="{f(dph)}" to="{f(dph + 360 * dn)}" dur="{T}s" repeatCount="indefinite"/>{circ}{arm}<g transform="translate({f(a)} 0)">')
    tip = f'<circle r="12" fill="url(#tipg)" stroke="none"/><circle r="2.4" fill="{EMBER}" stroke="none"/>'
    o.append(f'<g transform="translate({f(dc.real)} {f(dc.imag)})" fill="none" stroke="#d6cfc0" stroke-width=".7">')
    o.append(f'<circle r="2" fill="#d6cfc0" stroke="none"/>')
    o.append("".join(chain) + tip + "</g></g>" * len(terms))
    o.append("</g>")

    # captions
    o.append(f'<text x="40" y="48" fill="#8a8476" font-size="17">'
             f'<tspan class="m" font-size="12" letter-spacing=".6">{cap_top}</tspan>'
             f'<tspan class="si" dx="18" fill="#d6cfc0">z</tspan><tspan class="sr" fill="#d6cfc0">(</tspan><tspan class="si" fill="#d6cfc0">t</tspan>'
             f'<tspan class="sr" fill="#d6cfc0">) = </tspan><tspan class="sr" fill="#d6cfc0" font-size="21">Σ</tspan>'
             f'<tspan class="si" dx="4" fill="#d6cfc0">c</tspan><tspan class="si" fill="#d6cfc0" font-size="11" dy="4">n</tspan>'
             f'<tspan class="si" dx="3" dy="-4" fill="#d6cfc0">e</tspan><tspan class="si" fill="#d6cfc0" font-size="11" dy="-8">inωt</tspan></text>')
    o.append(f'<g opacity="0"><animate attributeName="opacity" from="0" to="1" begin="{T * 0.97:.1f}s" dur="2.5s" fill="freeze"/>'
             f'<text class="mm" x="40" y="{H - 58}" fill="{INK}" font-size="14" letter-spacing=".4" xml:space="preserve">{cap_who}</text>'
             f'<text class="m" x="40" y="{H - 36}" fill="#8a8476" font-size="12.5" xml:space="preserve">{cap_int}</text></g>')
    o.append("</svg>")
    open(OUT, "w", encoding="utf-8").write("\n".join(o))
    err = np.max(np.abs(rec - z))
    print(f"contours={len(tour)} runs={len(runs)} max_err={err:.2f}px size={sum(map(len, o)) / 1024:.0f}KB")


if __name__ == "__main__":
    main()
