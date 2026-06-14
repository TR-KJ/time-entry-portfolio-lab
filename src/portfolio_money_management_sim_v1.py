# ==========================================
# Time Entry Portfolio Lab
# portfolio_money_management_sim_v1.py
#
# 目的：
# - v1.2 Add Aussie Logic のトレード履歴CSVを読み込む
# - 損失額固定型・週次複利運用で資金曲線を作る
# - Base / Filter v1 / Filter v2 の accepted trades を同じ条件で比較する
#
# 前提：
# - 初期資金：500,000円
# - 1トレードリスク：週初残高の2%
# - 複利更新：月曜06:00 JST
# - 同時保有：各トレード同じ週の固定リスク額
#
# 損益計算：
# - YenPnL = WeekRiskAmount * (Pips / SL)
# - SL到達なら基本 -WeekRiskAmount
# - TP/TimeExitはPips/SL比率で円換算
#
# 入力候補：
# - /content/Portfolio_Integration_Results_v1_2_add_aussie_logic.csv
# - /content/Filter_Test_v1_Best_Accepted_Trades.csv
# - /content/Filter_v2_Best_Accepted_Trades.csv
#
# 出力：
# - /content/money_management_sim_v1/
# ==========================================

from google.colab import drive
import pandas as pd
import numpy as np
import os
import matplotlib.pyplot as plt

drive.mount('/content/drive')

# ==========================================
# 1. パラメータ
# ==========================================

INITIAL_CAPITAL = 500000
RISK_PER_TRADE_PCT = 0.02

# 月曜朝を 06:00 JST として週次複利更新
WEEK_ROLLOVER_HOUR = 6

OUT_DIR = '/content/money_management_sim_v1'
os.makedirs(OUT_DIR, exist_ok=True)

# ==========================================
# 2. 入力CSV候補
# ==========================================

DATASETS = [
    {
        'name': 'Base_v1_2',
        'path': '/content/Portfolio_Integration_Results_v1_2_add_aussie_logic.csv'
    },
    {
        'name': 'Filter_v1_Best',
        'path': '/content/Filter_Test_v1_Best_Accepted_Trades.csv'
    },
    {
        'name': 'Filter_v2_Best',
        'path': '/content/Filter_v2_Best_Accepted_Trades.csv'
    }
]

# Google Driveに置いている場合は、必要に応じて上のpathを変更してください。
# 例：
# '/content/drive/MyDrive/time-entry-portfolio-lab/results/v1_2_add_aussie_logic/Portfolio_Integration_Results_v1_2_add_aussie_logic.csv'

# ==========================================
# 3. 期間定義
# ==========================================

FULL_START = pd.Timestamp('2015-01-01')
FULL_END = pd.Timestamp('2026-03-31 23:59:59')

STRICT_IS_START = pd.Timestamp('2015-01-01')
STRICT_IS_END = pd.Timestamp('2024-12-31 23:59:59')

STRICT_OOS_START = pd.Timestamp('2025-01-01')
STRICT_OOS_END = pd.Timestamp('2026-03-31 23:59:59')

Q1_START = pd.Timestamp('2026-01-01')
Q1_END = pd.Timestamp('2026-03-31 23:59:59')

# ==========================================
# 4. 週キー関数
# ==========================================

def get_trading_week_start(dt):
    """
    月曜06:00を週次複利更新時刻とする。
    EntryTimeが月曜06:00より前なら前週扱い。
    """
    dt = pd.Timestamp(dt)

    monday = dt.normalize() - pd.Timedelta(days=dt.weekday())
    week_start = monday + pd.Timedelta(hours=WEEK_ROLLOVER_HOUR)

    if dt < week_start:
        week_start = week_start - pd.Timedelta(days=7)

    return week_start


# ==========================================
# 5. 集計関数
# ==========================================

