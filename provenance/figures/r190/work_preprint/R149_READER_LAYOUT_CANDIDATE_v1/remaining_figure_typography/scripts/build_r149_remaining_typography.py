#!/usr/bin/env python3
"""Deterministic, presentation-only successors for R149 small-label figures.

Scientific arrays, equations, labels, statuses and caveats are copied from
their active owners.  Only canvas geometry, public typography and placement
are changed.  The script writes exclusively inside this proposal component.
"""

from __future__ import annotations

import csv
import datetime as dt
import hashlib
import json
import math
import os
from pathlib import Path

os.environ.setdefault("SOURCE_DATE_EPOCH", "0")
os.environ.setdefault("MPLCONFIGDIR", "/tmp/ect-r149-remaining-mpl")
os.environ.setdefault("XDG_CACHE_HOME", "/tmp/ect-r149-remaining-xdg")

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch
import numpy as np


SCRIPT = Path(__file__).resolve()
COMPONENT = SCRIPT.parents[1]
OUT = COMPONENT / "outputs"
ROOT = next(p for p in SCRIPT.parents if (p / "ECT_preprint.tex").is_file())
LATEX = ROOT

BLUE = "#0072B2"
GREEN = "#009E73"
ORANGE = "#D55E00"
AMBER = "#A66E00"
PURPLE = "#CC79A7"
BLACK = "#222222"
GREY = "#666666"
LIGHT = "#E8E8E8"
PALE_BLUE = "#D9EAF7"
PALE_GREEN = "#DDF3EA"
PALE_AMBER = "#FCE8C4"
WHITE = "#FFFFFF"

FIXED = dt.datetime(2026, 7, 24, tzinfo=dt.timezone.utc)
ACC_CONV = 1e6 / 3.0856775814913673e19


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def configure() -> None:
    plt.rcParams.update({
        "font.family": "DejaVu Sans",
        "font.size": 14.0,
        "axes.titlesize": 14.5,
        "axes.labelsize": 14.0,
        "xtick.labelsize": 13.5,
        "ytick.labelsize": 13.5,
        "legend.fontsize": 12.5,
        "axes.linewidth": 0.8,
        "pdf.fonttype": 42,
        "ps.fonttype": 42,
        "savefig.facecolor": "white",
    })


def save(fig: plt.Figure, stem: str, title: str, subject: str) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    meta = {
        "Title": title, "Author": "ECT reproducibility workflow",
        "Subject": subject, "Creator": SCRIPT.name,
        "CreationDate": FIXED, "ModDate": FIXED,
    }
    fig.savefig(OUT / f"{stem}.pdf", bbox_inches="tight", metadata=meta)
    fig.savefig(OUT / f"{stem}.png", dpi=240, bbox_inches="tight",
                metadata={"Software": "ECT R149 deterministic renderer"})
    plt.close(fig)


def box(ax, xy, wh, text, fill, edge, ls="-", fs=10.4):
    x, y = xy; w, h = wh
    ax.add_patch(FancyBboxPatch((x-w/2, y-h/2), w, h,
        boxstyle="round,pad=0.07,rounding_size=0.12",
        facecolor=fill, edgecolor=edge, linestyle=ls, linewidth=1.4))
    ax.text(x, y, text, ha="center", va="center", fontsize=fs,
            linespacing=1.08, color=BLACK)


def arrow(ax, a, b, ls="--", rad=0):
    ax.add_patch(FancyArrowPatch(a, b, arrowstyle="-|>", mutation_scale=12,
        linewidth=1.3, linestyle=ls, color=BLACK,
        connectionstyle=f"arc3,rad={rad}"))


