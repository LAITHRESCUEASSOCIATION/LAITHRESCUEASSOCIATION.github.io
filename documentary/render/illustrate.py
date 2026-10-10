#!/usr/bin/env python3
"""Illustrated version of the Laith documentary shots.

Draws every shot listed in ../shots.csv as an animated illustration (pycairo)
and encodes it to ../shots/NN.mp4, ready for ../assemble.sh.

    python3 render/illustrate.py              # all shots
    python3 render/illustrate.py --only 03,04 # some shots
    python3 render/illustrate.py --sheet      # contact sheet of mid-frames only
"""
import argparse
import csv
import math
import os
import random
import subprocess
from multiprocessing import Pool

import cairo
import numpy as np
from PIL import Image, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
DOC = os.path.dirname(HERE)
W, H, FPS = 1920, 1080, 24
TAU = 2 * math.pi
ROUND = cairo.LINE_CAP_ROUND

# Laith field uniform palette (from assets/uniform-reference.jpg)
NAVY = '#2d325f'
NAVY_D = '#1f2347'
SHIRT = '#2a2f5a'
GOLD = '#e2b034'
SILVER = '#cfd3d9'
GREEN = '#2f8f5b'
SKIN = '#8a5a3b'
SKIN2 = '#9c6a47'
SKIN3 = '#7a4c30'
BEARD = '#1c1613'
SHOE = '#1b1b20'
CAPC = '#242951'
CAR = '#ecebe5'
TIRE = '#1a1a1c'
GLOVE = '#17171b'


# ---------------------------------------------------------------- utilities

def rgb(h):
    h = h.lstrip('#')
    return tuple(int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))


def mix(a, b, t):
    A, B = rgb(a), rgb(b)
    return '#%02x%02x%02x' % tuple(int(255 * (x + (y - x) * t)) for x, y in zip(A, B))


def col(ctx, h, a=1.0):
    ctx.set_source_rgba(*rgb(h), a)


def lin(x0, y0, x1, y1, stops):
    g = cairo.LinearGradient(x0, y0, x1, y1)
    for s in stops:
        g.add_color_stop_rgba(s[0], *rgb(s[1]), s[2] if len(s) > 2 else 1)
    return g


def rad(cx, cy, r0, r1, stops):
    g = cairo.RadialGradient(cx, cy, r0, cx, cy, r1)
    for s in stops:
        g.add_color_stop_rgba(s[0], *rgb(s[1]), s[2] if len(s) > 2 else 1)
    return g


def clamp(x, a=0.0, b=1.0):
    return max(a, min(b, x))


def ease(x):
    x = clamp(x)
    return x * x * (3 - 2 * x)


def lerp(a, b, t):
    return a + (b - a) * t


def wob(t, seed, speed=1.0):
    rs = random.Random(seed)
    s = n = 0
    for k in range(3):
        f = rs.uniform(.15, .5) * speed * (k + 1)
        p = rs.uniform(0, TAU)
        s += math.sin(TAU * f * t + p) / (k + 1)
        n += 1 / (k + 1)
    return s / n


def spline(ctx, pts, closed=True):
    n = len(pts)
    ctx.move_to(*pts[0])
    rng = range(n) if closed else range(n - 1)
    for i in rng:
        p0 = pts[i - 1] if (closed or i > 0) else pts[0]
        p1 = pts[i]
        p2 = pts[(i + 1) % n]
        p3 = pts[(i + 2) % n] if (closed or i + 2 < n) else pts[-1]
        ctx.curve_to(p1[0] + (p2[0] - p0[0]) / 6, p1[1] + (p2[1] - p0[1]) / 6,
                     p2[0] - (p3[0] - p1[0]) / 6, p2[1] - (p3[1] - p1[1]) / 6, p2[0], p2[1])
    if closed:
        ctx.close_path()


def poly(ctx, pts):
    ctx.move_to(*pts[0])
    for p in pts[1:]:
        ctx.line_to(*p)
    ctx.close_path()


def rrect(ctx, x, y, w, h, r):
    r = min(r, w / 2, h / 2)
    ctx.new_sub_path()
    ctx.arc(x + w - r, y + r, r, -TAU / 4, 0)
    ctx.arc(x + w - r, y + h - r, r, 0, TAU / 4)
    ctx.arc(x + r, y + h - r, r, TAU / 4, TAU / 2)
    ctx.arc(x + r, y + r, r, TAU / 2, 3 * TAU / 4)
    ctx.close_path()


def ellipse(ctx, x, y, rx, ry):
    ctx.save()
    ctx.translate(x, y)
    ctx.scale(max(rx, 1e-3), max(ry, 1e-3))
    ctx.arc(0, 0, 1, 0, TAU)
    ctx.restore()


def line(ctx, pts, w, color, a=1.0, cap=ROUND):
    ctx.set_line_cap(cap)
    ctx.set_line_join(cairo.LINE_JOIN_ROUND)
    ctx.set_line_width(w)
    col(ctx, color, a)
    ctx.move_to(*pts[0])
    for p in pts[1:]:
        ctx.line_to(*p)
    ctx.stroke()


def surface_array(s):
    s.flush()
    w, h = s.get_width(), s.get_height()
    return np.frombuffer(s.get_data(), np.uint8).reshape(h, s.get_stride())[:, :w * 4].reshape(h, w, 4)


def array_surface(a):
    h, w = a.shape[:2]
    s = cairo.ImageSurface(cairo.FORMAT_ARGB32, w, h)
    buf = np.frombuffer(s.get_data(), np.uint8).reshape(h, s.get_stride())
    buf[:, :w * 4] = a.reshape(h, w * 4)
    s.mark_dirty()
    return s


def pil_surface(im):
    a = np.array(im.convert('RGBA'), dtype=np.float32)
    a[..., :3] *= a[..., 3:4] / 255
    return array_surface(a[..., [2, 1, 0, 3]].astype(np.uint8))


def blur_surface(s, r):
    if r < 0.3:
        return s
    im = Image.fromarray(surface_array(s).copy(), 'RGBA').filter(ImageFilter.GaussianBlur(r))
    return array_surface(np.array(im))


def offscreen(draw, blur=0, w=W, h=H):
    s = cairo.ImageSurface(cairo.FORMAT_ARGB32, w, h)
    draw(cairo.Context(s))
    return blur_surface(s, blur)


def paint_surface(ctx, s, x=0, y=0, alpha=1.0):
    ctx.set_source_surface(s, x, y)
    ctx.paint_with_alpha(alpha)


_cache = {}


def cached(key, fn):
    if key not in _cache:
        _cache[key] = fn()
    return _cache[key]


# ------------------------------------------------------------ logo & fabric

def _logo_image(kind):
    im = Image.open(os.path.join(DOC, 'assets', 'laith-logo-gold.png')).convert('RGBA')
    if kind == 'vest':  # on the vest the clasped-hands emblem is printed white
        a = np.array(im)
        a[:870, :690, :3] = 240
        im = Image.fromarray(a)
    return im


def logo(ctx, kind, x, y, w, alpha=1.0):
    sizes = [48, 96, 192, 384, 768, 1536]
    mw = next((s for s in sizes if s >= w), sizes[-1])

    def make():
        im = _logo_image(kind)
        return pil_surface(im.resize((mw, round(im.height * mw / im.width)), Image.LANCZOS))
    s = cached(('logo', kind, mw), make)
    k = w / s.get_width()
    ctx.save()
    ctx.translate(x, y)
    ctx.scale(k, k)
    ctx.translate(-s.get_width() / 2, -s.get_height() / 2)
    ctx.set_source_surface(s, 0, 0)
    ctx.get_source().set_filter(cairo.FILTER_GOOD)
    ctx.paint_with_alpha(alpha)
    ctx.restore()


def fabric(ctx, px=1.0, alpha=0.35):
    """Woven-fabric texture, soft-light blended into the current clip."""
    def make():
        n = 512
        y, x = np.mgrid[0:n, 0:n]
        rs = np.random.default_rng(3)
        v = 128 + 16 * np.sin(x * TAU * 150 / n) * np.sin(y * TAU * 150 / n) + rs.normal(0, 11, (n, n))
        im = Image.fromarray(np.clip(v, 0, 255).astype(np.uint8), 'L').filter(ImageFilter.GaussianBlur(.6))
        return pil_surface(im.convert('RGBA'))
    p = cairo.SurfacePattern(cached('fabric', make))
    p.set_extend(cairo.EXTEND_REPEAT)
    p.set_filter(cairo.FILTER_GOOD)
    p.set_matrix(cairo.Matrix(xx=1 / px, yy=1 / px))
    ctx.save()
    ctx.set_operator(cairo.OPERATOR_SOFT_LIGHT)
    ctx.set_source(p)
    ctx.paint_with_alpha(alpha)
    ctx.restore()


# ------------------------------------------------------------ environment

TOD = {
    'dawn': dict(sky=[(0, '#141b33'), (.55, '#3b4466'), (.85, '#b9785a'), (1, '#f0b47a')],
                 far='#3a3448', mid='#4a3d45', near='#5e4a44', ground='#6d5546', sun='#ffd3a0', haze='#e8a676'),
    'morning': dict(sky=[(0, '#6f9cc4'), (.7, '#bcd2df'), (1, '#efe2cc')],
                    far='#a99a8f', mid='#c9a77c', near='#d6b17f', ground='#d2aa76', sun='#fff3d8', haze='#f3e2c6'),
    'noon': dict(sky=[(0, '#4f8bc4'), (.7, '#a9cbe3'), (1, '#e9e4d6')],
                 far='#b4a08d', mid='#d7b07a', near='#e0b880', ground='#dcb27a', sun='#ffffff', haze='#f1e6d2'),
    'golden': dict(sky=[(0, '#6f86a8'), (.5, '#e3b07a'), (1, '#f6d29b')],
                   far='#a07a66', mid='#c98f5a', near='#d49c62', ground='#c88d57', sun='#fff0c8', haze='#f4c88e'),
    'sunset': dict(sky=[(0, '#262447'), (.45, '#7b4a5e'), (.8, '#e0763d'), (1, '#f7c068')],
                   far='#4a3243', mid='#5e3a37', near='#6e432f', ground='#5a3624', sun='#ffe2a0', haze='#f0904a'),
}


def ridge(ctx, base, amp, seed, xoff=0.0, rough=0.0, x0=-60, x1=W + 60, bottom=H + 60):
    rs = random.Random(seed)
    comps = [(rs.uniform(.0008, .004), rs.uniform(0, TAU), rs.uniform(.3, 1)) for _ in range(6)]
    if rough:
        comps += [(rs.uniform(.01, .03), rs.uniform(0, TAU), rough * rs.uniform(.1, .3)) for _ in range(5)]
    tot = sum(c[2] for c in comps)
    ctx.move_to(x0, bottom)
    for x in range(int(x0), int(x1) + 12, 12):
        X = x + xoff
        ctx.line_to(x, base - amp * sum(a * math.sin(f * X + p) for f, p, a in comps) / tot)
    ctx.line_to(x1, bottom)
    ctx.close_path()


def ridge_y(base, amp, seed, x, xoff=0.0):
    rs = random.Random(seed)
    comps = [(rs.uniform(.0008, .004), rs.uniform(0, TAU), rs.uniform(.3, 1)) for _ in range(6)]
    tot = sum(c[2] for c in comps)
    return base - amp * sum(a * math.sin(f * (x + xoff) + p) for f, p, a in comps) / tot


def desert(ctx, tod, hy, xoff=0.0, sun=None, mount=True, seed=1, dunes=True, near_y=None):
    p = TOD[tod]
    ctx.set_source(lin(0, 0, 0, hy, p['sky']))
    ctx.rectangle(-200, -200, W + 400, hy + 210)
    ctx.fill()
    if sun:
        sx, sy, sr = sun
        ctx.set_source(rad(sx, sy, 0, sr * 12, [(0, p['sun'], .85), (.1, p['sun'], .45), (1, p['sun'], 0)]))
        ctx.rectangle(-200, -200, W + 400, hy + 210)
        ctx.fill()
        col(ctx, p['sun'])
        ctx.arc(sx, sy, sr, 0, TAU)
        ctx.fill()
    if mount:
        ridge(ctx, hy - 10, 70, seed, xoff * .15, rough=.6, x0=-200, x1=W + 200)
        ctx.set_source(lin(0, hy - 140, 0, hy + 20, [(0, p['far']), (1, mix(p['far'], p['haze'], .55))]))
        ctx.fill()
    col(ctx, p['haze'], .35)
    ctx.rectangle(-200, hy - 30, W + 400, 40)
    ctx.fill()
    ridge(ctx, hy + 10, 22, seed + 1, xoff * .35, x0=-200, x1=W + 200)
    ctx.set_source(lin(0, hy - 20, 0, hy + 80, [(0, mix(p['mid'], p['haze'], .3)), (1, p['mid'])]))
    ctx.fill()
    if dunes:
        ny = near_y if near_y is not None else hy + 150
        ridge(ctx, ny, 45, seed + 2, xoff * .7, x0=-200, x1=W + 200)
        ctx.set_source(lin(0, ny - 50, 0, H, [(0, p['near']), (1, p['ground'])]))
        ctx.fill()


