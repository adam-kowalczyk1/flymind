# Pilot analysis (exploratory; seeds 100–129, t_occ = 1.0 s)

## Reconciliation

records 240; planned primary 180 + diagnostic 60; missing 0; duplicates 0

## Per condition

| variant | completed | SUCCESS | CONTROL_FAILURE | DEGENERATE_CALIBRATION | TECHNICAL_FAILURE | n_valid_endpoint | abs_e_mean | abs_e_sd | abs_e_median | abs_e_q25 | abs_e_q75 | signed_e_mean | abs_e_mean_all_records | abs_e_onset_mean | delta_ball_mean | delta_aim_mean | t_reacq_n_defined | j_ctrl_mean | j_ctrl_n_zero | abs_e_ring_mean | n_ring_valid |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| BIO-Static | 30 | 20 | 10 | 0 | 0 | 30 | 15.07 | 7.82 | 15.34 | 9.42 | 21.57 | -15.07 | 15.07 | 4.54 | -13.48 | 4.79 | 2 | 0.12 | 0 | 22.00 | 30 |
| BIO-Hybrid | 30 | 25 | 5 | 0 | 0 | 30 | 13.15 | 6.05 | 12.49 | 9.38 | 16.59 | -9.81 | 13.15 | 4.42 | -13.48 | -0.37 | 7 | 0.12 | 0 | 15.75 | 30 |
| BIO-NoSelf | 30 | 15 | 15 | 0 | 0 | 30 | 17.80 | 9.52 | 19.28 | 12.31 | 22.84 | -17.09 | 17.80 | 3.81 | -13.48 | 6.62 | 6 | 0.14 | 0 | 34.24 | 30 |
| BIO-Shuffle | 30 | 0 | 0 | 30 | 0 | 0 | — | — | — | — | — | — | 10.96 | 5.37 | -13.48 | -0.01 | 0 | — | 0 | — | 0 |
| LastObs-PD | 30 | 30 | 0 | 0 | 0 | 30 | 14.58 | 1.31 | 14.68 | 13.60 | 15.32 | -14.58 | 14.58 | 1.09 | -13.48 | 1.72 | 0 | 0.00 | 0 | — | 0 |
| Kalman-PD | 30 | 30 | 0 | 0 | 0 | 30 | 5.86 | 1.07 | 5.59 | 4.98 | 6.37 | -5.86 | 5.86 | 0.81 | -13.48 | -7.58 | 1 | 0.03 | 0 | — | 0 |
| LastObs-Freeze-Diag | 30 | 30 | 0 | 0 | 0 | 30 | 12.85 | 2.10 | 12.77 | 11.58 | 13.76 | -12.85 | 12.85 | 1.09 | -13.48 | -0.00 | 0 | 0.00 | 30 | — | 0 |
| BIO-Static-Freeze-Diag | 30 | 28 | 2 | 0 | 0 | 30 | 10.27 | 4.72 | 8.99 | 6.81 | 12.84 | -10.27 | 10.27 | 4.54 | -13.48 | -0.00 | 1 | 0.00 | 30 | 25.89 | 30 |

## Paired contrasts D = |e_A| − |e_B| (deg; negative = A better)

| role | A | B | n_pairs | mean_D | sd_D | t_ci95_lo | t_ci95_hi | t_upper95_onesided | boot_ci95_lo | boot_ci95_hi | hl | hl_boot_lo | hl_boot_hi | wilcoxon_p | frac_A_better |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| NI-1 | BIO-Static | LastObs-PD | 30 | 0.49 | 7.98 | -2.49 | 3.47 | 2.97 | -2.31 | 3.26 | 0.42 | -2.29 | 3.79 | 0.78 | 0.47 |
| NI-2 | BIO-Hybrid | Kalman-PD | 30 | 7.29 | 5.95 | 5.07 | 9.51 | 9.14 | 5.17 | 9.42 | 7.26 | 4.85 | 9.34 | 0.00 | 0.10 |
| mech-self | BIO-Static | BIO-NoSelf | 30 | -2.73 | 9.57 | -6.31 | 0.84 | 0.23 | -6.05 | 0.55 | -2.46 | -6.36 | 1.47 | 0.31 | 0.50 |
| mech-velocity | BIO-Hybrid | BIO-Static | 30 | -1.91 | 9.04 | -5.29 | 1.46 | 0.89 | -5.05 | 1.42 | -2.16 | -5.19 | 1.05 | 0.21 | 0.60 |
| freeze-BIO | BIO-Static | BIO-Static-Freeze-Diag | 30 | 4.80 | 8.44 | 1.64 | 7.95 | 7.42 | 1.82 | 7.73 | 4.70 | 1.37 | 7.85 | 0.01 | 0.27 |
| freeze-LastObs | LastObs-PD | LastObs-Freeze-Diag | 30 | 1.72 | 1.09 | 1.31 | 2.13 | 2.06 | 1.35 | 2.10 | 1.68 | 1.27 | 2.15 | 0.00 | 0.03 |
| freeze-vs-BIOHybrid | BIO-Hybrid | BIO-Static-Freeze-Diag | 30 | 2.88 | 7.07 | 0.24 | 5.52 | 5.07 | 0.43 | 5.42 | 2.74 | 0.04 | 5.30 | 0.05 | 0.33 |
| context | Kalman-PD | LastObs-PD | 30 | -8.72 | 1.57 | -9.30 | -8.13 | -8.23 | -9.25 | -8.14 | -8.77 | -9.39 | -8.31 | 0.00 | 1.00 |
| shuffle-descriptive | BIO-Static | BIO-Shuffle | 30 | 4.11 | 9.85 | 0.43 | 7.78 | 7.16 | 0.72 | 7.64 | 3.68 | 0.44 | 7.17 | 0.03 | 0.33 |
