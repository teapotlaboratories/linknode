"""Trace widths for JLC04161H-3313 (T26b). Stack-up from https://jlcpcb.com/impedance (fetched 2026-11-21):
outer Cu 0.035 mm, prepreg 3313 0.0994 mm Er 4.1, inner Cu 0.0152 mm, core 1.265 mm Er 4.6.
Closed-form models (EST, about +-5-10 %): Hammerstad-Jensen microstrip with thickness correction, Wadell grounded
coplanar waveguide (with the same thickness correction), and the edge-coupled microstrip approximation Zdiff = 2 Z0 (1 - 0.48 exp(-0.96 s/h)).
Solder mask lowers these by a few ohms. Confirm with JLC's impedance calculator when ordering."""
import math
H, T, ER = 0.0994, 0.035, 4.1
def dw(w, h=H, t=T, er=ER):     # Hammerstad-Jensen strip-thickness width correction
    return t / math.pi * (1 + math.log(4 * math.e / math.sqrt((t / h) ** 2 + (1 / math.pi / (w / t + 1.1)) ** 2))) * (1 + 1 / er) / 2
def ms(w, h=H, t=T, er=ER):
    u = (w + dw(w, h, t, er)) / h
    a = 1 + math.log((u ** 4 + (u / 52) ** 2) / (u ** 4 + 0.432)) / 49 + math.log(1 + (u / 18.1) ** 3) / 18.7
    b = 0.564 * ((er - 0.9) / (er + 3)) ** 0.053
    ee = (er + 1) / 2 + (er - 1) / 2 * (1 + 10 / u) ** (-a * b)
    f = 6 + (2 * math.pi - 6) * math.exp(-(30.666 / u) ** 0.7528)
    return 60 / math.sqrt(ee) * math.log(f / u + math.sqrt(1 + (2 / u) ** 2)), ee
def K(k):                       # complete elliptic integral of the first kind via AGM
    a, b = 1.0, math.sqrt(1 - k * k)
    for _ in range(30): a, b = (a + b) / 2, math.sqrt(a * b)
    return math.pi / (2 * a)
def cpwg(w, g, h=H, er=ER, t=T):
    d = dw(w, h, t, er); w, g = w + d, g - d          # same thickness correction, applied to strip and gap
    k = w / (w + 2 * g); k1 = math.tanh(math.pi * w / 4 / h) / math.tanh(math.pi * (w + 2 * g) / 4 / h)
    kp, k1p = math.sqrt(1 - k * k), math.sqrt(1 - k1 * k1)
    r, r1 = K(k) / K(kp), K(k1) / K(k1p)
    ee = (1 + er * r1 / r) / (1 + r1 / r)
    return 60 * math.pi / math.sqrt(ee) / (r + r1), ee
def solve(f, target, lo=0.03, hi=1.0):
    for _ in range(60):
        m = (lo + hi) / 2
        lo, hi = (m, hi) if f(m) > target else (lo, m)
    return (lo + hi) / 2
if __name__ == '__main__':
    w50 = solve(lambda w: ms(w)[0], 50); print('microstrip 50 ohm: w = %.3f mm (eeff %.2f)' % (w50, ms(w50)[1]))
    for g in (0.15, 0.2, 0.25):
        w = solve(lambda w: cpwg(w, g)[0], 50); print('CPWG 50 ohm, gap %.2f: w = %.3f mm' % (g, w))
    for s in (0.1, 0.127, 0.15):
        w = solve(lambda w: 2 * ms(w)[0] * (1 - 0.48 * math.exp(-0.96 * s / H)), 90); print('USB diff 90 ohm, gap %.3f: w = %.3f mm' % (s, w))
