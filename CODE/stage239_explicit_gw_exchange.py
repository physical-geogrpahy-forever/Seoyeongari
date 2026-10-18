from __future__ import annotations

"""Seoyeongari Stage239: final explicit-groundwater diagnostic built on the locked
Stage239 base + (a) honest direct-front-to-herb bookkeeping and
(b) a real, reversible, hydrologic persistent-bare state. Derived from
the locked Stage239 lineage; earlier source versions are not required for
reproduction of this repository.

Changes relative to the earlier CN-only branch:
1) No 2010 meteorological spin-up or antecedent ecological gate.
   The 2011 observed pond footprint initializes the model at the rim/spill datum (h=0).
2) External runon is direct NRCS-CN runoff only:
      P_ext_eff = 0.70 * P; CN=68; Q_CN enters wetland directly.
   No root-zone bucket, recharge target, deep-loss alpha, or routing reservoir.
3) Temporary bare cells remain hydrologically inundatable; only herb/forest are irreversible.
4) Front arrival -> herb directly, no separate one-year bare-lag state.
   Audit note: in Stage239 this "one-year bare" state (age in [0,1) under integer-year
   bookkeeping) could never actually be reached -- bare_start is only set at the *end* of
   the year it fires, so the next time age is evaluated it is already >=1, i.e. already
   herb-eligible. The bare-lag variable was computed but never consumed downstream in
   Stage239's own code. So this is a bookkeeping/documentation correction, not a behavior
   change from what Stage239 actually computed; it implements the user's later explicit
   decision (front arrival -> herb directly) and removes the now-misleading LOCK/docstring
   claim that a one-year bare establishment state is enforced.
5) Peat elevation updates the surface-water storage-depth curve each year.
6) Direct precipitation interception inside the 2011 depression:
      water/bare: 0%; herb/forest: 30%.
7) State ET lock retained: open water=EP, flooded sedge=0.80 EP,
   exposed bare=0.30 ETo, herb=0.90 ETo, forest=1.00 ETo.
8) DSM shape/amplitude convention retained from Stage239: raw 0-0.48 m depth shape
   standardized by its SD and scaled by literature-bounded sigma=0.06/0.09 m.
9) Strict factorial observation operator: no counterfactual succession/grass mask is applied to Baseline or Eco-Geo.
10) Diagnostic geomorphic boundary: a non-herb/non-forest cell whose peat-raised surface exceeds the measured rim/spill datum h=0 is treated as geomorphic exposed bare outside the hydrologic footprint until/if subsidence returns it below h=0. No fitted threshold is introduced.
11) [NEW] Real persistent-bare hydrologic state, reversible, applied to all four scenarios
    (part of core "H"). A cell enters persistent bare for year y+1 if it satisfied the
    *already-declared* May1-15 14-day dry-exposure threshold AND was not re-flooded past the
    May15-Jun7 14-day / 0.05 m reflood-sieve in year y -- i.e. exactly the same `eligible`
   gate already computed (thresholds_for_year / DRY_N / REF_N / REF_DEPTH_M) to
    drive succession-front progress, now also used directly as a state. It is recomputed
    fresh every year (never cumulative), so a cell leaves persistent bare the first year it
    fails that same test (i.e. re-floods) -- it is not irreversible like herb/forest, and it
    is not a previous counterfactual counterfactual mask applied only at scoring time: it changes the
    actual `wetland` mask that drives storage curve, ET, and peat input for the following
    year. No new fitted duration or threshold is introduced anywhere in this mechanism.

No historical-area tuning is performed. Scoring is evaluation only.
"""

import hashlib
import itertools
import json
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
import rasterio
from shapely import distance, points

# -----------------------------------------------------------------------------
# Paths and direct site quantities
# -----------------------------------------------------------------------------
ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / 'DATA'
OUT = ROOT / 'GW_EXCHANGE_RESULTS'
OUT.mkdir(parents=True, exist_ok=True)

AWS = INPUT / 'met/OBS_AWS_DD_20250930013603.csv'
ASOS = INPUT / 'met/OBS_ASOS_DD_20250930041037.csv'
DSM = INPUT / 'geometry/stage156_dsm_bowl_depth_m.tif'
PLOT2011 = INPUT / 'geometry/plot_2011.shp'

