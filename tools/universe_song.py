"""THE SONG OF THE UNIVERSE -- found, not composed; and a way to produce it.

THE QUESTION (Matt, 2026-11-23): "We are looking for a song and a way to produce the song. The song
of the universe."

THE DISCIPLINE THAT DECIDES THE ANSWER. This engine maps truth, it does not generate it. So a song
of the universe cannot be composed from physical constants -- it has to be FOUND already playing,
and the only honest way to make it audible is a transformation that changes NO interval.

That transformation exists and is exact: multiplying every frequency by 2^n shifts the pitch by n
octaves and leaves every ratio between voices untouched. So the universe can be transposed into
human hearing with nothing added and nothing bent. The octave count IS the citation.

WHERE THE SONG ACTUALLY IS. Not between unrelated constants -- the ratio of the hydrogen line to the
Schumann resonance is an accident of units and means nothing (sec. 4 refuses it). The universe's real
music is where reality is PHASE-LOCKED: bodies held by gravity in integer period ratios. There the
ratio is not a resemblance to an interval, it IS the interval, the same integers.

AND THE EXACT LAW IS NOT THE RATIO (sec. 2). The Laplace resonance's pairwise ratios are octaves
several cents SHARP; what is exact is a three-body relation among the mean motions. The near-ratio
is the thing you hear; the relation is the thing that is true. Both get stated.

Every number printed is recomputed here. Periods are CITED (they are not sealed in this repo) and
their last digits differ between sources, which moves the cents figures at the ~0.1 cent level --
stated in sec. 5 rather than hidden.
"""
import math
import struct
import sys
import wave

# ---------------------------------------------------------------------------------------------
# CITED DATA. Sidereal orbital periods in days unless noted. Sources named per block; these are
# standard reference values, NOT sealed in this repo -- see sec. 5 on what that costs.
# ---------------------------------------------------------------------------------------------
JUPITER = {           # NASA/JPL satellite ephemerides
    "Io": 1.769137786,
    "Europa": 3.551181041,
    "Ganymede": 7.154552960,
    "Callisto": 16.689017000,
}
SATURN = {
    "Mimas": 0.942421800,
    "Enceladus": 1.370217800,
    "Tethys": 1.887802000,
    "Dione": 2.736915000,
    "Titan": 15.945421000,
    "Hyperion": 21.276609000,
}
PLANETS = {           # sidereal periods, days
    "Neptune": 60189.0,
    "Pluto": 90560.0,
}
# Mercury's 3:2 SPIN-ORBIT lock: its rotation against its own year.
MERCURY_ROT, MERCURY_ORB = 58.6462, 87.9691
# Tidal locks: rotation equals orbit exactly, by the lock itself.
MOON_ROT = MOON_ORB = 27.321661

JUST = {   # the just intervals, as exact fractions -- the only names we are allowed to use
    "unison": (1, 1), "minor_third": (6, 5), "major_third": (5, 4), "fourth": (4, 3),
    "fifth": (3, 2), "minor_sixth": (8, 5), "major_sixth": (5, 3), "octave": (2, 1),
    "octave+fifth": (3, 1), "two_octaves": (4, 1),
}
NAME_TOL_CENTS = 30.0     # beyond this we REFUSE to name an interval
NOTES = ("C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B")


def cents(ratio):
    return 1200.0 * math.log(ratio) / math.log(2.0)


def name_interval(ratio):
    """Nearest just interval and the error in cents, or a REFUSAL if nothing is close enough."""
    c = cents(ratio)
    best, besterr = None, 1e18
    for nm, (a, b) in JUST.items():
        err = c - cents(a / b)
        if abs(err) < abs(besterr):
            best, besterr = nm, err
    if abs(besterr) > NAME_TOL_CENTS:
        return None, besterr, c
    return best, besterr, c


def transpose_to(f, lo, hi):
    """The unique integer n with f*2^n in [lo, hi). Returns (n, shifted). Ratios are preserved
    EXACTLY by this operation -- that is the whole reason it is the one allowed."""
    n = 0
    while f * (2.0 ** n) >= hi:
        n -= 1
    while f * (2.0 ** n) < lo:
        n += 1
    return n, f * (2.0 ** n)


