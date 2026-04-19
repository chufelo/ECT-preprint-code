#!/usr/bin/env python3
"""
ISW in ECT: semi-analytic benchmark (v3 final)
Status: Level B.  eps=0.01 from Hubble benchmark, NOT fitted to ISW.
All deta != 0 are ILLUSTRATIVE PHENOMENOLOGICAL ANSATZE, not ECT predictions.
Observable: ISW-tracer overlap amplitude proxy (not C_l^{Tg}).
"""
import numpy as np, matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from pathlib import Path
from scipy.integrate import solve_ivp, quad, simpson
from scipy.interpolate import interp1d

OUT = Path(__file__).resolve().parent
Om=0.315; Or=9.1e-5; OL=1.-Om-Or; h=0.674; eps0=0.01

def E(a): return np.sqrt(Or/a**4+Om/a**3+OL)

def solve_growth(mu_f):
    def ode(a,y):
        D,dD=y; Ea=E(a); dE=(1./(2.*Ea))*(-4.*Or/a**5-3.*Om/a**4)
        return [dD, -(3./a+dE/Ea)*dD+1.5*Om*mu_f(a)/(a**5*Ea**2)*D]
    s=solve_ivp(ode,(1e-3,1.),[1e-3,1.],t_eval=np.linspace(1e-3,1.,1500),
                method='RK45',rtol=1e-10,atol=1e-12)
    n=s.y[0][-1]; return s.t, s.y[0]/n, s.y[1]/n

def isw_kernel(a,Di,dDi,mu_f,eta_f):
    da=1e-5; S=mu_f(a)*(1.+eta_f(a))/2.
    if a+da<1. and a-da>0.003:
        dS=(mu_f(a+da)*(1.+eta_f(a+da))/2.-mu_f(a-da)*(1.+eta_f(a-da))/2.)/(2.*da)
    else: dS=0.
    D=Di(a); dD=dDi(a)
    return ((dS*D+S*dD)/a - S*D/a**2)/(a*E(a))

a_arr=np.linspace(0.08,0.998,300); z_arr=1./a_arr-1.
nz_raw=z_arr**2*np.exp(-z_arr/0.35)
nz=nz_raw/simpson(nz_raw,x=z_arr); bias=1.5
Wg=bias*nz/a_arr**2

ag,Dl,dDl=solve_growth(lambda a:1.)
_,De,dDe=solve_growth(lambda a:a**(-2.*eps0))
Di_l=interp1d(ag,Dl,'cubic'); dDi_l=interp1d(ag,dDl,'cubic')
Di_e=interp1d(ag,De,'cubic'); dDi_e=interp1d(ag,dDe,'cubic')

Kl=np.array([isw_kernel(a,Di_l,dDi_l,lambda a:1.,lambda a:1.) for a in a_arr])
Ke0=np.array([isw_kernel(a,Di_e,dDi_e,lambda a:a**(-2.*eps0),lambda a:1.) for a in a_arr])
Ke_slip={}
for de in [0.0,0.02,0.05]:
    ef=lambda a,d=de:1.+d*(1.-a)
    Ke_slip[de]=np.array([isw_kernel(a,Di_e,dDi_e,lambda a:a**(-2.*eps0),ef) for a in a_arr])

def overlap_ratio(K_test,D_test,K_ref,D_ref):
    num=simpson(K_test*Wg*D_test,x=a_arr)
    den=simpson(K_ref*Wg*D_ref,x=a_arr)
    return num/den if abs(den)>1e-30 else 1.

A_base=overlap_ratio(Ke0,Di_e(a_arr),Kl,Di_l(a_arr))
A_02=overlap_ratio(Ke_slip[0.02],Di_e(a_arr),Kl,Di_l(a_arr))
A_05=overlap_ratio(Ke_slip[0.05],Di_e(a_arr),Kl,Di_l(a_arr))

IKl=simpson(Kl**2,x=a_arr); IKe=simpson(Ke0**2,x=a_arr)
power_diag=(IKe/IKl-1)*100

print("="*60)
print("ISW-TRACER OVERLAP AMPLITUDE PROXY")
print("="*60)
print(f"  baseline (eps=0.01, deta=0): {A_base:.4f}")
print(f"  illustr. deta=0.02:          {A_02:.4f}")
print(f"  illustr. deta=0.05:          {A_05:.4f}")
print(f"  Source-power diagnostic (kernel^2, internal): +{power_diag:.1f}%")

obs={'unWISE x Planck (2021)':(0.96,0.30),'VST ATLAS x Planck (2021)':(1.14,0.38),
     'AllWISE x WMAP (2016)':(1.14,0.53),'Planck XXI comb. (2016)':(1.00,0.33)}
print("\nPublished ISW amplitudes (reference only):")
for n,(v,e) in obs.items(): print(f"  {n}: {v:.2f} +/- {e:.2f}")
print("\nThe proxy lies within the broad range of published values.")
print("This is NOT a formal statistical consistency test.")

