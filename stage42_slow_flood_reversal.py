#!/usr/bin/env python3
"""Stage42 — test the previously unsearched slow flood-reversal regime.

Stage40 established that bidirectional hydroperiod ecology removes the hidden
near-linear year trend, but its smallest *interior* r_flood was 0.1 /yr. That
can be much faster than vegetation recovery/reversal reported for wetland
trajectories, which may unfold over years to decades. Stage42 changes no gate
and no process equation: it only expands the guarded r_flood grid downward,
while retaining Stage38 exact hydrology and Stage40 nested validation.

2022 remains sealed unless the full strict + nested gate passes.
"""
import json, shutil
from pathlib import Path
import stage40_bidirectional_hydroperiod as s40

OUT=Path('stage42_outputs');OUT.mkdir(exist_ok=True)
# Guard values surround every acceptable candidate; no accepted edge value.
GRIDS={
 'V0':[1000.,1600.,2200.],
 'p_shape':[6.,12.,18.],
 'tau_surf':[60.,120.,240.],
 'local_frac':[.15,.30,.45],
 'tau_fast':[30.,60.,120.],
 'k_gw_mm_d':[.02,.05,.10,.25,1.,2.,4.],
 'r_est_yr':[.01,.025,.05,.10,.25,.50],
 # Stage40 interior minimum was 0.1/yr. Stage42 resolves slow recovery.
 'r_flood_yr':[.0002,.001,.0025,.005,.01,.025,.05,.10,.25],
 'hydro_window_d':[7,14,30,60,90],
}

def relabel_summary():
    src=OUT/'stage40_summary.json'
    if not src.exists(): return
    d=json.loads(src.read_text(encoding='utf-8'))
    d['model']='Stage42 slow flood-reversal bidirectional hydroperiod ecology'
    d['stage42_change']='r_flood guard expanded downward only; equations and all acceptance gates unchanged'
    d['holdout_2022_used']=False
    (OUT/'stage42_summary.json').write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf-8')
    csv=OUT/'stage40_rejection_diagnostics.csv'
    if csv.exists(): shutil.copy2(csv,OUT/'stage42_rejection_diagnostics.csv')


def main():
    s40.GRIDS=GRIDS
    s40.OUT=OUT
    code=None
    try:
        s40.main()
    except SystemExit as e:
        code=e
    finally:
        relabel_summary()
    if code is not None: raise code

if __name__=='__main__': main()
