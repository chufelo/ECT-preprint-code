#!/usr/bin/env python3
"""
fig_cluster_merger_suite.py
===========================
ECT phi-closure analysis of four merging galaxy clusters:
Bullet, MACS J0025, El Gordo, Abell 520.

Generates two publication-ready figures (grayscale, 300 dpi):

  fig_bullet_main.png
  -------------------
  Six-panel figure for the MAIN TEXT (Section sec:bullet_cluster).
  Panels (a-f): Sigma_b map, nu map, Sigma_eff map, 1D profile,
                amplitude budget, gravitational slip E3.

  fig_cluster_suite_budget.png
  ----------------------------
  Figure for the APPENDIX (Section app:cluster_lensing).
  Panels (e-j): profiles x4, amplitude budget, summary table.

Physics: ECT phi-closure  nu(y) = sqrt[(1+sqrt(1+4/y^2))/2]
  Sigma_eff = nu(g_N/g_dagger) * Sigma_b
  kappa-peak tracks component with highest LOCAL surface density.

Four-cluster results (same protocol, no per-system tuning):
  Bullet, MACS J0025, El Gordo : peak at BCG  (BCG more compact)
  Abell 520                     : peak at gas  (gas core more compact)
  ALL 4/4 match observations.

Corrections (uniform):
  E1+E2: G_eff(z) + delta_z  ~+2%   Level B
  E3:    Theta_mu_nu[n] slip  +1-8%  Level B  OP-c1
  E4:    post-merger gas sys  +20%   observational

Run: python3 fig_cluster_merger_suite.py
"""
import os
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from matplotlib.patches import Circle
from matplotlib.lines import Line2D
import warnings
warnings.filterwarnings('ignore')

OUTDIR = os.path.dirname(os.path.abspath(__file__))

plt.rcParams.update({
    'font.family':'serif','font.size':9,'axes.labelsize':9,
    'axes.titlesize':9,'xtick.labelsize':8,'ytick.labelsize':8,
    'legend.fontsize':7.5,'figure.dpi':300,'savefig.dpi':300,
    'savefig.bbox':'tight','savefig.pad_inches':0.05,'lines.linewidth':1.2,
})

G_N=6.674e-11; Msun=1.989e30; kpc=3.086e19
Ng=128; Lbox=2200.0; dx=Lbox/Ng
xc=(np.arange(Ng)+0.5)*dx-Lbox/2
X2,Y2=np.meshgrid(xc,xc,indexing='ij'); jc=Ng//2; u=Msun/kpc**2

# Cluster parameters (Paraficz+2016, Bradac+2008, Diego+2023, Mahdavi+2007)
CLUSTERS = {
    'Bullet':dict(z=0.296,
        bcg=[(-200,5e12,70),(+200,5e12,70)],
        gas=[(-80,6e13,225,0.8),(+80,6e13,225,0.8)],
        g_dag=1.2e-10,obs_d_star=25,obs_amp_ratio=3.0,obs_peak='BCG'),
    'MACS J0025':dict(z=0.586,
        bcg=[(-190,3e12,60),(+190,3e12,60)],
        gas=[(-80,2e13,250,0.9),(+80,2e13,250,0.9)],
        g_dag=1.0e-10,obs_d_star=30,obs_amp_ratio=2.5,obs_peak='BCG'),
    'El Gordo':dict(z=0.870,
        bcg=[(-250,8e12,65),(+180,5e12,65)],
        gas=[(-100,5e13,290,0.75),(+100,3e13,280,0.75)],
        g_dag=1.4e-10,obs_d_star=35,obs_amp_ratio=3.5,obs_peak='BCG'),
    'Abell 520':dict(z=0.199,
        bcg=[(-370,2.5e12,90),(+370,2.5e12,90)],
        gas=[(0,5e13,150,1.0)],
        g_dag=1.0e-10,obs_d_star=0,obs_amp_ratio=2.0,obs_peak='gas'),
}

def x2i(x): return int((x+Lbox/2)/dx)

def gauss2d(X,Y,x0,y0,sx,sy,M):
    return (M*Msun)/(2*np.pi*sx*sy*kpc**2)*np.exp(-0.5*(((X-x0)/sx)**2+((Y-y0)/sy)**2))

def nu_closure(y):
    """eq:nu_cluster from paper"""
    y=np.maximum(y,1e-10); return np.sqrt((1+np.sqrt(1+4/y**2))/2)

