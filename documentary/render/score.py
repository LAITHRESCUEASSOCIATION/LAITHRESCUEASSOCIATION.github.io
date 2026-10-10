#!/usr/bin/env python3
"""Original score + field foley for the Laith documentary (fully synthesised, no samples).

Writes ../music/score.wav and ../music/foley.wav (3:00, 48 kHz stereo), following the
cue sheet in ../PROMPTS.md: quiet piano at dawn, a pulse during preparation, strings on
the road, a restrained build to the arrival, a pull-back for the human effort, then a
warm resolve under the logo.
"""
import os

import numpy as np
from scipy.io import wavfile
from scipy.signal import butter, fftconvolve, sosfilt

DOC = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SR = 48000
DUR = 180.0
N = int(SR * DUR)
rng = np.random.default_rng(7)

BPM = 70
BEAT = 60 / BPM
BAR = 4 * BEAT


def hz(midi):
    return 440.0 * 2 ** ((midi - 69) / 12)


def env_curve(points):
    """Piecewise-linear automation [(time, value), ...] over the whole film."""
    t = np.arange(N) / SR
    xs, ys = zip(*points)
    return np.interp(t, xs, ys)


def lp(x, f, order=2):
    return sosfilt(butter(order, f, 'low', fs=SR, output='sos'), x)


def hp(x, f, order=2):
    return sosfilt(butter(order, f, 'high', fs=SR, output='sos'), x)


def bp(x, f0, f1, order=2):
    return sosfilt(butter(order, [f0, f1], 'band', fs=SR, output='sos'), x)


def add(buf, start, sig, pan=0.0):
    i = int(start * SR)
    if i >= N or i + len(sig) <= 0:
        return
    j = min(N, i + len(sig))
    s = sig[:j - i]
    buf[0, i:j] += s * np.sqrt(.5 * (1 - pan))
    buf[1, i:j] += s * np.sqrt(.5 * (1 + pan))


def reverb(x, secs=3.4, wet=.35, seed=1):
    r = np.random.default_rng(seed)
    n = int(secs * SR)
    t = np.arange(n) / SR
    out = np.zeros_like(x)
    for c in range(2):
        ir = r.normal(0, 1, n) * np.exp(-t * 6.9 / secs)
        ir = lp(ir, 5200)
        ir[:int(.012 * SR)] = 0
        ir /= np.sqrt(np.sum(ir ** 2))
        out[c] = fftconvolve(x[c], ir)[:N]
    return x * (1 - wet) + out * wet * 2.2


# ------------------------------------------------------------------ instruments

def piano(f, dur, vel=.5):
    n = int((dur + 2.5) * SR)
    t = np.arange(n) / SR
    s = np.zeros(n)
    for k in range(1, 10):
        fk = f * k * np.sqrt(1 + .00035 * k * k)
        if fk > 16000:
            break
        s += np.sin(2 * np.pi * fk * t + rng.uniform(0, 6.28)) * k ** -1.4 * np.exp(-t * (.45 + .32 * k) * (f / 260) ** .3)
    s *= np.minimum(1, t / .004)
    rel = np.clip((dur + .25 - t) / .6, 0, 1) ** 2
    s *= .25 + .75 * rel
    s *= np.clip((dur + 2.5 - t) / .3, 0, 1)
    return s * vel * .3


def strings(f, dur, att=1.5, rel=2.0, bright=2200):
    n = int((dur + rel) * SR)
    t = np.arange(n) / SR
    s = np.zeros(n)
    for det in (-.006, 0, .0055):
        vib = 1 + .0018 * np.sin(2 * np.pi * (4.6 + det * 100) * t + rng.uniform(0, 6))
        ph = 2 * np.pi * np.cumsum(f * (1 + det) * vib) / SR
        for k in range(1, 14):
            if f * k > 9000:
                break
            s += np.sin(k * ph) / k
    s = lp(s, bright)
    e = np.minimum(1, t / att) * np.clip((dur + rel - t) / rel, 0, 1)
    return s * e * .06