def dust(ctx, t, n, seed, color='#fff1d6', alpha=.5, area=(0, 0, W, H), vx=12, vy=-4, size=(1, 3)):
    rs = random.Random(seed)
    ax, ay, aw, ah = area
    for _ in range(n):
        x0, y0 = rs.uniform(0, aw), rs.uniform(0, ah)
        s, ph, sp = rs.uniform(*size), rs.uniform(0, TAU), rs.uniform(.5, 1.5)
        x = ax + (x0 + vx * sp * t + 10 * math.sin(t * .7 + ph)) % aw
        y = ay + (y0 + vy * sp * t + 6 * math.sin(t * .9 + ph * 2)) % ah
        col(ctx, color, alpha * (.45 + .55 * math.sin(t * 1.3 + ph) ** 2))
        ctx.arc(x, y, s, 0, TAU)
        ctx.fill()


def puffs(ctx, t, emit, rate, life, seed, color='#e2c08e', alpha=.5, grow=60, drift=(0, -20), r0=8):
    """Dust cloud: particles spawned at emit(tau) for tau in [t-life, t]."""
    k1 = math.floor(t * rate)
    for k in range(int(k1 - life * rate), k1 + 1):
        tau = k / rate
        if tau < 0 or tau > t:
            continue
        src = emit(tau)
        if src is None:
            continue
        age = t - tau
        if age >= life:
            continue
        rs = random.Random(seed * 100003 + k)
        dx, dy = rs.uniform(-1, 1), rs.uniform(-1, .3)
        x = src[0] + (drift[0] + dx * 30) * age
        y = src[1] + (drift[1] + dy * 15) * age
        r = r0 + grow * age * rs.uniform(.6, 1.2)
        a = alpha * (1 - age / life) ** 1.5
        ctx.set_source(rad(x, y, 0, r, [(0, color, a), (1, color, 0)]))
        ctx.arc(x, y, r, 0, TAU)
        ctx.fill()


def vignette(ctx, a=.45):
    ctx.set_source(rad(W / 2, H / 2, H * .45, W * .75, [(0, '#000000', 0), (1, '#000000', a)]))
    ctx.paint()


def handheld(ctx, t, amt=6, seed=1, rot=.003, zoom=1.03):
    ctx.translate(W / 2, H / 2)
    ctx.scale(zoom, zoom)
    ctx.rotate(rot * wob(t, seed + 7))
    ctx.translate(-W / 2 + amt * wob(t, seed), -H / 2 + amt * wob(t, seed + 3))


def zoom_about(ctx, k, cx=W / 2, cy=H / 2):
    ctx.translate(cx, cy)
    ctx.scale(k, k)
    ctx.translate(-cx, -cy)


def grade_light(ctx, x, y, r, color, a):
    ctx.save()
    ctx.set_operator(cairo.OPERATOR_SCREEN)
    ctx.set_source(rad(x, y, 0, r, [(0, color, a), (1, color, 0)]))
    ctx.paint()
    ctx.restore()


# ------------------------------------------------------------ vehicles

def wheel(ctx, x, y, r, rot, rim='#8d8f93'):
    col(ctx, TIRE)
    ctx.arc(x, y, r, 0, TAU)
    ctx.fill()
    col(ctx, rim)
    ctx.arc(x, y, r * .58, 0, TAU)
    ctx.fill()
    for k in range(6):
        a = rot + k * TAU / 6
        line(ctx, [(x, y), (x + math.cos(a) * r * .55, y + math.sin(a) * r * .55)], r * .12, '#5d5f63')
    col(ctx, '#404246')
    ctx.arc(x, y, r * .15, 0, TAU)
    ctx.fill()


def tinted(ctx, draw, sil=0.0, silc='#120e18', light=None):
    """Draw into a group, then darken / light it (ATOP) before compositing."""
    if not sil and not light:
        draw()
        return
    ctx.push_group()
    draw()
    ctx.set_operator(cairo.OPERATOR_ATOP)
    if sil:
        col(ctx, silc, sil)
        ctx.paint()
    if light:
        (x0, y0, x1, y1, c, a) = light
        ctx.set_source(lin(x0, y0, x1, y1, [(0, c, a), (1, c, 0)]))
        ctx.paint()
    ctx.pop_group_to_source()
    ctx.paint()


def fj_side(ctx, x, y, L, facing=1, rot=0.0, body=CAR, sil=0.0, door=0.0, sway=0.0, dusty=.45, light=None,
            shadow=(0, 1)):
    ctx.save()
    ctx.translate(x, y)
    k = L / 100
    col(ctx, '#000000', .25 * (1 - sil * .5))
    ellipse(ctx, shadow[0] * 30 * k, 2 * k, 58 * k, 4 * k * shadow[1])
    ctx.fill()
    ctx.scale(facing * k, k)

    def draw():
        lower = [(-51, -12), (-52, -30), (-47, -37), (18, -38), (40, -35), (51, -30), (52, -13)]
        cabin = [(-47, -37), (-46, -58), (-42, -61), (11, -61), (15, -59), (24, -38)]
        for shape in (lower, cabin):
            poly(ctx, shape)
            ctx.set_source(lin(0, -61, 0, -12, [(0, mix(body, '#ffffff', .4)), (.55, body), (1, mix(body, '#a39d92', .5))]))
            ctx.fill()
        if dusty:
            poly(ctx, lower)
            ctx.set_source(lin(0, -12, 0, -26, [(0, '#c9a273', dusty), (1, '#c9a273', 0)]))
            ctx.fill()
        for wx in (-32, 33):
            col(ctx, '#3a3a3e')
            ctx.arc(wx, -11, 14.5, TAU / 2, TAU)
            ctx.close_path()
            ctx.fill()
        wins = [[(-43, -57), (-27, -57), (-27, -41), (-43, -41)], [(-24, -57), (-6, -57), (-6, -41), (-24, -41)],
                [(-3, -57), (11, -57), (20, -40), (-3, -40)]]
        for w_ in wins:
            poly(ctx, w_)
            ctx.set_source(lin(-40, -57, 10, -40, [(0, '#3d4652'), (.5, '#20262e'), (1, '#4a5563')]))
            ctx.fill()
        line(ctx, [(-5, -38), (-5, -15)], .5, '#8e8a83')
        line(ctx, [(17, -37), (17, -17)], .5, '#8e8a83')
        line(ctx, [(9, -30), (13, -30)], 1, '#6d6a65')
        if door > 0:
            poly(ctx, [(-4, -56), (16, -56), (16, -15), (-4, -15)])
            col(ctx, '#1d1f24')
            ctx.fill()
            poly(ctx, [(16, -57), (16 + 9 * door, -59), (16 + 9 * door, -13), (16, -15)])
            col(ctx, mix(body, '#9c978e', .3))
            ctx.fill()
        col(ctx, '#7c7f84')
        ctx.rectangle(49, -24, 5, 9)
        ctx.rectangle(-54, -24, 5, 9)
        ctx.fill()
        col(ctx, '#f4f1e6')
        ctx.arc(49.5, -30, 2.6, 0, TAU)
        ctx.fill()
        col(ctx, '#e88a2a')
        ctx.rectangle(49, -26.5, 2.5, 1.6)
        ctx.fill()
        for wx in (-32, 33):
            wheel(ctx, wx, -11, 11, rot)
        line(ctx, [(-45, -61), (-46 + sway, -150)], .7, '#222226')

    tinted(ctx, draw, sil, light=light)
    ctx.restore()


def fj_rear(ctx, x, y, w, sway=0.0, sil=0.0, body=CAR):
    ctx.save()
    ctx.translate(x, y)
    k = w / 100
    col(ctx, '#000000', .3)
    ellipse(ctx, 0, 1 * k, 58 * k, 5 * k)
    ctx.fill()
    ctx.scale(k, k)

    def draw():
        col(ctx, TIRE)
        rrect(ctx, -49, -18, 14, 18, 3)
        rrect(ctx, 35, -18, 14, 18, 3)
        ctx.fill()
        rrect(ctx, -50, -78, 100, 64, 6)
        ctx.set_source(lin(0, -78, 0, -14, [(0, mix(body, '#ffffff', .4)), (.6, body), (1, '#bfae93')]))
        ctx.fill()
        rrect(ctx, -39, -74, 78, 22, 3)
        ctx.set_source(lin(0, -74, 0, -52, [(0, '#4a5563'), (1, '#1d232b')]))
        ctx.fill()
        col(ctx, TIRE)
        ctx.arc(0, -36, 15, 0, TAU)
        ctx.fill()
        col(ctx, '#8d8f93')
        ctx.arc(0, -36, 8, 0, TAU)
        ctx.fill()
        col(ctx, '#b3262b')
        ctx.rectangle(-50, -56, 5, 18)
        ctx.rectangle(45, -56, 5, 18)
        ctx.fill()
        col(ctx, '#7c7f84')
        ctx.rectangle(-52, -20, 104, 7)
        ctx.fill()
        col(ctx, '#f2f2ee')
        ctx.rectangle(-9, -27, 18, 6)
        ctx.fill()
        line(ctx, [(40, -78), (42 + sway, -185)], .8, '#222226')

    tinted(ctx, draw, sil)
    ctx.restore()


def pickup_side(ctx, x, y, L, tilt=0.0, buried=0.0):
    ctx.save()
    ctx.translate(x, y)
    k = L / 100
    ctx.rotate(math.radians(tilt))
    ctx.scale(k, k)
    body = '#c9c2b4'
    poly(ctx, [(-52, -13), (-52, -33), (2, -34), (4, -53), (26, -53), (38, -36), (52, -32), (52, -13)])
    ctx.set_source(lin(0, -53, 0, -13, [(0, '#e4ded2'), (1, '#9e9685')]))
    ctx.fill()
    poly(ctx, [(7, -50), (24, -50), (33, -37), (7, -37)])
    col(ctx, '#2a3038')
    ctx.fill()
    line(ctx, [(-50, -33), (0, -33)], 1.2, '#8b8474')
    for wx in (-34, 34):
        col(ctx, '#3a3a3e')
        ctx.arc(wx, -11, 13.5, TAU / 2, TAU)
        ctx.fill()
        wheel(ctx, wx, -11, 10.5, .4)
    col(ctx, '#7c7f84')
    ctx.rectangle(50, -23, 4, 8)
    ctx.fill()
    ctx.restore()
    if buried:
        spline(ctx, [(x - L * .62, y + 8), (x - L * .45, y - L * .07 * buried), (x - L * .2, y - L * .02),
                     (x + L * .1, y + 10), (x - L * .2, y + 30)])
        col(ctx, '#d7ae76')
        ctx.fill()


# ------------------------------------------------------------ people

def _seg(p, ang, L, dirx):
    a = math.radians(ang)
    return (p[0] + math.sin(a) * L * dirx, p[1] + math.cos(a) * L)


def _band(ctx, a, b, f0, f1, w, color, alpha, store):
    p0 = (lerp(a[0], b[0], f0), lerp(a[1], b[1], f0))
    p1 = (lerp(a[0], b[0], f1), lerp(a[1], b[1], f1))
    line(ctx, [p0, p1], w, color, alpha, cap=cairo.LINE_CAP_BUTT)
    store.append((p0, p1, w))


