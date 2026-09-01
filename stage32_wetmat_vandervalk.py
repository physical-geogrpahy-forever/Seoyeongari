#!/usr/bin/env python3
import json, math, random
from pathlib import Path
import numpy as np
import pandas as pd
from stage30_macro_head_drainage_fast import forcing, metrics, OBS

OUT=Path('stage32_outputs'); OUT.mkdir(exist_ok=True)
A_EXT=8483.0
A_INIT=2241.762
A_WET=5939.5
SOIL_CAP=.294*.55*A_EXT
YEARS=sorted(OBS)

# Reference-based structure:
# WetMAT: soil storage -> drainable/intermediate storage -> surface flooding.
# van der Valk-type ecology: drawdown/exposure promotes establishment; inundation can reverse it.
# No explicit time trend, no lambda, no 2011 cap, no freeboard.

def surface_area(V,Ks):
    if V<=0: return 0.0
    return A_WET*(1.0-math.exp(-V/max(Ks,1e-9)))

def init_surface_storage(Ks):
    f=min(max(A_INIT/A_WET,1e-9),1-1e-9)
    return -Ks*math.log(1.0-f)

def hydro_sim(F,p):
    kch=p['K_ch']; tauch=p['tau_ch']; local_frac=p['local_frac']
    ks=p['K_surf']; taus=p['tau_surf']; leak=p['leak_mm_d']
    soil=.5*SOIL_CAP; ch=0.0; surf=init_surface_storage(ks)
    pre=F['pre']; pes=F['pes']; eto=F['eto']; ep=F['ep']; yy=F['year']; mm=F['month']
    mj_sum={y:0.0 for y in YEARS}; mj_n={y:0 for y in YEARS}
    exp_sum={y:0.0 for y in range(2011,2024)}; wet_sum={y:0.0 for y in range(2011,2024)}; nd={y:0 for y in range(2011,2024)}
    maxmass=0.0; drain_ch=0.0; drain_s=0.0; deep=0.0; maxA=0.0
    prev=soil+ch+surf
    for i in range(len(pre)):
        y=int(yy[i]); m=int(mm[i])
        A=surface_area(surf,ks)
        # upland/external catchment soil balance
        pext=pre[i]*A_EXT/1000.0
        qrun=max(0.0,pes[i]*A_EXT/1000.0)
        infil=max(0.0,pext-qrun)
        soil+=infil
        aet=min(soil,.95*eto[i]*A_EXT/1000.0); soil-=aet
        rech=max(soil-SOIL_CAP,0.0); soil-=rech
        local=rech*local_frac; deep_i=rech-local; deep+=deep_i
        # intermediate/drainable storage, WetMAT-style
        ch += qrun + local
        qlat=min(ch,ch/max(tauch,1e-9)); ch-=qlat; drain_ch+=qlat
        overflow=max(ch-kch,0.0)
        if overflow>0: ch-=overflow
        # surface flooded storage
        pr=.87*pre[i]*A/1000.0
        pe=.80*ep[i]*A/1000.0
        lk=leak*A/1000.0
        qsurf=min(surf,surf/max(taus,1e-9))
        surf += overflow + pr
        avail=surf
        losses=pe+lk+qsurf
        if losses>avail and losses>0:
            fac=avail/losses; pe*=fac; lk*=fac; qsurf*=fac
        surf-=pe+lk+qsurf; drain_s+=qsurf
        Aout=surface_area(surf,ks); maxA=max(maxA,Aout)
        if y in nd:
            # exposure severity inside the 2011 open-water footprint; bounded [0,1]
            exp_sum[y]+=max(0.0,1.0-Aout/A_INIT)
            wet_sum[y]+=min(1.0,Aout/A_INIT)
            nd[y]+=1
        if y in mj_sum and m in (5,6):
            mj_sum[y]+=Aout; mj_n[y]+=1
        # exact daily mass closure for water state
        total=soil+ch+surf
        pin=pext+pr
        pout=aet+deep_i+qlat+pe+lk+qsurf
        mass=(prev+pin)-(total+pout)
        maxmass=max(maxmass,abs(mass)); prev=total
    mj={y:mj_sum[y]/mj_n[y] for y in YEARS}
    exposure={y:(exp_sum[y]/nd[y] if nd[y] else 0.0) for y in nd}
    wetness={y:(wet_sum[y]/nd[y] if nd[y] else 0.0) for y in nd}
    return {'mj_inundated':mj,'exposure':exposure,'wetness':wetness,'max_mass_error':maxmass,'max_inundated_area':maxA,
            'channel_drain_m3':drain_ch,'surface_drain_m3':drain_s,'deep_m3':deep}

