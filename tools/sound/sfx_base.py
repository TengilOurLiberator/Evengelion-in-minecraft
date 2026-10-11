"""sfx_base.py - effects of the fortress: gate, rail wagon, lifts, doors, lights, impacts from above, the cage,
the plug.  Rooms are synthetic impulse responses (dsp.SPACES)."""
from dsp import *
from blocks import *
from reg import sound
from amb import _rail_clack


def _w(n, t0, sig, y, g=1.0):
    place(y, sig, t0, g)


@sound("sfx.gate_close", peak=-3.0, atten=64, note="huge blast door: drive motor spooling up, heavy slide with rail creaks, final boom and bolts, tunnel reverb")
def gate_close(r):
    n = N(9.0)
    t = T(n)
    y = np.zeros(n)
    f = np.interp(t, [0.2, 1.4, 5.0, 5.4], [55, 165, 160, 90])
    mot = whine(9.0, f, r, harm=6, level=1.0) * np.interp(t, [0, 0.2, 1.2, 5.0, 5.4, 5.5], [0, 0, 0.6, 0.7, 0.3, 0])
    y += pk(mot, -12)
    sl_n = N(4.8)
    slide = colored(sl_n, r, -6, lo=25, hi=500) * (0.7 + 0.3 * swell(sl_n, r, 3.0, 0.6, False)) * np.interp(T(sl_n), [0, 0.5, 4.3, 4.8], [0, 1, 1, 0.3])
    place(y, pk(slide, -7), 0.7)
    place(y, pk(scrape(4.6, r, 150, 1400, 1.2) * np.interp(T(N(4.6)), [0, 0.5, 4.0, 4.6], [0, 1, 0.8, 0.2]), -16), 0.8)
    for t0, f0, f1 in [(1.0, 80, 110), (2.4, 120, 85), (3.8, 90, 130)]:
        place(y, pk(creak(1.2, r, f0, f1, 0.6, 2.8), -14), t0)
    place(y, pk(thump(3.5, 55, 26, 0.08, 1.3, 0.003, 0.35), 0), 5.35)
    place(y, pk(plate(85, 3.0, r, 1.1, 22, 14), -3), 5.35)
    place(y, pk(steel_bar(175, 2.5, r, 1.6), -9), 5.35)
    place(y, pk(burst(0.25, r, 100, 3500, 0.04, 0.0006), -5), 5.35)
    for t0, f0 in [(5.75, 150), (6.0, 190), (6.3, 140)]:
        place(y, pk(clunk(f0, 0.6, r, 0.1, 1.0), -8), t0)
    place(y, pk(debris(3.0, r, 40, 2, 400, 4500), -22), 5.5)
    return reverb(y, space("tunnel", stereo=False), wet=0.6, dry=0.8, n=n)


@sound("sfx.train_start", peak=-8.0, atten=48, note="coupling clunk, electric drive winding up, rail clacks accelerating, rumble swelling")
def train_start(r):
    n = N(6.5)
    t = T(n)
    y = np.zeros(n)
    place(y, pk(clunk(120, 0.6, r, 0.1, 1.0), -4), 0.1)
    place(y, pk(steel_bar(300, 1.2, r, 0.5), -12), 0.1)
    f = np.interp(t, [0.4, 6.5], [90, 520]) ** 1.0
    mot = whine(6.5, f, r, harm=4, level=1.0) * np.interp(t, [0.3, 1.0, 6.0, 6.5], [0, 0.4, 1.0, 1.0])
    y += pk(mot, -14)
    tt = 0.7
    while tt < 6.4:
        rate = 0.7 + 7.5 * (tt / 6.5) ** 1.5
        for off, g in [(0, 1.0), (0.1 / (1 + rate / 3), 0.7)]:
            place(y, pk(_rail_clack(r, r.uniform(0.95, 1.05)), -14) * (0.4 + 0.6 * (tt / 6.5)), tt + off, g)
        tt += 1.0 / rate
    rum = colored(n, r, -6, lo=25, hi=220) * np.interp(t, [0, 1, 6.5], [0.05, 0.4, 1.0])
    y += pk(rum, -9)
    return reverb(y, space("tunnel", stereo=False), wet=0.45, dry=0.9, n=n)


@sound("sfx.train_stop", peak=-8.0, atten=48, note="brake squeal falling, clacks slowing, pneumatic hiss, final shunt")
def train_stop(r):
    n = N(6.5)
    t = T(n)
    y = np.zeros(n)
    f = np.interp(t, [0, 4.4, 5.0], [520, 120, 80])
    mot = whine(6.5, f, r, harm=4, level=1.0) * np.interp(t, [0, 0.3, 4.4, 5.0], [1.0, 1.0, 0.3, 0.0])
    y += pk(mot, -14)
    tt = 0.0
    while tt < 5.2:
        rate = 7.5 * (1 - tt / 5.4) ** 1.6 + 0.4
        for off, g in [(0, 1.0), (0.1 / (1 + rate / 3), 0.7)]:
            place(y, pk(_rail_clack(r, r.uniform(0.95, 1.05)), -14) * (0.4 + 0.6 * (1 - tt / 5.4)), tt + off, g)
        tt += 1.0 / rate
    sq = mix(squeal(3.4, r, 1850, 800, 1.0, 0.025) * 0.5, squeal(3.2, r, 1370, 610, 1.0, 0.03) * 0.35)
    sq *= np.interp(T(N(3.4)), [0, 0.3, 2.4, 3.4], [0, 1, 0.6, 0])
    place(y, pk(sq, -8), 1.0)
    place(y, pk(bp(white(N(3.4), r), 900, 3500, 2) * np.interp(T(N(3.4)), [0, 0.4, 2.8, 3.4], [0, 1, 0.5, 0]), -16), 1.0)
    place(y, pk(hiss(1.8, r, 3000, 9500, 0.02, 0.5), -9), 4.4)
    place(y, pk(clunk(105, 0.6, r, 0.1, 1.0), -4), 4.45)
    place(y, pk(clunk(140, 0.5, r, 0.08, 0.7), -9), 5.0)
    place(y, pk(steel_bar(280, 1.0, r, 0.4), -14), 5.0)
    rum = colored(n, r, -6, lo=25, hi=220) * np.interp(t, [0, 4.0, 5.2, 6.5], [1.0, 0.5, 0.1, 0.0])
    y += pk(rum, -9)
    return reverb(y, space("tunnel", stereo=False), wet=0.45, dry=0.9, n=n)


