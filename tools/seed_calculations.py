#!/usr/bin/env python3
"""THE CALCULATION MAP — every calculation placed by its CANONICAL FORM, so the
connectedness is visible: two calculations from different domains that share a
form are the SAME calculation under a change of variable.

Matt, 2026-09-13: "I want every calculation mapped, so we can identify the
connectedness. Think of a Smith chart." A Smith chart folds the whole impedance
plane onto one bounded disk via a Mobius transform, so impedance, admittance and
reflection are one geometry. This does the same for calculation: the FORM is the
chart, each calculation is a point on it, and calculations sharing a form are
joined (same_form) — the universality of the one kernel, at the calculation level.

NON-DESTRUCTIVE, idempotent, APPEND-only to data/calculation_cards.jsonl.

    python tools/seed_calculations.py --chart     # the connectedness, grouped by form
    python tools/seed_calculations.py --seed      # write the cards
    python tools/seed_calculations.py --check
"""
from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path

STORE = Path("data/calculation_cards.jsonl")

# canonical form id -> (equation, what the form IS)
FORMS: dict[str, tuple[str, str]] = {
    "exponential":     ("y = y0 * e^(kt)",            "change proportional to the present amount"),
    "inverse_square":  ("F = k / r^2",                "a quantity spread over a sphere's growing area"),
    "linear_flux":     ("flux = conductance * gradient", "a flow driven linearly by a difference"),
    "conservation":    ("in = out + change_in_store", "nothing is created or lost — a balance"),
    "wave":            ("d2u/dt2 = c^2 * laplacian(u)", "a disturbance propagating at a fixed speed"),
    "logistic":        ("dP/dt = rP(1 - P/K)",        "self-limited growth toward a ceiling"),
    "power_law":       ("y = a * x^k",                "scale-free proportionality across magnitudes"),
    "gaussian":        ("p(x) ~ e^(-(x-mu)^2/2sigma^2)", "the sum of many small independent effects"),
    "periodic":        ("x = A*cos(omega*t + phi)",   "restoring force proportional to displacement — oscillation/resonance"),
    "mobius_conformal": ("w = (a z + b)/(c z + d)",   "a fractional-linear map — the Smith chart itself; folds a plane onto a disk"),
    "fourier_spectral": ("f(t) = sum c_n e^(i n omega t)", "any signal as a sum of pure frequencies"),
    "optimization":    ("d/dx f = 0",                 "nature and choice both seek a stationary point — least or most"),
    "linear_system":   ("A x = b",                    "many coupled linear relations solved at once"),
    "accumulation":    ("total = integral of a rate", "the whole summed from its rate — area under a curve"),
    "ratio":           ("a/b = c/d",                  "proportional reasoning — scaling and normalization"),
    "modular":         ("a = b (mod n)",              "wrap-around arithmetic — cycles and remainders"),
    "diffusion":       ("du/dt = D * laplacian(u)",   "spreading by random walk — first in time, second in space (the heat equation)"),
    "eigenvalue":      ("A v = lambda v",             "the natural modes and spectrum of an operator — what a system does when left alone"),
    "stochastic":      ("dX = mu dt + sigma dW",      "evolution with a random increment — a drift plus noise (Ito)"),
    "recursion":       ("x_{n+1} = f(x_n)",           "the next state from the present — iterated maps and recurrences"),
    "variational":     ("delta integral L = 0",       "find the FUNCTION that extremizes an integral — calculus of variations (Euler-Lagrange)"),
    "green_function":  ("u = integral G(x,x') f(x') dx'", "the response to a point source, superposed — solving an inhomogeneous linear operator"),
    "convolution":     ("(f*g)(t) = integral f(tau) g(t-tau) dtau", "blend one signal by another — the operation of every linear time-invariant system"),
    # --- finer forms: the model is fractal, so a coarse form is a form-of-forms ---
    # children of ratio
    "proportion":      ("a/b = c/d",                  "direct proportion — scale by a ratio equal to one"),
    "rate":            ("q = extensive / extensive",  "an intensive quantity — a 'per' (density, efficiency, yield)"),
    "linear_map":      ("y = a + b x",                "an affine response — output linear in the input(s)"),
    "product_law":     ("q = f1 * f2 * ...",          "a quantity is the product of its factors"),
    "probability_ratio": ("P(A|B) = P(A,B)/P(B)",     "conditional and joint probability — Bayes"),
    # children of exponential
    "growth":          ("y = y0 e^(+kt)",             "continuous or geometric increase"),
    "decay":           ("y = y0 e^(-kt)",             "relaxation toward a floor — decay and cooling"),
    "discounting":     ("PV = FV/(1+r)^t",            "discrete present value — discounting and inflation"),
    # children of modular
    "cyclic":          ("x mod n (a cycle)",          "wrap-around cycles — clocks, calendars, pitch classes"),
    "check_digit":     ("weighted sum mod n = 0",     "error-detecting checksums — ISBN, Luhn, EAN"),
    "number_theoretic": ("a^x = 1 (mod m)",           "primes, gcd, modular inverse and exponentiation"),
}

# a form can be a finer case of a coarser one — the fractal nesting (child -> parent).
FORM_PARENT: dict[str, str] = {
    "proportion": "ratio", "rate": "ratio", "linear_map": "ratio",
    "product_law": "ratio", "probability_ratio": "ratio",
    "growth": "exponential", "decay": "exponential", "discounting": "exponential",
    "cyclic": "modular", "check_digit": "modular", "number_theoretic": "modular",
}