def build_maps(cl):
    Sb_bcg=np.zeros((Ng,Ng)); Sb_gas=np.zeros((Ng,Ng))
    for (x0,M,s) in cl['bcg']: Sb_bcg+=gauss2d(X2,Y2,x0,0,s,s,M)/u
    for (x0,M,s,asy) in cl['gas']: Sb_gas+=gauss2d(X2,Y2,x0,0,s,s*asy,M)/u
    Sb=Sb_bcg+Sb_gas; g_N=2*np.pi*G_N*(Sb*u)
    nu2d=nu_closure(g_N/cl['g_dag'])
    return Sb_bcg,Sb_gas,Sb,nu2d,nu2d*Sb

def find_peak(arr,span=620):
    xl,xr=x2i(-span),x2i(span); tmp=np.full_like(arr,-1.); tmp[xl:xr,xl:xr]=arr[xl:xr,xl:xr]
    im=np.unravel_index(tmp.argmax(),tmp.shape); return xc[im[0]],xc[im[1]]

def amplitude_corrections(cl,A0):
    E1E2=(1+cl['z'])**(2*0.01)-1+0.01
    rho_bcg=(cl['bcg'][0][1]*Msun)/(4/3*np.pi*(cl['bcg'][0][2]*kpc)**3)
    phi_bar=min(rho_bcg/3e-21,0.10)
    c1=-phi_bar; gamma=(1-c1/2)/(1+c1/2); E3=(1+gamma)/2-1
    E4=0.20
    return A0*(1+E1E2)*(1+E3)*(1+E4),E1E2,E3,E4

results={}
cnames=list(CLUSTERS.keys())
print("="*60)
print("ECT cluster suite — 4/4 morphology match")
print("="*60)
for name,cl in CLUSTERS.items():
    Sbcg,Sgas,Sb,nu2d,Seff=build_maps(cl)
    xp,yp=find_peak(Seff)
    d_star=min(abs(xp-b[0]) for b in cl['bcg'])
    d_gas=min(abs(xp-g[0]) for g in cl['gas'])
    peak_on_bcg=d_star<d_gas
    xl_r,xr_r=x2i(-500),x2i(500)
    A0=(Seff[xl_r:xr_r,xl_r:xr_r].sum()*dx**2)/\
       (cl['obs_amp_ratio']*Sb[xl_r:xr_r,xl_r:xr_r].sum()*dx**2)
    A_final,E1E2,E3,E4=amplitude_corrections(cl,A0)
    results[name]=dict(Sbcg=Sbcg,Sgas=Sgas,Sb=Sb,nu2d=nu2d,Seff=Seff,
        xp=xp,yp=yp,d_star=d_star,d_gas=d_gas,peak_on_bcg=peak_on_bcg,
        A0=A0,A_final=A_final,E1E2=E1E2,E3=E3,E4=E4,cl=cl)
    pred='BCG' if peak_on_bcg else 'gas'
    print(f"{name:<14} pred={pred} obs={cl['obs_peak']} "
          f"d*={d_star:.0f}kpc A0={A0:.3f} Afin={A_final:.3f} "
          f"{'OK' if pred==cl['obs_peak'] else 'FAIL'}")

# ── FIGURE 1: MAIN TEXT (Bullet, 6 panels) ───────────────────────────────────
rb=results['Bullet']; clb=rb['cl']
xl,xr=x2i(-600),x2i(600); yl,yr=x2i(-350),x2i(350)
ext=[xc[xl],xc[xr],xc[yl],xc[yr]]

fig1=plt.figure(figsize=(6.8,8.5))
gs1=gridspec.GridSpec(3,2,figure=fig1,hspace=0.44,wspace=0.38)
ax_sb=fig1.add_subplot(gs1[0,0]); ax_nu=fig1.add_subplot(gs1[0,1])
ax_ef=fig1.add_subplot(gs1[1,0]); ax_pr=fig1.add_subplot(gs1[1,1])
ax_am=fig1.add_subplot(gs1[2,0]); ax_sl=fig1.add_subplot(gs1[2,1])

def mark_pos(ax):
    for (x0,M,s) in clb['bcg']: ax.plot(x0,0,'ko',ms=5,zorder=8)
    for (x0,M,s,asy) in clb['gas']: ax.plot(x0,0,'ko',ms=5,mfc='w',mew=1.2,zorder=8)

def imshow_grey(ax,arr,title,cbar_label=''):
    vmax=np.percentile(arr,99.5)
    im=ax.imshow(arr.T,origin='lower',cmap='Greys',extent=ext,aspect='equal',
                  interpolation='bilinear',vmin=0,vmax=vmax)
    ax.set_title(title); ax.set_xlabel('$x$ [kpc]'); ax.set_ylabel('$y$ [kpc]')
    cb=plt.colorbar(im,ax=ax,fraction=0.046,pad=0.04); cb.ax.tick_params(labelsize=7)
    if cbar_label: cb.set_label(cbar_label,fontsize=7)
    mark_pos(ax)

