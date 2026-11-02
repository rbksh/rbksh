"""Generate assets/chaos.svg: five double pendulums whose starting angles differ
by 1e-4 rad. They begin as one, then the butterfly effect tears them apart.
Physics is integrated here (RK4); the SVG just replays it with SMIL."""
import sys
import numpy as np

OUT = sys.argv[1] if len(sys.argv) > 1 else "assets/chaos.svg"
W, H = 1000, 380
DUR, FPS = 24.0, 30
G, L1, L2, M1, M2 = 9.81, 1.0, 1.0, 1.0, 1.0
EPS = 1e-4
COLORS = ["#5eead4", "#818cf8", "#f472b6", "#fbbf24", "#e2e8f0"]
PIV = np.array([255.0, 190.0]); SC = 80.0   # pixels per metre
PLOT = (520, 92, 960, 270)                    # theta_2(t) panel


def deriv(s):
    t1, w1, t2, w2 = s
    d = t1 - t2
    den = 2 * M1 + M2 - M2 * np.cos(2 * d)
    a1 = (-G * (2 * M1 + M2) * np.sin(t1) - M2 * G * np.sin(t1 - 2 * t2)
          - 2 * np.sin(d) * M2 * (w2 * w2 * L2 + w1 * w1 * L1 * np.cos(d))) / (L1 * den)
    a2 = (2 * np.sin(d) * (w1 * w1 * L1 * (M1 + M2) + G * (M1 + M2) * np.cos(t1)
          + w2 * w2 * L2 * M2 * np.cos(d))) / (L2 * den)
    return np.array([w1, a1, w2, a2])


def simulate(t1, t2):
    s, dt, sub = np.array([t1, 0.0, t2, 0.0]), 1 / FPS / 40, 40
    out = []
    for _ in range(int(DUR * FPS) + 1):
        out.append(s.copy())
        for _ in range(sub):
            k1 = deriv(s); k2 = deriv(s + dt / 2 * k1); k3 = deriv(s + dt / 2 * k2); k4 = deriv(s + dt * k3)
            s = s + dt / 6 * (k1 + 2 * k2 + 2 * k3 + k4)
    return np.array(out)


def f(v):
    return f"{v:.1f}".rstrip("0").rstrip(".")


