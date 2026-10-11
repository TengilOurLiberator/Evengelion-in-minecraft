"""sfx_world.py - effects of the outside world: the platform and phone, the Angel, aircraft, the car, the mine."""
from dsp import *
from blocks import *
from reg import sound


@sound("sfx.card", peak=-4.0, stereo=True, atten=32, note="the single low hit under a title card: sub boom, membrane, beater, dark hall")
def card(r):
    n = N(5.0)
    y = thump(5.0, 58, 34, 0.12, 1.5, 0.004, 0.3)
    y += 0.55 * thump(5.0, 41, 41, 1.0, 2.4, 0.015, 0.1)
    y += 0.7 * pk(fit(drum(55, 3.0, r, tau=1.1, drop=1.45, tau_drop=0.08), n), -3)
    y += pk(fit(burst(0.35, r, 90, 2500, 0.04, 0.0005), n), -9)
    y += pk(fit(lp(white(N(1.2), r), 380, 2) * expo(N(1.2), 0.4, 0.01), n), -12)
    y = sat(y * 0.7, 1.4)
    st = reverb(y, space("hall"), wet=0.55, dry=0.9, n=n)
    return fade(st, 0.0, 1.5)


@sound("sfx.phone_pickup", peak=-14.0, atten=12, note="hook-switch ticks, plastic handset, cord rustle")
def phone_pickup(r):
    n = N(0.9)
    y = np.zeros(n)
    place(y, click(r, 2300, 0.0025), 0.0, 0.8)
    place(y, click(r, 1900, 0.0025), 0.045, 0.6)
    place(y, thump(0.12, 190, 110, 0.02, 0.035), 0.07, 0.8)
    place(y, plate(950, 0.3, r, 0.05, 8, 6.0), 0.07, 0.5)
    rus = bp(white(N(0.4), r), 500, 2400, 2) * swell(N(0.4), r, 14, 1.0, False) * np.sin(np.pi * T(N(0.4)) / 0.4)
    place(y, pk(rus, -14), 0.16)
    return y


@sound("sfx.phone_hangup", peak=-13.0, atten=12, note="handset back on its cradle: plastic clack, bounce, switch click")
def phone_hangup(r):
    n = N(0.7)
    y = np.zeros(n)
    place(y, thump(0.1, 220, 120, 0.015, 0.03), 0.0, 1.0)
    place(y, plate(1250, 0.25, r, 0.04, 8, 6.0), 0.0, 0.9)
    place(y, plate(900, 0.2, r, 0.03, 6, 5.0), 0.075, 0.45)
    place(y, click(r, 2100, 0.003), 0.03, 0.7)
    place(y, click(r, 2600, 0.002), 0.11, 0.4)
    return y


@sound("sfx.birds_up", peak=-15.0, atten=24, note="a flock taking off: ~30 birds of wing-flap flutter plus startled calls, wire twang")
def birds_up(r):
    n = N(4.5)
    y = np.zeros(n)
    flap = lambda: bp(white(N(0.05), r), 450, 2300, 2) * np.hanning(N(0.05))
    for b in range(30):
        t0 = 0.05 + 0.9 * r.random() ** 1.3
        life = r.uniform(1.2, 3.4)
        rate = r.uniform(8, 13)
        t = t0
        while t < t0 + life:
            fade_ = (1 - (t - t0) / life) ** 1.2
            place(y, flap() * r.uniform(0.5, 1.0) * fade_, t)
            t += 1.0 / rate * r.uniform(0.8, 1.2)
        if r.random() < 0.45:
            place(y, bird_phrase(r) * 0.8 * (r.uniform(0.3, 1.0)), t0 + r.uniform(0.0, 0.5))
    y = svf(y, 7000 * np.exp(-T(n) / 3.0) + 1500, 0.6, "lp")
    place(y, ks(hp(white(N(0.01), r), 300, 1) * 2, 330, 1.5, 0.995, 0.45) * 0.5, 0.0)
    return y


