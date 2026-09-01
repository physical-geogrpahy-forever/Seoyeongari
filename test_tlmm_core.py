#!/usr/bin/env python3
"""Regression tests against the official TLMM Springer workbook."""
from __future__ import annotations

from tlmm_core import (
    C_MIN_DEFAULT,W_MIN_DEFAULT,F_TEMPERATE_YR,S_GREAT_LAKES_EXAMPLE_YR,
    marsh_remaining_after_flooding,marsh_remaining_after_dewatering,
    lower_limit_step,upper_limit_step,boundary_history,
)


def close(a,b,tol=2e-14):
    if abs(float(a)-float(b))>tol:
        raise AssertionError((a,b,abs(float(a)-float(b))))


def main():
    f=F_TEMPERATE_YR; s=S_GREAT_LAKES_EXAMPLE_YR

    # Endpoint and monotonicity contracts.
    close(marsh_remaining_after_flooding(0,f),1.0)
    close(marsh_remaining_after_flooding(f,f),0.0)
    close(marsh_remaining_after_dewatering(0,s),1.0)
    close(marsh_remaining_after_dewatering(s,s),0.0)
    prev=1.0
    for k in range(0,6):
        q=marsh_remaining_after_flooding(k,f,C_MIN_DEFAULT)
        if q>prev+1e-14: raise AssertionError('flood response not monotone')
        prev=q
    prev=1.0
    for k in range(0,17):
        q=marsh_remaining_after_dewatering(k,s,W_MIN_DEFAULT)
        if q>prev+1e-14: raise AssertionError('upper response not monotone')
        prev=q

    # Exact cached values independently recovered from the authors' ESM:
    # combined Lake Erie sheet F105: dt=2, f=4, cmin=.01.
    close(marsh_remaining_after_flooding(2,4,.01),0.90909090909090917)
    # combined Lake Erie sheet K105: xt=4, s=15, wmin=.001.
    close(marsh_remaining_after_dewatering(4,15,.001),0.99468511166686502)
    # ESM upper factors at xt=12: J=.25118864315095801.
    # Hence K=(1-J)/(.999).
    close(marsh_remaining_after_dewatering(12,15,.001),(1-.25118864315095801)/.999)

    # Exact recurrence behavior.
    dt,F,mll=lower_limit_step(11.0,10.0,1,f_yr=4,cmin=.01)
    if dt!=2: raise AssertionError(dt)
    close(F,.90909090909090917)
    close(mll,11.0-F*(11.0-10.0))
    # Falling WL: duration resets and MLL follows the WL immediately.
    dt,F,mll=lower_limit_step(9.0,10.0,3,f_yr=4,cmin=.01)
    if dt!=0: raise AssertionError(dt)
    close(F,1.0); close(mll,9.0)

    xt,K,mul=upper_limit_step(9.0,10.0,3,s_yr=15,wmin=.001)
    if xt!=4: raise AssertionError(xt)
    close(K,.99468511166686502)
    close(mul,9.0-K*(9.0-10.0))
    # Rising WL: duration resets and MUL follows the WL immediately.
    xt,K,mul=upper_limit_step(11.0,10.0,7,s_yr=15,wmin=.001)
    if xt!=0: raise AssertionError(xt)
    close(K,1.0); close(mul,11.0)

    # First annual record initializes both boundaries to the first WL, as in
    # the official workbook; no fractional winter exposure input exists.
    h=boundary_history([2011,2012,2013],[5.0,4.0,3.0],f_yr=4,s_yr=15)
    close(h[0].marsh_lower_limit,5.0);close(h[0].marsh_upper_limit,5.0)
    if [r.xt_dewater_yr for r in h] != [0,1,2]: raise AssertionError(h)
    if [r.dt_flood_yr for r in h] != [0,0,0]: raise AssertionError(h)

    print('PASS_TLMM_CORE_EXACT_ESM_BOUNDARY_RECURSIONS')

if __name__=='__main__': main()