@sound("sfx.air_open", lufs=-24.0, stereo=True, atten=48, note="3 s: confined rumble opening out, a bandpassed whoosh widening, then the room's huge tail")
def air_open(r):
    n = N(3.0)
    t = T(n)
    rum = colored(n, r, -6, lo=20, hi=130) * np.interp(t, [0, 0.8, 2.0], [1.0, 0.7, 0.0])
    q = np.interp(t, [0, 2.2], [3.0, 0.7])
    f = np.exp(np.interp(t, [0, 0.4, 2.4], [np.log(160), np.log(300), np.log(3200)]))
    wh = svf(white(n, r), f, q, "bp") * np.sin(np.pi * np.clip(t / 2.6, 0, 1)) ** 1.5
    air = hp(white(n, r), 3000, 2) * 0.1 * np.interp(t, [0.4, 1.4, 3.0], [0, 1, 0]) * 0.5
    low = np.sin(phase_of(np.interp(t, [0, 3], [38, 31]))) * np.interp(t, [0, 0.2, 1.0, 2.4], [0, 1, 0.6, 0]) * 0.5
    y = pk(rum, -3) + pk(wh, -5) + pk(air, -22) + pk(low, -8)
    st = reverb(y, space("cavern"), wet=0.7, dry=0.7, n=n)
    return fade(st, 0.0, 1.0)


@sound("sfx.pa_chime", peak=-9.0, atten=40, note="three soft metallic notes D5-A5-F5 (own design), speaker-band-limited, in a corridor")
def pa_chime(r):
    n = N(3.2)
    y = np.zeros(n)
    for t0, f in [(0.0, 587.3), (0.52, 880.0), (1.04, 698.5)]:
        note = modal([f, f * 2.0, f * 2.76, f * 4.07, f * 5.4], [1.1, 0.7, 0.45, 0.25, 0.15], [1, 0.35, 0.2, 0.08, 0.05], 2.2, r, detune=2, attack=0.004)
        place(y, note, t0)
    y = eq(y, [(200, -24), (420, 0), (5200, 0), (7500, -22)], circ=False)
    y = sat(y * 0.8, 1.3)
    return reverb(y, space("corridor", stereo=False), wet=0.35, dry=1.0, n=n)


@sound("sfx.klaxon", peak=-8.0, atten=48, note="alert klaxon: three raspy pulses with an onset glide, in a corridor, 4 s")
def klaxon(r):
    n = N(4.0)
    y = np.zeros(n)
    pn = N(0.85)
    pt = T(pn)
    f = 400 + 70 * np.exp(-pt / 0.08)
    ph = phase_of(f)
    buzz = 1 + 0.3 * np.sin(TWO_PI * 38 * pt)
    tone = hosc(f, nh=24, rolloff=0.6) * buzz
    tone = sat(tone / np.max(np.abs(tone)), 2.5)
    tone = bp(tone, 280, 3200, 2)
    e = np.minimum(1, pt / 0.012) * np.minimum(1, (0.85 - pt) / 0.04)
    for t0 in (0.12, 1.42, 2.72):
        place(y, tone * e, t0)
    return reverb(y, space("corridor", stereo=False), wet=0.4, dry=1.0, n=n)


@sound("sfx.elevator_arrive", peak=-12.0, atten=32, note="brake clunk, a soft two-note tone (C5, G5), air settling")
def elevator_arrive(r):
    n = N(3.0)
    y = np.zeros(n)
    place(y, pk(clunk(105, 0.4, r, 0.06, 0.8), -9), 0.0)
    place(y, pk(hiss(0.8, r, 800, 4000, 0.05, 0.25), -26), 0.0)
    for t0, f in [(0.12, 523.3), (0.55, 784.0)]:
        place(y, modal([f, f * 2.0, f * 3.0], [1.4, 0.6, 0.3], [1, 0.25, 0.08], 2.4, r, detune=1, attack=0.006), t0, 0.7)
    return reverb(y, space("room", stereo=False), wet=0.3, dry=1.0, n=n)


@sound("sfx.elevator_doors", peak=-12.0, atten=32, note="servo whine, rail slide, soft end stops, servo down")
def elevator_doors(r):
    n = N(3.0)
    y = np.zeros(n)
    place(y, pk(whine(0.35, np.linspace(300, 680, N(0.35)), r, 3), -14) * np.hanning(N(0.35) * 2)[:N(0.35)], 0.0)
    sl = circ(lambda z: delayloop(z, 70.0, 0.55, 0.3), white(N(1.2), r))
    sl = bp(sl, 1200, 4200, 2) * np.interp(T(N(1.2)), [0, 0.15, 0.9, 1.2], [0, 1, 0.8, 0])
    place(y, pk(sl, -15), 0.15)
    place(y, pk(clunk(160, 0.25, r, 0.035, 0.4), -15), 1.38)
    place(y, pk(clunk(190, 0.25, r, 0.03, 0.3), -19), 1.46)
    place(y, pk(whine(0.3, np.linspace(650, 300, N(0.3)), r, 3), -18) * np.hanning(N(0.3) * 2)[N(0.3):], 1.4)
    return reverb(y, space("room", stereo=False), wet=0.25, dry=1.0, n=n)