def calc_money_metrics(input_df, label):
    d = input_df.copy()

    if d.empty:
        return {
            'Label': label,
            'Trades': 0,
            'FinalEquity': np.nan,
            'NetProfitYen': 0,
            'ReturnPct': np.nan,
            'MaxDDYen': 0,
            'MaxDDPct': 0,
            'RoMD_Yen': np.nan,
            'WinRate': np.nan,
            'PF_Yen': np.nan,
            'AvgYenPnL': np.nan,
            'WorstTradeYen': np.nan,
            'BestTradeYen': np.nan
        }

    d = d.sort_values('CloseTime').copy()

    d['Equity'] = INITIAL_CAPITAL + d['YenPnL'].cumsum()
    d['PeakEquity'] = d['Equity'].cummax()
    d['DrawdownYen'] = d['PeakEquity'] - d['Equity']
    d['DrawdownPct'] = d['DrawdownYen'] / d['PeakEquity'] * 100

    final_equity = d['Equity'].iloc[-1]
    net_profit = final_equity - INITIAL_CAPITAL
    return_pct = net_profit / INITIAL_CAPITAL * 100

    max_dd_yen = d['DrawdownYen'].max()
    max_dd_pct = d['DrawdownPct'].max()

    if max_dd_yen > 0:
        romd_yen = net_profit / max_dd_yen
    else:
        romd_yen = np.nan

    wins = d[d['YenPnL'] > 0]['YenPnL'].sum()
    losses = d[d['YenPnL'] < 0]['YenPnL'].sum()

    if losses < 0:
        pf_yen = wins / abs(losses)
    else:
        pf_yen = np.nan

    win_rate = len(d[d['YenPnL'] > 0]) / len(d) * 100

    return {
        'Label': label,
        'Trades': len(d),
        'FinalEquity': round(final_equity, 0),
        'NetProfitYen': round(net_profit, 0),
        'ReturnPct': round(return_pct, 2),
        'MaxDDYen': round(max_dd_yen, 0),
        'MaxDDPct': round(max_dd_pct, 2),
        'RoMD_Yen': round(romd_yen, 2) if not pd.isna(romd_yen) else np.nan,
        'WinRate': round(win_rate, 2),
        'PF_Yen': round(pf_yen, 3) if not pd.isna(pf_yen) else np.nan,
        'AvgYenPnL': round(d['YenPnL'].mean(), 0),
        'WorstTradeYen': round(d['YenPnL'].min(), 0),
        'BestTradeYen': round(d['YenPnL'].max(), 0)
    }


def calc_period_summaries(sim_df, dataset_name):
    rows = []

    full_df = sim_df[
        (sim_df['CloseTime'] >= FULL_START) &
        (sim_df['CloseTime'] <= FULL_END)
    ].copy()

    is_df = sim_df[
        (sim_df['CloseTime'] >= STRICT_IS_START) &
        (sim_df['CloseTime'] <= STRICT_IS_END)
    ].copy()

    oos_df = sim_df[
        (sim_df['CloseTime'] >= STRICT_OOS_START) &
        (sim_df['CloseTime'] <= STRICT_OOS_END)
    ].copy()

    q1_df = sim_df[
        (sim_df['CloseTime'] >= Q1_START) &
        (sim_df['CloseTime'] <= Q1_END)
    ].copy()

    rows.append(calc_money_metrics(full_df, f'{dataset_name}_Full_2015_2026Q1'))
    rows.append(calc_money_metrics(is_df, f'{dataset_name}_StrictIS_2015_2024'))
    rows.append(calc_money_metrics(oos_df, f'{dataset_name}_StrictOOS_2025_2026Q1'))
    rows.append(calc_money_metrics(q1_df, f'{dataset_name}_Q1_2026'))

    return pd.DataFrame(rows)


# ==========================================
# 6. 週次複利シミュレーション本体
# ==========================================

def run_weekly_fixed_risk_sim(trades_df, dataset_name):
    df = trades_df.copy()

    df['EntryTime'] = pd.to_datetime(df['EntryTime'])
    df['CloseTime'] = pd.to_datetime(df['CloseTime'])

    df = df.sort_values(['EntryTime', 'CloseTime']).reset_index(drop=True)

    required_cols = [
        'Strategy',
        'Pair',
        'Direction',
        'EntryTime',
        'CloseTime',
        'Pips',
        'SL'
    ]

    missing_cols = [c for c in required_cols if c not in df.columns]

    if missing_cols:
        raise ValueError(f'{dataset_name}: 必要な列がありません: {missing_cols}')

    # SLが0や欠損だと損失額固定計算ができないため除外
    df = df.dropna(subset=['SL']).copy()
    df = df[df['SL'] > 0].copy()

    df['TradingWeekStart'] = df['EntryTime'].apply(get_trading_week_start)

    # 週ごとにEntryTime順で並べる
    weeks = sorted(df['TradingWeekStart'].unique())

    current_balance = INITIAL_CAPITAL

    all_rows = []
    weekly_rows = []

    for week_start in weeks:
        week_df = df[df['TradingWeekStart'] == week_start].copy()
        week_df = week_df.sort_values(['EntryTime', 'CloseTime']).reset_index(drop=True)

        week_start_balance = current_balance
        risk_amount = week_start_balance * RISK_PER_TRADE_PCT

        week_pnl = 0

        for _, row in week_df.iterrows():
            pips = row['Pips']
            sl_pips = row['SL']

            r_multiple = pips / sl_pips
            yen_pnl = risk_amount * r_multiple

            row_dict = row.to_dict()
            row_dict['Dataset'] = dataset_name
            row_dict['WeekStartBalance'] = week_start_balance
            row_dict['RiskAmountYen'] = risk_amount
            row_dict['RMultiple'] = r_multiple
            row_dict['YenPnL'] = yen_pnl

            all_rows.append(row_dict)

            week_pnl += yen_pnl

        week_end_balance = week_start_balance + week_pnl
        current_balance = week_end_balance

        weekly_rows.append({
            'Dataset': dataset_name,
            'TradingWeekStart': week_start,
            'WeekStartBalance': round(week_start_balance, 0),
            'RiskAmountYen': round(risk_amount, 0),
            'Trades': len(week_df),
            'WeekYenPnL': round(week_pnl, 0),
            'WeekReturnPct': round(week_pnl / week_start_balance * 100, 2) if week_start_balance > 0 else np.nan,
            'WeekEndBalance': round(week_end_balance, 0)
        })

    sim_df = pd.DataFrame(all_rows)
    weekly_df = pd.DataFrame(weekly_rows)

    if sim_df.empty:
        return sim_df, weekly_df

    sim_df = sim_df.sort_values('CloseTime').reset_index(drop=True)
    sim_df['Equity'] = INITIAL_CAPITAL + sim_df['YenPnL'].cumsum()
    sim_df['PeakEquity'] = sim_df['Equity'].cummax()
    sim_df['DrawdownYen'] = sim_df['PeakEquity'] - sim_df['Equity']
    sim_df['DrawdownPct'] = sim_df['DrawdownYen'] / sim_df['PeakEquity'] * 100

    return sim_df, weekly_df


