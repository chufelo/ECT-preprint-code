#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# P6 S6-R20 (Claude): Y2 P25-prime — exact approach-fingerprint law for the core-smoothing slope
# (universal asymptote + regulator-specific 1/R coefficients: a1 = int_0^inf (1-f(u))/u^2 du;
# exponential regulator: a1 divergent -> exact log law (xi/R)[ln(R/2 xi)+1] from the C10 closed form);
# Y3 width-slope == pair-slope identity => uniform sigma_pair assignment.
import csv, math
import numpy as np
from pathlib import Path
OUT = Path(__file__).resolve().parent
RR = []
th = np.linspace(0.0, math.pi, 241)
def J0(x):
    x = np.atleast_1d(np.asarray(x, dtype=float))
    return np.trapezoid(np.cos(np.outer(x, np.sin(th))), th, axis=1)/math.pi

def secant(r, reg):
    x = np.arange(0.01, 4000.0 + 0.01, 0.01)
    t = x/float(r)
    f = {'exp': np.exp(-t), 'gauss': np.exp(-t*t), 'lorentz': 1.0/(1.0 + t*t)}[reg]
    y = (1.0 - J0(x))/(x*x)*f
    return float(np.trapezoid(y, x) + 0.01/4.0)

print('Y2 P25-prime: approach-fingerprint law (deficit x r vs exact constants):')
targets = {'gauss': math.sqrt(math.pi), 'lorentz': math.pi/2}
for reg in ('gauss', 'lorentz'):
    for r in (100.0, 200.0, 400.0):
        dr = (1.0 - secant(r, reg))*r
        rel = abs(dr/targets[reg] - 1)
        print('  %-8s r = %4.0f: deficit*r = %.4f vs a1 = %.4f (rel %.1e)' % (reg, r, dr, targets[reg], rel))
    assert rel < 0.02
    RR.append({'section':'Y2','case':reg,'value':'a1=%.4f'%targets[reg],'check':'int (1-f)/u^2 du','note':'pure 1/R approach (p = 1)'})
print('  exponential: a1 divergent -> exact LOG law from the C10 closed form: deficit = (xi/R)[ln(R/(2 xi)) + 1]:')
for r in (60.0, 100.0, 200.0):
    dr = (1.0 - secant(r, 'exp'))*r
    thv = math.log(r/2.0) + 1.0
    print('  exp      r = %4.0f: deficit*r = %.4f vs ln(r/2)+1 = %.4f (rel %.1e)' % (r, dr, thv, abs(dr/thv - 1)))
    assert abs(dr/thv - 1) < 0.02
RR.append({'section':'Y2','case':'exp','value':'deficit*r = ln(r/2)+1','check':'C10 closed form','note':"GPT's fitted exponent 0.80 = log artifact; true p = 1 with log"})

print('Y3 width-slope == pair-slope identity (uniform sigma_pair assignment):')
x = np.arange(0.005, 6000.0, 0.005)
base = (1.0 - J0(x))/(x*x)
pair_slope = float(np.trapezoid(base, x) + 0.005/4.0 + 1.0/6000.0)
# width difference d vs d' = effective dipole pair of size |Delta d| in the SAME functional:
# Phi_width(Delta)/Delta must equal Phi_pair(R)/R -> both = c1 (certified Q4 machinery).
d, dp = 20.0, 26.0
kg = np.logspace(-5, math.log10(400.0), 120000)
ph = np.linspace(0, 2*math.pi, 1024, endpoint=False)
KX = np.outer(kg, np.cos(ph))
amp2 = np.mean((np.sin(KX*d/2) - np.sin(KX*dp/2))**2, axis=1)*4.0
width_slope = float(np.trapezoid(kg**2*(amp2/kg**4), kg))/(2*math.pi)/abs(dp - d)*(2*math.pi)/(2.0)
print('  pair c1 = %.6f | width Phi/(2|Delta d|) per (2piW)^2-units = %.6f (rel %.1e)' % (pair_slope, width_slope, abs(width_slope/pair_slope - 1)))
RR.append({'section':'Y3','case':'sigma assignment','value':'rel %.1e'%abs(width_slope/pair_slope - 1),'check':'width == pair coefficient','note':'ALL certified P6-C formulas are pair-constructed => default sigma_dec = sigma_pair (zeta_0 = 2); sigma_face reserved for genuine single-sheet constructions (none in the ledger)'})
assert abs(width_slope/pair_slope - 1) < 0.005

with open(OUT/'p6_s6r20_claude_results.csv','w',newline='') as f:
    w_ = csv.DictWriter(f, fieldnames=['section','case','value','check','note']); w_.writeheader()
    for r in RR: w_.writerow(r)
print('WROTE p6_s6r20_claude_results.csv')