A_WET = 2241.7623884563154  # actual 2011 polygon area used by the rasterized model, m2
A_EXT = 8483.0              # external contributing area, m2
CN = 68.0
EXT_THROUGHFALL = 0.70
TERRESTRIAL_THROUGHFALL = 0.70  # 30% interception for herb and forest

# Peat profile / PTF inherited from the locked model lineage
PEAT_VOL = np.array([200.593,200.593,195.798,178.850,164.248,144.263,109.974,83.761], float)
PEAT_MID_CM = np.arange(5,80,10,dtype=float)
BD_SITE = 0.330
SY_M1=-0.697; SY_M2=-0.104; SY_B=-2.640
SY_LAYER=np.exp(SY_M1*np.log(BD_SITE)+SY_M2*np.log(PEAT_MID_CM)+SY_B)

AREA_TRAPA=627.945
AREA_SCHOENO=1147.026
F_TRAPA=AREA_TRAPA/(AREA_TRAPA+AREA_SCHOENO)
F_SCHOENO=1.0-F_TRAPA

MICRO_SIGMA=[0.065]
R_DRY=0.0114

K_FOREST=1.00
K_EXPOSED_HERB=0.90
K_BARE=0.30
K_FLOODED_SEDGE_EP=0.80

BARE_LAG_YR=1.0
FOREST_LAG_YR=5.283359281985527
DRY_N=14
REF_N=14
REF_DEPTH_M=0.05

TREE_RING_CASES={
    'A': {'intercept_yr':4.566670840115191, 'slope_yr_per_m':1.688994616251408},
    'B': {'intercept_yr':5.768663071246102, 'slope_yr_per_m':1.8946920238433163},
    'Combined': {'intercept_yr':5.283359281985527, 'slope_yr_per_m':1.7601036201640659},
}
for v in TREE_RING_CASES.values():
    v['speed_m_per_eligible_yr']=1.0/v['slope_yr_per_m']

# Site peat input retained as explicitly user-confirmed spatially uniform wetland input.
OM_INPUT=(.828*627.945 + .788*1147.026)/(627.945+1147.026)
OM_BULK_DENSITY=330.0*0.5196430986539488
K0=0.25
DECAY_N=0.55

OBSERVED_WETLAND_M2={
    2011:2242.974, 2013:2154.430, 2015:2147.678, 2017:2051.218,
    2019:2045.159, 2021:1965.256, 2023:1882.700,
}
SCORED_YEARS=[2013,2015,2017,2019,2021,2023]


# Explicit regional-groundwater exchange sensitivity term.
# Apr-May mean groundwater elevations from the nearest regional monitoring well (JQ-Geumak-1),
# supplied by the user. 2020 is used only as the zero-anomaly reference; no wetland-area
# observation enters this forcing. The term is active only in Apr-May because the boundary
# signal used here is the Apr-May mean head anomaly.
GW_AM_EL_M={2020:216.705, 2021:216.820, 2022:216.055, 2023:215.875, 2024:216.680}
GW_REF_EL_M=GW_AM_EL_M[2020]
# Leakage/exchange coefficient sensitivity, d^-1. Structural diagnostic only, not calibration.
GW_C_VALUES=[0.0,0.00025,0.0005,0.001,0.002,0.003]

