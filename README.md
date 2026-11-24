# AI-Assisted Closed-Loop Adaptive Execution Framework for ERP–Blockchain Integration: code and results

Archived version: https://doi.org/10.5281/zenodo.24496441

This repository accompanies the manuscript *AI-Assisted Closed-Loop Adaptive Execution Framework for Efficient ERP–Blockchain Integration*.
It contains one definitive configuration: **code version v5.2.1, design hash `d6c30b92b47d5336`**. The files below provide the results and the analysis scripts behind the tables and figures of the manuscript and Supplementary Material; `check_numbers.py` independently recomputes the key numerical entries.
Earlier notebooks, results and figures (v1–v5, including the “trained once, then multiplied by fixed factors” notebook) are **not** part of this release and should not be used.

## What is simulated
A trace-driven queue simulator replays 66,532 real Bitcoin blocks (heights 610,691–677,222; 2020-01-01 to 2021-03-31; 66,491 usable after rolling features). Chronological split with a six-block embargo: train 39,999 / validation 13,175 / test 13,305 blocks. The observation unit is one block. The ERP workload (class mix 10/60/30 %, sizes, 50 % off-loadable payloads, 3,600 s SLA) is an assumption. All latencies come from the executed queue; no result is obtained by transforming predictions. The test period was re-used during design (v1–v5.2.1): the manuscript calls it the reused evaluation period; it is not independent. Some notebook labels and result-file strings still say "held-out test" for the same period.

## Reproduce
1. `pip install numpy pandas scikit-learn pyarrow matplotlib` (Python 3.10+; the notebooks were run in Google Colab).
2. Check the released numbers: `python check_numbers.py` independently recomputes the key numerical entries listed below from `results/` and `delay_experiment/` and compares them with the manuscript; the CSV files and notebooks are the results and analysis scripts behind the reported tables and figures (prints PASS/FAIL per entry and the number of failures).
3. Re-run: execute the notebooks in `notebooks/` in this order: `..._MAIN_wording_fix.ipynb` (data, forecasting, main comparison), `..._ADDENDUM.ipynb`, `..._STRESS_ADDENDUM2.ipynb` (bursts, capacity dips, fairness, sensitivity). Each run prints the design hash; it must equal `d6c30b92b47d5336`.

## Where each manuscript item comes from
| Manuscript item | Script / notebook | Results file(s) |
|---|---|---|
| Table 1 (splits, simulator, regimes) | MAIN notebook | `dataset_audit.json`, `RESULTS_SUMMARY.json` |
| Table 2A forecast accuracy | MAIN notebook | `table_prediction_B.csv`, `table_prediction_block_bootstrap.csv` |
| Table 2B forecast ablations at matched off-chain share (pairs and intervals: Supp. Table S5b) | MAIN notebook | `table_matched_pairs.csv` |
| Table 2C recalibration | MAIN / ADDENDUM | `table_closed_loop_modes.csv`, `table_closed_loop_stress.csv` |
| Table 3A, 3B main comparison | MAIN notebook | `sim_raw_results.csv`, `table_pairwise_comparisons.csv`, `table_fairness.csv` |
| Table 4A overload (3 seeds) | ADDENDUM notebook | `table_completed_tps_overload.csv` |
| Table 4B bursts, Table S6, Table S6b (intervals) | STRESS_ADDENDUM2 | `table_bursty.csv`, `table_bursty_paired.csv` |
| Table 4C, Fig. 6 capacity dips | STRESS_ADDENDUM2 | `table_capacity_dip.csv`, `table_capacity_dip_paired.csv` (intervals: Supp. Table S6b) |
| Table 5A fairness and starvation | STRESS_ADDENDUM2 | `table_fairness.csv`, `table_fairness_raw.csv` |
| Table 5B sensitivity ranges | ADDENDUM notebook | `table_sensitivity_ranges.csv` (per-variant rows: `table_sensitivity_low_loads.csv`, `table_sensitivity_simulator.csv`) |
| Overhead (Sec. 4.4) | MAIN notebook | `table_overhead.csv` |
| Claims scorecard (Table S2) | all notebooks | `CLAIMS_SCORECARD.csv`, `CLAIMS_SCORECARD_ADDENDUM.csv` |
| Simulator validation (Table S3) | MAIN notebook | `table_sanity_tests.csv`, `table_analytical_validation.csv` |
| Controller design study (Sec. 4.5, Table S1, Fig. S1) | `design_study/` | `design_study/table_design_study_validation.csv` |
| Delayed activation (Sec. 4.6, Table 6, Supp. S8; exploratory: common off-chain-share cap, not a matched comparison) | `delay_experiment/` | `frontier_k{0,2,5,10}.csv`, `confirm_k{0,2,5,10}.csv` |
| Fresh-period confirmation (not run) | `fresh_period/fetch_fresh_period.py` | none yet |
| Figures | `figures/` (`make_*.py` and the PNG/PDF used) | — |

## Known gaps (do not claim these as reproduced)
- The delayed-activation experiment uses assumed delays and the validation period only.
- `table_*POSTHOC.csv` files are post-hoc analyses made after the test period had been inspected; they are not pre-specified results.
- No fresh-period (independent) confirmation has been run (`fresh_period/fetch_fresh_period.py` is provided).
- Nothing here is measured on Hyperledger Fabric, Ethereum or Quorum; deployment mappings are proposals.
- `check_numbers.py` covers the design hash; Tables 2A, 3A, 3B, 4A, 4B, 4C, 5A (LOW starvation rate and maximum LOW wait for every policy at all four loads), 5B and 6; the matched-pair counts of Table 2B; one interval of Supplementary Table S6b; the decision-divergence percentages of Supplementary Table S2; and the off-chain reductions of ADAPTIVE against BEST_FIXED in the bursty scenarios (Table 4B and Supplementary Table S6, base loads 0.3 and 0.6; the script also prints the value for every scenario). Each section runs in its own guard, so an error in one section is reported and counted as a failure without stopping the others, and the summary (`CHECKS RUN`, `FAILED`) and exit statement are the last lines of the script. It does not recompute the design-study table (Table S1), the claims scorecard as a whole (only the two groups of values named above) or the overhead numbers; these are read from the notebook outputs and result files.

## Citation and licence
Please cite the manuscript above and the archived version (Zenodo DOI above). The code is released under the MIT licence (`LICENSE`); the results files and figures are released under CC BY 4.0.

## Version history
- v5.2.1 (this release): code, configuration and results as reported in the manuscript (design hash `d6c30b92b47d5336`). In the second revision only documentation and `check_numbers.py` changed: the summary and exit statement were moved to the end of the script so that every check runs, and checks for Supplementary Tables S2 and S6 and for Table 5A at all loads were added. No experiment or result changed.
