#!/usr/bin/env python3
"""
fig_bullet_ect_profiles.py
===========================
Figure 3 — Bullet Cluster ECT: 1D profiles along the merger axis (y ~ 152).

Left panel  (0A): gas peak wins over BCG → global max at gas
Right panel (0B): concentration weight shifts global max to BCG
"""
import numpy as np
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy.ndimage import gaussian_filter
import os

OUTDIR = os.path.dirname(os.path.abspath(__file__))

def g2d(X,Y,x0,y0,sx,sy,amp):
    return amp*np.exp(-0.5*(((X-x0)/sx)**2+((Y-y0)/sy)**2))

N=300; X,Y=np.meshgrid(np.arange(N),np.arange(N))
main_gal=(90,150); sub_gal=(215,148); main_gas=(122,155); sub_gas=(188,153)
Sg=(g2d(X,Y,*main_gas,26,22,6.)+g2d(X,Y,*sub_gas,24,20,5.)+g2d(X,Y,153,152,36,11,1.5))
Sv=(g2d(X,Y,*main_gal,10,12,1.)+g2d(X,Y,*sub_gal,8,10,.85))
Ups=3.; Sb=Sg+Ups*Sv
S0A=np.clip(Sb,0,None)
al,Rs,eps,wm=1.5,18,1e-6,.2
lm=gaussian_filter(Sb,sigma=Rs); C=(Sb-lm)/(lm+eps); W=np.maximum(wm,1+al*C); S0B=np.clip(W*Sb,0,None)

fig,(ax_a,ax_b)=plt.subplots(1,2,figsize=(13,5))
x_arr=np.arange(N); row=152
for ax,arr,title,col in [
    (ax_a,S0A,"Model 0A: baryons-only",'#d62728'),
    (ax_b,S0B,f"Model 0B: concentration-weighted (α={al}, R={Rs}px)",'#2ca02c')]:
    gas_p=Sg[row,:]; gal_p=Ups*Sv[row,:]
    ax.fill_between(x_arr,gas_p,alpha=.25,color='lime',label='Gas component')
    ax.fill_between(x_arr,gal_p,alpha=.35,color='cyan',label='Galaxy component')
    ax.plot(x_arr,arr[row,:],color=col,lw=2.5,label='Σ_eff (predicted lensing)')
    for xv,ls,lc,lbl in [(main_gal[0],'--','cyan','BCG position'),(sub_gal[0],'--','cyan',None),
                          (main_gas[0],':','lime','Gas peak'),(sub_gas[0],':','lime',None)]:
        ax.axvline(xv,color=lc,ls=ls,lw=1.5,alpha=.8,label=lbl)
    ix_mx=np.argmax(arr[row,:])
    ax.scatter([ix_mx],[arr[row,ix_mx]],c=col,s=130,zorder=7,marker='^',label=f'Global max x={ix_mx}')
    ax.set_xlim(40,265); ax.set_xlabel('x [pixels] (merger axis)',fontsize=11)
    ax.set_ylabel('Σ_eff',fontsize=10); ax.set_title(title,fontsize=10)
    ax.legend(fontsize=8,loc='upper right'); ax.grid(alpha=.3)
plt.suptitle("Bullet Cluster 1D profiles along merger axis (y≈152)\n"
             "0A: max at gas | 0B: concentration weight shifts max to BCG",fontsize=10)
plt.tight_layout()
out=os.path.join(OUTDIR,'fig_bullet_ect_profiles.png')
fig.savefig(out,dpi=150,bbox_inches='tight'); print(f"Saved: {out}")