# (slug, title, formula, domain, form, note)
CALCS: list[tuple] = [
    # --- exponential: change proportional to the amount present ---
    ("compound_interest", "Compound interest", "A = P e^(rt)", "finance", "exponential", "money earns in proportion to the balance"),
    ("radioactive_decay", "Radioactive decay", "N = N0 e^(-lambda t)", "nuclear_physics", "exponential", "nuclei decay in proportion to how many remain"),
    ("newton_cooling", "Newton's law of cooling", "T = T_env + dT0 e^(-kt)", "thermodynamics", "exponential", "heat leaves in proportion to the temperature gap"),
    ("rc_discharge", "RC circuit discharge", "V = V0 e^(-t/RC)", "electrical", "exponential", "charge drains in proportion to the voltage left"),
    ("malthus_growth", "Malthusian population growth", "P = P0 e^(rt)", "ecology", "exponential", "births in proportion to the population"),
    ("beer_lambert", "Beer-Lambert absorption", "I = I0 e^(-a x)", "optics", "exponential", "light lost in proportion to intensity per unit path"),
    ("barometric", "Barometric (isothermal) formula", "p = p0 e^(-mgh/kT)", "meteorology", "exponential", "pressure falls in proportion to itself with height"),
    # --- inverse_square: spread over a sphere ---
    ("newton_gravity", "Newton's gravitation", "F = G m1 m2 / r^2", "physics", "inverse_square", "the field thins as the sphere it crosses grows"),
    ("coulomb", "Coulomb's law", "F = k q1 q2 / r^2", "electrical", "inverse_square", "the same 1/r^2 spreading, for charge"),
    ("light_intensity", "Illuminance falloff", "E = I / r^2", "optics", "inverse_square", "light per area falls as the sphere grows"),
    ("sound_intensity", "Sound intensity falloff", "I = P / (4 pi r^2)", "acoustics", "inverse_square", "acoustic power spread over a growing sphere"),
    # --- linear_flux: flow = conductance * gradient ---
    ("ohms_law", "Ohm's law", "I = V / R", "electrical", "linear_flux", "current is driven by a voltage gradient"),
    ("hookes_law", "Hooke's law", "F = k x", "materials_science", "linear_flux", "restoring flow of force set by a displacement gradient"),
    ("ficks_law", "Fick's law of diffusion", "J = -D dC/dx", "chemistry", "linear_flux", "particle flux driven by a concentration gradient"),
    ("fourier_conduction", "Fourier's heat conduction", "q = -k dT/dx", "thermodynamics", "linear_flux", "heat flux driven by a temperature gradient"),
    ("darcy_flow", "Darcy's law", "Q = -K dh/dl", "hydrology", "linear_flux", "groundwater flux driven by a head gradient"),
    # --- conservation: in = out + change_in_store ---
    ("accounting_identity", "Accounting identity", "Assets = Liabilities + Equity", "finance", "conservation", "value is conserved across the balance sheet"),
    ("kirchhoff_current", "Kirchhoff's current law", "sum(I_in) = sum(I_out)", "electrical", "conservation", "charge into a node equals charge out"),
    ("mass_balance", "Chemical mass balance", "mass_in = mass_out + accumulation", "chemistry", "conservation", "atoms are conserved through a reaction"),
    ("continuity", "Continuity equation", "d(rho)/dt + div(rho v) = 0", "physics", "conservation", "the general law: what flows in must be stored or flow out"),
    ("energy_balance", "First law (energy balance)", "dU = Q - W", "thermodynamics", "conservation", "energy is conserved — the same ledger, for heat and work"),
    # --- wave ---
    ("wave_equation", "The wave equation", "d2u/dt2 = c^2 u_xx", "physics", "wave", "the parent form of every propagating disturbance"),
    ("em_wave", "Electromagnetic waves", "d2E/dt2 = c^2 laplacian(E)", "electrical", "wave", "light is Maxwell's equations in wave form"),
    ("acoustic_wave", "Acoustic waves", "d2p/dt2 = c^2 laplacian(p)", "acoustics", "wave", "pressure obeys the same wave equation as light"),
    ("schrodinger", "Schrodinger equation", "i hbar dPsi/dt = H Psi", "physics", "wave", "matter as a (complex) wave"),
    # --- logistic ---
    ("carrying_capacity", "Logistic population (carrying capacity)", "dP/dt = rP(1 - P/K)", "ecology", "logistic", "growth that slows as it nears the limit"),
    ("epidemic_saturation", "Epidemic saturation (SIR)", "dI/dt = beta S I - gamma I", "medicine", "logistic", "spread self-limits as the susceptible pool empties"),
    ("adoption_curve", "Technology adoption (Bass/S-curve)", "F(t) = 1/(1+e^(-k(t-t0)))", "economics", "logistic", "uptake saturates as the market fills"),
    # --- power_law ---
    ("kleiber", "Kleiber's metabolic law", "B = a M^(3/4)", "biology", "power_law", "metabolism scales as a 3/4 power of mass"),
    ("gutenberg_richter", "Gutenberg-Richter law", "log N = a - b M", "geology", "power_law", "earthquake frequency scales as a power of magnitude"),
    ("zipf_pareto", "Zipf / Pareto law", "f ~ 1/rank^s", "linguistics", "power_law", "word (and wealth) frequency is scale-free"),
    ("kepler_third", "Kepler's third law", "T^2 = a^3", "astronomy", "power_law", "orbital period scales as a power of distance"),
    # --- gaussian ---
    ("central_limit", "Central limit theorem", "mean -> Normal(mu, sigma^2/n)", "statistics", "gaussian", "sums of many small effects go Gaussian"),
    ("measurement_error", "Measurement error", "x = x_true + Normal(0, sigma)", "physics", "gaussian", "independent errors add to a bell curve"),
    ("maxwell_boltzmann", "Maxwell-Boltzmann speeds", "f(v) ~ v^2 e^(-mv^2/2kT)", "thermodynamics", "gaussian", "molecular speeds are Gaussian in each component"),
    # --- periodic ---
    ("shm", "Simple harmonic motion", "x = A cos(omega t + phi)", "physics", "periodic", "a restoring force proportional to displacement"),
    ("lc_resonance", "LC circuit resonance", "omega = 1/sqrt(LC)", "electrical", "periodic", "charge sloshes between L and C — the electrical pendulum"),
    ("pendulum", "Pendulum period", "T = 2 pi sqrt(L/g)", "physics", "periodic", "gravity as the restoring force"),
    # --- mobius_conformal: the Smith chart's own form ---
    ("smith_reflection", "Reflection coefficient (the Smith chart)", "Gamma = (Z - Z0)/(Z + Z0)", "electrical", "mobius_conformal", "the Mobius map that folds the impedance plane onto the chart"),
    ("stereographic", "Stereographic projection", "maps the sphere to the plane conformally", "geography", "mobius_conformal", "the map projection that preserves angles — a conformal map"),
    ("cross_ratio", "The cross-ratio", "(z1,z2;z3,z4)", "geometry", "mobius_conformal", "the invariant every Mobius transform preserves"),
    # --- fourier_spectral: any signal as a sum of frequencies ---
    ("fourier_series", "Fourier series / transform", "f(t) = sum c_n e^(i n w t)", "mathematics", "fourier_spectral", "any periodic signal decomposes into pure tones"),
    ("harmonics_timbre", "Harmonic series & timbre", "f_n = n f_1", "music_theory", "fourier_spectral", "a note's color is its spectrum of overtones"),
    ("spectral_lines", "Atomic spectral lines", "1/lambda = R(1/n1^2 - 1/n2^2)", "atomic", "fourier_spectral", "atoms emit a discrete spectrum — their fingerprint"),
    ("xrd_diffraction", "X-ray diffraction (Bragg)", "n lambda = 2 d sin(theta)", "materials_science", "fourier_spectral", "a crystal is read from its diffraction spectrum — a Fourier transform of the lattice"),
    ("fft_signal", "The Fast Fourier Transform", "X_k = sum x_n e^(-2pi i kn/N)", "computer_science", "fourier_spectral", "the algorithm that turns a signal into its spectrum"),
    # --- optimization: seek a stationary point ---
    ("least_action", "Principle of least action", "delta S = 0", "physics", "optimization", "a system's path extremizes the action — physics as optimization"),
    ("least_squares", "Least squares", "min sum (y - f)^2", "statistics", "optimization", "the best fit minimizes squared error"),
    ("fermat_time", "Fermat's least time", "delta (path time) = 0", "optics", "optimization", "light takes the path of least time — Snell's law falls out"),
    ("marginal_optimum", "Marginal optimum", "MC = MR", "economics", "optimization", "profit is maximized where marginal cost meets marginal revenue"),
    ("max_entropy", "Maximum entropy inference", "max H subject to constraints", "information_theory", "optimization", "the least-biased distribution is the one of maximum entropy"),
    # --- linear_system: A x = b ---
    ("mesh_analysis", "Circuit mesh analysis", "Z i = v", "electrical", "linear_system", "a circuit is a linear system of loop equations"),
    ("stiffness_method", "Structural stiffness method", "K u = F", "architecture", "linear_system", "a structure's deflections solve a linear system"),
    ("leontief_io", "Leontief input-output", "x = (I - A)^-1 d", "economics", "linear_system", "an economy's outputs solve a linear system of interdependencies"),
    ("markov_chain", "Markov chain steady state", "pi P = pi", "probability", "linear_system", "the long-run distribution is a linear eigen-equation"),
    ("normal_equations", "Linear regression (normal equations)", "(X^T X) b = X^T y", "statistics", "linear_system", "the best-fit coefficients solve a linear system"),
    # --- accumulation: whole from a rate ---
    ("distance_from_velocity", "Distance from velocity", "x = integral v dt", "physics", "accumulation", "position accumulates velocity over time"),
    ("work_from_force", "Work from force", "W = integral F dx", "physics", "accumulation", "work accumulates force over distance"),
    ("charge_from_current", "Charge from current", "Q = integral I dt", "electrical", "accumulation", "charge accumulates current over time"),
    ("present_value_integral", "Continuous present value", "PV = integral CF e^(-rt) dt", "finance", "accumulation", "value accumulates discounted cash flow over time"),
    ("dose_accumulation", "Drug exposure (AUC)", "AUC = integral C dt", "medicine", "accumulation", "total exposure accumulates concentration over time"),
    # --- ratio: proportional reasoning ---
    ("stoichiometry", "Stoichiometry (mole ratios)", "n_A / n_B = a / b", "chemistry", "ratio", "reactants combine in fixed proportion"),
    ("similar_triangles", "Similar triangles", "a/A = b/B = c/C", "geometry", "ratio", "shape is scale-invariant proportion"),
    ("unit_conversion", "Unit conversion", "x * (unit_b / unit_a)", "units", "ratio", "converting is multiplying by a ratio equal to one"),
    ("map_scale", "Map scale", "map_dist / real_dist", "geography", "ratio", "a map is reality times a constant ratio"),
    ("gear_ratio", "Gear ratio", "w_out/w_in = N_in/N_out", "physics", "ratio", "gears trade speed for torque by a tooth ratio"),
    # --- modular: wrap-around arithmetic ---
    ("clock_arithmetic", "Clock / calendar arithmetic", "(h + t) mod 12", "calendar_time", "modular", "time wraps — hours and weekdays are modular"),
    ("checksum_mod", "Checksums (mod arithmetic)", "sum * w mod m", "cybersecurity", "modular", "ISBN, Luhn and CRC all catch errors by a modulus"),
    ("octave_equivalence", "Octave equivalence", "pitch class = note mod 12", "music_theory", "modular", "pitch is cyclic — an octave is mod 12"),
    ("cyclic_group", "Cyclic groups (modular arithmetic)", "Z/nZ", "mathematics", "modular", "the arithmetic of a finite cycle — the root of the rest"),
    ("rsa_modexp", "RSA (modular exponentiation)", "c = m^e mod n", "cybersecurity", "modular", "public-key encryption is exponentiation in a finite ring"),
    ("diffie_hellman", "Diffie-Hellman key exchange", "s = g^(ab) mod p", "cybersecurity", "modular", "a shared secret from public modular powers"),
    # --- more exponential ---
    ("capacitor_charge", "RC charging curve", "V = V0 (1 - e^(-t/RC))", "electrical", "exponential", "the mirror of discharge — approach in proportion to the gap remaining"),
    ("bacterial_growth", "Bacterial exponential growth", "N = N0 2^(t/td)", "biology", "exponential", "each cell divides — doublings in proportion to the count"),
    # --- more inverse_square ---
    ("gravitational_field", "Gravitational field strength", "g = G M / r^2", "physics", "inverse_square", "the field, not the force — same sphere-thinning geometry"),
    # --- more conservation ---
    ("bernoulli", "Bernoulli's equation", "p + rho v^2/2 + rho g h = const", "physics", "conservation", "energy per volume is conserved along a streamline"),
    ("momentum_conservation", "Conservation of momentum", "sum(m v) = const", "physics", "conservation", "total momentum is conserved absent external force"),
    # --- more wave ---
    ("string_wave", "Vibrating string speed", "v = sqrt(T/mu)", "music_theory", "wave", "a plucked string is the wave equation with tension and mass"),
    ("seismic_wave", "Seismic P- and S-waves", "v = sqrt(modulus/rho)", "geology", "wave", "the earth rings with the same wave equation"),
    # --- more periodic ---
    ("ac_steady_state", "AC steady state (phasors)", "v(t) = V cos(omega t + phi)", "electrical", "periodic", "the grid is one driven oscillation — solved as a rotating phasor"),
    # --- more fourier_spectral ---
    ("nmr_spectrum", "NMR spectroscopy", "f = gamma B0 / 2pi", "chemistry", "fourier_spectral", "nuclei resonate at a field-set frequency — a molecular spectrum"),
    # --- more linear_flux ---
    ("newton_viscosity", "Newton's law of viscosity", "tau = mu du/dy", "physics", "linear_flux", "shear stress driven by a velocity gradient"),
    # --- more optimization ---
    ("lagrange_multipliers", "Lagrange multipliers", "grad f = lambda grad g", "mathematics", "optimization", "a constrained optimum: the gradient aligns with the constraint"),
    ("linear_program", "Linear programming (simplex)", "max c.x  s.t. A x <= b", "economics", "optimization", "the best plan sits at a vertex of the feasible polytope"),
    # --- more accumulation ---
    ("entropy_integral", "Clausius entropy", "dS = integral dQ/T", "thermodynamics", "accumulation", "entropy accumulates heat weighted by inverse temperature"),
    ("impulse", "Impulse-momentum", "J = integral F dt", "physics", "accumulation", "change in momentum accumulates force over time"),
    ("center_of_mass", "Center of mass", "R = (1/M) integral r dm", "physics", "accumulation", "the balance point accumulates position weighted by mass"),
    # --- more power_law ---
    ("allometry", "Allometric scaling", "Y = a M^b", "biology", "power_law", "organ size, lifespan and rate all scale as powers of body mass"),
    ("stefan_boltzmann", "Stefan-Boltzmann law", "P = sigma A T^4", "thermodynamics", "power_law", "radiated power scales as the fourth power of temperature"),
    # === diffusion: du/dt = D laplacian(u) ===
    ("heat_equation", "The heat equation", "du/dt = alpha u_xx", "thermodynamics", "diffusion", "the parent form — temperature spreads by random molecular walk"),
    ("ficks_second", "Fick's second law", "dC/dt = D C_xx", "chemistry", "diffusion", "concentration obeys the same heat equation"),
    ("black_scholes", "Black-Scholes equation", "dV/dt + rS dV/dS + sigma^2 S^2/2 d2V/dS2 = rV", "finance", "diffusion", "an option price diffuses — the heat equation in disguise"),
    ("brownian_diffusion", "Brownian motion (mean square)", "<x^2> = 2 D t", "physics", "diffusion", "a pollen grain's spread — diffusion seen from one particle"),
    ("reaction_diffusion", "Reaction-diffusion (Turing patterns)", "du/dt = D u_xx + f(u)", "biology", "diffusion", "spots and stripes emerge where diffusion meets reaction"),
    # === eigenvalue: A v = lambda v ===
    ("energy_eigenvalues", "Energy levels (stationary Schrodinger)", "H psi = E psi", "physics", "eigenvalue", "an atom's allowed energies are the eigenvalues of its Hamiltonian"),
    ("pca", "Principal component analysis", "C v = lambda v", "statistics", "eigenvalue", "the axes of a cloud of data are the eigenvectors of its covariance"),
    ("vibration_modes", "Normal modes of vibration", "K x = omega^2 M x", "architecture", "eigenvalue", "a structure's natural frequencies are an eigenproblem"),
    ("pagerank", "PageRank", "r = M r", "computer_science", "eigenvalue", "a page's rank is the dominant eigenvector of the link matrix"),
    ("euler_buckling", "Euler buckling load", "P_cr = pi^2 E I / L^2", "architecture", "eigenvalue", "the critical load is the smallest eigenvalue of the column"),
    # === stochastic: dX = mu dt + sigma dW ===
    ("geometric_brownian", "Geometric Brownian motion", "dS = mu S dt + sigma S dW", "finance", "stochastic", "the standard model of an asset price — drift plus proportional noise"),
    ("langevin", "Langevin equation", "m dv = -gamma v dt + sigma dW", "physics", "stochastic", "a particle kicked by thermal noise against friction"),
    ("genetic_drift", "Wright-Fisher genetic drift", "dp = sqrt(p(1-p)/2N) dW", "biology", "stochastic", "allele frequencies wander randomly in a finite population"),
    ("ornstein_uhlenbeck", "Ornstein-Uhlenbeck (mean reversion)", "dx = theta(mu - x) dt + sigma dW", "statistics", "stochastic", "noise pulled back toward a mean — rates, spreads, velocities"),
    # === recursion: x_{n+1} = f(x_n) ===
    ("fibonacci", "Fibonacci recurrence", "F_n = F_{n-1} + F_{n-2}", "mathematics", "recursion", "each term the sum of the last two — its ratio tends to phi"),
    ("newton_method", "Newton's method", "x_{n+1} = x_n - f/f'", "mathematics", "recursion", "chase a root by following the tangent, again and again"),
    ("logistic_map", "The logistic map", "x_{n+1} = r x_n (1 - x_n)", "mathematics", "recursion", "the simplest recursion that becomes chaos"),
    ("euler_integration", "Euler's method (ODE stepping)", "y_{n+1} = y_n + h f(y_n)", "computer_science", "recursion", "solve a differential equation by stepping the rate forward"),
    ("compound_discrete", "Discrete compound interest", "A_{n+1} = A_n (1 + r)", "finance", "recursion", "the same growth as the exponential, taken one period at a time"),
    ("gradient_descent", "Gradient descent", "x_{n+1} = x_n - eta grad f", "computer_science", "recursion", "a recursion that walks downhill to an optimum — where learning lives"),
    ("kalman_filter", "Kalman filter", "x_k = A x_{k-1} + K(z_k - H x)", "computer_science", "recursion", "recursively fuse a prediction with a measurement — optimal tracking"),
    # === variational: delta integral L = 0 ===
    ("euler_lagrange", "Euler-Lagrange equation", "d/dt(dL/dq') - dL/dq = 0", "physics", "variational", "the equation a path must satisfy to extremize the action"),
    ("brachistochrone", "Brachistochrone (fastest descent)", "minimize integral ds/v", "mathematics", "variational", "the curve of quickest slide — the problem that founded the field"),
    ("geodesic", "Geodesic equation", "d2x/ds2 + Gamma (dx/ds)^2 = 0", "physics", "variational", "the straightest possible path on a curved space"),
    ("catenary", "Catenary (hanging chain)", "y = a cosh(x/a)", "architecture", "variational", "the shape that minimizes potential energy — and the ideal arch inverted"),
    ("minimal_surface", "Minimal surfaces (soap films)", "mean curvature H = 0", "mathematics", "variational", "the surface of least area spanning a boundary"),
    # === green_function: response to a point source, superposed ===
    ("electrostatic_potential", "Electrostatic potential (Poisson)", "phi = integral G rho dV", "electrical", "green_function", "the potential is the point-charge response summed over all charge"),
    ("gravitational_potential", "Newtonian potential", "phi = -integral G m / r dV", "physics", "green_function", "the same Green's function of the Laplacian, for mass"),
    ("heat_kernel", "The heat kernel", "G(x,t) ~ e^(-x^2/4Dt)/sqrt(t)", "thermodynamics", "green_function", "the fundamental solution — a point of heat spreading into a Gaussian"),
    ("feynman_propagator", "Feynman propagator", "amplitude = <x'| e^(-iHt) |x>", "physics", "green_function", "the quantum response to a point source in spacetime"),
    # === convolution: (f*g)(t) = integral f(tau) g(t-tau) dtau ===
    ("impulse_response", "LTI system response", "y(t) = (h * x)(t)", "electrical", "convolution", "any linear time-invariant system is convolution with its impulse response"),
    ("sum_of_randoms", "Density of a sum (convolution)", "p_{X+Y} = p_X * p_Y", "probability", "convolution", "add independent variables and their densities convolve — the road to the bell curve"),
    ("psf_blur", "Point-spread blur", "I' = I * PSF", "optics", "convolution", "every lens convolves the scene with its point-spread function"),
    ("moving_average", "Moving-average filter", "y = x * kernel", "statistics", "convolution", "smoothing is convolution with a window"),
    ("cnn_layer", "Convolutional neural network layer", "feature = input * filter", "computer_science", "convolution", "vision models learn the filters they convolve with"),
]

