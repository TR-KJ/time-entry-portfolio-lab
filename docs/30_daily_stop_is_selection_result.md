# Daily Stop IS Selection Result

Status: `-4R` frozen for one OOS test; not accepted for production

Selection date: 2026-09-09 JST

Input Trade Log SHA-256:

```text
cc32f32e3df57cb03416d111e3cf848fb6b2edc7f193b6da90201a2462420359
```

OOS1 and OOS2 were not calculated or viewed during this selection.

## IS comparison (2015-2021)

| Rule | Total R | Delta R | PF | Max DD (R) | Worst day (R) | Worst week (R) | Blocked trades |
|---|---:|---:|---:|---:|---:|---:|---:|
| None | 768.488273 | 0.000000 | 1.372171 | 27.540956 | -12.000000 | -14.455836 | 0 |
| -1R | 637.875116 | -130.613158 | 1.360615 | 26.722450 | -7.261429 | -10.457477 | 1,254 |
| -1.5R | 725.935610 | -42.552664 | 1.379756 | 25.710058 | -7.261429 | -10.719321 | 613 |
| -2R | 732.050072 | -36.438202 | 1.373022 | 26.415914 | -7.261429 | -10.719321 | 424 |
| -2.5R | 748.501001 | -19.987272 | 1.371013 | 27.373692 | -7.261429 | -10.719321 | 200 |
| -3R | 757.940936 | -10.547337 | 1.373828 | 27.662855 | -7.261429 | -10.922483 | 138 |
| -4R | 770.737662 | +2.249388 | 1.377502 | 27.540956 | -7.261429 | -10.800584 | 62 |

For `-4R`, avoided losses were 23.204408R and missed profits were 20.955020R; their difference equals the reported +2.249388R. Total R improved by only 0.292703%.

## Frozen decision

`-4R` is the only predeclared Daily Stop threshold with positive IS Delta R, and it modestly improves PF, worst day and worst week. It is therefore frozen as the sole candidate for one OOS report.

This is weak IS evidence, not a production adoption:

- Max DD is unchanged.
- The Total R gain is small.
- `-3R` loses 10.547337R, so there is no broad profitable plateau around the selected boundary.
- The yearly `-4R` Delta R is positive in 2015, 2018, 2020 and 2021; negative in 2016 and 2019; and zero in 2017.
- No intermediate threshold such as `-3.5R` may be added after seeing these results.

## Predeclared OOS interpretation

- `-4R` is run once, unchanged, on OOS1 (2022-2025) and OOS2 (2026 through 2026-09-09).
- OOS1 is the primary multi-year confirmation. For the profit objective, its Delta R must be positive.
- OOS1+OOS2 combined must also have positive Delta R and the conclusion must not depend only on the shorter OOS2 period.
- Max DD, worst day and worst week are supporting risk measures; they cannot override a negative OOS profit result.
- A negative or merely mixed OOS result means evidence is insufficient and Daily Stop is not adopted. The threshold is not retuned.

## Final outcome

The frozen OOS run is recorded in `docs/31_daily_stop_oos_result.md`. OOS was mixed and the combined profit improvement was only 0.059673%, so Daily Stop was not adopted and no threshold was retuned.
