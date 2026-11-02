"""Generate assets/braille.svg: a sentence in Braille that 'vibrates' cell by
cell (like HaptiBraille's haptic pulses) and decodes into text as it goes."""
import sys

OUT = sys.argv[1] if len(sys.argv) > 1 else "assets/braille.svg"
TEXT = sys.argv[2] if len(sys.argv) > 2 else "thanks for reading"
W, H = 1000, 150
STEP = 0.45            # seconds per cell
HOLD = 4.0             # seconds fully decoded before reset

# Grade 1 Braille, dots numbered 1-2-3 down the left column, 4-5-6 down the right
DOTS = dict(zip("abcdefghijklmnopqrstuvwxyz", [
    "1", "12", "14", "145", "15", "124", "1245", "125", "24", "245", "13", "123", "134", "1345", "135",
    "1234", "12345", "1235", "234", "2345", "136", "1236", "2456", "1346", "13456", "1356"]))
POS = {"1": (0, 0), "2": (0, 1), "3": (0, 2), "4": (1, 0), "5": (1, 1), "6": (1, 2)}


def main():
    n = len(TEXT)
    cycle = n * STEP + HOLD
    cw, gap = 38, 14              # cell pitch, dot pitch
    x0 = (W - (n - 1) * cw - gap) / 2
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" font-family="ui-monospace,SFMono-Regular,Menlo,Consolas,monospace">',
         '<defs><filter id="g" x="-200%" y="-200%" width="500%" height="500%"><feGaussianBlur stdDeviation="3" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter></defs>',
         f'<rect width="{W}" height="{H}" rx="18" fill="#070a12"/>',
         f'<text x="28" y="30" fill="#475569" font-size="12">// this line is Braille. each cell buzzes the way HaptiBraille vibrates your phone</text>']
    for i, ch in enumerate(TEXT):
        cx = x0 + i * cw
        t = i * STEP / cycle                        # moment this cell is "felt"
        t2 = min(t + 0.06, 0.97)
        raised = DOTS.get(ch, "")
        for d, (c, r) in POS.items():
            x, y = cx + c * gap, 52 + r * gap
            if d in raised:
                kt = f"0;{t:.4f};{t + .004:.4f};{t + .02:.4f};{t2:.4f};.97;1"
                o.append(f'<circle cx="{x:.1f}" cy="{y}" r="4.6" fill="#5eead4" filter="url(#g)">'
                         f'<animate attributeName="opacity" values=".18;.18;1;1;.75;.75;.18" keyTimes="{kt}" dur="{cycle:.2f}s" repeatCount="indefinite"/>'
                         f'<animate attributeName="r" values="4;4;7;4.6;4.6;4.6;4" keyTimes="{kt}" dur="{cycle:.2f}s" repeatCount="indefinite"/>'
                         f'<animateTransform attributeName="transform" type="translate" values="0 0;0 0;1.5 0;-1.5 0;0 0;0 0;0 0" keyTimes="{kt}" dur="{cycle:.2f}s" repeatCount="indefinite"/></circle>')
            else:
                o.append(f'<circle cx="{x:.1f}" cy="{y}" r="1.6" fill="#1e293b"/>')
        if ch != " ":
            kt = f"0;{t + .01:.4f};{t + .04:.4f};.96;1"
            o.append(f'<text x="{cx + gap / 2:.1f}" y="{H - 28}" text-anchor="middle" fill="#cbd5e1" font-size="17" opacity="0">{ch}'
                     f'<animate attributeName="opacity" values="0;0;1;1;0" keyTimes="{kt}" dur="{cycle:.2f}s" repeatCount="indefinite"/></text>')
    o.append("</svg>")
    open(OUT, "w", encoding="utf-8").write("".join(o))
    print(f"cells={n} cycle={cycle:.1f}s")


if __name__ == "__main__":
    main()
