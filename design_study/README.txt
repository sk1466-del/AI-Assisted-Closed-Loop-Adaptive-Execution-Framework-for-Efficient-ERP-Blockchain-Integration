Design study (Appendix A) - code as run in the working session.
ctrl6.py   : hysteresis, recovery hold, fairness guard, q80 forecast control, fluid-model MPC
setup6.py  : rebuilds state from the v5.2.1 notebook cells (build52.py) on the same block data
sim6.py, dev6.py, eval6.py : validation-only runs (20 dev seeds 5000+, rho 0.5/0.7/0.85/0.95) and capacity-dip runs
design_study_out.py : builds Table A1 and Fig. A1
NOTE: paths (/home/claude/..., scratchpad) are specific to the session and must be edited to run elsewhere.
This code is NOT merged into the v5.2.1 notebook yet, and has not been run on the held-out test or fresh data.
