# B7 U11 Validation Result Freeze


## U11 Validation Result Freeze — 2026-10-11

U11=COMPLETE_U11_VALIDATION_ONLY_FROZEN; U11ResultFrozen=true; U11ExecutionComplete=true; U11Executed=true; U11ExecutionAuthorized=false. ValidationPerformance=COMPLETE_FROZEN; ValidationCandidateCount40/PASS22/FAIL18/INSUFFICIENT_SAMPLE0. Formal Producer f763cfd25d79d59a1ba823de5493e8535c575e55; Candidate Freeze ebfe204d3561b064c1b4dc98d2fd417631dcc009. Actual /MyDrive/b7_u11_20261011_01_archive and checkpoint root passed COMPLETE, manifest, ZIP exact inventory/order/hash/Bytes/CRC/byte identity and40 jobs/121 trusted files, source unchanged. Producer Python3.13.16/NumPy2.3.5/pandas2.2.3; preflight855 tests and64 synthetic-schedule replays PASS. Earlier U11 NOT_RUN statements are implementation history, superseded by this audited formal result.

All40 sample sufficient. Formal failure counts (overlap): AvgPips5, MaxDDPips8, PFpips9, TotalPips2024 12, TotalPips2025 4.18 FAIL are performance-condition failures, not sample insufficiency. Six fail only2024 TotalPips. No period/weight/Gate changes. EURUSD PASS0/FAIL5; GBPUSD PASS0/FAIL2. GBPUSD Rank4 P1 PF1.0904444444443533 remains FAIL, no near-threshold rescue or P0 comparison. Rank7 P1 fails Avg/PF/both years. GBPAUD Rank2 P2 PASS. No Protection reselection, P1 deletion or P2 preference.

PASS22: AUDJPY4/EURAUD6/EURJPY4/GBPAUD3/GBPJPY5; AUDUSD/EURUSD/GBPUSD/USDJPY0. P0/P1/P2/P3=21/0/1/0. PASS boundary: minimum2024 Total36.19999999995071 EURAUD Rank6; minimum2025 Total157.49999999995964 GBPJPY Rank8; minimum Avg3.328260869565292 and PF1.2071858718451915, maximum DD/limit0.9820470109198551 AUDJPY Rank8 (265.2999999999997/270.1500000000009). Unrounded frozen rules PASS; no additional margin Gate.

Saved metrics/status arithmetic and selected Discovery DD×1.50 audited40/40 without M1 or performance recomputation. Selected trade/ID hashes and E2 ID hashes rehashed40/40. E2 baseline full streams were not persisted; their saved64hex hashes are authenticated by Producer checkpoint/archive identity, not reconstructed or replayed. Diagnostics/event aggregates are saved-result audits only, never Gates. See docs/b7/u11_result_freeze.md and results/b7/u11.

MonitorInputPrepared=true: research_inputs/b7/monitor_selected22_input.json is exactly the original-order PASS22 projection through unchanged project_monitor, all Candidate Freeze fields retained plus source candidate/checkpoint/Producer hashes and saved Validation metrics/stream hash. FAIL18 absent; no extra selection or sorting. Monitor [2026-01-01,2026-09-10) JST, OBSERVED_ONLY, ValidationOverrideAllowed=false, MonitorPerformanceEvaluated=false. MonitorImplementationAuthorized=false; MonitorExecutionAuthorized=false; MonitorExecuted=false; MonitorPerformance=NOT_RUN. No2026 price data read or Monitor trades/metrics/result generated. NoReplacement=true; PostValidationRetuningAllowed=false. Stop pending separate Monitor Implementation Only instruction.

## Source and integrity

Run b7_u11_20261011_01. Archive `/MyDrive/b7_u11_20261011_01_archive`; checkpoints `/MyDrive/b7_u11_20261011_01_checkpoints`. Trusted aggregate SHA256 `743fbc17f2b6ed4a1a9320b086fdf081e6d93194ba8d90050932a62b8bbc1061`. All14 archive files and13 ZIP members verified; all40 ordered candidate objects equal checkpoint sources. Source hashes unchanged before/after. Producer descends directly from Candidate Freeze. Input file/object hashes, six fingerprints, full U11 contract, calendar,72 M1 identities, spreads/pips/execution and exact producer environment are bound in input_identity; no M1 file content read for this Result Freeze.

