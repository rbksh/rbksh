"""Generate assets/bfs.svg: a breadth-first search floods a grid whose walls
spell my name. Every cell lights up at the moment BFS discovers it (colour =
distance), the name appears as the negative space the search routes around,
then the shortest path to the far edge is traced. All numbers shown are real.
"""
import os
import random
import sys
from collections import deque

from PIL import Image, ImageDraw, ImageFont
from webfont import face

OUT = sys.argv[1] if len(sys.argv) > 1 else "assets/bfs.svg"
NAME = "Shesh Shiromani"
HERE = os.path.dirname(os.path.abspath(__file__))
FONT = os.path.join(HERE, "..", "fonts", "IBMPlexMono-Bold.ttf")

W, H = 1000, 420
P, CELL = 6, 5                    # cell pitch / drawn size in px
COLS, ROWS = 160, 44
X0, Y0 = (W - COLS * P) // 2 + 1, 72
NOISE = 0.15
SEED = 8                           # fixed, so the maze is identical on every rebuild

FLOOD, PATH_T, HOLD, FADE = 9.0, 1.8, 6.0, 1.0
INK, MUTED, BG, EMBER = "#ece6d9", "#8a8476", "#0a0a0b", "#ff6a3d"
STOPS = [(0, (84, 81, 74)), (1, (30, 29, 27))]   # one neutral ramp: near = lighter, far = darker


def cmap(t):
    for (a, ca), (b, cb) in zip(STOPS, STOPS[1:]):
        if t <= b:
            u = (t - a) / (b - a)
            return "#%02x%02x%02x" % tuple(round(x + (y - x) * u) for x, y in zip(ca, cb))
    return "#%02x%02x%02x" % STOPS[-1][1]


def name_mask():
    S = 8
    img = Image.new("L", (COLS * S, ROWS * S), 0)
    d = ImageDraw.Draw(img)
    size = 300
    while True:
        fnt = ImageFont.truetype(FONT, size)
        l, t, r, b = d.textbbox((0, 0), NAME, font=fnt)
        if r - l <= COLS * S * 0.9 and b - t <= ROWS * S * 0.62:
            break
        size -= 4
    d.text(((COLS * S - (r - l)) / 2 - l, (ROWS * S - (b - t)) / 2 - t), NAME, font=fnt, fill=255)
    small = img.resize((COLS, ROWS), Image.BOX)
    return [[small.getpixel((x, y)) > 110 for x in range(COLS)] for y in range(ROWS)]


