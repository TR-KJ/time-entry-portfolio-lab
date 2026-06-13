# Time Entry Portfolio Lab

FXの時間固定エントリー・時間固定決済ロジックをPythonで検証・管理するためのレポジトリ。

## 目的

このレポジトリでは、現在運用中の時間アノマリー型ポートフォリオを再現し、追加フィルタによるPF・DD・RoMD改善を検証する。

主な目的：

- 現行ロジックの条件管理
- Pythonバックテストコードの管理
- 経済指標フィルターの管理
- トレードログの分析
- フィルタ追加検証
- 実運用成績との比較

## 対象

主な対象通貨ペア：

- USDJPY
- EURJPY
- GBPJPY
- AUDJPY
- AUDUSD
- EURAUD
- GBPAUD

## 検証方針

検証では以下を重視する。

- JST基準で検証する
- スプレッドを明示する
- SL/TP同一足到達時は保守的にSL優先とする
- 年末年始停止を反映する
- 重要指標停止を反映する
- IS/OOSを分けて確認する
- 年別・月別・ロジック別成績を確認する
- PFだけでなく、Max DD、RoMD、トレード数も確認する

## ディレクトリ構成

```text
time-entry-portfolio-lab/
│
├── README.md
├── CHANGELOG.md
├── ROADMAP.md
├── DEVELOPMENT_LOG.md
│
├── docs/
│   ├── 01_strategy_overview.md
│   ├── 02_backtest_policy.md
│   ├── 03_event_filter_rules.md
│   ├── 04_known_issues.md
│   └── 05_colab_usage.md
│
├── src/
│   ├── portfolio_backtest_v1.py
│   ├── portfolio_backtest_v2.py
│   └── modules/
│
├── configs/
│   ├── strategies_master.csv
│   ├── spreads.csv
│   └── portfolio_groups.csv
│
├── data/
│   ├── events/
│   └── sample/
│
├── results/
│   ├── v1_baseline/
│   ├── v2_engine_fix/
│   └── filter_tests/
│
└── notebooks/
    └── colab_portfolio_backtest.ipynb
```

## 現在のステータス

- 現行16ロジックのPythonコードあり
- UJ_Short_Coreに修正必要箇所あり
- EA / GA / オージー絡みロジック追加予定
- 2026年経済指標カレンダー追加予定
- フィルタ検証は、検証エンジン整備後に実施予定# time-entry-portfolio-lab
