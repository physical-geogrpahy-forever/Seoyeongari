#!/usr/bin/env python3
import json, math, itertools
from pathlib import Path
import numpy as np
import pandas as pd

AWS_PATH = Path('OBS_AWS_DD_20250930013603.csv')
ASOS_PATH = Path('OBS_ASOS_DD_20250930041037.csv')
OUT = Path('stage30_outputs'); OUT.mkdir(exist_ok=True)

# Locked project geometry / observations
A_REF = 2241.762
A_EXT = 8483.0
HB = 1.2
ALPHA = 1.3
SOIL_CAP = 0.294 * 0.55 * A_EXT
OBS = {2013:2154.430, 2015:2147.678, 2017:2051.218, 2019:2045.159, 2021:1965.256, 2023:1882.700}
TARGET26 = {2013:2182.2346, 2015:2203.2931, 2017:1962.5506, 2019:1999.3472, 2021:2184.1155, 2023:2196.6569}

# Original forcing constants/formulae recovered from authoritative optimizer
LAT_DEG=33.30456; ALT_M=188.42; A_S=0.25; B_S=0.50; WIND_Z=2.0
ALPHA_VEG=0.23; ALPHA_WATER=0.08; I_P=0.13; CN=68.0
S_MM=25400/CN-254; IA_MM=0.2*S_MM

def e0(t): return 0.6108*np.exp(17.27*t/(t+237.3))
def delta_fun(t): return 4098*e0(t)/(t+237.3)**2
def p_kpa(z): return 101.3*((293-0.0065*z)/293)**5.26
def u2_from_uz(u,z): return u*4.87/np.log(67.8*z-5.42)
def ra_n(doy,lat):
    gsc=.0820; dr=1+.033*np.cos(2*np.pi*doy/365.0)
    dec=.409*np.sin(2*np.pi*doy/365.0-1.39)
    ws=np.arccos(np.clip(-np.tan(lat)*np.tan(dec),-1,1))
    ra=(24*60/np.pi)*gsc*dr*(ws*np.sin(lat)*np.sin(dec)+np.cos(lat)*np.cos(dec)*np.sin(ws))
    return ra,(24/np.pi)*ws

def read_asos(path):
    for enc in ('cp949','utf-8-sig','utf-8'):
        try:
            return pd.read_csv(path, encoding=enc)
        except Exception:
            pass
    raise RuntimeError('ASOS encoding could not be read')