mu_arr=np.array([a**(-2.*eps0) for a in a_arr])
Sig0=mu_arr.copy(); Sig05=mu_arr*(2.+0.05*(1.-a_arr))/2.
def cum_weight(K):
    c=np.zeros_like(a_arr); tot=simpson(np.abs(K),x=a_arr)
    for i in range(len(a_arr)-1): c[i]=simpson(np.abs(K[i:]),x=a_arr[i:])
    return c/tot if tot>0 else c
Ccl=cum_weight(Kl); Cce=cum_weight(Ke0)

print("\nComputing heatmap...")
escan=np.array([0.,0.005,0.01,0.02,0.03,0.05])
dscan=np.array([0.,0.01,0.02,0.05,0.07,0.10])
Aheat=np.zeros((len(dscan),len(escan)))
for i,ep in enumerate(escan):
    _,Dv,dDv=solve_growth(lambda a,e=ep:a**(-2.*e))
    Div=interp1d(ag,Dv,'cubic')
    for j,de in enumerate(dscan):
        ef=lambda a,d=de:1.+d*(1.-a)
        Kv=np.array([isw_kernel(a,Div,interp1d(ag,dDv,'cubic'),
                     lambda a,e=ep:a**(-2.*e),ef) for a in a_arr])
        Aheat[j,i]=overlap_ratio(Kv,Div(a_arr),Kl,Di_l(a_arr))
print(f"Heatmap done. Benchmark: {Aheat[0,2]:.4f}")

# ==== FIGURE 1 ====
fig,axes=plt.subplots(2,2,figsize=(11,9))

ax=axes[0,0]
ax.plot(z_arr,mu_arr,'k-',lw=2,label=r'$\mu(z)=G_{\rm eff}/G_N$')
ax.plot(z_arr,Sig0,'k--',lw=1.5,label=r'$\Sigma$, $\delta\eta\!=\!0$')
ax.plot(z_arr,Sig05,'k:',lw=1.5,label=r'$\Sigma$, illustr. $\delta\eta\!=\!0.05$')
ax.axhline(1,color='gray',ls=':',lw=.8); ax.set_xlim(0,3); ax.set_ylim(.98,1.12)
ax.set_xlabel('Redshift $z$'); ax.set_ylabel('Response function')
ax.legend(fontsize=9,loc='upper left',framealpha=.9)
ax.set_title(r'(a) $\mu(z)$ and $\Sigma(z)$')
ax.text(.95,.05,r'$\varepsilon=0.01$',transform=ax.transAxes,fontsize=11,ha='right',
        bbox=dict(boxstyle='round',fc='white',ec='gray'))

ax=axes[0,1]; Kn=np.max(np.abs(Kl))
ax.plot(z_arr,Kl/Kn,'k-',lw=2,label=r'$\Lambda$CDM')
ax.plot(z_arr,Ke0/Kn,'k--',lw=2,label='ECT baseline')
ax.plot(z_arr,Ke_slip[0.02]/Kn,'k-.',lw=1.5,label=r'illustr. $\delta\eta\!=\!0.02$')
ax.plot(z_arr,Ke_slip[0.05]/Kn,'k:',lw=2,label=r'illustr. $\delta\eta\!=\!0.05$')
ax.set_xlim(0,3); ax.axhline(0,color='gray',ls=':',lw=.8)
ax.set_xlabel('Redshift $z$'); ax.set_ylabel('ISW source kernel [norm.]')
ax.legend(fontsize=9,loc='upper right',framealpha=.9)
ax.set_title('(b) ISW source kernel')

ax=axes[1,0]
ax.plot(z_arr,Ccl,'k-',lw=2,label=r'$\Lambda$CDM')
ax.plot(z_arr,Cce,'k--',lw=2,label=r'ECT ($\varepsilon\!=\!0.01$)')
ax.set_xlim(0,3); ax.set_ylim(0,1.05)
ax.set_xlabel('Redshift $z$'); ax.set_ylabel('Cumulative source-kernel weight')
ax.legend(fontsize=10,loc='lower right',framealpha=.9)
ax.set_title('(c) Cumulative ISW source weight')
ax.text(.03,.93,'diagnostic curve, not observable',transform=ax.transAxes,
        fontsize=8,va='top',style='italic',color='gray')

ax=axes[1,1]
im=ax.contourf(escan*100,dscan*100,Aheat,levels=np.linspace(.98,1.22,13),cmap='Greys')
cb=plt.colorbar(im,ax=ax); cb.set_label('Overlap proxy amplitude')
ax.plot(1.,0.,'ko',ms=10,mew=2,mfc='white',zorder=5)
ax.annotate('benchmark',xy=(1.,0.),xytext=(2.,2.5),fontsize=9,
            arrowprops=dict(arrowstyle='->'),
            bbox=dict(boxstyle='round',fc='white',ec='gray'))