def main():
    base1, base2 = np.radians(120), np.radians(-10)
    runs = [simulate(base1 + i * EPS, base2) for i in range(len(COLORS))]
    n = len(runs[0])
    kt = ";".join(f"{i / (n - 1):.4f}" for i in range(n))
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" font-family="ui-monospace,SFMono-Regular,Menlo,Consolas,monospace">',
         """<defs><radialGradient id="bg" cx=".3" cy=".4" r=".9"><stop offset="0" stop-color="#111a2e"/><stop offset="1" stop-color="#05070d"/></radialGradient>
<filter id="g" x="-50%%" y="-50%%" width="200%%" height="200%%"><feGaussianBlur stdDeviation="2.5" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
<clipPath id="reveal"><rect x="%d" y="0" width="0" height="%d"><animate attributeName="width" from="0" to="%d" dur="%ss" repeatCount="indefinite"/></rect></clipPath></defs>"""
         % (PLOT[0], H, PLOT[2] - PLOT[0], DUR),
         f'<rect width="{W}" height="{H}" rx="18" fill="url(#bg)"/>',
         f'<text x="520" y="40" fill="#64748b" font-size="13">// 5 double pendulums. starting angles differ by 0.0001 rad</text>']

    # whole scene loops with a soft fade so the restart is not a jump
    o.append(f'<g><animate attributeName="opacity" values="0;1;1;0" keyTimes="0;.03;.96;1" dur="{DUR}s" repeatCount="indefinite"/>')

    # pendulums: comet trails of the lower bob, then the arms
    for r, col in zip(runs, COLORS):
        t1, t2 = r[:, 0], r[:, 2]
        p1 = PIV + SC * L1 * np.c_[np.sin(t1), np.cos(t1)]
        p2 = p1 + SC * L2 * np.c_[np.sin(t2), np.cos(t2)]
        cum = np.concatenate([[0], np.cumsum(np.linalg.norm(np.diff(p2, axis=0), axis=1))])
        seg = 220
        d = "M" + " ".join(f"{f(x)},{f(y)}" for x, y in p2)
        offs = ";".join(f(seg - c) for c in cum)
        o.append(f'<path d="{d}" fill="none" stroke="{col}" stroke-width="1.6" stroke-linecap="round" stroke-opacity=".75" '
                 f'stroke-dasharray="{seg} {f(cum[-1] + seg)}" stroke-dashoffset="{seg}">'
                 f'<animate attributeName="stroke-dashoffset" values="{offs}" keyTimes="{kt}" dur="{DUR}s" repeatCount="indefinite"/></path>')
    for r, col in zip(runs, COLORS):
        a1 = ";".join(f(-np.degrees(x)) for x in r[:, 0])
        a2 = ";".join(f(-np.degrees(y - x)) for x, y in zip(r[:, 0], r[:, 2]))
        L1p, L2p = SC * L1, SC * L2
        o.append(f'<g transform="translate({f(PIV[0])} {f(PIV[1])})" stroke="{col}" stroke-width="2.2" stroke-linecap="round" fill="{col}" opacity=".85">'
                 f'<g><animateTransform attributeName="transform" type="rotate" values="{a1}" keyTimes="{kt}" dur="{DUR}s" repeatCount="indefinite"/>'
                 f'<line y2="{f(L1p)}"/><circle cy="{f(L1p)}" r="4.5"/>'
                 f'<g transform="translate(0 {f(L1p)})"><g><animateTransform attributeName="transform" type="rotate" values="{a2}" keyTimes="{kt}" dur="{DUR}s" repeatCount="indefinite"/>'
                 f'<line y2="{f(L2p)}"/><circle cy="{f(L2p)}" r="6" filter="url(#g)"/></g></g></g></g>')
    o.append(f'<circle cx="{f(PIV[0])}" cy="{f(PIV[1])}" r="4" fill="#cbd5e1"/>')

    # theta_2(t) plot, revealed in sync
    x0, y0, x1, y1 = PLOT
    o.append(f'<rect x="{x0}" y="{y0}" width="{x1 - x0}" height="{y1 - y0}" fill="none" stroke="#1e293b"/>'
             f'<text x="{x0}" y="{y0 - 10}" fill="#64748b" font-size="12">θ₂(t) — same start, different futures</text>'
             f'<text x="{x1}" y="{y1 + 18}" text-anchor="end" fill="#475569" font-size="11">t = {int(DUR)}s</text>'
             f'<text x="{x0}" y="{y1 + 18}" fill="#475569" font-size="11">t = 0</text>')
    allc = np.concatenate([np.cos(r[:, 2]) * 0 + r[:, 2] for r in runs])
    lo, hi = allc.min(), allc.max()
    o.append('<g clip-path="url(#reveal)" fill="none" stroke-width="1.4">')
    for r, col in zip(runs, COLORS):
        xs = x0 + (x1 - x0) * np.arange(n) / (n - 1)
        ys = y1 - 10 - (y1 - y0 - 20) * (r[:, 2] - lo) / (hi - lo)
        o.append(f'<path d="M' + " ".join(f"{f(x)},{f(y)}" for x, y in zip(xs, ys)) + f'" stroke="{col}" stroke-opacity=".85"/>')
    o.append("</g></g>")

    o.append(f'<text x="520" y="{H - 44}" fill="#cbd5e1" font-size="14">Deterministic ≠ predictable.</text>'
             f'<text x="520" y="{H - 24}" fill="#64748b" font-size="12">same reason a coin toss looks random → Dynamic-Coin-Toss</text>')
    o.append("</svg>")
    open(OUT, "w", encoding="utf-8").write("\n".join(o))
    sep = [np.max(np.abs(np.array([r[i, 2] for r in runs]) - runs[0][i, 2])) for i in range(n)]
    split = next((i / FPS for i, v in enumerate(sep) if v > 0.3), None)
    print(f"size={sum(map(len, o)) / 1024:.0f}KB visible split at t={split}s")


if __name__ == "__main__":
    main()
