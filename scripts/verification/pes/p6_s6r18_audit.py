#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# P6 S6-R18 frozen normalisation audit:
# A: C8 normalization table from ONE vertex derivation + convention-free invariant J_spat/J_temp = omega^2.
# B: threshold theorem template with counterterm — 5-case detuning map (C13 -> C13').
# C: residue Z_b, residual width Gamma_obs, visibility condition.
# E: P23 protocol shapes CSV (intrinsic edge-plus-line vs external golden-rule Lorentzians).
# CONVENTION (declared once, used everywhere):
#   J(omega; k_z) = sum_{k_perp} |V|^2/(2 Omega) delta(omega - Omega), per unit ribbon length L_z.
#   Bath: canonical eta with action (K/2)(d eta)^2, mode norm (2 K Omega V)^{-1/2}; c = 1 unless shown.
#   Vertices from the C8 cross terms: temporal V_T = K Omega G(k) (2 K Omega)^{-1/2}  [single component];
#   spatial V_S = K k^2 G(k) (2 K Omega)^{-1/2}  [vector contraction, already summed].
#   G(k) = -2 pi i W k_y cos(k_x d/2)/k^2;  <|G|^2>_phi = (2 pi W)^2 (k_perp^2/2)/(k_perp^2+k_z^2)^2 (d << 1/k).
#   REDUCED UNITS for tables: 2 pi W = 1, K = 1  (physical factor measured in A3).
import csv, math
import numpy as np
from pathlib import Path
OUT = Path(__file__).resolve().parent
RR = []

def Jker(w, q, vertex, K=1.0, W2pi=1.0, eps=8e-4):
    kp = np.linspace(1e-6, 12.0, 600000)
    Om = np.sqrt(kp*kp + q*q)
    dlt = np.exp(-((w - Om)/eps)**2/2)/(eps*math.sqrt(2*math.pi))
    G2 = (W2pi**2)*(kp*kp/2.0)/Om**4
    if vertex == 'temporal':
        V2 = K*Om*G2/2.0
    else:
        V2 = K*(Om**4)*G2/(2.0*Om)
    return float(np.trapezoid(kp/(2*math.pi)*V2/(2*Om)*dlt, kp))

print('A1 canonical kernels from the single vertex definition (reduced units):')
ws = np.array([0.7, 1.0, 1.6, 2.5, 4.0])
for q in (0.0, 0.5):
    JT = np.array([Jker(w, q, 'temporal') for w in ws if w > q + 0.15])
    JS = np.array([Jker(w, q, 'spatial') for w in ws if w > q + 0.15])
    wv = np.array([w for w in ws if w > q + 0.15])
    eT = float(np.max(np.abs(JT/((wv**2 - q*q)/(16*math.pi*wv**3)) - 1)))
    eS = float(np.max(np.abs(JS/((wv**2 - q*q)/(16*math.pi*wv)) - 1)))
    print('  k_z = %.1f: J_temp vs (w^2-q^2)/(16 pi w^3): worst %.1e | J_spat vs (w^2-q^2)/(16 pi w): worst %.1e' % (q, eT, eS))
    assert eT < 0.012 and eS < 0.012
    RR.append({'section':'A1','case':'k_z=%.1f'%q,'value':'eT %.1e eS %.1e'%(eT, eS),'check':'CANONICAL = historical-reduced / 4','note':'dictionary: R4/R17 reduced forms = 4 x canonical (dropped 1/2 in |V|^2 and 1/(2 Omega)); R17 spatial ALSO carried an extra /2 vs R4 (refuted by the w^2 invariant)'})
print('A2 convention-free invariant: J_spat/J_temp = omega^2 (kills any stray factor 2):')
for q in (0.0, 0.5):
    for w in (1.6, 2.5):
        if w <= q + 0.15: continue
        r = Jker(w, q, 'spatial')/Jker(w, q, 'temporal')
        assert abs(r/w**2 - 1) < 0.02
print('  invariant holds to <2%% on all sampled (w, k_z)  [R17 pair violated it by exactly 2]')
RR.append({'section':'A2','case':'J_S/J_T = w^2','value':'<2%','check':'invariant','note':'convention-free'})

