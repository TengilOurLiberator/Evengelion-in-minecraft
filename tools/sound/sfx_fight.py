"""sfx_fight.py - the plug, the launch and the fight: charge, roar, barrier, beam, blows, the cross of light, the
heartbeat and the 'your turn' cue."""
from dsp import *
from blocks import *
from reg import sound


@sound("sfx.launch_charge", lufs=-24.0, stereo=True, atten=32, note="3 s whine climbing exponentially with a second voice, accelerating arcing ticks and a swelling sub")
def launch_charge(r):
    dur = 3.0
    n = N(dur)
    t = T(n)
    p = t / dur
    f = 180 * (3400 / 180) ** (p ** 1.5)
    w1 = whine(dur, f, r, harm=4, level=1.0, jitter=0.003)
    w2 = whine(dur, f * 1.5, r, harm=3, level=0.5, jitter=0.004) * np.interp(t, [0, 1.0, 3.0], [0, 0.5, 1])
    hum = np.sin(phase_of(60 + 70 * p ** 2)) * 0.5
    nz = bp(white(n, r), 1500, 9000, 2) * p ** 2
    tk = ticks(dur, r, 8, 2500, 9000, 0.002, None, 1.0)
    rate = 10 + 150 * p ** 2
    tk = np.zeros(n)
    tt = 0.0
    while tt < dur:
        tt += r.exponential(1.0 / np.interp(tt, [0, 3], [8, 160]))
        place(tk, click(r, r.uniform(2500, 6500), 0.0015) * r.uniform(0.3, 1.0), tt)
    sub = np.sin(phase_of(28 + 12 * p)) * p ** 1.5
    y = pk(w1, -3) * (0.3 + 0.7 * p) + pk(w2, -9) + pk(hum, -16) + pk(nz, -22) + pk(tk, -18) + pk(sub, -12)
    y = svf(y, np.full(n, 12000.0), 0.7, "lp")
    st = widen(y, r, 0.5)
    st = reverb(st, space("hall"), wet=0.18, dry=1.0, n=n)
    return fade(st, 0.02, 0.03)


ROAR_LUFS = -17.0      # level of the roar in both sfx.launch and sfx.launch_roar (they are built raw so they match)


def _roar_cycle(r, dur=6.0):
    n = N(dur)
    t = T(n)
    low = eq(stereo_noise(n, r, -6.0, corr=0.7), [(20, -12), (60, 0), (150, -2), (400, -9), (1000, -17), (4000, -30)])
    low = low * swell(n, r, 1.5, 0.35)[:, None]
    mid = eq(stereo_noise(n, r, -3.0, corr=0.2), [(100, -30), (400, -4), (1200, 0), (3500, -6), (8000, -26)])
    mid = mid * (0.7 + 0.3 * swell(n, r, 3.0, 0.5))[:, None]
    rings = np.zeros((n, 2))
    for k in range(18):
        sn = N(0.3)
        st = T(sn)
        f = 3200 * (350 / 3200) ** (st / 0.3)
        w = svf(white(sn, r), f, 2.5, "bp") * np.sin(np.pi * st / 0.3) ** 2
        place(rings, w, k * dur / 18.0 + 0.11, pan=(-0.6 if k % 2 else 0.6), wrap=True)
    tone = sum(np.sin(TWO_PI * lockf(f0, dur) * t + i) * a for i, (f0, a) in enumerate([(92, 1), (184.5, 0.6), (277, 0.3)]))
    tone = tone * (0.7 + 0.3 * lfo(n, 12, 0.1))
    y = rn(low, -12) + rn(mid, -20) + rn(rings, -26) + pan(rn(tone, -34), 0.0)
    return sat(y * 1.2, 1.4)


@sound("sfx.launch_roar", raw=True, loop=True, stereo=True, atten=48, note="the 6 s seamless roaring ascent that sfx.launch ends on; loop it until cut")
def launch_roar(r):
    c = _roar_cycle(np.random.default_rng(777))
    return c * db(ROAR_LUFS - lufs(c))


