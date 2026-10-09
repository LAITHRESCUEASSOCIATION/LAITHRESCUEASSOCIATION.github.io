"""Generates the music bed and sound effects for the Laith video.

    python3 tools/audio.py public/audio

Everything is synthesised here, so there are no third-party rights.
120 BPM, one bar = 2 s = 60 frames; scene cuts in src/laith/theme.ts sit on bars.
"""
import os
import sys

import numpy as np
import soundfile as sf
from scipy.signal import butter, fftconvolve, sosfilt

SR = 44100
BPM = 120
BEAT = 60 / BPM
BAR = 4 * BEAT
LENGTH = 60.0
rng = np.random.default_rng(11)


def hz(m):
    return 440 * 2 ** ((m - 69) / 12)


def filt(x, kind, f, order=2):
    sos = butter(order, f, btype=kind, fs=SR, output="sos")
    return sosfilt(sos, x, axis=0)


def ir(seconds=2.2, decay=0.5, bright=6000):
    n = int(seconds * SR)
    t = np.arange(n) / SR
    out = np.stack([rng.standard_normal(n), rng.standard_normal(n)], 1)
    out *= np.exp(-t / decay)[:, None]
    out = filt(out, "low", bright)
    out[: int(0.012 * SR)] = 0  # pre-delay
    return out / np.abs(out).sum(0).max() * 6


def reverb(x, mix=0.25, **k):
    x2 = x if x.ndim == 2 else np.stack([x, x], 1)
    h = ir(**k)
    wet = np.stack([fftconvolve(x2[:, c], h[:, c])[: len(x2)] for c in (0, 1)], 1)
    return x2 * (1 - mix) + wet * mix


def stereo(x, pan=0.0):
    return np.stack([x * np.sqrt((1 - pan) / 2), x * np.sqrt((1 + pan) / 2)], 1)


class Track:
    def __init__(self, seconds):
        self.buf = np.zeros((int(seconds * SR), 2))

    def add(self, sig, at, gain=1.0, pan=0.0):
        s = sig if sig.ndim == 2 else stereo(sig, pan)
        i = int(at * SR)
        if i >= len(self.buf) or i + len(s) <= 0:
            return
        if i < 0:
            s, i = s[-i:], 0
        j = min(len(self.buf), i + len(s))
        self.buf[i:j] += s[: j - i] * gain


def env(n, a, d):
    t = np.arange(n) / SR
    e = np.exp(-t / d)
    na = int(a * SR)
    if na:
        e[:na] *= np.linspace(0, 1, na)
    return e


def saw(f, n, detune=0.0):
    t = np.arange(n) / SR
    ph = (f * (1 + detune) * t + rng.uniform()) % 1
    return 2 * ph - 1


# ---------- instruments ----------
def kick():
    n = int(0.45 * SR)
    t = np.arange(n) / SR
    f = 42 + 110 * np.exp(-t * 28)
    body = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 7)
    click = filt(rng.standard_normal(n), "high", 3000) * np.exp(-t * 300) * 0.3
    return np.tanh((body + click) * 1.6)


def clap():
    n = int(0.35 * SR)
    t = np.arange(n) / SR
    nz = filt(rng.standard_normal(n), "band", [900, 4000])
    e = np.zeros(n)
    for d in (0, 0.011, 0.022):
        e += (t >= d) * np.exp(-np.clip(t - d, 0, None) * 60)
    e += (t >= 0.03) * np.exp(-np.clip(t - 0.03, 0, None) * 14) * 0.6
    return nz * e


def hat(open_=False):
    n = int((0.25 if open_ else 0.06) * SR)
    t = np.arange(n) / SR
    return filt(rng.standard_normal(n), "high", 7500) * np.exp(-t * (14 if open_ else 70))


def tom(m):
    n = int(0.5 * SR)
    t = np.arange(n) / SR
    f = hz(m) * (1 + 0.5 * np.exp(-t * 20))
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 6)


def crash():
    n = int(3 * SR)
    t = np.arange(n) / SR
    return filt(rng.standard_normal(n), "high", 4000) * np.exp(-t * 1.4) * 0.6


def pluck(m, d=0.5):
    n = int(d * SR)
    t = np.arange(n) / SR
    f = hz(m)
    s = sum(np.sin(2 * np.pi * f * k * t) * np.exp(-t * (6 + 5 * k)) / k for k in range(1, 7))
    return s * np.minimum(1, t / 0.003)


def supersaw(m, n):
    s = sum(saw(hz(m), n, d) for d in (-0.011, -0.006, -0.002, 0.002, 0.006, 0.011))
    return filt(s / 6, "low", 3200)