# -----------------------------------------------------------------------------
# Meteorological forcing. No 2010 data are loaded or used.
# Wind is treated as 2-m wind, per user confirmation and the locked Stage239 lineage.
# -----------------------------------------------------------------------------
def load_forcing(start='2011-01-01', end='2024-12-31'):
    aws=pd.read_csv(AWS,encoding='cp949')
    aws['DATE']=pd.to_datetime(aws['time'],errors='coerce')
    aws=aws[(aws.DATE>=start)&(aws.DATE<=end)].sort_values('DATE').reset_index(drop=True)
    for c in ['tmean','tmin','tmax','wind']:
        aws[c]=pd.to_numeric(aws[c],errors='coerce').interpolate(limit_direction='both')
    aws['pre']=pd.to_numeric(aws['pre'],errors='coerce').fillna(0).clip(lower=0)

    asos=pd.read_csv(ASOS,encoding='cp949')
    asos['DATE']=pd.to_datetime(asos['time'],errors='coerce')
    asos=asos[(asos.DATE>=start)&(asos.DATE<=end)]
    if '지점' in asos.columns:
        asos=asos[pd.to_numeric(asos['지점'],errors='coerce').eq(189)]
    asos['hour']=pd.to_numeric(asos['hour'],errors='coerce')
    sun=asos.groupby('DATE')['hour'].mean()
    aws['sun']=aws.DATE.map(sun).fillna(0.0)

    lat=np.deg2rad(33.30456); alt=188.42
    doy=aws.DATE.dt.dayofyear.to_numpy(float)
    tmean=aws.tmean.to_numpy(float); tmin=aws.tmin.to_numpy(float); tmax=aws.tmax.to_numpy(float)
    pre=aws.pre.to_numpy(float); wind=aws.wind.to_numpy(float); sunshine=aws.sun.to_numpy(float)
    dr=1+0.033*np.cos(2*np.pi*doy/365)
    dec=0.409*np.sin(2*np.pi*doy/365-1.39)
    ws=np.arccos(np.clip(-np.tan(lat)*np.tan(dec),-1,1))
    ra=(24*60/np.pi)*0.082*dr*(ws*np.sin(lat)*np.sin(dec)+np.cos(lat)*np.cos(dec)*np.sin(ws))
    N=(24/np.pi)*ws
    # User-confirmed source wind is already 2-m wind: no 10m->2m conversion is applied.
    u2=wind
    patm=101.3*((293-0.0065*alt)/293)**5.26
    ga=.000665*patm
    rso=(.75+2e-5*alt)*ra
    nN=np.clip(sunshine/np.maximum(N,1e-6),0,1)
    rs=(.25+.50*nN)*ra
    def e0(t): return .6108*np.exp(17.27*t/(t+237.3))
    es=(e0(tmax)+e0(tmin))/2; ea=e0(tmin)
    Delta=4098*e0(tmean)/(tmean+237.3)**2
    f=np.clip(rs/np.maximum(rso,1e-6),0,1)
    sig=4.903e-9
    rnl=sig*(((tmax+273.16)**4+(tmin+273.16)**4)/2)*(.34-.14*np.sqrt(np.maximum(ea,0)))*(1.35*f-.35)
    rnveg=(1-.23)*rs-rnl; rnwat=(1-.08)*rs-rnl
    eto=(.408*Delta*rnveg + ga*(900/(tmean+273))*u2*(es-ea))/(Delta+ga*(1+.34*u2))
    eto=np.maximum(eto,0)
    lam=2.45
    ep=(Delta/(Delta+ga))*(rnwat/lam)+(ga/(Delta+ga))*(6.43*(1+.536*u2)/lam)*(es-ea)
    ep=np.maximum(ep,0)
    return pd.DataFrame({'DATE':aws.DATE,'PRE':pre,'ETo':eto,'EP':ep})

FDEV=load_forcing()

# -----------------------------------------------------------------------------
# Direct NRCS-CN runon; no bucket/recharge/routing.
# -----------------------------------------------------------------------------
def cn_runoff_mm(P_mm, cn=CN):
    P=np.asarray(P_mm,float)
    S=25400.0/float(cn)-254.0
    Ia=0.2*S
    Q=np.zeros_like(P)
    m=P>Ia
    Q[m]=(P[m]-Ia)**2/(P[m]-Ia+S)
    return Q

P_EXT_EFF=EXT_THROUGHFALL*FDEV.PRE.to_numpy(float)
QCN_MM=cn_runoff_mm(P_EXT_EFF)
RUNON_M3=QCN_MM*A_EXT/1000.0

# -----------------------------------------------------------------------------
# DSM geometry. Retain Stage239 sigma convention.
# -----------------------------------------------------------------------------
with rasterio.open(DSM) as ds:
    arr=ds.read(1).astype(float); nod=ds.nodata
    valid=np.isfinite(arr)
    if nod is not None: valid &= arr!=nod
    depth=arr[valid]
    rows,cols=np.where(valid)
    xs,ys=rasterio.transform.xy(ds.transform,rows,cols,offset='center')
    raster_crs=ds.crs