@sound("sfx.jolt", peak=-4.0, atten=48, note="ground shock: sub thump, rolling rumble, resonant window panes chattering")
def jolt(r):
    n = N(3.0)
    y = 1.0 * fit(thump(1.5, 60, 28, 0.1, 0.35, 0.003, 0.35), n)
    y += pk(colored(n, r, -6, hi=150) * expo(n, 0.8, 0.01), -5)
    chat = np.clip(0.5 + 0.9 * drift(n, r, 45, False), 0, 2) * expo(n, 0.7, 0.04)
    gl = sum(svf(white(n, r), f, 25, "bp") for f in (730, 1180, 1650, 2400, 3100))
    y += pk(gl * chat, -9)
    for t0 in (0.05, 0.3, 0.6, 0.95, 1.4):
        place(y, pk(glass_ring(r.uniform(900, 2800), 0.6, r, 0.3), -14), t0 + r.uniform(0, 0.1))
    return sat(y * 0.9, 1.2)


@sound("sfx.footfall_giant", peak=-4.0, atten=96, note="a colossal step far away: felt sub first, then the crunch, then the ground settling")
def footfall_giant(r):
    n = N(6.0)
    y = 1.0 * fit(thump(2.5, 38, 24, 0.25, 0.9, 0.03, 0.5), n)
    place(y, 0.3 * thump(2.0, 36, 24, 0.2, 0.7, 0.03, 0.4), 0.9)
    cr = burst(0.9, r, 90, 1400, 0.25, 0.005) * np.clip(0.5 + drift(N(0.9), r, 60, False), 0, 2)
    place(y, pk(cr, -4), 0.18)
    place(y, pk(debris(3.0, r, rate=60, rate_end=2, lo=300, hi=3500), -17), 0.3)
    place(y, pk(colored(N(4.5), r, -6, hi=110) * expo(N(4.5), 1.4, 0.15), -8), 0.2)
    return air_absorb(y, 2.5)


@sound("sfx.siren", lufs=-26.0, loop=True, stream=True, atten=64, note="city air-raid siren, two 10 s rise-and-fall cycles, rotor chop, echoing off the streets")
def siren(r):
    dur = 20.0
    n = N(dur)
    t = T(n)
    p = (t % 10.0) / 10.0
    ss = lambda x: x * x * (3 - 2 * x)
    shape = np.where(p < 0.45, ss(np.clip(p / 0.45, 0, 1)), 1 - ss(np.clip((p - 0.45) / 0.55, 0, 1)))
    shape = irfft(rfft(shape) * np.exp(-(rfftfreq(n, 1 / SR) / 0.9) ** 2), n)            # motor inertia
    f = 300 + 190 * shape
    f = f * (1 + 0.003 * lfo(n, 37))
    y = siren_tone(f, n)
    y = y * (0.65 + 0.35 * shape)
    chop = csvf(white(n, r), 1300 + 600 * shape, 1.5, "bp") * (0.6 + 0.4 * np.sin(phase_of(f * 6, True)))
    y = y / np.std(y) + 0.35 * chop / np.std(chop)
    y = eq(y, [(60, -20), (150, -8), (300, 0), (1000, -3), (3000, -16), (8000, -40)])
    return 0.55 * y + 1.0 * cconv(y, space("city", stereo=False))