def person(ctx, x, y, h, view='back', facing=1, phase=None, walk=1.0, arms=None, kneel=False, lean=0.0,
           nod=0.0, sil=0.0, tone=SKIN, vest_dy=0.0, carry=None, light=None, outfit='laith', gloves=False,
           breath=0.0, hide_head=False):
    """Stylised figure in the Laith uniform. Units: 100 = body height, feet at (0,0)."""
    ctx.save()
    ctx.translate(x, y)
    s = h / 100
    ctx.scale(s, s)
    out = {}
    THIGH, SHIN, UP, FORE = 23, 23, 15, 14
    f = facing
    side = view == 'side'
    # legs: (thigh angle, shin angle), positive = forward (side) / outward (back, front)
    lift = [0, 0]
    if kneel:
        legs = [(82, 0), (-8, -96)]
    elif phase is not None and side:
        legs = []
        for ph in (phase, phase + math.pi):
            th = 26 * walk * math.sin(ph)
            legs.append((th, th - 38 * walk * max(0.0, math.cos(ph))))
    else:
        legs = [(3, 2), (3, 2)]
        if phase is not None:
            lift = [4 * walk * max(0, math.sin(phase)), 4 * walk * max(0, -math.sin(phase))]
    hipx = [0, 0] if side else [-4.6, 4.6]
    dirs = [f, f] if side else [-1, 1]
    ank = []
    for i, (a1, a2) in enumerate(legs):
        k = _seg((hipx[i], 0), a1, THIGH, dirs[i])
        a = _seg(k, a2, SHIN - lift[i], dirs[i])
        ank.append((k, a))
    hip_y = -max(a[1] for _, a in ank) - 3
    Hc = (0, hip_y + (breath * .3))
    la = math.radians(lean)
    S = (Hc[0] + math.sin(la) * 33 * (f if side else 0), Hc[1] - math.cos(la) * 33 - breath)
    if arms is None:
        if phase is not None and side:
            arms = [(-22 * walk * math.sin(phase), -22 * walk * math.sin(phase) + 22),
                    (22 * walk * math.sin(phase), 22 * walk * math.sin(phase) + 22)]
        elif phase is not None:
            arms = [(8 + 5 * walk * math.sin(phase), 6), (8 - 5 * walk * math.sin(phase), 6)]
        else:
            arms = [(8, 4), (8, 4)] if not side else [(6, 18), (2, 14)]
    shx = [0, 0] if side else [-12, 12]
    arm_pts = []
    for i, (a1, a2) in enumerate(arms):
        sh = (S[0] + shx[i], S[1] + 2)
        el = _seg(sh, a1, UP, dirs[i])
        wr = _seg(el, a2, FORE, dirs[i])
        arm_pts.append((sh, el, wr))
    bands = []
    thobe = outfit == 'thobe'
    trou = '#2b3060'

    def draw_leg(i, dim=0.0):
        k, a = ank[i]
        hp = (Hc[0] + hipx[i], Hc[1])
        kk = (k[0] + Hc[0], k[1] + Hc[1])
        aa = (a[0] + Hc[0], a[1] + Hc[1])
        c = mix(trou, '#000000', dim)
        if not thobe:
            line(ctx, [hp, kk], 9.6, c)
            line(ctx, [kk, aa], 8.4, c)
            _band(ctx, kk, aa, .52, .6, 8.6, SILVER, 1, bands)
            _band(ctx, kk, aa, .7, .78, 8.6, SILVER, 1, bands)
        col(ctx, mix(SHOE, '#000000', dim))
        if side:
            ellipse(ctx, aa[0] + 2.6 * f, aa[1] + 1.6, 5.6, 2.6)
        else:
            ellipse(ctx, aa[0], aa[1] + 1.6, 4.2, 2.5)
        ctx.fill()

    def draw_arm(i, dim=0.0):
        sh, el, wr = arm_pts[i]
        sleeve = (lerp(sh[0], el[0], .62), lerp(sh[1], el[1], .62))
        sk = mix(tone, '#000000', dim)
        if thobe:
            line(ctx, [sh, el, wr], 6.2, mix('#ecebe6', '#000000', dim))
        else:
            line(ctx, [sh, el], 4.9, sk)
            line(ctx, [el, wr], 4.5, sk)
            line(ctx, [sh, sleeve], 6.8, mix(SHIRT, '#000000', dim))
        col(ctx, mix(GLOVE if gloves else tone, '#000000', dim))
        ctx.arc(wr[0], wr[1], 2.7, 0, TAU)
        ctx.fill()
        out['hand%d' % i] = ctx.user_to_device(*wr)

    def torso_path(dy=0.0, inset=0.0):
        if side:
            ux, uy = S[0] - Hc[0], S[1] - Hc[1]
            Ln = math.hypot(ux, uy)
            nx, ny = -uy / Ln * f, ux / Ln * f
            spline(ctx, [(S[0] - nx * 6.5, S[1] - ny * 6.5 + dy - 1), (S[0] + nx * 7.5, S[1] + ny * 7.5 + dy),
                         (lerp(S[0], Hc[0], .35) + nx * 8.8, lerp(S[1], Hc[1], .35) + ny * 8.8 + dy),
                         (Hc[0] + nx * 7.2, Hc[1] + ny * 7.2 + dy + 1.5), (Hc[0] - nx * 7.2, Hc[1] - ny * 7.2 + dy + 1.5),
                         (lerp(S[0], Hc[0], .5) - nx * 7, lerp(S[1], Hc[1], .5) - ny * 7 + dy)])
        else:
            w0, w1 = 13 - inset, 10.6 - inset
            ctx.move_to(S[0] - w0, S[1] + 3 + dy)
            ctx.curve_to(S[0] - w0, S[1] - 2 + dy, S[0] - 7, S[1] - 3 + dy, S[0] - 4, S[1] - 3 + dy)
            ctx.line_to(S[0] + 4, S[1] - 3 + dy)
            ctx.curve_to(S[0] + 7, S[1] - 3 + dy, S[0] + w0, S[1] - 2 + dy, S[0] + w0, S[1] + 3 + dy)
            ctx.line_to(Hc[0] + w1, Hc[1] + 2 + dy)
            ctx.line_to(Hc[0] - w1, Hc[1] + 2 + dy)
            ctx.close_path()

    def draw_torso():
        if thobe:
            ctx.move_to(S[0] - 12.5, S[1] + 2)
            ctx.curve_to(S[0] - 12, S[1] - 3, S[0] + 12, S[1] - 3, S[0] + 12.5, S[1] + 2)
            ctx.line_to(Hc[0] + 13, -2)
            ctx.line_to(Hc[0] - 13, -2)
            ctx.close_path()
            ctx.set_source(lin(-13, 0, 13, 0, [(0, '#cfccc4'), (.5, '#f3f1ec'), (1, '#d6d3cb')]))
            ctx.fill()
            return
        torso_path()
        col(ctx, SHIRT)
        ctx.fill()
        # vest
        ctx.save()
        torso_path(vest_dy, inset=-.4)
        ctx.set_source(lin(-14, 0, 14, 0, [(0, mix(NAVY, '#000000', .25)), (.5, NAVY), (1, mix(NAVY, '#000000', .2))]))
        ctx.fill_preserve()
        ctx.clip()
        if h > 500:
            fabric(ctx, 1.1 / s, .3)
        sy = lerp(S[1], Hc[1], .8) + vest_dy
        sy2 = lerp(S[1], Hc[1], .9) + vest_dy
        if side:
            ux = (S[0] - Hc[0]) * .1
            poly(ctx, [(-30 + ux, sy), (30 + ux, sy), (30, sy2), (-30, sy2)])
        else:
            ctx.rectangle(-20, sy, 40, sy2 - sy)
        col(ctx, SILVER)
        ctx.fill()
        bands.append(('rect', side, sy, sy2, S[0] - Hc[0]))
        if view == 'back':
            logo(ctx, 'vest', S[0], lerp(S[1], Hc[1], .33) + vest_dy, 17.5)
        elif view == 'front':
            line(ctx, [(S[0], S[1] - 2 + vest_dy), (Hc[0], Hc[1] + 2 + vest_dy)], .6, '#9097a3')
            logo(ctx, 'gold', S[0] - 6.5, S[1] + 6 + vest_dy, 5.2)
            col(ctx, GREEN)
            ctx.rectangle(S[0] + 4, S[1] + 4.6 + vest_dy, 5.2, 2.4)
            ctx.fill()
            for px_ in (-1, 1):
                col(ctx, NAVY_D, .7)
                ctx.rectangle(S[0] + px_ * 4 - (5 if px_ < 0 else 0), lerp(S[1], Hc[1], .45) + vest_dy, 5, 6)
                ctx.fill()
        else:
            cx_ = lerp(S[0], Hc[0], .22) + f * 5.6
            logo(ctx, 'gold', cx_, lerp(S[1], Hc[1], .2) + vest_dy, 3.6)
        ctx.restore()

    def draw_head():
        ctx.save()
        nk = (S[0], S[1] - 1)
        ctx.translate(*nk)
        ctx.rotate(math.radians(nod) * (f if side else 1))
        ctx.translate(-nk[0], -nk[1])
        hd = (S[0] + math.sin(la) * 10.5 * (f if side else 0), S[1] - 10.2)
        line(ctx, [nk, (hd[0], hd[1] + 3)], 5.4, mix(tone, '#000000', .18))
        if thobe:
            col(ctx, tone)
            ctx.arc(hd[0], hd[1], 5.8, 0, TAU)
            ctx.fill()
            spline(ctx, [(hd[0] - 7.5, hd[1] + 9), (hd[0] - 7.2, hd[1] - 3), (hd[0], hd[1] - 7.6),
                         (hd[0] + 7.2, hd[1] - 3), (hd[0] + 7.5, hd[1] + 9), (hd[0], hd[1] + 6)])
            col(ctx, '#b8333a')
            ctx.fill_preserve()
            ctx.save()
            ctx.clip()
            for gx in range(-8, 9, 2):
                line(ctx, [(hd[0] + gx, hd[1] - 8), (hd[0] + gx, hd[1] + 9)], .35, '#f1e9e4', .55)
            ctx.restore()
            ctx.restore()
            out['head'] = ctx.user_to_device(*hd)
            return
        col(ctx, tone)
        ctx.arc(hd[0], hd[1], 6, 0, TAU)
        ctx.fill()
        if view == 'back':
            ctx.save()
            ctx.arc(hd[0], hd[1], 6, 0, TAU)
            ctx.clip()
            ctx.set_source(lin(0, hd[1] - 2, 0, hd[1] + 6, [(0, '#1d1713'), (.75, '#2a201a'), (1, tone)]))
            ctx.paint()
            ctx.restore()
            ellipse(ctx, hd[0] - 6, hd[1] + .5, 1.1, 1.8)
            ellipse(ctx, hd[0] + 6, hd[1] + .5, 1.1, 1.8)
            col(ctx, mix(tone, '#000000', .15))
            ctx.fill()
            ctx.arc(hd[0], hd[1], 6.5, math.pi + .1, TAU - .1)
            ctx.close_path()
            col(ctx, CAPC)
            ctx.fill()
        elif view == 'front':
            ctx.save()
            ctx.arc(hd[0], hd[1], 6.05, 0, TAU)
            ctx.clip()
            spline(ctx, [(hd[0] - 6.2, hd[1] - .5), (hd[0] - 3, hd[1] + 1.8), (hd[0], hd[1] + 2.4),
                         (hd[0] + 3, hd[1] + 1.8), (hd[0] + 6.2, hd[1] - .5), (hd[0], hd[1] + 7)])
            col(ctx, BEARD, .93)
            ctx.fill()
            ctx.restore()
            col(ctx, '#140f0c')
            for ex in (-2.2, 2.2):
                ctx.arc(hd[0] + ex, hd[1] - .8, .6, 0, TAU)
                ctx.fill()
            ctx.arc(hd[0], hd[1], 6.5, math.pi, TAU)
            ctx.close_path()
            col(ctx, CAPC)
            ctx.fill()
            col(ctx, mix(CAPC, '#000000', .3))
            ellipse(ctx, hd[0], hd[1] - .9, 7.6, 1.5)
            ctx.fill()
        else:
            poly(ctx, [(hd[0] + f * 5.5, hd[1] - 1), (hd[0] + f * 7.4, hd[1] + 1.4), (hd[0] + f * 5.4, hd[1] + 2.2)])
            col(ctx, tone)
            ctx.fill()
            ctx.save()
            ctx.arc(hd[0], hd[1], 6.05, 0, TAU)
            ctx.clip()
            x0 = hd[0] - f * 1.5
            ctx.rectangle(min(x0, x0 + f * 9), hd[1] + 1.4, 9, 7)
            col(ctx, BEARD, .93)
            ctx.fill()
            ctx.rectangle(hd[0] - f * 7 if f > 0 else hd[0] + 1, hd[1] - 7, 6, 8.4)
            col(ctx, '#17120f')
            ctx.fill()
            ctx.restore()
            col(ctx, mix(tone, '#000000', .2))
            ellipse(ctx, hd[0] - f * .6, hd[1] + .2, 1.2, 1.7)
            ctx.fill()
            col(ctx, '#140f0c')
            ctx.arc(hd[0] + f * 3.7, hd[1] - .9, .55, 0, TAU)
            ctx.fill()
            ctx.arc(hd[0], hd[1], 6.4, math.pi, TAU)
            ctx.close_path()
            col(ctx, CAPC)
            ctx.fill()
            poly(ctx, [(hd[0] + f * 4, hd[1] - 2.2), (hd[0] + f * 10.8, hd[1] - 1.4), (hd[0] + f * 4, hd[1] - .6)])
            col(ctx, mix(CAPC, '#000000', .3))
            ctx.fill()
        ctx.restore()
        out['head'] = ctx.user_to_device(*hd)

    def draw_carry():
        if not carry:
            return
        i = 1 if not side else 0
        wr = arm_pts[i][2]
        if carry == 'bag':
            rrect(ctx, wr[0] - 6, wr[1] + 1, 12, 13, 2)
            ctx.set_source(lin(0, wr[1], 0, wr[1] + 14, [(0, '#d2452f'), (1, '#9b2a1d')]))
            ctx.fill()
            col(ctx, '#ffffff', .9)
            ctx.rectangle(wr[0] - .9, wr[1] + 4, 1.8, 6)
            ctx.rectangle(wr[0] - 3, wr[1] + 6.1, 6, 1.8)
            ctx.fill()
        elif carry == 'case':
            rrect(ctx, wr[0] - 7, wr[1] + 1, 14, 9, 1.5)
            col(ctx, '#7fb4d6', .9)
            ctx.fill()
        elif carry == 'bottle':
            ctx.save()
            ctx.translate(*wr)
            ctx.rotate(-1.0 * f)
            rrect(ctx, -1.6, -8, 3.2, 10, 1.2)
            col(ctx, '#bfe0f0', .85)
            ctx.fill()
            ctx.restore()

    def draw_all():
        if side:
            draw_arm(1, .25)
            draw_leg(1, .22)
            draw_leg(0)
            draw_torso()
            if not hide_head:
                draw_head()
            draw_arm(0)
        else:
            draw_leg(0)
            draw_leg(1)
            draw_torso()
            draw_arm(0)
            draw_arm(1)
            if not hide_head:
                draw_head()
        draw_carry()

    if sil or light:
        ctx.push_group()
        draw_all()
        ctx.set_operator(cairo.OPERATOR_ATOP)
        if sil:
            col(ctx, '#140f18', sil)
            ctx.paint()
        if light:
            dx, dy, c, a = light
            ctx.set_source(lin(-dx * 20, -50 - dy * 50, dx * 20, -50 + dy * 50, [(0, c, a), (1, c, 0)]))
            ctx.paint()
        ctx.set_operator(cairo.OPERATOR_OVER)
        if sil:  # reflective tape still catches the light
            for b in bands:
                if b[0] == 'rect':
                    continue
                p0, p1, w_ = b
                line(ctx, [p0, p1], w_, '#f3dcc0', .55 * sil, cap=cairo.LINE_CAP_BUTT)
        ctx.pop_group_to_source()
        ctx.paint()
    else:
        draw_all()
    ctx.restore()
    return out


