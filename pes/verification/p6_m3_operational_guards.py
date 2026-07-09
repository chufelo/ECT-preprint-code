#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# P6 M3-1 (Claude): operational procedures for the R22 guards.
# O1 = M3-G1 backaction: Gamma_obs(kappa_ext) linear extrapolation to zero readout — intercept test.
# O2 = M3-G2 trapped-mode discriminator: Z_b(g^2) must DECREASE with weight transferred to the shoulder,
#      sum rule Z + cont = 1 maintained (a trap gives Z ~ 1 const, no transfer).
# O3 = M3-G3 detuning calibration: omega_res(g^2) -> Omega_0 linearly in g^2 (g -> 0 extrapolation).
# Uses GPT's R22 edge model verbatim: J = A (w-E) exp(-(w-E)/wc), A = 12, wc = 2.2, E = 1; Sigma'' = g^2 J.
import csv, math
import numpy as np
from pathlib import Path
OUT = Path(__file__).resolve().parent
RR = []
E, A_edge, wc_edge = 1.0, 12.0, 2.2
x = np.linspace(E + 1e-6, E + 80.0*wc_edge, 260000)
Ju = A_edge*np.maximum(x - E, 0.0)*np.exp(-(x - E)/wc_edge)
def Sp_unit(w, eps=2.5e-5):
    den = x*x - w*w
    m = np.abs(x - w) > eps if w > E else np.ones_like(x, dtype=bool)
    return (2.0/math.pi)*float(np.trapezoid(x[m]*Ju[m]/den[m], x[m]))
def Ju_at(w):
    return A_edge*max(w - E, 0.0)*math.exp(-max(w - E, 0.0)/wc_edge)
def find_root(Om0, g2, lo, hi, n=200):
    xs = np.linspace(lo, hi, n)
    vals = np.array([xx*xx - Om0*Om0 + g2*Sp_unit(float(xx)) for xx in xs])
    for i in range(len(xs) - 1):
        if vals[i]*vals[i + 1] < 0:
            a, b, fa = xs[i], xs[i + 1], vals[i]
            for _ in range(60):
                mm = 0.5*(a + b); fm = mm*mm - Om0*Om0 + g2*Sp_unit(float(mm))
                if fa*fm <= 0: b = mm
                else: a, fa = mm, fm
            return 0.5*(a + b)
    return None

print('O1 (M3-G1) backaction extrapolation:')
gap_true = 0.019390
for G0, lab in ((0.0, 'intrinsic (Gamma_intr = 0)'), (0.003, 'trapped alternative (Gamma_0 = 0.003)')):
    kap = np.array([0.2, 0.4, 0.6, 0.8, 1.0])
    pert = np.array([1.0, -1.0, 0.5, -0.5, 0.0])*0.01
    Gobs = (0.008*kap + G0)*(1.0 + pert)
    co, cov = np.polyfit(kap, Gobs, 1, cov=True)
    ic, sic = co[1], math.sqrt(cov[1][1])
    verdict = 'INTRINSIC' if abs(ic) < 2*sic else 'TRAPPED'
    print('  %-38s intercept = %.5f +- %.5f -> %s' % (lab, ic, sic, verdict))
    RR.append({'section':'O1','case':lab,'value':'%.5f+-%.5f'%(ic, sic),'check':'2-sigma test','note':verdict})
assert RR[0]['note'] == 'INTRINSIC' and RR[1]['note'] == 'TRAPPED'
print('  requirement: sigma_intercept < Gamma_0-scale/2; with N points and eps relative noise, sigma_ic ~ eps Gamma(kappa_max) x O(1).')

print('O2 (M3-G2) weight-transfer discriminator (Delta = 0.02, GPT edge model):')
Om0 = E + 0.02
SigE = Sp_unit(E - 1e-7)
g2c = (Om0*Om0 - E*E)/SigE
wcont = np.linspace(E + 1e-6, E + 30.0, 3200)
Spv = np.array([Sp_unit(float(w)) for w in wcont])
prevZ = 2.0
for mult in (1.25, 1.5, 2.0):
    g2 = mult*g2c
    wb = find_root(Om0, g2, 1e-4, E - 1e-7)
    h = 1e-5
    dSp = (Sp_unit(wb + h) - Sp_unit(wb - h))/(2*h)
    Z = 1.0/(1.0 + g2*dSp/(2*wb))
    S2v = g2*A_edge*np.maximum(wcont - E, 0.0)*np.exp(-(wcont - E)/wc_edge)
    Awc = (1.0/math.pi)*S2v/((wcont**2 - Om0*Om0 + g2*Spv)**2 + S2v**2)
    cont = float(np.trapezoid(2*wcont*Awc, wcont))
    tot = Z + cont
    print('  g^2/g^2_crit = %.2f: omega_b = %.6f, Z = %.5f (decreasing), cont = %.5f, SUM = %.5f' % (mult, wb, Z, cont, tot))
    RR.append({'section':'O2','case':'mult=%.2f'%mult,'value':'Z=%.4f cont=%.4f'%(Z, cont),'check':'sum=1; Z decreasing','note':'sum=%.5f'%tot})
    assert abs(tot - 1.0) < 0.015 and Z < prevZ
    prevZ = Z
print('  trapped-mode alternative: Z ~ 1 constant, no transfer -> discriminated by dZ/dg^2 < 0 with sum = 1.')

print('O3 (M3-G3) detuning calibration by g -> 0 extrapolation of the above-edge resonance:')
g2s = np.array([0.1, 0.2, 0.3])*g2c
wres = np.array([find_root(Om0, float(g), E + 1e-6, E + 0.4) for g in g2s])
co = np.polyfit(g2s, wres, 1)
Om0_rec = co[1]
print('  omega_res(g^2) linear extrapolation: Omega_0_rec = %.6f (true %.6f, |err| = %.1e) => Delta_cal = %.6f' % (Om0_rec, Om0, abs(Om0_rec - Om0), Om0_rec - E))
RR.append({'section':'O3','case':'Delta calibration','value':'Om0_rec=%.6f'%Om0_rec,'check':'true %.4f'%Om0,'note':'closes the counterterm ambiguity operationally'})
assert abs(Om0_rec - Om0) < 2e-4

with open(OUT/'p6_m3_operational_results.csv','w',newline='') as f:
    w_ = csv.DictWriter(f, fieldnames=['section','case','value','check','note']); w_.writeheader()
    for r in RR: w_.writerow(r)
print('WROTE p6_m3_operational_results.csv')