@sound("sfx.launch", raw=True, stereo=True, atten=64, note="catapult: a brutal kick, then a roaring ascent (a rising turbine tone and quickening ring-lights over the roar); it ends in phase with the start of sfx.launch_roar, so play that straight after and loop it until cut")
def launch(r):
    cyc = _roar_cycle(np.random.default_rng(777))
    cyc = cyc * db(ROAR_LUFS - lufs(cyc))
    pre = N(0.8)
    intro = cyc[-pre:] * np.linspace(0.15, 1.0, pre)[:, None] ** 1.5
    y = np.concatenate([intro, cyc])
    n = len(y)
    kick = np.zeros(n)
    place(kick, thump(1.6, 82, 26, 0.05, 0.55, 0.001, 0.45), 0.0)
    place(kick, 0.8 * pk(plate(58, 2.0, r, 0.7, 14, 12), -4), 0.0)
    place(kick, pk(burst(0.25, r, 80, 5000, 0.04, 0.0004), -3), 0.0)
    place(kick, pk(lp(white(N(1.0), r), 500, 2) * expo(N(1.0), 0.25, 0.002), -6), 0.0)
    ks_ = sat(kick[:, None] * np.ones((1, 2)) * 0.7, 2.0)
    ks_ = reverb(ks_, space("tunnel"), wet=0.35, dry=1.0, n=n)
    ks_ = pk(ks_, -2.0)
    # the ascent: a turbine tone and quickening ring-light whooshes that die away exactly as the loop (sfx.launch_roar) takes over
    t = T(n)
    f = 90 * (700 / 90) ** (np.clip(t / 5.5, 0, 1) ** 1.2)
    asc_env = np.interp(t, [0, 0.4, 3.0, 5.5, 6.8], [0, 0.35, 1.0, 0.8, 0.0])
    asc = (np.sin(phase_of(f)) + 0.5 * np.sin(2 * phase_of(f) + 1) + 0.25 * np.sin(3 * phase_of(f) + 2)) * asc_env
    asc = asc / np.max(np.abs(asc)) * 0.12 * db(ROAR_LUFS + 17.0)
    st_ = np.zeros((n, 2))
    tt_ = 0.5
    while tt_ < 5.8:
        sn = N(0.3)
        sw_ = svf(white(sn, r), 3000 * (350 / 3000) ** (T(sn) / 0.3), 2.5, "bp") * np.sin(np.pi * T(sn) / 0.3) ** 2
        place(st_, sw_ * np.interp(tt_, [0, 3, 5.8, 6.8], [0.4, 1.0, 0.7, 0.0]), tt_, pan=r.uniform(-0.7, 0.7))
        tt_ += 1.0 / np.interp(tt_, [0, 5.8], [2.0, 6.0])
    st_ = st_ / (np.max(np.abs(st_)) + 1e-9) * 0.05 * db(ROAR_LUFS + 17.0)
    return y + ks_ + np.stack([asc, asc], axis=1) + st_

@sound("sfx.launch_arrive", peak=-3.0, atten=64, note="the lift locking at the top: clang, clamps, hydraulic hiss, groaning settle, open-air wind coming in")
def launch_arrive(r):
    n = N(5.5)
    t = T(n)
    y = np.zeros(n)
    place(y, pk(thump(1.2, 85, 36, 0.04, 0.35, 0.002), 0), 0.0)
    place(y, pk(plate(95, 3.5, r, 1.2, 22, 14), -2), 0.0)
    place(y, pk(steel_bar(210, 3.0, r, 1.4), -7), 0.0)
    place(y, pk(burst(0.15, r, 200, 6500, 0.025, 0.0004), -4), 0.0)
    for t0, f in [(0.25, 150), (0.52, 180), (0.8, 130)]:
        place(y, pk(clunk(f, 0.5, r, 0.07, 0.9), -8), t0)
    place(y, pk(hiss(1.8, r, 2000, 8000, 0.05, 0.7), -18), 0.3)
    for t0, f0, f1 in [(1.2, 90, 60), (2.2, 70, 100)]:
        place(y, pk(creak(1.0, r, f0, f1, 0.7, 2.4), -15), t0)
    wn = bp(white(n, r), 250, 1500, 2) * swell(n, r, 0.8, 0.8, False) * np.interp(t, [0, 0.5, 2.5, 5.5], [0, 0.5, 1.0, 0.8])
    y += pk(wn, -18)
    place(y, pk(debris(2.0, r, 30, 2, 500, 4000), -24), 0.3)
    return reverb(y, space("open", stereo=False), wet=0.4, dry=1.0, n=n)