def drum(f=70, decay=.5, vel=.5):
    n = int(1.6 * SR)
    t = np.arange(n) / SR
    pitch = f * (1 + .6 * np.exp(-t * 30))
    s = np.sin(2 * np.pi * np.cumsum(pitch) / SR) * np.exp(-t / decay)
    s += lp(rng.normal(0, 1, n), 900) * np.exp(-t * 40) * .3
    return s * vel


# ------------------------------------------------------------------ score

def score():
    mus = {k: np.zeros((2, N)) for k in ('piano', 'pad', 'drone', 'high', 'pulse', 'perc')}
    # D minor: i - VI - III - VII, two bars each; the last section resolves to D major
    prog = [[50, 57, 62, 65], [46, 53, 58, 62], [53, 57, 60, 65], [48, 55, 60, 64]]
    resolve = [50, 57, 62, 66, 69]
    chord_len = 2 * BAR

    def chord_at(t):
        return prog[int(t // chord_len) % 4]

    # drone (low D + A) for the whole film
    for start in np.arange(0, 175, 14):
        for m in (38, 45):
            add(mus['drone'], start, strings(hz(m), 14, att=4, rel=4, bright=700), pan=-.2 if m == 38 else .2)

    # piano: sparse at dawn, gentle arpeggios on the road, sparse again for the human effort
    t = 1.5
    while t < 165:
        ch = chord_at(t)
        if t < 55:
            step, notes, vel = 2 * BEAT, [ch[2] + 12, ch[3] + 12, ch[1] + 12], .45
        elif t < 85:
            step, notes, vel = BEAT, [ch[1] + 12, ch[2] + 12, ch[3] + 12, ch[2] + 24], .42
        elif t < 140:
            step, notes, vel = BEAT / 2, [ch[0] + 12, ch[1] + 12, ch[2] + 12, ch[3] + 12, ch[2] + 24, ch[3] + 12], .36
        else:
            step, notes, vel = 2 * BEAT, [ch[3] + 12, ch[2] + 12], .42
        idx = int(round(t / step))
        n = notes[idx % len(notes)]
        if not (t < 55 and rng.random() < .25):
            add(mus['piano'], t, piano(hz(n), step * 1.6, vel * rng.uniform(.8, 1.05)), pan=rng.uniform(-.3, .3))
        if (t < 25 or 140 < t < 165) and idx % 4 == 0:
            add(mus['piano'], t, piano(hz(ch[0] - 12 + 12), 3, .3), pan=-.2)
        t += step
    # resolve: D major, then the final low note under the logo
    for i, m in enumerate(resolve):
        add(mus['piano'], 165.5 + i * .35, piano(hz(m + 12), 6, .4), pan=-.3 + i * .15)
    add(mus['piano'], 175.2, piano(hz(38), 5, .5))
    add(mus['piano'], 175.25, piano(hz(69 + 12), 4, .18), pan=.3)

    # pad chords
    for c0 in np.arange(0, 165, chord_len):
        ch = chord_at(c0 + .1)
        for j, m in enumerate(ch):
            add(mus['pad'], c0, strings(hz(m), chord_len, att=2.2, rel=2.5), pan=(-.5, -.15, .15, .5)[j])
    for j, m in enumerate(resolve):
        add(mus['pad'], 164.6, strings(hz(m), 11, att=2.5, rel=4), pan=-.5 + j * .25)

    # high strings line on the road / arrival
    line = [74, 72, 69, 70, 74, 76, 77, 76, 74, 72, 74, 69]
    for i, m in enumerate(line):
        add(mus['high'], 85 + i * BAR * .72, strings(hz(m), BAR * 1.1, att=1.2, rel=1.8, bright=3600), pan=.3)
    for i, m in enumerate([77, 76, 74, 72, 74, 76, 77, 81]):
        add(mus['high'], 115 + i * BAR * .9, strings(hz(m), BAR, att=.9, rel=1.6, bright=4200), pan=.25)

    # heartbeat pulse
    t = 25.0
    while t < 141:
        add(mus['pulse'], t, drum(48, .35, .55))
        add(mus['pulse'], t + .32, drum(46, .3, .35))
        t += BEAT * 2
    # soft low toms at the arrival
    t = 115.0
    while t < 140:
        add(mus['perc'], t, drum(80, .7, .5), pan=-.2)
        add(mus['perc'], t + BEAT * 1.5, drum(95, .5, .3), pan=.2)
        t += BAR

    auto = {
        'drone': [(0, 0), (4, .9), (55, .8), (140, 1.0), (150, .7), (172, .6), (180, 0)],
        'piano': [(0, 1), (85, .8), (140, .65), (145, 1), (180, 1)],
        'pad': [(0, 0), (55, 0), (62, .55), (85, .75), (115, 1.0), (140, 1.0), (146, .45), (165, .5), (170, .9),
                (176, .4), (180, 0)],
        'high': [(0, 0), (85, .4), (115, .9), (140, .9), (146, 0), (180, 0)],
        'pulse': [(0, 0), (25, 0), (30, .5), (85, .6), (115, .9), (140, .9), (142, 0), (180, 0)],
        'perc': [(0, 1), (180, 1)],
    }
    gains = {'drone': .8, 'piano': 1.0, 'pad': .9, 'high': .6, 'pulse': .5, 'perc': .45}
    mix = np.zeros((2, N))
    for k, buf in mus.items():
        mix += buf * env_curve(auto[k]) * gains[k]
    mix = hp(mix, 30)
    mix = reverb(mix, 3.6, .38)
    mix *= env_curve([(0, 0), (1.5, 1), (178, 1), (180, 0)])
    return mix


# ------------------------------------------------------------------ foley

def noise(sec):
    return rng.normal(0, 1, int(sec * SR))


def shape(sig, a, r):
    n = len(sig)
    t = np.arange(n) / SR
    return sig * np.minimum(1, t / max(a, 1e-3)) * np.clip((n / SR - t) / max(r, 1e-3), 0, 1)


def breath(kind='out', sec=1.2, vol=.12, effort=0.0):
    x = noise(sec)
    if kind == 'in':
        x = bp(x, 900, 3800)
        e = np.sin(np.linspace(0, np.pi, len(x))) ** 1.5
    else:
        x = bp(x, 350, 2200 + 800 * effort)
        t = np.linspace(0, 1, len(x))
        e = np.minimum(1, t / .12) * (1 - t) ** 1.6
    return x * e * vol


def sigh(sec=.7, vol=.05, f0=118):
    """A very soft, breathy effort sound ('haa'): glottal pulses through vowel formants."""
    n = int(sec * SR)
    t = np.arange(n) / SR
    f = f0 * (1 - .12 * t / sec)
    ph = np.cumsum(f) / SR
    src = ((ph % 1) < .08).astype(float) * .6 + rng.normal(0, 1, n) * .5
    v = bp(src, 600, 820) + .6 * bp(src, 1050, 1350) + .25 * bp(src, 2400, 2800)
    e = np.minimum(1, t / .08) * (1 - t / sec) ** 1.5
    return v * e * vol


def click(f=3200, sec=.05, vol=.3):
    t = np.arange(int(sec * SR)) / SR
    return (np.sin(2 * np.pi * f * t) * .6 + hp(noise(sec), 2000) * .4) * np.exp(-t * 90) * vol


def thud(f=70, sec=.5, vol=.4):
    t = np.arange(int(sec * SR)) / SR
    return (np.sin(2 * np.pi * f * t) + lp(noise(sec), 400) * .5) * np.exp(-t * 12) * vol


def steps(buf, t0, t1, rate=1.9, vol=.07, pan=0.0):
    t = t0
    while t < t1:
        s = bp(noise(.18), 300, 2500) * np.exp(-np.arange(int(.18 * SR)) / SR * 22)
        add(buf, t + rng.uniform(-.04, .04), s * vol * rng.uniform(.7, 1.1), pan)
        t += 1 / rate


def foley():
    fx = np.zeros((2, N))
    # wind / room beds
    w = bp(rng.normal(0, 1, N), 120, 900)
    wmod = lp(rng.normal(0, 1, N), .3)
    wmod = .6 + .4 * wmod / (np.abs(wmod).max() + 1e-9)
    wind = w * wmod * env_curve([(0, 0), (2, .05), (25, .045), (26, .012), (55, .012), (56, .03), (67, .03),
                                 (73, .0), (115, 0), (116, .03), (165, .025), (175, .02), (180, 0)])
    fx[0] += wind
    fx[1] += np.roll(wind, 2400)
    # 0:25 preparation
    add(fx, 25.6, shape(bp(noise(1.3), 500, 5000), .2, .6) * .05)
    for i in range(46):
        add(fx, 30.4 + 1.9 * (i / 46) ** .8, click(4200, .02, .05))
    add(fx, 36.4, shape(bp(noise(.32), 1500, 7000), .02, .1) * .12)
    add(fx, 40.9, breath('in', .7, .08))
    add(fx, 41.4, thud(110, .3, .15))
    add(fx, 41.7, breath('out', 1.0, .09, .5))
    add(fx, 47.8, click(2200, .06, .2), .3)
    add(fx, 47.9, bp(noise(.35), 1500, 4000) * .02, .3)
    add(fx, 50.2, shape(bp(noise(.3), 1200, 6000), .02, .1) * .07)
    add(fx, 53.7, breath('out', 1.6, .08))
    # 0:55 leaving
    steps(fx, 55.2, 58.3, 2.2, .05)
    add(fx, 58.6, thud(85, .5, .35))
    add(fx, 58.65, click(1800, .05, .1))
    add(fx, 63.3, click(3600, .05, .3), -.2)
    add(fx, 63.33, click(2400, .04, .2), -.2)
    tt = np.arange(N) / SR
    eng_f = 38 + 10 * np.clip((tt - 67.6) / 2, 0, 1) + 3 * np.sin(tt * 2)
    eng = np.sin(2 * np.pi * np.cumsum(eng_f) / SR) + .5 * np.sin(4 * np.pi * np.cumsum(eng_f) / SR)
    eng = lp(eng + .4 * rng.normal(0, 1, N), 240)
    fx += eng * env_curve([(0, 0), (67.5, 0), (67.8, .09), (70, .05), (73, .03), (85, .035), (115, .03),
                           (117, 0), (180, 0)])
    road = lp(rng.normal(0, 1, N), 300)
    fx += road * env_curve([(0, 0), (72, 0), (74, .05), (113, .05), (116, 0), (180, 0)])
    add(fx, 101.5, breath('in', .8, .05))
    add(fx, 102.4, breath('out', 1.4, .06))
    # 1:55 arrival
    add(fx, 117.7, thud(90, .4, .3), -.3)
    add(fx, 117.9, thud(95, .4, .25), .3)
    steps(fx, 118.2, 139, 2.6, .06, -.2)
    steps(fx, 118.6, 139, 2.2, .05, .25)
    for k, t0 in enumerate(np.arange(122, 140, 3.1)):
        add(fx, t0, breath('in', .55, .05))
        add(fx, t0 + .6, breath('out', .9, .06, .4))
    # 2:20 human effort
    for t0 in np.arange(145, 150, .48):
        add(fx, t0, shape(bp(noise(.25), 400, 3000), .03, .15) * .06, .2)
    for t0 in np.arange(140.4, 162, 2.2):
        add(fx, t0, breath('in', .6, .06))
        add(fx, t0 + .7, breath('out', 1.1, .075, .8))
    add(fx, 151.9, sigh(.75, .06))
    steps(fx, 155.0, 158.0, 3.2, .06)
    # 2:45 after
    add(fx, 165.8, breath('in', 1.0, .06))
    add(fx, 166.9, breath('out', 2.4, .08))
    for i in range(14):
        t0 = 171 + i * .12 + rng.uniform(0, .04)
        n = int(.08 * SR)
        t = np.arange(n) / SR
        f = rng.uniform(500, 900) * (1 + 2 * t / .08)
        add(fx, t0, np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 40) * .03)
    fx *= env_curve([(0, 1), (176, 1), (178, 0), (180, 0)])
    return fx


def write(path, x, peak_db):
    x = x / (np.abs(x).max() + 1e-9) * 10 ** (peak_db / 20)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    wavfile.write(path, SR, (x.T * 32767).astype(np.int16))


if __name__ == '__main__':
    write(os.path.join(DOC, 'music', 'score.wav'), score(), -3)
    write(os.path.join(DOC, 'music', 'foley.wav'), foley(), -12)
    print('wrote music/score.wav and music/foley.wav')
