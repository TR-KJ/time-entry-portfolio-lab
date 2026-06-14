# ==========================================
# Time Entry Portfolio Lab
# portfolio_money_management_sim_v1_1.py
#
# 目的：
# - 損失額固定型・週次複利運用の資金曲線を作る
# - Base / Filter v1 / Filter v2 を同じ資金管理条件で比較する
#
# v1.1 修正点：
# - Q1 / OOS のMaxDDPctを、期間内だけで再計算しない
# - 2015年から継続した資金曲線上で期間内DDを評価する
# - 期間開始時点残高 / 期間終了時点残高 / 期間リターンを出す
#
# 前提：
# - 初期資金：500,000円
# - 1トレードリスク：週初残高の2%
# - 複利更新：月曜06:00 JST
# - 同時保有：各トレード同じ週の固定リスク額
#
# 損益計算：
# - YenPnL = WeekRiskAmount * (Pips / SL)
#
# 入力候補：
# - /content/Portfolio_Integration_Results_v1_2_add_aussie_logic.csv
# - /content/Filter_Test_v1_Best_Accepted_Trades.csv
# - /content/Filter_v2_Best_Accepted_Trades.csv
#
# 出力：
# - /content/money_sim_v1_1_weekly_fixed_risk/
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

OUT_DIR = '/content/money_sim_v1_1_weekly_fixed_risk'
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

# Google Drive保存版を使う場合は、必要に応じてpathを変更してください。
# 例：
# '/content/drive/MyDrive/time-entry-portfolio-lab/results/v1_2_add_aussie_logic/Portfolio_Integration_Results_v1_2_add_aussie_logic.csv'

# ==========================================
# 3. 期間定義
# ==========================================

PERIODS = [
    {
        'label': 'Full_2015_2026Q1',
        'start': pd.Timestamp('2015-01-01'),
        'end': pd.Timestamp('2026-03-31 23:59:59')
    },
    {
        'label': 'StrictIS_2015_2024',
        'start': pd.Timestamp('2015-01-01'),
        'end': pd.Timestamp('2024-12-31 23:59:59')
    },
    {
        'label': 'StrictOOS_2025_2026Q1',
        'start': pd.Timestamp('2025-01-01'),
        'end': pd.Timestamp('2026-03-31 23:59:59')
    },
    {
        'label': 'Q1_2026',
        'start': pd.Timestamp('2026-01-01'),
        'end': pd.Timestamp('2026-03-31 23:59:59')
    }
]

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
# 5. シミュレーション本体
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

    df = df.dropna(subset=['SL']).copy()
    df = df[df['SL'] > 0].copy()

    if df.empty:
        return pd.DataFrame(), pd.DataFrame()

    df['TradingWeekStart'] = df['EntryTime'].apply(get_trading_week_start)

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

    # 継続資金曲線
    sim_df['Equity'] = INITIAL_CAPITAL + sim_df['YenPnL'].cumsum()
    sim_df['PeakEquity'] = sim_df['Equity'].cummax()
    sim_df['DrawdownYen'] = sim_df['PeakEquity'] - sim_df['Equity']
    sim_df['DrawdownPct'] = sim_df['DrawdownYen'] / sim_df['PeakEquity'] * 100

    # トレード単位の補助列
    sim_df['TradeReturnPctOnWeekStart'] = sim_df['YenPnL'] / sim_df['WeekStartBalance'] * 100

    return sim_df, weekly_df


# ==========================================
# 6. 期間集計 v1.1
# ==========================================

def get_equity_before_period(sim_df, period_start):
    before = sim_df[sim_df['CloseTime'] < period_start].copy()

    if before.empty:
        return INITIAL_CAPITAL

    return before['Equity'].iloc[-1]