def architecture() -> None:
    fig, ax = plt.subplots(figsize=(7.0, 7.5))
    ax.set_xlim(0, 10); ax.set_ylim(0.2, 16.2); ax.axis("off")
    ax.text(5, 15.85, "Euclidean Condensate Theory - programme architecture",
            ha="center", weight="bold", fontsize=13)
    ax.text(5, 15.45, "Candidate or conditional routes never upgrade claim status.",
            ha="center", color=GREY, fontsize=10)
    box(ax, (5,14.55),(7.6,0.85), r"$\Phi$-medium on $M^4$ - P1-P6 and DP"+"\n"+r"proposed S11 / ERP-$\Phi$",
        PALE_BLUE, BLUE, fs=10.8)
    box(ax, (5,12.95),(7.9,1.55),
        r"P4-supplied $O(4)\to O(3)$ ordered branch"+"\n"
        r"$\langle\partial_A\Phi\rangle=u_0\delta_{Aw}$ (input)"+"\n"
        r"principal scalar hyperbolicity: $\alpha>\beta$"+"\n"
        "physical clocks / metric Open",
        PALE_GREEN, GREEN, "-.", fs=10.2)
    box(ax, (5,11.15),(6.7,0.9),
        "Supplied scalar ordered-branch EFT\n"
        r"$K^{AB}=\beta\delta^{AB}-\alpha n^A n^B$",
        WHITE, GREY, fs=10.5)
    box(ax, (2.55,9.40),(4.35,1.15),
        "Metric / gravity completion\nMacroscopic Physics, Part II\nphysical tensor, source, metric Open",
        WHITE, GREY, "--", 9.9)
    box(ax, (7.45,9.40),(4.35,1.15),
        "Quantum reconstruction programme\nQuantum Sector, Part III\nstate / operators / Born owners Open",
        WHITE, GREY, "--", 9.9)
    box(ax, (2.55,6.20),(4.35,2.30),
        r"Scalar ansatz; tensor and $G_N$"+"\nowners Open\n"
        r"Conditional ERP-$\Phi$/HRC cosmology"+"\n"
        "BTFR/RAR diagnostics\nmetric/lensing Open",
        WHITE, GREY, "--", 9.8)
    box(ax, (7.45,6.20),(4.35,2.65),
        "Supplied free-Gaussian\ncomplete corrected OS-II package\n"
        "PES-R taxonomy; measure route conditional\n"
        r"Gleason: $\dim\mathcal{H}\geq3$ under C1+C2"+"\n"
        "qubit: C2q Busch effect/POVM\nphysical state/event/probability\noutcome/update owners Open",
        WHITE, GREY, "--", 9.5)
    box(ax, (5,2.85),(8.8,1.70),
        "Conditional outputs / external falsifiers\n"
        r"BTFR slope 4 conditional; $a_{M0}$ matched"+"\n"
        "LIV / fifth-force / scalar-BVP / Unruh targets\nphysical ECT owners Open",
        PALE_AMBER, AMBER, "--", 10.2)
    for a,b in [((5,14.12),(5,13.78)),((5,12.18),(5,11.63)),
                ((4.05,10.70),(2.85,10.00)),((5.95,10.70),(7.15,10.00)),
                ((2.55,8.82),(2.55,7.40)),((7.45,8.82),(7.45,7.58)),
                ((2.55,5.02),(4.18,3.72)),((7.45,4.87),(5.82,3.72))]:
        arrow(ax,a,b)
    ax.add_patch(FancyArrowPatch((4.75,8.15),(5.25,8.15),
        arrowstyle="<|-|>", mutation_scale=11, linewidth=1.1,
        linestyle="--", color=GREY))
    ax.text(5,8.05,"common-action back-reaction not yet derived",
            ha="center", fontsize=9.2, color=GREY, style="italic",
            bbox=dict(boxstyle="round,pad=.08",fc=WHITE,ec="none",alpha=.94))
    ax.text(5,1.32,"Dashed near-black arrows: conditional/candidate routes; literal Open text remains authoritative.",
            ha="center", fontsize=9.4, color=BLACK)
    ax.text(5,0.86,"Colour is redundant through luminance, border style and direct status wording.",
            ha="center", fontsize=9.4, color=GREY)
    save(fig, "fig_ect_architecture_typography_r149",
         "Euclidean Condensate Theory programme architecture",
         "Presentation-only reflow of active Figure 1; statuses and topology preserved.")