def boom(dur=2.5):
    n = int(dur * SR)
    t = np.arange(n) / SR
    f = 30 + 45 * np.exp(-t * 3)
    sub = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 1.6)
    crack = filt(rng.standard_normal(n), "low", 1500) * np.exp(-t * 9) * 0.5
    return np.tanh((sub + crack) * 1.3)


def riser(dur=2.0):
    n = int(dur * SR)
    t = np.arange(n) / SR
    p = t / dur
    nz = rng.standard_normal(n)
    lo = filt(nz, "band", [300, 1200]) * (1 - p)
    hi = filt(nz, "band", [2000, 9000]) * p
    tone = saw(1, n) * 0
    f = 110 * 2 ** (p * 2.5)
    tone = np.sin(2 * np.pi * np.cumsum(f) / SR) * 0.25
    return (lo + hi + tone) * p**2


def reverse_cymbal(dur=1.5):
    return crash()[: int(dur * SR)][::-1] * 1.3


# ---------- sfx ----------
def whoosh(dur=0.7, lo=300, hi=6000):
    n = int(dur * SR)
    t = np.arange(n) / SR
    p = t / dur
    nz = rng.standard_normal(n)
    out = np.zeros(n)
    bands = np.geomspace(lo, hi, 9)
    for a, b in zip(bands[:-1], bands[1:]):
        c = (np.log(a) - np.log(lo)) / (np.log(hi) - np.log(lo))
        w = np.exp(-((p - c) ** 2) / 0.02)
        out += filt(nz, "band", [a, b]) * w
    amp = np.sin(np.pi * p) ** 1.5
    s = out * amp
    pan = np.linspace(-0.7, 0.7, n)
    return np.stack([s * np.sqrt((1 - pan) / 2), s * np.sqrt((1 + pan) / 2)], 1)


def impact():
    s = boom(2.0) + np.concatenate([filt(rng.standard_normal(int(0.4 * SR)), "band", [200, 3000]) * np.exp(-np.arange(int(0.4 * SR)) / SR * 14) * 0.4, np.zeros(int(1.6 * SR))])
    return reverb(s, 0.3, seconds=2.5, decay=0.7)


def glitch():
    n = int(0.35 * SR)
    out = np.zeros(n)
    i = 0
    while i < n:
        seg = int(rng.uniform(0.01, 0.04) * SR)
        f = rng.choice([220, 440, 880, 1760, 3520])
        t = np.arange(seg) / SR
        s = np.sign(np.sin(2 * np.pi * f * t)) * 0.3 if rng.uniform() < 0.5 else filt(rng.standard_normal(seg), "high", 2000) * 0.4
        out[i : i + seg] = s[: n - i] * (rng.uniform() < 0.8)
        i += seg
    return out * np.linspace(1, 0.4, n)


def tick():
    n = int(0.04 * SR)
    t = np.arange(n) / SR
    return (np.sin(2 * np.pi * 2400 * t) * 0.6 + filt(rng.standard_normal(n), "high", 5000) * 0.3) * np.exp(-t * 160)


def shimmer():
    n = int(2.5 * SR)
    t = np.arange(n) / SR
    s = sum(np.sin(2 * np.pi * hz(m) * t + i) * np.exp(-t * (1.2 + i * 0.3)) * (t > i * 0.06) for i, m in enumerate([86, 90, 93, 98, 102]))
    return reverb(s * 0.2, 0.5, seconds=3, decay=1.0)


def pop():
    n = int(0.12 * SR)
    t = np.arange(n) / SR
    f = 900 * np.exp(-t * 30) + 300
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 40)