@sound("sfx.jet_pass", peak=-8.0, atten=96, note="Doppler fly-past: turbine roar, tonal whine and rumble all riding the Doppler curve")
def jet_pass(r):
    n = N(7.0)
    t = T(n)
    v, d0, t0, c = 190.0, 320.0, 3.0, 343.0
    x = v * (t - t0)
    R = np.sqrt(d0 ** 2 + x ** 2)
    vr = v * x / R
    dop = 1.0 / (1.0 + vr / c)
    amp = d0 / R
    rough = eq(white(n, r), [(60, -30), (250, -8), (1000, 0), (3500, -6), (9000, -22)])
    y = svf(rough, 3200 * dop, 0.8, "lp") * 1.0
    y = y / np.std(y)
    ph = phase_of(1150 * dop)
    whine = (np.sin(ph) + 0.4 * np.sin(2 * ph) + 0.2 * np.sin(3 * ph)) * (1 + 0.1 * drift(n, r, 20, False))
    low = np.sin(phase_of(110 * dop)) + 0.5 * np.sin(phase_of(220 * dop) + 1)
    y = (0.9 * y + 0.35 * whine + 0.4 * low) * amp ** 1.3
    wake = colored(n, r, -6, hi=300) * np.where(t > t0 + 0.3, np.exp(-(t - t0 - 0.3) / 1.2), 0) * np.minimum(1, (t - t0) / 0.5).clip(0, 1)
    y += pk(wake, -9) * amp.max() * 0.4
    return svf(y, 9000 * amp ** 0.5 + 800, 0.6, "lp")


@sound("sfx.gunfire_far", peak=-10.0, atten=96, note="three bursts of aircraft cannon far off: dull thump + crack per round, open-air echoes")
def gunfire_far(r):
    n = N(6.0)
    y = np.zeros(n)
    shot = mix(thump(0.12, 140, 70, 0.012, 0.03, 0.0008), 0.5 * pk(burst(0.05, r, 600, 3800, 0.008, 0.0004), 0))
    for t0, ln in [(0.4, 0.9), (2.3, 1.3), (4.0, 0.7)]:
        t = t0
        while t < t0 + ln:
            place(y, shot * r.uniform(0.6, 1.0), t + r.normal(0, 0.0015))
            t += 1.0 / 50.0 * r.uniform(0.92, 1.08)
    y = svf(y, 2600, 0.7, "lp")
    return 0.8 * y + 0.5 * reverb(y, space("open", stereo=False), wet=1.0, dry=0.0, n=n)


@sound("sfx.explosion_far", peak=-6.0, atten=128, note="a blast several kilometres off: delayed, dulled, long hill echoes")
def explosion_far(r):
    n = N(9.0)
    y = blast(r, 9.0, size=0.9, sub=(60, 22), crack=0.5, dist=0.8, tail=1.2, bright=0.6, drive=1.2)
    return reverb(y, space("open", stereo=False), wet=0.5, dry=1.0, n=n)


@sound("sfx.explosion_near", peak=-1.5, atten=96, note="a close blast: crack, fireball, sub, debris, city echoes")
def explosion_near(r):
    n = N(10.0)
    y = blast(r, 10.0, size=1.0, sub=(75, 24), crack=1.2, dist=0.0, tail=1.0, bright=1.0, drive=2.0)
    return reverb(y, space("city", stereo=False), wet=0.5, dry=1.0, n=n)


@sound("sfx.crash", peak=-3.0, atten=96, note="aircraft into ground: falling engine scream, impact, metal pile, scrape, fireball whump, fire crackle")
def crash(r):
    n = N(8.0)
    t = T(n)
    y = np.zeros(n)
    an = N(1.35)
    at = T(an)
    f = 1900 * np.exp(-at / 0.9) + 650
    scream = whine(1.35, f, r, harm=4, level=1.0) + 0.8 * svf(white(an, r), f * 1.5, 1.0, "bp")
    y[:an] += pk(scream * (at / 1.35) ** 1.6, -6)
    t0 = 1.3
    place(y, pk(blast(r, 5.0, size=0.45, sub=(70, 30), crack=1.0, drive=1.8, debris_level=0.6), -1), t0)
    place(y, pk(metal_crash(2.5, r, 1.0, 22, 100, 1800), -3), t0)
    sl = scrape(1.9, r, 200, 2600) * np.linspace(1, 0.05, N(1.9)) ** 1.5
    place(y, pk(sl, -9), t0 + 0.05)
    place(y, pk(colored(N(3.0), r, -6, lo=25, hi=400) * expo(N(3.0), 0.6, 0.02), -4), t0 + 0.15)
    fire = ticks(6.3, r, 45, 1500, 6000, 0.003, 8, 1.0, (0.1, 0.8))
    fire = fire * expo(N(6.3), 3.0) * 1.0
    place(y, pk(fire, -22), 1.7)
    place(y, pk(hiss(6.0, r, 900, 5000, 0.5, None, 1.0) * expo(N(6.0), 2.5), -30), 1.7)
    return y


