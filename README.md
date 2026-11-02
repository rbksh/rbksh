<p align="center">
  <a href="https://rbksh.vercel.app/"><img src="assets/fourier.svg" width="100%" alt="Shesh Shiromani, written by a chain of 260 rotating circles (a Fourier series)"></a>
</p>

<p align="center">
  <a href="https://rbksh.vercel.app/"><img src="https://img.shields.io/badge/portfolio-rbksh.vercel.app-0a0a0b?style=flat-square&labelColor=0a0a0b&color=ece6d9" alt="portfolio"></a>
  <a href="https://www.linkedin.com/in/shesh08/"><img src="https://img.shields.io/badge/linkedin-shesh08-0a0a0b?style=flat-square&logo=linkedin&logoColor=ece6d9&labelColor=0a0a0b&color=ece6d9" alt="linkedin"></a>
  <a href="https://codeforces.com/profile/shesh08"><img src="https://img.shields.io/badge/codeforces-shesh08-0a0a0b?style=flat-square&logo=codeforces&logoColor=ff6a3d&labelColor=0a0a0b&color=ff6a3d" alt="codeforces"></a>
</p>

The animation above isn't a GIF or a font trick. My name was sampled into 4,096 points and run through a discrete Fourier transform. The 260 largest terms became 260 circles, each one spinning at its own integer frequency. Stack them tip to tail and the last one writes my name. The math is in [`tools/fourier.py`](tools/fourier.py).

I study Computer Science at **BITS Pilani**, and before that I was at **DPS RK Puram**. I'm into Machine Learning, Competitive Programming, Calculus and Theoretical Physics, and I like problems where a clean model turns into surprising behaviour.

### Things I've built

| | |
|---|---|
| **[HaptiBraille](https://github.com/rbksh/HaptiBraille)** | Read any text through your phone's vibrations as haptic Braille. No sound, no screen, no extra hardware. |
| **[Dynamic-Coin-Toss](https://github.com/rbksh/Dynamic-Coin-Toss)** | PINNs and a 5-DoF mechanical model of a coin toss, linked to chaos theory and the law of small numbers. |
| **[poker-bot-engine](https://github.com/rbksh/poker-bot-engine)** | No-Limit Hold'em bot in Python, Rust and C++, built for Sequoia's 60-minute bot contest. |
| **[benchrank](https://github.com/rbksh/benchrank)** | Low-latency trading infra and a distributed benchmarking platform for high-concurrency load (IICPC hackathon). |
| **[colonel-blotto-s-game](https://github.com/rbksh/colonel-blotto-s-game)** | Colonel Blotto simulator with evolution analytics, equilibrium search and tournaments. |
| **[Nomex](https://github.com/rbksh/Nomex)** | IUPAC name generator and checker for students working through organic chemistry. |

### Why I care about chaos

<p align="center">
  <a href="https://github.com/rbksh/Dynamic-Coin-Toss"><img src="assets/chaos.svg" width="100%" alt="Five double pendulums starting 0.0001 rad apart, diverging over time"></a>
</p>

These five pendulums start 0.0001 rad apart. They move as one for about six seconds, then the tiny difference blows up. The physics is integrated with RK4 in [`tools/chaos.py`](tools/chaos.py) and replayed frame by frame in pure SVG.

<p align="center">
  <a href="https://github.com/rbksh/HaptiBraille"><img src="assets/braille.svg" width="100%" alt="'thanks for reading' in Braille, decoding cell by cell"></a>
</p>

<sub>Every animation here is hand-generated SVG with SMIL. There's no JavaScript, no GIFs and no third-party widgets. The generators are in <a href="tools/">tools/</a>.</sub>