# ---------- music ----------
def music():
    m = Track(LENGTH)
    drums = Track(LENGTH)
    bass = Track(LENGTH)
    pads = Track(LENGTH)
    arp = Track(LENGTH)
    fx = Track(LENGTH)
    K, C, H, HO = kick(), clap(), hat(), hat(True)

    # D hijaz: D Eb F# G A Bb C
    prog = [[50, 57, 62, 66], [51, 58, 62, 67], [48, 55, 60, 63], [50, 57, 62, 66]]
    roots = [38, 39, 36, 38]
    hijaz = [62, 63, 66, 67, 69, 70, 72, 74]
    arp_pat = [0, 2, 4, 7, 4, 2, 5, 3]

    bars = int(LENGTH / BAR)
    for b in range(bars):
        t0 = b * BAR
        ch = prog[(b // 2) % 4]
        root = roots[(b // 2) % 4]
        full = 8 <= b < 24 or 25 <= b < 27
        groove = 2 <= b < 24 or 25 <= b < 27
        breakdown = b == 24
        outro = b >= 27

        # pads: whole song, swell into each pair of bars
        if b % 2 == 0 and not outro:
            n = int(2 * BAR * SR)
            s = sum(supersaw(x, n) for x in ch) / len(ch)
            s *= np.minimum(1, np.arange(n) / SR / 0.4) * np.minimum(1, (n - np.arange(n)) / SR / 0.3)
            pads.add(stereo(s, -0.3) * 0.5 + stereo(np.roll(s, 400), 0.3) * 0.5, t0, 0.75 if full else 0.55)

        if groove:
            for beat in range(4):
                tb = t0 + beat * BEAT
                drums.add(K, tb, 0.6 if full or beat % 2 == 0 else 0)
                if beat in (1, 3):
                    drums.add(C, tb, 0.5 if full else 0.35, 0.1)
                for k in range(4 if full else 2):
                    drums.add(H, tb + k * BEAT / (4 if full else 2), 0.10 if k % 2 else 0.16, 0.3)
                if full and beat == 3:
                    drums.add(HO, tb + BEAT / 2, 0.12, -0.3)
            # bass 8ths
            for k in range(8):
                tb = t0 + k * BEAT / 2
                n = int(BEAT / 2 * SR * 0.9)
                s = saw(hz(root), n) + 0.6 * np.sin(2 * np.pi * hz(root) * np.arange(n) / SR)
                s = filt(s, "low", 400 if full else 260) * env(n, 0.005, 0.18)
                bass.add(s, tb, 0.22)
            # arp 16ths
            if b >= 4:
                for k in range(16):
                    deg = arp_pat[(k + b) % 8]
                    arp.add(pluck(hijaz[deg] + (12 if full and k % 4 == 3 else 0), 0.35), t0 + k * BEAT / 4, 0.28, (-0.4 if k % 2 else 0.4))
            # tom fill on section ends
            if b in (7, 15, 23):
                for k, mm in enumerate([50, 50, 47, 47, 43, 43, 40, 40]):
                    drums.add(tom(mm), t0 + 3 * BEAT + k * BEAT / 8, 0.3)

        if breakdown:
            fx.add(riser(BAR), t0, 0.5)
            fx.add(reverse_cymbal(1.5), t0 + BAR - 1.5, 0.5)
            for k in range(16):  # snare roll building
                drums.add(C, t0 + k * BEAT / 4 * (1 if k < 8 else 1), 0.05 + 0.02 * k, 0)

    # intro: drone + riser into the groove
    n = int(4 * SR)
    drone = supersaw(38, n) * np.minimum(1, np.arange(n) / SR / 1.5)
    pads.add(drone, 0, 0.25)
    fx.add(riser(2.0), 2.0, 0.35)
    # crashes + booms on section starts
    for t in (4.0, 16.0, 50.0):
        fx.add(crash(), t, 0.35)
    for t in (0.0, 16.0, 50.0, 54.0):
        fx.add(boom(), t, 0.35)
    # outro: sustained chord ringing out
    n = int(6 * SR)
    s = sum(supersaw(x, n) for x in [50, 57, 62, 66, 69]) / 5
    s *= np.exp(-np.arange(n) / SR / 2.2)
    pads.add(stereo(s), 54.0, 0.3)
    arp.add(sum(pluck(x, 3.0) for x in [62, 66, 69, 74]), 54.0, 0.12)

    # sidechain: duck pads + bass on each kick in groove sections
    t = np.arange(len(m.buf)) / SR
    phase = (t % BEAT) / BEAT
    duck = 1 - 0.55 * np.exp(-phase * 7)
    in_groove = ((t >= 4) & (t < 48)) | ((t >= 50) & (t < 54))
    duck = np.where(in_groove, duck, 1)[:, None]

    m.buf += drums.buf
    m.buf += bass.buf * duck
    m.buf += reverb(pads.buf * duck, 0.35, seconds=3, decay=1.2)
    m.buf += reverb(arp.buf, 0.4, seconds=2, decay=0.6)
    m.buf += reverb(fx.buf, 0.3)
    mix = filt(filt(m.buf, "high", 28), "low", 16000)
    out = np.tanh(mix * 1.2) / np.tanh(1.2)
    fade = np.minimum(1, (LENGTH - t) / 2.5)[:, None]
    out *= fade
    return out / np.abs(out).max() * 0.9


def main(outdir):
    os.makedirs(outdir, exist_ok=True)
    sf.write(f"{outdir}/music.wav", music().astype(np.float32), SR)
    sfx = {
        "whoosh": whoosh(),
        "swish": whoosh(0.35, 800, 9000),
        "impact": impact(),
        "glitch": glitch(),
        "tick": tick(),
        "shimmer": shimmer(),
        "pop": pop(),
        "riser": riser(1.0),
    }
    for name, s in sfx.items():
        s = s if s.ndim == 2 else stereo(s)
        sf.write(f"{outdir}/sfx-{name}.wav", (s / np.abs(s).max() * 0.9).astype(np.float32), SR)


if __name__ == "__main__":
    main(sys.argv[1])
