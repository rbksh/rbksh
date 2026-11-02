"""Generate assets/fourier.svg: a chain of rotating circles (a truncated
Fourier series) that writes the name, then keeps re-tracing it forever.

Pure SVG + SMIL, no JS, so it animates inside a GitHub README <img>.
"""
import sys
import numpy as np
from fontTools.ttLib import TTFont
from fontTools.pens.basePen import BasePen

TEXT = sys.argv[1] if len(sys.argv) > 1 else "Shesh Shiromani"
FONT = r"C:\Windows\Fonts\segoescb.ttf"
OUT = sys.argv[2] if len(sys.argv) > 2 else "assets/fourier.svg"

W, H = 1000, 380
N = 4096          # samples along the closed curve
K = 260           # epicycles kept
T = 30.0          # seconds per full revolution of the series
BOX = (70, 70, 930, 250)   # where the lettering is fitted


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

    o = []
    o.append(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" font-family="ui-monospace,SFMono-Regular,Menlo,Consolas,monospace">')
    o.append(f"""<defs>
<linearGradient id="ink" gradientUnits="userSpaceOnUse" x1="{BOX[0]}" x2="{BOX[2]}" y1="0" y2="0"><stop offset="0" stop-color="#5eead4"/><stop offset=".5" stop-color="#818cf8"/><stop offset="1" stop-color="#f472b6"/></linearGradient>
<radialGradient id="bg" cx=".5" cy=".45" r=".75"><stop offset="0" stop-color="#111a2e"/><stop offset="1" stop-color="#05070d"/></radialGradient>
<filter id="glow" x="-10%" y="-30%" width="120%" height="160%"><feGaussianBlur stdDeviation="3.2" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
<filter id="tipglow" x="-300%" y="-300%" width="700%" height="700%"><feGaussianBlur stdDeviation="4"/></filter>
<pattern id="grid" width="25" height="25" patternUnits="userSpaceOnUse"><path d="M25 0H0V25" fill="none" stroke="#1d2740" stroke-width=".6"/></pattern>
</defs>""")
    o.append(f'<rect width="{W}" height="{H}" rx="18" fill="url(#bg)"/><rect width="{W}" height="{H}" rx="18" fill="url(#grid)" opacity=".55"/>')
    o.append(f'<line x1="0" y1="{f(dc.imag)}" x2="{W}" y2="{f(dc.imag)}" stroke="#2a3655" stroke-width=".6" stroke-dasharray="2 6"/>')
    o.append(f'<line x1="{f(dc.real)}" y1="0" x2="{f(dc.real)}" y2="{H}" stroke="#2a3655" stroke-width=".6" stroke-dasharray="2 6"/>')

    # trace: faint ghost of the final drawing, then the revealed ink
    o.append('<g fill="none" stroke-linecap="round" stroke-linejoin="round">')
    for a, b, l in runs:
        L = poly_len(a, b) + 0.5
        t0, dur = a / N * T, max((b - a) / N * T, 0.01)
        style = 'stroke="url(#ink)" stroke-width="2.2" filter="url(#glow)"' if l else 'stroke="#64748b" stroke-width=".8" stroke-opacity=".35"'
        o.append(f'<path d="{seg_d(a, b)}" {style} stroke-dasharray="{f(L)} {f(L + 5)}" stroke-dashoffset="{f(L)}">'
                 f'<animate attributeName="stroke-dashoffset" from="{f(L)}" to="0" begin="{t0:.3f}s" dur="{dur:.3f}s" fill="freeze"/></path>')
    # comet that rides along the curve forever (after the first pass, it re-traces the name)
    full = "M" + " ".join(f"{f(p.real)},{f(p.imag)}" for p in np.append(rec, rec[0]))
    Lf = float(np.sum(np.abs(np.diff(np.append(rec, rec[0])))))
    seg = 140
    o.append(f'<path d="{full}" stroke="#e0f2fe" stroke-width="2.6" stroke-dasharray="{seg} {f(Lf + seg)}" stroke-dashoffset="{seg}" opacity=".9" filter="url(#glow)">'
             f'<animate attributeName="stroke-dashoffset" from="{seg}" to="{f(seg - Lf)}" dur="{T}s" repeatCount="indefinite"/></path>')
    o.append("</g>")

    # the machine: nested rotating frames, one per Fourier term
    chain = []
    prev_n, prev_ph = 0, 0.0
    for k, (a, n, ph) in enumerate(terms):
        dn, dph = n - prev_n, np.degrees(ph - prev_ph)
        prev_n, prev_ph = n, ph
        op = max(0.06, 0.55 * (a / terms[0][0]) ** 0.35)
        circ = f'<circle r="{f(a)}" stroke-opacity="{op:.2f}"/>' if a > 1.2 else ""
        arm = f'<path d="M0 0H{f(a)}" stroke-opacity="{min(.9, op + .25):.2f}"/>' if a > 0.4 else ""
        chain.append(f'<g><animateTransform attributeName="transform" type="rotate" from="{f(dph)}" to="{f(dph + 360 * dn)}" dur="{T}s" repeatCount="indefinite"/>{circ}{arm}<g transform="translate({f(a)} 0)">')
    tip = '<circle r="9" fill="#a5b4fc" filter="url(#tipglow)"/><circle r="2.6" fill="#fff"/>'
    o.append(f'<g transform="translate({f(dc.real)} {f(dc.imag)})" fill="none" stroke="#94a3b8" stroke-width=".8">')
    o.append("".join(chain) + tip + "</g></g>" * len(terms))
    o.append("</g>")

    # captions
    o.append(f'<text x="28" y="40" fill="#64748b" font-size="13">// {K} spinning circles, one continuous curve: z(t) = Σ cₙ·e^(i·n·ωt)</text>')
    o.append(f'<g opacity="0"><animate attributeName="opacity" from="0" to="1" begin="{T * 0.97:.1f}s" dur="2s" fill="freeze"/>'
             f'<text x="{W / 2}" y="{H - 52}" text-anchor="middle" fill="#cbd5e1" font-size="16" letter-spacing="1">CS @ BITS Pilani · SST  ·  DSA · ML · Calculus · Statistics · Theoretical Physics</text>'
             f'<text x="{W / 2}" y="{H - 28}" text-anchor="middle" fill="#64748b" font-size="12">the drawing is done. the machine never stops.</text></g>')
    o.append(f'<text x="{W - 28}" y="40" text-anchor="end" fill="#334155" font-size="12">T = {int(T)}s</text>')
    o.append("</svg>")
    open(OUT, "w", encoding="utf-8").write("\n".join(o))
    err = np.max(np.abs(rec - z))
    print(f"contours={len(tour)} runs={len(runs)} max_err={err:.2f}px size={sum(map(len, o)) / 1024:.0f}KB")


if __name__ == "__main__":
    main()