@sound("sfx.door_heavy", peak=-6.0, atten=40, note="bulkhead: latch release, hydraulic hiss and whine, groaning swing, thud and seal")
def door_heavy(r):
    n = N(3.2)
    y = np.zeros(n)
    place(y, pk(clunk(230, 0.4, r, 0.05, 0.8), -6), 0.0)
    place(y, click(r, 2400, 0.002), 0.0, 0.6)
    place(y, pk(hiss(1.0, r, 1500, 7000, 0.1, None), -22) * 1.0, 0.1)
    place(y, pk(whine(1.0, np.interp(T(N(1.0)), [0, 1.0], [110, 190]), r, 3), -22), 0.12)
    place(y, pk(creak(1.1, r, 70, 115, 0.7, 2.6), -12), 0.2)
    place(y, pk(scrape(1.0, r, 150, 900) * np.interp(T(N(1.0)), [0, 0.3, 1.0], [0, 1, 0.3]), -22), 0.25)
    place(y, pk(thump(0.7, 75, 40, 0.03, 0.2, 0.002), 0), 1.4)
    place(y, pk(plate(150, 1.4, r, 0.5, 18, 10), -4), 1.4)
    place(y, pk(burst(0.2, r, 100, 3500, 0.03, 0.0005), -8), 1.4)
    place(y, pk(hiss(1.0, r, 2500, 8000, 0.03, 0.4), -20), 1.5)
    return reverb(y, space("corridor", stereo=False), wet=0.3, dry=1.0, n=n)


@sound("sfx.door_boom", peak=-3.0, stereo=True, atten=64, note="the cage door shutting: crack, sub boom, plate and bar rings, bolt clunks, hangar reverb")
def door_boom(r):
    n = N(8.0)
    y = np.zeros(n)
    place(y, thump(4.0, 50, 28, 0.12, 1.5, 0.003, 0.3), 0.0)
    place(y, pk(plate(72, 5.0, r, 1.1, 22, 18), -4), 0.0)
    place(y, pk(steel_bar(112, 3.5, r, 2.0), -8), 0.0)
    place(y, pk(burst(0.2, r, 100, 4000, 0.03, 0.0005), -4), 0.0)
    place(y, pk(clunk(140, 0.6, r, 0.1, 1.0), -7), 0.17)
    place(y, pk(clunk(175, 0.6, r, 0.1, 1.0), -9), 0.36)
    st = reverb(y, space("hangar"), wet=1.1, dry=0.55, n=n)
    return fade(st, 0.0, 1.5)


def _breaker(r, v):
    n = N(1.2)
    t = T(n)
    k = 1.0 + 0.05 * (v - 2)
    y = np.zeros(n)
    for t0, g in [(0.0, 0.5), (0.017 * k, 0.4), (0.031 * k, 0.3)]:
        place(y, click(r, r.uniform(1800, 3200), 0.002) * g, t0)
    t0 = 0.045 * k
    place(y, pk(thump(0.4, 135 * k, 62, 0.012, 0.1, 0.001), 0), t0)
    place(y, pk(plate(240 * k, 0.8, r, 0.2, 16, 9), -3), t0)
    place(y, pk(steel_bar(420 * k, 0.7, r, 0.22), -9), t0)
    place(y, pk(burst(0.05, r, 600, 5000, 0.006, 0.0004), -7), t0)
    f0 = 100 * (0.95 + 0.05 * v)
    f = np.interp(t, [0.05, 0.45, 1.3], [f0 * 0.62, f0, f0]) * (1 + 0.003 * drift(n, r, 15, False))
    ph = phase_of(f)
    hum = sum(np.sin(h * ph + h) / h ** 0.8 for h in range(1, 9))
    g = np.interp(t, [0.05, 0.12, 0.5, 0.9, 1.2], [0, 0.4, 1.0, 0.85, 0.7])
    flick = np.where(t < 0.28, (np.sin(TWO_PI * (31 + 6 * v) * t) > -0.2).astype(float), 1.0)
    flick = lp(flick, 300, 1)
    y += pk(hum * g * flick, -10)
    corona = bp(white(n, r), 3800, 9500, 2) * np.interp(t, [0.12, 0.6, 1.35], [0, 1, 0.7]) * flick
    y += pk(corona, -22)
    return y


for _v in (0, 1, 2, 3):
    sound("sfx.breaker" if _v == 0 else f"sfx.breaker_{_v}", lufs=-20.0, atten=40,
          note="one bank of lights: contactor chatter and clunk, ballast hum rising, lamp corona" + ("" if _v == 0 else f" (variant {_v})"))(
        (lambda v: (lambda r: _breaker(r, v)))(_v))


@sound("sfx.booth_light", peak=-14.0, atten=24, note="small switch, tube strike ping, a flickering buzz settling to a faint hum")
def booth_light(r):
    n = N(1.4)
    t = T(n)
    y = np.zeros(n)
    place(y, click(r, 2600, 0.002), 0.0, 0.8)
    place(y, pk(glass_ring(2350, 0.5, r, 0.25), -10), 0.012)
    gate = np.where(t < 0.3, (np.sin(TWO_PI * 43 * t) > -0.1).astype(float), 1.0)
    gate = lp(gate, 400, 1)
    ph = phase_of(np.full(n, 100.0))
    hum = sum(np.sin(h * ph + h) / h for h in range(1, 7)) * gate * np.interp(t, [0.03, 0.2, 1.4], [0, 1, 0.5])
    y += pk(hum, -12)
    y += pk(bp(white(n, r), 3500, 8500, 2) * gate * np.interp(t, [0.03, 0.3, 1.4], [0, 1, 0.3]), -26)
    return reverb(y, space("booth", stereo=False), wet=0.3, dry=1.0, n=n)