def species() -> None:
    phi0 = 2.44e18
    groups = [("Leptons", {"$e$":.000511,r"$\mu$":.1057,r"$\tau$":1.777}, BLUE),
              ("Hadrons", {"$p/n$":.938}, GREEN),
              ("Heavy quarks", {"$b$":4.18,"$t$":173.0}, AMBER)]
    fig,ax=plt.subplots(figsize=(7.1,4.9)); y=0; ticks=[]; labs=[]; spans=[]
    for gn,ps,col in groups:
        s=y
        for name,m in ps.items():
            v=np.log10(m/phi0); ax.barh(y,v,color=col,edgecolor=BLACK,height=.6)
            ax.text(v+.3,y,rf"$\sim10^{{{int(round(v))}}}$",va="center",fontsize=12.0)
            ticks.append(y); labs.append(name); y+=1
        spans.append((gn,s,y-1,col)); y+=.4
    ax.set_yticks(ticks,labs); ax.set_xlabel(
        r"$\log_{10}\,\beta_5^{\rm bench}$,  $\beta_5^{\rm bench}=m_f/\phi_0$"
        "\n(hand-selected ratio; not a derived microscopic coupling)")
    ax.set_xlim(-24,-13); ax.invert_xaxis(); ax.set_ylim(-.5,y-.2)
    for gn,s,e,col in spans:
        ax.annotate(gn,(-13.5,(s+e)/2),fontsize=11.8,ha="left",va="center",
                    style="italic",bbox=dict(boxstyle="round,pad=.2",fc=WHITE,ec=col,lw=.8))
    x=np.log10(.000511/phi0); ax.axvline(x,color=GREY,ls=":",lw=.8)
    ax.text(x-.15,y-.3,"electron\nbenchmark",fontsize=11.5,ha="right",va="top",color=GREY)
    ax.set_title(r"Hand-selected species benchmark $\beta_5^{\rm bench}\sim m_f/\phi_0$ (Level C/Open)")
    fig.tight_layout()
    save(fig,"fig_species_beta5_typography_r149","Hand-selected species benchmark",
         "Presentation-only successor; benchmark values and status unchanged.")


def coupling() -> None:
    labels=["Strong\n"+r"$\alpha_s$","EM\n"+r"$\alpha$",
            "Gravity\n"+r"$G_Nm^2/\hbar c$","Unowned benchmark\n"+r"$\beta_5^{\rm bench}=m_f/\phi_0$"]
    ve=[0,-2.14,-44.8,-22.3]; vp=[0,-2.14,-38.2,-18.4]; x=np.arange(4)
    fig,ax=plt.subplots(figsize=(7.2,5.1))
    ax.scatter(x-.12,ve,s=110,marker="o",color=BLUE,edgecolors=BLACK,label="electron scale",zorder=5)
    ax.scatter(x+.12,vp,s=110,marker="s",color=AMBER,edgecolors=BLACK,label="proton scale",zorder=5)
    for i,(a,b) in enumerate(zip(ve,vp)):
        ax.plot([x[i]-.12,x[i]+.12],[a,b],color=".7")
        ax.text(x[i]-.12,a-2.5 if a<-5 else a+2,
                rf"$10^{{{int(round(a))}}}$" if a<-5 else r"$\sim1$",ha="center",fontsize=11.5)
        if b<-5 and abs(b-a)>3: ax.text(x[i]+.12,b-2.5,rf"$10^{{{int(round(b))}}}$",ha="center",fontsize=11.5)
    ax.set_xticks(x,labels); ax.set_ylabel(r"$\log_{10}$(characteristic dimensionless suppression)")
    ax.set_ylim(-52,8); ax.axhline(0,color=BLACK,lw=.6); ax.legend(loc="lower right")
    ax.annotate(r"$\beta_5^{\rm bench}>\alpha_G$ numerically,"
                "\nbut this hand-set benchmark is not\na derived force coupling",
                (2.48,-30.5),ha="center",va="center",fontsize=11.5,
                bbox=dict(boxstyle="round,pad=.35",fc=PALE_AMBER,ec=AMBER))
    ax.set_title("Schematic comparison with a hand-selected C/Open benchmark\n"
                 "(not identical force laws; not an ECT prediction)")
    fig.tight_layout()
    save(fig,"fig_coupling_comparison_typography_r149","Conditional coupling comparison",
         "Presentation-only successor; values, labels and scientific caveat unchanged.")