# calc slug -> the parent THEORY card on THE FLOOR it rests on (joins the two maps into one body).
# Only confident links; a calc with no clean parent theory is left unlinked — a gap stays a gap.
CALC_THEORY: dict[str, str] = {
    "compound_interest": "card_theory_time_value_of_money_discounting",
    "radioactive_decay": "card_theory_nuclear_decay_binding_energy",
    "rc_discharge": "card_theory_ohm_s_law_circuit_theory",
    "malthus_growth": "card_theory_population_ecology",
    "barometric": "card_theory_atmospheric_thermodynamics",
    "newton_gravity": "card_theory_newton_s_law_of_universal_gravitation",
    "coulomb": "card_theory_maxwell_s_equations_classical_electromagnetism",
    "light_intensity": "card_theory_wave_optics",
    "sound_intensity": "card_theory_acoustic_wave_theory",
    "ohms_law": "card_theory_ohm_s_law_circuit_theory",
    "hookes_law": "card_theory_elasticity",
    "darcy_flow": "card_theory_hydrologic_cycle_open_channel_flow",
    "accounting_identity": "card_theory_double_entry_accounting_identity",
    "kirchhoff_current": "card_theory_ohm_s_law_circuit_theory",
    "mass_balance": "card_theory_law_of_conservation_of_mass",
    "continuity": "card_theory_law_of_conservation_of_mass",
    "energy_balance": "card_theory_conservation_of_energy",
    "em_wave": "card_theory_maxwell_s_equations_classical_electromagnetism",
    "acoustic_wave": "card_theory_acoustic_wave_theory",
    "schrodinger": "card_theory_quantum_mechanics",
    "carrying_capacity": "card_theory_population_ecology",
    "epidemic_saturation": "card_theory_germ_theory_of_disease",
    "gutenberg_richter": "card_theory_seismology_earthquake_magnitude",
    "kepler_third": "card_theory_heliocentrism_kepler_s_laws",
    "central_limit": "card_theory_central_limit_theorem",
    "measurement_error": "card_theory_central_limit_theorem",
    "maxwell_boltzmann": "card_theory_kinetic_theory_of_gases",
    "shm": "card_theory_elasticity",
    "lc_resonance": "card_theory_ohm_s_law_circuit_theory",
    "pendulum": "card_theory_newton_s_three_laws_of_motion",
    "smith_reflection": "card_theory_maxwell_s_equations_classical_electromagnetism",
    "harmonics_timbre": "card_theory_music_theory",
    "spectral_lines": "card_theory_bohr_quantum_model_of_the_atom",
    "xrd_diffraction": "card_theory_wave_optics",
    "least_action": "card_theory_newton_s_three_laws_of_motion",
    "fermat_time": "card_theory_wave_optics",
    "marginal_optimum": "card_theory_supply_demand_market_equilibrium",
    "max_entropy": "card_theory_shannon_information_theory",
    "mesh_analysis": "card_theory_ohm_s_law_circuit_theory",
    "stiffness_method": "card_theory_structural_statics",
    "leontief_io": "card_theory_supply_demand_market_equilibrium",
    "markov_chain": "card_theory_kolmogorov_probability_axioms",
    "normal_equations": "card_theory_linear_algebra",
    "distance_from_velocity": "card_theory_newton_s_three_laws_of_motion",
    "work_from_force": "card_theory_newton_s_three_laws_of_motion",
    "charge_from_current": "card_theory_ohm_s_law_circuit_theory",
    "present_value_integral": "card_theory_time_value_of_money_discounting",
    "dose_accumulation": "card_theory_pharmacokinetics",
    "stoichiometry": "card_theory_stoichiometry_the_mole_concept",
    "similar_triangles": "card_theory_euclidean_geometry_the_parallel_postulate",
    "gear_ratio": "card_theory_newton_s_three_laws_of_motion",
    "clock_arithmetic": "card_theory_calendar_theory",
    "checksum_mod": "card_theory_cryptographic_security",
    "octave_equivalence": "card_theory_music_theory",
    "cyclic_group": "card_theory_fundamental_theorem_of_arithmetic",
    # --- gap closers: parent theories that DO exist on THE FLOOR ---
    "newton_cooling": "card_theory_heat_transfer",
    "beer_lambert": "card_theory_spectroscopy",
    "ficks_law": "card_theory_kinetic_theory_of_gases",
    "fourier_conduction": "card_theory_heat_transfer",
    "wave_equation": "card_theory_differential_equations",
    "adoption_curve": "card_theory_epidemiology_models",
    "kleiber": "card_theory_scaling_laws",
    "zipf_pareto": "card_theory_power_laws",
    "stereographic": "card_theory_map_projections",
    "fourier_series": "card_theory_fourier_analysis___signal_processing",
    "fft_signal": "card_theory_fourier_analysis___signal_processing",
    "least_squares": "card_theory_optimization",
    "unit_conversion": "card_theory_dimensional_analysis",
    "map_scale": "card_theory_map_projections",
    "cross_ratio": "card_theory_projective_geometry",
    # --- new calculations ---
    "rsa_modexp": "card_theory_cryptographic_security",
    "diffie_hellman": "card_theory_diffie_hellman_key_exchange",
    "capacitor_charge": "card_theory_ohm_s_law_circuit_theory",
    "bacterial_growth": "card_theory_population_ecology",
    "gravitational_field": "card_theory_newton_s_law_of_universal_gravitation",
    "bernoulli": "card_theory_fluid_mechanics",
    "momentum_conservation": "card_theory_conservation_of_linear_angular_momentum",
    "string_wave": "card_theory_acoustic_wave_theory",
    "seismic_wave": "card_theory_seismology_earthquake_magnitude",
    "ac_steady_state": "card_theory_ac_polyphase_power",
    "nmr_spectrum": "card_theory_spectroscopy",
    "newton_viscosity": "card_theory_fluid_mechanics",
    "lagrange_multipliers": "card_theory_optimization",
    "linear_program": "card_theory_linear_programming_duality",
    "entropy_integral": "card_theory_second_law_of_thermodynamics",
    "impulse": "card_theory_conservation_of_linear_angular_momentum",
    "center_of_mass": "card_theory_newton_s_three_laws_of_motion",
    "allometry": "card_theory_scaling_laws",
    "stefan_boltzmann": "card_theory_electromagnetic_spectrum",
    "heat_equation": "card_theory_heat_transfer",
    "ficks_second": "card_theory_kinetic_theory_of_gases",
    "black_scholes": "card_theory_modern_portfolio_theory",
    "brownian_diffusion": "card_theory_statistical_mechanics",
    "reaction_diffusion": "card_theory_emergence",
    "energy_eigenvalues": "card_theory_quantum_mechanics",
    "pca": "card_theory_singular_value_decomposition",
    "vibration_modes": "card_theory_structural_statics",
    "pagerank": "card_theory_network_science",
    "euler_buckling": "card_theory_structural_statics",
    "geometric_brownian": "card_theory_modern_portfolio_theory",
    "langevin": "card_theory_statistical_mechanics",
    "genetic_drift": "card_theory_hardy_weinberg_equilibrium",
    "ornstein_uhlenbeck": "card_theory_stochastic_processes",
    "fibonacci": "card_theory_golden_ratio_phyllotaxis",
    "newton_method": "card_theory_numerical_analysis",
    "logistic_map": "card_theory_dynamical_systems___deterministic_chaos",
    "euler_integration": "card_theory_numerical_analysis",
    "compound_discrete": "card_theory_time_value_of_money_discounting",
    "gradient_descent": "card_theory_optimization",
    "kalman_filter": "card_theory_control_theory___cybernetics__feedback__stability",
    "euler_lagrange": "card_theory_noether_s_theorem__symmetry_and_conservation",
    "brachistochrone": "card_theory_optimization",
    "geodesic": "card_theory_differential_geometry",
    "catenary": "card_theory_structural_statics",
    "minimal_surface": "card_theory_differential_geometry",
    "electrostatic_potential": "card_theory_maxwell_s_equations_classical_electromagnetism",
    "gravitational_potential": "card_theory_newton_s_law_of_universal_gravitation",
    "heat_kernel": "card_theory_heat_transfer",
    "feynman_propagator": "card_theory_standard_model_quantum_field_theory",
    "impulse_response": "card_theory_fourier_analysis___signal_processing",
    "sum_of_randoms": "card_theory_central_limit_theorem",
    "psf_blur": "card_theory_wave_optics",
    "moving_average": "card_theory_fourier_analysis___signal_processing",
    "cnn_layer": "card_theory_statistical_learning_theory__bias_variance__generali",
}


