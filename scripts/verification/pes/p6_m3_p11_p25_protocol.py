#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
P6 M3-3 protocol audit: P11 Airy width + P25/P25' core-profile fingerprint.

Purpose:
  1) Numerically audit the Airy transfer-matrix scaling under an explicitly declared
     physical tilt-stiffness convention K_b.
  2) Show the convention-neutral way to read P11: if the ledger symbol kappa_b means
     physical stiffness, the Airy width decreases as K_b^{-1/3}; if it means flexibility
     D_b = 1/K_b, it increases as D_b^{+1/3}.
  3) Provide toy operational checks for the C9 coherence window and P25/P25' fingerprint.

Dependencies: numpy only; relative output path.
"""
import csv
import math
from pathlib import Path
import numpy as np

OUT = Path(__file__).resolve().parent
ROWS = []

AIRY_A1 = 2.338107410459767  # first zero magnitude of Ai(-a)=0; Dirichlet half-line constant


def fit_slope(x, y):
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    return float(np.polyfit(np.log(x), np.log(y), 1)[0])


def airy_halfline(sigma, K, n=120, xmax_factor=14.0):
    """Solve H = -1/(2K) d^2/dx^2 + sigma*x on x>0 with Dirichlet endpoints.

    K is the physical tilt stiffness in S/S0 = int dz [K/2 (dx/dz)^2 + sigma*x].
    The transfer Hamiltonian therefore has inverse mass 1/K.
    """
    ell = (1.0/(2.0*K*sigma))**(1.0/3.0)
    xmax = xmax_factor * ell
    h = xmax / (n + 1)
    x = h * (np.arange(n, dtype=float) + 1.0)
    diag = (1.0/(K*h*h)) + sigma*x
    off = np.full(n-1, -1.0/(2.0*K*h*h), dtype=float)
    H = np.diag(diag) + np.diag(off, 1) + np.diag(off, -1)
    vals, vecs = np.linalg.eigh(H)
    v = vecs[:, 0]
    w = v*v
    w = w/np.sum(w)
    mean = float(np.sum(w*x))
    rms = float(math.sqrt(np.sum(w*x*x)))
    # weighted quantiles of x
    cdf = np.cumsum(w)
    q50 = float(np.interp(0.50, cdf, x))
    q90 = float(np.interp(0.90, cdf, x))
    return {"E0": float(vals[0]), "ell": ell, "mean": mean, "rms": rms, "q50": q50, "q90": q90,
            "mean_scaled": mean/ell, "rms_scaled": rms/ell, "qratio": q90/q50}


# A. Airy convention audit.
sigmas = np.array([0.55, 0.95, 1.65, 2.85])
Ks = np.array([0.55, 0.95, 1.65, 2.85])
K0 = 1.25
sigma0 = 1.35

sigma_scan = [airy_halfline(s, K0) for s in sigmas]
K_scan = [airy_halfline(sigma0, k) for k in Ks]

E_sigma_slope = fit_slope(sigmas, [r["E0"] for r in sigma_scan])
E_K_slope = fit_slope(Ks, [r["E0"] for r in K_scan])
w_sigma_slope = fit_slope(sigmas, [r["rms"] for r in sigma_scan])
w_K_slope = fit_slope(Ks, [r["rms"] for r in K_scan])
Lcoh_sigma_slope = fit_slope(sigmas, [1.0/(s*r["rms"]) for s, r in zip(sigmas, sigma_scan)])
Lcoh_K_slope = fit_slope(Ks, [1.0/(sigma0*r["rms"]) for k, r in zip(Ks, K_scan)])

ROWS += [
    {"section":"A","case":"declared convention","value":"S/S0=int dz [K_b/2 (dx/dz)^2 + sigma*x]","check":"H=-1/(2K_b)d2+sigma*x","note":"K_b is physical tilt stiffness; larger K_b penalizes slopes more"},
    {"section":"A","case":"E0 sigma exponent","value":"%.6f" % E_sigma_slope,"check":"expected +2/3","note":"matches ledger energy formula E0=|a1|(sigma^2/(2K_b))^(1/3)"},
    {"section":"A","case":"E0 K_b exponent","value":"%.6f" % E_K_slope,"check":"expected -1/3","note":"physical stiffness in denominator"},
    {"section":"A","case":"width sigma exponent","value":"%.6f" % w_sigma_slope,"check":"expected -1/3","note":"Airy width narrows when the linear loudness slope grows"},
    {"section":"A","case":"width K_b exponent","value":"%.6f" % w_K_slope,"check":"expected -1/3 under stiffness convention","note":"if ledger wants +1/3, its symbol must be flexibility D_b=1/K_b, not stiffness"},
]

# A2. Constant check and shape collapse.
all_cases = []
for s in [0.60, 1.10, 2.10]:
    for k in [0.70, 1.60]:
        r = airy_halfline(s, k)
        all_cases.append(r)
E_const = []
for s in [0.60, 1.10, 2.10]:
    for k in [0.70, 1.60]:
        r = airy_halfline(s, k)
        scale = (s*s/(2.0*k))**(1.0/3.0)
        E_const.append(r["E0"]/scale)
mean_scaled = np.array([r["mean_scaled"] for r in all_cases])
rms_scaled = np.array([r["rms_scaled"] for r in all_cases])
qratio = np.array([r["qratio"] for r in all_cases])
ROWS += [
    {"section":"A2","case":"Dirichlet Airy constant","value":"%.6f" % float(np.mean(E_const)),"check":"|a1|=%.6f" % AIRY_A1,"note":"finite-difference half-line check"},
    {"section":"A2","case":"shape collapse mean/ell CV","value":"%.2e" % float(np.std(mean_scaled)/np.mean(mean_scaled)),"check":"small","note":"Airy-squared width shape is universal after x/ell rescaling"},
    {"section":"A2","case":"shape collapse rms/ell CV","value":"%.2e" % float(np.std(rms_scaled)/np.mean(rms_scaled)),"check":"small","note":"use rms width or distribution quantiles, not only fit slope"},
    {"section":"A2","case":"shape collapse q90/q50 CV","value":"%.2e" % float(np.std(qratio)/np.mean(qratio)),"check":"small","note":"dimensionless quantile ratios are boundary-condition sensitive but parameter-independent"},
]

# B. Coherence-window exponents from C9 under the same convention.
ROWS += [
    {"section":"B","case":"Lz_coh sigma exponent","value":"%.6f" % Lcoh_sigma_slope,"check":"expected -2/3","note":"Lz_coh = -ln P/(sigma*l_w); l_w~sigma^-1/3"},
    {"section":"B","case":"Lz_coh K_b exponent","value":"%.6f" % Lcoh_K_slope,"check":"expected +1/3 under stiffness convention","note":"stiffer line has smaller width, hence longer coherence length"},
]

# C. Convention-neutral dictionary.
ROWS += [
    {"section":"C","case":"stiffness symbol K_b","value":"l_w~(K_b*sigma)^(-1/3)","check":"transfer matrix","note":"recommended if K_b=T_line/(2S0) from Nambu-Goto tilt inertia"},
    {"section":"C","case":"flexibility symbol D_b=1/K_b","value":"l_w~(D_b/sigma)^(1/3)","check":"same physics","note":"this is the only reading under which a +1/3 exponent is correct"},
    {"section":"C","case":"stiffness/flexibility dictionary","value":"resolved: K_b is stiffness; D_b=1/K_b","check":"energy formula and C5","note":"l_w~(K_b*sigma)^(-1/3)=(D_b/sigma)^(1/3); convention fixed in the current preprint"},
]

# D. P25/P25' operational fingerprint toy: exact asymptotic laws with small finite-r corrections.
rvals = np.array([60.0, 90.0, 135.0, 205.0, 310.0, 470.0])
fingerprints = {
    "gauss": (math.sqrt(math.pi)/rvals + 0.37/(rvals*rvals), math.sqrt(math.pi), "finite a1=sqrt(pi)"),
    "lorentz": ((math.pi/2.0)/rvals + 0.21/(rvals*rvals), math.pi/2.0, "finite a1=pi/2"),
    "exp": ((np.log(rvals/2.0)+1.0)/rvals + 0.15/(rvals*rvals), 1.0, "log law")
}
for name, (deficit, target, note) in fingerprints.items():
    if name == "exp":
        stat = float(np.median(deficit*rvals/(np.log(rvals/2.0)+1.0)))
        rel = abs(stat - 1.0)
        check = "deficit*r/[ln(r/2)+1] -> 1"
    else:
        stat = float(np.median(deficit*rvals))
        rel = abs(stat/target - 1.0)
        check = "deficit*r -> %.6f" % target
    ROWS.append({"section":"D","case":name,"value":"%.6f rel=%.2e" % (stat, rel),"check":check,"note":"P25' core-profile fingerprint toy; %s" % note})

# E. Decision matrix rows.
ROWS += [
    {"section":"E","case":"support pattern","value":"Airy shape + exponents + C9 window + P25' fingerprint","check":"all four","note":"supports M3-3 only as a composite protocol"},
    {"section":"E","case":"false positive","value":"Airy-like slope without shape collapse","check":"reject/ambiguous","note":"could be harmonic trap, finite resolution, wrong boundary, or mixed channels"},
    {"section":"E","case":"profile mismatch","value":"P25' fails while P11 passes","check":"kernel mismatch","note":"Airy width may be real but not from the certified C1/C10 record kernel"},
]

with open(OUT/"p6_m3_p11_p25_results.csv", "w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=["section", "case", "value", "check", "note"])
    writer.writeheader()
    for row in ROWS:
        writer.writerow(row)

print("WROTE", OUT/"p6_m3_p11_p25_results.csv")
for row in ROWS:
    print("{section:>2s} | {case:<32s} | {value:<50s} | {check} | {note}".format(**row))
