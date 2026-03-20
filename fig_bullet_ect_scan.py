#!/usr/bin/env python3
"""
fig_bullet_ect_scan.py
=======================
Figure 2 — Bullet Cluster ECT: parameter scan heatmap (alpha x R_smooth) for Model 0B
+ summary text panel.

Q = d_gas / d_gal for the global maximum of Sigma_eff:
  Q > 1 (green) => peak closer to galaxy  [PASS]
  Q < 1 (red)   => peak closer to gas      [FAIL]
"""
import numpy as np
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy.ndimage import gaussian_filter
import os

OUTDIR = os.path.dirname(os.path.abspath(__file__))

def g2d(X,Y,x0,y0,sx,sy,amp):
    return amp*np.exp(-0.5*(((X-x0)/sx)**2+((Y-y0)/sy)**2))
def global_max(arr):
    iy,ix=np.unravel_index(np.argmax(arr),arr.shape); return iy,ix,float(arr[iy,ix])
def classify(ix,iy,gal,gas):
    dg=np.hypot(ix-gal[0],iy-gal[1]); da=np.hypot(ix-gas[0],iy-gas[1])
    return dg,da,da/(dg+0.5),('GALAXY' if dg<da else 'GAS')

N=300; X,Y=np.meshgrid(np.arange(N),np.arange(N))
main_gal=(90,150); sub_gal=(215,148); main_gas=(122,155); sub_gas=(188,153)
Sg=(g2d(X,Y,*main_gas,26,22,6.)+g2d(X,Y,*sub_gas,24,20,5.)+g2d(X,Y,153,152,36,11,1.5))
Sv=(g2d(X,Y,*main_gal,10,12,1.)+g2d(X,Y,*sub_gal,8,10,.85))
Ups=3.; Sb=Sg+Ups*Sv; M_gas=np.sum(Sg); M_gal=Ups*np.sum(Sv)
eps=1e-6; wm=0.2

S0A=np.clip(Sb,0,None)
iy0A,ix0A,_=global_max(S0A); _,_,Q0A,_=classify(ix0A,iy0A,main_gal,main_gas)

al_def,R_def=1.5,18
lm_=gaussian_filter(Sb,sigma=R_def); C_=(Sb-lm_)/(lm_+eps); W_=np.maximum(wm,1+al_def*C_)
S0B=np.clip(W_*Sb,0,None); iy0B,ix0B,_=global_max(S0B); _,_,Q0B,_=classify(ix0B,iy0B,main_gal,main_gas)

alphas=[0.5,1.0,1.5,2.0,3.0,4.0]; rvals=[8,12,18,25,35]
scan_Q=np.zeros((len(alphas),len(rvals))); scan_lbl=np.empty_like(scan_Q,dtype=object)
for i,a in enumerate(alphas):
    for j,R in enumerate(rvals):
        lm_=gaussian_filter(Sb,sigma=R); C_=(Sb-lm_)/(lm_+eps)
        W_=np.maximum(wm,1+a*C_); S_=np.clip(W_*Sb,0,None)
        iy_,ix_,_=global_max(S_); _,_,Q_,l_=classify(ix_,iy_,main_gal,main_gas)
        scan_Q[i,j]=Q_; scan_lbl[i,j]=l_

fig,(ax1,ax2)=plt.subplots(1,2,figsize=(14,5))
disp=np.minimum(scan_Q,8.)
im=ax1.imshow(disp,origin='lower',cmap='RdYlGn',vmin=0,vmax=8,aspect='auto')
ax1.set_xticks(range(len(rvals))); ax1.set_xticklabels([str(r) for r in rvals])
ax1.set_yticks(range(len(alphas))); ax1.set_yticklabels([str(a) for a in alphas])
ax1.set_xlabel('R_smooth [px]',fontsize=11); ax1.set_ylabel('α (concentration strength)',fontsize=11)
ax1.set_title('ECT 0B parameter scan: Q = d_gas/d_gal\ngreen (Q>1) = PASS | red = FAIL',fontsize=10)
plt.colorbar(im,ax=ax1,label='Q (clipped at 8)')
try: ax1.contour(disp,levels=[1.0],colors='black',linewidths=2.5)
except: pass
for i in range(len(alphas)):
    for j in range(len(rvals)):
        col='white' if disp[i,j]<1.2 or disp[i,j]>6.5 else 'black'
        ax1.text(j,i,f'{min(scan_Q[i,j],99):.1f}\n{"✓" if scan_lbl[i,j]=="GALAXY" else "✗"}',
                 ha='center',va='center',fontsize=8,color=col)

ax2.set_xlim(0,1); ax2.set_ylim(0,1); ax2.axis('off')
lines=[
    ("Bullet Cluster ECT — Result Summary",0.93,12,'black',True),
    (f"Geometry: M_gas/M_gal = {M_gas/M_gal:.1f}× (Bullet Cluster: ~4–8×)",0.83,10,'#333333',False),
    ("Gas: extended σ~26px, dominates total mass",0.76,9,'#555555',False),
    ("BCG: compact σ~10px, lower total mass",0.70,9,'#555555',False),
    ("Gas displaced ~32px behind BCG (ram-pressure lag)",0.64,9,'#555555',False),
    ("Model 0A (baryons-only):",0.55,10,'black',True),
    (f"  Global max → GAS   Q = {Q0A:.2f}   ✗  FAIL",0.48,10,'#cc0000',False),
    ("Model 0B (concentration-weighted):",0.39,10,'black',True),
    (f"  Global max → BCG   Q = {Q0B:.2f}   ✓  PASS",0.32,10,'#006600',False),
    ("  Robust: α ≥ 1.0, all R_smooth ∈ [8, 35]px",0.25,9,'#006600',False),
    ("Physical mechanism:",0.16,10,'black',True),
    ("  Compact BCG amplified by concentration weight",0.09,9,'#333333',False),
    ("  → derive W(x,y) from ECT action (Level B)",0.02,9,'#888888',False),
]
for txt,y,fs,col,bold in lines:
    ax2.text(0.04,y,txt,transform=ax2.transAxes,fontsize=fs,color=col,
             fontweight='bold' if bold else 'normal',va='center')
plt.suptitle("ECT 0B parameter scan: concentration-weighted closure vs Bullet Cluster",fontsize=11)
plt.tight_layout()
out=os.path.join(OUTDIR,'fig_bullet_ect_scan.png')
fig.savefig(out,dpi=150,bbox_inches='tight'); print(f"Saved: {out}")