# --- merge in the engine's own verifier computations (found from src/concordance/verifiers) ---
# The curated calculations above are the core; the verifiers are the deterministic checks the
# concordance actually runs. seed_verifiers places only the COMPUTATIONAL ones, by form, with the
# formula as evidence; its --check proves every placed name is a real verifier in the engine source.
try:
    from seed_verifiers import NEW_FORMS as _VFORMS, verifier_calcs as _vcalcs, verifier_theory as _vtheory
    FORMS.update(_VFORMS)
    CALCS = CALCS + _vcalcs()
    CALC_THEORY = {**CALC_THEORY, **_vtheory()}
except Exception:  # noqa: BLE001 — verifiers are optional; the curated core stands alone without them
    pass


# --- REFINE: split the coarse forms into their finer children (the model is fractal) ---
# One slug -> child-form map, applied to the merged CALCS, so both curated and verifier
# calculations move to the finer form without touching 100+ tuples. Every slug that was
# on ratio / exponential / modular appears here exactly once.
_REFINE_GROUPS: dict[str, list[str]] = {
    # ratio -> proportion / rate / linear_map / product_law / probability_ratio
    "proportion": ["stoichiometry", "similar_triangles", "unit_conversion", "map_scale", "gear_ratio",
                   "v_units_conversion", "v_music_frequency_ratio", "v_acoustics_doppler_shift",
                   "v_periodic_table_atomic_mass_weighted_average", "v_optics_photon_energy",
                   "v_optics_de_broglie", "v_optics_magnification", "v_optics_thin_lens"],
    "rate": ["v_agriculture_stocking_density", "v_architecture_floor_area_ratio",
             "v_architecture_window_wall_ratio", "v_architecture_occupant_load",
             "v_economics_gdp_per_capita", "v_economics_price_elasticity", "v_energy_efficiency",
             "v_energy_runtime", "v_labor_annual_to_hourly", "v_materials_science_density",
             "v_medicine_bmi", "v_nuclear_physics_binding_energy_per_nucleon", "v_real_estate_cap_rate",
             "v_real_estate_gross_rent_mult", "v_real_estate_loan_to_value", "v_real_estate_debt_service_cov",
             "v_real_estate_rental_yield", "v_retrieval_precision", "v_retrieval_recall_of_known",
             "v_sports_analytics_games_behind", "v_thermodynamics_carnot_efficiency",
             "v_thermodynamics_entropy_change", "v_verify_molarity", "v_construction_beam_load",
             "v_construction_paint_coverage"],
    "linear_map": ["v_exercise_science_max_heart_rate", "v_exercise_science_target_heart_rate_zone",
                   "v_medicine_a1c_to_eag", "v_medicine_egfr_cockcroft", "v_medicine_map",
                   "v_photography_hyperfocal_distance", "v_soil_science_lime_requirement",
                   "v_labor_take_home_pay", "v_labor_overtime_pay", "v_nutrition_macronutrient_calories",
                   "v_oceanography_pressure_at_depth"],
    "product_law": ["v_electrical_power", "v_thermodynamics_ideal_gas_law", "v_thermodynamics_specific_heat",
                    "v_physics_newtons_second_law", "v_hydrology_rational_runoff",
                    "v_exercise_science_energy_expenditure", "v_medicine_drug_dosage", "v_labor_gross_pay",
                    "v_construction_rebar_weight", "v_soil_science_npk_requirement", "v_soil_science_irrigation_req",
                    "v_ecology_carbon_footprint_transport", "v_economics_simple_interest",
                    "v_materials_science_thermal_expansion", "v_energy_battery_sizing",
                    "v_energy_solar_daily_yield", "v_construction_floor_tiles", "v_law_flsa_overtime",
                    "v_probability_binomial_mean"],
    "probability_ratio": ["v_probability_bayes", "v_probability_conditional", "v_probability_independence",
                          "v_quantum_computing_quantum_fidelity"],
    # exponential -> growth / decay / discounting
    "growth": ["compound_interest", "malthus_growth", "bacterial_growth", "v_economics_compound_interest",
               "v_economics_future_value", "v_finance_compound_interest", "v_music_equal_temperament_freq",
               "v_real_estate_monthly_mortgage", "v_meteorology_saturation_vapor_pressure",
               "v_thermodynamics_clausius_clapeyron"],
    "decay": ["radioactive_decay", "newton_cooling", "rc_discharge", "beer_lambert", "barometric",
              "capacitor_charge", "v_geology_radiometric_decay", "v_nuclear_physics_radioactive_decay",
              "v_electrical_rc_time_constant", "v_ecology_trophic_efficiency"],
    "discounting": ["v_economics_present_value", "v_economics_inflation_adjusted", "v_finance_present_value"],
    # modular -> cyclic / check_digit / number_theoretic
    "cyclic": ["clock_arithmetic", "octave_equivalence", "v_calendar_time_leap_year",
               "v_calendar_time_day_of_week", "v_calendar_time_utc_offset", "v_music_interval_semitones",
               "v_music_scale_membership"],
    "check_digit": ["checksum_mod", "v_doc_validation_isbn10", "v_doc_validation_isbn13",
                    "v_doc_validation_luhn", "v_doc_validation_ean_upc"],
    "number_theoretic": ["cyclic_group", "rsa_modexp", "diffie_hellman", "v_number_theory_primality",
                         "v_number_theory_gcd", "v_number_theory_modular_inverse",
                         "v_number_theory_perfect_number", "v_quantum_computing_shor_period"],
}
REFINE: dict[str, str] = {slug: child for child, slugs in _REFINE_GROUPS.items() for slug in slugs}
CALCS = [(s, t, f, d, REFINE.get(s, form), n) for (s, t, f, d, form, n) in CALCS]