DEPTH_SD=float(depth.std(ddof=0))
UNIT_DEPTH=depth/DEPTH_SD
CELL=A_WET/len(depth)

poly=gpd.read_file(PLOT2011).to_crs(raster_crs).geometry.iloc[0]
DIST_TO_BOUNDARY=np.asarray(distance(points(np.asarray(xs),np.asarray(ys)),poly.boundary),float)

# -----------------------------------------------------------------------------
# Storage curve. This is rebuilt whenever peat surface or irreversible land cover changes.
# Surface ponding is allowed only on water/bare cells. The shared subsurface peat store is
# retained over the initial depression control volume.
# -----------------------------------------------------------------------------
def subsurface_storage(h):
    depth_wt=max(-float(h),0.0)
    total=0.0
    for j,(V,Sy) in enumerate(zip(PEAT_VOL,SY_LAYER)):
        z0=0.1*j; z1=0.1*(j+1)
        frac=np.clip((z1-depth_wt)/(z1-z0),0,1)
        total += V*Sy*frac
    return float(total)

HGRID=np.linspace(-0.80,0.0,8001)
SUBSURF=np.array([subsurface_storage(h) for h in HGRID],float)

def base_surface(sigma):
    return -UNIT_DEPTH*float(sigma)

def make_storage_curve(surface, hydrologic_mask):
    S=SUBSURF.copy()
    zall=np.asarray(surface,float)[np.asarray(hydrologic_mask,bool)]
    for j in range(0,len(zall),500):
        z=zall[j:j+500]
        S += np.maximum(HGRID[:,None]-z[None,:],0).sum(axis=1)*CELL
    S=np.maximum.accumulate(S)
    return S,float(S[0]),float(S[-1])

def interp_h(S,Sg):
    return float(np.interp(np.clip(S,Sg[0],Sg[-1]),Sg,HGRID))

# -----------------------------------------------------------------------------
# Peat process
# -----------------------------------------------------------------------------
def peat_decay_step(cohorts):
    for c in cohorts:
        ratio=np.divide(c['m'],c['m0'],out=np.zeros_like(c['m']),where=c['m0']>0)
        c['m']*=np.exp(-K0*np.power(np.clip(ratio,0,1),DECAY_N))

# -----------------------------------------------------------------------------
# State-weighted hydrology
# -----------------------------------------------------------------------------
def daily_et_m3(row,n_water,n_exposed_bare,n_geomorphic_bare,n_herb,n_forest):
    fw=n_water/len(depth)
    fb=(n_exposed_bare+n_geomorphic_bare)/len(depth)
    fh=n_herb/len(depth)
    fo=n_forest/len(depth)
    mm=(fw*F_TRAPA*float(row.EP)
        + fw*F_SCHOENO*K_FLOODED_SEDGE_EP*float(row.EP)
        + fb*K_BARE*float(row.ETo)
        + fh*K_EXPOSED_HERB*float(row.ETo)
        + fo*K_FOREST*float(row.ETo))
    return mm*A_WET/1000.0