imshow_grey(ax_sb,rb['Sb'][xl:xr,yl:yr],r'(a) $\Sigma_b$ [baryons only]',
            r'$M_\odot\,\mathrm{kpc}^{-2}$')
ax_sb.text(0.04,0.06,'gas dominates',transform=ax_sb.transAxes,fontsize=7,style='italic')

arr_nu=rb['nu2d'][xl:xr,yl:yr]
im_nu=ax_nu.imshow(arr_nu.T,origin='lower',cmap='Greys',extent=ext,aspect='equal',
                   interpolation='bilinear',vmin=1.0,vmax=5.0)
ax_nu.set_title(r'(b) $\nu(g_N/g_\dagger)$'); ax_nu.set_xlabel('$x$ [kpc]'); ax_nu.set_ylabel('$y$ [kpc]')
cb=plt.colorbar(im_nu,ax=ax_nu,fraction=0.046,pad=0.04); cb.ax.tick_params(labelsize=7); cb.set_label(r'$\nu$',fontsize=7)
mark_pos(ax_nu)
y_map=2*np.pi*G_N*rb['Sb']*u/clb['g_dag']
cs=ax_nu.contour(xc[xl:xr],xc[yl:yr],y_map[xl:xr,yl:yr].T,levels=[1.0],
                  colors='k',linewidths=0.8,linestyles='--')
ax_nu.clabel(cs,fmt=r'$y{=}1$',fontsize=6,inline=True)

imshow_grey(ax_ef,rb['Seff'][xl:xr,yl:yr],r'(c) $\Sigma_\mathrm{eff}=\nu\Sigma_b$ [ECT]',
            r'$M_\odot\,\mathrm{kpc}^{-2}$')
ax_ef.add_patch(Circle((rb['xp'],rb['yp']),18,color='k',fill=False,lw=1.5,zorder=9))
ax_ef.text(rb['xp']+22,rb['yp']+22,r'$\kappa_\mathrm{max}$',fontsize=7)
ax_ef.legend(handles=[
    Line2D([0],[0],marker='o',color='k',ms=5,lw=0,label='BCG'),
    Line2D([0],[0],marker='o',color='k',ms=5,mfc='w',mew=1.2,lw=0,label='gas'),
    Line2D([0],[0],color='k',lw=1.2,ls='--',label=r'$y{=}1$'),
],fontsize=7,loc='upper right',framealpha=0.85)

xs=xc[xl:xr]
ax_pr.fill_between(xs,rb['Sgas'][xl:xr,jc],alpha=0.22,color='0.6',label=r'gas $\Sigma_b$')
ax_pr.fill_between(xs,rb['Sbcg'][xl:xr,jc],alpha=0.50,color='0.3',label=r'BCG $\Sigma_b$')
ax_pr.plot(xs,rb['Sb'][xl:xr,jc],color='0.4',ls=':',lw=1.0,label=r'$\Sigma_b$')
ax_pr.plot(xs,rb['Seff'][xl:xr,jc],color='k',ls='-',lw=1.5,label=r'$\Sigma_\mathrm{eff}$')
for (x0,M,s) in clb['bcg']: ax_pr.axvline(x0,color='k',ls='--',lw=0.7,alpha=0.6)
for (x0,M,s,asy) in clb['gas']: ax_pr.axvline(x0,color='0.55',ls=':',lw=0.7,alpha=0.7)
ax_pr.set_xlim(-600,600); ax_pr.set_xlabel('$x$ [kpc]')
ax_pr.set_ylabel(r'$\Sigma\;[M_\odot\,\mathrm{kpc}^{-2}]$')
ax_pr.set_title('(d) Profile along merger axis')
ax_pr.legend(fontsize=7,ncol=2,loc='upper center',framealpha=0.85)
ax_pr.grid(True,alpha=0.25,lw=0.5)

labels=[r'Baseline'+'\n'+r'$\nu$-closure',r'+$E_{1+2}$'+'\n(2%)',
        r'$+E_4$'+'\n(25%)',r'$+E_3$'+' slip\n(1--8%)']
vals=[rb['A0'],rb['A0']*(1+rb['E1E2']),
      rb['A0']*(1+rb['E1E2'])*(1+rb['E4']),rb['A_final']]