print('A3 physical-units factor (K, 2 pi W explicit):')
r1 = Jker(1.6, 0.0, 'temporal', K=2.0, W2pi=3.0)/Jker(1.6, 0.0, 'temporal')
r2 = Jker(2.5, 0.5, 'spatial', K=2.0, W2pi=3.0)/Jker(2.5, 0.5, 'spatial')
print('  J(K=2, 2piW=3)/J(1,1) = %.4f / %.4f (theory K*(2 pi W)^2 = 18): units factor = K (2 pi W)^2, w,q-independent' % (r1, r2))
assert abs(r1/18 - 1) < 0.01 and abs(r2/18 - 1) < 0.01
RR.append({'section':'A3','case':'physical factor','value':'%.3f'%r1,'check':'K (2 pi W)^2','note':'sigma_dec/zeta_0 absorbs overall scale; exponents untouched'})
print('A4 normalization table (per unit L_z; physical = column x K (2 pi W)^2):')
print('  channel   | CANONICAL (vertex def.)           | historical-reduced (x4, used R4-R17) | k_z=0 face (canon) | components')
print('  temporal  | (w^2 - c^2 k_z^2)/(16 pi w^3)     | (w^2 - c^2 k_z^2)/(4 pi w^3)         | 1/(16 pi w)        | 1 (q_dot)')
print('  spatial   | (w^2 - c^2 k_z^2)/(16 pi c^2 w)   | (w^2 - c^2 k_z^2)/(4 pi c^2 w)       | w/(16 pi)          | summed vector')
print('  invariant J_spat/J_temp = w^2/c^2 holds in BOTH columns; exponents/faces/structure untouched;')
print('  the overall constant flows into sigma_dec zeta_0 (open) — NO downstream statement changes.')

# ---------- Part B: threshold theorem template with counterterm (5-case detuning map) ----------
print('B threshold theorem template: J = g^2 (w - E) Theta(w - E) e^{-w/20}; D = w^2 - Om0^2 + Sig_R(w) - dct:')
E = 1.0
wgrid = np.linspace(E + 1e-9, 80.0, 500000)
def Sig2(w, g2): return g2*(w - E)*np.exp(-w/20.0)*(w > E)
# KERNEL CORRECTION (R19 honesty event): bosonic dispersion with the mirror term,
# Sigma_1(w0) = (2/pi) P int w' Sigma_2(w')/(w'^2 - w0^2) dw'  [w0 below the support here].
def Sig1(w0, g2): return (2.0/math.pi)*float(np.trapezoid(wgrid*Sig2(wgrid, g2)/(wgrid*wgrid - w0*w0), wgrid))
def pole(Om0, g2, dct=0.0):
    f = lambda w: w*w - Om0*Om0 + Sig1(w, g2) - dct
    lo, hi = 1e-3*E, E - 1e-8
    if f(lo)*f(hi) > 0: return None
    flo = f(lo)
    for _ in range(70):
        mid = 0.5*(lo + hi)
        if f(mid)*flo <= 0: hi = mid
        else: lo, flo = mid, f(mid)
    return 0.5*(lo + hi)
g2v = 0.05
S1E = Sig1(E - 1e-7, g2v)
# case 1: exact bare edge, no subtraction (perturbative-window scaling fit)
wb1 = pole(E, g2v)
sc = math.log((E - pole(E, 0.04))/(E - pole(E, 0.01)))/math.log(4.0)
print('  case 1 (bare edge, dct = 0):        omega_b = %.6f (g^2 = 0.05), binding %.2e; binding ∝ (g^2)^%.2f in the perturbative window (theory 1)' % (wb1, E - wb1, sc))
# case 2: physical-edge convention (subtract Sig1 at the edge)
wb2 = pole(E, g2v, dct=S1E)
print('  case 2 (subtracted, dct = Sig1(E)): pole at %.7f (= edge to %.1e): detachment MAGNITUDE is convention-dependent; Gamma = 0 robust (soft edge)' % (wb2, abs(wb2 - E)))
# case 3: positive detuning
delta = 0.02
Om0p = E*(1 + delta)
g2crit = (Om0p*Om0p - E*E)/(S1E/g2v)
wb3a = pole(Om0p, 0.5*g2crit); wb3b = pole(Om0p, 2.0*g2crit)
GamR = math.pi*Sig2(np.array([Om0p]), 0.5*g2crit)[0]/(2*Om0p)
print('  case 3 (Delta = +%.2f): g^2_crit = %.4f; g^2 = 0.5 crit -> %s (resonance, width ~ %.1e); g^2 = 2 crit -> bound at %.6f' %
      (delta, g2crit, 'NO bound state' if wb3a is None else 'bound %.6f' % wb3a, GamR, wb3b))
