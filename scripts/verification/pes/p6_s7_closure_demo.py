#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Synthetic/model-internal P26 protocol check: reconstruct J_W from a generated
# width corner, then test two withheld observables against the same supplied
# kernel. This is not an ECT prediction or a physical-channel closure.
# T3 is a Cauchy--Schwarz cross-spectrum positivity detector (practical G4 test).
import csv, math
import numpy as np
from pathlib import Path
OUT = Path(__file__).resolve().parent
RR = []
C, wc, T = 0.37, 3.4, 0.72
def Jtrue(x): return C*np.maximum(x, 0.0)*np.exp(-x/wc)
def nB(x): return 1.0/(np.exp(x/T) - 1.0)

print('T2 synthetic P26 over-closure loop (ground truth: C = 0.37, omega_c = 3.4, T = 0.72; coordinate monitor F = 1):')
Om = 0.45 + 0.22*np.arange(1, 9)
Gam = 2*math.pi*Jtrue(Om)*(1.0 + nB(Om))            # "measured" width corner
Jrec_pts = Gam/(2*math.pi*(1.0 + nB(Om)))           # de-occupied reconstruction at grid points
co = np.polyfit(Om, np.log(Jrec_pts/Om), 1)         # ln(J/w) = ln C - w/wc
C_rec, wc_rec = math.exp(co[1]), -1.0/co[0]
print('  reconstructed: C = %.6f (true 0.37, rel %.1e), omega_c = %.6f (true 3.4, rel %.1e)'
      % (C_rec, abs(C_rec/C - 1), wc_rec, abs(wc_rec/wc - 1)))
RR.append({'section':'T2','case':'kernel reconstruction','value':'C=%.5f wc=%.5f'%(C_rec, wc_rec),'check':'0.37 / 3.4','note':'from the width corner alone'})
assert abs(C_rec/C - 1) < 5e-3 and abs(wc_rec/wc - 1) < 5e-3

wg = np.logspace(-6, 2.3, 30000)
def Phi(Cv, wcv, t):
    S = Cv*wg*np.exp(-wg/wcv)/np.tanh(wg/(2*T))
    return float(np.trapezoid(S*(1 - np.cos(wg*t))/wg**2, wg))
worstD = 0.0
for t in (0.5, 5.0, 50.0):
    r = Phi(C_rec, wc_rec, t)/Phi(C, wc, t)
    worstD = max(worstD, abs(r - 1))
    print('  model-internal dephasing holdout: t = %5.1f: Phi_rec/Phi_true = %.6f' % (t, r))
RR.append({'section':'T2','case':'dephasing corner','value':'worst %.2e'%worstD,'check':'<1e-2','note':'reproduced from synthetic reconstruction'})
assert worstD < 1e-2

wkk = np.linspace(1e-5, 80.0*wc, 250000)
def shift(Cv, wcv, Om0, eps=3e-4):
    Jk = Cv*wkk*np.exp(-wkk/wcv)
    m = np.abs(wkk - Om0) > eps
    return float((2.0/math.pi)*np.trapezoid(wkk[m]*Jk[m]/(wkk[m]**2 - Om0**2), wkk[m]))
rs = shift(C_rec, wc_rec, 0.9)/shift(C, wc, 0.9)
print('  model-internal KK-shift holdout: Omega_0 = 0.9: shift_rec/shift_true = %.6f' % rs)
RR.append({'section':'T2','case':'shift corner','value':'%.6f'%rs,'check':'1','note':'bosonic mirror kernel (R19)'})
assert abs(rs - 1) < 1e-2
print('  => the supplied synthetic triangle closes internally; this is a protocol self-consistency check, not an ECT prediction or physical P26 closure.')

print('T3 Cauchy-Schwarz positivity detector (practical G4 test):')
for r_, lab in ((0.63, 'admissible'), (1.20, 'VIOLATION')):
    J11 = J22 = float(Jtrue(np.array([1.0]))[0]); J12 = r_*J11
    ok = J12*J12 <= J11*J22 + 1e-15
    print('  r = %.2f: |J12|^2 <= J11 J22 -> %s (%s)' % (r_, ok, lab))
    RR.append({'section':'T3','case':'r=%.2f'%r_,'value':str(ok),'check':'True/False','note':lab})
assert RR[-2]['value'] == 'True' and RR[-1]['value'] == 'False'

print('T1 kappa_ind cross-check (independent grid):')
wq = np.logspace(-8, 2.5, 400000)
kap = (2.0/math.pi)*float(np.trapezoid(Jtrue(wq)/wq, wq))
kcl = (2.0*C/math.pi)*wc
print('  kappa_ind = %.9f vs closed %.9f (rel %.1e)' % (kap, kcl, abs(kap/kcl - 1)))
assert abs(kap/kcl - 1) < 1e-5

with open(OUT/'p6_s7_results.csv','w',newline='') as f:
    w_ = csv.DictWriter(f, fieldnames=['section','case','value','check','note']); w_.writeheader()
    for r in RR: w_.writerow(r)
print('WROTE p6_s7_results.csv')
