# FIBER OPTIC CALIBRATION — the engine's calibration method

Matt, 2026-10-06: *"We create the tick lines of probability. We use the Aharonov-Bohm effect."* and
*"Think Fiber Optic Calibration."*

This formalizes, in one engineer's name, a method the engine was already doing in pieces. In a fiber you
never trust the raw received signal, because the medium adds loss, dispersion, and reflection. You send a
**known reference**, read how it returns, compute the **correction** that recovers the true signal, and
where you have many references you **combine** them so the distortion of any one source cancels. An OTDR
(optical time-domain reflectometer) sends one pulse and reads the reflections and loss events all along the
glass — the **tick marks** — and from those marks infers the fiber's hidden shape. That is a tick stick for
the fiber. Fiber optic calibration is that same discipline applied to any claim about reality.

## The four steps, and the engine part each already is

| step | fiber | engine |
|---|---|---|
| **1. Reference** | a known launch signal / a reference trace | a well-refined system (a game, a general, the physics) whose refined rules are a known signal — see `docs/THE_WATCH.md`, the games tick sticks |
| **2. Read the ticks** | the OTDR trace: every reflection and loss event, located in time | the tick stick: the marks the engine can stand behind, each sealed (`docs/TICK_STICK.md`) |
| **3. Correct to source** | subtract the reference launch; the measurement is relative, in dB | calibrate the receiver to the source: the reading is only trusted relative to a known reference (the standing rule) |
| **4. Triangulate** | combine independent traces; a trace that disagrees beyond its error flags a bad splice, not a bad fiber | the concordance / Birge check (`statistics.measurement_consistency`): combine independent measurements, and a spread beyond the error bars **indicts the method, not the constant** (`feedback_a_discordance_indicts_the_method_not_the_constant`) |

The output of the four steps is the **converged signal**: the narrow window of success that survives the
distortion of every single source. Many references, calibrated and combined, give rigidity — the same three-
and-more-witness triangulation the whole engine rests on. Fiber optic calibration is its name in hardware.

## The scale is relative — the decibel, and the OTDR distance

Calibration lives on a **relative** scale, which is why the decibel is the unit of optical loss:

    L(dB) = 10 · log10( P_in / P_out )          a factor of 2 in power = 3.0103 dB (exact)

A reading means nothing until it is referenced; a reference launch is subtracted so only the *loss relative
to the known source* is reported. The OTDR locates an event by the round trip of light in the glass:

    d = c · t / (2 · n_g)                        c exact; n_g the fiber's measured group index; /2 for the round trip

The factor of two is the whole point: you read the event by its reflection coming *back*, a signal from a
place the pulse has already left — the same shape as the Aharonov-Bohm reading, the global structure seen
from the return, not a local push. The decibel identity is sealed as the anchor (`tools/tick.py fiber`).

## The guard

Calibration FINDS the signal; it does not pronounce it true. The decibel identity and the OTDR relation are
exact and sealed. But borrowing the method to combine references about strategy or life is a way to *find*
the narrow window, never a claim that the references obey Maxwell's equations. The verifiers remain the only
authority on truth (`feedback_let_the_math_determine_truth`). Seal the arithmetic; calibrate to find;
launder nothing. Each reference is weighed by its own evidence, and a reference that disagrees beyond its
error is examined as a possible bad splice before it is believed as new physics.