## Pair status

| Pair | PASS | FAIL | INSUFFICIENT |
|---|---:|---:|---:|
| AUDJPY | 4 | 0 | 0 |
| AUDUSD | 0 | 0 | 0 |
| EURAUD | 6 | 1 | 0 |
| EURJPY | 4 | 4 | 0 |
| EURUSD | 0 | 5 | 0 |
| GBPAUD | 3 | 2 | 0 |
| GBPJPY | 5 | 3 | 0 |
| GBPUSD | 0 | 2 | 0 |
| USDJPY | 0 | 1 | 0 |

## PASS and FAIL exact inventory

Original U11 order retained. Full unrounded saved values are in pass_inventory.json/fail_inventory.json. Conditions remain unchanged.

| Pair | Rank | Mode | Status | Failed checks | CandidateID |
|---|---:|---|---|---|---|
| AUDJPY | 4 | P0 | PASS | none | `B7S1:AUDJPY:LONG:MON:E0765:D1:X0535:H1210` |
| AUDJPY | 5 | P0 | PASS | none | `B7S1:AUDJPY:LONG:MON:E0695:D1:X0530:H1275` |
| AUDJPY | 6 | P0 | PASS | none | `B7S1:AUDJPY:LONG:MON:E0675:D1:X0595:H1360` |
| AUDJPY | 8 | P0 | PASS | none | `B7S1:AUDJPY:LONG:MON:E0765:D1:X0610:H1285` |
| EURAUD | 1 | P0 | PASS | none | `B7S1:EURAUD:SHORT:MON:E0755:D1:X0365:H1050` |
| EURAUD | 2 | P0 | PASS | none | `B7S1:EURAUD:SHORT:MON:E1200:D1:X0365:H0605` |
| EURAUD | 3 | P0 | PASS | none | `B7S1:EURAUD:SHORT:MON:E1060:D1:X0365:H0745` |
| EURAUD | 4 | P0 | PASS | none | `B7S1:EURAUD:SHORT:MON:E1135:D1:X0365:H0670` |
| EURAUD | 5 | P0 | FAIL | TotalPips2024 | `B7S1:EURAUD:SHORT:MON:E1200:D1:X0425:H0665` |
| EURAUD | 6 | P0 | PASS | none | `B7S1:EURAUD:LONG:THU:E0365:D0:X0600:H0235` |
| EURAUD | 8 | P0 | PASS | none | `B7S1:EURAUD:SHORT:MON:E1100:D1:X0365:H0705` |
| EURJPY | 1 | P0 | FAIL | MaxDDPips, PFpips | `B7S1:EURJPY:LONG:MON:E0765:D1:X0720:H1395` |
| EURJPY | 2 | P0 | PASS | none | `B7S1:EURJPY:LONG:MON:E0425:D1:X0220:H1235` |
| EURJPY | 3 | P0 | FAIL | MaxDDPips | `B7S1:EURJPY:LONG:MON:E0730:D1:X0720:H1430` |
| EURJPY | 4 | P0 | FAIL | MaxDDPips | `B7S1:EURJPY:LONG:MON:E0765:D1:X0535:H1210` |
| EURJPY | 5 | P0 | PASS | none | `B7S1:EURJPY:LONG:MON:E0655:D1:X0355:H1140` |
| EURJPY | 6 | P0 | PASS | none | `B7S1:EURJPY:LONG:MON:E0610:D1:X0555:H1385` |
| EURJPY | 7 | P0 | FAIL | MaxDDPips | `B7S1:EURJPY:LONG:MON:E0715:D1:X0555:H1280` |
| EURJPY | 8 | P0 | PASS | none | `B7S1:EURJPY:LONG:MON:E0825:D1:X0720:H1335` |
| EURUSD | 1 | P0 | FAIL | AvgPips, PFpips, TotalPips2024 | `B7S1:EURUSD:LONG:TUE:E0365:D0:X1280:H0915` |
| EURUSD | 2 | P0 | FAIL | PFpips, TotalPips2024 | `B7S1:EURUSD:LONG:TUE:E0365:D0:X1155:H0790` |
| EURUSD | 4 | P0 | FAIL | AvgPips, MaxDDPips, PFpips, TotalPips2024, TotalPips2025 | `B7S1:EURUSD:LONG:TUE:E0365:D0:X1115:H0750` |
| EURUSD | 6 | P0 | FAIL | AvgPips, MaxDDPips, PFpips, TotalPips2024 | `B7S1:EURUSD:LONG:MON:E0945:D1:X0750:H1245` |
| EURUSD | 7 | P0 | FAIL | AvgPips, MaxDDPips, PFpips, TotalPips2024, TotalPips2025 | `B7S1:EURUSD:LONG:TUE:E0365:D0:X1245:H0880` |
| GBPAUD | 1 | P0 | FAIL | TotalPips2024 | `B7S1:GBPAUD:SHORT:MON:E1140:D1:X0370:H0670` |
| GBPAUD | 2 | P2 | PASS | none | `B7S1:GBPAUD:SHORT:MON:E1200:D1:X0370:H0610` |
| GBPAUD | 3 | P0 | PASS | none | `B7S1:GBPAUD:SHORT:MON:E1275:D1:X0370:H0535` |
| GBPAUD | 4 | P0 | PASS | none | `B7S1:GBPAUD:SHORT:MON:E1235:D1:X0370:H0575` |
| GBPAUD | 5 | P0 | FAIL | TotalPips2024 | `B7S1:GBPAUD:SHORT:WED:E0115:D0:X1370:H1255` |
| GBPJPY | 1 | P0 | PASS | none | `B7S1:GBPJPY:LONG:MON:E0820:D1:X0810:H1430` |
| GBPJPY | 2 | P0 | PASS | none | `B7S1:GBPJPY:LONG:MON:E0820:D1:X0755:H1375` |
| GBPJPY | 3 | P0 | FAIL | TotalPips2024 | `B7S1:GBPJPY:LONG:MON:E0765:D1:X0755:H1430` |
| GBPJPY | 4 | P0 | PASS | none | `B7S1:GBPJPY:LONG:MON:E0820:D1:X0720:H1340` |
| GBPJPY | 5 | P0 | FAIL | TotalPips2024 | `B7S1:GBPJPY:LONG:MON:E0765:D1:X0720:H1395` |
| GBPJPY | 6 | P0 | PASS | none | `B7S1:GBPJPY:LONG:MON:E0835:D1:X0790:H1395` |
| GBPJPY | 7 | P0 | FAIL | TotalPips2024 | `B7S1:GBPJPY:LONG:MON:E0730:D1:X0720:H1430` |
| GBPJPY | 8 | P0 | PASS | none | `B7S1:GBPJPY:LONG:MON:E0870:D1:X0810:H1380` |
| GBPUSD | 4 | P1 | FAIL | PFpips | `B7S1:GBPUSD:LONG:TUE:E0365:D0:X1120:H0755` |
| GBPUSD | 7 | P1 | FAIL | AvgPips, PFpips, TotalPips2024, TotalPips2025 | `B7S1:GBPUSD:LONG:TUE:E0370:D0:X1180:H0810` |
| USDJPY | 4 | P0 | FAIL | MaxDDPips, PFpips, TotalPips2025 | `B7S1:USDJPY:LONG:MON:E0835:D1:X0355:H0960` |