@sound("sfx.car_arrive", peak=-10.0, atten=48, note="engine rising as it approaches, tyre squeal and scrub, suspension settling, idling")
def car_arrive(r):
    n = N(6.5)
    t = T(n)
    rpm = np.interp(t, [0, 1.5, 2.5, 2.9, 3.9, 6.5], [1500, 3000, 3800, 3300, 900, 850])
    eng = engine(6.5, rpm, r, 4, 0.7, 0.8)
    amp = np.interp(t, [0, 2.4, 2.9, 3.9, 6.5], [0.05, 0.8, 1.0, 0.6, 0.35]) ** 1.2
    tyre = bp(white(n, r), 700, 3200, 2) * np.interp(t, [0, 1.0, 2.4, 2.45, 3.9, 4.0], [0.02, 0.2, 0.3, 0.0, 0.0, 0.0])
    y = pk(eng, -2) * amp + pk(tyre, -10)
    sq = np.zeros(n)
    sn = N(1.45)
    place(sq, squeal(1.45, r, 1100, 880, 1.0, 0.02) * 0.5, 2.45)
    place(sq, squeal(1.3, r, 1650, 1300, 1.0, 0.03) * 0.3, 2.55)
    place(sq, pk(bp(white(sn, r), 1500, 5500, 2) * np.interp(T(sn), [0, 0.1, 1.2, 1.45], [0, 1, 0.7, 0]), -9), 2.45)
    y += pk(sq, -5)
    place(y, thump(0.4, 90, 48, 0.03, 0.12, 0.003) * 0.8, 3.92)
    place(y, pk(plate(380, 0.8, r, 0.25, 14, 8), -9), 3.92)
    return y


@sound("sfx.car_door", peak=-12.0, atten=24, note="door slam: body thump, panel ring, double latch click, seal puff")
def car_door(r):
    n = N(1.2)
    y = np.zeros(n)
    place(y, thump(0.3, 150, 75, 0.02, 0.07, 0.001), 0.0, 1.0)
    place(y, pk(plate(310, 0.9, r, 0.16, 16, 9), -5), 0.0, 1.0)
    place(y, pk(plate(850, 0.4, r, 0.08, 10, 8), -9), 0.0, 1.0)
    place(y, click(r, 2600, 0.002), 0.028, 0.7)
    place(y, click(r, 3200, 0.0015), 0.05, 0.5)
    place(y, pk(lp(white(N(0.15), r), 1600, 2) * expo(N(0.15), 0.04), -16), 0.01)
    place(y, pk(lp(white(N(0.3), r), 300, 2) * expo(N(0.3), 0.1), -10), 0.0)
    return y


@sound("sfx.car_start", peak=-12.0, atten=24, note="starter cranking, engine catching, settling to idle")
def car_start(r):
    n = N(3.5)
    t = T(n)
    y = np.zeros(n)
    cn = N(1.2)
    ct = T(cn)
    crank_rate = 4.5
    comp = (0.5 + 0.5 * np.sin(TWO_PI * crank_rate * ct)) ** 2
    f = 140 + 50 * comp
    cr = whine(1.2, f, r, harm=4, level=0.8) * (0.5 + 0.5 * comp) + 0.4 * lp(white(cn, r), 900, 2) * comp
    y[:cn] += pk(cr * np.minimum(1, ct / 0.03) * np.minimum(1, (1.2 - ct) / 0.1), -6)
    rpm = np.interp(t, [1.1, 1.3, 1.6, 2.2, 3.5], [250, 900, 1100, 880, 850])
    eng = engine(3.5, rpm, r, 4, 0.5, 1.4)
    e = np.interp(t, [1.1, 1.2, 1.7, 3.0, 3.5], [0, 0.7, 1.0, 0.9, 0.0])
    y += pk(eng, -5) * e
    place(y, thump(0.3, 70, 40, 0.04, 0.09), 1.18, 0.7)
    return y


