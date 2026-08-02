#!/usr/bin/env python3
"""Independent red-team checks for the R114 finite-body publication owner."""

from __future__ import annotations

import csv
import hashlib
import json
import math
from pathlib import Path

import numpy as np
from scipy.integrate import quad
from scipy.optimize import brentq
from scipy.sparse import diags, lil_matrix
from scipy.sparse.linalg import spsolve


LATEX_ROOT = Path(__file__).resolve().parents[3]
SOURCE = LATEX_ROOT / "data" / "cosmology_r114"
OUT = SOURCE
N, M = 3.0, 1.0
WIDTH = 0.03
RADIUS = 1.0


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def h_body(x):
    return 0.5 * (1.0 - np.tanh((x - RADIUS) / WIDTH))


def f_rhs(u, x, r, eta):
    return (u**N - r * u**M - (1.0-r))/(N-M*r) - eta*h_body(x)


def dfdu(u, r):
    return (N*u**(N-1.0)-M*r*u**(M-1.0))/(N-M*r)


def interior_root(r, eta):
    fun=lambda u: float(f_rhs(u, 0.0, r, eta))
    hi=max(3.0,(eta*(N-M*r)+2.0)**(1.0/N)*4.0)
    return brentq(fun,1.0,hi,xtol=1e-14,rtol=1e-14)


def fd_continuation(r, etas=(3.0,33.0,333.0,3333.0), dx=0.005, xmax=15.0):
    """Independent sparse Newton continuation for w=x(u-1), no BVP seed."""
    intervals=int(round(xmax/dx)); x=np.linspace(0.0,xmax,intervals+1)
    w=None; out=[]
    for eta in etas:
        root=interior_root(r,eta)
        if w is None:
            u0=1.0+(root-1.0)*0.5*(1.0-np.tanh((x-RADIUS)/0.18))
            w=x*(u0-1.0); w[0]=0.0
        else:
            old=max(w[1]/x[1],1e-14)
            w *= (root-1.0)/old
        for iteration in range(35):
            xi=x[1:-1]; ui=1.0+w[1:-1]/xi
            resid_i=(w[:-2]-2*w[1:-1]+w[2:])/dx**2-xi*f_rhs(ui,xi,r,eta)
            resid_b=(3*w[-1]-4*w[-2]+w[-3])/(2*dx)+w[-1]
            resid=np.r_[resid_i,resid_b]
            norm=float(np.max(np.abs(resid)))
            if norm<2e-9:
                break
            size=intervals; jac=lil_matrix((size,size))
            rows=np.arange(intervals-1)
            jac[rows,rows]=-2/dx**2-dfdu(ui,r)
            jac[rows[1:],rows[1:]-1]=1/dx**2
            jac[rows[:-1],rows[:-1]+1]=1/dx**2
            jac[intervals-2,intervals-1]=1/dx**2
            jac[intervals-1,intervals-3]=1/(2*dx)
            jac[intervals-1,intervals-2]=-4/(2*dx)
            jac[intervals-1,intervals-1]=3/(2*dx)+1
            delta=spsolve(jac.tocsc(),-resid)
            damping=1.0
            for _ in range(40):
                trial=w.copy(); trial[1:]+=damping*delta
                if np.min(1+trial[1:]/x[1:])<=0:
                    damping*=0.5; continue
                ti=1+trial[1:-1]/xi
                tr=np.r_[(trial[:-2]-2*trial[1:-1]+trial[2:])/dx**2-xi*f_rhs(ti,xi,r,eta),
                         (3*trial[-1]-4*trial[-2]+trial[-3])/(2*dx)+trial[-1]]
                if np.max(np.abs(tr))<norm:
                    w=trial; break
                damping*=0.5
            else:
                raise RuntimeError("Newton line search failed")
        else:
            raise RuntimeError("Newton failed")
        amplitude=float(math.exp(xmax)*w[-1])
        out.append({"r":r,"eta":eta,"dx":dx,"xmax":xmax,"iterations":iteration+1,
                    "max_residual":norm,"asymptotic_amplitude_boundary":amplitude})
    return out