def load_forcing():
    aws=pd.read_csv(AWS_PATH)
    d=pd.to_datetime(aws['time'],errors='coerce')
    df=pd.DataFrame({
        'DATE':d,'DOY':d.dt.dayofyear,
        'TMEAN':pd.to_numeric(aws['tmean'],errors='coerce'),
        'TMIN':pd.to_numeric(aws['tmin'],errors='coerce'),
        'TMAX':pd.to_numeric(aws['tmax'],errors='coerce'),
        'PRE':pd.to_numeric(aws['pre'],errors='coerce'),
        'U_raw':pd.to_numeric(aws['wind'],errors='coerce')})
    asos=read_asos(ASOS_PATH)
    if '지점' in asos.columns: asos=asos[asos['지점']==189]
    # The repository file has time/hour even if Korean header bytes are legacy encoded.
    if 'time' not in asos.columns or 'hour' not in asos.columns:
        lower={str(c).strip().lower():c for c in asos.columns}
        if 'time' not in lower or 'hour' not in lower:
            raise RuntimeError(f'ASOS columns not recognized: {list(asos.columns)}')
        tc,hc=lower['time'],lower['hour']
    else: tc,hc='time','hour'
    sun=pd.DataFrame({'DATE':pd.to_datetime(asos[tc],errors='coerce'),'SUNH':pd.to_numeric(asos[hc],errors='coerce')}).dropna(subset=['DATE'])
    sun=sun.groupby('DATE',as_index=False)['SUNH'].mean()
    df=df.merge(sun,on='DATE',how='left'); df['SUNH']=df['SUNH'].fillna(0)
    df=df[(df.DATE>='2011-01-01')&(df.DATE<='2023-12-31')].copy().reset_index(drop=True)

    missing_before={c:int(df[c].isna().sum()) for c in ['TMEAN','TMIN','TMAX','PRE','U_raw','SUNH']}
    # Preserve precipitation strictly; only meteorological state variables are linearly infilled if isolated gaps exist.
    df['PRE']=df['PRE'].fillna(0).clip(lower=0)
    for c in ['TMEAN','TMIN','TMAX','U_raw']:
        df[c]=df[c].interpolate(limit_direction='both')

    lat=np.deg2rad(LAT_DEG); pres=p_kpa(ALT_M); ga=.000665*pres; lam=2.45
    ra,N=ra_n(df.DOY.to_numpy(float),lat); u2=u2_from_uz(df.U_raw.to_numpy(float),WIND_Z)
    rso=(.75+2e-5*ALT_M)*ra; nn=np.clip(df.SUNH.to_numpy(float)/np.maximum(N,1e-6),0,1); rs=(A_S+B_S*nn)*ra
    es=(e0(df.TMAX.to_numpy(float))+e0(df.TMIN.to_numpy(float)))/2; ea=e0(df.TMIN.to_numpy(float)); D=delta_fun(df.TMEAN.to_numpy(float))
    sigma=4.903e-9; tmaxk=df.TMAX.to_numpy(float)+273.16; tmink=df.TMIN.to_numpy(float)+273.16
    f=np.clip(rs/np.maximum(rso,1e-6),0,1); kc=1.35*f-.35
    rnl=sigma*((tmaxk**4+tmink**4)/2)*(0.34-0.14*np.sqrt(np.maximum(ea,0)))*kc
    rnveg=(1-ALPHA_VEG)*rs-rnl; rnwater=(1-ALPHA_WATER)*rs-rnl
    eto=np.maximum((.408*D*rnveg+ga*(900/(df.TMEAN.to_numpy(float)+273))*u2*(es-ea))/(D+ga*(1+.34*u2)),0)
    ep=np.maximum((D/(D+ga))*(rnwater/lam)+(ga/(D+ga))*(6.43*(1+.536*u2)/lam)*(es-ea),0)
    pc=df.PRE.to_numpy(float)
    pes=np.where((np.isnan(pc))|(pc<=IA_MM),0,(pc-IA_MM)**2/(pc+.8*S_MM))
    df['ETo']=eto; df['E_P']=ep; df['P_ES']=pes; df['P_P']=(1-I_P)*df.PRE
    df.to_csv(OUT/'daily_forcing_stage30.csv',index=False)
    annual=df.groupby(df.DATE.dt.year)['PRE'].sum().to_dict()
    return df, missing_before, annual

def v_of_h(h):
    if h<=0: return 0.0
    return A_REF*HB/(ALPHA+1)*(h/HB)**(ALPHA+1)
def h_of_v(v):
    if v<=0: return 0.0
    return HB*(v/(A_REF*HB/(ALPHA+1)))**(1/(ALPHA+1))
def a_of_v(v):
    h=h_of_v(v)
    return 0.0 if h<=0 else A_REF*(h/HB)**ALPHA

def score(pred, obs=OBS):
    yrs=sorted(obs); o=np.array([obs[y] for y in yrs]); p=np.array([pred[y] for y in yrs])
    rmse=float(np.sqrt(np.mean((p-o)**2))); nrmse=float(rmse/o.mean()*100); mae=float(np.mean(np.abs(p-o)))
    return rmse,nrmse,mae