def seesaw() -> None:
    v2=246.; phi0=2.44e18; mr=np.logspace(6,19,500)
    ys=[1.,.1,4.5e-3,1e-3,1e-4]
    labs=[r"$y_\nu=1$",r"$y_\nu=0.1$",r"$y_\nu\approx4.5\times10^{-3}$",r"$y_\nu=10^{-3}$",r"$y_\nu=10^{-4}$"]
    styles=["--","-.", "-",":",(0,(3,1,1,1,1,1))]; cols=[GREY,ORANGE,BLUE,GREEN,AMBER]
    marks=["s","^",None,"o","v"]
    fig,ax=plt.subplots(figsize=(7.0,5.4))
    for y,lab,ls,c,m in zip(ys,labs,styles,cols,marks):
        ax.plot(mr,y*y*v2*v2/mr*1e9,ls=ls,lw=2.2 if y==4.5e-3 else 1.5,
                color=c,label=lab,marker=m,markevery=75,ms=3.5)
    floor=v2*v2/phi0*1e9; ax.axhline(floor,color=GREY,ls="--",lw=1)
    ax.text(1.5e6,floor*1.8,r"supplied benchmark $m_\nu=v_2^2/\phi_0$",fontsize=11.5)
    ax.axhspan(.04,.06,color=LIGHT,zorder=0); ax.text(3e17,.05,"imported atmospheric band",fontsize=11.5,ha="right")
    for xv,lab,ls in [(2.4e10,"supplied $M_R$ anchor","-"),(1e9,"leptogenesis benchmark","--"),(2.44e18,r"$\phi_0$",":")]:
        ax.axvline(xv,color=GREY,ls=ls,lw=.8); ax.text(xv*1.15,2e-7,lab,rotation=90,fontsize=11.5,va="bottom")
    ax.set(xscale="log",yscale="log",xlim=(1e6,1e19),ylim=(1e-7,1e4),
           xlabel=r"$M_R$ [GeV]",ylabel=r"$m_\nu$ [eV]")
    ax.legend(loc="upper right"); ax.set_title("SUPPLIED SEESAW BENCHMARK - Level C/Open;\nanchors are not ECT predictions",color="#7A1F1F",weight="bold")
    fig.tight_layout()
    save(fig,"fig_neutrino_seesaw_typography_r149","Supplied seesaw benchmark",
         "Presentation-only successor; arrays, anchors, line identities and status unchanged.")


def neutrino_correction() -> None:
    e=np.logspace(-2,6,500); ev=e*1e9
    std=2.5e-3/(2*ev); director=2e-29*ev
    fig,ax=plt.subplots(figsize=(7.1,5.0))
    ax.loglog(e,std,color=GREY,ls="--",lw=2,marker="s",markevery=75,
              label=r"imported $\Delta m^2_{\rm atm}/(2E)$")
    ax.loglog(e,director,color=AMBER,lw=2,marker="D",markevery=75,
              label=r"optional $\beta_\nu^{\rm bench}E$")
    ax.axvspan(.1,100,color=LIGHT,zorder=-5,label="illustrative energy band")
    ax.text(.5,.05,r"$\kappa_\nu=1$ BENCHMARK ONLY - vertex/coefficient Open",
            transform=ax.transAxes,ha="center",weight="bold",fontsize=11.8,
            bbox=dict(boxstyle="round,pad=.3",fc=PALE_AMBER,ec=AMBER))
    ax.set(xlabel=r"Energy $E$ [GeV]",ylabel="Hamiltonian scale [eV]")
    ax.set_title("Optional preferred-direction diagnostic (not an ECT prediction)")
    ax.grid(True,which="both",ls=":",alpha=.35); ax.legend()
    fig.tight_layout()
    save(fig,"fig_neutrino_corrections_typography_r149","Optional neutrino director diagnostic",
         "Presentation-only successor; conditional curves and caveat unchanged.")


def timescale() -> None:
    path=LATEX/"data/cosmology_r113/R113_ONE_POLE_CLUSTER_NO_GO_v2.json"
    d=json.loads(path.read_text())
    rows=sorted((float(k.removeprefix("H0=")),1000*float(v)) for k,v in d["tau_aM_Gyr"].items())
    h=np.array([r[0] for r in rows]); tau=np.array([r[1] for r in rows])
    req=sorted(float(v) for v in d["required_offset_times_Myr"].values())
    fig,ax=plt.subplots(figsize=(7.1,4.9))
    ax.fill_between([h.min()-1,h.max()+1],min(req),max(req),facecolor=PALE_BLUE,
                    edgecolor=BLUE,linewidth=1.2,label="70-100 kpc ballistic target")
    ax.plot(h,tau,color=ORANGE,ls="-.",marker="x",ms=8,mew=1.7,lw=2,
            label=r"conditional $\tau_{a_M}=2\pi/H_0$")
    ax.set_yscale("log"); ax.set_xlabel(r"$H_0$ [km s$^{-1}$ Mpc$^{-1}$]"); ax.set_ylabel("time [Myr]")
    ax.set_title("Conditional timescale mismatch"); ax.grid(True,which="both",alpha=.3); ax.legend(loc="center left")
    ax.text(.98,.06,"required merger-offset time",transform=ax.transAxes,ha="right",
            color=BLUE,weight="bold",fontsize=11.5)
    fig.suptitle("One-real-pole cluster-scale test",weight="bold",y=.99)
    fig.tight_layout()
    save(fig,"fig11_a_timescale_mismatch_typography_r149","One-real-pole timescale mismatch",
         "Presentation-only successor; frozen R113 values and conditional no-go unchanged.")


