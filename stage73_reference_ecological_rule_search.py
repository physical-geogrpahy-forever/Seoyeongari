#!/usr/bin/env python3
"""Stage73 — literature-bounded ecological establishment-rule comparison.

Goal
----
Replace an opaque ecological state label with hydrologically explicit rules whose
forms and candidate time scales are constrained by wetland/riparian vegetation
literature, then compare in-sample open-water-area accuracy under the accepted
Stage71 deterministic hydrology and the site-derived 0.38 mm/yr peat central
estimate.

This is an accuracy search *within literature-defined rule families*.  It is not
an acceptance gate and does not change hydrology, peat rate, forcing, observation
years, or the 2022-area contract.

Rule families
-------------
1) continuous_exposure_hazard (legacy comparator):
   first-order persistent establishment hazard after a trailing continuous-
   exposure window.  Trigger windows and rates are searched only over the
   pre-existing model/literature support.

2) woo_persistent_fraction:
   C(t) = max[C(t-1), min(exposed over previous D days)].
   Under nested hypsometric exposure this is the fraction of the 2011 open-water
   footprint that remained exposed continuously for D days and is then retained
   as established.  D uses the total establishment-window support implied by
   Hu et al. (2021): initial ~3 d inundation-free period + 5-12 weeks subsequent
   stability, plus the 70/85-d moist-soil benchmarks of Ahn et al. (2004).

3) dry_period_maturation:
   persistent establishment increases gradually with uninterrupted exposure;
   a cohort reaches full maturity at D=70 or 85 d.  This translates the Ahn et
   al. (2004) finding that ~70 d had been recommended from field observations and
   >85 d was required in their daily millet model for >=50% maximum production.
   It is a diagnostic analogue, not a claim that Seoyeongari vegetation is millet.

4) hydroperiod_hazard:
   first-order establishment hazard from exposed fraction without a consecutive-
   day threshold.  This represents the broader depth/duration/frequency control
   documented by Casanova & Brock (2000) and Webb et al. (2012).

References
----------
- Casanova & Brock 2000 Plant Ecology 147:237-250. DOI 10.1023/A:1009875226637
- Ahn, Sparks & White 2004 River Res. Applic. 20:485-498. DOI 10.1002/rra.769
- Ahn et al. 2007 Ecological Modelling 204:315-325. DOI 10.1016/j.ecolmodel.2007.01.006
- Balke et al. 2014 Journal of Ecology 102. DOI 10.1111/1365-2745.12241
- Hu et al. 2021 Geophysical Research Letters. DOI 10.1029/2021GL095596
- Webb et al. 2012 Aquatic Botany 103:1-14. DOI 10.1016/j.aquabot.2012.06.003
"""
from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Dict, Iterable, List, Sequence, Tuple

import numpy as np

from eghm_deterministic_forcing import deterministic_forcing
from eghm_deterministic_kernel import (
    A0, EVAL_YEARS, OBS_MONTHS, SELECTED_STRUCTURE,
    annual_support, hydro, hydrologic_feature, mean_fsum, rolling_min_complete,
)
from eghm_deterministic_scenarios import (
    fit_four_scenarios, fit_two_nonnegative_fixed, metrics_fixed,
    peat_geomorphic_loss, predict_fixed,
)

OUT = Path('stage73_outputs')
OUT.mkdir(exist_ok=True)

OBS = {2013:2154.430, 2015:2147.678, 2017:2051.218, 2019:2045.159, 2021:1965.256, 2023:1882.700}
Y = [float(OBS[y]) for y in EVAL_YEARS]
PEAT_RATE = 0.38

# Candidate supports are deliberately finite and literature/pre-existing bounded.
LEGACY_WINDOWS_D = [3, 5, 7, 14, 21, 38, 45, 59, 70, 73, 85, 87]
LEGACY_RATES_YR = [0.025, 0.05, 0.10, 0.25]
WOO_WINDOWS_D = [38, 45, 59, 70, 73, 85, 87]
AHN_MATURATION_D = [70, 85]
HYDROPERIOD_RATES_YR = [0.025, 0.05, 0.10, 0.25]


def exposed_fraction(area: Sequence[float]) -> List[float]:
    return [min(max((A0-float(a))/A0, 0.0), 1.0) for a in area]


def state_continuous_hazard(exposed: Sequence[float], window_d: int, rate_yr: float) -> List[float]:
    ew = rolling_min_complete(exposed, int(window_d))
    rd = float(rate_yr)/365.0
    surv = 1.0
    out=[]
    for e in ew:
        q=min(max(1.0-rd*float(e),0.0),1.0)
        surv *= q
        out.append(1.0-surv)
    return out


def state_woo_persistent_fraction(exposed: Sequence[float], window_d: int) -> List[float]:
    """Persistent fraction after D consecutive days of exposure."""
    qual=rolling_min_complete(exposed,int(window_d))
    best=0.0; out=[]
    for q in qual:
        best=max(best,float(q))
        out.append(best)
    return out


