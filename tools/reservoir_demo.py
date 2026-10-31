#!/usr/bin/env python3
"""RESERVOIR COMPUTING, measured — a fixed, untrained reservoir plus one trained LINEAR readout remembers the past;
the same readout on the raw input remembers nothing. Pure Python, seeded, no dependency (the engine's discipline).

    python tools/reservoir_demo.py            # N=100 units, Jaeger's memory-capacity task
    python tools/reservoir_demo.py 50 7       # N units, seed

THE TASK (Jaeger 2001, "Short term memory in echo state networks", GMD Report 152): drive the reservoir with an
i.i.d. uniform input u(t) in [-1,1]; for each delay k train a linear readout to reconstruct u(t-k) from the
reservoir state x(t); the MEMORY CAPACITY is MC = sum_k r^2_k (the squared correlation on held-out data), and
Jaeger proved MC <= N. The CONTROL trains the identical readout on [u(t), 1] alone — no reservoir — so whatever
memory appears is the reservoir's, not the regression's.

THE RESERVOIR is never trained: W is random (density 0.1), scaled to spectral radius 0.9 (the echo-state
condition — fading memory), W_in random; x(t+1) = tanh(W x(t) + W_in u(t+1)). THE READOUT is ridge regression
on [x(t), 1] — one closed-form solve per delay, sharing one Gram matrix. Trained weights: N+1 per output.
"""
from __future__ import annotations

import math
import random
import sys


def spectral_radius(W, iters=300):
    n = len(W)
    v = [1.0] * n
    lam = 0.0
    for _ in range(iters):
        w = [sum(W[i][j] * v[j] for j in range(n)) for i in range(n)]
        lam = math.sqrt(sum(a * a for a in w))
        if lam == 0:
            return 0.0
        v = [a / lam for a in w]
    return lam


def cholesky_solve(A, bs):
    """Solve A w = b for several b (A symmetric positive definite): one factorization, many solves."""
    n = len(A)
    L = [[0.0] * n for _ in range(n)]
    for i in range(n):
        for j in range(i + 1):
            s = A[i][j] - sum(L[i][k] * L[j][k] for k in range(j))
            L[i][j] = math.sqrt(max(s, 1e-18)) if i == j else s / L[j][j]
    outs = []
    for b in bs:
        y = [0.0] * n
        for i in range(n):
            y[i] = (b[i] - sum(L[i][k] * y[k] for k in range(i))) / L[i][i]
        w = [0.0] * n
        for i in range(n - 1, -1, -1):
            w[i] = (y[i] - sum(L[k][i] * w[k] for k in range(i + 1, n))) / L[i][i]
        outs.append(w)
    return outs


def memory_capacity(features, u, delays, train, test, ridge=1e-6):
    """Train one linear readout per delay on `train` rows, score r^2 on `test` rows; return (MC, r^2 by delay)."""
    d = len(features[0])
    G = [[0.0] * d for _ in range(d)]
    for t in train:
        f = features[t]
        for i in range(d):
            fi = f[i]
            if fi:
                row = G[i]
                for j in range(d):
                    row[j] += fi * f[j]
    for i in range(d):
        G[i][i] += ridge
    rhs = []
    for k in delays:
        rhs.append([sum(features[t][i] * u[t - k] for t in train) for i in range(d)])
    ws = cholesky_solve(G, rhs)
    r2s = []
    for k, w in zip(delays, ws):
        ys = [u[t - k] for t in test]
        ps = [sum(wi * fi for wi, fi in zip(w, features[t])) for t in test]
        my, mp = sum(ys) / len(ys), sum(ps) / len(ps)
        cov = sum((a - my) * (b - mp) for a, b in zip(ys, ps))
        vy = sum((a - my) ** 2 for a in ys)
        vp = sum((b - mp) ** 2 for b in ps)
        r2s.append(cov * cov / (vy * vp) if vy > 0 and vp > 0 else 0.0)
    return sum(r2s), r2s


def run(N=100, seed=2026, T=2600, washout=200, n_train=1200, K=80, density=0.1, rho=0.9):
    rng = random.Random(seed)
    W = [[(rng.uniform(-1, 1) if rng.random() < density else 0.0) for _ in range(N)] for _ in range(N)]
    sr = spectral_radius(W)
    W = [[a * rho / sr for a in row] for row in W]
    W_in = [rng.uniform(-1, 1) for _ in range(N)]
    u = [rng.uniform(-1, 1) for _ in range(T)]
    x = [0.0] * N
    states = []
    for t in range(T):
        x = [math.tanh(sum(W[i][j] * x[j] for j in range(N) if W[i][j]) + W_in[i] * u[t]) for i in range(N)]
        states.append(x + [1.0])
    train = range(washout, washout + n_train)
    test = range(washout + n_train, T)
    delays = list(range(1, K + 1))
    mc_res, r2_res = memory_capacity(states, u, delays, train, test)
    mc_ctl, _ = memory_capacity([[u[t], 1.0] for t in range(T)], u, delays, train, test)
    horizon = next((k for k, r in zip(delays, r2_res) if r < 0.5), K + 1)
    return {"N": N, "seed": seed, "spectral_radius": rho, "trained_weights_per_readout": N + 1,
            "fixed_weights": N * N + N, "memory_capacity": round(mc_res, 2), "bound_N": N,
            "control_no_reservoir": round(mc_ctl, 4), "horizon_delay_r2_below_half": horizon,
            "r2_by_delay_1_5_10_20": [round(r2_res[k - 1], 3) for k in (1, 5, 10, 20)]}


if __name__ == "__main__":
    N = int(sys.argv[1]) if len(sys.argv) > 1 else 100
    seed = int(sys.argv[2]) if len(sys.argv) > 2 else 2026
    out = run(N=N, seed=seed)
    for k, v in out.items():
        print(f"{k:>32}: {v}")
    assert out["memory_capacity"] <= out["bound_N"], "Jaeger's bound MC <= N violated"
    assert out["memory_capacity"] > 10 * max(out["control_no_reservoir"], 0.1), "the reservoir did not remember"
    print("OK - the fixed reservoir remembers; the readout alone does not; MC <= N holds")