def bust(ctx, x, y, s, facing=1, nod=0.0, tone=SKIN, beard=1.0, squint=0.0, blink=0.0, light=None, sil=0.0,
         sweat=0.0, rim='#ffcf8a'):
    """Profile head-and-shoulders close-up. Units: head about 100 tall, origin at head centre."""
    ctx.save()
    ctx.translate(x, y)
    ctx.scale(s * facing, s)

    def draw():
        spline(ctx, [(-150, 260), (-140, 110), (-90, 74), (-30, 66), (30, 68), (80, 88), (122, 132), (132, 260)])
        ctx.set_source(lin(-150, 0, 130, 0, [(0, mix(NAVY, '#000000', .3)), (.6, NAVY), (1, mix(NAVY, '#000000', .1))]))
        ctx.fill_preserve()
        ctx.save()
        ctx.clip()
        fabric(ctx, 1.2 / s, .35)
        col(ctx, NAVY_D, .6)
        line(ctx, [(-60, 80), (-80, 260)], 1.5, NAVY_D, .6)
        ctx.save()
        ctx.translate(70, 150)
        ctx.scale(facing, 1)
        logo(ctx, 'gold', 0, 0, 40)
        ctx.restore()
        ctx.restore()
        poly(ctx, [(-34, 64), (-10, 92), (16, 94), (36, 68), (18, 76), (-20, 74)])
        col(ctx, SHIRT)
        ctx.fill()
        poly(ctx, [(-22, 26), (16, 38), (20, 84), (-28, 86)])
        ctx.set_source(lin(0, 30, 0, 86, [(0, mix(tone, '#000000', .45)), (1, mix(tone, '#000000', .15))]))
        ctx.fill()
        ctx.save()
        ctx.translate(0, 40)
        ctx.rotate(math.radians(nod))
        ctx.translate(0, -40)
        head = [(-2, -58), (22, -52), (36, -34), (40, -16), (38, -8), (44, 2), (52, 10), (48, 14), (41, 16),
                (43, 22), (40, 25), (42, 29), (39, 34), (35, 44), (22, 50), (6, 48), (-8, 42), (-20, 34),
                (-30, 18), (-44, -4), (-46, -24), (-36, -46), (-20, -56)]
        spline(ctx, head)
        col(ctx, tone)
        ctx.fill()
        ctx.save()
        spline(ctx, head)
        ctx.clip()
        ctx.set_source(lin(-46, 0, 52, 0, [(0, '#000000', .35), (.6, '#000000', 0), (1, '#ffffff', .06)]))
        ctx.paint()
        ctx.restore()
        if beard:
            spline(ctx, [(41, 30), (38, 37), (34, 46), (20, 52), (4, 50), (-10, 44), (-19, 32), (-17, 18),
                         (-8, 22), (4, 30), (18, 32), (30, 30), (37, 27)])
            col(ctx, BEARD, .92 * beard)
            ctx.fill()
            spline(ctx, [(34, 18), (42, 19), (44, 22), (38, 23), (32, 21)])
            col(ctx, BEARD, .9 * beard)
            ctx.fill()
        spline(ctx, [(-46, -22), (-44, -4), (-30, 16), (-20, 30), (-15, 18), (-24, 4), (-30, -14)])
        col(ctx, '#17120f')
        ctx.fill()
        col(ctx, mix(tone, '#000000', .22))
        ellipse(ctx, -12, 4, 6, 9)
        ctx.fill()
        line(ctx, [(-12, -1), (-9, 6)], 1.4, mix(tone, '#000000', .45))
        eh = 2.4 * (1 - .55 * squint) * (1 - blink)
        col(ctx, '#e9e2d6')
        ellipse(ctx, 28, -6 + squint, 5, max(.3, eh))
        ctx.fill()
        col(ctx, '#1a120e')
        ellipse(ctx, 30, -6 + squint, 2.4, max(.3, eh * .95))
        ctx.fill()
        line(ctx, [(22, -8.5 + squint), (34, -8 + squint)], 1.2, '#2a1b14', .9)
        line(ctx, [(18, -15 + squint * 2), (27, -17 + squint * 2), (36, -14 + squint * 2)], 3.4, '#1f1612')
        line(ctx, [(39, 25), (35, 25.5)], 1.2, '#4a2a1e', .8)
        if sweat:
            for sx_, sy_ in ((30, -24), (24, -30), (14, -26)):
                col(ctx, '#ffffff', .55 * sweat)
                ellipse(ctx, sx_, sy_, 1.4, 2)
                ctx.fill()
        cap = [(-48, -14), (-45, -40), (-27, -61), (0, -67), (24, -61), (38, -43), (41, -27), (34, -22),
               (0, -24), (-30, -18)]
        spline(ctx, cap)
        ctx.set_source(lin(-40, -67, 30, -20, [(0, mix(CAPC, '#000000', .3)), (1, mix(CAPC, '#ffffff', .08))]))
        ctx.fill()
        spline(ctx, [(30, -31), (64, -25), (67, -20), (33, -20)])
        col(ctx, mix(CAPC, '#000000', .35))
        ctx.fill()
        line(ctx, [(-10, -66), (20, -26)], .8, '#000000', .3)
        ctx.restore()

    if sil or light:
        ctx.push_group()
        draw()
        ctx.set_operator(cairo.OPERATOR_ATOP)
        if sil:
            col(ctx, '#150f12', sil)
            ctx.paint()
            ctx.set_source(lin(70, 0, 25, 0, [(0, rim, .85), (1, rim, 0)]))
            ctx.paint()
        if light:
            x0, x1, c, a = light
            ctx.set_source(lin(x0, 0, x1, 0, [(0, c, a), (1, c, 0)]))
            ctx.paint()
        ctx.pop_group_to_source()
        ctx.paint()
    else:
        draw()
    ctx.restore()


def hand(ctx, x, y, s, angle=0.0, kind='glove', grip=0.0, flip=False, tone=SKIN, sleeve=None, cuff=None):
    """Hand pointing along +x from the wrist at (x,y). kind: glove | skin."""
    ctx.save()
    ctx.translate(x, y)
    ctx.rotate(angle)
    ctx.scale(s, -s if flip else s)
    c = GLOVE if kind == 'glove' else tone
    hi = '#3a3a42' if kind == 'glove' else mix(tone, '#ffffff', .15)
    if sleeve:
        rrect(ctx, -420, -26, 420, 52, 10)
        ctx.set_source(lin(0, -26, 0, 26, [(0, mix(sleeve, '#ffffff', .1)), (1, mix(sleeve, '#000000', .3))]))
        ctx.fill()
        if cuff:
            ctx.rectangle(-60, -26, 12, 52)
            col(ctx, cuff)
            ctx.fill()
    if kind == 'skin' and not sleeve:
        line(ctx, [(-300, 0), (0, 0)], 34, tone)
    rrect(ctx, -4, -19, 46, 38, 12)
    ctx.set_source(lin(0, -19, 0, 19, [(0, hi), (1, c)]))
    ctx.fill()
    for i, (fy, fl) in enumerate(((-13, 26), (-4.5, 30), (4.5, 28), (13, 22))):
        b = math.radians(70 * grip)
        p0 = (40, fy)
        p1 = (40 + fl * .55, fy)
        p2 = (p1[0] + math.cos(b) * fl * .5, fy + math.sin(b) * fl * .5)
        line(ctx, [p0, p1, p2], 9, c)
        line(ctx, [(p0[0] + 2, fy - 2.5), (p1[0], fy - 2.5)], 1.6, hi, .6)
    ta = math.radians(-55 + 40 * grip)
    t0 = (14, -16)
    line(ctx, [t0, (t0[0] + math.cos(ta) * 26, t0[1] + math.sin(ta) * 26)], 10, c)
    if kind == 'glove':
        rrect(ctx, -8, -21, 14, 42, 4)
        col(ctx, '#26262c')
        ctx.fill()
    ctx.restore()


def vest_flat(ctx, x, y, w, side='front', zip_y=-46.0, gap=7.0, badge=True, hang=False, tex=True):
    """The Laith vest laid flat / hanging. Units: 100 = vest width; origin at vest centre."""
    ctx.save()
    ctx.translate(x, y)
    k = w / 100
    ctx.scale(k, k)

    def outline():
        ctx.move_to(-17, -62)
        ctx.line_to(-34, -58)
        ctx.curve_to(-30, -45, -28, -30, -40, -18)
        ctx.line_to(-41, 56)
        ctx.curve_to(-20, 59, 20, 59, 41, 56)
        ctx.line_to(40, -18)
        ctx.curve_to(28, -30, 30, -45, 34, -58)
        ctx.line_to(17, -62)
        if side == 'front':
            ctx.curve_to(10, -48, -10, -48, -17, -62)
        else:
            ctx.curve_to(10, -58, -10, -58, -17, -62)
        ctx.close_path()

    outline()
    ctx.set_source(lin(-41, 0, 41, 0, [(0, mix(NAVY, '#000000', .3)), (.45, mix(NAVY, '#ffffff', .03)),
                                       (1, mix(NAVY, '#000000', .25))]))
    ctx.fill_preserve()
    ctx.save()
    ctx.clip()
    if tex:
        fabric(ctx, 1.0 / k, .4)
    ctx.set_source(lin(0, 28, 0, 38, [(0, '#aeb3ba'), (.4, '#eef0f2'), (1, '#b7bcc3')]))
    ctx.rectangle(-45, 28, 90, 10)
    ctx.fill()
    line(ctx, [(-45, 28.2), (45, 28.2)], .3, '#7d828a')
    line(ctx, [(-45, 37.8), (45, 37.8)], .3, '#7d828a')
    if side == 'back':
        logo(ctx, 'vest', 0, -16, 60)
    else:
        if zip_y > -46:
            poly(ctx, [(-gap, -64), (gap, -64), (0, zip_y)])
            ctx.set_source(lin(-gap, 0, gap, 0, [(0, '#151834'), (.5, SHIRT), (1, '#151834')]))
            ctx.fill()
        zy = zip_y
        yy = max(zy, -48)
        while yy < 56:
            col(ctx, '#3b3f4c')
            ctx.rectangle(-.9, yy, 1.8, .7)
            ctx.fill()
            col(ctx, '#6c717d')
            ctx.rectangle(-.9, yy + .7, 1.8, .4)
            ctx.fill()
            yy += 1.3
        rrect(ctx, -1.8, zy - 1, 3.6, 5, .8)
        ctx.set_source(lin(-2, 0, 2, 0, [(0, '#8b9099'), (.5, '#e0e3e7'), (1, '#7b8089')]))
        ctx.fill()
        rrect(ctx, -1.1, zy + 3.4, 2.2, 5, .6)
        col(ctx, '#2b2d33')
        ctx.fill()
        for px_ in (-1, 1):
            rrect(ctx, min(px_ * 8, px_ * 30), -18, 22, 22, 1.2)
            col(ctx, NAVY_D, .55)
            ctx.fill()
            rrect(ctx, min(px_ * 8, px_ * 30), -20, 22, 6, 1.2)
            col(ctx, NAVY_D, .85)
            ctx.fill()
        logo(ctx, 'gold', -20, -34, 14)
        if badge:
            draw_badge(ctx, 20, -34, 16)
    ctx.restore()
    outline()
    ctx.set_line_width(.6)
    col(ctx, '#11132a', .8)
    ctx.stroke()
    ctx.restore()


def draw_badge(ctx, x, y, w, alpha=1.0):
    h = w * .48
    rrect(ctx, x - w / 2, y - h / 2, w, h, w * .06)
    ctx.set_source(lin(0, y - h / 2, 0, y + h / 2, [(0, '#3aa36b', alpha), (1, '#23744a', alpha)]))
    ctx.fill()
    ctx.set_line_width(w * .025)
    col(ctx, '#e8f2ec', .8 * alpha)
    rrect(ctx, x - w / 2 + w * .05, y - h / 2 + w * .05, w * .9, h - w * .1, w * .04)
    ctx.stroke()
    for i, ln in enumerate((.55, .4)):
        line(ctx, [(x + w * .35, y - h * .12 + i * h * .3), (x + w * .35 - w * ln, y - h * .12 + i * h * .3)],
             w * .045, '#ffffff', .85 * alpha)
    logo(ctx, 'gold', x - w * .3, y, w * .22, alpha)