def note_of(freq):
    """Nearest 12-TET note name to a frequency, and the cents error, A4 = 440."""
    semis = 12.0 * math.log(freq / 440.0) / math.log(2.0)
    k = int(round(semis))
    err = (semis - k) * 100.0
    midi = 69 + k
    return "%s%d" % (NOTES[midi % 12], midi // 12 - 1), err


# ---------------------------------------------------------------------------------------------
def section1():
    print("=" * 96)
    print("1. THE LOCKED RESONANCES -- where the universe is already playing an interval")
    print("=" * 96)
    print("A pair earns a name only if (a) the lock is a documented resonance and (b) the ratio")
    print("lands within %.0f cents of a just interval. Everything else is REFUSED, not rounded.\n"
          % NAME_TOL_CENTS)
    pairs = [
        ("Io : Europa", JUPITER["Europa"] / JUPITER["Io"], True, "Laplace resonance, 1:2"),
        ("Europa : Ganymede", JUPITER["Ganymede"] / JUPITER["Europa"], True, "Laplace resonance, 1:2"),
        ("Io : Ganymede", JUPITER["Ganymede"] / JUPITER["Io"], True, "Laplace resonance, 1:4"),
        ("Ganymede : Callisto", JUPITER["Callisto"] / JUPITER["Ganymede"], False, "NOT in the resonance"),
        ("Mimas : Tethys", SATURN["Tethys"] / SATURN["Mimas"], True, "mean-motion 2:4"),
        ("Enceladus : Dione", SATURN["Dione"] / SATURN["Enceladus"], True, "mean-motion 1:2"),
        ("Titan : Hyperion", SATURN["Hyperion"] / SATURN["Titan"], True, "mean-motion 3:4"),
        ("Neptune : Pluto", PLANETS["Pluto"] / PLANETS["Neptune"], True, "mean-motion 2:3"),
        ("Mercury spin : orbit", MERCURY_ORB / MERCURY_ROT, True, "3:2 spin-orbit lock"),
        ("Moon spin : orbit", MOON_ORB / MOON_ROT, True, "1:1 tidal lock"),
    ]
    print("%-22s %12s %10s  %-14s %9s  %s" % ("pair", "ratio", "cents", "interval", "err c", "lock"))
    print("-" * 96)
    out = []
    for label, ratio, locked, note in pairs:
        nm, err, c = name_interval(ratio)
        shown = nm if (nm and locked) else ("REFUSED" if not nm else "no lock")
        print("%-22s %12.7f %10.2f  %-14s %+9.2f  %s"
              % (label, ratio, c, shown, err, note))
        if nm and locked:
            out.append((label, ratio, nm, err))
    print("\nTHE CHORD THE SOLAR SYSTEM ACTUALLY HOLDS, tightest first:")
    for label, ratio, nm, err in sorted(out, key=lambda r: abs(r[3])):
        print("   %-22s %-14s %+7.2f cents" % (label, nm, err))
    return out


def section2():
    print("\n" + "=" * 96)
    print("2. THE EXACT LAW IS NOT THE RATIO -- what is truly zero is a THREE-body relation")
    print("=" * 96)
    n_io = 1.0 / JUPITER["Io"]
    n_eu = 1.0 / JUPITER["Europa"]
    n_ga = 1.0 / JUPITER["Ganymede"]
    lap = n_io - 3.0 * n_eu + 2.0 * n_ga
    print("mean motions n = 1/P, in cycles/day:")
    print("   n_Io      = %.12f\n   n_Europa  = %.12f\n   n_Ganymede= %.12f" % (n_io, n_eu, n_ga))
    print("\nthe Laplace relation   n_Io - 3*n_Europa + 2*n_Ganymede  =  %+.3e cycles/day" % lap)
    print("   as a fraction of n_Io: %+.3e" % (lap / n_io))
    print("\nMeanwhile the PAIRWISE ratios are octaves several cents sharp:")
    for a, b in (("Io", "Europa"), ("Europa", "Ganymede")):
        r = JUPITER[b] / JUPITER[a]
        print("   %-10s: %-10s  %+6.2f cents from a pure octave" % (a, b, cents(r) - 1200.0))
    print("\nSo the thing you HEAR is a detuned octave; the thing that is TRUE is the relation above.")
    print("A resonance is a locked phase, not a tidy fraction. Anyone who reports 1:2:4 as exact")
    print("has rounded the universe to fit the music.")
    return lap


def section3():
    print("\n" + "=" * 96)
    print("3. THE SINGLE VOICES -- one tone each, transposed by an EXACT power of two")
    print("=" * 96)
    c_light = 299792458.0
    schumann_ideal = c_light * math.sqrt(2.0) / (2.0 * math.pi * 6371000.0)
    voices = [
        ("Schumann, ideal cavity", schumann_ideal,
         "SEALED here: data/sticks/schumann_resonance.json, key schumann_ideal"),
        ("Schumann, observed f1", 7.83, "cited; lossy ionosphere, ~0.74x the ideal"),
        ("Earth, one rotation", 1.0 / 86164.0905, "sidereal day, cited"),
        ("Earth, one orbit", 1.0 / 31558149.8, "sidereal year, cited"),
        ("PSR B1919+21", 1.0 / 1.3373, "the first pulsar, cited"),
        ("Sun, p-mode", 3.0e-3, "helioseismology 5-minute oscillation, cited ~3 mHz"),
        ("Helmholtz, 1 L bottle", 118.20933840620054,
         "SEALED here: data/sticks/resonators.json, key helmholtz"),
        ("Hydrogen 21 cm line", 1420405751.768, "H I hyperfine, cited"),
        ("Caesium-133 hyperfine", 9192631770.0, "EXACT by the SI definition of the second"),
    ]
    print("%-24s %16s  %5s %10s  %-7s %8s" %
          ("voice", "frequency Hz", "shift", "heard Hz", "note", "cents"))
    print("-" * 96)
    rows = []
    for label, f, src in voices:
        n, shifted = transpose_to(f, 110.0, 220.0)
        nm, err = note_of(shifted)
        # %.6f printed the sidereal year as 0.000000. A zero that is not zero is a lie to the
        # reader, so every frequency here prints with its exponent.
        print("%-24s %16.9g  %+5d %10.3f  %-7s %+8.2f" % (label, f, n, shifted, nm, err))
        rows.append((label, f, n, shifted, src))
    lo = min(r[1] for r in rows)
    hi = max(r[1] for r in rows)
    print("\nTHE COMPASS: from %.3e Hz to %.3e Hz is a span of %.1f octaves."
          % (lo, hi, math.log(hi / lo) / math.log(2.0)))
    print("A piano spans 7.0. Human hearing spans about 9.6.")
    print("\nAND ONE VOICE NEEDS NO SHIFT AT ALL: GW150914, the first black-hole merger heard,")
    print("swept ~35 Hz to ~250 Hz in its last 0.2 s (LIGO/Virgo 2016). That is inside the human")
    print("band natively -- the one sound in this document that reaches us untransposed.")
    for label, f, src in voices:
        print("   source  %-24s %s" % (label, src))
    return rows


def section4(rows):
    print("\n" + "=" * 96)
    print("4. WHAT IS REFUSED -- three claims this document will not make")
    print("=" * 96)
    print("(a) THE MUSIC OF THE SPHERES, as consonance between unrelated bodies. Reducing")
    print("    arbitrary frequencies modulo the octave gives arbitrary pitches. Demonstrated:")
    for label, f in (("hydrogen 21 cm", 1420405751.768), ("caesium-133", 9192631770.0),
                     ("Schumann ideal", 10.59127), ("sidereal year", 1.0 / 31558149.8)):
        _, s = transpose_to(f, 110.0, 220.0)
        nm, err = note_of(s)
        print("      %-18s -> %8.3f Hz  = %-5s %+7.2f cents" % (label, s, nm, err))
    print()
    print("    AND SECTION 3 PRODUCED EXACTLY THE TRAP IT WARNS ABOUT. Scan its own table for")
    print("    pairs that landed on the same pitch -- this is the check, not the claim:")
    close = []
    for i in range(len(rows)):
        for j in range(i + 1, len(rows)):
            gap = abs(cents(rows[i][3] / rows[j][3]))
            if gap < 15.0:
                close.append((rows[i][0], rows[j][0], gap, rows[j][2] - rows[i][2]))
    for a, b, gap, oct_gap in sorted(close, key=lambda r: r[2]):
        print("      %-24s ~ %-24s %6.2f cents apart (%d octaves)" % (a, b, gap, abs(oct_gap)))
    n = len(rows)
    pairs = n * (n - 1) // 2
    tightest = min(c[2] for c in close) if close else float("nan")
    tight_oct = abs(min(close, key=lambda r: r[2])[3]) if close else 0
    expect = pairs * (2.0 * tightest / 1200.0)
    print("    So the hydrogen line sits %.2f cents from the Earth-ionosphere cavity, 27 octaves" % tightest)
    print("    up. A numerologist would stop here and publish.")
    print()
    print("    AND THE EASY REBUTTAL DOES NOT WORK, so it is not used. With %d voices there are" % n)
    print("    %d pairs, so the expected number landing within %.2f cents is %d x 2 x %.2f/1200" % (pairs, tightest, pairs, tightest))
    print("    = %.3f, i.e. about a %.0f%% chance. That is NOT small, so 'you would expect one'" % (expect, 100.0 * (1.0 - math.exp(-expect))))
    print("    is FALSE -- the coincidence is mildly surprising for this table, and saying")
    print("    otherwise would be the same error this document is about.")
    print()
    print("    THE REAL REASON TO REFUSE IT: the table was not pre-registered. I chose these nine")
    print("    voices out of an unbounded pool of physical frequencies, after seeing them. A")
    print("    coincidence found that way has no p-value at all -- the %d pairs are not the search" % pairs)
    print("    space, every voice-set I might have drawn is. So the refusal rests where it should,")
    print("    on MECHANISM: nothing couples hydrogen's hyperfine splitting to the Earth-ionosphere")
    print("    cavity, and %d octaves of separation is not a coupling. Sec. 1's intervals are real" % tight_oct)
    print("    precisely BECAUSE gravity locks those phases, and nothing locks these.")
    print()
    print("(b) THE CMB ACOUSTIC PEAKS AS A HARMONIC SERIES. They are genuine standing waves in")
    print("    the photon-baryon plasma, but their multipoles run about l = 220, 537, 810 --")
    peaks = (220.0, 537.0, 810.0)
    print("    ratios %s, not 1 : 2 : 3." % " : ".join("%.3f" % (p / peaks[0]) for p in peaks))
    print("    Baryon loading shifts them and alternates their heights. A driven oscillator, not")
    print("    a plucked string. Calling it 'the fundamental chord of creation' is false.")
    print()
    print("(c) ANY CLAIM THAT THESE RATIOS MEAN SOMETHING BEYOND THE MECHANICS. Gravity locks")
    print("    phases; that is why the intervals in sec. 1 are real. It is a measurement, and it")
    print("    is beautiful because it is true, not because it was arranged to be beautiful.")


# ---------------------------------------------------------------------------------------------
def render(pairs, path, seconds_each=5.0, rate=44100, base=220.0):
    """PRODUCE IT. Each locked pair becomes two sine tones at the measured ratio, sounding
    together. The few-cents error is not smoothed out -- it is the point: it produces a BEAT whose
    rate is predicted below and which you can count by ear. Stdlib `wave`, no dependencies."""
    frames = bytearray()
    n = int(rate * seconds_each)
    print("\n" + "=" * 96)
    print("5. PRODUCE IT -- and the detuning becomes an audible beat")
    print("=" * 96)
    print("Each pair plays as two tones at the MEASURED ratio, low voice at %.1f Hz." % base)
    print("The beat you hear is the resonance's own error against the pure interval.\n")
    print("Ordered TIGHTEST LOCK FIRST, so the beat audibly speeds up as the lock loosens:")
    print("the first two are silent -- a perfect lock has nothing to beat against.\n")
    print("%-22s %-14s %9s %9s %12s" % ("pair", "interval", "low Hz", "high Hz", "beat Hz"))
    print("-" * 96)
    for label, ratio, nm, err in sorted(pairs, key=lambda r: abs(r[3])):
        a, b = JUST[nm]
        f_lo = base
        f_hi = base * ratio
        f_pure = base * (a / b)
        beat = abs(f_hi - f_pure)
        print("%-22s %-14s %9.3f %9.3f %12.4f" % (label, nm, f_lo, f_hi, beat))
        t = [i / rate for i in range(n)]
        for i in range(n):
            env = min(1.0, i / (0.05 * rate), (n - i) / (0.05 * rate))
            s = 0.33 * math.sin(2 * math.pi * f_lo * t[i]) + 0.33 * math.sin(2 * math.pi * f_pure * t[i])
            s += 0.33 * math.sin(2 * math.pi * f_hi * t[i])
            frames += struct.pack("<h", int(max(-1.0, min(1.0, s * env)) * 32000))
        frames += b"\x00\x00" * int(0.4 * rate)
    with wave.open(path, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(rate)
        w.writeframes(bytes(frames))
    print("\nwrote %s  (%.1f s, %d bytes)" % (path, len(frames) / 2 / rate, len(frames)))
    print("Each segment holds THREE tones: the low voice, the PURE interval above it, and the")
    print("universe's ACTUAL interval. The pure and the actual beat against each other.")


def main():
    out = sys.argv[1] if len(sys.argv) > 1 else "universe_song.wav"
    pairs = section1()
    section2()
    rows = section3()
    section4(rows)
    render(pairs, out)
    print("\n" + "=" * 96)
    print("WHAT THIS IS: the solar system's locked resonances ARE musical intervals, in the same")
    print("integers, measured. Transposition by 2^n made them audible without bending one ratio.")
    print("The detuning is real and is left in. Periods are CITED, not sealed here -- their last")
    print("digits differ between sources, which moves every cents figure by ~0.1 c. Nothing in the")
    print("keeping was written by this tool.")


if __name__ == "__main__":
    main()