@sound("sfx.barrier", peak=-8.0, atten=48, note="a blow stopping dead on a wall of light: muffled thwomp, a ringing cluster of glassy partials, combed shimmer")
def barrier(r):
    n = N(3.6)
    t = T(n)
    y = np.zeros(n)
    place(y, pk(lp(thump(0.4, 120, 55, 0.02, 0.1, 0.002), 300), -4), 0.0)
    for f, a, tau in [(1180, 1.0, 1.4), (1710, 0.8, 1.1), (2530, 0.6, 0.9), (3810, 0.4, 0.7), (5290, 0.3, 0.5)]:
        place(y, modal([f, f * 1.0029], [tau, tau], [a, a * 0.8], 3.4, r, attack=0.002) * 0.4, 0.0)
    sh = circ(lambda z: delayloop(z, SR / 330.0, 0.8, 0.2), white(N(3.0), r))
    sh = bp(sh, 2500, 9000, 2) * swell(N(3.0), r, 12, 1.0, False) * expo(N(3.0), 0.9, 0.01)
    place(y, pk(sh, -16), 0.0)
    ch = np.sin(phase_of(np.interp(T(N(0.35)), [0, 0.35], [900, 3600]))) * np.hanning(N(0.35) * 2)[:N(0.35)]
    place(y, pk(ch, -18), 0.0)
    place(y, pk(burst(0.03, r, 1500, 9000, 0.005, 0.0003), -6), 0.0)
    return reverb(y, space("plate", stereo=False), wet=0.3, dry=1.0, n=n)


@sound("sfx.core_crack", peak=-3.0, atten=48, note="a big crystalline sphere splitting: accelerating cracks with glassy rings, ice-squeals, a final split and thud, tinkling shards")
def core_crack(r):
    n = N(3.0)
    y = np.zeros(n)
    for i, (t0, g) in enumerate([(0.0, 0.35), (0.16, 0.45), (0.31, 0.55), (0.43, 0.7), (0.54, 0.9), (0.62, 1.0)]):
        place(y, pk(burst(0.04, r, 1500, 10000, 0.006, 0.0002), -3) * g, t0)
        place(y, pk(glass_ring(r.uniform(2600, 7200), 0.5, r, 0.14), -8) * g, t0)
        place(y, pk(squeal(0.12, r, r.uniform(1400, 2200), r.uniform(2800, 4200), 1.0, 0.01), -14) * g, t0)
    t1 = 0.72
    place(y, pk(burst(0.35, r, 300, 9000, 0.07, 0.0003), -1), t1)
    place(y, pk(thump(1.0, 90, 38, 0.04, 0.3, 0.002), 0), t1)
    place(y, pk(plate(140, 1.5, r, 0.45, 18, 12), -5), t1)
    place(y, pk(glass_shatter(r, 2.0), -6), t1)
    place(y, pk(ticks(2.2, r, 90, 2500, 9500, 0.002, 4, 1.5), -13), t1 + 0.1)
    place(y, pk(colored(N(1.8), r, -6, hi=200) * expo(N(1.8), 0.5, 0.01), -8), t1)
    return reverb(y, space("room", stereo=False), wet=0.3, dry=1.0, n=n)


@sound("sfx.beam_charge", lufs=-22.0, stereo=True, atten=48, note="2 s rising: whine, accelerating discharge ticks, a deep swell, cut off at its peak")
def beam_charge(r):
    dur = 2.0
    n = N(dur)
    t = T(n)
    p = t / dur
    f = 260 * (6500 / 260) ** (p ** 1.3)
    w = whine(dur, f, r, harm=3, level=1.0, jitter=0.004)
    sw = pk(colored(n, r, -6, hi=200) * p ** 1.5, -6)
    nz = bp(white(n, r), 1200, 9500, 2) * p ** 2
    tk = np.zeros(n)
    tt = 0.0
    while tt < dur:
        tt += r.exponential(1.0 / np.interp(tt, [0, 2], [10, 220]))
        place(tk, click(r, r.uniform(2000, 7000), 0.0015) * r.uniform(0.3, 1), tt)
    y = pk(w, -4) * (0.3 + 0.7 * p) + sw + pk(nz, -20) + pk(tk, -17)
    st = widen(y, r, 0.5)
    return fade(st, 0.01, 0.015)