def _above(r, hard):
    s = 1.35 if hard else 1.0
    dur = 9.0 if hard else 7.0
    n = N(dur)
    y = np.zeros(n)
    place(y, pk(thump(3.5, 46, 21, 0.18, 0.9 * s, 0.012, 0.4), 0), 0.0)
    place(y, pk(lp(white(N(0.8), r), 230, 2) * expo(N(0.8), 0.3, 0.012), -3), 0.0)
    place(y, pk(colored(N(5.0), r, -6, lo=20, hi=110) * expo(N(5.0), 1.5 * s, 0.1), -4), 0.05)
    if hard:
        place(y, pk(thump(2.5, 52, 24, 0.14, 0.7, 0.01, 0.4), -2), 0.38)
        place(y, pk(metal_crash(2.2, r, 1.0, 20, 90, 1800), -8), 0.1)
        for t0 in (0.15, 0.3, 0.52, 0.8):
            place(y, pk(clunk(r.uniform(130, 220), 0.5, r, 0.08, 0.8), -14), t0)
    crk = [(0.3, 55, 90), (0.9, 110, 70), (1.7, 65, 95)] + ([(0.5, 80, 140), (2.3, 140, 60), (3.0, 70, 110)] if hard else [])
    for t0, f0, f1 in crk:
        place(y, pk(creak(r.uniform(0.7, 1.4), r, f0, f1, 0.6, 2.2), -11 if hard else -13), t0)
    for _ in range(4 if not hard else 8):
        place(y, pk(steel_bar(r.uniform(120, 700), 1.2, r, 0.5), -22), r.uniform(0.3, 3.0))
    place(y, pk(debris(5.5, r, 35 * s, 1, 500, 4500), -18), 0.5)
    place(y, pk(hiss(3.5, r, 3000, 9000, 0.4, 1.5), -32), 0.8)
    st = reverb(y, space("hangar"), wet=0.75, dry=0.8, n=n)
    return fade(st, 0.0, 1.5)


sound("sfx.impact_above", peak=-4.0, stereo=True, atten=64,
      note="the fortress struck from the surface: muffled colossal blow, structure groaning, debris ticks, hangar reverb")(lambda r: _above(r, False))
sound("sfx.impact_above_hard", peak=-1.8, stereo=True, atten=64,
      note="a worse one: double blow, steel tearing, more groaning and debris")(lambda r: _above(r, True))


@sound("sfx.lights_flicker", peak=-14.0, atten=40, note="ballast hum stuttering on and off with relay ticks and snaps")
def lights_flicker(r):
    n = N(2.0)
    t = T(n)
    ons = [(0.0, 0.10), (0.17, 0.22), (0.30, 0.55), (0.62, 2.05)]
    gate = np.zeros(n)
    for a, b in ons:
        gate[N(a):N(b)] = 1.0
    gate = lp(gate, 600, 1)
    ph = phase_of(np.full(n, 100.0))
    hum = sum(np.sin(h * ph + h) / h ** 0.8 for h in range(1, 8)) * gate
    buzz = bp(white(n, r), 2500, 7000, 2) * gate
    y = pk(hum, -8) + pk(buzz, -24)
    for a, b in ons:
        place(y, click(r, r.uniform(1500, 3500), 0.003) * 0.6, a)
        place(y, click(r, r.uniform(1500, 3500), 0.002) * 0.4, b)
    place(y, pk(hiss(0.6, r, 3000, 9000, 0.01, 0.2), -26), 0.62)
    y *= np.interp(t, [0, 1.3, 2.0], [1, 0.9, 0.35])
    return reverb(y, space("room", stereo=False), wet=0.25, dry=1.0, n=n)


@sound("sfx.dust_fall", lufs=-34.0, atten=24, note="fine dust sifting down: soft hiss, tiny grains, an occasional pebble")
def dust_fall(r):
    n = N(5.0)
    t = T(n)
    y = bp(white(n, r), 3000, 9500, 2) * swell(n, r, 14, 1.2, False)
    y = pk(y, -6) * np.interp(t, [0, 0.8, 2.2, 5.0], [0, 1, 0.5, 0])
    g = ticks(5.0, r, 160, 2000, 9000, 0.0015, 20, 1.2, (0.1, 0.5)) * np.interp(t, [0, 0.5, 1.5, 5.0], [0, 1, 0.6, 0.02])
    y += pk(g, -14)
    y += pk(lp(white(n, r), 700, 2), -34) * np.interp(t, [0, 1.0, 4.0], [0, 1, 0])
    for _ in range(5):
        place(y, pk(glass_ring(r.uniform(2500, 5500), 0.12, r, 0.04), -22), r.uniform(0.6, 3.5))
    return y


@sound("sfx.gurney", lufs=-30.0, loop=True, atten=24, note="hospital bed on two squeaking casters, 6 s, whole wheel revolutions so it loops")
def gurney(r):
    dur = 6.0
    n = N(dur)
    t = T(n)
    roll = circ(lambda z: lp(z, 600, 2), white(n, r))
    roll = roll * (0.55 + 0.45 * (0.5 + 0.5 * np.cos(TWO_PI * 18 * t / dur)) ** 1.5)
    y = pk(roll, -14)
    for revs, f, ph0, lvl in [(18, 1850, 0.0, -10), (15, 2650, 1.3, -14)]:
        gate = np.clip(np.sin(TWO_PI * revs * t / dur + ph0), 0, 1) ** 2.5
        fv = f * (1 + 0.05 * drift(n, r, 1.5)) * (1 + 0.03 * gate)
        sq = np.sin(phase_of(fv, True)) + 0.35 * np.sin(2 * phase_of(fv, True) + 0.5) + 0.08 * csvf(white(n, r), f * 1.5, 3, "bp")
        y += pk(sq * gate, lvl) * (0.75 + 0.25 * swell(n, r, 3, 0.6))
    for revs, ph0 in [(18, 0.0), (15, 1.3)]:
        for k in range(revs):
            tk = (k + (0.25 - ph0 / TWO_PI) % 1.0) * dur / revs
            place(y, pk(click(r, 1100, 0.004, 0.06), -24), tk, 1.0, wrap=True)
    y += pk(fold(ticks(dur + 0.5, r, 6, 1500, 5000, 0.003), n), -34)
    return y