def _theory_ids() -> set[str]:
    ids = set()
    p = Path("data/theory_cards.jsonl")
    if p.exists():
        for line in p.read_text(encoding="utf-8").splitlines():
            if line.strip():
                try:
                    ids.add(json.loads(line)["id"])
                except (ValueError, KeyError):
                    pass
    return ids


def _existing_ids() -> set[str]:
    ids = set()
    if STORE.exists():
        for line in STORE.read_text(encoding="utf-8").splitlines():
            if line.strip():
                try:
                    ids.add(json.loads(line)["id"])
                except (ValueError, KeyError):
                    pass
    return ids


def _form_spine(form: str) -> dict:
    eq, desc = FORMS[form]
    conns = []
    parent = FORM_PARENT.get(form)
    if parent:  # the fractal nesting, made explicit in the card graph
        conns.append({"to_card_id": f"card_form_{parent}", "relationship": "specializes",
                      "evidence": f"a finer case of the {parent} form ({FORMS[parent][0]})"})
    return {
        "id": f"card_form_{form}", "kind": "reference",
        "title": f"Canonical form: {form}  ({eq})",
        "body": f"A canonical mathematical FORM: {eq} — {desc}. Every calculation joined here is this same computation under a change of variable; the domains differ, the form does not."
                + (f" It is a finer case of the {parent} form." if parent else ""),
        "source": {"label": "The Calculation Map — canonical forms", "url": "", "domain": "mathematics", "authority_tier": "reference"},
        "shelf": "forms", "box": "form", "bands": ["form", form, "calculation-map"],
        "subject": form, "connections": conns, "author": "engine", "created_at": 0.0, "updated_at": 0.0,
        "visibility": "public", "lifecycle_stage": "public", "volatility": "permanent",
        "surface": "secular", "generated": False,
        "extra": {"equation": eq, "form": form, "parent_form": parent or ""},
    }


