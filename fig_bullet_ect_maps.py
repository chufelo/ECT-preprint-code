#!/usr/bin/env python3
"""
fig_bullet_ect_maps.py
=======================
Figure 1 — Bullet Cluster ECT falsification test: six-panel map.
Components (gas, galaxies, total baryons) + Model 0A + Model 0B + lensing target.
Red circle = global max of predicted Sigma_eff.
"""
import numpy as np
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy.ndimage import gaussian_filter, maximum_filter
from matplotlib.lines import Line2D
import os

OUTDIR = os.path.dirname(os.path.abspath(__file__))

def g2d(X,Y,x0,y0,sx,sy,amp):
    return amp*np.exp(-0.5*(((X-x0)/sx)**2+((Y-y0)/sy)**2))
def global_max(arr):
    iy,ix=np.unravel_index(np.argmax(arr),arr.shape); return iy,ix,float(arr[iy,ix])
def find_peaks(arr,md=15,tr=0.10,mp=10):
    thr=tr*np.max(arr); mf=maximum_filter(arr,size=md); mask=(arr==mf)&(arr>=thr)
    pts=np.argwhere(mask); vals=[arr[iy,ix] for iy,ix in pts]; order=np.argsort(vals)[::-1]
    return [(int(pts[k][0]),int(pts[k][1]),float(vals[k])) for k in order[:mp]]
def classify(ix,iy,gal,gas):
    dg=np.hypot(ix-gal[0],iy-gal[1]); da=np.hypot(ix-gas[0],iy-gas[1])
    return dg,da,da/(dg+0.5),('GALAXY' if dg<da else 'GAS')

N=300; X,Y=np.meshgrid(np.arange(N),np.arange(N))
main_gal=(90,150); sub_gal=(215,148); main_gas=(122,155); sub_gas=(188,153)
Sg=(g2d(X,Y,*main_gas,26,22,6.)+g2d(X,Y,*sub_gas,24,20,5.)+g2d(X,Y,153,152,36,11,1.5))
Sv=(g2d(X,Y,*main_gal,10,12,1.)+g2d(X,Y,*sub_gal,8,10,.85))
Ups=3.; Sb=Sg+Ups*Sv; M_gas=np.sum(Sg); M_gal=Ups*np.sum(Sv)
S0A=np.clip(Sb,0,None)
al,Rs,eps,wm=1.5,18,1e-6,.2
lm=gaussian_filter(Sb,sigma=Rs); C=(Sb-lm)/(lm+eps); W=np.maximum(wm,1+al*C); S0B=np.clip(W*Sb,0,None)
kobs=g2d(X,Y,*main_gal,14,14,1.4)+g2d(X,Y,*sub_gal,12,12,1.2)
iy0A,ix0A,_=global_max(S0A); iy0B,ix0B,_=global_max(S0B)
_,_,Q0A,lbl0A=classify(ix0A,iy0A,main_gal,main_gas)
_,_,Q0B,lbl0B=classify(ix0B,iy0B,main_gal,main_gas)
obs_peaks=find_peaks(kobs,md=20)
print(f"M_gas/M_gal={M_gas/M_gal:.1f}x | 0A:{lbl0A} Q={Q0A:.2f} | 0B:{lbl0B} Q={Q0B:.2f}")

fig,axes=plt.subplots(2,3,figsize=(16,10))
panels=[(Sg,"Gas Σ_gas\n(dominates mass, M_gas/M_gal≈{:.0f}×)".format(M_gas/M_gal)),
        (Ups*Sv,"Galaxies Υ·Σ_gal\n(compact BCGs)"),
        (Sb,"Total baryons Σ_b\n(input to Model 0A)"),
        (S0A,"ECT 0A: baryons-only\n→ global max at GAS  [FAIL]"),
        (S0B,f"ECT 0B: concentration-weighted (α={al}, R={Rs}px)\n→ global max at BCG  [PASS]"),
        (kobs,"Observed lensing target (toy)\nPeaks near BCGs")]
for idx,(ax,(arr,title)) in enumerate(zip(axes.ravel(),panels)):
    im=ax.imshow(arr,origin='lower',cmap='inferno',interpolation='bilinear')
    ax.set_title(title,fontsize=9,pad=4)
    for xy in [main_gal,sub_gal]: ax.scatter(*xy,c='cyan',marker='x',s=110,lw=2.5,zorder=7)
    for xy in [main_gas,sub_gas]: ax.scatter(*xy,c='lime',marker='+',s=130,lw=2.5,zorder=7)
    if idx==3: ax.add_patch(plt.Circle((ix0A,iy0A),10,color='red',fill=False,lw=2.5,zorder=8))
    elif idx==4: ax.add_patch(plt.Circle((ix0B,iy0B),10,color='red',fill=False,lw=2.5,zorder=8))
    elif idx==5:
        shown=0
        for iy_,ix_,_ in obs_peaks:
            if 40<ix_<265 and 90<iy_<210:
                ax.add_patch(plt.Circle((ix_,iy_),10,color='red',fill=False,lw=2.5,zorder=8))
                shown+=1
                if shown>=2: break
    ax.set_xlim(40,265); ax.set_ylim(90,210); plt.colorbar(im,ax=ax,fraction=.046,pad=.04)
axes[0,0].legend(handles=[
    Line2D([0],[0],marker='x',color='cyan',lw=0,ms=9,label='BCG / galaxy peak'),
    Line2D([0],[0],marker='+',color='lime',lw=0,ms=11,label='Gas peak (X-ray)'),
    Line2D([0],[0],marker='o',color='red',lw=0,ms=9,markerfacecolor='none',markeredgewidth=2,label='ECT predicted lensing max'),
],fontsize=8,loc='upper left')
plt.suptitle(f"Bullet Cluster ECT falsification test  |  M_gas/M_gal={M_gas/M_gal:.1f}×\n"
             f"0A (baryon sum) FAILS — peak at gas  |  0B (concentration-weighted) PASSES — peak at BCG",
             fontsize=10,y=1.01)
plt.tight_layout()
out=os.path.join(OUTDIR,'fig_bullet_ect_maps.png')
fig.savefig(out,dpi=150,bbox_inches='tight'); print(f"Saved: {out}")