@sound("sfx.mine", peak=-1.0, ceiling=-1.08, stereo=True, atten=128, fin=0.0, fout=0.0,
       note="0.0 s rising whine cut dead at 0.4 s; digital silence 0.4-2.4 s; the blast at 2.4 s with a long rolling tail")
def mine(r):
    n = N(9.0)
    y = np.zeros((n, 2))
    wn = N(0.4)
    wt = T(wn)
    f = 700 * (6200 / 700) ** ((wt / 0.4) ** 1.3)
    ph = phase_of(f)
    w = (np.sin(ph) + 0.35 * np.sin(2 * ph + 0.4) + 0.12 * np.sin(3 * ph)) + 0.08 * svf(white(wn, r), f, 6, "bp")
    w = w * (0.08 + 0.92 * (wt / 0.4) ** 1.2)
    w[-N(0.0015):] *= np.linspace(1, 0, N(0.0015))
    w[0] = 0.0
    y[:wn, 0] += 0.5 * w
    y[:wn, 1] += 0.5 * np.roll(w, 7)
    bn = N(6.6)
    b = blast(r, 6.6, size=2.2, sub=(62, 16), crack=1.3, dist=0.0, tail=0.95, bright=1.2, drive=1.9, debris_level=0.5)
    b = np.concatenate([[0.0], b[:-1]])
    st = widen(b, r, 0.5)
    mix = np.minimum(1, T(bn) / 0.12)[:, None]
    bs = np.stack([b, b], axis=1) * (1 - mix) + st * mix
    bs = bs * (1 + 0.3 * np.stack([np.sin(TWO_PI * 0.4 * T(bn)), -np.sin(TWO_PI * 0.4 * T(bn))], axis=1) * mix)
    bs = reverb(bs, space("city"), wet=0.35, dry=1.0, n=bn)
    bs[:N(0.0003)] = 0.0
    tail_fade = np.minimum(1, (9.0 - 2.4 - T(bn)) / 1.4).clip(0, 1)
    bs *= tail_fade[:, None]
    y[N(2.4):N(2.4) + bn] += bs
    y[N(0.4):N(2.4)] = 0.0
    y[-1] = 0.0
    return y, {"whine_end_s": 0.4, "silence_start_s": 0.4, "silence_end_s": 2.4, "blast_s": 2.4}


@sound("sfx.ears_ringing", lufs=-33.0, stereo=True, atten=32, note="8 s fading tinnitus: two near-detuned tones per ear, pressure thrum, a trace of hiss")
def ears_ringing(r):
    n = N(8.0)
    t = T(n)
    e = env([(0, 0), (0.08, 1.0), (2.0, 0.5), (5.0, 0.08), (7.9, 0.0005), (8.0, 0.0)], n, "exp")
    e[:N(0.08)] = np.linspace(0, 1, N(0.08))
    waver = 1 + 0.15 * np.sin(TWO_PI * 0.31 * t + 1) + 0.08 * np.sin(TWO_PI * 0.77 * t)
    L = np.sin(TWO_PI * 4230 * t) + 0.5 * np.sin(TWO_PI * 4262 * t + 1) + 0.25 * np.sin(TWO_PI * 6410 * t)
    R = np.sin(TWO_PI * 4410 * t) + 0.5 * np.sin(TWO_PI * 4388 * t + 2) + 0.25 * np.sin(TWO_PI * 3120 * t)
    hs = hp(white(n, r), 6000, 2) * 0.05
    th = lp(white(n, r), 90, 2) * env([(0, 1), (1.5, 0.0), (8, 0)], n)
    return np.stack([L * waver * e + hs * e + th * 0.4, R * waver * e + np.roll(hs, 50) * e + np.roll(th, 30) * 0.4], axis=1)