# ==========================================
# 7. 実行
# ==========================================

all_summary_rows = []
all_period_summary = []
all_weekly = []

sim_outputs = {}

for item in DATASETS:
    name = item['name']
    path = item['path']

    if not os.path.exists(path):
        print(f'⚠️ skip: {name} CSV not found: {path}')
        continue

    trades = pd.read_csv(path)

    print('\n' + '=' * 80)
    print(f'Running weekly fixed-risk sim: {name}')
    print('=' * 80)

    sim_df, weekly_df = run_weekly_fixed_risk_sim(trades, name)

    if sim_df.empty:
        print(f'⚠️ No trades after simulation: {name}')
        continue

    sim_outputs[name] = sim_df

    period_summary = calc_period_summaries(sim_df, name)
    all_period_summary.append(period_summary)

    all_weekly.append(weekly_df)

    # Strategy summary
    strategy_rows = []

    for strategy, sub in sim_df.groupby('Strategy'):
        strategy_rows.append(calc_money_metrics(sub, f'{name}_{strategy}'))

    strategy_summary = pd.DataFrame(strategy_rows)
    strategy_summary = strategy_summary.sort_values('NetProfitYen', ascending=False)

    # 保存
    sim_df.to_csv(f'{OUT_DIR}/{name}_MoneySim_TradeLog.csv', index=False)
    weekly_df.to_csv(f'{OUT_DIR}/{name}_MoneySim_Weekly.csv', index=False)
    period_summary.to_csv(f'{OUT_DIR}/{name}_MoneySim_PeriodSummary.csv', index=False)
    strategy_summary.to_csv(f'{OUT_DIR}/{name}_MoneySim_StrategySummary.csv', index=False)

    print(period_summary.to_string(index=False))

# ==========================================
# 8. 統合保存
# ==========================================

if all_period_summary:
    combined_period_summary = pd.concat(all_period_summary).reset_index(drop=True)
    combined_period_summary.to_csv(f'{OUT_DIR}/MoneySim_v1_Combined_PeriodSummary.csv', index=False)

    print('\n' + '=' * 80)
    print('Combined Period Summary')
    print('=' * 80)
    print(combined_period_summary.to_string(index=False))

if all_weekly:
    combined_weekly = pd.concat(all_weekly).reset_index(drop=True)
    combined_weekly.to_csv(f'{OUT_DIR}/MoneySim_v1_Combined_Weekly.csv', index=False)

# ==========================================
# 9. グラフ
# ==========================================

for name, sim_df in sim_outputs.items():
    plt.figure(figsize=(14, 5))
    plt.plot(sim_df['CloseTime'], sim_df['Equity'])
    plt.title(f'Equity Curve - {name}')
    plt.xlabel('CloseTime')
    plt.ylabel('Equity JPY')
    plt.grid(True)
    plt.show()

    plt.figure(figsize=(14, 5))
    plt.plot(sim_df['CloseTime'], sim_df['DrawdownPct'])
    plt.title(f'Drawdown % - {name}')
    plt.xlabel('CloseTime')
    plt.ylabel('Drawdown %')
    plt.grid(True)
    plt.show()

print('\n✅ Money management simulation v1 completed.')
print(f'Output dir: {OUT_DIR}')
