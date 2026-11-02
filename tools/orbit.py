"""Generate assets/orbit.svg: my public GitHub repos as a planetary system.

  distance from the centre -> age rank (oldest repo = outermost orbit)
  planet size              -> repo size (log scale)
  colour                   -> main language
  orbital period           -> Kepler's third law, T ~ a^1.5
  halo                     -> pushed to in the last 14 days

Orbits are circles seen at a tilt, so planets pass behind and in front of
the name. Re-run daily by .github/workflows/orbit.yml.
"""
import datetime as dt
import hashlib
import json
import math
import os
import sys
import urllib.request

from webfont import face

USER = "rbksh"
OUT = sys.argv[1] if len(sys.argv) > 1 else "assets/orbit.svg"
W, H = 1000, 430
CX, CY = 500, 212
RX_IN, RX_OUT, TILT = 150, 470, 0.29
T_OUT = 170.0                     # seconds for the outermost orbit
LABELS = ["HaptiBraille", "poker-bot-engine", "Dynamic-Coin-Toss", "benchrank"]
LANG = {"Python": "#e3c57a", "C++": "#ff6a3d", "TypeScript": "#7ea6f2", "JavaScript": "#d9cf72",
        "HTML": "#d9876a", "CSS": "#b892c9", "Dart": "#5fc7c0", "Jupyter Notebook": "#f0a35e"}
OTHER = "#8a8476"
INK, MUTED, BG = "#ece6d9", "#8a8476", "#0a0a0b"


def repos():
    req = urllib.request.Request(f"https://api.github.com/users/{USER}/repos?per_page=100&type=owner",
                                 headers={"Accept": "application/vnd.github+json", "User-Agent": "orbit-svg"})
    if os.environ.get("GITHUB_TOKEN"):
        req.add_header("Authorization", f"Bearer {os.environ['GITHUB_TOKEN']}")
    data = json.load(urllib.request.urlopen(req))
    rs = [r for r in data if not r["fork"] and r["name"].lower() != USER.lower()]
    return sorted(rs, key=lambda r: r["created_at"], reverse=True)   # newest first = innermost


def f(v):
    return f"{v:.1f}".rstrip("0").rstrip(".")