def state_dry_period_maturation(exposed: Sequence[float], maturity_d: int) -> List[float]:
    """Persistent max of duration-weighted continuously exposed fraction.

    For each day, consider all trailing uninterrupted windows k=1..D.  A fraction
    continuously exposed for k days receives maturity k/D; after D days it is 1.
    Running maximum makes successful establishment persistent over the study span.
    """
    e=[float(v) for v in exposed]
    D=max(1,int(maturity_d))
    best=0.0; out=[0.0]*len(e)
    for t in range(len(e)):
        mn=1.0
        local=0.0
        lim=min(D,t+1)
        for k in range(1,lim+1):
            mn=min(mn,e[t-k+1])
            local=max(local,mn*(float(k)/float(D)))
            if mn<=0.0:
                break
        best=max(best,local)
        out[t]=best
    return out


def state_hydroperiod_hazard(exposed: Sequence[float], rate_yr: float) -> List[float]:
    rd=float(rate_yr)/365.0
    surv=1.0; out=[]
    for e in exposed:
        q=min(max(1.0-rd*float(e),0.0),1.0)
        surv*=q
        out.append(1.0-surv)
    return out


def candidate_states(exposed: Sequence[float]) -> List[Dict[str,object]]:
    out=[]
    for d in LEGACY_WINDOWS_D:
        for r in LEGACY_RATES_YR:
            out.append({'family':'continuous_exposure_hazard','window_d':d,'rate_yr':r,
                        'n_rule_parameters':2,'state':state_continuous_hazard(exposed,d,r)})
    for d in WOO_WINDOWS_D:
        out.append({'family':'woo_persistent_fraction','window_d':d,'rate_yr':None,
                    'n_rule_parameters':1,'state':state_woo_persistent_fraction(exposed,d)})
    for d in AHN_MATURATION_D:
        out.append({'family':'dry_period_maturation','window_d':d,'rate_yr':None,
                    'n_rule_parameters':1,'state':state_dry_period_maturation(exposed,d)})
    for r in HYDROPERIOD_RATES_YR:
        out.append({'family':'hydroperiod_hazard','window_d':None,'rate_yr':r,
                    'n_rule_parameters':1,'state':state_hydroperiod_hazard(exposed,r)})
    return out


def aicc_from_rmse(rmse: float, n: int, k: int) -> float:
    # Gaussian least-squares constant omitted; valid for relative comparison.
    rss=float(rmse)*float(rmse)*float(n)
    if rss<=0.0 or n-k-1<=0:
        return float('inf')
    return float(n*math.log(rss/n)+2*k+(2*k*(k+1))/(n-k-1))


def fit_integrated(C: Sequence[float], H: Sequence[float], G: Sequence[float], obs: Sequence[float], train_idx: Sequence[int] | None=None):
    if train_idx is None:
        train_idx=list(range(len(obs)))
    idx=[int(i) for i in train_idx]
    geom=[A0-float(G[i]) for i in range(len(obs))]
    negC=[-float(v) for v in C]
    target=[float(obs[i])-geom[i] for i in idx]
    kc,kh=fit_two_nonnegative_fixed([negC[i] for i in idx],[float(H[i]) for i in idx],target,upper_first=A0)
    pred=predict_fixed(geom,negC,kc,H,kh)
    return kc,kh,pred


def nested_loocv(candidates: Sequence[Dict[str,object]], H: Sequence[float], G: Sequence[float]) -> Dict[str,Dict[str,float]]:
    fams=sorted(set(str(c['family']) for c in candidates))
    result={}
    for fam in fams:
        famc=[c for c in candidates if c['family']==fam]
        errs=[]; chosen=[]
        for hold in range(len(Y)):
            train=[i for i in range(len(Y)) if i!=hold]
            scored=[]
            for c in famc:
                C=c['annual_state']
                kc,kh,pred=fit_integrated(C,H,G,Y,train)
                train_m=metrics_fixed([pred[i] for i in train],[Y[i] for i in train])['RMSE_m2']
                scored.append((float(train_m),str(c.get('window_d')),str(c.get('rate_yr')),c,kc,kh,pred))
            scored.sort(key=lambda z:(z[0],z[1],z[2]))
            best=scored[0]
            err=float(best[6][hold])-float(Y[hold])
            errs.append(err)
            chosen.append({'held_out_year':int(EVAL_YEARS[hold]),'window_d':best[3].get('window_d'),'rate_yr':best[3].get('rate_yr')})
        rm=math.sqrt(math.fsum(e*e for e in errs)/len(errs))
        result[fam]={'nested_LOOCV_RMSE_m2':float(rm),'nested_LOOCV_nRMSE_pct':float(100.0*rm/mean_fsum(Y)),'choices':chosen}
    return result


