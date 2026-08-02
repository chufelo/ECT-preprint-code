#!/usr/bin/env python3
"""Build four R149 presentation-only typography successors.

This proposal-only builder redraws four panels from their identified frozen
owners.  It changes neither arrays, curves, selected values, nor literal
scientific status.  The change is confined to typographic scale, page geometry
and redundant (colour + line/marker/direct-text) accessibility treatment.

It deliberately does not write into LaTex/figures or edit any TeX source.
"""
from __future__ import annotations

import csv
import hashlib
import json
import os
from pathlib import Path

os.environ.setdefault("MPLCONFIGDIR", str(Path(__file__).resolve().parent / "qa" / "mplconfig"))
os.environ.setdefault("XDG_CACHE_HOME", str(Path(__file__).resolve().parent / "qa" / "cache"))

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image

ROOT = next(parent for parent in Path(__file__).resolve().parents if (parent / "ECT_preprint.tex").is_file())
OUT = Path(__file__).resolve().parent
ASSETS = OUT / "assets"
QA = OUT / "qa"

# Calm, luminance-separated Okabe--Ito-derived role palette.
BLUE, GREEN, ORANGE, VERMILION = "#0072B2", "#009E73", "#C57A00", "#B3451F"
GRAPHITE, GREY = "#252525", "#666666"
PALE_BLUE, PALE_GREEN, PALE_ORANGE, PALE_GREY = "#D9EAF5", "#DDEFE5", "#F4E3C2", "#EBEBEB"