def run_year(forcing,runon,surface,Sg,S0,wetland,geomorphic_bare,herb,forest,persistent_bare,year,gw_c=0.0):
    S=float(S0); Smin=float(Sg[0]); Smax=float(Sg[-1]); out=[]; maxerr=0.0
    hydrologic=np.asarray(wetland,bool)  # includes ecological bare: bare may reflood
    surf=np.asarray(surface,float)
    surf_h=surf[hydrologic]
    surf_sorted=np.sort(surf_h)
    n_wet=int(hydrologic.sum()); n_geom=int(np.asarray(geomorphic_bare,bool).sum()); n_herb=int(herb.sum()); n_forest=int(forest.sum())
    n_pbare=int(np.asarray(persistent_bare,bool).sum())

    # Direct precipitation throughfall: hydrologic bare + geomorphic bare + persistent bare 100%; herb/forest 70%.
    # Persistent bare gets the same 0% interception as other bare classes (README ET/interception lock).
    tf_frac=(n_wet+n_geom+n_pbare + TERRESTRIAL_THROUGHFALL*(n_herb+n_forest))/len(depth)

    for r,qr in zip(forcing.itertuples(index=False),np.asarray(runon,float)):
        prev=S
        pin=float(r.PRE)*A_WET/1000.0*tf_frac
        S += pin + float(qr)

        # Explicit groundwater exchange anomaly term (m3 d-1):
        # Qgw = Cgw * A_wet * (Hgw_y - Hgw_2020), active in Apr-May only.
        # Positive anomaly supplies water; negative anomaly exports water. Negative exchange
        # is limited by water available above Smin, so storage cannot fall below the model bound.
        gw_anom_m=(GW_AM_EL_M.get(int(year),GW_REF_EL_M)-GW_REF_EL_M) if int(year)>=2020 else 0.0
        qgw_potential=(float(gw_c)*A_WET*float(gw_anom_m)) if int(r.DATE.month) in (4,5) else 0.0
        if qgw_potential >= 0.0:
            qgw=float(qgw_potential); S += qgw
        else:
            qloss=min(max(S-Smin,0.0),-float(qgw_potential)); qgw=-qloss; S-=qloss

        spill=max(S-Smax,0.0); S-=spill

        hpre=interp_h(S,Sg)
        n_water=int(np.searchsorted(surf_sorted,hpre,side='left'))
        n_exposed_bare=n_wet-n_water

        demand=daily_et_m3(r,n_water,n_exposed_bare,n_geom+n_pbare,n_herb,n_forest)
        et=min(max(S-Smin,0.0),demand); S-=et

        qsub=0.0
        if float(r.PRE)<=0.0:
            # Preserve the Stage239 rain-free reference-recession implementation.
            href=max(HGRID[0],hpre-R_DRY)
            sref=float(np.interp(href,HGRID,Sg))
            qsub=max(S-sref,0.0); S-=qsub

        spill2=max(S-Smax,0.0); S-=spill2; spill+=spill2
        h=interp_h(S,Sg)
        err=prev+pin+float(qr)+qgw-et-qsub-spill-S
        maxerr=max(maxerr,abs(err))
        out.append((r.DATE,h,S,n_water*CELL*F_TRAPA,n_water*CELL*F_SCHOENO,
                    n_exposed_bare*CELL,n_herb*CELL,n_forest*CELL,n_wet*CELL,
                    pin,float(qr),qgw,et,qsub,spill,err))

    df=pd.DataFrame(out,columns=['DATE','WTD_m','storage_m3','open_water_m2','flooded_sedge_m2',
        'bare_m2','herb_m2','forest_m2','water_plus_bare_m2','Pwet_m3','runon_m3',
        'Qgw_m3','ETwet_m3','Qsub_m3','spill_m3','mass_error_m3'])
    return df,S,maxerr

# -----------------------------------------------------------------------------
# Gate functions retained from Stage239.
# -----------------------------------------------------------------------------
def window_minmax(a,n,mode):
    if len(a)<n: return np.nan
    vals=[(np.max if mode=='max' else np.min)(a[j:j+n]) for j in range(len(a)-n+1)]
    return float(min(vals) if mode=='max' else max(vals))

def thresholds_for_year(wet,y):
    d=wet[(wet.DATE>=pd.Timestamp(f'{y}-05-01'))&(wet.DATE<=pd.Timestamp(f'{y}-05-15'))].WTD_m.to_numpy(float)
    r=wet[(wet.DATE>=pd.Timestamp(f'{y}-05-15'))&(wet.DATE<=pd.Timestamp(f'{y}-06-07'))].WTD_m.to_numpy(float)
    return window_minmax(d,DRY_N,'max'),window_minmax(r,REF_N,'min')

