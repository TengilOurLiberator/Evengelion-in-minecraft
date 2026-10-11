"""music.py - the original score.  Spare, tense, cold; low drones, ostinatos, percussion, pads and bell tones, all
generated here from oscillators, noise, FM and modal bodies.  Nothing is sampled and nothing quotes any existing piece.

Key centre D (D1 = 36.7 Hz).  Every loopable cue is built periodically: events wrap round the end, steady tones are
locked to whole cycles, the reverb is circular.  Cues with a one-shot lead-in (decision, launch) also export their
looping end section as a second file (music.decision_loop, music.launch_loop): the last cycle of the long file is
the same audio as the loop, so playing the loop file straight after the long one is seamless.
"""
from dsp import *
from blocks import *
from reg import sound

_N = {"C": 0, "C#": 1, "Db": 1, "D": 2, "D#": 3, "Eb": 3, "E": 4, "F": 5, "F#": 6, "Gb": 6, "G": 7, "G#": 8, "Ab": 8, "A": 9, "A#": 10, "Bb": 10, "B": 11}


def hz(name):
    m = 12 * (int(name[-1]) + 1) + _N[name[:-1]]
    return 440.0 * 2 ** ((m - 69) / 12.0)


class Mix:
    """stereo dry bus + reverb send.  loop=True wraps events and uses circular reverb."""

    def __init__(self, dur, loop=False, offset=0.0):
        self.dur, self.loop, self.offset = dur, loop, offset     # offset: events are nudged late so no hit sits exactly on the loop join
        self.n = N(dur)
        self.dry = np.zeros((self.n, 2))
        self.send = np.zeros((self.n, 2))

    def add(self, sig, t, gain=1.0, pan=0.0, send=0.3):
        place(self.dry, sig, t + self.offset, gain, pan, wrap=self.loop)
        if send:
            place(self.send, sig, t + self.offset, gain * send, pan, wrap=self.loop)

    def full(self, sig, gain=1.0, send=0.3):
        sig = fit(sig, self.n)
        if sig.ndim == 1:
            sig = np.stack([sig, sig], axis=1)
        self.dry += gain * sig
        if send:
            self.send += gain * send * sig

    def render(self, space_name="hall", wet=1.0):
        ir = space(space_name)
        w = cconv(self.send, ir) if self.loop else reverb(self.send, ir, wet=1.0, dry=0.0, n=self.n)
        return self.dry + wet * w


def sine_lock(f, dur, t0=0.0, n=None):
    n = n or N(dur)
    return np.sin(TWO_PI * lockf(f, dur) * (T(n) - t0))


# ------------------------------------------------------------------ instruments
def mallet(f, dur, r, bright=1.0, tau=0.15):
    n = N(dur)
    t = T(n)
    idx = bright * 2.2 * np.exp(-t / 0.04)
    y = np.sin(phase_of(np.full(n, f)) + idx * np.sin(phase_of(np.full(n, f * 3.0))))
    y = y * np.exp(-t / tau) + 0.3 * np.sin(TWO_PI * f * t) * np.exp(-t / (tau * 1.6))
    y[:N(0.006)] += 0.15 * bright * lp(white(N(0.006), r), 4000, 1)
    return y


def bass_pluck(f, dur, r, tau=0.2, bright=0.6):
    n = N(dur)
    t = T(n)
    y = hosc(np.full(n, f), n, nh=14, rolloff=1.3)
    y = svf(y, f * (1.5 + 8 * bright * np.exp(-t / 0.05)), 0.9, "lp")
    return (y + 0.8 * np.sin(TWO_PI * f * t)) * np.exp(-t / tau) * np.minimum(1, t / 0.003)


def sub_pulse(f, dur, atk=0.12, tau=0.9):
    n = N(dur)
    t = T(n)
    ph = TWO_PI * f * t
    return sat(np.sin(ph) + 0.2 * np.sin(2 * ph), 1.6) * np.minimum(1, t / atk) ** 2 * np.exp(-t / tau)


def kick(r, f=115.0, body=50.0, dur=0.35, tau=0.1):
    return mix(thump(dur, f, body, 0.012, tau, 0.0007, 0.25), 0.4 * pk(burst(0.012, r, 500, 6000, 0.002, 0.0002), 0))


def tom(f, dur, r, tau=0.35):
    return drum(f, dur, r, tau=tau, drop=1.3, tau_drop=0.04, click=0.3)


def snare(r):
    return mix(0.9 * pk(burst(0.25, r, 1500, 7500, 0.07, 0.0005), 0), 1.0 * thump(0.15, 220, 150, 0.02, 0.05, 0.0005, 0.1))


def hat(r, op=False):
    return pk(hp(white(N(0.2), r), 7000, 2) * expo(N(0.2), 0.12 if op else 0.018, 0.0003), 0)


def metal(f, dur, r, tau=0.08):
    return modal([f, f * 2.76, f * 5.4, f * 8.9], [tau, tau * 0.6, tau * 0.35, tau * 0.2], [1, 0.5, 0.3, 0.15], dur, r, detune=10)


def glass_note(f, dur, r, tau=2.5):
    return bell(f, dur, r, tau=tau, bright=0.5)


def softbell(f, dur, r, tau=3.0):
    """clean bell: near-harmonic partials with slight stretch, long decay"""
    return modal([f, f * 2.0, f * 3.01, f * 4.2, f * 5.43], [tau, tau * 0.6, tau * 0.35, tau * 0.2, tau * 0.1], [1, 0.4, 0.2, 0.08, 0.04], dur, r, detune=2, beat=0.0009, attack=0.003)


def swell_curve(n, centre, width, power=2.0):
    t = np.arange(n) / n
    d = np.abs(((t - centre + 0.5) % 1.0) - 0.5)
    return np.exp(-(d / width) ** power)


def soften(x, hz_=1.0):
    """circular lowpass of a control signal so section changes fade rather than step"""
    f = rfftfreq(len(x), 1 / SR)
    return irfft(rfft(x) * np.exp(-(f / hz_) ** 2), len(x))

