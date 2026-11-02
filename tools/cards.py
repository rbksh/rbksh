"""Static, typeset cards for the README (GitHub markdown can't choose fonts,
so text that should look good is set here with embedded IBM Plex)."""
import os

from PIL import ImageFont
from webfont import face

HERE = os.path.dirname(os.path.abspath(__file__))
FONTS = os.path.join(HERE, "..", "fonts")
OUT = os.path.join(HERE, "..", "assets")
W = 1000
INK, MUTED, DIM, BG, LINE, EMBER = "#ece6d9", "#9a9385", "#5d584f", "#0a0a0b", "#1f1e1b", "#ff6a3d"

PROJECTS = [
    ("A", "HaptiBraille", "Read any text through your phone's vibration as haptic Braille. No sound, no screen, no extra hardware.", ["dart", "kotlin", "haptics", "accessibility"]),
    ("B", "benchrank", "Low-latency trading infrastructure and a distributed benchmarking platform under heavy concurrent load. Built for IICPC.", ["typescript", "low-latency", "distributed"]),
    ("C", "poker-bot-engine", "No-Limit Hold'em bot written for Sequoia's 60-minute bot contest.", ["python", "rust", "game theory"]),
    ("D", "colonel-blotto-s-game", "Colonel Blotto simulator with evolutionary analytics, equilibrium search and tournaments.", ["javascript", "game theory", "simulation"]),
    ("E", "Dynamic-Coin-Toss", "Physics-informed neural nets and a 5-DoF model of a coin toss, and why it behaves like chance.", ["python", "PINNs", "chaos"]),
    ("F", "Nomex", "IUPAC name generator and checker for students learning organic chemistry.", ["python", "parsing", "chemistry"]),
]
ABOUT = [
    "CS at BITS Pilani, previously DPS RK Puram.",
    "Machine learning, competitive programming, calculus, theoretical physics,",
    "and lately, market microstructure.",
]
ABOUT_NOTE = "The banner above is a real BFS run. My name is part of the wall."
LINKS = [("portfolio", "rbksh.vercel.app"), ("linkedin", "shesh08"), ("codeforces", "shesh08")]
BRAILLE = "thanks for reading"
DOTS = dict(zip("abcdefghijklmnopqrstuvwxyz", ["1", "12", "14", "145", "15", "124", "1245", "125", "24", "245", "13", "123", "134", "1345", "135", "1234", "12345", "1235", "234", "2345", "136", "1236", "2456", "1346", "13456", "1356"]))

ALLTEXT = "".join(p[1] + p[2] + "".join(p[3]) + p[0] for p in PROJECTS) + "".join(ABOUT) + ABOUT_NOTE + "".join(a + b for a, b in LINKS)
CSS = (face("Sans", "IBMPlexSans-Regular.ttf", ALLTEXT + "Problemset6 problems#tags·→ that's braille. HaptiBraille can buzz it on your phone")
       + face("SansSB", "IBMPlexSans-SemiBold.ttf", ALLTEXT + "Problemset", 600)
       + face("Mono", "IBMPlexMono-Regular.ttf", ALLTEXT + "Problemset6 problems#tags·→ that's braille. HaptiBraille can buzz it on your phone/0123456789")
       + ".s{font-family:Sans,system-ui,sans-serif}.sb{font-family:SansSB,system-ui,sans-serif;font-weight:600}"
       + ".m{font-family:Mono,ui-monospace,Menlo,Consolas,monospace}")


def measure(text, file, size):
    return ImageFont.truetype(os.path.join(FONTS, file), size).getlength(text)


def wrap(text, file, size, width):
    lines, cur = [], ""
    for w in text.split():
        t = (cur + " " + w).strip()
        if measure(t, file, size) > width and cur:
            lines.append(cur); cur = w
        else:
            cur = t
    return lines + [cur]


def svg(name, w, h, body, bg=True):
    head = f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}"><defs><style>{CSS}</style></defs>'
    rect = f'<rect x=".5" y=".5" width="{w - 1}" height="{h - 1}" rx="10" fill="{BG}" stroke="{LINE}"/>' if bg else ""
    open(os.path.join(OUT, name), "w", encoding="utf-8").write(head + rect + body + "</svg>")


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace("'", "&#39;")


def main():
    # links: one small card each so every link is its own click target
    for label, sub in LINKS:
        w = 44 + max(measure(label, "IBMPlexMono-Regular.ttf", 13), measure(sub, "IBMPlexSans-Regular.ttf", 12))
        w = int(w) + 8
        svg(f"link-{label}.svg", w, 52,
            f'<circle cx="20" cy="19" r="3" fill="{EMBER}"/>'
            f'<text class="m" x="32" y="23" font-size="13" fill="{INK}">{label}</text>'
            f'<text class="s" x="32" y="40" font-size="12" fill="{MUTED}">{sub}</text>')

    # problemset, styled after a judge's problem list; one row per image so each row links to its repo
    svg("problemset.svg", W, 64,
        f'<text class="sb" x="36" y="40" font-size="20" fill="{INK}">Problemset</text>'
        f'<text class="m" x="{W - 36}" y="39" text-anchor="end" font-size="12" fill="{DIM}">{len(PROJECTS)} problems</text>')
    for letter, name, desc, tags in PROJECTS:
        lines = wrap(desc, "IBMPlexSans-Regular.ttf", 14, 560)
        h = 52 + 20 * len(lines) + 8
        body = (f'<text class="m" x="40" y="38" font-size="18" fill="{EMBER}">{letter}</text>'
                f'<line x1="78" y1="18" x2="78" y2="{h - 18}" stroke="{LINE}"/>'
                f'<text class="sb" x="100" y="38" font-size="17" fill="{INK}">{esc(name)}</text>')
        for i, ln in enumerate(lines):
            body += f'<text class="s" x="100" y="{62 + 20 * i}" font-size="14" fill="{MUTED}">{esc(ln)}</text>'
        x = W - 36
        for t in reversed(tags):
            tw = measure(t, "IBMPlexMono-Regular.ttf", 11.5) + 18
            x -= tw
            body += (f'<rect x="{x:.1f}" y="22" width="{tw:.1f}" height="22" rx="4" fill="none" stroke="#2c2a26"/>'
                     f'<text class="m" x="{x + tw / 2:.1f}" y="37" text-anchor="middle" font-size="11.5" fill="{MUTED}">{esc(t)}</text>')
            x -= 6
        svg(f"p-{letter.lower()}.svg", W, h, body)

    # footer: braille drawn as real dots, with the reading underneath
    pitch, gap, cells = 26, 9, len(BRAILLE)
    total = cells * pitch
    x0, body = (W - total) / 2, ""
    pos = {"1": (0, 0), "2": (0, 1), "3": (0, 2), "4": (1, 0), "5": (1, 1), "6": (1, 2)}
    for i, ch in enumerate(BRAILLE):
        for d, (c, r) in pos.items():
            on = d in DOTS.get(ch, "")
            body += f'<circle cx="{x0 + i * pitch + c * gap:.1f}" cy="{30 + r * gap}" r="{3 if on else 1.2}" fill="{INK if on else "#2a2925"}"/>'
    body += f'<text class="m" x="{W / 2}" y="{98}" text-anchor="middle" font-size="12" fill="{DIM}">that\'s braille. HaptiBraille can buzz it on your phone</text>'
    svg("braille.svg", W, 124, body)
    print("ok")


if __name__ == "__main__":
    main()