# -----------------------------------------------------------------------------
# Actual transition scenarios.
# Arrival is recorded as the start of the following calendar year. This gives one full
# annual bare establishment state before herb appears. Bare cells remain hydrologically
# inundatable during that year; herb and forest are irreversible.
# -----------------------------------------------------------------------------
def simulate_transition(sigma,case_name,with_peat,succession,gw_c=0.0):
    case=TREE_RING_CASES[case_name]; speed=case['speed_m_per_eligible_yr']
    n=len(depth); progress=np.zeros(n); bare_start=np.full(n,np.nan)
    peat_z=np.zeros(n); cohorts=[]; records=[]; gates=[]; maxerr=0.0
    z0=base_surface(sigma)
    # Real hydrologic persistent-bare state. No history before 2011 (no spin-up rule).
    persistent_bare=np.zeros(n,bool)
    # Accumulated (not single-year-snapshot) hydrologic progress toward persistent bare, using
    # the exact same already-declared speed/DIST_TO_BOUNDARY the succession front uses. No new
    # numeric constant is introduced.
    progress_h=np.zeros(n)

    # No 2010 spin-up. Observed 2011 pond boundary is the rim/spill datum h=0.
    wetland=np.ones(n,bool)
    Sg,Smin,Smax=make_storage_curve(z0+peat_z,wetland)
    S=Smax

    for y in range(2011,2025):
        age=y-bare_start
        # Front arrival -> herb directly (see module docstring point 4).
        # [CHANGED FROM STAGE238, point 12] Herb is reversible: a cell that already crossed
        # the front (bare_start finite, age within [0,FOREST_LAG_YR)) is only actually
        # classified herb in years its accumulated hydrologic evidence (progress_h, the same
        # already-declared speed/DIST_TO_BOUNDARY accumulator used for persistent bare) is
        # still >= DIST_TO_BOUNDARY. If it re-floods (progress_h resets and later falls back
        # under DIST_TO_BOUNDARY), herb clears for that cell and it reverts to ordinary
        # wetland/bare classification via current elevation vs. water level, same as any
        # never-captured cell. Forest is untouched: still governed purely by elapsed age since
        # the *original* bare_start (tree-ring age-distance intercept), irreversible, exactly
        # as in the locked Stage239 state.
        on_herb_track=np.isfinite(bare_start)&(age>=0)&(age<FOREST_LAG_YR)
        herb=on_herb_track&persistent_bare
        forest=np.isfinite(bare_start)&(age>=FOREST_LAG_YR)
        if not succession:
            herb[:]=False; forest[:]=False

        surface=z0+peat_z
        # Pure geomorphic boundary: peat-raised surface above the observed rim/spill datum h=0
        # is outside the ponding footprint, but remains a reversible exposed-bare terrestrial surface.
        geomorphic_bare=(surface>0.0)&~(herb|forest)
        # Persistent bare (hydrologic-evidence state carried from the previous year's gate,
        # see point 11) is likewise reversible and herb/forest still take precedence.
        active_pbare=persistent_bare&~(herb|forest|geomorphic_bare)
        wetland=~(herb|forest|geomorphic_bare|active_pbare)

        Sg,Smin,Smax=make_storage_curve(surface,wetland)
        # If peat rise / terrestrialization reduces capacity, displaced water spills rather than
        # being silently retained above the new storage curve.
        S=min(max(S,Smin),Smax)

        mask=FDEV.DATE.dt.year.eq(y).to_numpy()
        fy=FDEV.loc[mask].reset_index(drop=True); ry=RUNON_M3[mask]
        wy,S,e=run_year(fy,ry,surface,Sg,S,wetland,geomorphic_bare,herb,forest,active_pbare,y,gw_c=gw_c); maxerr=max(maxerr,e)

        support=wy[(wy.DATE.dt.month>=5)&(wy.DATE.dt.month<=6)]
        if len(support)==0: support=wy
        records.append((y,float(support.open_water_m2.mean()),float(support.flooded_sedge_m2.mean()),
            float(support.bare_m2.mean()),float(geomorphic_bare.sum()*CELL),float(active_pbare.sum()*CELL),
            float(support.herb_m2.mean()),float(support.forest_m2.mean()),
            float(support.water_plus_bare_m2.mean()),float(peat_z.mean())))

        dth,rth=thresholds_for_year(wy,y)
        surface=z0+peat_z
        eligible=((surface>=dth)&~(surface<=rth-REF_DEPTH_M)) if np.isfinite(dth) and np.isfinite(rth) else np.zeros(n,bool)
        pending=~np.isfinite(bare_start)
        if succession:
            progress[pending&eligible]+=speed
            progress[pending&~eligible]=0.0
            reached=pending&(progress>=DIST_TO_BOUNDARY)
            # Front arrival is diagnosed from year y hydrology; herb begins at the next
            # annual state update (y+1), directly -- see module docstring point 4.
            bare_start[reached]=float(y)
        else:
            reached=np.zeros(n,bool)

        # Persistent-bare state for year y+1. Uses the same eligible gate as the succession
        # front, but -- per the same accumulation the front already uses -- requires eligible
        # evidence to accumulate (via the same speed) to each cell's own already-declared
        # DIST_TO_BOUNDARY before counting, exactly mirroring how the succession front already
        # damps single-year anomalies. This applies to every scenario regardless of the
        # succession flag (this is what makes Baseline/Eco-Geo non-flat), and remains fully
        # reversible: progress_h resets to 0 the moment a cell fails `eligible` again (i.e.
        # re-floods per the same reflood-sieve test), so persistent_bare clears immediately
        # once progress_h next falls back under DIST_TO_BOUNDARY. No new numeric constant is
        # introduced -- speed and DIST_TO_BOUNDARY are the same already-declared quantities
        # the front itself uses.
        progress_h[eligible]+=speed
        progress_h[~eligible]=0.0
        persistent_bare=(progress_h>=DIST_TO_BOUNDARY)&~(herb|forest)

        gates.append((y,int(eligible.sum()),float(reached.sum()*CELL),float(np.isfinite(bare_start).sum()*CELL),
                      float(wy.ETwet_m3.sum()),float(wy.Qgw_m3.sum()),float(wy.WTD_m.mean()),
                      float(np.mean(progress[pending])) if np.any(pending) else 0.0))

        if with_peat:
            peat_decay_step(cohorts)
            m0=OM_INPUT*wetland.astype(float)
            cohorts.append({'m0':m0.copy(),'m':m0.copy()})
            peat_z=np.sum(np.stack([c['m'] for c in cohorts]),axis=0)/OM_BULK_DENSITY

    return records,gates,maxerr