## Failed-check combinations

| Persisted key order | Count |
|---|---:|
| TotalPips2024 | 6 |
| MaxDDPips, PFpips | 1 |
| MaxDDPips | 3 |
| AvgPips, PFpips, TotalPips2024 | 1 |
| PFpips, TotalPips2024 | 1 |
| AvgPips, MaxDDPips, PFpips, TotalPips2024, TotalPips2025 | 2 |
| AvgPips, MaxDDPips, PFpips, TotalPips2024 | 1 |
| PFpips | 1 |
| AvgPips, PFpips, TotalPips2024, TotalPips2025 | 1 |
| MaxDDPips, PFpips, TotalPips2025 | 1 |

## Selected Protection and boundaries

```json
{
  "SelectedProtection": [
    {
      "AvgPips": 6.121276595745033,
      "CandidateID": "B7S1:GBPAUD:SHORT:MON:E1200:D1:X0370:H0610",
      "DDLimit": 617.6999999999846,
      "FailedChecks": [],
      "FormalProtectionMode": "P2",
      "PFpips": 1.4296915838996662,
      "PairRank": 2,
      "Status": "PASS",
      "Symbol": "GBPAUD",
      "TotalPips2024": 57.50000000000204,
      "TotalPips2025": 517.9000000000309,
      "ValidationDD": 260.4999999999972
    },
    {
      "AvgPips": 0.9690476190466751,
      "CandidateID": "B7S1:GBPUSD:LONG:TUE:E0365:D0:X1120:H0755",
      "DDLimit": 370.0500000000011,
      "FailedChecks": [
        "PFpips"
      ],
      "FormalProtectionMode": "P1",
      "PFpips": 1.0904444444443533,
      "PairRank": 4,
      "Status": "FAIL",
      "Symbol": "GBPUSD",
      "TotalPips2024": 35.99999999995286,
      "TotalPips2025": 45.399999999967804,
      "ValidationDD": 247.90000000001075
    },
    {
      "AvgPips": -2.1944444444452964,
      "CandidateID": "B7S1:GBPUSD:LONG:TUE:E0370:D0:X1180:H0810",
      "DDLimit": 554.4000000000315,
      "FailedChecks": [
        "AvgPips",
        "PFpips",
        "TotalPips2024",
        "TotalPips2025"
      ],
      "FormalProtectionMode": "P1",
      "PFpips": 0.8460038986354218,
      "PairRank": 7,
      "Status": "FAIL",
      "Symbol": "GBPUSD",
      "TotalPips2024": -136.40000000004306,
      "TotalPips2025": -61.10000000003362,
      "ValidationDD": 286.900000000074
    }
  ],
  "Boundaries": {
    "AvgPips": {
      "CandidateID": "B7S1:AUDJPY:LONG:MON:E0765:D1:X0610:H1285",
      "PairRank": 8,
      "Symbol": "AUDJPY",
      "Value": 3.328260869565292
    },
    "MaxDDRatio": {
      "CandidateID": "B7S1:AUDJPY:LONG:MON:E0765:D1:X0610:H1285",
      "DDLimit": 270.1500000000009,
      "PairRank": 8,
      "Symbol": "AUDJPY",
      "ValidationDD": 265.2999999999997,
      "Value": 0.9820470109198551
    },
    "PFpips": {
      "CandidateID": "B7S1:AUDJPY:LONG:MON:E0765:D1:X0610:H1285",
      "PairRank": 8,
      "Symbol": "AUDJPY",
      "Value": 1.2071858718451915
    },
    "TotalPips2024": {
      "CandidateID": "B7S1:EURAUD:LONG:THU:E0365:D0:X0600:H0235",
      "PairRank": 6,
      "Symbol": "EURAUD",
      "Value": 36.19999999995071
    },
    "TotalPips2025": {
      "CandidateID": "B7S1:GBPJPY:LONG:MON:E0870:D1:X0810:H1380",
      "PairRank": 8,
      "Symbol": "GBPJPY",
      "Value": 157.49999999995964
    }
  }
}
```

