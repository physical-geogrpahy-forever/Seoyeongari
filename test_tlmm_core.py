#!/usr/bin/env python3
from __future__ import annotations

from tlmm_core import (
    C_MIN_DEFAULT,W_MIN_DEFAULT,F_TEMPERATE_YR,S_GREAT_LAKES_EXAMPLE_YR,
    marsh_remaining_after_flooding,marsh_remaining_after_dewatering,
    band_history,assert_partition,
)


def close(a,b,tol=1e-12):
    if abs(a-b)>tol: raise AssertionError((a,b))


def main():
    f=F_TEMPERATE_YR; s=S_GREAT_LAKES_EXAMPLE_YR
    close(marsh_remaining_after_flooding(0,f),1.0)
    close(marsh_remaining_after_flooding(f,f),0.0)
    close(marsh_remaining_after_dewatering(0,s),1.0)
    close(marsh_remaining_after_dewatering(s,s),0.0)
    prev=1.0
    for k in range(0,5):
        q=marsh_remaining_after_flooding(k,f,C_MIN_DEFAULT)
        if q>prev+1e-12: raise AssertionError('flood curve not monotone')
        prev=q
    prev=1.0
    for k in range(0,16):
        q=marsh_remaining_after_dewatering(k,s,W_MIN_DEFAULT)
        if q>prev+1e-12: raise AssertionError('dewatering curve not monotone')
        prev=q

    # Initially mapped open water remains aquatic while September water level
    # stays above the elevation.
    h=band_history([2011,2012],[1.0,1.0],0.5,f_yr=f,s_yr=s)
    close(h[0].marsh_fraction,0.0); close(h[1].marsh_fraction,0.0)
    assert_partition(h)

    # A first dewatered growing season produces nearly complete marsh, then
    # woody succession increases only while dewatering continues.
    h=band_history([2011,2012,2013,2014],[1.0,0.0,0.0,0.0],0.5,f_yr=f,s_yr=s)
    if not (h[1].marsh_fraction > 0.99 and h[2].woody_fraction > h[1].woody_fraction):
        raise AssertionError(h)
    assert_partition(h)

    # Winter-only exposure is not an input to TLMM here: the annual driver is
    # the published growing-season water-level series. If September remains
    # flooded, no dewatering year is accumulated.
    h=band_history([2011,2012,2013,2014],[1.0,1.0,1.0,1.0],0.5,f_yr=f,s_yr=s)
    if any(r.xt_dewater_yr != 0.0 for r in h): raise AssertionError(h)
    print('PASS_TLMM_CORE_PUBLISHED_EQUATIONS')

if __name__=='__main__': main()