assert wb3a is None and wb3b is not None and wb3b < E
# case 4: negative detuning
wb4 = pole(E*(1 - delta), g2v)
print('  case 4 (Delta = -%.2f): bound at %.6f (trivially protected, pushed further down)' % (delta, wb4))
assert wb4 < E*(1 - delta)
# case 5: finite-size edge smoothing
b = E - wb1
for Lp in (20.0, 60.0):
    dwe = math.pi**2/(2*E*Lp**2)
    print('  case 5 (L_perp = %g): edge granularity %.2e vs binding %.2e -> %s' % (Lp, dwe, b, 'VISIBLE' if b > 3*dwe else 'smeared'))
RR.append({'section':'B','case':'5-case map','value':'g2crit(0.02)=%.4f'%g2crit,'check':'C13 -> C13-prime','note':'Gamma(omega_b)=0 robust for cases 1,2,4 and case 3 iff g^2 > g^2_crit; magnitude convention-dependent (G2 guard)'})

# ---------- Part C: residue, residual width, visibility ----------
print('C residue and visibility:')
for g2 in (0.02, 0.05, 0.1):
    wb = pole(E, g2)
    if wb is None:
        print('  g^2 = %.2f: no real sub-edge pole (strong-coupling limit of the template) — outside the perturbative window' % g2)
        continue
    h = 1e-4
    dS = (Sig1(wb + h, g2) - Sig1(wb - h, g2))/(2*h)
    Zb = 1.0/abs(2*wb + dS)*2*wb   # Z_b = 2 w_b / |D'(w_b)|, D' = 2w + dSig1/dw
    print('  g^2 = %.2f: omega_b = %.6f, Z_b = %.4f' % (g2, wb, Zb))
    RR.append({'section':'C','case':'g2=%.2f'%g2,'value':'Z_b=%.4f'%Zb,'check':'->1 weak coupling','note':'binding %.2e'%(E-wb)})
print('  Gamma_obs = max(Gamma_ext, Gamma_Lz, Gamma_T, Gamma_disorder, 1/T_obs); visible iff E - omega_b > delta_omega_edge AND Z_b = O(1).')

# ---------- Part E: P23 protocol shapes ----------
print('E P23 shapes CSV (intrinsic edge-plus-line vs external Lorentzians):')
g2 = 0.05
wb = pole(E, g2); Zb = 0.985
wsh = np.linspace(0.85, 2.2, 1351)
sres = 0.006
Sint = Zb*np.exp(-((wsh - wb)/sres)**2/2)/(sres*math.sqrt(2*math.pi)) + Sig2(wsh, g2)*5.0
Sext = np.zeros_like(wsh)
for n in (1, 2, 3):
    On = n*E*1.05; Gn = 0.03*math.sqrt(n)   # golden-rule widths (C12 coordinate row shape x J)
    Sext += (Gn/math.pi)/((wsh - On)**2 + Gn**2)
with open(OUT/'p6_s6r18_shapes.csv', 'w', newline='') as f:
    w_ = csv.writer(f); w_.writerow(['omega', 'S_intrinsic_edge_plus_line', 'S_external_lorentzians'])
    for i in range(len(wsh)): w_.writerow(['%.5f' % wsh[i], '%.6e' % Sint[i], '%.6e' % Sext[i]])
print('  wrote p6_s6r18_shapes.csv (%d rows): sharp sub-edge line + soft shoulder vs Lorentzian ladder' % len(wsh))

with open(OUT/'p6_s6r18_results.csv', 'w', newline='') as f:
    w_ = csv.DictWriter(f, fieldnames=['section','case','value','check','note']); w_.writeheader()
    for r in RR: w_.writerow(r)
print('WROTE p6_s6r18_results.csv')