def chronology() -> None:
    path=LATEX/"data/cosmology_r103/R103_TWO_SLOPE_CONDITIONAL_OBSERVABLES_v1.csv"
    rows=list(csv.DictReader(path.open()))
    z=np.array([float(r["z"]) for r in rows]); t2=np.array([float(r["H0_t_two_slope"]) for r in rows])
    tc=np.array([float(r["H0_t_reference"]) for r in rows]); order=np.argsort(z)[::-1]
    z=z[order]; conv=977.7922216807891/67.4; t2=conv*t2[order]; tc=conv*tc[order]
    res=1e6*(t2-tc)
    fig,(ax,ra)=plt.subplots(2,1,figsize=(7.0,8.8),gridspec_kw={"height_ratios":[2.45,1]})
    fig.suptitle("Conditional chronology of the named two-slope ordered branch",weight="bold",y=.985)
    fig.subplots_adjust(left=.12,right=.97,bottom=.275,top=.875,hspace=.64)
    ax.set_xscale("log"); ax.set_xlim(.14,16); ax.set_ylim(0,1.22); ax.set_yticks([])
    ax.set_xlabel("conditional branch age [Gyr, logarithmic scale]"); ax.set_xticks([.2,.5,1,2,5,10],["0.2","0.5","1","2","5","10"])
    for s in ("left","right","top"): ax.spines[s].set_visible(False)
    ax.grid(True,axis="x")
    ax.text(.02,1.08,"Formation/front selection: Open\nsolver enters an already ordered regular branch",
            transform=ax.transAxes,ha="left",va="center",weight="bold",fontsize=12.0,
            bbox=dict(boxstyle="round,pad=.3",fc=PALE_AMBER,ec=AMBER,ls="--"))
    ax.plot([t2[0],t2[-1]],[.57,.57],color=BLUE,lw=3,solid_capstyle="round")
    ax.plot([tc[0],tc[-1]],[.43,.43],color=GREY,lw=1.8,ls="--")
    ax.text(13.65,.64,"two-slope",color=BLUE,ha="right",weight="bold",fontsize=12.0)
    ax.text(13.65,.33,"matched control",color=GREY,ha="right",fontsize=12.0)
    for i,(zi,ti,ct) in enumerate(zip(z,t2,tc)):
        ax.plot(ti,.57,"o",ms=5,color=BLUE); ax.plot(ct,.43,"D",ms=4,mfc=WHITE,mec=GREY)
        yy=.18 if i%2==0 else .79; va="top" if yy<.3 else "bottom"
        ax.plot([ti,ti],[.53 if yy<.3 else .61,yy+(.02 if yy<.3 else -.02)],color="#AAB0B3",lw=.7)
        age=f"{ti:.3f}" if ti<10 else f"{ti:.2f}"
        ax.text(ti,yy,f"$z={zi:g}$\n{age} Gyr",ha="center",va=va,fontsize=11.5)
    ra.plot(z,res,color=AMBER,lw=2,marker="o",ms=4.5,label=r"$t_{2s}-t_{ctl}$")
    ra.axhline(0,color=BLACK,ls=":",lw=.8); ra.set_xscale("log"); ra.invert_xaxis()
    ra.set(xlabel="redshift $z$ (early $\\rightarrow$ present)",ylabel="age residual [kyr]")
    ra.set_title("Residual on its own scale;\nthe histories overlap in the main chronology",
                 fontsize=12.0, pad=8)
    ra.grid(True); ra.legend(loc="lower left")
    ra.text(.99,.18,"same present fractions;\nno independent JWST likelihood",
            transform=ra.transAxes,ha="right",fontsize=11.2,color=GREY,
            bbox=dict(boxstyle="round,pad=.15",fc=WHITE,ec="none",alpha=.92))
    fig.text(.5,.055,
             r"Externally supplied calibration: $H_0=67.4$ km s$^{-1}$ Mpc$^{-1}$,"
             r" $t_0=13.980496$ Gyr."
             "\n"+r"The separate BC03 clock fit ($H_0=68.586\pm3.949$) is not used here."
             "\nNeither calibration is a universal P1-P6 prediction.",
             ha="center",fontsize=11.0,linespacing=1.18)
    save(fig,"r123_conditional_chronology_typography_r149","Conditional two-slope chronology",
         "Presentation-only successor from frozen R103 arrays; statuses and numerical values unchanged.")