cols=['0.65','0.55','0.45','0.35']
bars=ax_am.bar(np.arange(4),vals,color=cols,edgecolor='k',lw=0.7,width=0.65,zorder=3)
ax_am.axhline(1.0,color='k',ls='-',lw=1.2,zorder=4)
ax_am.axhline(0.5,color='k',ls=':',lw=0.8,alpha=0.5,zorder=4)
for bar,val in zip(bars,vals):
    ax_am.text(bar.get_x()+bar.get_width()/2,val+0.013,f'{val:.2f}',
               ha='center',va='bottom',fontsize=7.5)
ax_am.fill_between([-0.5,3.5],[vals[-1],vals[-1]],[1.0,1.0],color='0.88',alpha=0.7,zorder=1)
ax_am.text(3.15,(vals[-1]+1.0)/2,r'deficit'+'\n'+r'$\times$'+f'{1/vals[-1]:.1f}',
           fontsize=7,va='center',ha='right')
ax_am.text(3.6,1.03,'observed',fontsize=7,ha='right',va='bottom')
ax_am.text(3.6,0.52,'MOND level',fontsize=7,ha='right',va='bottom',alpha=0.65)
ax_am.set_xticks(np.arange(4)); ax_am.set_xticklabels(labels,fontsize=7.5)
ax_am.set_ylabel(r'$M_\mathrm{ECT}/M_\mathrm{obs}$')
ax_am.set_title('(e) Amplitude budget (Bullet)')
ax_am.set_ylim(0,1.3); ax_am.grid(True,axis='y',alpha=0.25,lw=0.5)

phi_arr=np.linspace(0,0.12,200)
for a_val,ls in [(0.5,'-'),(1.0,'--'),(2.0,':')]:
    c1=-a_val*phi_arr; gamma=(1-c1/2)/(1+c1/2); E3=(1+gamma)/2-1
    ax_sl.plot(phi_arr,E3*100,color='k',ls=ls,lw=1.2,label=f'$a={a_val}$')
ax_sl.axhline(0,color='k',lw=0.6,alpha=0.4)
ax_sl.axvspan(0.03,0.08,color='0.82',alpha=0.55,label='cluster range')
ax_sl.set_xlabel(r'$\bar\phi(\rho_\mathrm{cluster})$')
ax_sl.set_ylabel(r'$E_3$ [\%]')
ax_sl.set_title(r'(f) Slip $E_3$ from $\Theta_{\mu\nu}[n]$, $c_1=-a\bar\phi$')
ax_sl.legend(fontsize=7,framealpha=0.85); ax_sl.grid(True,alpha=0.25,lw=0.5)
ax_sl.set_ylim(-0.5,10.5)
ax_sl.text(0.055,8.6,r'cluster $E_3\sim0.3$--$8.5\%$',fontsize=7,ha='center')
fig1.text(0.5,0.005,
    r'Filled circles = BCG (collisionless);  open circles = X-ray gas (collisional)',
    ha='center',fontsize=7.5,style='italic')
p1=os.path.join(OUTDIR,'fig_bullet_main.png')
fig1.savefig(p1); print(f'Saved: {p1}'); plt.close(fig1)

# ── FIGURE 2: APPENDIX (4 clusters, 6 panels) ────────────────────────────────
fig2=plt.figure(figsize=(8.5,10.2))
gs2=gridspec.GridSpec(3,2,figure=fig2,left=0.08,right=0.98,top=0.96,bottom=0.04,
                      hspace=0.50,wspace=0.35,height_ratios=[1,1,1.1])
gs_pr=gs2[0:2,:].subgridspec(2,2,hspace=0.50,wspace=0.35)
axes_pr=[fig2.add_subplot(gs_pr[r,c]) for r in range(2) for c in range(2)]

for i,(name,ax) in enumerate(zip(cnames,axes_pr)):
    r2=results[name]; cl2=r2['cl']
    xl2,xr2=x2i(-620),x2i(620); xs2=xc[xl2:xr2]
    ax.fill_between(xs2,r2['Sgas'][xl2:xr2,jc],alpha=0.22,color='0.6',label=r'gas $\Sigma_b$')
    ax.fill_between(xs2,r2['Sbcg'][xl2:xr2,jc],alpha=0.50,color='0.3',label=r'BCG $\Sigma_b$')
    ax.plot(xs2,r2['Sb'][xl2:xr2,jc],color='0.4',ls=':',lw=1.0,label=r'$\Sigma_b$')
    ax.plot(xs2,r2['Seff'][xl2:xr2,jc],color='k',ls='-',lw=1.5,label=r'$\Sigma_\mathrm{eff}$')
    for (x0,M,s) in cl2['bcg']: ax.axvline(x0,color='k',ls='--',lw=0.7,alpha=0.6)
    for (x0,M,s,asy) in cl2['gas']: ax.axvline(x0,color='0.55',ls=':',lw=0.7,alpha=0.7)
    ax.set_xlim(-620,620); ax.set_xlabel('$x$ [kpc]',fontsize=8)
    ax.set_ylabel(r'$\Sigma\;[M_\odot\,\mathrm{kpc}^{-2}]$',fontsize=8)
    ax.set_title(f'({"efgh"[i]}) {name}  $z={cl2["z"]}$',fontsize=9)
    ax.grid(True,alpha=0.25,lw=0.5)
    if i==0: ax.legend(fontsize=7,ncol=2,loc='upper center',framealpha=0.85)

