#!/usr/bin/env python3
"""Re-render active monochrome/partly monochrome R123 figures as vector PDFs.

The numerical arrays and graph topology are copied from the named live owner
scripts.  Only presentation changes: exact R123 palette, readable type,
line/marker/direct-label redundancy and removal of decorative hatch.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import platform
import sys

SCRIPT = Path(__file__).resolve()
COMPONENT = SCRIPT.parent.parent
R123 = SCRIPT.parents[3]
LATEX = SCRIPT.parents[6]
MPLCONFIG = COMPONENT / "qa" / "mplconfig"
MPLCONFIG.mkdir(parents=True, exist_ok=True)
os.environ.setdefault("MPLCONFIGDIR", str(MPLCONFIG))
os.environ.setdefault("SOURCE_DATE_EPOCH", "1784592000")

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
import numpy as np


PALETTE_PATH = R123 / "scripts" / "r123_palette.py"
spec = importlib.util.spec_from_file_location("r123_palette", PALETTE_PATH)
P = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = P
assert spec.loader is not None
spec.loader.exec_module(P)

PDF_META = {
    "Creator": "ECT R123 deterministic renderer",
    "Producer": "Matplotlib",
    "CreationDate": datetime(2026, 7, 21, tzinfo=timezone.utc),
    "ModDate": datetime(2026, 7, 21, tzinfo=timezone.utc),
}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def style() -> None:
    plt.rcParams.update(
        {
            "font.family": "DejaVu Serif",
            "font.size": 12,
            "axes.titlesize": 12.5,
            "axes.labelsize": 12,
            "xtick.labelsize": 10.5,
            "ytick.labelsize": 10.5,
            "legend.fontsize": 10.5,
            "mathtext.fontset": "cm",
            "axes.linewidth": 0.9,
            "pdf.fonttype": 42,
        }
    )


def save(fig, path: Path, title: str) -> None:
    fig.savefig(path, bbox_inches="tight", metadata={**PDF_META, "Title": title})
    plt.close(fig)


def scales(path: Path) -> dict:
    style()
    g_n, m_sun, kpc = 6.67430e-11, 1.98847e30, 3.0856775814913673e19
    a_m0, phi0, v2 = 1.0824013602e-10, 2.435e18, 246.22
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10.8, 5.2), constrained_layout=True)
    x = np.array([0.0, 1.0]); energies = np.array([phi0, v2])
    ax1.plot(x, energies, "--", color=P.GRAPHITE, lw=1.5, zorder=1)
    ax1.scatter([0], [phi0], s=105, color=P.LEVEL_A_EDGE, marker="o", zorder=3, label=r"$\phi_0$: structural scale")
    ax1.scatter([1], [v2], s=100, color=P.EXTERNAL_EDGE, marker="s", zorder=3, label=r"$v_2$: matched external scale")
    ax1.set_yscale("log"); ax1.set_xlim(-0.45, 1.45); ax1.set_ylim(1e1, 1e20)
    ax1.set_xticks(x, [r"$\phi_0$", r"$v_2$"]); ax1.set_ylabel("energy / matching scale [GeV]")
    ax1.set_title("(a) Energy-dimension inventory", loc="left", fontweight="bold")
    ax1.annotate(r"$\phi_0\simeq\bar M_{\rm Pl}$" + "\n" + r"$2.435\times10^{18}$ GeV", (0, phi0), xytext=(25, -8), textcoords="offset points", ha="left", va="top", arrowprops={"arrowstyle":"->","color":P.LEVEL_A_EDGE})
    ax1.annotate(r"$v_2=246.22$ GeV" + "\nmatched; origin Open", (1, v2), xytext=(-18, 28), textcoords="offset points", ha="right", va="bottom", arrowprops={"arrowstyle":"->","color":P.EXTERNAL_EDGE})
    ax1.text(0.5, 0.49, r"$\phi_0/v_2\simeq9.9\times10^{15}$" + "\nmechanism Open", transform=ax1.transAxes, ha="center", va="center", bbox={"boxstyle":"round,pad=0.35","fc":P.OPEN_FILL,"ec":P.OPEN_EDGE})
    ax1.grid(True, color=P.GRID, lw=0.7); ax1.legend(loc="lower left", frameon=True)

    masses = np.logspace(7, 12, 300); r_kpc = np.sqrt(g_n * masses * m_sun / a_m0) / kpc
    ax2.plot(masses, r_kpc, color=P.HRC0, lw=2.4, label="conditional HRC matching identity")
    m_ref = 1e10; r_ref = np.sqrt(g_n*m_ref*m_sun/a_m0)/kpc
    ax2.scatter([m_ref], [r_ref], s=95, color=P.NFW, marker="D", zorder=3, label="declared reference mass")
    ax2.set_xscale("log"); ax2.set_yscale("log")
    ax2.set_xlabel(r"baryonic mass $M_{\rm bar}$ [$M_\odot$]")
    ax2.set_ylabel(r"conditional HRC matching length $L_{\rm gal}=r_*$ [kpc]")
    ax2.set_title("(b) Conditional HRC matching length", loc="left", fontweight="bold")
    ax2.annotate(r"$M_{\rm bar}=10^{10}M_\odot$"+"\n"+rf"$r_*={r_ref:.1f}$ kpc", (m_ref,r_ref), xytext=(22,-27), textcoords="offset points", ha="left", va="top", arrowprops={"arrowstyle":"->","color":P.NFW})
    ax2.text(0.04,0.96,r"$r_*=\sqrt{G_NM_{\rm bar}/a_{M0}}$"+"\n"+r"$a_{M0}=1.0824\times10^{-10}$ m s$^{-2}$ (matched)", transform=ax2.transAxes,ha="left",va="top",bbox={"boxstyle":"round,pad=0.35","fc":P.LEVEL_C_FILL,"ec":P.LEVEL_C_EDGE})
    ax2.text(0.96,0.06,"No common GeV axis\nNo RG link claimed",transform=ax2.transAxes,ha="right",va="bottom",color=P.GRAPHITE)
    ax2.grid(True,color=P.GRID,lw=0.7); ax2.legend(loc="lower right", frameon=True)
    save(fig,path,"R123 dimensionally separated scale inventory")
    return {"phi0_GeV":phi0,"v2_GeV":v2,"a_M0":a_m0,"r_ref_kpc":r_ref,"points":300}


def species(path: Path) -> dict:
    style(); phi0=2.44e18
    groups=[("Leptons",[("$e$",0.000511),(r"$\mu$",0.1057),(r"$\tau$",1.777)],P.HRC0,"o"),("Hadrons",[("$p/n$",0.938)],P.HRC3,"s"),("Heavy quarks",[("$b$",4.18),("$t$",173.0)],P.MOND,"D")]
    fig,ax=plt.subplots(figsize=(8.2,5.0),constrained_layout=True); y=0; ticks=[]; labels=[]; vals=[]
    for name,particles,col,marker in groups:
        y0=y
        for label,mass in particles:
            value=np.log10(mass/phi0); vals.append(value)
            ax.barh(y,value,color=col,edgecolor=P.INK,height=0.58,zorder=2)
            ax.scatter([value],[y],marker=marker,s=46,color=P.PAPER,edgecolor=P.INK,zorder=3)
            ax.text(value+0.28,y,rf"$\sim10^{{{int(np.round(value))}}}$",va="center",ha="left",fontsize=10.2)
            ticks.append(y); labels.append(label); y+=1
        ax.text(-13.55,(y0+y-1)/2,name,ha="left",va="center",fontsize=9,fontstyle="italic",bbox={"boxstyle":"round,pad=0.2","fc":P.PAPER,"ec":col})
        y+=0.38
    ax.set_yticks(ticks,labels); ax.set_xlabel(r"$\log_{10}\beta_5^{\rm bench}$, $\beta_5^{\rm bench}=m_f/\phi_0$"+"\n(hand-selected ratio; not a derived microscopic coupling)")
    ax.set_xlim(-24,-13); ax.invert_xaxis(); ax.set_ylim(-0.5,y-0.2)
    ebase=np.log10(0.000511/phi0); ax.axvline(ebase,color=P.GRAPHITE,ls=":",lw=1.2)
    ax.text(ebase-0.12,y-0.28,"electron\nbenchmark",fontsize=8.2,ha="right",va="top",color=P.GRAPHITE)
    ax.set_title(r"Hand-selected species benchmark $\beta_5^{\rm bench}\sim m_f/\phi_0$ (Level C/Open)",fontweight="bold")
    ax.grid(axis="x",color=P.GRID,lw=0.7)
    save(fig,path,"R123 hand-selected species benchmark")
    return {"phi0_bench_GeV":phi0,"log10_values":vals}


def coupling(path: Path) -> dict:
    style(); labels=["Strong\n"+r"$\alpha_s$","EM\n"+r"$\alpha$","Gravity\n"+r"$G_Nm^2/\hbar c$","Unowned benchmark\n"+r"$\beta_5^{\rm bench}=m_f/\phi_0$"]
    ve=np.array([0,-2.14,-44.8,-22.3]); vp=np.array([0,-2.14,-38.2,-18.4]); x=np.arange(4)
    fig,ax=plt.subplots(figsize=(8.6,5.2),constrained_layout=True)
    ax.scatter(x-.12,ve,s=125,marker="o",color=P.HRC0,edgecolor=P.INK,label="electron scale",zorder=3)
    ax.scatter(x+.12,vp,s=125,marker="s",color=P.MOND,edgecolor=P.INK,label="proton scale",zorder=3)
    for i in range(4): ax.plot([x[i]-.12,x[i]+.12],[ve[i],vp[i]],color=P.GRAPHITE,lw=1.2,zorder=1)
    for i,(a,b) in enumerate(zip(ve,vp)):
        ax.text(x[i]-.12,a+(2 if a>-5 else -2.6),r"$\sim1$" if a>-5 else rf"$10^{{{int(round(a))}}}$",ha="center",fontsize=10.2,color=P.INK)
        if b<-5 and abs(b-a)>3: ax.text(x[i]+.12,b-2.6,rf"$10^{{{int(round(b))}}}$",ha="center",fontsize=10.2,color=P.INK)
    ax.set_xticks(x,labels); ax.set_ylabel(r"$\log_{10}$(characteristic dimensionless suppression)")
    ax.set_ylim(-52,8); ax.axhline(0,color=P.INK,lw=0.8); ax.grid(axis="y",color=P.GRID,lw=0.7)
    ax.legend(loc="lower right",frameon=True)
    ax.annotate(r"$\beta_5^{\rm bench}>\alpha_G$ numerically,"+"\nbut this hand-set benchmark is not\na derived force coupling",xy=(2.5,-31),ha="center",va="center",fontsize=10.2,bbox={"boxstyle":"round,pad=0.4","fc":P.OPEN_FILL,"ec":P.OPEN_EDGE})
    ax.set_title("Schematic comparison with a hand-selected C/Open benchmark\n(not identical force laws; not an ECT prediction)",fontweight="bold")
    save(fig,path,"R123 characteristic interaction-suppression comparison")
    return {"electron":ve.tolist(),"proton":vp.tolist()}


def neutrino(path: Path) -> dict:
    style(); egev=np.logspace(-2,6,500); eev=egev*1e9; dm2=2.5e-3; beta=2e-29
    standard=dm2/(2*eev); director=beta*eev
    fig,ax=plt.subplots(figsize=(8.0,5.2),constrained_layout=True)
    ax.loglog(egev,standard,color=P.EXTERNAL_EDGE,ls="--",marker="s",markevery=80,lw=2,label=r"imported $\Delta m^2_{\rm atm}/(2E)$")
    ax.loglog(egev,director,color=P.OPEN_EDGE,ls="-",marker="D",markevery=80,lw=2,label=r"optional $\beta_\nu^{\rm bench}E$")
    ax.axvspan(.1,100,color=P.EXTERNAL_FILL,zorder=-5,label="illustrative energy band")
    ax.text(.5,.04,r"$\kappa_\nu=1$ BENCHMARK ONLY — vertex/coefficient Open",transform=ax.transAxes,ha="center",va="bottom",fontsize=10.2,fontweight="bold",bbox={"boxstyle":"round,pad=0.35","fc":P.OPEN_FILL,"ec":P.OPEN_EDGE})
    ax.set_xlabel(r"Energy $E$ [GeV]"); ax.set_ylabel("Hamiltonian scale [eV]")
    ax.set_title("Optional preferred-direction diagnostic (not an ECT prediction)",fontweight="bold")
    ax.grid(True,which="both",color=P.GRID,lw=.7); ax.legend(loc="best")
    save(fig,path,"R123 optional neutrino-director diagnostic")
    return {"count":500,"dm2_atm_eV2":dm2,"beta_bench":beta,"standard_endpoints":[float(standard[0]),float(standard[-1])],"director_endpoints":[float(director[0]),float(director[-1])]}


def gamma(path: Path) -> dict:
    style(); phi=np.logspace(-3,1,500); retention=np.exp(-phi)
    fig,ax=plt.subplots(figsize=(8.6,5.0),constrained_layout=True)
    ax.set_xscale("log"); ax.plot(phi,retention,color=P.LEVEL_B_EDGE,ls="-",marker="o",markevery=65,lw=2.4,label="declared pure-dephasing closure: V/V0 = exp(-Phi)")
    for x,label,marker in [(.006,"Procopio visibility proxy","s"),(.062,"Jacques visibility proxy","D")]:
        ax.plot(x,np.exp(-x),marker,ms=8,color=P.DATA); ax.annotate(label,(x,np.exp(-x)),xytext=(8,-27),textcoords="offset points",fontsize=9,arrowprops={"arrowstyle":"->","color":P.GRAPHITE})
    ax.axvline(np.log(np.sqrt(2)),color=P.LEVEL_C_EDGE,ls="--",lw=1.4,label="Werner-visibility CHSH toy marker")
    ax.axvline(1.0,color=P.OPEN_EDGE,ls=":",lw=1.5,label="order-unity marker (not universal)")
    ax.set_xlabel("pairwise dephasing proxy Phi (for branch pair a,b)"); ax.set_ylabel("coherence retention V/V0")
    ax.set_ylim(0,1.05); ax.set_xlim(1e-3,10); ax.grid(True,which="both",color=P.GRID,lw=.7); ax.legend(loc="lower left")
    save(fig,path,"R123 visibility-only pairwise dephasing proxy")
    return {"count":500,"formula":"exp(-Phi)","proxy_x":[.006,.062],"toy_markers":[float(np.log(np.sqrt(2))),1.0]}


def qubit(path: Path) -> dict:
    style(); phi=np.logspace(-3,1.5,1000); vis=np.exp(-phi)
    p=np.clip((1+vis)/2,1e-15,1-1e-15); info=2*(-p*np.log(p)-(1-p)*np.log(1-p))/np.log(2)
    fig,ax1=plt.subplots(figsize=(8.0,5.1),constrained_layout=True)
    ax1.semilogx(phi,info,color=P.LEVEL_A_EDGE,ls="-",marker="o",markevery=110,lw=2.2,label=r"total $I(S{:}E)$ in the pure-dilation toy")
    ax1.set_xlabel(r"pairwise dephasing parameter $\Phi$"); ax1.set_ylabel(r"mutual information $I(S{:}E)$ [bits]"); ax1.set_xlim(1e-3,30); ax1.set_ylim(0,2.12)
    ax2=ax1.twinx(); ax2.semilogx(phi,vis,color=P.LEVEL_B_EDGE,ls="--",marker="s",markevery=110,lw=1.8,label="residual coherence V = exp(-Phi)"); ax2.set_ylabel(r"residual coherence $V$",color=P.LEVEL_B_EDGE); ax2.tick_params(axis="y",colors=P.LEVEL_B_EDGE); ax2.set_ylim(0,1.05)
    for x,label,ls,col in [(.006,"visibility proxy",":",P.EXTERNAL_EDGE),(.062,"visibility proxy",":",P.EXTERNAL_EDGE),(float(np.log(np.sqrt(2))),"Werner toy marker","--",P.LEVEL_C_EDGE),(1.0,r"$\Phi=1$: model marker, not boundary","-.",P.OPEN_EDGE)]:
        ax1.axvline(x,color=col,ls=ls,lw=1.0); ax1.text(x*1.08,.12 if x<.1 else (.38 if x<.8 else 1.05),label,rotation=90,va="bottom",fontsize=8.2,color=col)
    l1,a1=ax1.get_legend_handles_labels(); l2,a2=ax2.get_legend_handles_labels(); ax1.legend(l1+l2,a1+a2,loc="lower right")
    ax1.grid(True,which="both",color=P.GRID,lw=.6)
    save(fig,path,"R123 pure-dilation qubit toy")
    return {"count":1000,"info_endpoints":[float(info[0]),float(info[-1])],"visibility_endpoints":[float(vis[0]),float(vis[-1])]}


def box(ax,xy,w,h,title,body,fill,edge,status=None,dashed=False):
    x,y=xy; patch=FancyBboxPatch((x-w/2,y-h/2),w,h,boxstyle="round,pad=.018,rounding_size=.045",facecolor=fill,edgecolor=edge,linewidth=1.5,linestyle="--" if dashed else "-"); ax.add_patch(patch)
    ax.text(x,y+.16*h,title,ha="center",va="center",fontsize=10.2,fontweight="bold",color=P.INK)
    ax.text(x,y-.10*h,body,ha="center",va="center",fontsize=8.5,color=P.INK)
    if status: ax.text(x,y-.34*h,status,ha="center",va="center",fontsize=8.0,fontweight="bold",color=edge)


def ontology(path: Path) -> dict:
    style(); fig,ax=plt.subplots(figsize=(10.2,6.4),constrained_layout=True); ax.set_xlim(-5.5,5.5); ax.set_ylim(-5.6,2); ax.axis("off")
    box(ax,(0,1),4.0,1.0,"Full condensate candidate description","interacting OS/unitarity completion",P.OPEN_FILL,P.OPEN_EDGE,"OPEN")
    box(ax,(0,-.75),4.2,1.0,"Declared resolved/unresolved split","physical vertices + state + protocol required",P.EXTERNAL_FILL,P.EXTERNAL_EDGE,"SUPPLIED SPLIT")
    box(ax,(-3.0,-2.65),3.2,1.1,"Coherence-retaining channel","small Phi(a,b) for declared comparisons",P.LEVEL_B_FILL,P.LEVEL_B_EDGE,"CONDITIONAL")
    box(ax,(1.0,-2.65),3.2,1.1,"Record-forming channel","large Phi(a,b) for declared comparisons",P.LEVEL_B_FILL,P.LEVEL_B_EDGE,"CONDITIONAL")
    box(ax,(4.15,-2.65),2.45,1.1,"Gravity-mediator / GIE","own vertex and channel required",P.OPEN_FILL,P.OPEN_EDGE,"OPEN",True)
    box(ax,(-.75,-4.7),4.4,1.0,"No universal transition","no metric-signature or ontology jump from Phi(a,b)",P.TENSION_FILL,P.TENSION_EDGE,"NO-GO GUARD")
    box(ax,(3.25,-4.7),2.65,1.0,"Unique outcome / update","OP-Q19",P.OPEN_FILL,P.OPEN_EDGE,"OPEN",True)
    edges=[((0,.48),(0,-.23),"-"),((0,-1.27),(-3,-2.08),"-"),((0,-1.27),(1,-2.08),"-"),((0,-1.27),(4.15,-2.08),"--"),((-3,-3.22),(-.75,-4.18),"-"),((1,-3.22),(-.75,-4.18),"-"),((1,-3.22),(3.25,-4.18),"--")]
    for a,b,ls in edges: ax.annotate("",xy=b,xytext=a,arrowprops={"arrowstyle":"-|>","linestyle":ls,"linewidth":1.2,"color":P.INK})
    ax.set_title("Status-guarded full/reduced-description map",fontweight="bold")
    save(fig,path,"R123 status-guarded full/reduced ontology map")
    return {"nodes":7,"edges":7,"topology_preserved":True}


def qm_compare(path: Path) -> dict:
    style(); fig,ax=plt.subplots(figsize=(10.8,7.0),constrained_layout=True); ax.set_xlim(0,10); ax.set_ylim(0,10.4); ax.axis("off")
    box(ax,(2.55,9.7),4.4,.75,"Standard quantum mechanics","external comparison column",P.EXTERNAL_FILL,P.EXTERNAL_EDGE,"EXTERNAL")
    box(ax,(7.45,9.7),4.4,.75,"Euclidean Condensate Theory","status-sensitive programme column",P.LEVEL_B_FILL,P.LEVEL_B_EDGE,"MIXED STATUS")
    left=[("Cauchy initial-value problem","wavefunction at initial time given; evolve forward"),(r"$i\hbar\,\partial_t\psi=H\psi$","Schrödinger / Dirac equation"),(r"$|\psi|^2$: Born rule","fundamental axiom"),("Time: fundamental coordinate","Lorentzian spacetime a priori"),("Measurement / update rule","textbook formulations; interpretations differ")]
    right=[("Specified BVP / ensemble","existence / uniqueness / selection Open",P.OPEN_FILL,P.OPEN_EDGE,"OPEN"),(r"$\delta^{AB}\partial_A\partial_B\Phi-V'(\Phi)=0$","Euclidean condensate equation",P.LEVEL_A_FILL,P.LEVEL_A_EDGE,"MODEL-INTERNAL"),("Born probability / physical weights","Gleason represents a supplied measure; reconstruction/outcome Open",P.OPEN_FILL,P.OPEN_EDGE,"OPEN"),("P4 supplies an ordered direction","scalar signature needs supplied coefficients; cones Open",P.LEVEL_B_FILL,P.LEVEL_B_EDGE,"CONDITIONAL"),("Measurement / outcome map","decoherence alone does not select outcome",P.OPEN_FILL,P.OPEN_EDGE,"OPEN")]
    ys=[8.45,6.85,5.25,3.65,2.05]
    for y,(title,body) in zip(ys,left): box(ax,(2.55,y),4.4,1.15,title,body,P.EXTERNAL_FILL,P.EXTERNAL_EDGE,"EXTERNAL")
    for y,(title,body,fill,edge,status) in zip(ys,right): box(ax,(7.45,y),4.4,1.15,title,body,fill,edge,status)
    ax.plot([5,5],[1.35,9.15],color=P.GRID,ls="--",lw=1)
    ax.text(5,.65,"Colours encode scientific status; every status is also written explicitly.",ha="center",fontsize=8.5,color=P.GRAPHITE)
    save(fig,path,"R123 status-sensitive ECT versus standard-QM comparison")
    return {"rows":5,"scientific_text_preserved":True,"status_mapping_added":True}


BUILDERS={
    "fig_condensate_scales_r123.pdf":scales,
    "fig_species_beta5_r123.pdf":species,
    "fig_coupling_comparison_r123.pdf":coupling,
    "fig_neutrino_corrections_r123.pdf":neutrino,
    "fig_gamma_crossover_r123.pdf":gamma,
    "fig_qubit_info_decoherence_r123.pdf":qubit,
    "fig_two_level_ontology_r123.pdf":ontology,
    "fig_ect_vs_qm_r123.pdf":qm_compare,
}

OWNER_PATHS = {
    "fig_condensate_scales_r123.pdf": [LATEX / "scripts" / "fig3_condensate_scales.py"],
    "fig_species_beta5_r123.pdf": [LATEX / "scripts" / "gen_fig_species.py"],
    "fig_coupling_comparison_r123.pdf": [LATEX / "scripts" / "gen_fig_comparison.py"],
    "fig_neutrino_corrections_r123.pdf": [LATEX / "scripts" / "fig_neutrino_corrections.py"],
    "fig_gamma_crossover_r123.pdf": [LATEX / "scripts" / "fig_gamma_crossover.py"],
    "fig_qubit_info_decoherence_r123.pdf": [LATEX / "scripts" / "fig_qubit_info_decoherence.py"],
    "fig_two_level_ontology_r123.pdf": [LATEX / "scripts" / "fig_two_level_ontology.gv"],
    "fig_ect_vs_qm_r123.pdf": [LATEX / "scripts" / "render_fig_ect_vs_qm.py", LATEX / "figures" / "source" / "svg" / "fig_ect_vs_qm.svg"],
}


def main() -> int:
    ap=argparse.ArgumentParser(); ap.add_argument("--output",type=Path,default=COMPONENT/"assets"/"monochrome_remediation"); args=ap.parse_args(); args.output.mkdir(parents=True,exist_ok=True)
    payload={}; outputs={}
    for name,builder in BUILDERS.items():
        p=args.output/name; payload[name]=builder(p); outputs[name]=sha256(p)
    owners = {
        name: [{"path": str(path.relative_to(LATEX)), "sha256": sha256(path)} for path in OWNER_PATHS[name]]
        for name in sorted(OWNER_PATHS)
    }
    manifest={"schema":"ECT-R123-monochrome-remediation-v1","status":"PROPOSAL ONLY - LIVE APPLY NOT AUTHORISED","palette_owner":str(PALETTE_PATH),"owners":owners,"outputs":outputs,"scientific_payload":payload,"runtime":{"python":platform.python_version(),"matplotlib":matplotlib.__version__,"numpy":np.__version__}}
    (args.output/"R123_MONOCHROME_REMEDIATION_MANIFEST_v1.json").write_text(json.dumps(manifest,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps(outputs,indent=2,sort_keys=True)); return 0


if __name__=="__main__": raise SystemExit(main())