def mu0(x): return x/np.sqrt(1+np.asarray(x)**2)
def mu3(x):
    xx=np.asarray(x); y=xx*xx
    return mu0(xx)*(1-(4/3)*y/(1+y)**2)
def solve_g(gn,a,which):
    if gn<=0:return 0.
    law=mu0 if which=="HRC0" else mu3; lo=gn; hi=max(gn+a,math.sqrt(gn*a)*4,a)
    while float(law(hi/a))*hi<gn:hi*=2
    for _ in range(100):
        mid=(lo+hi)/2
        if float(law(mid/a))*mid<gn:lo=mid
        else:hi=mid
    return (lo+hi)/2


def rar() -> None:
    p=LATEX/"data/hrc_r97/R97_HRC_SOURCE_POINTS.csv"; s=LATEX/"data/hrc_r97/R97_HRC_SOURCE_SCALE_SUMMARY.json"
    rows=list(csv.DictReader(p.open())); physical={}
    for r in rows: physical.setdefault((r["galaxy"],r["source_row_index"]),r)
    gn=np.array([float(r["gN_si"]) for r in physical.values()])
    go=np.array([float(r["vobs_km_s"])**2/max(float(r["radius_kpc"]),1e-12)*ACC_CONV for r in physical.values()])
    d=json.loads(s.read_text())
    a0=np.mean([v["a0_si_mean"] for v in d["cross_validation"]["HRC0"]["by_seed"].values()])
    a3=np.mean([v["a0_si_mean"] for v in d["cross_validation"]["HRC3"]["by_seed"].values()])
    grid=np.logspace(-13.5,-8.5,350)
    pred0=np.array([solve_g(v,a0,"HRC0") for v in grid]); pred3=np.array([solve_g(v,a3,"HRC3") for v in grid])
    fig,ax=plt.subplots(figsize=(7.0,5.8))
    ax.scatter(gn,go,s=6,alpha=.18,color=GREY,rasterized=True,label="SPARC points (3343)")
    ax.plot(grid,grid,color=BLACK,lw=1.4,ls=":",label="Newtonian")
    ax.plot(grid,pred0,color=BLUE,lw=2.3,ls="--",label=f"HRC-0, $a_M={a0:.2e}$")
    ax.plot(grid,pred3,color=ORANGE,lw=2.3,ls="-",label=f"HRC-3, $a_M={a3:.2e}$")
    ax.set(xscale="log",yscale="log",xlabel=r"$g_N$ [m s$^{-2}$]",ylabel=r"$g_{\rm obs}$ [m s$^{-2}$]")
    ax.set_title("HRC-only radial-acceleration diagnostic"); ax.grid(True,which="both",alpha=.22); ax.legend()
    fig.tight_layout()
    save(fig,"R97_HRC_RAR_DIAGNOSTIC_typography_r149","HRC-only RAR diagnostic",
         "Presentation-only successor; frozen 3343 entries and held-out HRC scales unchanged.")