@sound("sfx.rig_tear", peak=-6.0, atten=64, note="bolts popping, steel tearing with a rising rasp, cables snapping, then a falling whistle")
def rig_tear(r):
    n = N(4.2)
    y = np.zeros(n)
    for t0 in (0.05, 0.12, 0.21, 0.28, 0.4, 0.46, 0.6):
        place(y, pk(clunk(r.uniform(200, 380), 0.3, r, 0.04, 0.4), -12), t0)
        place(y, click(r, r.uniform(1200, 3500), 0.003) * 0.7, t0)
    tn = N(2.3)
    place(y, pk(creak(2.3, r, 380, 140, 0.9, 4.0, 3.0, 0.9), -7) * np.interp(T(tn), [0, 1.5, 2.3], [0.3, 1, 0.7]), 0.1)
    place(y, pk(scrape(2.2, r, 600, 6000, 1.6) * np.interp(T(N(2.2)), [0, 1.8, 2.2], [0.1, 1, 0.5]), -14), 0.2)
    place(y, pk(ks(hp(white(N(0.01), r), 200, 1), 180, 1.6, 0.997, 0.4), -9), 0.9)
    place(y, pk(ks(hp(white(N(0.01), r), 200, 1), 260, 1.6, 0.997, 0.4), -12), 1.3)
    place(y, pk(creak(1.5, r, 60, 46, 0.7, 2.0), -9), 0.4)
    ft = N(1.5)
    fw = svf(white(ft, r), np.exp(np.linspace(np.log(2600), np.log(300), ft)), 3, "bp") * np.linspace(0.1, 1, ft) ** 1.5
    place(y, pk(fw, -16), 2.0)
    return reverb(y, space("hangar", stereo=False), wet=0.4, dry=1.0, n=n)


@sound("sfx.rig_crash", peak=-2.0, atten=64, note="a lighting rig hitting something hard: sub thud, a pile of plates, shattering glass, a pipe rolling away")
def rig_crash(r):
    n = N(5.0)
    y = np.zeros(n)
    place(y, thump(0.9, 110, 40, 0.03, 0.3, 0.002), 0.0, 1.0)
    place(y, pk(metal_crash(3.2, r, 1.2, 32, 90, 2400), -2), 0.0)
    place(y, pk(plate(180, 2.0, r, 0.6, 20, 12), -5), 0.0)
    place(y, pk(burst(0.3, r, 200, 7000, 0.05, 0.0004), -3), 0.0)
    place(y, pk(glass_shatter(r, 1.8), -5), 0.02)
    place(y, pk(scrape(1.2, r, 300, 2000) * np.linspace(1, 0, N(1.2)), -17), 0.3)
    place(y, pk(steel_bar(330, 2.5, r, 1.2), -17), 0.9)
    place(y, pk(debris(4.0, r, 60, 3, 600, 6000), -16), 0.2)
    return reverb(y, space("hangar", stereo=False), wet=0.55, dry=1.0, n=n)


@sound("sfx.hand_rise", lufs=-24.0, stereo=True, atten=64, note="something vast rising out of liquid: cascading water, deep creaks, a morphing formant groan, vast hall")
def hand_rise(r):
    dur = 9.0
    n = N(dur)
    t = T(n)
    wat = eq(white(n, r), [(120, -30), (400, -6), (1500, 0), (5000, -8), (10000, -26)])
    wat = wat * np.clip(1 + 0.6 * drift(n, r, 40, False), 0, 3) * np.interp(t, [0, 0.4, 2.6, 5.0, 9.0], [0, 0.4, 1.0, 0.45, 0.1])
    wave = colored(n, r, -3, lo=40, hi=700) * (0.5 + 0.5 * np.sin(TWO_PI * 0.55 * t - 1.0)) * np.interp(t, [0, 1, 4, 9], [0, 1, 0.6, 0.1])
    bub = np.zeros(n)
    for _ in range(140):
        f0 = r.uniform(100, 600)
        tb = r.beta(2, 4) * dur
        bt = T(N(0.07))
        place(bub, np.sin(phase_of(f0 * (1 + 1.3 * bt / 0.07))) * np.exp(-bt / 0.02) * r.uniform(0.2, 1), tb)
    y = pk(wat, -7) + pk(wave, -9) + pk(bub, -20)
    for t0, f0, f1 in [(0.8, 48, 70), (2.0, 80, 52), (3.2, 60, 100), (4.6, 110, 62)]:
        place(y, pk(creak(r.uniform(1.0, 1.8), r, f0, f1, 0.8, 2.2, 3.0), -10), t0)
    f = np.interp(t, [0, 1.5, 3.5, 5.5, 9], [34, 42, 58, 46, 33]) * (1 + 0.04 * drift(n, r, 3, False))
    mixv = np.clip(np.interp(t, [0, 3, 5.5, 9], [0, 0.2, 1.0, 0.3]), 0, 1)
    gr = choir(f, dur, r, "oh", 3, 30, 0.03, 0.8, 0.2, None, "ah", mixv)
    gr *= np.interp(t, [0, 1.5, 4.5, 6.5, 9], [0, 0.3, 1.0, 0.7, 0.0])
    y += pk(gr, -4)
    place(y, pk(burst(0.7, r, 150, 4500, 0.2, 0.004), -8), 2.4)
    place(y, pk(thump(2.0, 40, 26, 0.2, 0.6, 0.02, 0.3), -4), 2.3)
    st = reverb(y, space("hangar"), wet=0.6, dry=0.7, n=n)
    return fade(st, 0.0, 1.8)