@sound("sfx.car_roll", peak=-4.0, atten=64, note="a car going over twice: four body hits with glass, a long slide, settling clinks and steam")
def car_roll(r):
    n = N(5.0)
    y = np.zeros(n)
    for t0, g, f in [(0.12, 1.0, 170), (0.55, 0.8, 130), (0.98, 1.0, 150), (1.45, 0.7, 120)]:
        h = mix(thump(0.4, 95, 45, 0.03, 0.12, 0.002), 0.7 * pk(plate(f, 1.3, r, 0.5, 26, 18), -3), 0.5 * pk(burst(0.3, r, 200, 5000, 0.05, 0.0008), -3))
        place(y, h * g, t0)
    place(y, pk(glass_shatter(r, 1.6), -4), 0.12)
    place(y, pk(glass_shatter(r, 1.4), -7), 0.98)
    sl = scrape(1.9, r, 180, 2400) * np.interp(T(N(1.9)), [0, 0.3, 1.9], [0.6, 1.0, 0.0])
    place(y, pk(sl, -8), 1.5)
    place(y, pk(colored(N(3.0), r, -6, lo=25, hi=300) * expo(N(3.0), 0.9, 0.02), -7), 1.5)
    place(y, pk(debris(4.5, r, 80, 2, 400, 5000), -14), 0.2)
    for t0 in (3.5, 3.85, 4.2):
        place(y, pk(steel_bar(r.uniform(500, 1500), 0.5, r, 0.15), -17), t0)
    place(y, pk(hiss(1.3, r, 2500, 8000, 0.05, 0.5), -24), 3.4)
    return y


@sound("sfx.car_drop", peak=-4.0, atten=48, note="the car falls back onto its wheels: suspension thud, springs, loose metal and glass, rocking creaks")
def car_drop(r):
    n = N(3.0)
    y = np.zeros(n)
    place(y, thump(0.45, 82, 44, 0.03, 0.14, 0.002) * 1.1, 0.0)
    place(y, pk(plate(260, 1.0, r, 0.38, 20, 14), -4), 0.0)
    place(y, pk(burst(0.25, r, 150, 4000, 0.05, 0.0008), -6), 0.0)
    place(y, pk(creak(0.55, r, 210, 120, 0.6, 3.0), -11), 0.04)
    place(y, pk(ks(hp(white(N(0.01), r), 200, 1), 95, 1.4, 0.996, 0.3), -9), 0.02)
    place(y, pk(debris(2.5, r, 60, 3, 800, 7000), -14), 0.1)
    place(y, pk(glass_shatter(r, 1.2), -16), 0.05)
    for t0, f0, f1 in [(0.5, 150, 180), (0.95, 175, 140)]:
        place(y, pk(creak(0.4, r, f0, f1, 0.5, 2.5), -17), t0)
    return y


@sound("sfx.car_alarms_far", peak=-20.0, atten=96, note="EXTRA (cue 1 'car alarms far off'): three distant car alarms of different patterns over each other, 9 s")
def car_alarms_far(r):
    n = N(9.0)
    y = np.zeros(n)
    for t0, f_lo, f_hi, per, cnt, lvl in [(0.0, 900, 1500, 0.62, 13, 1.0), (1.3, 1200, 2100, 0.41, 18, 0.7), (2.6, 700, 1100, 1.1, 6, 0.8)]:
        for j in range(cnt):
            sn = N(per * 0.55)
            tt = T(sn)
            f = f_lo * (f_hi / f_lo) ** (tt / (per * 0.55))
            ph = phase_of(f)
            tone = (np.sin(ph) + 0.4 * np.sin(2 * ph)) * np.sin(np.pi * tt / (per * 0.55)) ** 0.5
            place(y, tone * lvl, t0 + j * per)
    y = svf(y, 2400, 0.7, "lp")
    return 0.5 * y + 1.0 * reverb(y, space("city", stereo=False), wet=1.0, dry=0.0, n=n)