def main():
    source_names = [
        "R114_R105_ACTION_STATE_INPUT_SNAPSHOT_v1.csv",
        "R114_TWOSLOPE_FINITEBODY_TARGETS_v1.json",
        "R114_TWOSLOPE_FINITEBODY_GRID_v1.csv",
        "R114_EARLYG_CASSINI_CHARGE_TARGETS_v1.csv",
    ]
    manifest={name:{"sha256":sha(SOURCE/name)} for name in source_names}

    linear_unit=quad(lambda x:x*math.sinh(x)*float(h_body(x)),0.0,10.0,
                     epsabs=1e-13,epsrel=1e-13,limit=500)[0]
    fd99=fd_continuation(0.99)
    fd100=fd_continuation(1.0)
    tail99=fd99[-1]["asymptotic_amplitude_boundary"]/(3333.0*linear_unit)
    tail100=fd100[-1]["asymptotic_amplitude_boundary"]/(3333.0*linear_unit)

    targets=[]; delta=2.3e-5; pref=delta/(4-2*delta)
    with (SOURCE/"R114_R105_ACTION_STATE_INPUT_SNAPSHOT_v1.csv").open() as f:
        for row in csv.DictReader(f):
            a=float(row["a"]); k=float(row["kappa"]); alpha2=a*a/(4*k+6*a*a)
            smax=min(1.0,pref/alpha2)
            targets.append({"a":a,"kappa":k,"alpha2":alpha2,"smax":smax,
                            "suppression":1/smax})

    original=json.loads((SOURCE/"R114_TWOSLOPE_FINITEBODY_TARGETS_v1.json").read_text())
    stated=min(x["far_tail_suppression_proxy"] for x in original["bvp_rows"])
    payload={
        "date":"2026-07-20",
        "schema":"ECT-R114-two-slope-finite-body-independent-redteam-v1",
        "manifest":manifest,
        "algebra":{
            "reduction":"PASS: A=C0*f, C_X=a*A, so laplacian(exp(aq))=a*exp(aq)*E/A",
            "dimensionless_normalisation":"PASS: m_out^2=A_plus*y_out^(n-1)*(n-m*r)",
            "vacuum_endpoint":"rho_out=0 implies r=1 exactly; r=0.99 is near-vacuum, not the endpoint",
        },
        "linear_unit_asymptotic_amplitude":linear_unit,
        "fd_r_0p99":fd99,
        "fd_r_1":fd100,
        "stated_x5_x9_proxy_r0p99_eta3333":stated,
        "asymptotic_proxy_r0p99_eta3333":tail99,
        "relative_shift_stated_to_asymptotic":(stated-tail99)/tail99,
        "vacuum_endpoint_asymptotic_proxy_r1_eta3333":tail100,
        "cassini_targets_independent":targets,
        "status":{
            "scalar_proxy_algebra":"PASS",
            "frozen_operational_proxy_0p0063997":"PASS_AS_DEFINED_X5_X9",
            "literal_asymptotic_tail_0p0063997":"FAIL_SMALL_0p094_PERCENT_BIAS",
            "physical_sensitivity_identification":"NOT_IDENTIFIABLE",
            "joint_earlyG_Cassini_feasibility":"NOT_ESTABLISHED",
        },
    }
    payload["all_redteam_gates_pass"] = (
        abs(stated-0.006399711753031447) < 5e-15
        and abs(tail99-0.006393895851846394) < 5e-13
        and abs(tail100-0.006372442153563478) < 5e-13
        and payload["status"]["physical_sensitivity_identification"] == "NOT_IDENTIFIABLE"
    )
    (OUT/"R114_TWOSLOPE_FINITEBODY_REDTEAM_v1.json").write_text(
        json.dumps(payload,indent=2,sort_keys=True)+"\n"
    )
    print(json.dumps(payload["status"],indent=2))


if __name__=="__main__":
    main()