@sound("sfx.eyes_on", lufs=-28.0, atten=48, note="quiet ominous power-up: a low drone climbing, beating high tones, filament hiss, a muffled seat-click")
def eyes_on(r):
    n = N(4.8)
    t = T(n)
    f = np.interp(t, [0, 3.0, 4.8], [52, 84, 80])
    ph = phase_of(f)
    drone = (np.sin(ph) + 0.5 * np.sin(2 * ph + 0.3) + 0.3 * np.sin(3 * ph + 1.0)) * np.interp(t, [0, 1.5, 3.2, 4.8], [0, 0.6, 1.0, 0.5])
    hi = (np.sin(TWO_PI * 880 * t) + np.sin(TWO_PI * 887 * t + 1) + 0.5 * np.sin(TWO_PI * 1320 * t + 2)) * np.interp(t, [0.4, 1.8, 3.4, 4.8], [0, 0.5, 1.0, 0.3])
    sh = bp(white(n, r), 2000, 6500, 2) * np.interp(t, [0.2, 3.0, 4.8], [0, 1, 0.2])
    y = pk(drone, -4) + pk(hi, -22) + pk(sh, -30)
    place(y, pk(lp(clunk(90, 0.4, r, 0.06, 0.8), 400), -16), 3.3)
    return reverb(y, space("hangar", stereo=False), wet=0.5, dry=0.8, n=n)


@sound("sfx.alarm_cut", peak=-8.0, atten=48, note="a two-tone alarm stopping dead, leaving only the corridor's tail")
def alarm_cut(r):
    n = N(2.4)
    an = N(0.8)
    t = T(an)
    f = np.where((t % 0.8) < 0.4, 700.0, 940.0)
    f = lp(f, 80, 1)
    tone = hosc(f, nh=14, rolloff=1.0, odd=True)
    tone = tone / np.max(np.abs(tone)) * np.minimum(1, t / 0.004)
    tone[-N(0.0005):] *= np.linspace(1, 0, N(0.0005))
    dry = np.zeros(n)
    dry[:an] = tone
    wet = reverb(dry, space("room", stereo=False), wet=1.0, dry=0.0, n=n)
    return dry + 0.45 * wet


@sound("sfx.hatch_close", peak=-6.0, atten=24, note="capsule hatch: clang, accelerating ratchet, pressure hiss, the outside going dull")
def hatch_close(r):
    n = N(4.5)
    t = T(n)
    y = np.zeros(n)
    place(y, pk(thump(0.5, 95, 45, 0.02, 0.12), 0), 0.0)
    place(y, pk(plate(420, 0.8, r, 0.22, 16, 9), -4), 0.0)
    place(y, pk(burst(0.1, r, 300, 5000, 0.015, 0.0005), -6), 0.0)
    tt = 0.35
    gap = 0.11
    while tt < 0.95:
        place(y, pk(click(r, 1800, 0.003, 0.05), -10), tt)
        place(y, pk(clunk(260, 0.15, r, 0.02, 0.3), -22), tt)
        tt += gap
        gap *= 0.82
    place(y, pk(clunk(150, 0.5, r, 0.06, 1.0), -4), 1.0)
    h = hiss(2.4, r, 2500, 9000, 0.3, None, 1.0) * np.sin(np.pi * np.linspace(0, 1, N(2.4))) ** 1.5
    place(y, pk(h, -14), 1.0)
    place(y, pk(colored(N(2.8), r, -6, lo=25, hi=140) * np.sin(np.pi * np.linspace(0, 1, N(2.8))), -14), 1.0)
    cutoff = np.interp(t, [0, 0.9, 1.8, 4.5], [9500, 9000, 1800, 1500])
    y = svf(y, cutoff, 0.6, "lp")
    return reverb(y, space("capsule", stereo=False), wet=0.5, dry=0.8, n=n)


@sound("sfx.fluid_fill", lufs=-28.0, stereo=True, atten=24, note="8 s: trickle and bubbling, a cavity resonance climbing as the chamber fills, then everything submerged and dull")
def fluid_fill(r):
    dur = 8.0
    n = N(dur)
    t = T(n)
    rate = np.interp(np.arange(N(dur)) / SR, [0, 2, 5, 8], [40, 150, 120, 30])
    bub = np.zeros(n)
    tt = 0.0
    while tt < dur:
        tt += r.exponential(1.0 / np.interp(tt, [0, 2, 5, 8], [40, 150, 120, 30]))
        f0 = r.uniform(300, 1500) * np.interp(tt, [0, 6, 8], [1.0, 0.5, 0.3])
        ln = r.uniform(0.02, 0.06)
        bt = T(N(ln))
        place(bub, np.sin(phase_of(f0 * (1 + 0.8 * bt / ln))) * np.exp(-bt / (ln / 3)) * r.uniform(0.2, 1), tt)
    pour = bp(white(n, r), 1000, 4500, 2) * np.interp(t, [0, 1.5, 4.5, 6.0, 8], [0.05, 0.5, 1.0, 0.4, 0.0])
    cav = svf(white(n, r), np.exp(np.interp(t, [0, 6.0, 8.0], [np.log(150), np.log(900), np.log(900)])), 9, "bp") * np.interp(t, [0, 1, 5, 7, 8], [0, 0.6, 1.0, 0.4, 0.1])
    y = pk(bub, -10) * np.interp(t, [0, 5, 7, 8], [1, 0.7, 0.3, 0.2]) + pk(pour, -8) + pk(cav, -9)
    cutoff = np.exp(np.interp(t, [0, 4.5, 6.5, 8.0], [np.log(11000), np.log(7000), np.log(450), np.log(380)]))
    y = svf(y, cutoff, 0.6, "lp")
    y += pk(np.sin(TWO_PI * 52 * t) + 0.5 * np.sin(TWO_PI * 104 * t), -16) * np.interp(t, [4.5, 7, 8], [0, 1, 1])
    st = np.stack([y, np.roll(svf(y, cutoff * 0.9, 0.6, "lp"), 37)], axis=1)
    st = reverb(st, space("capsule"), wet=0.35, dry=0.8, n=n)
    return fade(st, 0.02, 0.0)