def eco_predict(h,r_est,r_loss,cmax):
    C=0.0
    pred={}
    C_by_year={}
    for y in range(2011,2024):
        C_by_year[y]=C
        if y in OBS:
            pred[y]=max(0.0,h['mj_inundated'][y]-C)
        # state for next year uses only current year's hydrologic history
        E=h['exposure'][y]; W=h['wetness'][y]
        establish=r_est*E*max(cmax-C,0.0)
        loss=r_loss*W*C
        C=min(max(C+establish-loss,0.0),cmax)
    rm,nrm,mae=metrics(pred)
    return {'pred':pred,'C_by_year':C_by_year,'rmse':rm,'nrmse':nrm,'mae':mae,'final_C':C}

def sample_hydro(rng,n=1800):
    out=[]
    for _ in range(n):
        # Log-uniform or bounded ranges, intentionally broad but physically interpretable.
        p={
          'K_ch':10**rng.uniform(math.log10(50),math.log10(1500)),
          'tau_ch':10**rng.uniform(math.log10(15),math.log10(730)),
          'local_frac':rng.uniform(.05,.45),
          'K_surf':10**rng.uniform(math.log10(150),math.log10(3500)),
          'tau_surf':10**rng.uniform(math.log10(30),math.log10(1460)),
          'leak_mm_d':10**rng.uniform(math.log10(.1),math.log10(3.0))}
        out.append(p)
    return out

def loocv_fixed_structure(h,eco_grid):
    # Diagnostic only: choose ecology params on five observed years and test held-out year.
    ys=YEARS; preds={}
    for hold in ys:
        best=None
        for r_est,r_loss,cmax in eco_grid:
            e=eco_predict(h,r_est,r_loss,cmax)
            train=[y for y in ys if y!=hold]
            o=np.array([OBS[y] for y in train]); p=np.array([e['pred'][y] for y in train])
            rm=float(np.sqrt(np.mean((p-o)**2)))
            if best is None or rm<best[0]: best=(rm,e, (r_est,r_loss,cmax))
        preds[hold]=best[1]['pred'][hold]
    o=np.array([OBS[y] for y in ys]); p=np.array([preds[y] for y in ys]); rm=float(np.sqrt(np.mean((p-o)**2)))
    return rm,rm/o.mean()*100,preds

def main():
    F,missing,annual=forcing(); rng=random.Random(32026)
    eco_grid=[(re,rl,cm) for re in [.03,.06,.10,.15,.25,.40,.60] for rl in [0,.01,.03,.06,.10,.20] for cm in [300.,450.,600.,800.,1000.,1300.]]
    best=[]
    for j,p in enumerate(sample_hydro(rng,1800)):
        h=hydro_sim(F,p)
        # Reject numerical failure only; no accuracy/ecology constraint imposed here.
        if h['max_mass_error']>1e-7: continue
        for re,rl,cm in eco_grid:
            e=eco_predict(h,re,rl,cm)
            best.append((e['nrmse'],p,h,re,rl,cm,e))
        if (j+1)%200==0: print('hydro candidates',j+1)
    best.sort(key=lambda x:x[0])
    top=best[:100]
    rows=[]
    for nrm,p,h,re,rl,cm,e in top:
        row={**p,'r_est_yr':re,'r_loss_yr':rl,'Cmax_m2':cm,'rmse':e['rmse'],'nrmse':e['nrmse'],'mae':e['mae'],'final_C_m2':e['final_C'],
             'max_mass_error_m3':h['max_mass_error'],'max_inundated_area_m2':h['max_inundated_area']}
        for y in YEARS:
            row[f'inund_{y}']=h['mj_inundated'][y]; row[f'C_{y}']=e['C_by_year'][y]; row[f'pred_{y}']=e['pred'][y]
        rows.append(row)
    pd.DataFrame(rows).to_csv(OUT/'stage32_top100.csv',index=False)
    nrm,p,h,re,rl,cm,e=best[0]
    cv_rm,cv_nrm,cvp=loocv_fixed_structure(h,eco_grid)
    summary={'best_hydrology':p,'best_ecology':{'r_est_yr':re,'r_loss_yr':rl,'Cmax_m2':cm},'best':e,
             'hydrologic_inundated_may_june':h['mj_inundated'],'annual_exposure':h['exposure'],'annual_wetness':h['wetness'],
             'hydrology_diagnostics':{k:h[k] for k in ['max_mass_error','max_inundated_area','channel_drain_m3','surface_drain_m3','deep_m3']},
             'loocv':{'rmse':cv_rm,'nrmse':cv_nrm,'pred':cvp},
             'benchmarks':{'stage31b_time_nrmse':0.7692692574776534,'stage31c_no_time_nrmse':1.0969697397128737,'stage31e_nrmse':1.001791458580214},
             'rules':{'lambda':0,'explicit_time':False,'hard_2011_cap':False,'freeboard':False,'DSM':False,'bathymetry':False,
                      'open_water_equation':'A_open=A_inundated-C_colonized','hydrology':'WetMAT-like soil -> intermediate drainable storage -> surface flooding',
                      'ecology':'exposure establishment and inundation reversal; van der Valk-type hydroperiod control'}}
    (OUT/'stage32_summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(summary,ensure_ascii=False,indent=2))

if __name__=='__main__': main()