def first_aid_bag(ctx, x, y, w, rot=0.0):
    ctx.save()
    ctx.translate(x, y)
    ctx.rotate(rot)
    k = w / 100
    ctx.scale(k, k)
    line(ctx, [(-22, -58), (-16, -74), (16, -74), (22, -58)], 6, '#2b2b30')
    rrect(ctx, -50, -60, 100, 120, 18)
    ctx.set_source(lin(-50, -60, 50, 60, [(0, '#e0553a'), (1, '#9a2a1d')]))
    ctx.fill()
    rrect(ctx, -36, 0, 72, 46, 10)
    col(ctx, '#b7341f')
    ctx.fill()
    line(ctx, [(-46, -46), (46, -46)], 2.4, '#3a2a28')
    col(ctx, '#ffffff')
    ctx.rectangle(-6, -36, 12, 32)
    ctx.rectangle(-16, -26, 32, 12)
    ctx.fill()
    ctx.set_source(lin(0, 20, 0, 28, [(0, '#b7bcc3'), (.5, '#f1f2f4'), (1, '#b7bcc3')]))
    ctx.rectangle(-36, 20, 72, 7)
    ctx.fill()
    ctx.restore()


def radio(ctx, x, y, w, t, rot=0.0):
    ctx.save()
    ctx.translate(x, y)
    ctx.rotate(rot)
    k = w / 100
    ctx.scale(k, k)
    line(ctx, [(-28, -120), (-28, -230)], 14, '#111114')
    rrect(ctx, -50, -125, 100, 250, 18)
    ctx.set_source(lin(-50, 0, 50, 0, [(0, '#2a2b30'), (.5, '#3a3b42'), (1, '#1c1d21')]))
    ctx.fill()
    col(ctx, '#111114')
    ctx.arc(20, -140, 13, 0, TAU)
    ctx.fill()
    rrect(ctx, -34, -100, 68, 50, 6)
    col(ctx, '#6f8a6c')
    ctx.fill()
    for i in range(7):
        line(ctx, [(-30, -20 + i * 12), (30, -20 + i * 12)], 4, '#16161a')
    on = (t % .9) < .25
    col(ctx, '#58ff8a' if on else '#1f4a2a')
    ctx.arc(-24, -110, 5, 0, TAU)
    ctx.fill()
    if on:
        ctx.set_source(rad(-24, -110, 0, 30, [(0, '#58ff8a', .6), (1, '#58ff8a', 0)]))
        ctx.arc(-24, -110, 30, 0, TAU)
        ctx.fill()
    ctx.restore()


# ------------------------------------------------------------ shots

def s01(ctx, t, d):
    zoom_about(ctx, 1 + .07 * t / d, W / 2, H * .6)
    hy = 622
    desert(ctx, 'dawn', hy, sun=(1260, 652 - 22 * t / d, 24), seed=11, dunes=False)
    ctx.set_source(lin(0, hy, 0, H, [(0, '#6b5646'), (1, '#3b2f2a')]))
    ctx.rectangle(-100, hy, W + 200, H)
    ctx.fill()
    vp = (960, hy + 2)
    poly(ctx, [(vp[0] - 4, vp[1]), (vp[0] + 4, vp[1]), (1700, H + 40), (220, H + 40)])
    ctx.set_source(lin(0, hy, 0, H, [(0, '#5d5056'), (1, '#24232a')]))
    ctx.fill()
    for i in range(14):
        z0, z1 = (i / 14) ** 2.2, ((i + .45) / 14) ** 2.2
        y0, y1 = vp[1] + (H - vp[1]) * z0, vp[1] + (H - vp[1]) * z1
        w0, w1 = 1 + 14 * z0, 1 + 14 * z1
        poly(ctx, [(960 - w0, y0), (960 + w0, y0), (960 + w1, y1), (960 - w1, y1)])
        col(ctx, '#d9c9a4', .55)
        ctx.fill()
    for sx in (-1, 1):
        line(ctx, [(vp[0] + sx * 5, vp[1]), (960 + sx * 700, H + 40)], 2, '#cbbfa6', .35)
    fj_side(ctx, 1110, 640, 38, facing=-1, sil=.55, dusty=0)
    ctx.set_source(rad(1090, 632, 0, 18, [(0, '#ffe7b0', .9), (1, '#ffe7b0', 0)]))
    ctx.arc(1090, 632, 18, 0, TAU)
    ctx.fill()
    dust(ctx, t, 70, 3, '#ffd9a8', .35, (0, 560, W, 300), vx=26, vy=-2, size=(1, 2.4))
    vignette(ctx, .55)


def building(ctx, x0, x1, top, base, light=1):
    ctx.set_source(lin(x0, 0, x1, 0, [(0, '#d8bb93'), (1, '#b89a74')]))
    ctx.rectangle(x0, top, x1 - x0, base - top)
    ctx.fill()
    col(ctx, '#c6a983')
    ctx.rectangle(x0 - 10, top - 18, x1 - x0 + 20, 22)
    ctx.fill()
    col(ctx, '#2a2420')
    ctx.rectangle(x0 + (x1 - x0) * .42, base - 230, 110, 230)
    ctx.fill()
    col(ctx, '#3a332d')
    ctx.rectangle(x0 + 70, top + 90, 150, 100)
    ctx.rectangle(x1 - 220, top + 90, 150, 100)
    ctx.fill()
    col(ctx, '#ffffff', .07 * light)
    ctx.rectangle(x0, top, (x1 - x0) * .5, base - top)
    ctx.fill()


def s02(ctx, t, d):
    handheld(ctx, t, 5, 2)
    hy = 690
    desert(ctx, 'morning', hy, sun=(160, 380, 34), seed=21, dunes=False)
    ctx.set_source(lin(0, hy, 0, H, [(0, '#cfae80'), (1, '#a88a63')]))
    ctx.rectangle(-100, hy, W + 200, H)
    ctx.fill()
    rs = random.Random(5)
    for _ in range(400):
        col(ctx, rs.choice(['#8f7556', '#e7cfa6', '#b69771']), .5)
        ctx.arc(rs.uniform(0, W), rs.uniform(hy + 20, H), rs.uniform(1, 3), 0, TAU)
        ctx.fill()
    building(ctx, 230, 1080, 360, 770)
    poly(ctx, [(1080, 770), (1380, 770), (1080, 520)])
    col(ctx, '#6b5236', .25)
    ctx.fill()
    col(ctx, '#000000', .18)
    poly(ctx, [(1180, 860), (1820, 860), (1980, 940), (1300, 960)])
    ctx.fill()
    fj_side(ctx, 1420, 860, 560, facing=-1, sway=3 * math.sin(t * 1.3), shadow=(.4, 1.5))
    for i in range(5):
        a = .05 + .03 * math.sin(t * .8 + i)
        poly(ctx, [(120 + i * 140, -50), (220 + i * 140, -50), (1100 + i * 200, H + 50), (900 + i * 200, H + 50)])
        col(ctx, '#fff4d6', a)
        ctx.fill()
    dust(ctx, t, 90, 7, '#fff6df', .5, (0, 0, W, H), vx=10, vy=-5)
    vignette(ctx, .4)


def s03(ctx, t, d):
    dx = lerp(70, -70, ease(t / d))
    ctx.translate(dx, 0)
    ctx.set_source(lin(0, 0, W, 0, [(0, '#8d7358'), (.5, '#b89a77'), (1, '#7c6450')]))
    ctx.rectangle(-200, -100, W + 400, H + 200)
    ctx.fill()
    fabric(ctx, 3.2, .18)
    lx = 300 + 80 * t / d
    poly(ctx, [(lx, -50), (lx + 520, -50), (lx + 1100, H + 50), (lx + 560, H + 50)])
    col(ctx, '#ffe9c6', .22)
    ctx.fill()
    ctx.save()
    ctx.translate(26, 34)
    col(ctx, '#2a1d12', .0)
    vest_flat(ctx, 960, 640, 640, 'front', tex=False)
    ctx.restore()
    ctx.save()
    ctx.push_group()
    vest_flat(ctx, 960 + 26, 640 + 30, 640, 'front', tex=False)
    ctx.set_operator(cairo.OPERATOR_ATOP)
    col(ctx, '#2a1d12', .9)
    ctx.paint()
    ctx.pop_group_to_source()
    ctx.paint_with_alpha(.35)
    ctx.restore()
    line(ctx, [(960, 200), (960, 228)], 10, '#5d5d61')
    ctx.arc(960, 232, 16, 0, math.pi)
    ctx.set_line_width(7)
    col(ctx, '#77777c')
    ctx.stroke()
    vest_flat(ctx, 960, 640, 640, 'front')
    poly(ctx, [(lx, -50), (lx + 520, -50), (lx + 1100, H + 50), (lx + 560, H + 50)])
    col(ctx, '#ffe9c6', .1)
    ctx.fill()
    dust(ctx, t, 60, 9, '#fff4dc', .6, (lx, 0, 900, H), vx=6, vy=-3)
    vignette(ctx, .55)


def s04(ctx, t, d):
    p = ease(t / d * 1.1)
    u = lerp(36, -18, p)
    scale = 26
    vy = 540 - u * scale

    def draw(c):
        col(c, '#1a1c30')
        c.paint()
        vest_flat(c, 960, vy, 100 * scale, 'back')
        c.set_source(lin(W, 0, 0, H, [(0, '#ffd59a', .25), (.6, '#ffd59a', 0)]))
        c.paint()
    r = 12 * (1 - ease(t / (d * .7)))
    s = offscreen(draw, r)
    paint_surface(ctx, s)
    dust(ctx, t, 40, 4, '#fff1d6', .5, vx=8, vy=-2, size=(1, 2.5))
    vignette(ctx, .6)


def interior_bg(ctx, door=True, warm='#ffe1b0'):
    ctx.set_source(lin(0, 0, W, 0, [(0, '#2b2622'), (.5, '#3c342e'), (1, '#26211e')]))
    ctx.paint()
    if door:
        s = cached('doorway', lambda: offscreen(lambda c: (desert(c, 'morning', 640, seed=31),
                                                           person(c, 700, 900, 300, 'front'),
                                                           person(c, 1150, 880, 280, 'side', facing=-1)), 14))
        ctx.save()
        ctx.rectangle(640, 0, 640, H)
        ctx.clip()
        paint_surface(ctx, s)
        col(ctx, '#ffffff', .18)
        ctx.paint()
        ctx.restore()
        grade_light(ctx, 960, 500, 900, warm, .35)


def s05(ctx, t, d):
    handheld(ctx, t, 6, 5)
    interior_bg(ctx)
    e = ease((t - .3) / 2.2)
    up = lerp(150, 10, e)
    fo = lerp(40, 4, e)
    person(ctx, 960, 1620, 1500, 'back', arms=[(up, fo), (up, fo)], vest_dy=lerp(-30, 0, e),
           light=(0, -1, '#ffe2b8', .25))
    vignette(ctx, .55)


def s06(ctx, t, d):
    handheld(ctx, t, 4, 6, zoom=1.05)
    e = ease(t / d * 1.15)
    zy = lerp(46, -44, e)
    k = 34
    cy = clamp(540 - zy * k, -900, 2000)
    col(ctx, '#151833')
    ctx.paint()
    vest_flat(ctx, 960, cy, 100 * k, 'front', zip_y=zy, gap=lerp(9, 0, ease((t / d) * 1.2)))
    sy = cy + zy * k
    hand(ctx, 960 + 36, sy + 120, 3.2, angle=-math.pi / 2 - .3, kind='skin', grip=.7, tone=SKIN, flip=True)
    grade_light(ctx, 1500, 200, 1200, '#ffd9a0', .18)
    vignette(ctx, .55)


def s07(ctx, t, d):
    handheld(ctx, t, 3, 7, zoom=1.04)
    k = 26
    col(ctx, '#151833')
    ctx.paint()
    vx = 960 - 6 * k
    vy = 540 + 34 * k
    vest_flat(ctx, vx, vy, 100 * k, 'front', badge=False)
    bx, by = vx + 20 * k, vy - 34 * k
    e = ease((t - .3) / 1.4)
    draw_badge(ctx, bx + (1 - e) * 60, by - (1 - e) * 40, 16 * k * lerp(1.15, 1, e), alpha=lerp(.0, 1, ease(t / .5)))
    push = ease((t - 1.5) / .4) * (1 - ease((t - 2.4) / 1.2))
    hx = bx + 120 + 600 * (1 - ease((t - .2) / 1.3)) + 700 * ease((t - 2.4) / 1.5)
    hand(ctx, hx + 260, by + 30 - 20 * push, 3.4, angle=math.pi + .15, kind='skin', grip=.25, tone=SKIN2,
         sleeve=SHIRT)
    grade_light(ctx, 400, 100, 1300, '#ffd9a0', .2)
    vignette(ctx, .55)