def _calc_card(slug, title, formula, domain, form, note, theory_ids=frozenset()) -> dict:
    eq, desc = FORMS[form]
    conns = [{"to_card_id": f"card_form_{form}", "relationship": "same_form",
              "evidence": f"an instance of the {form} form: {eq}"}]
    tid = CALC_THEORY.get(slug)
    if tid and tid in theory_ids:
        conns.append({"to_card_id": tid, "relationship": "rests_on",
                      "evidence": f"this calculation is the computational edge of the {tid.replace('card_theory_', '').replace('_', ' ')} theory"})
    return {
        "id": f"card_calc_{slug}", "kind": "reference", "title": title,
        "body": f"{title} — {domain}. Formula: {formula}. Canonical FORM: {form} ({eq}) — {note}. Same form, different domain: this is the {form} computation under a change of variable.",
        "source": {"label": "The Calculation Map — every calculation, mapped by form", "url": "", "domain": domain, "authority_tier": "reference"},
        "shelf": "calculations", "box": "calc", "bands": ["calculation", domain, form],
        "subject": title, "connections": conns,
        "author": "engine", "created_at": 0.0, "updated_at": 0.0, "visibility": "public",
        "lifecycle_stage": "public", "volatility": "permanent", "surface": "secular", "generated": False,
        "extra": {"form": form, "formula": formula, "domain": domain, "equation": eq},
    }


