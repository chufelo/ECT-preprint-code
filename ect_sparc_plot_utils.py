#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Common utilities for ECT SPARC plots."""
from __future__ import annotations
import math, os
from pathlib import Path
from typing import Sequence
import numpy as np
import pandas as pd

G_SI   = 6.67430e-11
C_SI   = 299792458.0
KPC    = 3.085677581491367e19
MSUN   = 1.98847e30
KM     = 1000.0
DEFAULT_H0_KM_S_MPC = 70.0
A0_MOND = 1.2e-10

def normalize_name(name):
    return str(name).replace(" ","").replace("-","").upper()

def pick_col(df, candidates):
    cols_norm = {normalize_name(c): c for c in df.columns}
    for cand in candidates:
        key = normalize_name(cand)
        if key in cols_norm:
            return cols_norm[key]
    raise KeyError(f"None of {candidates} found")

def weighted_mean(values, errors):
    v,e = np.asarray(values,float), np.asarray(errors,float)
    mask = np.isfinite(v)&np.isfinite(e)&(e>0)
    if mask.sum()==0: return np.nan, np.nan
    w = 1/e[mask]**2
    mu = np.sum(w*v[mask])/np.sum(w)
    return mu, math.sqrt(1/np.sum(w))

def h0_si(h0=DEFAULT_H0_KM_S_MPC):
    return h0*1000/(3.085677581491367e22)

def gdag0_cH0_over_2pi(h0=DEFAULT_H0_KM_S_MPC):
    return C_SI*h0_si(h0)/(2*math.pi)

def load_sparc_mrt(path):
    rows=[]
    with open(path,'r',encoding='utf-8',errors='ignore') as f:
        for line in f:
            s=line.strip()
            if not s or s.startswith('#') or s.startswith('\\') or s.startswith('|'):
                continue
            parts=s.split()
            if len(parts)<10: continue
            galaxy=parts[0]
            try:
                R_kpc=float(parts[4]); Vobs=float(parts[5]); eV=float(parts[6])
                Vgas=float(parts[7]); Vdisk=float(parts[8]); Vbul=float(parts[9])
            except: continue
            rows.append({'galaxy':galaxy,'galaxy_norm':normalize_name(galaxy),
                         'R_kpc':R_kpc,'Vobs_kms':Vobs,'e_Vobs_kms':eV,
                         'Vgas_kms':Vgas,'Vdisk_kms':Vdisk,'Vbul_kms':Vbul})
    df=pd.DataFrame(rows)
    if df.empty: raise RuntimeError(f"No rows parsed from {path}")
    return df

def load_fit_results(path):
    df=pd.read_csv(path)
    df['galaxy_norm']=df[pick_col(df,['galaxy','name'])].map(normalize_name)
    return df

def get_result_row(results_df, galaxy):
    g=normalize_name(galaxy)
    sub=results_df.loc[results_df['galaxy_norm']==g]
    if len(sub)==0: raise KeyError(f"{galaxy} not found")
    return sub.iloc[0]

def baryonic_v2_kms2(Vgas,Vdisk,Vbul,ml_disk,ml_bul):
    return np.asarray(Vgas)**2 + ml_disk*np.asarray(Vdisk)**2 + ml_bul*np.asarray(Vbul)**2

def g_from_v2_and_R(v2_kms2,R_kpc):
    return np.asarray(v2_kms2)*KM**2 / (np.asarray(R_kpc)*KPC)

def gobs_from_Vobs(Vobs_kms,R_kpc):
    return g_from_v2_and_R(np.asarray(Vobs_kms)**2, R_kpc)

def ect_g_from_gbar(gbar, gdag):
    gbar=np.asarray(gbar,float)
    return 0.5*(gbar+np.sqrt(gbar**2+4*gbar*gdag))

def mond_g_from_gbar(gbar, a0=A0_MOND):
    gbar=np.asarray(gbar,float)
    return 0.5*(gbar+np.sqrt(gbar**2+4*gbar*a0))

def velocity_from_g(R_kpc, g_si):
    return np.sqrt(np.asarray(g_si)*np.asarray(R_kpc)*KPC)/KM

def estimate_tail_velocity(R_kpc,Vobs_kms,eV_kms,tail_fraction=0.25,min_points=3):
    R,V,eV=np.asarray(R_kpc,float),np.asarray(Vobs_kms,float),np.asarray(eV_kms,float)
    mask=np.isfinite(R)&np.isfinite(V)&np.isfinite(eV)
    R,V,eV=R[mask],V[mask],eV[mask]
    if len(R)<min_points: return np.nan,np.nan,np.zeros(len(R),bool)
    idx=np.argsort(R); R,V,eV=R[idx],V[idx],eV[idx]
    n_tail=max(min_points,int(math.ceil(tail_fraction*len(R))))
    tail_mask=np.zeros(len(R),bool); tail_mask[-n_tail:]=True
    vflat,evflat=weighted_mean(V[tail_mask],np.maximum(eV[tail_mask],1.0))
    return vflat,evflat,tail_mask

def estimate_outer_effective_baryonic_mass(R_kpc,gbar_si,tail_mask):
    R,gbar=np.asarray(R_kpc,float),np.asarray(gbar_si,float)
    if not tail_mask.any(): return np.nan
    R_tail=np.nanmedian(R[tail_mask])*KPC
    g_tail=np.nanmedian(gbar[tail_mask])
    return (R_tail**2*g_tail)/G_SI/MSUN

def get_fixed_ml_gdag_si(row):
    for key in ['gdag_fixed_si','gdag_fixed_m_s2','gdag_fit_fixed_si','gdag_fit_m_s2','gdag_fit_si']:
        if key in row.index and pd.notna(row[key]): return float(row[key])
    raise KeyError("Cannot find fixed-ML gdag")

def get_free_ml_gdag_si(row):
    for key in ['gdag_free_si','gdag_free_m_s2','gdag_fit_free_si']:
        if key in row.index and pd.notna(row[key]): return float(row[key])
    return np.nan

def get_ml_disk_fixed(row,default=0.5):
    for key in ['ml_fixed','ml_disk_fixed','ups_disk_fixed']:
        if key in row.index and pd.notna(row[key]): return float(row[key])
    return default

def get_ml_disk_free(row,default=0.5):
    for key in ['ml_free','ml_disk_free','ml_disk_best','ups_disk_best','ml_mond']:
        if key in row.index and pd.notna(row[key]): return float(row[key])
    return default

def get_clean_flag(row):
    if 'clean' in row.index: return bool(row['clean'])
    if 'flag_low_quality' in row.index: return not bool(row['flag_low_quality'])
    return True

def apply_bw_matplotlib_style(plt):
    plt.rcParams.update({'font.size':11,'axes.grid':True,'grid.alpha':0.20,
        'grid.linestyle':'-','figure.facecolor':'white','axes.facecolor':'white',
        'savefig.facecolor':'white'})