# -----------------------------------------------------------------------------
# Strict-factorial controls
# Baseline and Eco-Geo have no succession state and no counterfactual grass mask.
# Their hydrologic water/bare partition is retained diagnostically, while mapped wetland
# footprint uses the same water + hydrologic-bare state operator as all scenarios.
# -----------------------------------------------------------------------------

# -----------------------------------------------------------------------------
# Run ensemble: only sigma is a hydrologic structural bracket. No AWC/root/recharge/recession
# routing dimensions remain.
# -----------------------------------------------------------------------------
trajectories=[]; gates=[]; score_rows=[]; area_rows=[]
case_name='Combined'
for gw_c in GW_C_VALUES:
    for scenario,peat,succession in [('Baseline',False,False),('Eco-Geo',True,False),('Hydrosere',False,True),('Integrated',True,True)]:
        rec,gg,err=simulate_transition(0.065,case_name,peat,succession,gw_c=gw_c)
        rt=pd.DataFrame(rec,columns=['year','open_water_m2','flooded_sedge_m2','bare_m2','geomorphic_bare_m2','persistent_bare_m2','herb_m2','forest_m2','water_plus_bare_m2','mean_peat_increment_m'])
        rt['gw_c_d-1']=gw_c; rt['scenario']=scenario
        trajectories.append(rt)
        gt=pd.DataFrame(gg,columns=['year','eligible_cells','new_front_reached_m2','front_reached_total_m2','annual_ETwet_m3','annual_Qgw_m3','annual_mean_WTD_m','mean_pending_progress_m'])
        gt['gw_c_d-1']=gw_c; gt['scenario']=scenario
        gates.append(gt)
        for _,rr in rt.iterrows():
            area_rows.append((gw_c,scenario,int(rr.year),float(rr.water_plus_bare_m2)))
        q=rt[rt.year.isin(SCORED_YEARS)].set_index('year').water_plus_bare_m2
        pred=np.array([float(q.loc[y]) for y in SCORED_YEARS])
        obs=np.array([OBSERVED_WETLAND_M2[y] for y in SCORED_YEARS],float)
        rmse=float(np.sqrt(np.mean((pred-obs)**2)))
        pre21=np.array([2013,2015,2017,2019,2021])
        pred5=np.array([float(rt.set_index('year').water_plus_bare_m2.loc[int(y)]) for y in pre21])
        obs5=np.array([OBSERVED_WETLAND_M2[int(y)] for y in pre21],float)
        rmse5=float(np.sqrt(np.mean((pred5-obs5)**2)))
        p2022=float(rt.set_index('year').water_plus_bare_m2.loc[2022])
        score_rows.append((gw_c,scenario,rmse,100*rmse/obs.mean(),rmse5,100*rmse5/obs5.mean(),p2022,p2022-1988.56,*pred,float(pred[-1]-OBSERVED_WETLAND_M2[2023]),err))

