#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# P6 S6-R19: S2 spectral-weight SUM RULE for C13' (Z + int rho_cont = 1, joint normalization);
# S3 P24 certification (g^2_crit prop Delta); S4 T_eff thermometer spot-check.
# KERNEL CORRECTION RECORD: the first version used the naive KK kernel 1/(w'-w); the correct bosonic
# dispersion for D(w) = w^2 - Om0^2 + Sigma is Sigma'(w) = (2/pi) P int w' Sigma''(w')/(w'^2 - w^2) dw'
# (mirror term included). All numbers below use the corrected kernel; R18 B/C numbers re-quoted separately.
import csv, math
import numpy as np
from pathlib import Path
OUT = Path(__file__).resolve().parent
RR = []
E = 1.0; LAM = 80.0
grid = np.linspace(E + 1e-9, LAM, 120000)
def S2f(w, g2): return g2*(w - E)*np.exp(-w/20.0)*(w > E)
def S1_below(w0, g2):
    return (2.0/math.pi)*float(np.trapezoid(grid*S2f(grid, g2)/(grid*grid - w0*w0), grid))
def S1_inside(w0, g2):
    s0 = float(S2f(np.array([w0]), g2)[0])
    dg = grid*grid - w0*w0
    core = np.where(np.abs(dg) < 1e-10, 0.0, (grid*S2f(grid, g2) - w0*s0)/np.where(np.abs(dg) < 1e-10, 1.0, dg))
    pv = (1.0/(2*w0))*math.log(((LAM - w0)*(w0 + E))/((LAM + w0)*(w0 - E))) if w0 > E + 1e-15 else 0.0
    return (2.0/math.pi)*(float(np.trapezoid(core, grid)) + w0*s0*pv)
def pole(Om0, g2):
    f = lambda w: w*w - Om0*Om0 + S1_below(w, g2)
    lo, hi = 1e-3*E, E - 1e-8
    if f(lo)*f(hi) > 0: return None
    flo = f(lo)
    for _ in range(70):
        mid = 0.5*(lo + hi)
        if f(mid)*flo <= 0: hi = mid
        else: lo, flo = mid, f(mid)
    return 0.5*(lo + hi)

print('S2 spectral-weight sum rule (bare-edge convention, Omega_0 = E; corrected bosonic KK kernel):')
for g2 in (0.02, 0.05, 0.08):
    wb = pole(E, g2)
    if wb is None:
        print('  g^2 = %.2f: no real sub-edge pole (Sigma_1(E) > E^2, overdamped template zone)' % g2)
        continue
    h = 1e-5
    dS_dw2 = (S1_below(wb + h, g2) - S1_below(wb - h, g2))/(2*h)/(2*wb)
    Zt = 1.0/(1.0 + dS_dw2)
    wcont = np.linspace(E + 1e-6, 76.0, 4000)
    S1v = np.array([S1_inside(w, g2) for w in wcont])
    S2v = S2f(wcont, g2)
    A = (1.0/math.pi)*S2v/((wcont**2 - E*E + S1v)**2 + S2v**2)
    cont = float(np.trapezoid(2*wcont*A, wcont))
    tot = Zt + cont
    print('  g^2 = %.2f: omega_b = %.6f, Z = %.5f, continuum weight = %.5f, SUM = %.5f' % (g2, wb, Zt, cont, tot))
    RR.append({'section':'S2','case':'g2=%.2f'%g2,'value':'Z=%.4f cont=%.4f'%(Zt, cont),'check':'sum=1','note':'sum=%.5f (corrected KK kernel)'%tot})
    assert abs(tot - 1.0) < 0.01

print('S3 P24: g^2_crit(Delta) prop Delta (corrected kernel):')
g2ref = 0.05
S1E_per_g2 = S1_below(E - 1e-7, g2ref)/g2ref
ds = np.array([0.01, 0.02, 0.04])
gc = np.array([(E*E*((1 + dv)**2 - 1))/S1E_per_g2 for dv in ds])
sl = float(np.polyfit(np.log(ds), np.log(gc), 1)[0])
for dv, g in zip(ds, gc): print('  Delta = %.2f: g^2_crit = %.5f' % (dv, g))
print('  slope = %.3f (theory 1 + O(Delta))' % sl)
RR.append({'section':'S3','case':'P24','value':'slope %.3f'%sl,'check':'~1','note':'narrow resonance <-> sub-edge rebinding transition'})
assert 0.95 < sl < 1.10

print('S4 T_eff thermometer spot-check (independent):')
T = 0.7; w = 1.3
nB = 1.0/(math.exp(w/T) - 1.0)
Text = w/math.log((1 + nB)/nB)
print('  extract at omega = %.1f: T_eff = %.6f (true 0.7)' % (w, Text))
assert abs(Text - T) < 1e-12

with open(OUT/'p6_s6r19_results.csv','w',newline='') as f:
    w_ = csv.DictWriter(f, fieldnames=['section','case','value','check','note']); w_.writeheader()
    for r in RR: w_.writerow(r)
print('WROTE p6_s6r19_results.csv')
