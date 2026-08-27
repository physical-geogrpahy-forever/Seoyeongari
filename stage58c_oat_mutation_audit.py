#!/usr/bin/env python3
"""Stage58c — detect whether Stage58 OAT loops mutate central state/coefficients."""
from __future__ import annotations
import copy, json
from pathlib import Path
import numpy as np
import stage57_aprmay_four_scenario_peat as s57
import stage58_aprmay_oat_provenance as s58

OUT=Path('stage58c_outputs'); OUT.mkdir(exist_ok=True)


def snap():
    cc,st=s58.central_coefficients(); h,S,H,G,corr=st
    metrics=[]
    for name,b in cc.items():
        pr=s58.predict(name,S,H,G,b['Kc'],b['Kh']); rm,nr=s57.metric(pr)
        metrics.append({'Scenario':name,'RMSE_m2':float(rm),'nRMSE_pct':float(nr),'Kc':float(b['Kc']),'Kh':float(b['Kh'])})
    metrics.sort(key=lambda z:z['Scenario'])
    return {'cc':copy.deepcopy(cc),'S':S.copy(),'H':H.copy(),'G':G.copy(),'V':np.asarray(h['V']).copy(),'metrics':metrics}


def maxdiff(a,b): return float(np.max(np.abs(np.asarray(a,float)-np.asarray(b,float))))


def main():
    before=snap()
    # Execute exactly the Stage58 OAT rows without writing a second full summary.
    for p,vals in s58.OAT.items():
        for v in vals:
            s58.rows_for(p,v,'fixed',before['cc'])
            s58.rows_for(p,v,'profile_refit',before['cc'])
    after=snap()
    diffs={
      'V_max_abs':maxdiff(before['V'],after['V']),
      'S_max_abs':maxdiff(before['S'],after['S']),
      'H_max_abs':maxdiff(before['H'],after['H']),
      'G_max_abs':maxdiff(before['G'],after['G']),
      'cc_max_abs':max(abs(before['cc'][k][q]-after['cc'][k][q]) for k in before['cc'] for q in ['Kc','Kh']),
      'metric_nrmse_max_abs':max(abs(a['nRMSE_pct']-b['nRMSE_pct']) for a,b in zip(before['metrics'],after['metrics'])),
    }
    status='PASS_NO_OAT_MUTATION' if max(diffs.values())<=1e-12 else 'FAIL_OAT_MUTATION'
    summary={'status':status,'differences':diffs,'before_metrics':before['metrics'],'after_metrics':after['metrics']}
    (OUT/'stage58c_summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(summary,ensure_ascii=False,indent=2))
    if status!='PASS_NO_OAT_MUTATION': raise SystemExit('OAT loop mutated central state')

if __name__=='__main__': main()