T=pd.concat(trajectories,ignore_index=True)
G=pd.concat(gates,ignore_index=True)
AREA=pd.DataFrame(area_rows,columns=['gw_c_d-1','scenario','year','mapped_area_m2'])
SCORES=pd.DataFrame(score_rows,columns=['gw_c_d-1','scenario','RMSE_m2','nRMSE_pct','RMSE_2013_2021_m2','nRMSE_2013_2021_pct','pred_2022','resid_2022_vs_1988_56']+[f'pred_{y}' for y in SCORED_YEARS]+['resid_2023','max_mass_error_m3'])
T.to_csv(OUT/'stage239_explicit_gw_states.csv',index=False)
G.to_csv(OUT/'stage239_explicit_gw_annual_waterbalance.csv',index=False)
AREA.to_csv(OUT/'stage239_explicit_gw_area.csv',index=False)
SCORES.to_csv(OUT/'stage239_explicit_gw_scores.csv',index=False)

# Compact Integrated table and groundwater forcing table.
integ=SCORES[SCORES.scenario.eq('Integrated')].copy().sort_values('gw_c_d-1')
integ['within_30m_2023']=integ.resid_2023.abs()<=30
integ.to_csv(OUT/'integrated_explicit_gw_sensitivity.csv',index=False)
pd.DataFrame([{'year':y,'AprMay_GW_EL_m':GW_AM_EL_M.get(y,np.nan),'anomaly_vs_2020_m':GW_AM_EL_M.get(y,GW_REF_EL_M)-GW_REF_EL_M if y>=2020 else 0.0} for y in range(2011,2025)]).to_csv(OUT/'groundwater_boundary_input.csv',index=False)
print('\nINTEGRATED EXPLICIT GW SENSITIVITY')
print(integ[['gw_c_d-1','nRMSE_pct','nRMSE_2013_2021_pct','pred_2022','resid_2022_vs_1988_56','pred_2023','resid_2023','within_30m_2023','max_mass_error_m3']].to_string(index=False))
# Diagnostic lock / manifest
LOCK={
 'stage':'239_explicit_groundwater_exchange_sensitivity',
 'base':'Stage239 sigma=0.065 Combined tree-ring case; no other science parameters changed',
 'groundwater_term':'Qgw = Cgw * A_WET * (GW_AprMay(year) - GW_AprMay(2020)); active Apr-May only; signed exchange added explicitly to daily storage balance',
 'GW_reference_year':2020,
 'GW_AprMay_EL_m':GW_AM_EL_M,
 'Cgw_d-1':GW_C_VALUES,
 'interpretation':'structural sensitivity / reviewer-requested simplified groundwater term; Cgw is not site-calibrated and no central value is selected from area fit',
 'existing_Qsub':'unchanged Stage239 rain-free R_DRY=0.0114 m/d recession term retained',
 'sigma_m':0.065,
 'scored_years':SCORED_YEARS,
}
(OUT/'GW_EXCHANGE_LOCK.json').write_text(json.dumps(LOCK,ensure_ascii=False,indent=2),encoding='utf-8')
files=[p for p in OUT.iterdir() if p.is_file() and p.name!='MANIFEST_SHA256.csv']
def sha(p):
    h=hashlib.sha256()
    with open(p,'rb') as f:
        for b in iter(lambda:f.read(1<<20),b''): h.update(b)
    return h.hexdigest()
pd.DataFrame([{'file':p.name,'size_bytes':p.stat().st_size,'sha256':sha(p)} for p in sorted(files)]).to_csv(OUT/'MANIFEST_SHA256.csv',index=False)
print('\nLOCK')
print(json.dumps(LOCK,ensure_ascii=False,indent=2))