def cmd_check() -> int:
    bad = [c[0] for c in CALCS if c[4] not in FORMS]
    if bad:
        print("calcs with unknown form:", bad); return 3
    parents = set(FORM_PARENT.values())
    stranded = [c[0] for c in CALCS if c[4] in parents]
    if stranded:
        print(f"calcs stranded on a bare parent form (add to REFINE): {stranded}"); return 3
    leaves = [f for f in FORMS if f not in parents]
    print(f"OK: {len(FORMS)} forms ({len(leaves)} leaf, {len(parents)} parent), "
          f"{len(CALCS)} calculations, all on leaf forms.")
    return 0


def cmd_chart() -> int:
    by = defaultdict(list)
    for c in CALCS:
        by[c[4]].append(c)
    print("THE CALCULATION MAP — calculations grouped by canonical form.\n"
          "Each block is ONE calculation wearing many domains' clothes.\n")
    for form, (eq, desc) in FORMS.items():
        rows = by.get(form, [])
        if not rows:
            continue
        doms = sorted({r[3] for r in rows})
        print(f"== {form}   {eq}   ({desc})")
        for slug, title, formula, domain, _f, note in rows:
            print(f"     {domain:16} {title:34} {formula}")
        print(f"     -> {len(rows)} calculations across {len(doms)} domains, ONE form.\n")
    return 0