def udg() -> None:
    rows=list(csv.DictReader((LATEX/"data/hrc_r97/R97_HRC_UDG_DIAGNOSTIC.csv").open()))
    fig,ax=plt.subplots(figsize=(7.1,5.8))
    for r in rows:
        name=r["object"]; x=float(r["Rdyn"])
        if r["domain"]=="NO_POSITIVE_HRC_ENHANCEMENT_SOLUTION":
            ax.scatter(x,1,marker="x",s=80,color=BLACK,lw=2)
            ax.annotate(name,(x,1),xytext=(7,8),textcoords="offset points",fontsize=11.5); continue
        a0=float(r["aM_HRC0_over_match"]); a3=float(r["aM_HRC3_over_match"])
        ax.scatter(x,a0,marker="o",s=55,facecolor=WHITE,edgecolor=BLUE,lw=1.5)
        ax.scatter(x,a3,marker="s",s=48,facecolor=ORANGE,edgecolor=BLACK,lw=.6)
        disp=name
        if r["endpoint"]!="central":disp+=" (low)" if r["endpoint"].startswith("low") else " (high)"
        offset=(-7,8) if x>30 else (7,7)
        align="right" if x>30 else "left"
        ax.annotate(disp,(x,a3),xytext=offset,textcoords="offset points",
                    ha=align,fontsize=11.2)
    ax.axhline(1,color=BLACK,ls=":",lw=1.4,label="matched scale")
    ax.scatter([],[],marker="o",facecolor=WHITE,edgecolor=BLUE,label="HRC-0 inverse")
    ax.scatter([],[],marker="s",facecolor=ORANGE,edgecolor=BLACK,label="HRC-3 inverse")
    ax.scatter([],[],marker="x",color=BLACK,label="no positive enhancement solution")
    ax.set(xscale="log",yscale="log",xlabel=r"central proxy $\mathcal{R}_{\rm dyn}=g_{\rm obs}/g_N$",
           ylabel=r"required $a_M/a_{M0}$")
    ax.set_title("HRC-only UDG inverse-scale stress test"); ax.grid(True,which="both",alpha=.22)
    ax.legend(loc="upper center",bbox_to_anchor=(.5,-.18),ncol=2,
              columnspacing=1.1,handletextpad=.5)
    fig.subplots_adjust(left=.14,right=.97,top=.90,bottom=.27)
    save(fig,"R97_HRC_UDG_STRESS_typography_r149","HRC-only UDG inverse-scale stress test",
         "Presentation-only successor; frozen UDG rows and domain labels unchanged.")


def qubit() -> None:
    phi=np.logspace(-3,1.5,1000); v=np.exp(-phi)
    p=np.clip((1+v)/2,1e-15,1-1e-15); h=-(p*np.log(p)+(1-p)*np.log(1-p))
    info=2*h/np.log(2)
    fig,ax=plt.subplots(figsize=(7.2,5.0)); ax2=ax.twinx()
    ax.semilogx(phi,info,color=BLUE,lw=2,marker="o",markevery=100,label=r"total $I(S{:}E)$ in the pure-dilation toy")
    ax2.semilogx(phi,v,color=GREEN,ls="--",lw=1.8,marker="s",markevery=100,label=r"residual coherence $V=e^{-\Phi}$")
    ax.set(xlabel=r"pairwise dephasing parameter $\Phi$",ylabel=r"mutual information $I(S{:}E)$ [bits]",
           xlim=(1e-3,30),ylim=(0,2.12))
    ax2.set_ylabel(r"residual coherence $V$",color=GREEN); ax2.tick_params(axis="y",colors=GREEN); ax2.set_ylim(0,1.05)
    for x,label,y in [(.006,"visibility proxy",.12),(.062,"visibility proxy",.12),(np.log(np.sqrt(2)),"Werner toy marker",.38)]:
        ax.axvline(x,color=GREY,ls=":" if x<.1 else "--",lw=.9)
        ax.text(x*1.08,y,label,rotation=90,va="bottom",fontsize=11.2,color=GREY)
    ax.axvline(1,color=AMBER,ls="-.",lw=1)
    ax.text(1.08,1.12,r"$\Phi=1$: model marker, not boundary",rotation=90,va="bottom",fontsize=11.2,color=AMBER)
    l1,t1=ax.get_legend_handles_labels(); l2,t2=ax2.get_legend_handles_labels()
    ax.legend(l1+l2,t1+t2,loc="lower right"); ax.grid(True,which="both",color=".9",lw=.4)
    fig.tight_layout()
    save(fig,"fig_qubit_info_decoherence_typography_r149","Pure-dilation qubit information toy",
         "Presentation-only successor; arrays, proxy markers and status unchanged.")


def main() -> None:
    configure()
    for fn in (architecture,species,coupling,seesaw,neutrino_correction,
               timescale,chronology,rar,udg,qubit):
        fn()
    print(json.dumps({"outputs": sorted(p.name for p in OUT.glob("*"))}, indent=2))


if __name__ == "__main__":
    main()