def s08(ctx, t, d):
    handheld(ctx, t, 5, 8)
    ctx.set_source(lin(0, 0, 0, H, [(0, '#4a4038'), (1, '#2f2924')]))
    ctx.paint()
    fabric(ctx, 4, .15)
    for sy in (300, 760):
        col(ctx, '#77787d')
        ctx.rectangle(-50, sy, W + 100, 16)
        ctx.fill()
        col(ctx, '#000000', .3)
        ctx.rectangle(-50, sy + 16, W + 100, 30)
        ctx.fill()
    for i, c in enumerate(('#e07a2a', '#d9d6cf', '#3c6e9e')):
        rrect(ctx, 260 + i * 170, 140, 120, 160, 20)
        col(ctx, c, .9)
        ctx.fill()
    for i in range(4):
        rrect(ctx, 1350 + i * 90, 640, 60, 120, 10)
        col(ctx, '#9cc6df', .7)
        ctx.fill()
    e = ease((t - 1.3) / 2.6)
    bx, by = lerp(960, 1500, e), lerp(760 - 230, -400, e)
    rot = lerp(0, .25, e) + .05 * math.sin(t * 3) * e
    reach = ease(t / 1.2)
    ax0 = (1900, -200)
    hx, hy_ = lerp(1700, bx + 10, reach), lerp(-300, by - 300, reach)
    line(ctx, [ax0, (hx, hy_)], 120, SKIN)
    line(ctx, [ax0, (lerp(ax0[0], hx, .45), lerp(ax0[1], hy_, .45))], 150, SHIRT)
    first_aid_bag(ctx, bx, by, 460, rot)
    col(ctx, SKIN)
    ctx.arc(hx, hy_, 55, 0, TAU)
    ctx.fill()
    grade_light(ctx, 300, 0, 1400, '#ffd9a0', .2)
    vignette(ctx, .5)


def s09(ctx, t, d):
    zoom_about(ctx, 1 + .06 * t / d)
    ctx.set_source(lin(0, 0, W, H, [(0, '#5b3f2b'), (1, '#3b2919')]))
    ctx.paint()
    for i in range(30):
        line(ctx, [(-50, i * 40 + 10 * math.sin(i)), (W + 50, i * 40 + 14 * math.sin(i * 1.7))], 2, '#2a1b10', .25)
    ctx.save()
    ctx.translate(560, 520)
    ctx.rotate(-.12)
    col(ctx, '#e3d6b6')
    ctx.rectangle(-460, -330, 920, 660)
    ctx.fill()
    for j in range(9):
        spline(ctx, [(-440 + 20 * j, -300 + 70 * j), (-100, -260 + 60 * j + 30 * math.sin(j)),
                     (200, -280 + 70 * j), (440, -240 + 60 * j)], closed=False)
        ctx.set_line_width(2)
        col(ctx, '#a68b5b', .7)
        ctx.stroke()
    spline(ctx, [(-380, 250), (-150, 80), (60, 120), (300, -160)], closed=False)
    ctx.set_dash([18, 12])
    ctx.set_line_width(6)
    col(ctx, '#b8333a', .85)
    ctx.stroke()
    ctx.set_dash([])
    ctx.restore()
    rrect(ctx, 1380, 180, 380, 520, 14)
    col(ctx, '#1c2433')
    ctx.fill()
    line(ctx, [(1420, 760), (1750, 640)], 12, '#d9a33a')
    lift = ease((t - 2.8) / 1.6)
    reach = ease((t - 1.1) / 1.4)
    rx, ry = 1180, 620 - 40 * lift
    col(ctx, '#000000', .35 + .1 * lift)
    rrect(ctx, rx - 110 + 40 * lift, ry - 230 + 50 * lift, 240, 520, 40)
    ctx.fill()
    radio(ctx, rx, ry, 230 * (1 + .06 * lift), t, rot=-.05)
    hand(ctx, lerp(1300, rx + 30, reach), lerp(1500, ry + 360, reach), 3.6, angle=-math.pi / 2 - .1,
         kind='glove', grip=.4 + .4 * lift, sleeve=SHIRT, cuff=SILVER)
    grade_light(ctx, 1500, 0, 1300, '#ffd9a0', .18)
    vignette(ctx, .5)


def s10(ctx, t, d):
    off = lerp(H, 0, ease((t - .8) / 2.8))
    handheld(ctx, t, 4, 10)
    interior_bg(ctx, door=True)
    ctx.translate(0, -off)
    bust(ctx, 860, 470, 4.2, facing=1, tone=SKIN, blink=1.0 if 4.2 < t < 4.35 else 0.0,
         light=(60, -20, '#ffd9a8', .25))
    hand(ctx, 700, H + 640, 3.3, angle=-.25, kind='glove', grip=.6, sleeve=SHIRT, cuff=SILVER)
    pull = 30 * math.sin(min(t, 2.5) * 6)
    hand(ctx, 1240 + pull, H + 520, 3.0, angle=math.pi + .35, kind='glove', grip=.85, flip=True, sleeve=SHIRT)
    vignette(ctx, .55)


def s11(ctx, t, d):
    handheld(ctx, t, 8, 11)
    desert(ctx, 'morning', 600, sun=(1250, 420, 40), seed=41, dunes=False)
    ctx.set_source(lin(0, 600, 0, H, [(0, '#cfae80'), (1, '#b0905f')]))
    ctx.rectangle(-100, 600, W + 200, H)
    ctx.fill()
    fj_side(ctx, 1230, 760, 640, facing=-1, door=ease((t - 3.5) / 1), sway=2 * math.sin(t))
    for i, (x0, x1, y0, carry) in enumerate(((560, 1020, 1060, None), (860, 1150, 1100, 'bag'),
                                             (300, 860, 1150, None))):
        e = t / d
        x = lerp(x0, x1, e)
        sc = lerp(1.0, .78, e)
        y = lerp(y0, 860 + i * 18, e)
        h = 620 * sc
        col(ctx, '#3a2a1c', .25)
        poly(ctx, [(x - 30 * sc, y), (x + 30 * sc, y), (x + 60, y + 260), (x - 60, y + 260)])
        ctx.fill()
        person(ctx, x, y, h, 'back', phase=t * 7 + i * 1.7, carry=carry, tone=(SKIN, SKIN2, SKIN3)[i])
    dust(ctx, t, 50, 12, '#fff3d6', .45)
    vignette(ctx, .45)


def s12(ctx, t, d):
    handheld(ctx, t, 4, 12)
    ctx.save()
    ctx.rectangle(1240, 0, 700, 760)
    ctx.clip()
    ctx.translate(-((t * 900) % 3000), 0)
    for k in range(3):
        ctx.save()
        ctx.translate(k * 3000, 0)
        desert(ctx, 'morning', 420, xoff=0, seed=51 + k, mount=True)
        ctx.restore()
    ctx.restore()
    col(ctx, '#ffffff', .12)
    ctx.rectangle(1240, 0, 700, 760)
    ctx.fill()
    ctx.set_source(lin(0, 0, 1300, 0, [(0, '#121317'), (1, '#2a2c33')]))
    ctx.rectangle(-100, -100, 1340, H + 200)
    ctx.rectangle(1240, 760, 800, 400)
    ctx.fill()
    line(ctx, [(1240, 0), (1240, 770), (1960, 770)], 40, '#1a1b20')
    vest_flat(ctx, 700, 980, 1500, 'front')
    rrect(ctx, 30, 120, 230, 1100, 100)
    col(ctx, SHIRT)
    ctx.fill()
    rrect(ctx, 1140, 120, 230, 1100, 100)
    col(ctx, SHIRT)
    ctx.fill()
    e = ease((t - .4) / 2.0)
    x0, y0 = 330, -60
    x1, y1 = lerp(330, 1120, e), lerp(-60, 1010, e)
    line(ctx, [(x0, y0), (x1, y1)], 95, '#26272c')
    line(ctx, [(x0 + 30, y0), (x1 + 30, y1)], 4, '#3c3d44')
    col(ctx, '#9da2aa')
    rrect(ctx, x1 - 40, y1 - 30, 80, 60, 8)
    ctx.fill()
    if t > 2.4:
        col(ctx, '#ffffff', .6 * max(0, 1 - (t - 2.4) * 3))
        ctx.arc(1120, 1010, 70, 0, TAU)
        ctx.fill()
    hand(ctx, x1 + 40, y1 + 40, 2.8, angle=.9, kind='skin', grip=.7, tone=SKIN, sleeve=SHIRT)
    radio(ctx, 260, 1000, 160, t, rot=1.2)
    grade_light(ctx, 1500, 300, 1100, '#fff1d0', .3)
    vignette(ctx, .5)


def s13(ctx, t, d):
    handheld(ctx, t, 4, 13)
    desert(ctx, 'morning', 640, sun=(300, 300, 38), seed=61, dunes=False)
    ctx.set_source(lin(0, 640, 0, H, [(0, '#cfae80'), (1, '#a88a63')]))
    ctx.rectangle(-100, 640, W + 200, H)
    ctx.fill()
    building(ctx, -200, 420, 330, 720)
    e1 = clamp((t - .6) / (d - .6)) ** 2
    x1 = lerp(820, 2900, e1)
    e2 = clamp((t - 1.6) / (d - 1.6)) ** 1.6
    x2 = lerp(-700, 1500, e2)

    def em1(tau):
        e_ = clamp((tau - .6) / (d - .6)) ** 2
        return None if tau < .7 else (lerp(820, 2900, e_) - 300, 840)

    def em2(tau):
        e_ = clamp((tau - 1.6) / (d - 1.6)) ** 1.6
        return None if tau < 1.7 else (lerp(-700, 1500, e_) - 280, 900)
    puffs(ctx, t, em1, 14, 2.6, 1, alpha=.5, grow=110, drift=(-20, -30), r0=20)
    fj_side(ctx, x1, 860, 640, facing=1, rot=e1 * 30, sway=6 * math.sin(t * 2))
    puffs(ctx, t, em2, 14, 2.6, 2, alpha=.5, grow=110, drift=(-20, -30), r0=20)
    fj_side(ctx, x2, 930, 600, facing=1, rot=e2 * 30, sway=5 * math.sin(t * 2 + 1))
    vignette(ctx, .45)


def road_view(ctx, t, hy, speed=1.0, tod='morning', seed=71):
    desert(ctx, tod, hy, xoff=t * 40, sun=(1400, hy - 260, 34), seed=seed, dunes=False)
    p = TOD[tod]
    ctx.set_source(lin(0, hy, 0, H, [(0, p['mid']), (1, p['ground'])]))
    ctx.rectangle(-100, hy, W + 200, H)
    ctx.fill()
    for side_ in (-1, 1):
        ctx.save()
        ctx.translate(960, hy)
        ctx.scale(side_, 1)
        ridge(ctx, 60, 50, seed + 5 + side_, xoff=t * 300 * speed, x0=260, x1=1300, bottom=420)
        col(ctx, mix(p['near'], '#000000', .08))
        ctx.fill()
        ctx.restore()
    poly(ctx, [(956, hy), (964, hy), (1800, H + 40), (120, H + 40)])
    ctx.set_source(lin(0, hy, 0, H, [(0, '#7a706c'), (1, '#3a3638')]))
    ctx.fill()
    ph = (t * speed * 1.6) % 1
    for i in range(14):
        z0, z1 = ((i + ph) / 14) ** 2.4, ((i + ph + .45) / 14) ** 2.4
        y0, y1 = hy + (H - hy) * z0, hy + (H - hy) * z1
        w0, w1 = 1 + 18 * z0, 1 + 18 * z1
        poly(ctx, [(960 - w0, y0), (960 + w0, y0), (960 + w1, y1), (960 - w1, y1)])
        col(ctx, '#efe4c8', .8)
        ctx.fill()


def s14(ctx, t, d):
    ctx.translate(2 * math.sin(t * 17), 2 * math.sin(t * 13))
    road_view(ctx, t, 470, 1.0)
    for i in range(3):
        x = ((t * 600 + i * 900) % 3200) - 800
        poly(ctx, [(x, -50), (x + 140, -50), (x - 400, H), (x - 540, H)])
        col(ctx, '#ffffff', .06)
        ctx.fill()
    col(ctx, '#121317')
    spline(ctx, [(-100, 700), (500, 640), (960, 630), (1420, 640), (2020, 700), (2020, 1200), (-100, 1200)])
    ctx.fill()
    poly(ctx, [(-100, -100), (2020, -100), (2020, 70), (-100, 90)])
    ctx.fill()
    poly(ctx, [(-100, -100), (150, -100), (-20, 760), (-100, 760)])
    poly(ctx, [(2020, -100), (1780, -100), (1940, 760), (2020, 760)])
    ctx.fill()
    ctx.save()
    ctx.arc(520, 1150, 380, math.pi * 1.05, math.pi * 1.95)
    ctx.set_line_width(46)
    col(ctx, '#222328')
    ctx.stroke()
    ctx.restore()
    hand(ctx, 230, 860, 2.4, angle=-.9, kind='skin', grip=.9, tone=SKIN, sleeve=SHIRT)
    hand(ctx, 800, 860, 2.4, angle=-2.2, kind='skin', grip=.9, tone=SKIN, flip=True, sleeve=SHIRT)
    person(ctx, 330, 1760, 1500, 'back')
    radio(ctx, 1600, 980, 120, t, rot=-.3)
    hand(ctx, 1780, 1060, 2.2, angle=-2.6, kind='glove', grip=.8, flip=True, sleeve=SHIRT)
    vignette(ctx, .5)


def s15(ctx, t, d):
    handheld(ctx, t, 7, 15)
    road_view(ctx, t * .6, 560, .8, 'noon', seed=81)
    for i in range(6):
        y = 560 + i * 6
        line(ctx, [(0, y + 2 * math.sin(t * 5 + i)), (W, y + 2 * math.sin(t * 4 + i * 2))], 3, '#ffffff', .05)
    fx, fy = 1000 + 8 * math.sin(t * .7), 700

    def e1(tau):
        return (1000 + 8 * math.sin(tau * .7), 700)

    def e2(tau):
        return (930 + 20 * math.sin(tau * .5), 900)
    puffs(ctx, t, lambda tau: (e1(tau)[0], e1(tau)[1] - 10), 10, 2.5, 3, alpha=.35, grow=120, drift=(0, 60), r0=20)
    fj_rear(ctx, fx, fy, 150, sway=4 * math.sin(t * 2))
    puffs(ctx, t, lambda tau: (e2(tau)[0], e2(tau)[1] - 10), 10, 2, 4, alpha=.4, grow=200, drift=(0, 160), r0=30)
    fj_rear(ctx, 930 + 20 * math.sin(t * .5), 900, 340, sway=6 * math.sin(t * 2.2))
    vignette(ctx, .45)