def main():
    rs = repos()
    now = dt.datetime.now(dt.timezone.utc)
    n = len(rs)
    names = "".join(r["name"] for r in rs if r["name"] in LABELS)
    cap1 = f"each planet is one of my {n} public repos"
    cap2 = "distance = age   size = code   speed = Kepler's third law"
    who = "Computer Science @ BITS Pilani  ·  DPS RK Puram"
    what = "Machine Learning  ·  Competitive Programming  ·  Calculus  ·  Theoretical Physics"
    stamp = f"rebuilt daily by a GitHub Action · {now:%d %b %Y}"
    langs = [l for l in LANG if any(r["language"] == l for r in rs)]
    css = (face("Plex", "IBMPlexMono-Regular.ttf", cap1 + cap2 + what + stamp + names + "".join(langs) + "other")
           + face("PlexM", "IBMPlexMono-Medium.ttf", who, 500)
           + face("Serif", "InstrumentSerif-Italic.ttf", "Shesh Shiromani")
           + ".m{font-family:Plex,ui-monospace,Menlo,Consolas,monospace}"
           + ".mm{font-family:PlexM,ui-monospace,Menlo,Consolas,monospace;font-weight:500}"
           + ".s{font-family:Serif,Georgia,serif;font-style:italic}")

    o = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}">',
         f"""<defs><style>{css}</style>
<radialGradient id="bg" cx=".5" cy=".5" r=".75"><stop offset="0" stop-color="#121211"/><stop offset="1" stop-color="{BG}"/></radialGradient>
<radialGradient id="sun" cx=".5" cy=".5" r=".5"><stop offset="0" stop-color="#ff8a5c" stop-opacity=".22"/><stop offset=".55" stop-color="#ff6a3d" stop-opacity=".06"/><stop offset="1" stop-color="#ff6a3d" stop-opacity="0"/></radialGradient>
<radialGradient id="halo"><stop offset=".45" stop-color="{INK}" stop-opacity=".35"/><stop offset="1" stop-color="{INK}" stop-opacity="0"/></radialGradient>
<clipPath id="back"><rect width="{W}" height="{CY}"/></clipPath>
<clipPath id="front"><rect y="{CY}" width="{W}" height="{H - CY}"/></clipPath>
</defs>""",
         f'<rect width="{W}" height="{H}" rx="14" fill="url(#bg)"/>']

    # a few fixed background stars, seeded so the sky never changes between rebuilds
    seed = int(hashlib.md5(USER.encode()).hexdigest(), 16)
    for i in range(70):
        seed = (seed * 6364136223846793005 + 1442695040888963407) % 2 ** 64
        x, y, b = seed % W, (seed >> 20) % H, ((seed >> 40) % 100) / 100
        o.append(f'<circle cx="{x}" cy="{y}" r="{.4 + .6 * b:.2f}" fill="{INK}" opacity="{.08 + .22 * b:.2f}"/>')

    planets = []
    for i, r in enumerate(rs):
        rx = RX_IN + (RX_OUT - RX_IN) * (i / max(n - 1, 1))
        ry = rx * TILT
        period = T_OUT * (rx / RX_OUT) ** 1.5
        if r["name"] in LABELS:      # spread the labelled planets so their names don't pile up
            phase = 2 * math.pi * (LABELS.index(r["name"]) / len(LABELS) + .1)
        else:
            phase = int(hashlib.md5(r["name"].encode()).hexdigest()[:8], 16) / 2 ** 32 * 2 * math.pi
        size = 2.2 + 1.6 * math.log10(r["size"] + 1)
        col = LANG.get(r["language"], OTHER)
        active = (now - dt.datetime.fromisoformat(r["pushed_at"].replace("Z", "+00:00"))).days < 14
        o.append(f'<ellipse cx="{CX}" cy="{CY}" rx="{f(rx)}" ry="{f(ry)}" fill="none" stroke="{INK}" stroke-opacity=".07" stroke-width=".8"/>')

        M = 96
        th = [phase + 2 * math.pi * k / M for k in range(M + 1)]
        pts = ";".join(f"{f(CX + rx * math.cos(t))},{f(CY + ry * math.sin(t))}" for t in th)
        rad = ";".join(f(size * (1 + .2 * math.sin(t))) for t in th)
        opa = ";".join(f"{.55 + .45 * (1 + math.sin(t)) / 2:.2f}" for t in th)
        lab = ";".join(f"{max(0, min(.8, .4 + .8 * math.sin(t))):.2f}" for t in th)
        anim = f'dur="{period:.2f}s" repeatCount="indefinite"'
        body = (f'<animateMotion values="{pts}" {anim}/>'
                + (f'<circle r="{f(size * 2.6)}" fill="url(#halo)"><animate attributeName="opacity" values=".3;1;.3" dur="2.4s" repeatCount="indefinite"/></circle>' if active else "")
                + f'<circle fill="{col}"><animate attributeName="r" values="{rad}" {anim}/><animate attributeName="opacity" values="{opa}" {anim}/></circle>'
                + (f'<text class="m" x="{f(size + 6)}" y="3.5" font-size="10.5" fill="{INK}">{r["name"]}<animate attributeName="opacity" values="{lab}" {anim}/></text>' if r["name"] in LABELS else ""))
        planets.append(f'<g>{body}</g>')

    o.append(f'<g clip-path="url(#back)">{"".join(planets)}</g>')
    o.append(f'<ellipse cx="{CX}" cy="{CY}" rx="260" ry="120" fill="url(#sun)"/>')
    o.append(f'<text class="s" x="{CX}" y="{CY + 17}" text-anchor="middle" font-size="58" fill="{INK}">Shesh Shiromani</text>')
    o.append(f'<g clip-path="url(#front)">{"".join(planets)}</g>')

    o.append(f'<text class="m" x="32" y="38" font-size="12" fill="{INK}" fill-opacity=".8">{cap1}</text>'
             f'<text class="m" x="32" y="56" font-size="11" fill="{MUTED}" xml:space="preserve">{cap2}</text>')
    x = W - 32
    for l in reversed(langs + ["other"]):
        w = 6.6 * len(l.split()[0]) + 22
        x -= w
        o.append(f'<circle cx="{f(x + 4)}" cy="34" r="3.5" fill="{LANG.get(l, OTHER)}"/><text class="m" x="{f(x + 12)}" y="38" font-size="11" fill="{MUTED}">{l.split()[0]}</text>')
    o.append(f'<text class="mm" x="32" y="{H - 44}" font-size="14" fill="{INK}" xml:space="preserve">{who}</text>'
             f'<text class="m" x="32" y="{H - 24}" font-size="12" fill="{MUTED}" xml:space="preserve">{what}</text>'
             f'<text class="m" x="{W - 32}" y="{H - 24}" text-anchor="end" font-size="10.5" fill="{MUTED}" fill-opacity=".7">{stamp}</text>')
    o.append("</svg>")
    open(OUT, "w", encoding="utf-8").write("\n".join(o))
    print(f"{n} planets, {sum(map(len, o)) / 1024:.0f}KB")


if __name__ == "__main__":
    main()