def simulate(df, pars, mode='stage30', variant=None, keep_daily=False):
    variant=variant or {}
    local_frac=pars.get('local_frac',.30); fast_frac=pars.get('fast_frac',.25)
    tau_fast=pars.get('tau_fast',60.); tau_slow=pars.get('tau_slow',730.); leak=pars.get('leak_mm_d',.5); c2=pars.get('c2',0.)
    soil_init=variant.get('soil_init','half')
    soil={'zero':0.0,'half':SOIL_CAP/2,'full':SOIL_CAP}.get(soil_init,SOIL_CAP/2)
    fast=0.0; slow=0.0; pond=v_of_h(HB); cap=v_of_h(HB)
    rows=[]; total_spill=total_qlat=total_deep=total_recharge=0.0; max_mass=0.0
    # Whole-system accounting starts after initialization; initial storages are state, not flux.
    prev_total=soil+fast+slow+pond
    for r in df.itertuples(index=False):
        pre=float(r.PRE); pes=float(r.P_ES); eto=float(r.ETo); ep=float(r.E_P); pp=float(r.P_P)
        # External catchment: rainfall partitions into SCS runoff + infiltrating soil water.
        pext=pre*A_EXT/1000.0; qrun=min(pext, max(0.0,pes*A_EXT/1000.0)); infil=max(pext-qrun,0.0)
        soil += infil
        if variant.get('soil_order','et_then_recharge')=='recharge_then_et':
            recharge=max(soil-SOIL_CAP,0.0); soil-=recharge
            aet=min(soil, .95*eto*A_EXT/1000.0); soil-=aet
        else:
            aet=min(soil, .95*eto*A_EXT/1000.0); soil-=aet
            recharge=max(soil-SOIL_CAP,0.0); soil-=recharge
        local=recharge*local_frac; deep=recharge-local
        total_recharge+=recharge; total_deep+=deep
        rf=local*fast_frac; rs=local-rf
        if variant.get('release_order','post')=='pre':
            qf=min(fast,fast/tau_fast); qs=min(slow,slow/tau_slow)
            fast-=qf; slow-=qs; fast+=rf; slow+=rs
        else:
            fast+=rf; slow+=rs
            qf=min(fast,fast/tau_fast); qs=min(slow,slow/tau_slow)
            fast-=qf; slow-=qs

        area=a_of_v(pond); h=h_of_v(pond)
        rain_area=A_REF if variant.get('pond_rain_area','dynamic')=='fixed' else area
        evap_area=A_REF if variant.get('pond_evap_area','dynamic')=='fixed' else area
        leak_area=A_REF if variant.get('pond_leak_area','dynamic')=='fixed' else area
        prain=pp*rain_area/1000.0
        pevap=min(pond+qrun+qf+qs+prain, .80*ep*evap_area/1000.0)
        pleak=leak*leak_area/1000.0
        if variant.get('include_qs01',False): pleak += .01*pp*leak_area/1000.0
        # Head drainage has no threshold/cap: Dupuit-type continuous Q = C2*h^2.
        qlat=0.0 if mode=='stage26' else c2*h*h
        available=pond+qrun+qf+qs+prain
        total_loss=min(available, pevap+pleak+qlat)
        # Preserve requested proportions when water is limiting; normally not active.
        denom=pevap+pleak+qlat
        if denom>0 and total_loss<denom:
            fac=total_loss/denom; pevap*=fac; pleak*=fac; qlat*=fac
        pond=available-pevap-pleak-qlat
        spill=0.0
        if mode=='stage26' and pond>cap:
            spill=pond-cap; pond=cap
        total_spill+=spill; total_qlat+=qlat

        total_now=soil+fast+slow+pond
        # Inputs: external rainfall + direct pond rainfall. Outputs: catchment AET/deep + pond evap/leak/qlat/spill.
        mass=(prev_total + pext + prain) - (total_now + aet + deep + pevap + pleak + qlat + spill)
        max_mass=max(max_mass,abs(mass)); prev_total=total_now
        rows.append((r.DATE,a_of_v(pond),h_of_v(pond),pond,soil,fast,slow,recharge,deep,qrun,qf,qs,prain,pevap,pleak,qlat,spill,mass))
    daily=pd.DataFrame(rows,columns=['date','area_m2','h_m','pond_m3','soil_m3','fast_m3','slow_m3','recharge_m3','deep_m3','runoff_to_pond_m3','fast_return_m3','slow_return_m3','pond_rain_m3','pond_evap_m3','pond_leak_m3','head_drain_m3','spill_m3','mass_error_m3'])
    daily['date']=pd.to_datetime(daily['date'])
    pred={}
    for y in OBS:
        s=daily[(daily.date.dt.year==y)&(daily.date.dt.month.isin([5,6]))]
        pred[y]=float(s.area_m2.mean())
    rmse,nrmse,mae=score(pred)
    spring=daily[daily.date.dt.month.isin([3,4])]
    result={'pred':pred,'rmse':rmse,'nrmse':nrmse,'mae':mae,'max_h':float(daily.h_m.max()),
            'dry_days':int((daily.area_m2<1.0).sum()),'spring_dry_days':int((spring.area_m2<1.0).sum()),
            'spill_m3':total_spill,'head_drain_m3':total_qlat,'deep_m3':total_deep,'recharge_m3':total_recharge,
            'max_daily_mass_error_m3':max_mass,'final_storage_m3':float(daily.iloc[-1][['pond_m3','soil_m3','fast_m3','slow_m3']].sum())}
    return result,(daily if keep_daily else None)