def main():
    letters = name_mask()
    rng = random.Random(SEED)
    near = lambda x, y: any(letters[j][i] for j in range(max(0, y - 1), min(ROWS, y + 2))
                            for i in range(max(0, x - 1), min(COLS, x + 2)))
    src = (0, ROWS // 2)
    wall = [[letters[y][x] or (not near(x, y) and x > 2 and rng.random() < NOISE) for x in range(COLS)] for y in range(ROWS)]

    dist, par = {src: 0}, {src: None}
    q = deque([src])
    while q:
        x, y = q.popleft()
        for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
            if 0 <= nx < COLS and 0 <= ny < ROWS and not wall[ny][nx] and (nx, ny) not in dist:
                dist[nx, ny] = dist[x, y] + 1
                par[nx, ny] = (x, y)
                q.append((nx, ny))
    maxd = max(dist.values())
    right = [(COLS - 1, y) for y in range(ROWS) if (COLS - 1, y) in dist]
    tgt = min(right, key=lambda c: (dist[c], abs(c[1] - ROWS // 2)))
    path, c = [], tgt
    while c:
        path.append(c); c = par[c]
    path.reverse()

    C = FLOOD + PATH_T + 1.2 + HOLD + FADE
    k = lambda t: f"{min(max(t / C, 0), 1):.4f}"
    end_vis = k(C - FADE)
    anim = f'dur="{C:.2f}s" repeatCount="indefinite"'

    def runs(cells):
        rows = {}
        for x, y in cells:
            rows.setdefault(y, []).append(x)
        out = []
        for y, xs in rows.items():
            xs.sort(); s = p = xs[0]
            for x in xs[1:] + [None]:
                if x is not None and x == p + 1:
                    p = x; continue
                out.append(f"M{X0 + s * P} {Y0 + y * P}h{(p - s) * P + CELL}v{CELL}h-{(p - s) * P + CELL}z")
                if x is not None:
                    s = p = x
        return "".join(out)

    reach, plen = len(dist), len(path) - 1
    cap1 = f"bfs from ({src[0]},{src[1]}) on a {COLS}×{ROWS} grid. walls = my name + {int(NOISE * 100)}% noise"
    cap2 = f"{reach:,} cells reached in {maxd} layers · shortest path to the right edge: {plen} steps"
    who = "Computer Science @ BITS Pilani  ·  DPS RK Puram"
    what = "Machine Learning  ·  Competitive Programming  ·  Calculus  ·  Theoretical Physics"
    css = (face("Plex", "IBMPlexMono-Regular.ttf", cap1 + cap2 + what + "dist=0123456789")
           + face("PlexM", "IBMPlexMono-Medium.ttf", who, 500)
           + ".m{font-family:Plex,ui-monospace,Menlo,Consolas,monospace}"
           + ".mm{font-family:PlexM,ui-monospace,Menlo,Consolas,monospace;font-weight:500}")

    o = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}">',
         f'<defs><style>{css}</style>'
         f'<filter id="glow" x="-5%" y="-20%" width="110%" height="140%"><feGaussianBlur stdDeviation="2" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter></defs>',
         f'<rect width="{W}" height="{H}" rx="14" fill="{BG}"/>',
         # unvisited open cells: faint grid so the board is visible before the flood
         f'<path d="{runs([(x, y) for y in range(ROWS) for x in range(COLS) if not wall[y][x]])}" fill="#141413"/>',
         f'<path d="{runs([(x, y) for y in range(ROWS) for x in range(COLS) if wall[y][x] and not letters[y][x]])}" fill="#0f0f0e"/>']

    # the flood: one element per BFS layer, appearing white-hot then cooling to its distance colour
    layers = {}
    for cell, d in dist.items():
        layers.setdefault(d, []).append(cell)
    o.append("<g>")
    for d in range(maxd + 1):
        t = d / maxd * FLOOD
        col = cmap(d / maxd)
        o.append(f'<path d="{runs(layers[d])}" fill="{col}" opacity="0">'
                 f'<animate attributeName="opacity" values="0;0;1;1;0" keyTimes="0;{k(t)};{k(t + .02)};{end_vis};1" {anim}/>'
                 f'<animate attributeName="fill" values="{INK};{INK};{col};{col}" keyTimes="0;{k(t)};{k(t + .5)};1" {anim}/></path>')
    o.append("</g>")

    # the name: same colour as empty board (invisible) until the flood exposes it, then lit, then it lights up
    t_name = FLOOD + PATH_T
    o.append(f'<path d="{runs([(x, y) for y in range(ROWS) for x in range(COLS) if letters[y][x]])}" fill="#141413">'
             f'<animate attributeName="fill" values="#141413;#141413;{INK};{INK};#141413" keyTimes="0;{k(t_name)};{k(t_name + 1.2)};{end_vis};1" {anim}/></path>')

    # shortest path, traced after the flood
    pts = " ".join(f"{X0 + x * P + CELL / 2:.1f},{Y0 + y * P + CELL / 2:.1f}" for x, y in path)
    L = plen * P + 2
    o.append(f'<polyline points="{pts}" fill="none" stroke="{EMBER}" stroke-width="2.6" stroke-linejoin="round" stroke-linecap="round" '
             f'stroke-dasharray="{L} {L}" stroke-dashoffset="{L}" filter="url(#glow)">'
             f'<animate attributeName="stroke-dashoffset" values="{L};{L};0;0;{L}" keyTimes="0;{k(FLOOD + .1)};{k(FLOOD + .1 + PATH_T)};{end_vis};1" {anim}/>'
             f'<animate attributeName="opacity" values="1;1;0" keyTimes="0;{end_vis};1" {anim}/></polyline>')
    sx, sy = X0 + src[0] * P + CELL / 2, Y0 + src[1] * P + CELL / 2
    tx, ty = X0 + tgt[0] * P + CELL / 2, Y0 + tgt[1] * P + CELL / 2
    o.append(f'<circle cx="{sx}" cy="{sy}" r="4" fill="{EMBER}"/><circle cx="{tx}" cy="{ty}" r="4" fill="none" stroke="{EMBER}" stroke-width="1.5"/>')

    # live distance counter, one frame per layer
    o.append(f'<text class="m" x="{W - 62}" y="38" text-anchor="end" font-size="12" fill="{MUTED}">dist = </text><g class="m" font-size="12" fill="{EMBER}">')
    step = max(1, maxd // 120)
    shown = list(range(0, maxd + 1, step))
    if shown[-1] != maxd:
        shown.append(maxd)
    for i, d in enumerate(shown):
        a = d / maxd * FLOOD
        b = shown[i + 1] / maxd * FLOOD if i + 1 < len(shown) else C - FADE
        o.append(f'<text x="{W - 56}" y="38" opacity="0">{d}'
                 f'<animate attributeName="opacity" values="0;1;0" keyTimes="0;{k(a)};{k(b)}" calcMode="discrete" {anim}/></text>')
    o.append("</g>")

    o.append(f'<text class="m" x="30" y="38" font-size="12" fill="{INK}" fill-opacity=".85">{cap1}</text>'
             f'<text class="m" x="30" y="56" font-size="11.5" fill="{MUTED}">{cap2}</text>')
    o.append(f'<text class="mm" x="30" y="{H - 40}" font-size="14" fill="{INK}" xml:space="preserve">{who}</text>'
             f'<text class="m" x="30" y="{H - 20}" font-size="12" fill="{MUTED}" xml:space="preserve">{what}</text>')
    o.append("</svg>")
    open(OUT, "w", encoding="utf-8").write("\n".join(o))
    print(f"reach={reach} layers={maxd} path={plen} cycle={C:.1f}s size={sum(map(len, o)) / 1024:.0f}KB")


if __name__ == "__main__":
    main()
