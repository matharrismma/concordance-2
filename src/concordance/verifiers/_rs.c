/* Riemann-Siegel Z(t), first correction term — the hot loop of the critical-line scan, in C.
 *
 * THE WORD IN THE READER'S TONGUE for machines: this mirrors the pure-python _rs_z in
 * verifiers/number_theory.py term for term, so on a box with the same libm it agrees to the last
 * bit (measured: 0.0 difference). It is an OPTIONAL accelerator: a node without a C compiler uses
 * numpy, and a node without numpy uses pure python — all three agree away from the zeros, and the
 * scan defers to exact mpmath wherever |Z| is within the formula's own error, so the count is the
 * same whichever backend ran. Found, never generated: this computes Hardy's Z, it decides nothing.
 *
 * Built on first use by riemann_accel.build(); the .so is a local artifact, never synced.
 * Compile: cc -O3 -fPIC -shared -fopenmp -o _rs<suffix>.so _rs.c -lm
 */
#include <math.h>
#include <stddef.h>

#ifndef M_PI
#define M_PI 3.14159265358979323846
#endif
static const double TWO_PI = 6.283185307179586;

/* Z(t[i]) for i in [0, n), written to out[i]. Each t independent — parallel across cores when the
 * build found OpenMP. No fast-math: IEEE semantics, so a value near zero is the same here as in
 * python, and the scan's exact-mpmath recount lands on the same spans. */
void nh_rs_z_array(const double *ts, long n, double *out) {
#ifdef _OPENMP
    #pragma omp parallel for schedule(static)
#endif
    for (long i = 0; i < n; i++) {
        double t = ts[i];
        double a = sqrt(t / TWO_PI);
        long m = (long)a;
        double th = t / 2.0 * log(t / TWO_PI) - t / 2.0 - M_PI / 8.0
                    + 1.0 / (48.0 * t) + 7.0 / (5760.0 * t * t * t);
        double s = 0.0;
        for (long k = 1; k <= m; k++) {
            s += cos(th - t * log((double)k)) / sqrt((double)k);
        }
        double p = a - (double)m;
        double c0 = cos(TWO_PI * (p * p - p - 1.0 / 16.0)) / cos(TWO_PI * p);
        double corr = ((m & 1L) ? 1.0 : -1.0) * pow(a, -0.5) * c0;
        out[i] = 2.0 * s + corr;
    }
}