# ================================================================== dread
@sound("music.dread", lufs=-26.0, loop=True,
       note="the monster appears: a sub heartbeat every 4 s, a slow dissonant cluster swelling and fading, reversed metal swells, a thin high pair")
def dread(r):
    dur = 72.0
    n = N(dur)
    t = T(n)
    m = Mix(dur, loop=True)
    for i, (name, ph, a) in enumerate([("D2", 0.0, 1.0), ("Eb2", 0.33, 0.8), ("A2", 0.66, 0.7), ("Ab2", 0.5, 0.55), ("D3", 0.15, 0.4), ("Bb3", 0.8, 0.2)]):
        v = pad(hz(name), dur, r, voices=3, detune=8, cutoff=2.0, rolloff=1.3, lockdur=dur)
        sw = (0.5 + 0.5 * np.sin(TWO_PI * (t / dur + ph))) ** 2.2
        m.full(widen(v, r, 0.5) * (sw * a)[:, None], 0.5, 0.5)
    for k in range(18):
        m.add(sub_pulse(hz("D1"), 3.2) * (0.8 + 0.2 * r.random()), 2.0 + 4.0 * k, 1.0, 0.0, 0.08)
    for k in (1, 6, 11, 16):
        pl = plate(hz("D2") * 0.76, 5.0, r, 3.0, 12, 8)[::-1]
        pl = pl * np.linspace(0.2, 1, len(pl)) ** 0.5
        m.add(pk(lp(pl, 600, 2), -6), 2.0 + 4.0 * k - 5.0, 0.35, r.uniform(-0.4, 0.4), 0.7)
    ht = sine_lock(1975.5, dur) + 0.8 * sine_lock(1977.1, dur) + 0.3 * sine_lock(2960.0, dur)
    ht = ht * (0.5 + 0.5 * np.sin(TWO_PI * (8 * t / dur))) ** 1.5 * (0.35 + 0.65 * swell_curve(n, 0.55, 0.3))
    m.full(widen(ht, r, 0.9), 0.03, 0.9)
    air = eq(stereo_noise(n, r, -3, corr=0.1), [(100, -40), (300, -6), (800, 0), (2500, -14), (8000, -40)]) * swell(n, r, 0.08, 0.8)[:, None]
    m.full(air, 0.05, 0.6)
    y = m.render("cathedral", 0.9)
    return eq(y, [(25, -8), (38, 0), (160, 0), (4000, -4), (9000, -14)])


# ================================================================== road
@sound("music.road", lufs=-25.0, loop=True,
       note="the drive: a muted 3+3+2 mallet ostinato over a plucked bass, brushed shaker, soft pulse, chord changes every 8 bars (Dm Bb Gm A)")