INPUTS = {
    "one_pole_json": (
        ROOT / "data/cosmology_r113/R113_ONE_POLE_CLUSTER_NO_GO_v2.json",
        "d0cbf68192cc26629b9ec92a561b0b999888b6fd5dc518c5648e6cbbbc86fff0",
    ),
    "r103_hwg_csv": (
        ROOT / "data/cosmology_r103/R103_TWO_SLOPE_HWG_FROZEN_v1.csv",
        "fe7d5c9b4aca42ff7e552e38eef96284efcdc89cdd9066d63b8f5bfe6c4acd8e",
    ),
    "m1_payload": (
        ROOT / "provenance/figures/r190/research_derivations/pes_usage/gpt/R120_PUBLIC_RELEASE_CLOSURE_CANDIDATE_v1/m1_final/M1_PUBLIC_PROTOCOL_PAYLOAD_v2.json",
        "ee4224bcd850ce243661dc2dbcca3b473a3df3dc37a288fed7ab2ca009a05a97",
    ),
    "r114_closure_owner": (
        ROOT / "scripts/figures/make_r114_closure_figures.py",
        "2112dd42d156e32a4651302b8791f87b6a3a6c4392ee54315a018175609721b5",
    ),
    "r103_visual_owner": (
        ROOT / "scripts/figures/make_r103_restored_visuals.py",
        "cf56ba45ca6da910782303ea15058ed378846392e58dfa1e75e790d6d29cef26",
    ),
    "r114_m1_kernel": (
        ROOT / "scripts/figures/make_r114_pes_m1_fdt_figure_v2.py",
        "5cf03a9b248983c055162b01451d7b13466504a1c571dcead48b638b0d491d76",
    ),
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require_inputs() -> dict[str, str]:
    actual = {}
    for name, (path, expected) in INPUTS.items():
        digest = sha256(path) if path.is_file() else "MISSING"
        if digest != expected:
            raise RuntimeError(f"input lock failed for {name}: {digest} != {expected}")
        actual[name] = digest
    return actual


def configure() -> None:
    os.environ.setdefault("SOURCE_DATE_EPOCH", "1784918400")
    plt.rcParams.update({
        "font.family": "DejaVu Sans", "font.size": 10.5,
        "axes.titlesize": 12.2, "axes.labelsize": 11.0,
        "xtick.labelsize": 9.8, "ytick.labelsize": 9.8,
        "legend.fontsize": 9.0, "axes.edgecolor": GRAPHITE,
        "axes.linewidth": 0.85, "axes.grid": True,
        "grid.color": "#D5D8DA", "grid.linewidth": 0.52,
        "grid.alpha": 0.9, "pdf.fonttype": 42, "ps.fonttype": 42,
        "savefig.facecolor": "white", "text.color": GRAPHITE,
    })


def metadata(title: str) -> dict[str, str]:
    return {"Title": title, "Author": "ECT reproducibility workflow",
            "Subject": "R149 presentation-only typography successor; scientific payload unchanged",
            "Creator": "R149 second-half typography successor builder"}


def save(fig: plt.Figure, stem: str, title: str) -> None:
    ASSETS.mkdir(parents=True, exist_ok=True)
    fig.savefig(ASSETS / f"{stem}.pdf", metadata=metadata(title))
    fig.savefig(ASSETS / f"{stem}.png", dpi=240, metadata={"Software": "R149 typography successor"})
    plt.close(fig)


def previews(stem: str) -> list[Path]:
    QA.mkdir(parents=True, exist_ok=True)
    source = Image.open(ASSETS / f"{stem}.png").convert("RGB")
    outputs = []
    for name, image in (("colour", source), ("gray", source.convert("L").convert("RGB"))):
        p = QA / f"{stem}_{name}.png"; image.save(p); outputs.append(p)
    # Standard Machado matrices; direct labels/markers remain redundant cues.
    matrices = {
        "protan": np.array([[0.152286,1.052583,-.204868],[.114503,.786281,.099216],[-.003882,-.048116,1.051998]]),
        "deutan": np.array([[.367322,.860646,-.227968],[.280085,.672501,.047413],[-.011820,.042940,.968881]]),
        "tritan": np.array([[1.255528,-.076749,-.178779],[-.078411,.930809,.147602],[.004733,.691367,.303900]]),
    }
    a = np.asarray(source, dtype=float)/255.0
    linear = np.where(a <= .04045, a/12.92, ((a+.055)/1.055)**2.4)
    for name, matrix in matrices.items():
        b = np.einsum("...j,ij->...i", linear, matrix)
        srgb = np.where(b <= .0031308, 12.92*b, 1.055*np.power(np.clip(b,0,None),1/2.4)-.055)
        p = QA / f"{stem}_{name}.png"; Image.fromarray(np.uint8(np.rint(np.clip(srgb,0,1)*255))).save(p); outputs.append(p)
    return outputs


def one_pole() -> None:
    data = json.loads(INPUTS["one_pole_json"][0].read_text())
    distances = sorted((float(k.removeprefix("v=")), 1000*float(v)) for k,v in data["ballistic_transport_at_H0_70_Mpc"].items())
    speeds, distance = np.array(distances).T
    fig, ax = plt.subplots(figsize=(6.5, 4.55))
    # Reserve a genuine footer band.  A visually distinct status sentence
    # must never collide with the x-axis merely because the PDF parses.
    fig.subplots_adjust(left=.13, right=.98, bottom=.20, top=.80)
    ax.axhspan(70,100, facecolor=PALE_BLUE, edgecolor=BLUE, linewidth=.9, label="70--100 kpc target offset")
    ax.text(speeds.max()-12, 84, "observed-offset scale", ha="right", va="center", color="#285A78", weight="bold", fontsize=9.3)
    ax.plot(speeds, distance, color=VERMILION, ls="-.", marker="x", ms=8.4, mew=1.8, lw=2.0, label="v τaM at H0 = 70")
    ax.set_yscale("log"); ax.set(xlabel="speed [km s⁻¹]", ylabel="distance [kpc]", title="Ballistic-distance mismatch")
    # Log-scale exponents are rendered as smaller superscripts.  This explicit
    # size keeps the *visible* exponent at the project minimum of 8.5 pt.
    ax.tick_params(axis="both", labelsize=12.5)
    ax.legend(loc="center left", fontsize=9.3)
    ax.text(.975,.60, "mismatch 2.02×10³–3.85×10³\nrestricted to one real pole + ballistic transport", transform=ax.transAxes, ha="right", va="center", fontsize=9.3, bbox={"boxstyle":"round,pad=.28", "facecolor":"white", "edgecolor":GREY,"linewidth":.75})
    fig.suptitle("One-real-pole cluster-scale test", fontsize=13.0, weight="bold")
    fig.text(.5,.052,"Conditional no-go for the named one-real-pole + ballistic model. General causal kernels remain Open.",ha="center",fontsize=9.2,color=GREY)
    save(fig,"fig11_b_ballistic_distance_mismatch_r149","One-real-pole cluster-scale test: ballistic-distance mismatch")


def orientation() -> None:
    fig, ax = plt.subplots(figsize=(6.5, 5.15)); ax.set(xlim=(0,10),ylim=(0,10)); ax.axis("off")
    ax.text(5,9.55,"Orientation stiffness: established and conditional upstream chain",ha="center",fontsize=12.3,weight="bold")
    ax.text(5,9.15,"Every status is literal; colour is redundant with border style and wording.",ha="center",fontsize=9.2,color=GREY)
    def box(y,title,body,face,edge,ls):
        p=plt.matplotlib.patches.FancyBboxPatch((.8,y),8.4,1.28,boxstyle="round,pad=.04,rounding_size=.12",facecolor=face,edgecolor=edge,linewidth=1.75,linestyle=ls)
        ax.add_patch(p); ax.text(5,y+.86,title,ha="center",va="center",fontsize=11.2,weight="bold"); ax.text(5,y+.43,body,ha="center",va="center",fontsize=9.6)
    box(6.65,"Ordered variables","∂A Φ = u nA; P4 kinematics -- Level A",PALE_BLUE,BLUE,"-")
    ax.annotate("background reduction",xy=(5,5.98),xytext=(5,6.45),ha="center",va="center",fontsize=9.5,arrowprops={"arrowstyle":"-|>","color":BLUE,"lw":1.5})
    box(4.50,"Heavy-radial determinant","½ Tr ln Oσ; NLO -- CONDITIONAL declared closure",PALE_GREEN,GREEN,"--")
    ax.annotate("operator basis",xy=(5,3.83),xytext=(5,4.30),ha="center",va="center",fontsize=9.5,arrowprops={"arrowstyle":"-|>","color":GREEN,"lw":1.5,"linestyle":"--"})
    box(2.35,"Orientation coefficient Cₙ","Cₙ = âeff/(16π²mσ²) -- CONDITIONAL; matching Open",PALE_GREEN,GREEN,"--")
    handles=[plt.matplotlib.patches.Patch(facecolor=PALE_BLUE,edgecolor=BLUE,label="Level A definition / kinematics"),plt.matplotlib.patches.Patch(facecolor=PALE_GREEN,edgecolor=GREEN,linestyle="--",label="conditional under declared assumptions")]
    ax.legend(handles=handles,ncol=1,loc="lower center",frameon=False,fontsize=8.7,bbox_to_anchor=(.5,.02))
    fig.subplots_adjust(.04,.03,.96,.97)
    save(fig,"fig41_a_orientation_stiffness_upstream_r149","Orientation stiffness upstream chain")


def two_slope() -> None:
    with INPUTS["r103_hwg_csv"][0].open(newline="",encoding="utf-8") as f: rows=list(csv.DictReader(f))
    x=np.log1p(np.array([float(r["z"]) for r in rows])); ctl=np.array([float(r["w_eff_reference"]) for r in rows]); ts=np.array([float(r["w_eff_two_slope"]) for r in rows])
    fig,ax=plt.subplots(figsize=(6.5,4.55))
    fig.subplots_adjust(left=.13, right=.98, bottom=.20, top=.80)
    ax.plot(x,ctl,color=GRAPHITE,marker="s",ls="--",lw=1.55,ms=6.3,label="matched control")
    ax.plot(x,ts,color=GREEN,marker="^",markerfacecolor="white",markeredgewidth=1.55,ls="-.",lw=2.0,ms=7.2,label="two-slope")
    ax.set(xlabel="ln(1 + z)",ylabel="w_eff = −1 − 2H′/(3H)",title="(b) Total kinematic w_eff")
    ax.legend(loc="lower right"); ax.text(.03,.93,"curves overlap at this scale",transform=ax.transAxes,fontsize=9.2,va="top")
    fig.suptitle("Conditional total kinematic equation of state",fontsize=13,weight="bold")
    fig.text(.5,.052,"Conditional supplied two-slope state; no common-ε law. This is total kinematic w_eff.",ha="center",fontsize=9.3,color=GREY)
    save(fig,"fig43_b_two_slope_w_r149","Conditional total kinematic equation of state")


def m1() -> None:
    payload=json.loads(INPUTS["m1_payload"][0].read_text())["figure_payload"]
    assert payload["status"]=="PASS" and "no ECT prediction" in payload["classification"]
    def xy(rows,key): return np.array([float(r["omega"]) for r in rows]),np.array([float(r[key]) for r in rows])
    two=payload["non_equilibrium_two_bath_counterexample"]["rows"]; occ=payload["nonthermal_occupation_bump_counterexample"]["rows"]; fil=payload["filter_guard"]["rows"]; temp=float(payload["thermal_oscillator_benchmark"]["input_temperature"])
    x1,y1=xy(two,"T_eff"); x2,y2=xy(occ,"T_eff"); x3,y3=xy(fil,"T_eff_mismatched_filters")
    fig,ax=plt.subplots(figsize=(6.5,4.55))
    fig.subplots_adjust(left=.13, right=.98, bottom=.20, top=.80)
    ax.plot(x1,y1,color=ORANGE,lw=2.0,ls="--",marker="D",ms=6,markeredgecolor=GRAPHITE,label="two thermal baths")
    ax.plot(x2,y2,color=VERMILION,lw=2.0,ls="-.",marker="x",ms=8,mew=1.7,label="nonthermal occupation")
    ax.plot(x3,y3,color=GREY,lw=2.0,ls=":",marker="s",ms=5.6,markerfacecolor="white",markeredgecolor=GRAPHITE,label="mismatched filters")
    ax.axhline(temp,color=GRAPHITE,lw=1.0,ls="--",label="input temperature")
    ax.set(xlabel="angular frequency ω [synthetic units]",ylabel="apparent Teff [synthetic energy units]",title="Ordinary non-KMS or protocol counterexamples",ylim=(3.7,15.7))
    ax.text(.03,.96,"finite-window/bin data:\nforward model required",transform=ax.transAxes,fontsize=8.7,va="top",bbox={"boxstyle":"round,pad=.25","facecolor":PALE_BLUE,"edgecolor":"#285A78","linewidth":.7})
    ax.legend(loc="lower left",ncol=2,fontsize=9.0)
    fig.suptitle("M1 same-channel FDT protocol",fontsize=13,weight="bold")
    fig.text(.5,.052,"Ordinary non-KMS/protocol counterexamples; mismatch is not by itself ECT evidence.",ha="center",fontsize=9.1,color=GREY)
    save(fig,"fig47_b_counterexamples_r149","M1 same-channel FDT protocol: counterexamples")


def main() -> None:
    locks=require_inputs(); configure(); one_pole(); orientation(); two_slope(); m1()
    preview_files=[]
    for stem in ("fig11_b_ballistic_distance_mismatch_r149","fig41_a_orientation_stiffness_upstream_r149","fig43_b_two_slope_w_r149","fig47_b_counterexamples_r149"):
        preview_files.extend(previews(stem))
    # The contact sheet is a deterministic review aid, not a scientific asset.
    from make_contact_sheet import main as make_contact_sheet
    make_contact_sheet()
    contact = QA / "R149_SECOND_HALF_TYPOGRAPHY_CONTACT_SHEET.png"
    manifest={"schema":"r149-second-half-typography-successors/v1","scientific_change":"none","input_hashes":locks,"outputs":{p.name:sha256(p) for p in sorted(ASSETS.glob("*"))},"previews":{p.name:sha256(p) for p in sorted(preview_files)},"review_contact_sheet":{contact.name:sha256(contact)}}
    (OUT/"R149_SECOND_HALF_TYPOGRAPHY_MANIFEST_v1.json").write_text(json.dumps(manifest,indent=2,sort_keys=True)+"\n")

if __name__=="__main__": main()