## Event saved-result recount

| Pair | E0 | E2 | Removed | Retention | Multi-event overlap |
|---|---:|---:|---:|---:|---:|
| AUDJPY | 376 | 372 | 4 | 0.9893617021276596 | 0 |
| EURAUD | 806 | 790 | 16 | 0.9801488833746899 | 0 |
| EURJPY | 761 | 746 | 15 | 0.9802890932982917 | 0 |
| EURUSD | 441 | 437 | 4 | 0.9909297052154195 | 0 |
| GBPAUD | 484 | 459 | 25 | 0.9483471074380165 | 0 |
| GBPJPY | 808 | 784 | 24 | 0.9702970297029703 | 0 |
| GBPUSD | 176 | 174 | 2 | 0.9886363636363636 | 0 |
| USDJPY | 93 | 93 | 0 | 1.0 | 0 |

Per-event removal counts are preserved in event_recount.json and independently match event_summary.json. Diagnostics rows exactly match saved Candidate diagnostics. WTL/Giveback/win rate/PF delta/retention/activation do not alter status. No metric recalculation from TradeResults.

## Monitor exact input only

Path `research_inputs/b7/monitor_selected22_input.json`; SHA256 `677aa3a9a18e9b8b46dcf7900ad9d4adbcc8a9bd0bf5e057b22e7e839fd434d2`; Bytes 260069; ObjectSHA256 `bd4eca4cf0aa5b0bace249ff61259f290f5c495d6f335fc71651a01b215bf3c9`. Ordered unique22 equals the original40 filtered by Validation PASS. No performance sort or pair sort. All immutable fields unchanged, exact saved metrics object, actual candidate/checkpoint hashes and selected stream hash. PASS22 counts21/0/1/0 Protection and pair counts above. U11ResultFreezeReference is the containing Git commit to avoid a circular self-hash. Future Monitor must bind this Result Freeze SHA. Monitor remains NOT_RUN; its OBSERVED_ONLY value is prospective input metadata, not a generated result.