def road(r):
    bars = 32
    dur = round(bars * 4 * 60.0 / 112.0 / 0.05) * 0.05       # 68.6 s: a whole number of game ticks, so a tick-scheduled replay loops exactly
    spb = dur / (bars * 4)
    m = Mix(dur, loop=True, offset=0.03)
    chords = [("D", ["D4", "F4", "A4", "C5"], "D2", ["D3", "A3"]), ("Bb", ["Bb3", "D4", "F4", "A4"], "Bb1", ["Bb2", "F3"]),
              ("G", ["G3", "Bb3", "D4", "F4"], "G1", ["G2", "D3"]), ("A", ["A3", "C#4", "E4", "G4"], "A1", ["A2", "E3"])]
    step = spb / 4
    accents = {0, 3, 6, 8, 11, 14}
    cell = [0, None, None, 1, None, None, 2, None, 0, None, None, 3, None, None, 2, 1]
    for bar in range(bars):
        ch = chords[bar // 8]
        t0 = bar * 4 * spb
        _, arp, bassn, padn = ch
        bf = hz(bassn)
        for s, nm in [(0, 1.0), (2, 0.7), (5, 0.8), (7, 0.6)]:
            f = bf * (1.5 if (bar % 4 == 3 and s == 7) else 1.0)
            m.add(bass_pluck(f, 0.35, r, 0.2), t0 + s * spb / 2, 0.55 * nm, 0.0, 0.1)
        if bar >= 2:
            for s, ix in enumerate(cell):
                if ix is None:
                    continue
                if bar % 8 == 7 and s >= 12:
                    continue
                f = hz(arp[ix])
                g = (0.55 if s in accents else 0.3) * r.uniform(0.85, 1.0)
                m.add(lp(mallet(f, 0.45, r, 0.9 if s in accents else 0.6, 0.12), 3200, 1), t0 + s * step, g, (-0.5 if s % 2 else 0.5), 0.35)
        if bar >= 4:
            for s in range(16):
                if s % 2 == 1 or (s % 4 == 2):
                    m.add(hat(r, False), t0 + s * step, (0.045 if s % 4 == 2 else 0.028) * r.uniform(0.7, 1.0), r.uniform(-0.6, 0.6), 0.1)
        for b in (0, 2):
            m.add(kick(r, 90, 52, 0.25, 0.07), t0 + b * spb, 0.28, 0.0, 0.05)
        if bar % 8 == 0:
            for j, nm in enumerate(padn):
                p = pad(hz(nm), 8 * 4 * spb * 1.0, r, voices=3, detune=7, cutoff=1.6, rolloff=1.5, attack=2.0, release=3.0)
                m.add(widen(p, r, 0.4), t0, 0.12, 0.0, 0.5)
    y = m.render("room", 0.7)
    return eq(y, [(35, -10), (60, 0), (250, 0), (2500, -3), (7000, -8), (14000, -20)])


# ================================================================== descent
@sound("music.descent", lufs=-26.0, fout=0.05,
       note="the reveal: grows from nothing, a held breath at 7.4-7.9 s, then the BLOOM at exactly 8.0 s (wide chord, choir pad, bell, sub), bells and chord shifts, fading to nothing at 50 s",
       bloom_s=8.0)
def descent(r):
    dur = 50.0
    tail = 6.0
    m = Mix(dur + tail, loop=False)
    n = m.n
    t = T(n)
    B = 8.0
    # --- 0..8 s: out of nothing
    air = bp(white(n, r), 150, 2200, 2) * np.interp(t, [0, 3, 7.4, 7.9, 8.0], [0, 0.25, 1.0, 0.5, 0.0])
    m.full(widen(pk(air, -3), r, 0.8), db(-26), 0.6)
    drone = (np.sin(TWO_PI * hz("D1") * t) + 0.5 * np.sin(TWO_PI * hz("D2") * t + 1) + 0.25 * np.sin(TWO_PI * hz("A2") * t + 2)) * np.interp(t, [0, 2, 7.4, 7.9, 8.2], [0, 0.25, 1.0, 0.5, 0.0])
    m.full(pk(drone, -3) * db(-22), 1.0, 0.3)
    for i, k in enumerate([5, 6, 7, 8, 9, 10, 11, 12]):              # overtone ladder climbing through the first 8 s
        st = 0.8 + i * 0.85
        e = np.interp(t, [st, st + 1.2, 7.4, 7.9, 8.1], [0, 1, 1, 0.4, 0.0])
        m.full(widen(np.sin(TWO_PI * hz("D2") * k * t + k) * e, r, 0.8) * db(-34) / np.sqrt(k), 1.0, 0.8)
    rs = svf(white(n, r), np.exp(np.interp(t, [0, 7.4, 8.0], [np.log(300), np.log(5500), np.log(5500)])), 1.5, "bp") * np.interp(t, [0, 4, 7.4, 7.9, 8.0], [0, 0.1, 1.0, 0.35, 0])
    m.full(widen(pk(rs, -3), r, 0.9), db(-34), 0.5)
    # --- the bloom at 8.0 s: every chord voice starts at B exactly (the first with a 0.2 s attack)
    chords = [(8.0, 22.0, ["D2", "A2", "E3", "A3", "D4", "F#4", "A4", "E5"]),
              (22.0, 34.0, ["B1", "F#2", "D3", "A3", "D4", "F#4", "C#5"]),
              (34.0, 44.0, ["G1", "D2", "D3", "B3", "F#4", "A4", "C#5"]),
              (44.0, 50.0, ["D2", "A2", "D3", "F#3", "A3", "E4"])]
    for ci, (a, b, notes) in enumerate(chords):
        atk = 0.2 if ci == 0 else 3.5
        last = ci == len(chords) - 1
        end = dur if last else b + 3.5
        span = end - a
        ts = T(N(span))
        e = np.interp(ts, [0, atk, (span - 3.5) if not last else span * 0.7, span], [0, 1, 1 if not last else 0.9, 0.0]) ** (1.2 if ci == 0 else 1.0)
        for j, nm in enumerate(notes):
            f = hz(nm)
            lowv = f < 150
            if lowv:
                v = pad(f, span, r, voices=3, detune=7, cutoff=2.4, rolloff=1.2, attack=0.01, release=0.01)
            else:
                v = choir(f, span, r, "ah", 3, 12, 0.005, 5.0, 0.015, None, "oh", np.full(len(ts), 0.3 + 0.4 * (j % 3) / 2))
            gain = (1.0 if lowv else 0.55) * (0.9 + 0.1 * r.random())
            m.add(widen(v, r, 0.6) * e[:, None] * db(-13) * gain, a, 1.0, 0.0, 0.7)
    m.add(softbell(hz("D5"), 8.0, r, 4.0), B, 0.55, 0.0, 0.8)
    m.add(softbell(hz("A5"), 8.0, r, 4.0), B + 0.04, 0.3, 0.3, 0.8)
    m.add(sub_pulse(hz("D1"), 6.0, 0.25, 2.2), B, 0.9, 0.0, 0.1)
    m.add(0.5 * pk(lp(white(N(3.0), r), 1500, 2) * np.interp(T(N(3.0)), [0, 0.1, 3.0], [0, 1, 0]), -6), B, 0.35, 0.0, 0.6)
    # --- bells after the bloom, D lydian
    seq = [(12.0, "F#5"), (15.5, "A5"), (18.0, "E5"), (21.0, "B4"), (26.0, "C#5"), (29.5, "F#5"), (33.0, "D5"), (37.0, "A4"), (41.0, "E5"), (45.0, "F#5")]
    for tb, nm in seq:
        m.add(softbell(hz(nm), 7.0, r, 3.5), tb, r.uniform(0.18, 0.3), r.uniform(-0.6, 0.6), 0.85)
    y = m.render("cavern", 0.9)
    y = eq(y, [(25, -10), (40, 0), (150, 0), (5000, -2), (11000, -10)], circ=False)[:N(dur)]
    y = y * np.interp(np.arange(len(y)) / SR, [dur - 9.0, dur], [1.0, 0.0])[:, None] ** 1.5
    return y, {"bloom_s": B}

# ================================================================== cage
@sound("music.cage", lufs=-27.0, loop=True,
       note="the hangar after the lights: a held cold open-fifth pad with a 9th, glass bells falling E5 -> D5 every 5 s, sub drone, thin air")
def cage(r):
    dur = 80.0
    n = N(dur)
    t = T(n)
    m = Mix(dur, loop=True)
    for i, (nm, a) in enumerate([("D2", 1.0), ("A2", 0.8), ("E3", 0.45), ("A3", 0.4), ("D4", 0.25)]):
        v = pad(hz(nm), dur, r, voices=3, detune=5, cutoff=1.7, rolloff=1.5, lockdur=dur)
        sw = 0.75 + 0.25 * np.sin(TWO_PI * (t / dur * (2 + i) + 0.17 * i))
        m.full(widen(v, r, 0.5) * (sw * a)[:, None], 0.45, 0.6)
    hi = (sine_lock(hz("D6"), dur) + 0.7 * sine_lock(hz("D6") + 0.6, dur) + 0.4 * sine_lock(hz("A5"), dur) + 0.3 * sine_lock(hz("E6"), dur))
    hi = hi * (0.5 + 0.5 * np.sin(TWO_PI * (5 * t / dur))) ** 2 * (0.4 + 0.6 * swell_curve(n, 0.3, 0.35))
    m.full(widen(hi, r, 0.9), 0.025, 0.9)
    sub = sine_lock(hz("D1"), dur) + 0.6 * sine_lock(hz("D1") + 0.2, dur) + 0.2 * sine_lock(hz("D2"), dur)
    m.full(sub * (0.7 + 0.3 * np.sin(TWO_PI * 2 * t / dur)), 0.12, 0.05)
    for k in range(16):
        t0 = 3.0 + k * 5.0
        m.add(glass_note(hz("E5"), 8.0, r, 3.0), t0, 0.22 * r.uniform(0.85, 1.0), -0.25, 0.9)
        if k % 4 != 3:
            m.add(glass_note(hz("D5"), 8.0, r, 3.0), t0 + 2.5, 0.2 * r.uniform(0.85, 1.0), 0.25, 0.9)
    air = eq(stereo_noise(n, r, 0, corr=0.1), [(1500, -40), (4000, -6), (8000, 0), (14000, -8)]) * swell(n, r, 0.05, 0.7)[:, None]
    m.full(air, 0.02, 0.4)
    y = m.render("hangar", 0.8)
    return eq(y, [(25, -6), (36, 0), (120, 0), (5000, -3), (10000, -12)])


# ================================================================== father
@sound("music.father", lufs=-28.0, loop=True,
       note="almost nothing: one sustained low tone (D2 over a D1 floor) and one high thin tone (A6) with a slow beat, breathing over 20 s")
def father(r):
    dur = 60.0
    n = N(dur)
    t = T(n)
    m = Mix(dur, loop=True)
    low = (hosc(np.full(n, lockf(hz("D2"), dur)), n, nh=10, rolloff=2.2, loop=True) + 0.5 * sine_lock(hz("D1"), dur) + 0.12 * sine_lock(hz("A2"), dur))
    low = csvf(low, 260.0, 0.7, "lp")
    low = low * (0.78 + 0.22 * np.sin(TWO_PI * 3 * t / dur))
    m.full(widen(low, r, 0.25), 0.55, 0.3)
    high = sine_lock(hz("A6"), dur) + 0.6 * sine_lock(hz("A6") + 0.4, dur)
    high = high * (0.55 + 0.45 * np.sin(TWO_PI * 3 * t / dur + 1.2)) ** 2
    m.full(widen(high, r, 0.9), 0.016, 0.9)
    y = m.render("cathedral", 0.6)
    return eq(y, [(25, -8), (36, 0), (200, 0), (1000, -6), (3000, 0), (9000, -10)])


# ================================================================== decision
DEC_BPM = 104.0
DEC_P = round(24 * 60.0 / DEC_BPM / 0.05) * 0.05      # 13.85 s = 277 ticks
DEC_RAMP = 90.0


def _heart(r, amp=1.0):
    lub = thump(0.5, 62, 38, 0.04, 0.12, 0.006, 0.25)
    dub = 0.62 * thump(0.4, 78, 50, 0.035, 0.09, 0.006, 0.25)
    return lub * amp, dub * amp

def _decision(r, loop):
    P = DEC_P
    Tm = 0.0 if loop else DEC_RAMP
    dur = P if loop else DEC_RAMP + P
    m = Mix(dur, loop=loop, offset=0.03)
    n = m.n
    t = T(n)
    tt = t - Tm
    spb = P / 24.0
    g = np.ones(n) if loop else np.interp(t, [0, DEC_RAMP], [0.2, 1.0]) ** 1.4
    g[t >= Tm] = 1.0
    drone = (sine_lock(hz("D2"), P, Tm, n) + 0.6 * sine_lock(hz("A2"), P, Tm, n) + 0.4 * sine_lock(hz("D2") + 0.5, P, Tm, n) + 0.25 * sine_lock(hz("D3"), P, Tm, n))
    m.full(drone * g, 0.28, 0.35)
    # tension tone: a creeping semitone ladder, constant (and phase-locked to the loop) in the last cycle
    flast = lockf(hz("C6"), P)
    if loop:
        ph = TWO_PI * flast * tt
    else:
        steps = [(0.0, hz("A5")), (30.0, hz("Bb5")), (55.0, hz("B5")), (75.0, flast)]
        f = np.full(n, steps[0][1])
        for st, fv in steps[1:]:
            f = np.where(t >= st, fv, f)
        k = N(1.5)
        f = uniform_filter1d(f, size=2 * k + 1, mode="nearest")
        f = np.where(t >= Tm, flast, f)
        ph = phase_of(f)
        ph = ph - ph[N(Tm)]
    tone = np.sin(ph) + 0.8 * np.sin(ph * (1 + 3.0 / flast) + 0.5)
    trem = 0.65 + 0.35 * np.sin(TWO_PI * lockf(DEC_BPM / 60.0 * 2, P) * tt)
    ge = np.interp(t, [0, 10, DEC_RAMP], [0.25, 0.4, 1.0]) if not loop else np.ones(n)
    ge[t >= Tm] = 1.0
    m.full(widen(tone * trem * ge, np.random.default_rng(901), 0.8), 0.022, 0.8)
    clus =(sine_lock(hz("E3"), P, Tm, n) + sine_lock(hz("Eb3"), P, Tm, n) + 0.6 * sine_lock(hz("Ab3"), P, Tm, n))
    ce = np.interp(t, [40, 80, Tm], [0, 0.8, 1.0]) if not loop else np.ones(n)
    ce[t < 40] = 0.0
    m.full(clus * ce * (0.8 + 0.2 * np.sin(TWO_PI * lockf(0.25, P) * tt)), 0.06, 0.5)
    nz = eq(stereo_noise(n, r, 0, corr=0.1), [(200, -40), (1500, -8), (5000, 0), (12000, -6)])
    ne = np.interp(t, [55, 90], [0, 0.6]) if not loop else np.full(n, 0.6)
    ne[t < 55] = 0.0
    m.full(nz * ne[:, None], 0.03, 0.4)
    # events
    bt = 1.0
    ticks_gain = lambda tm: float(np.interp(tm, [50, DEC_RAMP], [0.0, 1.0]))
    if not loop:
        while bt < Tm - 0.45 * spb:
            bpm = 48 + (DEC_BPM - 48) * (bt / DEC_RAMP) ** 1.6
            dtb = 60.0 / bpm
            lub, dub = _heart(r, 0.55 + 0.45 * bt / DEC_RAMP)
            m.add(lub, bt, 1.0, 0.0, 0.12)
            m.add(dub, bt + min(0.3, 0.45 * dtb), 1.0, 0.0, 0.12)
            if ticks_gain(bt) > 0:
                m.add(metal(r.uniform(2400, 3000), 0.15, r, 0.02), bt + dtb * 0.5, 0.05 * ticks_gain(bt), r.uniform(-0.5, 0.5), 0.3)
            bt += dtb
    for k in range(24):                                  # the cycle: identical events in the long file and in the loop file
        rk = np.random.default_rng(1000 + k)
        tb = Tm + k * spb
        lub, dub = _heart(rk, 1.0)
        m.add(lub, tb, 1.0, 0.0, 0.12)
        m.add(dub, tb + 0.28, 1.0, 0.0, 0.12)
        m.add(metal(2650.0 + 40 * (k % 3), 0.15, rk, 0.02), tb + 0.5 * spb, 0.05, (-0.5 if k % 2 else 0.5), 0.3)
        if k % 8 == 0:
            m.add(tom(hz("D2"), 1.2, rk, 0.5), tb, 0.55, 0.0, 0.5)
    y = m.render("hall", 0.5)
    return eq(y, [(25, -6), (40, 0), (200, 0), (5000, -3), (11000, -12)], circ=loop)


@sound("music.decision", lufs=-26.0, fout=0.0,
       note="while the player decides: a heartbeat that tightens from 48 to 104 bpm over 90 s while a tone creeps up by semitones and a cluster and noise grow; the last 13.85 s are the loop cycle (music.decision_loop)",
       loop_start_s=DEC_RAMP, loop_seconds=DEC_P)
def decision(r):
    return _decision(np.random.default_rng(5), False), {"loop_start_s": round(DEC_RAMP, 3), "loop_seconds": round(DEC_P, 4)}


@sound("music.decision_loop", lufs=-26.0, loop=True,
       note="the end section of music.decision, seamless: 24 beats at 104 bpm with the held tension tone, cluster and ticking; play it right after music.decision")
def decision_loop(r):
    return _decision(np.random.default_rng(5), True)


# ================================================================== resolve
@sound("music.resolve", lufs=-26.0, fout=0.0,
       note="12 s release: a last thump, the cluster sliding by semitones into D major add9, a warm choir swell, an exhale of noise, one bell, a long tail")
def resolve(r):
    dur = 12.0
    m = Mix(dur, loop=False)
    n = m.n
    t = T(n)
    R = 1.4
    m.add(sub_pulse(hz("D1"), 4.0, 0.03, 1.2), 0.0, 1.0, 0.0, 0.1)
    m.add(thump(0.5, 62, 38, 0.04, 0.12, 0.006, 0.25), 0.0, 0.7, 0.0, 0.1)
    slide = lambda a, b: np.where(t < R, a, np.where(t < R + 2.0, a * (b / a) ** ((t - R) / 2.0), b))
    for fa, fb, gain in [(hz("Eb2"), hz("D2"), 1.0), (hz("Ab2"), hz("A2"), 0.8), (hz("D2"), hz("D2"), 0.8), (hz("Ab3"), hz("A3"), 0.5), (hz("B5"), hz("A5"), 0.12)]:
        f = slide(fa, fb)
        ph = phase_of(f)
        v = np.sin(ph) + 0.4 * np.sin(2 * ph + 0.5) + 0.2 * np.sin(3 * ph)
        e = np.interp(t, [0, 0.3, 1.4, 5.0, 10.0, 12.0], [0, 1, 1, 0.9, 0.3, 0.0])
        m.full(widen(v * e * gain, r, 0.5) * db(-18), 1.0, 0.6)
    for nm, a in [("D3", 0.8), ("A3", 0.7), ("E4", 0.5), ("F#4", 0.5), ("A4", 0.45), ("D5", 0.3)]:
        f = hz(nm)
        v = choir(f, dur, r, "oo", 4, 10, 0.005, 5.0, 0.02, None, "ah", np.interp(t, [1.4, 5.0], [0, 1]))
        e = np.interp(t, [0, 1.3, 3.2, 6.5, 12.0], [0, 0, 1, 0.6, 0.0])
        m.full(widen(v * e * a, r, 0.6) * db(-14), 1.0, 0.8)
    ex = svf(white(n, r), np.interp(t, [0, 1.4, 4.0], [3500, 3500, 600]), 0.8, "lp") * np.interp(t, [0.8, 1.5, 4.5], [0, 1, 0])
    m.full(widen(ex, r, 0.9) * db(-38), 1.0, 0.5)
    m.add(softbell(hz("D5"), 8.0, r, 4.0), 2.1, 0.4, 0.2, 0.9)
    m.add(softbell(hz("A4"), 8.0, r, 4.0), 3.0, 0.25, -0.3, 0.9)
    y = m.render("cathedral", 0.8)
    return fade(y, 0.0, 3.0)


# ================================================================== launch
LAU_BPM = 144.0
LAU_SPB = 60.0 / LAU_BPM
LAU_BAR = 4 * LAU_SPB
LAU_BUILD = 12 * LAU_BAR
LAU_CYC = 26.65                                    # 533 ticks (16 bars at 144.09 bpm); the build is exactly 12 bars at 144 bpm = 20 s
DBAR = LAU_CYC / 16
DSPB = DBAR / 4


def _drive_events(m, r, t0, loop):
    """one 16-bar drive cycle starting at t0"""
    roots = ["D2", "D2", "Bb1", "C2"] * 2 + ["D2", "D2", "Eb2", "E2", "D2", "D2", "F2", "Ab1"][:8]
    cells = [[0, 0, 1, 0], [0, 0, 0, 3], [0, 1, 0, 0], [0, 0, 4, 0]]
    for bar in range(16):
        tb = t0 + bar * DBAR
        root = hz(roots[bar]) if bar < 8 else hz(["D2", "D2", "Eb2", "E2", "D2", "F2", "F#2", "A1"][bar - 8])
        for s in range(8):
            semis = [0, 0, 1, 0, 0, 7, 0, 3 if bar % 4 == 3 else 0][s]
            f = root * 2 ** (semis / 12.0)
            m.add(brass(f, 0.2, r, 0.5, 2, 6, 0.03, 0.01, 0.06), tb + s * DSPB / 2, 0.42 * (1.0 if s % 2 == 0 else 0.7), 0.0, 0.2)
        for b, (kick_g, tom_g) in enumerate([(1.0, 0.0), (0.0, 0.5), (0.8, 0.0), (0.0, 0.55)]):
            if kick_g:
                m.add(kick(r, 100, 48, 0.3, 0.12), tb + b * DSPB, 0.9 * kick_g, 0.0, 0.1)
                m.add(tom(hz("D2"), 0.8, r, 0.35), tb + b * DSPB, 0.4 * kick_g, -0.2, 0.3)
            if tom_g:
                m.add(tom(hz("A2") if b == 1 else hz("F2"), 0.7, r, 0.3), tb + (b + 0.5) * DSPB, 0.45, 0.3, 0.3)
        for s in range(8):
            m.add(hat(r, False), tb + (s + 0.5) * DSPB / 2 * 2 / 2 + DSPB / 4, 0.05 * r.uniform(0.7, 1.0), r.uniform(-0.6, 0.6), 0.1)
        if bar % 4 == 3:
            for nm, gi in [("D3", 1.0), ("A3", 0.8), ("D4", 0.6), ("F4", 0.5)]:
                m.add(brass(hz(nm), 0.9, r, 0.8, 3, 9, 0.08, 0.02, 0.2), tb, 0.3 * gi, 0.0, 0.5)
            m.add(metal(hz("D4"), 1.2, r, 0.5), tb, 0.2, 0.0, 0.5)


@sound("music.launch", lufs=-24.5, fout=0.0,
       note="builds for exactly 20 s (12 bars at 144 bpm: drone, taiko density doubling, rising noise and tone, low brass swells) then drives (16-bar cycle of low-brass ostinato and drums, twice); the cycle is music.launch_loop",
       loop_start_s=LAU_BUILD, loop_seconds=LAU_CYC)
def launch(r):
    r = np.random.default_rng(11)
    dur = LAU_BUILD + 2 * LAU_CYC
    m = Mix(dur, loop=False, offset=0.03)
    n = m.n
    t = T(n)
    tb_end = LAU_BUILD
    drone = (np.sin(TWO_PI * hz("D1") * t) + 0.6 * np.sin(TWO_PI * hz("D2") * t + 1)) * np.interp(t, [0, 8, tb_end, tb_end + 0.01], [0.15, 0.7, 1.0, 0.0])
    m.full(drone * db(-14), 1.0, 0.2)
    rs = svf(white(n, r), np.exp(np.interp(t, [0, tb_end], [np.log(200), np.log(9000)])), 1.2, "bp") * np.interp(t, [0, 10, tb_end - 0.2, tb_end], [0, 0.15, 1.0, 0.0]) ** 2
    m.full(widen(rs, r, 0.8) * db(-34), 1.0, 0.5)
    rf = 90 * (900 / 90) ** (np.clip(t / tb_end, 0, 1) ** 1.3)
    rt = (np.sin(phase_of(rf)) + 0.5 * np.sin(2 * phase_of(rf))) * np.interp(t, [0, 12, tb_end - 0.2, tb_end], [0, 0.2, 1.0, 0.0])
    m.full(widen(rt, r, 0.6) * db(-32), 1.0, 0.5)
    for bar in range(12):
        tb = bar * LAU_BAR
        if bar < 4:
            hits = [0]
        elif bar < 8:
            hits = [0, 2]
        elif bar < 10:
            hits = [0, 1, 2, 3]
        elif bar < 12:
            hits = [0, 0.5, 1, 1.5, 2, 2.5, 3, 3.5]
        if bar == 11:
            hits = hits + [3.75, 3.25, 2.75]
        for h in hits:
            g = 0.4 + 0.6 * (bar / 11.0)
            m.add(tom(hz("D2") if h % 1 == 0 else hz("A2"), 1.0, r, 0.45), tb + h * LAU_SPB, 0.6 * g, 0.0, 0.4)
            if bar >= 8:
                m.add(kick(r, 100, 48, 0.3, 0.12), tb + h * LAU_SPB, 0.35 * g, 0.0, 0.1)
        if 4 <= bar < 12 and bar % 2 == 0:
            for nm, gi in [(["D2", "F2", "G2", "A2"][(bar - 4) // 2], 1.0), (["A2", "C3", "D3", "E3"][(bar - 4) // 2], 0.7)]:
                m.add(brass(hz(nm), 2 * LAU_BAR, r, 0.55 + 0.04 * bar, 3, 8, 1.2, 0.04, 0.3), tb, 0.35 * gi, 0.0, 0.4)
        if bar in (7, 11):
            m.add(metal(hz("D4") * 0.75, 2.0, r, 0.6), tb + 3 * LAU_SPB, 0.25, 0.0, 0.6)
            m.add(pk(lp(white(N(1.2), r), 3000, 2) * np.interp(T(N(1.2)), [0, 1.1, 1.2], [0, 1, 0]), -6), tb + 2 * LAU_SPB, 0.15, 0.0, 0.4)
    for c in range(2):                                   # the LAST cycle uses the same random stream as music.launch_loop
        _drive_events(m, np.random.default_rng(99 + c), tb_end + c * LAU_CYC, False)
    y = m.render("hall", 0.5)
    y = eq(y, [(25, -6), (40, 0), (200, 0), (5000, -2), (12000, -10)], circ=False)
    return y, {"buildup_s": round(LAU_BUILD, 3), "loop_start_s": round(LAU_BUILD, 3), "loop_seconds": round(LAU_CYC, 4)}


@sound("music.launch_loop", lufs=-24.5, loop=True,
       note="the 16-bar drive of music.launch, seamless (26.67 s at 144 bpm); loop it until the surface")
def launch_loop(r):
    m = Mix(LAU_CYC, loop=True, offset=0.03)
    _drive_events(m, np.random.default_rng(100), 0.0, True)
    y = m.render("hall", 0.5)
    return eq(y, [(25, -6), (40, 0), (200, 0), (5000, -2), (12000, -10)])


# ================================================================== fight
def _fight(r, bpm, bars, final):
    dur = round(bars * 4 * 60.0 / bpm / 0.05) * 0.05          # a whole number of game ticks
    spb = dur / (bars * 4)
    bar_s = 4 * spb
    m = Mix(dur, loop=True, offset=0.03)
    sec = lambda b: b // 8
    if not final:
        cells = {0: [0, 0, 1, 0, 0, 5, 0, 3], 1: [0, 0, 1, 0, 6, 0, 5, 0], 2: [0, 3, 0, 1, 0, 3, 0, 6]}
        roots = ["D2", "D2", "Bb1", "C2"]
    else:
        cells = {0: [0, 1, 0, 6, 0, 1, 0, 7], 1: [0, 0, 1, 0, 6, 6, 0, 1], 2: [0, 1, 6, 1, 0, 7, 6, 1]}
        roots = ["D2", "Eb2", "D2", "F#2"]
    for bar in range(bars):
        tb = bar * bar_s
        s8 = sec(bar)
        root = hz(roots[(bar // 2) % 4])
        cell = cells[s8 % 3]
        density = 2 if final else 1
        steps = 8 * density
        breakdown = (s8 == 3)
        for s in range(steps):
            semis = cell[(s // density) % 8] if density == 1 else cell[(s // 2) % 8] + (12 if s % 2 else 0)
            f = root * 2 ** (semis / 12.0)
            g = 0.5 if (s % density == 0 and (s // density) % 2 == 0) else 0.34
            if breakdown and bar % 8 < 4:
                g *= 0.6
            m.add(brass(f * (2 if final and s % 2 else 1), spb / 2 / density * 0.9, r, 0.55, 2, 8, 0.01, 0.01, 0.03), tb + s * spb / (2 * density), g, 0.0, 0.1)
        if not breakdown or bar % 8 >= 4:
            for b in range(4):
                m.add(kick(r, 105, 46, 0.3, 0.12), tb + b * spb, 0.85 if b % 2 == 0 else 0.5, 0.0, 0.08)
                if b % 2 == 0:
                    m.add(tom(hz("D2"), 0.8, r, 0.3), tb + b * spb, 0.35, -0.25, 0.3)
            for b in (1, 3):
                m.add(snare(r), tb + b * spb, 0.5, 0.0, 0.25)
            for s in (3, 7):
                m.add(tom(hz("A2") if s == 3 else hz("F2"), 0.5, r, 0.2), tb + (s + 0.5) * spb / 2, 0.25, 0.3 * (1 if s == 3 else -1), 0.3)
        for s in range(16):
            if (s % 2 == 1) or final:
                m.add(hat(r, s % 8 == 7), tb + s * spb / 4, 0.05 * r.uniform(0.6, 1.0), r.uniform(-0.6, 0.6), 0.1)
        if bar % 8 in (0,):
            m.add(metal(hz("D4") * 0.5, 3.0, r, 0.9), tb, 0.3, 0.0, 0.7)
        if s8 >= 1 and not (breakdown and bar % 8 < 4) and bar % 2 == 0:
            for (a, b_) in [("D4", "Ab4"), ("C4", "F#4")][(bar // 2) % 2:][:1]:
                for off in (1.5, 2.5, 3.5) if not final else (0.5, 1.5, 2.5, 3.5):
                    m.add(brass(hz(a), 0.25, r, 0.8, 3, 10, 0.01, 0.03, 0.05), tb + off * spb, 0.3, -0.2, 0.3)
                    m.add(brass(hz(b_), 0.25, r, 0.8, 3, 10, 0.01, 0.03, 0.05), tb + off * spb, 0.26, 0.2, 0.3)
        if final and s8 >= 1:
            arp = ["D5", "F#5", "A5", "Eb5", "A5", "F#5", "C#5", "A4"] if (bar // 2) % 2 == 0 else ["D5", "Eb5", "G5", "F#5", "D5", "Eb5", "A5", "G5"]
            for s in range(16):
                m.add(mallet(hz(arp[s % 8]) , 0.25, r, 1.2, 0.07) * 1.0, tb + s * spb / 4, 0.18 if s % 4 == 0 else 0.1, (-0.5 if s % 2 else 0.5), 0.35)
    # long layers
    t = T(m.n)
    sec_idx = (t // (8 * bar_s)).astype(int)
    lvl = soften(np.array([0.45, 0.8, 1.0, 0.5, 1.0, 1.0])[sec_idx], 0.4)
    strings = np.zeros(m.n)
    for nm, a in ([("D3", 1.0), ("A3", 0.7), ("D4", 0.5), ("Eb4", 0.35)] if not final else [("A3", 1.0), ("D4", 0.7), ("Eb4", 0.6), ("F#4", 0.5), ("A4", 0.35)]):
        v = pad(hz(nm), dur, r, voices=3, detune=10, cutoff=3.0 if final else 2.2, rolloff=1.0, lockdur=dur)
        trem = 0.6 + 0.4 * np.sin(TWO_PI * lockf(bpm / 60.0 * 2, dur) * t)
        strings += v * trem * a * lvl
    m.full(widen(strings, r, 0.7), 0.16, 0.5)
    if final:
        sf = 300 * (3000 / 300) ** ((t / (8 * bar_s)) % 1.0)
        sir = np.sin(phase_of(sf, True)) + 0.5 * np.sin(2 * phase_of(sf, True))
        sir = sir * (0.5 + 0.5 * np.sin(TWO_PI * lockf(0.25 / bar_s, dur) * t - 1.0)) ** 2
        m.full(widen(sir, r, 0.6), 0.02, 0.5)
    y = m.render("hall", 0.4)
    return eq(y, [(25, -6), (40, 0), (200, 0), (5000, -2), (12000, -8)])


@sound("music.fight", lufs=-24.5, loop=True,
       note="the battle: 152 bpm, 40 bars; kick/taiko and cannon-snare, chromatic low-brass ostinato, dissonant dyad stabs, tremolo pad; sections of 8 bars add layers and bar 25-28 break down")
def fight(r):
    return _fight(np.random.default_rng(21), 152.0, 40, False)


@sound("music.fight_final", lufs=-24.2, loop=True,
       note="the last phase: 172 bpm, 48 bars; double-time bass, high mallet 16th ostinato, tritone stabs, a siren-like tone rising every 8 bars")
def fight_final(r):
    return _fight(np.random.default_rng(22), 172.0, 48, True)


# ================================================================== victory
@sound("music.victory", lufs=-27.0, fout=0.0,
       note="40 s, exhausted quiet then dawn: wind and a faint sub, slow bells, a D major add9 chord blooming from nothing, a breathing sustain, high shimmer, fading out")
def victory(r):
    dur = 40.0
    tail = 5.0
    m = Mix(dur + tail, loop=False)
    n = m.n
    t = T(n)
    wind = eq(stereo_noise(n, r, -3, corr=0.2), [(60, -30), (200, 0), (700, -6), (2500, -20), (8000, -40)]) * swell(n, r, 0.12, 0.9, False)[:, None]
    m.full(wind * np.interp(t, [0, 3, 22, 34, 40], [0.2, 1, 0.8, 0.3, 0.0])[:, None], db(-30), 0.3)
    m.full(np.sin(TWO_PI * hz("D1") * t) * np.interp(t, [0, 4, 30, 40], [0, 0.6, 0.4, 0]), db(-26), 0.1)
    for tb, nm, g in [(5.0, "D3", 0.35), (9.0, "A3", 0.3), (13.0, "F#4", 0.25), (16.5, "E4", 0.25)]:
        m.add(softbell(hz(nm), 9.0, r, 4.5), tb, g, r.uniform(-0.3, 0.3), 0.9)
    for nm, a, st in [("D2", 1.0, 15.0), ("A2", 0.8, 16.0), ("F#3", 0.6, 17.5), ("A3", 0.6, 18.5), ("E4", 0.5, 19.5), ("D4", 0.5, 20.0), ("A4", 0.4, 21.0)]:
        f = hz(nm)
        e = np.interp(t, [st, st + 6.0, 30.0, 40.0], [0, 1.0, 0.8, 0.0])
        if f < 150:
            v = pad(f, dur + tail, r, voices=3, detune=6, cutoff=2.0, rolloff=1.3, attack=0.01, release=0.01)
        else:
            v = choir(f, dur + tail, r, "oo", 4, 10, 0.004, 4.6, 0.02, None, "ah", np.interp(t, [st, st + 8], [0, 1]))
        m.full(widen(v, r, 0.6) * e[:, None], db(-15) * a, 0.8)
    sh = np.zeros(n)
    for k in (6, 8, 9, 10, 12):
        sh += np.sin(TWO_PI * hz("D3") * k * t + k) * (0.6 + 0.4 * np.sin(TWO_PI * (0.11 * k) * t)) / k
    sh = sh * np.interp(t, [22, 27, 34, 40], [0, 1, 0.5, 0])
    m.full(widen(sh, r, 0.9), db(-30), 0.9)
    for tb, nm in [(24.0, "F#5"), (28.0, "A5"), (31.0, "E5"), (34.5, "D5")]:
        m.add(softbell(hz(nm), 9.0, r, 4.0), tb, 0.16, r.uniform(-0.5, 0.5), 0.9)
    y = m.render("cathedral", 0.8)
    y = eq(y, [(25, -8), (40, 0), (150, 0), (5000, -2), (11000, -10)], circ=False)
    y = fade(y, 0.0, 6.0) if False else y
    y = y[:N(dur + tail)]
    ramp = np.interp(np.arange(len(y)) / SR, [dur - 8.0, dur + tail], [1.0, 0.0])
    return (y * ramp[:, None])[:N(dur)]


# ================================================================== defeat
@sound("music.defeat", lufs=-25.0, fout=0.0,
       note="8 s: a low blow, a dissonant pad collapsing downward as its filter closes, a detuned bell dying, then only reverb")
def defeat(r):
    dur = 8.0
    m = Mix(dur, loop=False)
    n = m.n
    t = T(n)
    m.add(sub_pulse(hz("D1"), 4.0, 0.02, 1.3), 0.0, 1.0, 0.0, 0.15)
    m.add(tom(hz("D2"), 2.0, r, 1.0), 0.0, 0.7, 0.0, 0.5)
    f1 = hz("D3") * 2 ** (-np.minimum(t, 4.0) * 12 / 4.0 / 12 * 1.5)
    for ratio, g in [(1.0, 1.0), (1.0595, 0.7), (1.5, 0.6), (1.41, 0.4)]:
        f = f1 * ratio
        ph = phase_of(f)
        v = hosc(f, n, nh=20, rolloff=1.2)
        v = svf(v, np.interp(t, [0, 4, 8], [2200, 220, 120]), 0.9, "lp")
        v *= np.interp(t, [0, 0.05, 1.5, 4.0, 7.0], [0, 1, 0.7, 0.3, 0.0])
        m.full(widen(v * g, r, 0.5) * db(-16), 1.0, 0.6)
    bl = bell(hz("D4") * 0.97, 7.0, r, tau=3.0, bright=0.4)
    m.add(bl, 0.15, 0.3, 0.2, 0.9)
    y = m.render("cathedral", 0.9)
    return fade(y, 0.0, 2.5)