@sound("sfx.contact", lufs=-26.0, stereo=True, atten=24, note="the plug walls turning to glass: a shimmering cluster of high partials, FM glints, a rising airy sweep, a clear wide pad")
def contact(r):
    dur = 6.0
    n = N(dur)
    t = T(n)
    y = np.zeros((n, 2))
    base = 220.0
    for k in range(8, 25):
        f = base * k * (1 + r.uniform(-0.004, 0.004))
        st = r.uniform(0.2, 1.2)
        en = r.uniform(2.5, 4.5)
        e = np.interp(t, [0, st, en, en + 1.5, dur], [0, 0, 1, 0.5, 0.0]) * (0.6 + 0.4 * np.sin(TWO_PI * r.uniform(2, 9) * t + r.uniform(0, 6.28)))
        y += pan(np.sin(TWO_PI * f * t + r.uniform(0, 6.28)) * e / k ** 0.5, r.uniform(-0.9, 0.9))
    y = rn(y, -22)
    gl = np.zeros((n, 2))
    for _ in range(46):
        f = r.uniform(3500, 9500)
        gn = N(0.35)
        gt = T(gn)
        g = np.sin(phase_of(np.full(gn, f)) + 2.0 * np.sin(phase_of(np.full(gn, f * 1.41)))) * np.exp(-gt / 0.07)
        place(gl, g * r.uniform(0.2, 1.0), r.uniform(0.3, 3.8), pan=r.uniform(-1, 1))
    y += rn(gl, -34)
    sw = svf(white(n, r), np.exp(np.interp(t, [0, 0.3, 2.2, 6], [np.log(500), np.log(700), np.log(6500), np.log(6500)])), 1.5, "bp")
    sw = sw * np.interp(t, [0, 0.3, 1.8, 3.5, 6], [0, 0.2, 1, 0.2, 0])
    y += rn(widen(sw, r, 0.8), -36)
    pad_ = np.zeros(n)
    for f, a in [(440, 1.0), (660.3, 0.8), (880.2, 0.6), (1109.0, 0.3)]:
        pad_ += a * np.sin(TWO_PI * f * t) + a * 0.7 * np.sin(TWO_PI * (f * 1.0035) * t + 1)
    pad_ *= np.interp(t, [0, 2.4, 3.6, 6.0], [0, 0, 1, 0])
    y += rn(widen(pad_, r, 0.7), -34)
    st = reverb(y, space("hall"), wet=0.5, dry=0.7, n=n)
    return fade(st, 0.05, 0.4)


@sound("sfx.sync_rise", lufs=-26.0, stereo=True, atten=24, note="a tone climbing for 4 s while detuned voices converge, locking into a just-intoned D chord that holds and fades")
def sync_rise(r):
    dur = 9.5
    n = N(dur)
    t = T(n)
    R0 = 146.83
    tgt = [R0 * x for x in (1.0, 1.5, 2.0, 2.5, 3.0, 4.0)]
    lock = 4.2
    y = np.zeros((n, 2))
    amps = [1.0, 0.7, 0.8, 0.45, 0.35, 0.3]
    for i, (ft, a) in enumerate(zip(tgt, amps)):
        detune_c = r.choice([-1, 1]) * r.uniform(25, 60)
        prog = np.clip(t / lock, 0, 1)
        f_start = ft * 2 ** (-(1.2 + 0.3 * i))
        f = np.where(t < lock, f_start * (ft / f_start) ** (prog ** 1.6) * 2 ** (detune_c * (1 - prog) / 1200), ft)
        ph = phase_of(f)
        v = np.sin(ph) + 0.3 * np.sin(2 * ph + 0.4) * np.interp(t, [0, lock, lock + 0.5], [0.0, 0.3, 1.0]) + 0.1 * np.sin(3 * ph)
        e = np.interp(t, [0, 0.3 + 0.2 * i, lock, 6.0, dur], [0, 0.15, 0.7, 1.0, 0.0])
        y += pan(v * e * a, -0.6 + 1.2 * i / 5)
    main = np.interp(t, [0, 4.0, 4.3], [80.0, 587.3, 587.3])
    main = 80.0 * (587.3 / 80.0) ** (np.clip(t / 4.0, 0, 1) ** 1.4)
    mv = np.sin(phase_of(main)) + 0.25 * np.sin(2 * phase_of(main))
    mv *= np.interp(t, [0, 0.5, 4.0, 4.4, 6.0], [0, 0.3, 0.8, 0.5, 0.0])
    y += pan(mv, 0.0) * 0.6
    place(y, thump(0.6, 78, 52, 0.05, 0.18, 0.004) * 0.35, lock)
    y = eq(y, [(40, -12), (120, 0), (3000, 0), (9000, -12)], circ=False)
    st = reverb(y, space("hall"), wet=0.35, dry=0.85, n=n)
    return fade(st, 0.1, 0.5)


def _bolt(r, f, hit):
    n = N(3.6)
    y = np.zeros(n)
    place(y, pk(burst(0.03, r, 800, 9000, 0.004, 0.0002), -2), 0.0)
    place(y, click(r, 3400, 0.0012, 0.01), 0.0, 0.8)
    place(y, thump(0.6, 80, 42, 0.02, 0.15, 0.001) * 1.0, 0.0)
    place(y, pk(plate(f * 1.4, 1.5, r, 0.35, 18, 10), -4), 0.0)
    place(y, pk(steel_bar(f, 3.2, r, 1.9), -6), 0.0)
    place(y, pk(steel_bar(f * 1.007, 3.0, r, 1.6), -10), 0.0)
    place(y, pk(clunk(hit, 0.5, r, 0.06, 0.8), -9), 0.07)
    return reverb(y, space("hangar", stereo=False), wet=0.45, dry=1.0, n=n)


for _i, (_f, _h) in enumerate([(132.0, 170.0), (147.0, 150.0), (124.0, 190.0)], 1):
    sound(f"sfx.bolt_{_i}", peak=-2.0, atten=64, note=f"one huge lock bolt releasing: crack, sub, plate and bar ring (variant {_i})")(
        (lambda f, h: (lambda r: _bolt(r, f, h)))(_f, _h))