def main():
    F,_,_,_=deterministic_forcing()
    P=dict(SELECTED_STRUCTURE)
    h=hydro(F,P)
    e=exposed_fraction(h['area'])
    H=hydrologic_feature(h['dates'],h['return_flow'],int(P['hydro_window_d']),years=EVAL_YEARS,months=OBS_MONTHS)
    Gd,_,_=peat_geomorphic_loss(h['dates'],h['V'],PEAT_RATE,P['V0'],P['p_shape'])
    G=annual_support(h['dates'],Gd,years=EVAL_YEARS,months=OBS_MONTHS)

    candidates=candidate_states(e)
    rows=[]
    for c in candidates:
        C=annual_support(h['dates'],c['state'],years=EVAL_YEARS,months=OBS_MONTHS)
        c['annual_state']=C
        scenarios=fit_four_scenarios(C,H,G,Y,A0)
        integ=next(z for z in scenarios if z['Scenario']=='Integrated Model')
        hydro_s=next(z for z in scenarios if z['Scenario']=='Hydrosere Only Model')
        k_total=int(c['n_rule_parameters'])+2  # rule hyperparameter(s) + Kc + Kh
        rows.append({
            'family':c['family'],'window_d':c.get('window_d'),'rate_yr':c.get('rate_yr'),
            'n_rule_parameters':int(c['n_rule_parameters']),'k_total_for_AICc':k_total,
            'Integrated_RMSE_m2':float(integ['RMSE_m2']),'Integrated_nRMSE_pct':float(integ['nRMSE_pct']),
            'Hydrosere_RMSE_m2':float(hydro_s['RMSE_m2']),'Hydrosere_nRMSE_pct':float(hydro_s['nRMSE_pct']),
            'K_colonizable_m2':float(integ['K_colonizable_m2']),
            'K_hydro_m2_per_m3':float(integ['K_hydro_m2_per_m3']),
            'AICc_relative':aicc_from_rmse(float(integ['RMSE_m2']),len(Y),k_total),
            **{f'C_{int(y)}':float(C[i]) for i,y in enumerate(EVAL_YEARS)},
            **{f'pred_{int(y)}':float(integ['pred'][i]) for i,y in enumerate(EVAL_YEARS)},
        })

    rows_sorted=sorted(rows,key=lambda z:(z['Integrated_nRMSE_pct'],z['AICc_relative'],z['family'],str(z['window_d']),str(z['rate_yr'])))
    family_best={}
    for fam in sorted(set(r['family'] for r in rows)):
        family_best[fam]=next(r for r in rows_sorted if r['family']==fam)

    loocv=nested_loocv(candidates,H,G)
    for fam,b in family_best.items():
        b.update({k:v for k,v in loocv[fam].items() if k!='choices'})

    import csv
    fields=list(rows_sorted[0].keys())
    with (OUT/'stage73_rule_search.csv').open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=fields); w.writeheader(); w.writerows(rows_sorted)
    (OUT/'stage73_nested_loocv.json').write_text(json.dumps(loocv,ensure_ascii=False,indent=2),encoding='utf-8')

    best=rows_sorted[0]
    result={
        'status':'PASS_STAGE73_REFERENCE_BOUNDED_RULE_SEARCH',
        'observation_variable':'mapped open-water pond surface area',
        'observation_support':'April-May',
        'observed_years':[int(y) for y in EVAL_YEARS],
        'pond_area_observation_2022':'ABSENT',
        'hydrology_changed':False,'peat_rate_changed':False,'peat_rate_mm_yr':PEAT_RATE,
        'selection_objective':'minimum full-six-year Integrated nRMSE within literature/pre-existing bounded ecological rule candidates',
        'selection_is_acceptance_gate':False,
        'best_in_sample':best,
        'family_best':family_best,
        'nested_LOOCV_role':'diagnostic only; not selection or acceptance gate',
        'nested_LOOCV':loocv,
        'references':[
            {'citation':'Casanova & Brock 2000','doi':'10.1023/A:1009875226637','role':'flood depth/duration/frequency control of wetland establishment'},
            {'citation':'Ahn, Sparks & White 2004','doi':'10.1002/rra.769','role':'daily hydrologic vegetation model; ~70-d field recommendation and >85-d modeled dry-period benchmark'},
            {'citation':'Ahn et al. 2007','doi':'10.1016/j.ecolmodel.2007.01.006','role':'dynamic seedling recruitment/survival response to flood timing and duration'},
            {'citation':'Balke et al. 2014','doi':'10.1111/1365-2745.12241','role':'Window of Opportunity concept; minimum disturbance-free establishment period'},
            {'citation':'Hu et al. 2021','doi':'10.1029/2021GL095596','role':'mechanistic WoO: initial ~3 d inundation-free + subsequent 5-12 week stability, calibrated 8 weeks in study'},
            {'citation':'Webb et al. 2012','doi':'10.1016/j.aquabot.2012.06.003','role':'systematic review of wetland plant response to water-regime components'},
        ],
        'physical_closure':{
            'mass_error_m3':float(h['mass_error']),
            'area_partition_error_m2':float(h['area_partition_error']),
            'precip_partition_error_m3':float(h['precip_partition_error']),
        },
    }
    (OUT/'stage73_summary.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(result,ensure_ascii=False,indent=2))

if __name__=='__main__':
    main()
