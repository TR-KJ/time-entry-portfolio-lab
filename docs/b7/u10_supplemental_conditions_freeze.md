# B7 U10 Supplemental Conditions Freeze — U10-S01

Pre-performance resolution of AUD CPI calendar source ambiguity. Original conditions, U09 Result and U10 input remain unchanged.

B7 canonical event AUD_CPI reads the final AUD_CPI_DATES array from source commit 173be2a114dad6bd183a0a1515581528850f0850, path src/portfolio_backtest_v1_2_add_aussie_logic.py. Source blob f087a22554fb920e2c7230b0626e72f654376358; SHA256 4b71f6b7b1cdbe3266cd9b7cefae37811781561016a013a34d7c8c84247ef32d. Initial44 + AUD_CPI_2026_DATES4 = final48; Discovery16 exact dates are preserved in the supplemental prespec. The same source has no AU_CPI_DATES definition. Legacy event_filter_validation_v1.py queries that undefined name for AU_CPI and returns an empty set; this lookup must not be reused. B7 reads its frozen calendar artifact, never the legacy resolver.

Same JST date,10:30,±120 minutes inclusive,no DST. AUD_CPI is added to E2 only for AUDJPY,AUDUSD,EURAUD,GBPAUD. No legacy event alias, Candidate C matrix, strategy override or date_all_day rule. The other seven events retain their frozen semantics. This identifies the existing array; no date correction, supplementation, replacement or historical reconstruction.

No formal U10 result viewed=true; U10Executed=false; ValidationPerformance=NOT_RUN; MonitorPerformance=NOT_RUN. This conditions-only commit precedes implementation. Its commit SHA and supplemental prespec SHA256 must be bound by U10 implementation/runtime identity.

Supplemental prespec SHA256: `5dc8c39e2e1bb2ab85c893e8769d601e4cb8d1a295e56bf543c6a6643d92130b`.
