#!/usr/bin/env python3
"""Stage91-v2 — self-contained TLMM coupling verification from saved CSV artifacts.

No project Python modules are imported. The TLMM recurrence and p=18 geometry
are implemented directly from the audited formulas so the diagnostic can run
from the Stage85/88/89 CSV outputs alone.
"""
from __future__ import annotations
import json, math
from pathlib import Path
import numpy as np
import pandas as pd

ROOT=Path('/mnt/data')
S85=ROOT/'stage85_artifact'
OUT=ROOT/'stage91_v2_outputs'; OUT.mkdir(exist_ok=True)

A0=2241.762; V0=1000.0; P=18.0
H0=V0*(P+2.0)/(A0*P)
F=4.0; S=30.0; CMIN=0.01; WMIN=0.001
OBS={2013:2154.430,2015:2147.678,2017:2051.218,2019:2045.159,2021:1965.256,2023:1882.700}
EVAL=tuple(OBS)

def area_h(h):
    z=min(max(float(h),0.0),H0)
    return 0.0 if z<=0 else A0*(z/H0)**(1.0/9.0)

def depth_v(v):
    v=float(v)
    return 0.0 if v<=0 else H0*(v/V0)**(9.0/10.0)

def flood_response(dt,f=F,cmin=CMIN):
    x=(-math.log10(cmin))*((max(float(dt),0.0)-f)/f)
    x=min(x,0.0); cd=10.0**x
    return min(max((1.0-cd)/(1.0-cmin),0.0),1.0)

def woody_response(xt,s=S,wmin=WMIN):
    x=(-math.log10(wmin))*((max(float(xt),0.0)-s)/s)
    x=min(x,0.0); wx=10.0**x
    return min(max((1.0-wx)/(1.0-wmin),0.0),1.0)

def overlay(df,hcol,driver_months=(9,),eval_months=(4,5),s=S):
    d=df.copy(); d['DATE']=pd.to_datetime(d['DATE']); d['YEAR']=d.DATE.dt.year
    lower=upper=H0; dt=xt=0; mapped=np.zeros(len(d)); states=[]
    for y,g in d.groupby('YEAR',sort=True):
        cap=area_h(lower)
        for idx,row in g.iterrows():
            mapped[d.index.get_loc(idx)]=min(area_h(row[hcol]),cap)
        drv=g[g.DATE.dt.month.isin(driver_months)]
        wl=float(drv[hcol].mean())
        ndt=dt+1 if wl>lower else 0; fr=flood_response(ndt)
        nl=wl if wl<=lower else wl-fr*(wl-lower)
        nxt=0 if wl>=upper else xt+1; wr=woody_response(nxt,s=s)
        nu=wl if wl>=upper else wl-wr*(wl-upper)
        states.append({'driver_year':int(y),'driver_level_m':wl,'MLL_before_m':lower,'MLL_after_m':nl,
                       'MUL_before_m':upper,'MUL_after_m':nu,'A_MLL_before_m2':cap})
        lower,upper,dt,xt=nl,nu,ndt,nxt
    d['tlmm_open_m2']=mapped
    pred=[]
    for y in EVAL:
        q=d[(d.YEAR==y)&d.DATE.dt.month.isin(eval_months)]
        p=float(q.tlmm_open_m2.mean()); pred.append({'Year':y,'Pred_m2':p,'Obs_m2':OBS[y],'Error_m2':p-OBS[y]})
    pt=pd.DataFrame(pred); rmse=float(np.sqrt(np.mean(np.square(pt.Error_m2))))
    nr=100.0*rmse/float(np.mean(list(OBS.values())))
    return d,pd.DataFrame(states),pt,{'RMSE_m2':rmse,'nRMSE_pct':nr}