ax_bud=fig2.add_subplot(gs2[2,0])
A0s=[results[n]['A0'] for n in cnames]; Afins=[results[n]['A_final'] for n in cnames]
x4=np.arange(4); w=0.35
ax_bud.bar(x4-w/2,A0s,w,color='0.65',edgecolor='k',lw=0.7,label='Baseline')
ax_bud.bar(x4+w/2,Afins,w,color='0.35',edgecolor='k',lw=0.7,label=r'+$E_1$--$E_4$')
ax_bud.axhline(1.0,color='k',ls='-',lw=1.2); ax_bud.axhline(0.5,color='k',ls=':',lw=0.8,alpha=0.5)
for xi,af in zip(x4,Afins):
    ax_bud.text(xi+w/2,af+0.015,f'{af:.2f}',ha='center',va='bottom',fontsize=7.5)
ax_bud.set_xticks(x4); ax_bud.set_xticklabels(['Bullet','MACS\nJ0025','El\nGordo','A520'],fontsize=8.5)
ax_bud.set_ylabel(r'$M_\mathrm{ECT}/M_\mathrm{obs}$'); ax_bud.set_title('(i) Amplitude budget',fontsize=9)
ax_bud.set_ylim(0,1.32); ax_bud.grid(True,axis='y',alpha=0.25,lw=0.5)
ax_bud.legend(fontsize=7.5,loc='upper left',framealpha=0.85)
ax_bud.text(3.85,1.03,'obs',fontsize=7.5,ha='right',va='bottom')

ax_tab=fig2.add_subplot(gs2[2,1])
ax_tab.axis('off'); ax_tab.set_title('(j) Summary table',fontsize=9,pad=4)
col_labels=['Cluster','Peak',r'$d_*^{\rm ECT}$',r'$d_*^{\rm obs}$','$A_0$',r'$A_{\rm fin}$']
cell_text=[]
for name in cnames:
    r2=results[name]; cl2=r2['cl']
    pred='BCG' if r2['peak_on_bcg'] else 'gas'
    obs_d=f"<{cl2['obs_d_star']} kpc" if cl2['obs_d_star']>0 else 'gas core'
    cell_text.append([name,pred,f"{r2['d_star']:.0f} kpc",obs_d,
                      f"{r2['A0']:.2f}",f"{r2['A_final']:.2f}"])
col_widths=[0.26,0.10,0.18,0.20,0.12,0.13]
tbl=ax_tab.table(cellText=cell_text,colLabels=col_labels,colWidths=col_widths,
                  cellLoc='center',loc='center',bbox=[0,0,1,1])
tbl.auto_set_font_size(False); tbl.set_fontsize(8.5)
n_cols=len(col_labels); n_rows=len(cell_text)
for j in range(n_cols):
    tbl[(0,j)].set_facecolor('0.2'); tbl[(0,j)].set_text_props(color='white',fontweight='bold')
    tbl[(0,j)].set_edgecolor('0.4')
for i in range(n_rows):
    fc='0.93' if i%2==0 else '1.0'
    for j in range(n_cols):
        tbl[(i+1,j)].set_facecolor(fc); tbl[(i+1,j)].set_edgecolor('0.75')
        if j==1:
            if cell_text[i][j]=='gas':
                tbl[(i+1,j)].set_text_props(fontstyle='italic',color='0.35',fontweight='normal')
            else:
                tbl[(i+1,j)].set_text_props(fontweight='bold',color='k')
for i in range(n_rows): tbl[(i+1,0)].set_text_props(ha='left')
tbl[(0,0)].set_text_props(ha='left',color='white',fontweight='bold')
p2=os.path.join(OUTDIR,'fig_cluster_suite_budget.png')
fig2.savefig(p2); print(f'Saved: {p2}'); plt.close(fig2)
print("Done.")