@sound("sfx.bridge_slide", peak=-10.0, atten=64, note="a massive walkway sliding away: rumble fading with distance, rail squeal, wheel clatter, soft end stop")
def bridge_slide(r):
    n = N(6.5)
    t = T(n)
    amp = np.interp(t, [0, 0.6, 1.5, 5.0, 6.5], [0, 1, 0.9, 0.3, 0.1])
    y = pk(colored(n, r, -6, lo=25, hi=200) * (0.7 + 0.3 * swell(n, r, 2, 0.5, False)), 0) * amp
    cr = creak(5.0, r, 300, 420, 0.8, 2.0, 3.0, 0.7)
    place(y, pk(cr, -14) * np.interp(T(N(5.0)), [0, 1, 5], [1, 0.8, 0.2]), 0.3)
    place(y, pk(scrape(5.0, r, 200, 1500) * np.interp(T(N(5.0)), [0, 0.8, 5], [0.2, 1, 0.2]), -20), 0.3)
    place(y, pk(ticks(5.0, r, 12, 300, 1800, 0.004), -20) * 1.0, 0.4)
    place(y, pk(thump(0.5, 70, 40, 0.03, 0.15), -8), 5.6)
    place(y, pk(plate(200, 0.8, r, 0.2, 12, 8), -14), 5.6)
    y = svf(y, np.interp(t, [0, 3, 6.5], [4000, 1500, 600]), 0.6, "lp")
    return reverb(y, space("hangar", stereo=False), wet=0.5, dry=0.9, n=n)


# ------------------------------------------------------------------ extras the cue sheet mentions but the event list did not
@sound("sfx.alarm_loop", peak=-10.0, loop=True, atten=48, note="EXTRA: the two-tone alarm that sfx.alarm_cut stops (3.2 s = 64 ticks, loops); 700/940 Hz, same timbre")
def alarm_loop(r):
    dur = 8 * 0.4                                    # 3.2 s = 64 ticks
    n = N(dur)
    t = T(n)
    f = np.where((t % 0.8) < 0.4, 700.0, 940.0)
    f = circ(lambda z: lp(z, 80, 1), f)
    tone = hosc(f, nh=14, rolloff=1.0, odd=True, loop=False)
    tone = tone / np.max(np.abs(tone))
    return cconv(tone, space("room", stereo=False)) * 0.45 + tone


@sound("sfx.chains", peak=-12.0, atten=48, note="EXTRA (cue 5.21 'chains swing'): heavy chains clinking as they swing after a blow, 5 s")
def chains(r):
    n = N(5.0)
    y = np.zeros(n)
    t = 0.05
    while t < 4.3:
        f = r.uniform(500, 2400)
        place(y, pk(steel_bar(f, 0.6, r, 0.12 + 0.1 * r.random()), -4 - 12 * t / 4.3) * r.uniform(0.4, 1.0), t)
        place(y, pk(thump(0.08, r.uniform(200, 420), 150, 0.01, 0.025), -14) * r.uniform(0.3, 1.0), t)
        t += r.exponential(0.07 + 0.22 * (t / 4.3) ** 1.5) + 0.02
    place(y, pk(creak(2.0, r, 90, 70, 0.5, 2.5), -26), 0.1)
    return reverb(y, space("hangar", stereo=False), wet=0.5, dry=1.0, n=n)


@sound("sfx.lake_ring", peak=-16.0, atten=48, note="EXTRA (cue 5.21 'the lake rings'): the red lake sloshing and a low resonant ring after a blow, 7 s")
def lake_ring(r):
    n = N(7.0)
    t = T(n)
    y = modal([52.0, 78.5, 131.0, 205.0], [2.6, 2.0, 1.4, 1.0], [1.0, 0.7, 0.4, 0.2], 7.0, r, detune=6, beat=0.003, attack=0.05)
    y = y / np.max(np.abs(y)) * 0.8
    sl = svf(white(n, r), 450 + 150 * drift(n, r, 0.6, False), 1.3, "bp") * (0.5 + 0.5 * np.sin(TWO_PI * 0.9 * t - 1.0)) ** 2 * np.interp(t, [0, 0.3, 3.0, 7.0], [0, 1, 0.5, 0.0])
    y += pk(sl, -14)
    for _ in range(18):
        f0 = r.uniform(150, 420)
        bt = T(N(0.08))
        place(y, np.sin(phase_of(f0 * (1 + 1.2 * bt / 0.08))) * np.exp(-bt / 0.03) * r.uniform(0.1, 0.4), r.uniform(0.2, 4.0))
    return reverb(y, space("hangar", stereo=False), wet=0.6, dry=0.8, n=n)


@sound("sfx.breathing", peak=-18.0, loop=True, atten=8, note="EXTRA (cue 6 'own breathing'): a close, muffled breath cycle inside a helmet-like space, 8 s = 2 breaths, loops")
def breathing(r):
    dur = 8.0
    n = N(dur)
    y = np.zeros(n)
    for k in range(2):
        t0 = 0.4 + k * 4.0 + r.normal(0, 0.05)
        inn = N(1.5)
        ti = T(inn)
        a = svf(white(inn, r), 700 + 900 * (ti / 1.5), 1.0, "bp") * np.sin(np.pi * np.minimum(1, ti / 1.5) * 0.9) ** 1.5
        place(y, pk(a, -2), t0, 1.0, wrap=True)
        exn = N(1.9)
        te = T(exn)
        b = svf(white(exn, r), 900 - 500 * (te / 1.9), 0.9, "bp") * np.exp(-te / 0.8) * np.minimum(1, te / 0.15)
        place(y, pk(b, -4), t0 + 2.0, 1.0, wrap=True)
    y = eq(y, [(80, -20), (200, 0), (900, 0), (2500, -10), (6000, -26)])
    return cconv(y, space("capsule", stereo=False)) * 0.5 + y