@sound("sfx.beam_fire", peak=-2.0, stereo=True, atten=96, note="a particle beam: crack and sub boom, then a roaring FM and sawtooth core with sizzle, decaying through city echoes")
def beam_fire(r):
    dur = 5.0
    n = N(dur)
    t = T(n)
    e = np.interp(t, [0, 0.02, 0.15, 1.6, 2.4, 5.0], [0, 1, 0.8, 0.7, 0.2, 0.0])
    core = fm(np.full(n, 220.0), 1.0, 3.0 + 2 * np.sin(TWO_PI * 5 * t), n) + 0.6 * hosc(np.full(n, 110.0), n, nh=24, rolloff=1.0)
    core = svf(core, np.full(n, 2600.0), 0.9, "lp")
    siz = hp(white(n, r), 2500, 2) * (0.6 + 0.4 * np.clip(drift(n, r, 40, False), -1, 1))
    sub = np.sin(phase_of(np.interp(t, [0, 0.3, 5], [90, 48, 40])))
    y = pk(core, -4) * e + pk(siz, -12) * e + pk(sub, -3) * np.interp(t, [0, 0.01, 0.3, 3.0, 5.0], [0, 1, 0.8, 0.3, 0])
    y[:N(0.15)] += pk(burst(0.15, r, 200, 9000, 0.03, 0.0003), -2)
    y += pk(fit(thump(1.5, 95, 28, 0.08, 0.5, 0.002, 0.4), n), -2)
    y = sat(y * 0.7, 1.8)
    st = widen(y, r, 0.45)
    st = reverb(st, space("city"), wet=0.3, dry=1.0, n=n)
    return fade(st, 0.0, 0.6)


@sound("sfx.giant_hit", peak=-3.0, atten=64, note="the giant taking a blow: body thud, wet slap, armour plate, a short organic grunt, falling debris")
def giant_hit(r):
    n = N(3.0)
    y = np.zeros(n)
    place(y, pk(thump(1.0, 88, 36, 0.04, 0.22, 0.002, 0.3), 0), 0.0)
    place(y, pk(lp(white(N(0.3), r), 1300, 2) * expo(N(0.3), 0.07, 0.001), -6), 0.0)
    place(y, pk(plate(250, 1.6, r, 0.45, 20, 12), -4), 0.01)
    place(y, pk(burst(0.05, r, 600, 8000, 0.007, 0.0003), -5), 0.0)
    gr = choir(np.interp(T(N(0.9)), [0, 0.2, 0.9], [60, 75, 50]), 0.9, r, "oh", 3, 30, 0.03, 4.0, 0.25, None, "ah", np.linspace(0, 1, N(0.9)))
    gr *= np.interp(T(N(0.9)), [0, 0.06, 0.3, 0.9], [0, 1, 0.6, 0])
    place(y, pk(gr, -9), 0.08)
    place(y, pk(debris(2.2, r, 40, 2, 500, 5000), -17), 0.1)
    return reverb(y, space("city", stereo=False), wet=0.35, dry=1.0, n=n)


@sound("sfx.giant_punch", peak=-2.0, atten=64, note="the giant landing a blow: swinging whoosh, a heavy concussion, plate crack, a small blast of dust and rattle")
def giant_punch(r):
    n = N(3.0)
    t = T(n)
    y = np.zeros(n)
    wn = N(0.4)
    w = svf(white(wn, r), np.exp(np.linspace(np.log(200), np.log(1500), wn)), 1.1, "bp") * np.sin(np.pi * np.linspace(0, 1, wn) ** 0.8) ** 2
    place(y, pk(w, -9), 0.0)
    t0 = 0.4
    place(y, pk(thump(1.3, 100, 34, 0.05, 0.3, 0.002, 0.35), 0), t0)
    place(y, pk(plate(190, 1.8, r, 0.55, 22, 14), -3), t0)
    place(y, pk(burst(0.15, r, 300, 8500, 0.02, 0.0003), -2), t0)
    place(y, pk(blast(r, 2.4, size=0.4, sub=(70, 40), crack=0.0, drive=1.6, debris_level=0.6), -7), t0)
    place(y, pk(debris(2.0, r, 70, 4, 800, 6500), -16), t0 + 0.05)
    return reverb(y, space("city", stereo=False), wet=0.4, dry=1.0, n=n)