def s16(ctx, t, d):
    ctx.translate(W / 2, H / 2)
    ctx.rotate(.35 + .05 * t / d)
    ctx.scale(1.05 + .05 * t / d, 1.05 + .05 * t / d)
    ctx.translate(-W / 2 - 60 * t, -H / 2 - 25 * t)
    col(ctx, '#d7ad74')
    ctx.rectangle(-1500, -1500, W + 3000, H + 3000)
    ctx.fill()
    for i in range(-14, 30):
        base = i * 110
        pts = [(x, base + 34 * math.sin(x * .004 + i) + 14 * math.sin(x * .011 + 2 * i)) for x in range(-1500, 3500, 40)]
        ctx.move_to(*pts[0])
        for p in pts[1:]:
            ctx.line_to(*p)
        for p in reversed(pts):
            ctx.line_to(p[0], p[1] + 46 + 10 * math.sin(p[0] * .007 + i))
        ctx.close_path()
        ctx.set_source(lin(0, base, 0, base + 60, [(0, '#8c623d', .55), (1, '#8c623d', 0)]))
        ctx.fill()
        ctx.move_to(*pts[0])
        for p in pts[1:]:
            ctx.line_to(*p)
        ctx.set_line_width(3)
        col(ctx, '#f6dcae', .6)
        ctx.stroke()

    def path(tau):
        return (300 + 140 * tau, 500 + 50 * math.sin(tau * .5) + 18 * tau)
    for j, lag in enumerate((0, 1.3)):
        for k in range(60):
            tau = t - lag - k * .05
            if tau < -3:
                break
            x, y = path(tau)
            col(ctx, '#f1d5a5', .35 * (1 - k / 60))
            ctx.arc(x - 6, y, 6 + k * .6, 0, TAU)
            ctx.fill()
        x, y = path(t - lag)
        x2, y2 = path(t - lag + .1)
        ang = math.atan2(y2 - y, x2 - x)
        ctx.save()
        ctx.translate(x, y)
        ctx.rotate(ang)
        col(ctx, '#000000', .35)
        rrect(ctx, -22 + 10, -10 + 14, 44, 22, 4)
        ctx.fill()
        col(ctx, CAR)
        rrect(ctx, -22, -10, 44, 22, 4)
        ctx.fill()
        col(ctx, '#2a3038')
        rrect(ctx, -2, -8, 12, 18, 2)
        ctx.fill()
        ctx.restore()


def s17(ctx, t, d):
    ctx.translate(2.5 * math.sin(t * 23), 2 * math.sin(t * 19))
    col(ctx, '#1d1e23')
    ctx.paint()
    for i in range(-2, 30):
        line(ctx, [(i * 70 - 300, -50), (i * 70 + 200, H + 50)], 14, '#16171b', .9)
    rs = random.Random(17)
    for _ in range(500):
        col(ctx, rs.choice(['#c9a273', '#e1c196', '#a88356']), .7)
        ctx.arc(rs.uniform(0, W), rs.uniform(300, H), rs.uniform(1, 3.2), 0, TAU)
        ctx.fill()
    for lx_, ang in ((620, .1), (1300, -.12)):
        ctx.save()
        ctx.translate(lx_, -100)
        ctx.rotate(ang)
        rrect(ctx, -110, -200, 220, 1000, 40)
        ctx.set_source(lin(-110, 0, 110, 0, [(0, '#1e2246'), (.5, '#2e3466'), (1, '#1a1d3c')]))
        ctx.fill()
        for by in (520, 610):
            ctx.set_source(lin(0, by, 0, by + 46, [(0, '#aeb3ba'), (.5, '#f1f2f4'), (1, '#aeb3ba')]))
            ctx.rectangle(-112, by, 224, 46)
            ctx.fill()
        rrect(ctx, -130, 760, 260, 330, 90)
        ctx.set_source(lin(0, 760, 0, 1090, [(0, '#3a3a40'), (1, '#18181c')]))
        ctx.fill()
        for k in range(5):
            line(ctx, [(-50, 800 + k * 34), (50, 800 + k * 34)], 6, '#6b6b70')
        col(ctx, '#c9a273', .5)
        ctx.arc(0, 1060, 120, 0, math.pi)
        ctx.fill()
        ctx.restore()
    first_aid_bag(ctx, 960, 760 + 4 * math.sin(t * 20), 320, .05)
    x = ((t * 260) % 2600) - 600
    poly(ctx, [(x, -50), (x + 260, -50), (x + 760, H + 50), (x + 500, H + 50)])
    col(ctx, '#ffe7b8', .12)
    ctx.fill()
    vignette(ctx, .6)


def s18(ctx, t, d):
    handheld(ctx, t, 5, 18)
    col(ctx, '#17181d')
    ctx.paint()
    ctx.save()
    rrect(ctx, 700, 160, 520, 380, 40)
    ctx.clip()
    ctx.translate(-((t * 700) % 2200), -120)
    for k in range(3):
        ctx.save()
        ctx.translate(k * 2200, 0)
        desert(ctx, 'noon', 520, seed=91 + k)
        ctx.restore()
    ctx.restore()
    nod = 9 * math.sin(clamp((t - 3.4) / 1.0) * math.pi)
    bust(ctx, 470, 610, 4.6, facing=1, tone=SKIN2, sweat=.6, light=(80, 0, '#fff2d0', .25))
    bust(ctx, 1450, 600, 4.6, facing=-1, tone=SKIN, nod=nod, sweat=.5, light=(80, 0, '#fff2d0', .25))
    x = ((t * 300) % 2800) - 600
    poly(ctx, [(x, -50), (x + 300, -50), (x + 800, H + 50), (x + 500, H + 50)])
    col(ctx, '#fff1d0', .1)
    ctx.fill()
    vignette(ctx, .55)


def s19(ctx, t, d):
    handheld(ctx, t, 5, 19)
    hy = 430
    desert(ctx, 'noon', hy, sun=(1500, 120, 40), seed=101, near_y=hy + 60)
    vx = lerp(900, 1000, t / d)
    vs = lerp(260, 120, ease((t - 2.5) / 5))
    if t > 2.2:
        puffs(ctx, t, lambda tau: (lerp(900, 1000, tau / d), hy + 150 - 40 * ease((tau - 2.5) / 5)) if tau > 2.2 else None,
              10, 2, 5, alpha=.4, grow=80, drift=(0, 20), r0=15)
        fj_rear(ctx, vx, hy + 160 - 40 * ease((t - 2.5) / 5), vs, sway=4 * math.sin(t * 2))
    for i in range(4):
        person(ctx, 1400 + i * 24, hy + 30, 38, 'front', tone=SKIN, sil=.4)
    ctx.set_source(lin(0, hy + 300, 0, H, [(0, '#d9b07a', 0), (1, '#c99d66', 1)]))
    ctx.rectangle(-100, hy + 300, W + 200, H)
    ctx.fill()
    rs = random.Random(19)
    for _ in range(300):
        y = rs.uniform(hy + 380, H)
        col(ctx, rs.choice(['#a8845a', '#f0d7ac']), .6)
        ctx.arc(rs.uniform(0, W), y, rs.uniform(1, 4) * (y - hy) / 600, 0, TAU)
        ctx.fill()
    wx = lerp(2400, -700, ease(t / 3.0))
    if t < 3.2:
        rs = random.Random(9)
        for k in range(160):
            age = (t * 3 + rs.random()) % 1
            x = wx + 250 + age * rs.uniform(200, 700)
            y = 900 - age * rs.uniform(100, 400) + age * age * 500
            col(ctx, '#e3c18f', .7 * (1 - age))
            ctx.arc(x, y, rs.uniform(3, 9), 0, TAU)
            ctx.fill()
        col(ctx, CAR)
        ctx.rectangle(wx - 700, -100, 1400, 620)
        ctx.fill()
        col(ctx, '#2e2e33')
        ctx.arc(wx, 820, 400, math.pi, TAU)
        ctx.fill()
        wheel(ctx, wx, 820, 340, -t * 8)
        rs = random.Random(3)
        for k in range(16):
            a = -t * 8 + k * TAU / 16
            ctx.save()
            ctx.translate(wx + math.cos(a) * 320, 820 + math.sin(a) * 320)
            ctx.rotate(a)
            col(ctx, '#0e0e10')
            ctx.rectangle(-20, -40, 40, 80)
            ctx.fill()
            ctx.restore()
    vignette(ctx, .45)


def _walker(t, t0, p0, p1, dur):
    e = ease((t - t0) / dur)
    moving = 0 < (t - t0) < dur
    return lerp(p0[0], p1[0], e), lerp(p0[1], p1[1], e), moving


def s20(ctx, t, d):
    handheld(ctx, t, 6, 20)
    desert(ctx, 'noon', 560, sun=(1700, 140, 36), seed=111, near_y=700)
    pickup_side(ctx, 1500, 790, 420, tilt=-7, buried=1)
    e = ease(t / 2.4)
    for j, (x0, x1, y_, L) in enumerate(((-1100, 940, 830, 380), (-600, 430, 900, 450))):
        x = lerp(x0, x1, e)
        puffs(ctx, t, lambda tau, x0=x0, x1=x1, y_=y_: (lerp(x0, x1, ease(tau / 2.4)) - 180, y_ - 20)
              if tau < 2.6 else None, 12, 3, 20 + j, alpha=.45, grow=100, drift=(30, -25), r0=20)
        fj_side(ctx, x, y_, L, facing=1, rot=e * 18, door=ease((t - 2.7) / .6), sway=4 * math.sin(t * 2 + j))
    starts = [(470, 905), (520, 900), (960, 835), (1000, 838), (940, 832)]
    ends = [(1320, 820), (1180, 900), (1560, 860), (1440, 930), (1700, 830)]
    carries = ['bag', None, 'case', None, 'bag']
    for i in range(5):
        t0 = 2.9 + i * .25
        if t < t0:
            continue
        x, y, moving = _walker(t, t0, starts[i], ends[i], 3.4)
        person(ctx, x, y, 240, 'side', facing=1, phase=(t - t0) * 9 if moving else None,
               carry=carries[i], tone=(SKIN, SKIN2, SKIN3, SKIN, SKIN2)[i])
    dust(ctx, t, 60, 20, '#fff1d6', .4)
    vignette(ctx, .45)


def s21(ctx, t, d):
    handheld(ctx, t, 6, 21)
    s = cached('s21bg', lambda: offscreen(lambda c: (desert(c, 'noon', 520, sun=(300, 120, 36), seed=121, near_y=700),
                                                      pickup_side(c, 1300, 760, 520, tilt=-7, buried=1)), 10))
    paint_surface(ctx, s)
    for i, (x0, x1, f) in enumerate(((900, 260, -1), (1000, 1680, 1))):
        x, y, moving = _walker(t, .7 + i * .2, (x0, 960), (x1, 930), 4.2)
        person(ctx, x, y, 430, 'side', facing=f, phase=t * 8 if moving else None, carry='bag' if i else None,
               tone=(SKIN2, SKIN3)[i])
    up = lerp(10, 82, ease((t - .3) / .8))
    person(ctx, 760, 1500, 1300, 'back', arms=[(8, 4), (up, up - 6)], tone=SKIN, light=(1, -1, '#fff3d8', .2))
    vignette(ctx, .45)


def s22(ctx, t, d):
    ctx.translate(3 * math.sin(t * 7), 4 * math.sin(t * 9))
    desert(ctx, 'noon', 380, xoff=t * 300, sun=(300, 80, 30), seed=131, near_y=520)
    ctx.set_source(lin(0, 700, 0, H, [(0, '#dcb27a'), (1, '#c79a62')]))
    ctx.rectangle(-100, 700, W + 200, H)
    ctx.fill()
    rs = random.Random(22)
    for _ in range(260):
        x = (rs.uniform(0, W + 400) - t * 700) % (W + 400) - 200
        y = rs.uniform(720, H)
        col(ctx, rs.choice(['#a8845a', '#f0d7ac']), .6)
        ctx.arc(x, y, rs.uniform(1.5, 5) * (y - 600) / 400, 0, TAU)
        ctx.fill()
    hands = []
    for i, (x, h, ph0) in enumerate(((380, 1500, 0), (1000, 1550, 2), (1560, 1450, 4))):
        ph = t * 8.5 + ph0
        for k in range(-1, 3):
            step = math.floor(ph / math.pi) - k
            ts = (step * math.pi - ph0) / 8.5
            age = t - ts
            if 0 <= age < 1.2:
                px = x + 60 - age * 700
                col(ctx, '#e8c995', .55 * (1 - age / 1.2))
                ctx.arc(px, 1000 - age * 40, 20 + age * 90, 0, TAU)
                ctx.fill()
        o = person(ctx, x, 1010, h, 'side', facing=1, phase=ph, walk=1.1, gloves=True,
                   arms=[(30, 40), (20, 30)] if i < 2 else None, carry='bag' if i == 2 else None,
                   tone=(SKIN, SKIN2, SKIN3)[i])
        hands.append(o.get('hand0'))
    if hands[0] and hands[1]:
        ctx.save()
        ctx.identity_matrix()
        (a, b) = hands[0], hands[1]
        line(ctx, [(a[0] - 40, a[1]), (b[0] + 40, b[1])], 34, '#d38a2e')
        line(ctx, [(a[0] - 40, a[1] - 10), (b[0] + 40, b[1] - 10)], 6, '#f2b65c', .7)
        ctx.restore()
    vignette(ctx, .4)


