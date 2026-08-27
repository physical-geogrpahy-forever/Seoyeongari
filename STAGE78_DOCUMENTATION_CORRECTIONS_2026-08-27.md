# Stage78 documentation corrections — 2026-08-27

This file records two corrections discovered during manuscript synchronization. They correct documentation/handoff descriptions only; the executed Stage78 calculations are unchanged.

## 1. `hydro_window_d`

The executed `eghm_deterministic_kernel.py` has:

`hydro_window_d = 14`

Stage78 calls this kernel value directly. Therefore `H` is based on a causal trailing **14-day** sum of fast + slow local-return flow.

The v7 handoff `CURRENT_STATE_v7.json` entry `hydro_window_d = 60` is erroneous metadata. Do not propagate it. `tau_surf = 60 d` remains the correct surface-drainage residence time.

## 2. Integrated exposure basis

A generic hydrology-only exposure equation is sufficient for Hydrosere Only but incomplete for the accepted Integrated Stage78 calculation.

The actual causal coupled ordering inherited from Stage77 is:

1. `f_peat(t) = clamp[1 - A_terr(t-1)/A0, 0, 1]`
2. `G_eff(t) = f_peat(t) * G_wet(t)`
3. `A_exposure(t) = max[A_hyd(t) - G_eff(t), 0]`
4. `e(t) = clamp[(A0 - A_exposure(t))/A0, 0, 1]`
5. `D(t) = D(t-1) + e(t)/365`
6. `A_terr(t) = clamp[beta_D D(t), 0, A0]`

Thus previous terrestrialization reduces the remaining wet peat-forming fraction, and residual peat surface expression contributes to the exposure basis used to update cumulative terrestrialization.

This is an eco-geomorphic area-partition feedback in the modeled surface-expression subsystem. It does **not** modify the conserved hydrologic storage recurrence.

For manuscript synchronization details, see `STAGE78_MANUSCRIPT_SYNC_PATCH.md`.