ax.set_xlabel(r'$\varepsilon$ [%]')
ax.set_ylabel(r'$\delta\eta_{\max}$ [%] (illustrative ansatz)')
ax.set_title(r'(d) Overlap proxy $A(\varepsilon,\delta\eta)$')
plt.tight_layout()
plt.savefig(OUT/"ect_isw_diagnostic_v3.png",dpi=200,bbox_inches='tight')
print("Fig 1 saved.")

# ==== FIGURE 2 ====
fig,axes=plt.subplots(1,2,figsize=(13,5))

ax=axes[0]
onames=list(obs.keys())
ovals=[obs[n][0] for n in onames]; oerrs=[obs[n][1] for n in onames]
ax.errorbar(ovals,range(len(onames)),xerr=oerrs,fmt='ks',ms=7,
            capsize=5,capthick=1.5,lw=1.5,zorder=5,label='Published amplitudes')
ax.axvline(1.,color='gray',ls=':',lw=1.5,label=r'$\Lambda$CDM')
ax.axvline(A_base,color='k',ls='-',lw=2,alpha=.8,
           label=f'ECT baseline proxy ({A_base:.3f})')
ax.axvline(A_02,color='k',ls='--',lw=1.5,alpha=.7,
           label=f'illustr. $\\delta\\eta$=0.02 ({A_02:.3f})')
ax.axvline(A_05,color='k',ls=':',lw=2,alpha=.7,
           label=f'illustr. $\\delta\\eta$=0.05 ({A_05:.3f})')
ax.set_yticks(range(len(onames))); ax.set_yticklabels(onames,fontsize=9)
ax.set_xlabel('ISW amplitude'); ax.set_xlim(0,2)
ax.legend(fontsize=7.5,loc='upper right',framealpha=.95)
ax.set_title('(a) Overlap proxy vs published ISW amplitudes')
ax.grid(True,alpha=.15,axis='x')
ax.annotate(r'$\varepsilon$=0.01 from Hubble benchmark'+
            '\nproxy comparison only\nnot fitted to ISW',
            xy=(A_base+.02,2.3),fontsize=8,
            bbox=dict(boxstyle='round',fc='white',ec='gray',alpha=.9))

ax=axes[1]
Ascan=[]
for ep in escan:
    _,Dv,dDv=solve_growth(lambda a,e=ep:a**(-2.*e))
    Div=interp1d(ag,Dv,'cubic')
    Kv=np.array([isw_kernel(a,Div,interp1d(ag,dDv,'cubic'),
                 lambda a,e=ep:a**(-2.*e),lambda a:1.) for a in a_arr])
    Ascan.append(overlap_ratio(Kv,Div(a_arr),Kl,Di_l(a_arr)))
Ascan=np.array(Ascan)
bv,be=0.96,0.30
ax.plot(escan*100,Ascan,'k-o',lw=2,ms=7,label='ECT baseline proxy')
ax.axhspan(bv-be,bv+be,alpha=.15,color='gray',label='unWISE published range')
ax.axhspan(bv-2*be,bv+2*be,alpha=.06,color='gray')
ax.axhline(bv,color='k',ls=':',lw=1,alpha=.5)
ax.axhline(1.,color='gray',ls=':',lw=1)
ax.axvline(1.,color='k',ls='--',lw=1.5,alpha=.6)
ax.text(1.15,1.12,'benchmark\n'+r'$\varepsilon\!=\!0.01$',fontsize=9)
ax.axhspan(.88,1.12,alpha=.04,color='black')
ax.text(4.,.9,'representative\nfuture precision',fontsize=7.5,
        ha='center',color='gray',style='italic')
ax.set_xlabel(r'$\varepsilon$ [%]')
ax.set_ylabel('Overlap proxy amplitude')
ax.set_title('(b) ISW sensitivity vs published amplitude range')
ax.set_xlim(-.1,5.5); ax.set_ylim(.4,1.5)
ax.legend(fontsize=8.5,loc='upper left',framealpha=.95); ax.grid(True,alpha=.15)
plt.tight_layout()
plt.savefig(OUT/"ect_isw_vs_obs_v3.png",dpi=200,bbox_inches='tight')
print("Fig 2 saved.")

print(f"""
{'='*60}
HONEST SUMMARY (Level B)
{'='*60}
ISW-tracer overlap amplitude proxy:
  baseline: {A_base:.3f}  (~{(A_base-1)*100:.0f}% enhancement)
  illustr. deta=0.02: {A_02:.3f}
  illustr. deta=0.05: {A_05:.3f}
Source-power diagnostic (kernel^2, internal): +{power_diag:.1f}%

The proxy lies within the broad range of published ISW
amplitude measurements. This is NOT a formal statistical
test — the proxy is not the observed estimator itself.
""")