def cmd_seed() -> int:
    existing = _existing_ids()
    tids = _theory_ids()
    cards = []
    for form in FORMS:
        sid = f"card_form_{form}"
        if sid not in existing:
            cards.append(_form_spine(form))
    for c in CALCS:
        cid = f"card_calc_{c[0]}"
        if cid not in existing:
            cards.append(_calc_card(*c, theory_ids=tids))
    if not cards:
        print("nothing to add (idempotent).")
        return 0
    STORE.parent.mkdir(parents=True, exist_ok=True)
    with STORE.open("a", encoding="utf-8") as fh:
        for card in cards:
            fh.write(json.dumps(card, ensure_ascii=False) + "\n")
    n_forms = sum(1 for c in cards if c["shelf"] == "forms")
    print(f"appended {len(cards)} cards ({n_forms} form-spines + {len(cards)-n_forms} calculations) -> {STORE}")
    return 0


def cmd_rebuild() -> int:
    """Rewrite the calc store from CALCS, cross-linking each calc to its parent theory on THE FLOOR.

    Safe: the calc store is fully generated from CALCS (no hand-enrichment to lose), so a rewrite
    is deterministic. This is how the calc <-> theory links are applied to existing cards.
    """
    if cmd_check():
        return 3
    tids = _theory_ids()
    unresolved = sorted({t for t in CALC_THEORY.values() if t not in tids})
    if unresolved:
        print("WARN unresolved theory targets (link skipped for these):")
        for t in unresolved:
            print("   ", t)
    cards = [_form_spine(f) for f in FORMS]
    linked = 0
    for c in CALCS:
        card = _calc_card(*c, theory_ids=tids)
        if any(cn["relationship"] == "rests_on" for cn in card["connections"]):
            linked += 1
        cards.append(card)
    STORE.parent.mkdir(parents=True, exist_ok=True)
    STORE.write_text("\n".join(json.dumps(c, ensure_ascii=False) for c in cards) + "\n", encoding="utf-8")
    print(f"rebuilt {STORE}: {len(FORMS)} forms + {len(CALCS)} calculations, "
          f"{linked}/{len(CALCS)} cross-linked to their parent theory on THE FLOOR")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--chart", action="store_true")
    ap.add_argument("--seed", action="store_true")
    ap.add_argument("--rebuild", action="store_true", help="rewrite the store, cross-linking calcs to theories")
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()
    if args.check:
        return cmd_check()
    if args.rebuild:
        return cmd_rebuild()
    if args.seed:
        if cmd_check():
            return 3
        return cmd_seed()
    return cmd_chart()


if __name__ == "__main__":
    raise SystemExit(main())