## Actual source artifact SHA256 and Bytes

| Artifact | Bytes | SHA256 |
|---|---:|---|
| COMPLETE.json | 208 | `06ff2eeef2b8ff1b82186de8c9fa9a1bc9b35c22dc7740af0012265639606fc4` |
| archive.zip | 703783 | `581e3c073fced4abaedb57d6d4e0b1fa51abe385abbdfc68a6fd688007c513fc` |
| artifact_manifest.json | 1331 | `174cb8ad051da485059e160c8ac4d11ebb0de5f99ddf815a16ce2aa4876b34ae` |
| candidate_results.json | 5210379 | `1a9e70d18ea1a36a4b8d4a3887b866bc4f14525368b93f4d83f15d63cee667cf` |
| checkpoint_audit.json | 5892 | `c59ae11d0efc3b5f119d44dfc19edb3606e29a9211867460052b2752eb3cd4ed` |
| diagnostic_summary.json | 37927 | `853d205616902d973df1c2eb7b030fc5eb1a8e36b409ef378fdbd97bac09533b` |
| event_summary.json | 14638 | `8dd80bcfe1d3d6c644caea922a6806096498f79d9331fcd7d3c774e591b308e7` |
| formal_check_summary.json | 285 | `3a87746152a0d3697f2b52497b3b85aefaf44a31e9061d2e6fb88eff0802c394` |
| input_identity.json | 64128 | `65469b37d48d92b894e2d650baef3067e11f2c9c1ca13b65abf88a009523d8d0` |
| pair_summary.json | 426 | `bdc5feca1d9b8ab9bcf6fac67866e6e221451f79b50de7d8d5f33a2d7efff607` |
| preflight.json | 64926 | `69f854b843c8bcefbfdea41a7e6e4a6a5ead3c8e76246d338dfe3ae5664302ec` |
| review.json | 175 | `3359d952c4ec2cce4963fdd3885fade89742693a1565c568ff7a19f8189dd3d1` |
| sample_summary.json | 98 | `a7d37854371082ade022adcc33dd1b24970bf38eafe9f7f66abb5b91d6c3099f` |
| status_summary.json | 98 | `3d37e5f9bcc111fda9db2c642d8ea0e3e17fefb7a17f7cc9837193042da0ad56` |

candidate_results.json and archive.zip stay in Drive; other source artifacts are copied byte-identically. Full immutable Producer and Candidate Freeze release manifests remain historical snapshots, including their historical documentation hashes. Current Result Freeze github_artifact_manifest binds current documents/status. Earlier mutable release memberships unchanged; only dependent SHA/Bytes refreshed. Existing production code/tests/notebooks/inputs/results/conditions unchanged. Main/B6/EA/SET/VPS/live/forward/Global R2/portfolio unchanged.

Tests Total 873 / PASS 873 / FAIL 0 / ERROR 0 / SKIP 0. Added tests are synthetic persisted-arithmetic/projection checks; no formal replay. Work test environment {'Python': '3.12.14', 'NumPy': '2.3.5', 'pandas': '2.2.3'}.
