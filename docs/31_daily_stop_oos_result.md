# Daily Stop Frozen OOS Result

Status: COMPLETE — Daily Stop not adopted for the profit objective

Decision date: 2026-09-09 JST

Frozen threshold: `-4R`

Input Trade Log SHA-256:

```text
cc32f32e3df57cb03416d111e3cf848fb6b2edc7f193b6da90201a2462420359
```

The threshold was selected from IS before OOS was calculated. It was not changed after OOS was viewed.

## Result by segment

| Segment | Baseline R | -4R Stop R | Delta R | Delta % | Baseline PF | Stop PF | Baseline Max DD | Stop Max DD | Blocked |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| IS | 768.488273 | 770.737662 | +2.249388 | +0.292703% | 1.372171 | 1.377502 | 27.540956 | 27.540956 | 62 |
| OOS1 | 601.960585 | 603.002779 | +1.042194 | +0.173133% | 1.489975 | 1.494546 | 22.196976 | 18.583552 | 25 |
| OOS2 | 19.818791 | 19.147630 | -0.671162 | -3.386493% | 1.095529 | 1.092309 | 18.954206 | 18.954206 | 3 |
| OOS combined | 621.779376 | 622.150409 | +0.371033 | +0.059673% | 1.432989 | 1.436065 | 22.196976 | 18.954206 | 28 |
| Full | 1390.267649 | 1392.888070 | +2.620421 | +0.188483% | 1.397117 | 1.401592 | 27.540956 | 27.540956 | 90 |

## OOS consistency

The yearly OOS Delta R was:

| Year | Delta R |
|---:|---:|
| 2022 | -1.970119 |
| 2023 | +2.288980 |
| 2024 | -0.469333 |
| 2025 | +1.192667 |
| 2026 through 2026-09-09 | -0.671162 |

Two OOS years improved and three deteriorated. The OOS-combined gain was only 0.371033R, or 0.059673% of the baseline result. Avoided losses were 9.280889R and missed profits were 8.909856R.

## Risk observations

OOS1 Max DD improved from 22.196976R to 18.583552R. Its worst day improved from -10.880000R to -7.880000R and its worst week improved from -12.824402R to -9.210977R. OOS2 Max DD, worst day and worst week were unchanged.

These tail-risk improvements are real within this simulation, but they do not establish a repeatable increase in profit. The original research question was whether Daily Stop increases profit amount, and the predeclared rule treats a mixed OOS result as insufficient.

## Final decision

Daily Stop is not adopted for the current 28-strategy portfolio. The no-Daily-Stop Baseline remains the official configuration.

- Do not retune the threshold after OOS.
- Do not add a post-hoc `-3.5R` or another threshold.
- Do not change EA, VPS, SET or live-operation code.
- The risk-reduction observation may be retained as research evidence, but any future risk-control study must be separately predeclared.