def calc_period_metrics_continuous_equity(sim_df, dataset_name, period_label, start, end):
    """
    2015年から継続した資金曲線を前提に、期間内の成績を計算する。

    v1.1の重要ポイント：
    - 期間内だけでEquityを50万円から再計算しない
    - 期間開始時点の実残高をStartEquityとする
    - MaxDDPctは継続資金曲線の期間内DrawdownPct最大
    """

    d = sim_df[
        (sim_df['CloseTime'] >= start) &
        (sim_df['CloseTime'] <= end)
    ].copy()

    start_equity = get_equity_before_period(sim_df, start)

    if d.empty:
        return {
            'Dataset': dataset_name,
            'Period': period_label,
            'Trades': 0,
            'StartEquity': round(start_equity, 0),
            'EndEquity': round(start_equity, 0),
            'NetProfitYen': 0,
            'ReturnPct': 0,
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

    end_equity = d['Equity'].iloc[-1]
    net_profit = end_equity - start_equity

    if start_equity > 0:
        return_pct = net_profit / start_equity * 100
    else:
        return_pct = np.nan

    # 期間内の継続DD最大
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
        'Dataset': dataset_name,
        'Period': period_label,
        'Trades': len(d),
        'StartEquity': round(start_equity, 0),
        'EndEquity': round(end_equity, 0),
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


def calc_all_period_summaries(sim_df, dataset_name):
    rows = []

    for p in PERIODS:
        rows.append(
            calc_period_metrics_continuous_equity(
                sim_df=sim_df,
                dataset_name=dataset_name,
                period_label=p['label'],
                start=p['start'],
                end=p['end']
            )
        )

    return pd.DataFrame(rows)


# ==========================================
# 7. 補助集計
# ==========================================

def calc_strategy_summary(sim_df, dataset_name):
    rows = []

    for strategy, sub in sim_df.groupby('Strategy'):
        sub = sub.sort_values('CloseTime').copy()

        wins = sub[sub['YenPnL'] > 0]['YenPnL'].sum()
        losses = sub[sub['YenPnL'] < 0]['YenPnL'].sum()

        if losses < 0:
            pf = wins / abs(losses)
        else:
            pf = np.nan

        total = sub['YenPnL'].sum()
        win_rate = len(sub[sub['YenPnL'] > 0]) / len(sub) * 100

        rows.append({
            'Dataset': dataset_name,
            'Strategy': strategy,
            'Trades': len(sub),
            'TotalYenPnL': round(total, 0),
            'WinRate': round(win_rate, 2),
            'PF_Yen': round(pf, 3) if not pd.isna(pf) else np.nan,
            'AvgYenPnL': round(sub['YenPnL'].mean(), 0),
            'WorstTradeYen': round(sub['YenPnL'].min(), 0),
            'BestTradeYen': round(sub['YenPnL'].max(), 0)
        })

    result = pd.DataFrame(rows)

    if not result.empty:
        result = result.sort_values('TotalYenPnL', ascending=False)

    return result


def calc_yearly_summary(sim_df, dataset_name):
    d = sim_df.copy()
    d['Year'] = d['CloseTime'].dt.year

    rows = []

    for year, sub in d.groupby('Year'):
        start_equity = get_equity_before_period(sim_df, pd.Timestamp(f'{year}-01-01'))
        end_equity = sub.sort_values('CloseTime')['Equity'].iloc[-1]
        net_profit = end_equity - start_equity

        rows.append({
            'Dataset': dataset_name,
            'Year': year,
            'Trades': len(sub),
            'StartEquity': round(start_equity, 0),
            'EndEquity': round(end_equity, 0),
            'NetProfitYen': round(net_profit, 0),
            'ReturnPct': round(net_profit / start_equity * 100, 2) if start_equity > 0 else np.nan,
            'MaxDDYen': round(sub['DrawdownYen'].max(), 0),
            'MaxDDPct': round(sub['DrawdownPct'].max(), 2)
        })

    return pd.DataFrame(rows)


# ==========================================
# 8. 実行
# ==========================================

all_period_summary = []
all_weekly = []
all_yearly = []

sim_outputs = {}

for item in DATASETS:
    name = item['name']
    path = item['path']

    if not os.path.exists(path):
        print(f'⚠️ skip: {name} CSV not found: {path}')
        continue

    trades = pd.read_csv(path)

    print('\n' + '=' * 90)
    print(f'Running weekly fixed-risk sim v1.1: {name}')
    print('=' * 90)

    sim_df, weekly_df = run_weekly_fixed_risk_sim(trades, name)

    if sim_df.empty:
        print(f'⚠️ No trades after simulation: {name}')
        continue

    sim_outputs[name] = sim_df

    period_summary = calc_all_period_summaries(sim_df, name)
    strategy_summary = calc_strategy_summary(sim_df, name)
    yearly_summary = calc_yearly_summary(sim_df, name)

    all_period_summary.append(period_summary)
    all_weekly.append(weekly_df)
    all_yearly.append(yearly_summary)

    # 個別保存
    sim_df.to_csv(f'{OUT_DIR}/{name}_MoneySim_v1_1_TradeLog.csv', index=False)
    weekly_df.to_csv(f'{OUT_DIR}/{name}_MoneySim_v1_1_Weekly.csv', index=False)
    period_summary.to_csv(f'{OUT_DIR}/{name}_MoneySim_v1_1_PeriodSummary.csv', index=False)
    strategy_summary.to_csv(f'{OUT_DIR}/{name}_MoneySim_v1_1_StrategySummary.csv', index=False)
    yearly_summary.to_csv(f'{OUT_DIR}/{name}_MoneySim_v1_1_YearlySummary.csv', index=False)

    print(period_summary.to_string(index=False))

# ==========================================
# 9. 統合保存
# ==========================================

if all_period_summary:
    combined_period_summary = pd.concat(all_period_summary).reset_index(drop=True)
    combined_period_summary.to_csv(f'{OUT_DIR}/MoneySim_v1_1_Combined_PeriodSummary.csv', index=False)

    print('\n' + '=' * 90)
    print('Combined Period Summary')
    print('=' * 90)
    print(combined_period_summary.to_string(index=False))

if all_weekly:
    combined_weekly = pd.concat(all_weekly).reset_index(drop=True)
    combined_weekly.to_csv(f'{OUT_DIR}/MoneySim_v1_1_Combined_Weekly.csv', index=False)

if all_yearly:
    combined_yearly = pd.concat(all_yearly).reset_index(drop=True)
    combined_yearly.to_csv(f'{OUT_DIR}/MoneySim_v1_1_Combined_YearlySummary.csv', index=False)

# ==========================================
# 10. グラフ
# ==========================================

for name, sim_df in sim_outputs.items():
    plt.figure(figsize=(14, 5))
    plt.plot(sim_df['CloseTime'], sim_df['Equity'])
    plt.title(f'Equity Curve - {name} - MoneySim v1.1')
    plt.xlabel('CloseTime')
    plt.ylabel('Equity JPY')
    plt.grid(True)
    plt.show()

    plt.figure(figsize=(14, 5))
    plt.plot(sim_df['CloseTime'], sim_df['DrawdownPct'])
    plt.title(f'Drawdown % - {name} - MoneySim v1.1')
    plt.xlabel('CloseTime')
    plt.ylabel('Drawdown %')
    plt.grid(True)
    plt.show()

print('\n✅ Money management simulation v1.1 completed.')
print(f'Output dir: {OUT_DIR}')