def stage26_regression(df):
    target=np.array([TARGET26[y] for y in sorted(TARGET26)])
    variants=[]
    for soil_init,soil_order,release_order,rain_area,evap_area,leak_area,qs01 in itertools.product(
        ['zero','half','full'],['et_then_recharge','recharge_then_et'],['post','pre'],['dynamic','fixed'],['dynamic','fixed'],['dynamic','fixed'],[False,True]):
        v={'soil_init':soil_init,'soil_order':soil_order,'release_order':release_order,
           'pond_rain_area':rain_area,'pond_evap_area':evap_area,'pond_leak_area':leak_area,'include_qs01':qs01}
        r,_=simulate(df,{'local_frac':.30,'fast_frac':.25,'tau_fast':60.,'tau_slow':730.,'leak_mm_d':.5},'stage26',v,False)
        p=np.array([r['pred'][y] for y in sorted(TARGET26)])
        rr=float(np.sqrt(np.mean((p-target)**2)))
        variants.append((rr,v,r))
    variants.sort(key=lambda x:x[0])
    rows=[]
    for rr,v,r in variants[:20]:
        rows.append({'target_rmse_m2':rr,**v,'obs_nrmse_pct':r['nrmse'],'spill_m3':r['spill_m3'],'max_h_m':r['max_h'],**{f'p{y}':r['pred'][y] for y in sorted(TARGET26)}})
    pd.DataFrame(rows).to_csv(OUT/'stage26_regression_variants.csv',index=False)
    return variants[0]

def stage30_sweep(df, variant):
    # First isolate the structural replacement with Stage-26 parameters.
    c2_values=[0,.125,.25,.5,1,2,3,4,5,6,8,10,12,16,24,32,48]
    fixed=[]
    for c2 in c2_values:
        p={'local_frac':.30,'fast_frac':.25,'tau_fast':60.,'tau_slow':730.,'leak_mm_d':.5,'c2':c2}
        r,_=simulate(df,p,'stage30',variant,False); fixed.append({**p,**r})
    pd.DataFrame([{k:(json.dumps(v) if isinstance(v,dict) else v) for k,v in x.items()} for x in fixed]).to_csv(OUT/'stage30_fixed_stage26_params.csv',index=False)

    # Limited joint screen: same process family, no cap/freeboard/relaxation parameter.
    grid={
      'local_frac':[.10,.20,.30], 'fast_frac':[.25,.50,.75], 'tau_fast':[30.,60.],
      'tau_slow':[365.,730.,1460.], 'leak_mm_d':[.5,1.,2.,4.091],
      'c2':[.125,.25,.5,1.,2.,3.,4.,5.,6.,8.,10.,12.,16.,24.,32.,48.]}
    best=[]
    for vals in itertools.product(*grid.values()):
        p=dict(zip(grid.keys(),vals)); r,_=simulate(df,p,'stage30',variant,False)
        best.append((r['nrmse'],p,r))
    best.sort(key=lambda x:x[0])
    top=[]
    for _,p,r in best[:100]:
        row={**p,**{k:v for k,v in r.items() if k!='pred'},**{f'p{y}':r['pred'][y] for y in sorted(OBS)}}; top.append(row)
    pd.DataFrame(top).to_csv(OUT/'stage30_joint_top100.csv',index=False)
    bp,br=best[0][1],best[0][2]
    br_full,daily=simulate(df,bp,'stage30',variant,True)
    daily.to_csv(OUT/'stage30_best_daily.csv',index=False)
    return fixed,bp,br_full

def main():
    df,missing,annual=load_forcing()
    rr,best_variant,r26=stage26_regression(df)
    fixed,bp,b30=stage30_sweep(df,best_variant)
    report={
      'forcing_rows':len(df),'forcing_start':str(df.DATE.min().date()),'forcing_end':str(df.DATE.max().date()),
      'missing_raw':missing,'annual_precip_mm':{str(k):float(v) for k,v in annual.items()},
      'stage26_known_nrmse_pct':8.008034,'stage26_regression_target_rmse_m2':rr,
      'stage26_selected_variant':best_variant,'stage26_reconstructed':r26,
      'stage30_best_params':bp,'stage30_best':b30,
      'rules':{'lambda':0,'hard_cap':False,'freeboard_threshold':False,'dsm_used':False,'bathymetry_used':False,'drainage':'Q=C2*h^2 continuous'}
    }
    (OUT/'stage30_summary.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print('=== STAGE 26 REGRESSION ===')
    print('target-vector RMSE m2:',rr); print('variant:',best_variant); print(json.dumps(r26,ensure_ascii=False,indent=2))
    print('=== STAGE 30 BEST ==='); print('params:',bp); print(json.dumps(b30,ensure_ascii=False,indent=2))
    print('=== ANNUAL PRECIP CHECK ==='); print(json.dumps({y:annual.get(y) for y in [2013,2015,2017,2019,2021,2023]},indent=2))

if __name__=='__main__': main()