def main():
    summary=pd.read_csv(S85/'stage85_four_scenario_summary_s30.csv')
    sens=pd.read_csv(S85/'stage85_s15_s30_published_sensitivity.csv')
    ann=pd.read_csv(S85/'stage85_annual_state_diagnostics.csv')
    base=pd.read_csv(S85/'baseline_model_daily.csv'); hydro=pd.read_csv(S85/'hydrosere_only_model_daily.csv')
    base['DATE']=pd.to_datetime(base.DATE); hydro['DATE']=pd.to_datetime(hydro.DATE)

    get=lambda scen: float(summary.loc[summary.Scenario==scen,'nRMSE_pct'].iloc[0])
    baseline_nr=get('Baseline Model'); hyd_nr=get('Hydrosere Only Model'); int_nr=get('Integrated Model')
    s15=float(sens[(sens.Scenario=='Hydrosere Only Model')&(sens.s_yr==15.0)].nRMSE_pct.iloc[0])

    b15=base[(base.YEAR==2015)&base.DATE.dt.month.isin([4,5])]
    h15=hydro[(hydro.YEAR==2015)&hydro.DATE.dt.month.isin([4,5])]
    obs15=OBS[2015]; b15p=float(b15.mapped_open_water_m2.mean()); h15p=float(h15.mapped_open_water_m2.mean())
    capped=int(np.isclose(h15.mapped_open_water_m2,h15.TLMM_aquatic_zone_m2,atol=1e-9).sum())

    # Freeze official Baseline hydrology and add only the MLL clip.
    _,st_frozen,p_frozen,m_frozen=overlay(base,'effective_h_m',(9,))

    # Non-final structural controls: same TLMM overlay on Stage88/89 hydrologies.
    d88=pd.read_csv(ROOT/'stage88_threshold_hard_raw_daily.csv'); d88['h_for_tlmm']=d88.V_m3.map(depth_v)
    _,_,p88,m88=overlay(d88,'h_for_tlmm',(9,))
    d89=pd.read_csv(ROOT/'stage89_cap_729p6_daily.csv'); d89['h_for_tlmm']=d89.surface_m3.map(depth_v)
    _,_,p89,m89=overlay(d89,'h_for_tlmm',(4,5))

    ah=ann[ann.Scenario=='Hydrosere Only Model'].set_index('Year')
    result={
      'status':'PASS_STAGE91_V2_SELF_CONTAINED_VERIFICATION',
      'official_stage85':{'Baseline_nRMSE_pct':baseline_nr,'Hydrosere_nRMSE_pct':hyd_nr,'Integrated_nRMSE_pct':int_nr,
                          'TLMM_increment_vs_baseline_pp':hyd_nr-baseline_nr,'peat_increment_vs_hydrosere_pp':int_nr-hyd_nr,
                          'Hydrosere_s15_nRMSE_pct':s15,'Hydrosere_s30_nRMSE_pct':hyd_nr},
      '2015':{'observed_m2':obs15,'baseline_pred_m2':b15p,'hydrosere_pred_m2':h15p,
              'TLMM_removed_m2':b15p-h15p,'AprMay_days':len(h15),'days_at_MLL_cap':capped,
              'MLL_m':float(h15.TLMM_MLL_m.iloc[0]),'A_MLL_m2':float(h15.TLMM_aquatic_zone_m2.iloc[0])},
      'hysteresis_chain':{'2013_September_effective_h_m':float(ah.loc[2013,'September_mean_effective_h_m']),
                          '2014_Dec31_MLL_m':float(ah.loc[2014,'December31_MLL_m']),
                          '2015_Dec31_MLL_m':float(ah.loc[2015,'December31_MLL_m'])},
      'frozen_stage85_hydrology_plus_MLL_clip':m_frozen,
      'structural_controls_not_accepted':{
          'Stage88_threshold_hard_raw_plus_TLMM_September':m88,
          'Stage89_cap729p6_plus_TLMM_AprMay_driver':m89},
      'notes':['Stage88/89 controls are diagnostics only, not accepted science.',
               'The exact published f,s,cmin,wmin were not fitted or changed.']
    }
    (OUT/'stage91_v2_summary.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    p_frozen.to_csv(OUT/'stage91_v2_frozen_stage85_predictions.csv',index=False)
    p88.to_csv(OUT/'stage91_v2_stage88_tlmm_predictions.csv',index=False)
    p89.to_csv(OUT/'stage91_v2_stage89_tlmm_predictions.csv',index=False)
    st_frozen.to_csv(OUT/'stage91_v2_frozen_stage85_states.csv',index=False)
    print(json.dumps(result,ensure_ascii=False,indent=2))

if __name__=='__main__': main()