@sound("sfx.cross", lufs=-26.0, stereo=True, stream=True, atten=96, note="a pillar of light: a pure sine climbing three octaves, a synthetic vowel choir on an open D chord, shimmer, cathedral reverb")
def cross(r):
    dur = 13.0
    n = N(dur)
    t = T(n)
    p = np.clip(t / 7.0, 0, 1)
    f = 146.83 * 8 ** (p ** 1.2)
    ph = phase_of(f)
    tone = np.sin(ph) + 0.12 * np.sin(2 * ph)
    tone *= np.interp(t, [0, 0.8, 7.0, 10.5, 13.0], [0, 0.5, 1.0, 0.7, 0])
    fifth = np.sin(phase_of(f * 1.5)) * np.interp(t, [0, 3.0, 7.0, 10.5, 13.0], [0, 0, 0.5, 0.4, 0])
    y = np.zeros((n, 2))
    y += pan(tone, 0.0) * 0.8 + pan(fifth, 0.2) * 0.4
    chord = [(146.83, -0.5), (220.25, 0.4), (293.66, -0.2), (367.0, 0.5), (440.5, -0.7)]
    for f0, pn in chord:
        c = choir(f0, dur, r, "ah", 4, 12, 0.005, 5.0, 0.02, None, "oh", np.interp(t, [0, 7, 13], [0, 0.4, 0.8]))
        c *= np.interp(t, [0, 1.8, 7.0, 10.0, 13.0], [0, 0.1, 1.0, 0.8, 0.0])
        y += pan(c, pn) * 0.5
    sh = np.zeros(n)
    for k in (4, 6, 8, 10):
        sh += np.sin(TWO_PI * 146.83 * k * t + k) * (0.6 + 0.4 * np.sin(TWO_PI * (0.3 + 0.1 * k) * t)) / k
    sh *= np.interp(t, [0, 4.0, 8.0, 12.0, 13.0], [0, 0, 1, 0.3, 0])
    y += widen(sh, r, 0.8) * 0.35
    y = eq(y, [(40, -12), (100, 0), (6000, 0), (12000, -10)], circ=False)
    st = reverb(y, space("cathedral"), wet=0.55, dry=0.75, n=n)
    return fade(st, 0.1, 1.5)


@sound("sfx.heartbeat", peak=-8.0, loop=True, atten=16, note="10 s, nine lub-dubs at 54 bpm with a little irregularity, chest-muffled")
def heartbeat(r):
    dur = 10.0
    n = N(dur)
    y = np.zeros(n)
    per = dur / 9.0
    for k in range(9):
        t0 = 0.3 + k * per + r.normal(0, 0.006)
        lub = thump(0.4, 64, 40, 0.04, 0.09, 0.006, 0.2) + 0.25 * lp(white(N(0.4), r), 160, 2) * expo(N(0.4), 0.05, 0.004)
        dub = 0.65 * thump(0.35, 80, 52, 0.035, 0.07, 0.006, 0.2) + 0.15 * lp(white(N(0.35), r), 180, 2) * expo(N(0.35), 0.04, 0.004)
        place(y, lub, t0, 1.0, wrap=True)
        place(y, dub, t0 + 0.3 + r.normal(0, 0.004), 1.0, wrap=True)
    return eq(y, [(25, -6), (60, 0), (120, 0), (250, -18), (600, -40)])


@sound("sfx.speak_chime", peak=-16.0, atten=16, fout=0.05, note="'your turn': two soft rising notes A5 -> E6, a gentle marimba-like timbre, tiny room; deliberately unlike every other chime")
def speak_chime(r):
    n = N(1.4)
    y = np.zeros(n)
    for t0, f, d in [(0.0, 880.0, 0.55), (0.17, 1318.5, 0.85)]:
        note = modal([f, f * 2.0, f * 3.99], [d, d * 0.4, d * 0.12], [1.0, 0.18, 0.04], 1.2, None, attack=0.008)
        place(y, note, t0)
    y = eq(y, [(300, -12), (700, 0), (6000, 0), (9000, -10)], circ=False)
    return reverb(y, space("booth", stereo=False), wet=0.2, dry=1.0, n=n)