def s23(ctx, t, d):
    handheld(ctx, t, 5, 23)
    desert(ctx, 'noon', 500, sun=(1500, 100, 34), seed=141, near_y=680)
    fj_side(ctx, 260, 860, 620, facing=1, sway=2 * math.sin(t))
    col(ctx, '#000000', .2)
    poly(ctx, [(0, 860), (700, 860), (900, 960), (0, 980)])
    ctx.fill()
    x, y, moving = _walker(t, .2, (760, 900), (520, 930), 4.6)
    person(ctx, x - 70, y, 360, 'side', facing=-1, phase=t * 6 if moving else None, outfit='thobe', tone=SKIN2,
           walk=.7)
    person(ctx, x + 40, y + 10, 380, 'side', facing=-1, phase=t * 6 if moving else None, tone=SKIN3, walk=.7,
           arms=[(50, 60), (6, 16)])
    pickup_side(ctx, 1950, 930, 900, tilt=-6, buried=0)
    col(ctx, TIRE)
    ctx.arc(1560, 960, 120, 0, TAU)
    ctx.fill()
    col(ctx, '#8d8f93')
    ctx.arc(1560, 960, 66, 0, TAU)
    ctx.fill()
    spline(ctx, [(1300, 1100), (1420, 1000), (1560, 1010), (1720, 990), (1800, 1100)])
    col(ctx, '#d9b07a')
    ctx.fill()
    sig = ease((t - 3.2) / .5) * (1 - ease((t - 4.6) / .6))
    person(ctx, 1230, 1100, 640, 'side', facing=1, kneel=True, lean=28,
           arms=[(80, 95), (lerp(20, 150, sig), lerp(30, 175, sig))], tone=SKIN, gloves=True,
           nod=lerp(14, -8, sig))
    vignette(ctx, .45)


def s24(ctx, t, d):
    s = cached('s24bg', lambda: offscreen(lambda c: desert(c, 'golden', 560, sun=(960, 420, 60), seed=151), 22))
    paint_surface(ctx, s)
    e = ease(t / 2.0)
    pull = ease((t - 2.4) / 2.2)
    cx, cy = 960, 600 - 70 * pull
    hand(ctx, lerp(-200, cx - 120, e), cy + 10, 3.2, angle=.05, kind='glove', grip=.2 + .7 * e, sleeve=NAVY,
         cuff=SILVER)
    hand(ctx, lerp(W + 200, cx + 120, e), cy - 10, 3.2, angle=math.pi - .05, kind='skin', grip=.2 + .7 * e,
         flip=True, tone=SKIN2, sleeve='#efede7')
    grade_light(ctx, cx, cy - 200, 700, '#fff0c8', .25 + .25 * e)
    dust(ctx, t, 60, 24, '#fff1d6', .5)
    vignette(ctx, .5)


def s25(ctx, t, d):
    handheld(ctx, t, 7, 25)
    desert(ctx, 'noon', 380, sun=(1700, 80, 34), seed=161, near_y=520)
    ctx.set_source(lin(0, 760, 0, H, [(0, '#dcb27a'), (1, '#c79a62')]))
    ctx.rectangle(-100, 760, W + 200, H)
    ctx.fill()
    pickup_side(ctx, 2300, 1100, 1500, tilt=-5)
    col(ctx, TIRE)
    ctx.arc(1420, 900, 230, 0, TAU)
    ctx.fill()
    col(ctx, '#8d8f93')
    ctx.arc(1420, 900, 130, 0, TAU)
    ctx.fill()
    dig = math.sin(t * 4.2)
    level = lerp(0, 120, t / d)
    spline(ctx, [(980, 1200), (1120, 980 + level), (1420, 1000 + level), (1700, 990 + level), (1900, 1200)])
    col(ctx, '#d9b07a')
    ctx.fill()
    rs = random.Random(25)
    for k in range(90):
        age = (t * 1.4 + rs.random()) % 1
        x = 1150 - age * rs.uniform(300, 700)
        y = 980 - age * rs.uniform(200, 500) + age * age * 700
        col(ctx, '#e3c18f', .75 * (1 - age))
        ctx.arc(x, y, rs.uniform(3, 8), 0, TAU)
        ctx.fill()
    person(ctx, 780, 1220, 1050, 'side', facing=1, kneel=True, lean=34 + 6 * dig,
           arms=[(95 + 25 * dig, 110 + 30 * dig), (75 - 25 * dig, 95 - 20 * dig)], gloves=True, tone=SKIN3,
           breath=.6 * math.sin(t * 2.4), nod=12)
    vignette(ctx, .45)


def s26(ctx, t, d):
    s = cached('s26bg', lambda: offscreen(lambda c: desert(c, 'noon', 640, sun=(1650, 160, 50), seed=171), 26))
    paint_surface(ctx, s)
    bob = 6 * math.sin(t * 2.2)
    bust(ctx, 860, 600 + bob, 5.4, facing=1, tone=SKIN, squint=.8, sweat=1.0, light=(60, -40, '#fff4d8', .3))
    w = ease((t - 1.0) / 1.5)
    away = ease((t - 2.8) / 1.2)
    hx = lerp(1700, 800, w) + 900 * away
    hy_ = lerp(1300, 380, ease((t - .6) / .8)) + 600 * away
    hand(ctx, hx, hy_, 2.9, angle=math.pi + .25, kind='glove', grip=.35, flip=True, sleeve=SHIRT)
    grade_light(ctx, 1650, 160, 1300, '#fff6dc', .45)
    vignette(ctx, .45)


def s27(ctx, t, d):
    handheld(ctx, t, 6, 27)
    desert(ctx, 'noon', 560, sun=(400, 120, 34), seed=181, near_y=720)
    fj_side(ctx, 1240, 790, 520, facing=-1, sway=2 * math.sin(t))
    col(ctx, '#000000', .2)
    poly(ctx, [(980, 790), (1500, 790), (1650, 860), (900, 870)])
    ctx.fill()
    e = ease(t / 3.0)
    x, y = lerp(640, 1050, e), lerp(1250, 900, e)
    h = lerp(820, 470, e)
    walking = t < 3.0
    down = ease((t - 3.0) / .5)
    hips = ease((t - 3.4) / .6)
    if t > 3.0:
        first_aid_bag(ctx, x + h * .14, y - 8, h * .12)
    arms = None
    if not walking:
        arms = [(lerp(8, 45, hips), lerp(4, -75, hips)), (lerp(8, 45, hips), lerp(4, -75, hips))]
    person(ctx, x, y, h, 'back', phase=t * 8 if walking else None, carry='bag' if t < 3.0 else None, arms=arms,
           tone=SKIN2, breath=1.2 * math.sin(t * 2.6) * hips, gloves=True)
    vignette(ctx, .45)


def s28(ctx, t, d):
    s = cached('s28bg', lambda: offscreen(lambda c: desert(c, 'golden', 600, sun=(900, 380, 50), seed=191), 24))
    cam = lerp(260, 1660, ease(t / d))
    ctx.save()
    ctx.scale(1.3, 1.3)
    paint_surface(ctx, s, -cam * .3 / 1.3, -H * .1)
    ctx.restore()
    ctx.translate(-cam, 0)
    n1 = 8 * math.sin(clamp((t - 1.0) / 1.0) * math.pi)
    n2 = 8 * math.sin(clamp((t - 3.4) / 1.0) * math.pi)
    bust(ctx, 1150, 600, 5.0, facing=1, tone=SKIN2, nod=n1, sweat=.8, light=(60, -10, '#ffd9a0', .35))
    bust(ctx, 2700, 610, 5.0, facing=-1, tone=SKIN3, nod=n2, sweat=.8, light=(60, -10, '#ffd9a0', .35))
    ctx.identity_matrix()
    vignette(ctx, .5)


def s29(ctx, t, d):
    def bg(c):
        desert(c, 'golden', 640, sun=(1600, 560, 60), seed=201)
        fj_side(c, 520, 780, 600, facing=1, sil=.5)
    s = cached('s29bg', lambda: offscreen(bg, 16))
    paint_surface(ctx, s)
    grade_light(ctx, 1600, 560, 1000, '#ffcf8a', .35)
    bust(ctx, 1080, 560 + 5 * math.sin(t * 1.4), 5.2, facing=1, tone=SKIN, sil=.6,
         blink=1.0 if 3.6 < t < 3.75 else 0.0)
    off = ease((t - .6) / 2.4)
    hand(ctx, 260, 1040, 3.6, angle=-.5, kind='skin', grip=.2, tone=SKIN, sleeve=SHIRT)
    hand(ctx, 260 + 260 * off + 30, 1040 - 160 * off - 20, 3.6 * (1 - .1 * off), angle=-.5 - .5 * off,
         kind='glove', grip=.2)
    vignette(ctx, .55)


def s30(ctx, t, d):
    zoom_about(ctx, 1 + .05 * t / d, W / 2, H * .6)
    desert(ctx, 'sunset', 640, sun=(1250, 640, 50), seed=211, dunes=False)
    ridge(ctx, 820, 60, 213, x0=-200, x1=W + 200)
    ctx.set_source(lin(0, 700, 0, H, [(0, '#5a3524'), (1, '#24140f')]))
    ctx.fill()
    fj_side(ctx, 360, ridge_y(820, 60, 213, 360) + 8, 440, facing=1, sil=.9)
    fj_side(ctx, 1660, ridge_y(820, 60, 213, 1660) + 8, 400, facing=-1, sil=.9)
    xs = [700, 800, 900, 1010, 1120, 1240]
    for i, x in enumerate(xs):
        y = ridge_y(820, 60, 213, x) + 4
        arms = None
        carry = None
        view = 'front' if i % 2 else 'side'
        if i == 2:
            k = ease((t - 1.2) / .8) * (1 - ease((t - 3.6) / .8))
            arms = [(8, 4), (lerp(10, 150, k), lerp(10, 200, k))]
            carry = 'bottle'
            view = 'side'
        if i == 4:
            arms = [(70, 50), (8, 4)]
        person(ctx, x, y, 250, view, facing=1 if x < 1000 else -1, sil=.92, arms=arms, carry=carry)
    grade_light(ctx, 1250, 640, 1100, '#ffb36a', .35)
    vignette(ctx, .55)


SHOTS = {'%02d' % i: globals()['s%02d' % i] for i in range(1, 31)}


# ------------------------------------------------------------ rendering

def render_shot(args):
    sid, dur, outdir = args
    fn = SHOTS[sid]
    n = int(round(dur * FPS))
    os.makedirs(outdir, exist_ok=True)
    out = os.path.join(outdir, sid + '.mp4')
    p = subprocess.Popen(['ffmpeg', '-nostdin', '-loglevel', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'bgra',
                          '-s', '%dx%d' % (W, H), '-r', str(FPS), '-i', '-', '-c:v', 'libx264', '-preset', 'medium',
                          '-crf', '16', '-pix_fmt', 'yuv420p', out], stdin=subprocess.PIPE)
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H)
    for i in range(n):
        ctx = cairo.Context(surf)
        col(ctx, '#000000')
        ctx.paint()
        fn(ctx, i / FPS, dur)
        surf.flush()
        p.stdin.write(bytes(surf.get_data()))
    p.stdin.close()
    p.wait()
    return sid


def sheet(rows, path):
    thumbs = []
    for sid, dur in rows:
        surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H)
        ctx = cairo.Context(surf)
        col(ctx, '#000000')
        ctx.paint()
        SHOTS[sid](ctx, dur * .6, dur)
        im = Image.fromarray(surface_array(surf)[..., [2, 1, 0]].copy()).resize((480, 270))
        thumbs.append(im)
    cols = 5
    rows_n = math.ceil(len(thumbs) / cols)
    out = Image.new('RGB', (cols * 484, rows_n * 274), '#111')
    for i, im in enumerate(thumbs):
        out.paste(im, ((i % cols) * 484, (i // cols) * 274))
    out.save(path)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--only')
    ap.add_argument('--sheet')
    ap.add_argument('--out', default=os.path.join(DOC, 'shots'))
    a = ap.parse_args()
    with open(os.path.join(DOC, 'shots.csv')) as fh:
        rows = [(r['id'], float(r['duration'])) for r in csv.DictReader(fh)]
    if a.only:
        keep = set(a.only.split(','))
        rows = [r for r in rows if r[0] in keep]
    if a.sheet:
        sheet(rows, a.sheet)
        return
    with Pool(os.cpu_count()) as pool:
        for sid in pool.imap_unordered(render_shot, [(sid, dur, a.out) for sid, dur in rows]):
            print('rendered', sid, flush=True)


if __name__ == '__main__':
    main()
