# ==========================================
# Time Entry Portfolio Lab
# money_risk_compare_global_atr_p70_v1.py
#
# 目的：
# - 暫定本命フィルタ Global H1 ATR P70 を対象に
# - 損失額固定型・週次複利でリスク率比較を行う
#
# 比較リスク率：
# - 1.0%
# - 1.5%
# - 2.0%
#
# 前提：
# - 初期資金：500,000円
# - 複利更新：月曜06:00 JST
# - 同時保有：各トレード同じ週の固定リスク額
#
# 入力候補：
# - /content/money_filter_logic_atr_select_v1/Global_H1_ATR_P70_Accepted_Trades.csv
# - なければ /content/money_filter_deep_dive_v1/DeepDive_H1_ATR_P70_Accepted_Trades.csv
#
# 出力：
# - /content/money_risk_compare_global_atr_p70_v1/
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
RISK_PCTS = [0.01, 0.015, 0.02]
WEEK_ROLLOVER_HOUR = 6

OUT_DIR = '/content/money_risk_compare_global_atr_p70_v1'
os.makedirs(OUT_DIR, exist_ok=True)

INPUT_CANDIDATES = [
    '/content/money_filter_logic_atr_select_v1/Global_H1_ATR_P70_Accepted_Trades.csv',
    '/content/money_filter_deep_dive_v1/DeepDive_H1_ATR_P70_Accepted_Trades.csv'
]

TRADE_CSV = None

for path in INPUT_CANDIDATES:
    if os.path.exists(path):
        TRADE_CSV = path
        break

if TRADE_CSV is None:
    raise FileNotFoundError(
        'Global H1 ATR P70 Accepted Trades CSV が見つかりません。候補パスを確認してください。'
    )

print(f'✅ Input CSV: {TRADE_CSV}')

# ==========================================
# 2. 期間定義
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
# 3. 読み込み
# ==========================================

df = pd.read_csv(TRADE_CSV)

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
    raise ValueError(f'必要な列がありません: {missing_cols}')

df = df.dropna(subset=['SL']).copy()
df = df[df['SL'] > 0].copy()

print('✅ Trades loaded')
print(f'Rows: {len(df):,}')
print(f"Period: {df['CloseTime'].min()} 〜 {df['CloseTime'].max()}")

# ==========================================
# 4. 週キー関数
# ==========================================

def get_trading_week_start(dt):
    """
    月曜06:00 JSTを週次複利更新タイミングとする。
    月曜06:00より前の決済・エントリーは前週扱い。
    """
    dt = pd.Timestamp(dt)

    monday = dt.normalize() - pd.Timedelta(days=dt.weekday())
    week_start = monday + pd.Timedelta(hours=WEEK_ROLLOVER_HOUR)

    if dt < week_start:
        week_start = week_start - pd.Timedelta(days=7)

    return week_start

# ==========================================
# 5. MoneySim本体
# ==========================================

def run_weekly_fixed_risk_sim(trades_df, dataset_name, risk_pct):
    t = trades_df.copy()

    t['EntryTime'] = pd.to_datetime(t['EntryTime'])
    t['CloseTime'] = pd.to_datetime(t['CloseTime'])

    t = t.sort_values(['EntryTime', 'CloseTime']).reset_index(drop=True)

    t['TradingWeekStart'] = t['EntryTime'].apply(get_trading_week_start)

    weeks = sorted(t['TradingWeekStart'].unique())

    current_balance = INITIAL_CAPITAL

    all_rows = []
    weekly_rows = []

    for week_start in weeks:
        week_df = t[t['TradingWeekStart'] == week_start].copy()
        week_df = week_df.sort_values(['EntryTime', 'CloseTime']).reset_index(drop=True)

        week_start_balance = current_balance
        risk_amount = week_start_balance * risk_pct

        week_pnl = 0

        for _, row in week_df.iterrows():
            r_multiple = row['Pips'] / row['SL']
            yen_pnl = risk_amount * r_multiple

            row_dict = row.to_dict()
            row_dict['Dataset'] = dataset_name
            row_dict['RiskPct'] = risk_pct
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
            'RiskPct': risk_pct,
            'TradingWeekStart': week_start,
            'WeekStartBalance': round(week_start_balance, 0),
            'RiskAmountYen': round(risk_amount, 0),
            'Trades': len(week_df),
            'WeekYenPnL': round(week_pnl, 0),
            'WeekReturnPct': round(week_pnl / week_start_balance * 100, 2) if week_start_balance > 0 else np.nan,
            'WeekEndBalance': round(week_end_balance, 0)
        })

    sim = pd.DataFrame(all_rows)
    weekly = pd.DataFrame(weekly_rows)

    if sim.empty:
        return sim, weekly

    sim = sim.sort_values('CloseTime').reset_index(drop=True)
    sim['Equity'] = INITIAL_CAPITAL + sim['YenPnL'].cumsum()
    sim['PeakEquity'] = sim['Equity'].cummax()
    sim['DrawdownYen'] = sim['PeakEquity'] - sim['Equity']
    sim['DrawdownPct'] = sim['DrawdownYen'] / sim['PeakEquity'] * 100
    sim['TradeReturnPctOnWeekStart'] = sim['YenPnL'] / sim['WeekStartBalance'] * 100

    return sim, weekly

# ==========================================
# 6. 集計関数
# ==========================================

def get_equity_before_period(sim_df, period_start):
    before = sim_df[sim_df['CloseTime'] < period_start].copy()

    if before.empty:
        return INITIAL_CAPITAL

    return before['Equity'].iloc[-1]


def calc_period_metrics(sim_df, weekly_df, dataset_name, risk_pct, period_label, start, end):
    d = sim_df[
        (sim_df['CloseTime'] >= start) &
        (sim_df['CloseTime'] <= end)
    ].copy()

    w = weekly_df[
        (weekly_df['TradingWeekStart'] >= start - pd.Timedelta(days=7)) &
        (weekly_df['TradingWeekStart'] <= end)
    ].copy()

    start_equity = get_equity_before_period(sim_df, start)

    if d.empty:
        return {
            'Dataset': dataset_name,
            'RiskPct': risk_pct,
            'RiskPctLabel': f'{risk_pct * 100:.1f}%',
            'Period': period_label,
            'Trades': 0,
            'StartEquity': round(start_equity, 0),
            'EndEquity': round(start_equity, 0),
            'NetProfitYen': 0,
            'ReturnPct': 0,
            'MaxDDYen': 0,
            'MaxDDPct': 0,
            'MoneyRoMD': np.nan,
            'PF_Yen': np.nan,
            'WorstWeekReturnPct': np.nan,
            'BestWeekReturnPct': np.nan,
            'AvgWeekReturnPct': np.nan,
            'NegativeWeeks': 0,
            'PositiveWeeks': 0
        }

    d = d.sort_values('CloseTime').copy()

    end_equity = d['Equity'].iloc[-1]
    net_profit = end_equity - start_equity

    return_pct = net_profit / start_equity * 100 if start_equity > 0 else np.nan

    max_dd_yen = d['DrawdownYen'].max()
    max_dd_pct = d['DrawdownPct'].max()

    money_romd = net_profit / max_dd_yen if max_dd_yen > 0 else np.nan

    wins = d[d['YenPnL'] > 0]['YenPnL'].sum()
    losses = d[d['YenPnL'] < 0]['YenPnL'].sum()

    pf_yen = wins / abs(losses) if losses < 0 else np.nan

    if not w.empty:
        worst_week = w['WeekReturnPct'].min()
        best_week = w['WeekReturnPct'].max()
        avg_week = w['WeekReturnPct'].mean()
        negative_weeks = len(w[w['WeekReturnPct'] < 0])
        positive_weeks = len(w[w['WeekReturnPct'] > 0])
    else:
        worst_week = np.nan
        best_week = np.nan
        avg_week = np.nan
        negative_weeks = 0
        positive_weeks = 0

    return {
        'Dataset': dataset_name,
        'RiskPct': risk_pct,
        'RiskPctLabel': f'{risk_pct * 100:.1f}%',
        'Period': period_label,
        'Trades': len(d),
        'StartEquity': round(start_equity, 0),
        'EndEquity': round(end_equity, 0),
        'NetProfitYen': round(net_profit, 0),
        'ReturnPct': round(return_pct, 2),
        'MaxDDYen': round(max_dd_yen, 0),
        'MaxDDPct': round(max_dd_pct, 2),
        'MoneyRoMD': round(money_romd, 2) if not pd.isna(money_romd) else np.nan,
        'PF_Yen': round(pf_yen, 3) if not pd.isna(pf_yen) else np.nan,
        'WorstWeekReturnPct': round(worst_week, 2) if not pd.isna(worst_week) else np.nan,
        'BestWeekReturnPct': round(best_week, 2) if not pd.isna(best_week) else np.nan,
        'AvgWeekReturnPct': round(avg_week, 2) if not pd.isna(avg_week) else np.nan,
        'NegativeWeeks': negative_weeks,
        'PositiveWeeks': positive_weeks
    }


def calc_all_period_metrics(sim_df, weekly_df, dataset_name, risk_pct):
    rows = []

    for p in PERIODS:
        rows.append(
            calc_period_metrics(
                sim_df=sim_df,
                weekly_df=weekly_df,
                dataset_name=dataset_name,
                risk_pct=risk_pct,
                period_label=p['label'],
                start=p['start'],
                end=p['end']
            )
        )

    return pd.DataFrame(rows)


def calc_yearly_summary(sim_df, dataset_name, risk_pct):
    d = sim_df.copy()
    d['Year'] = d['CloseTime'].dt.year

    rows = []

    for year, sub in d.groupby('Year'):
        start = pd.Timestamp(f'{year}-01-01')
        start_equity = get_equity_before_period(sim_df, start)

        end_equity = sub.sort_values('CloseTime')['Equity'].iloc[-1]
        net_profit = end_equity - start_equity
        return_pct = net_profit / start_equity * 100 if start_equity > 0 else np.nan

        rows.append({
            'Dataset': dataset_name,
            'RiskPct': risk_pct,
            'RiskPctLabel': f'{risk_pct * 100:.1f}%',
            'Year': year,
            'Trades': len(sub),
            'StartEquity': round(start_equity, 0),
            'EndEquity': round(end_equity, 0),
            'NetProfitYen': round(net_profit, 0),
            'ReturnPct': round(return_pct, 2),
            'MaxDDYen': round(sub['DrawdownYen'].max(), 0),
            'MaxDDPct': round(sub['DrawdownPct'].max(), 2)
        })

    return pd.DataFrame(rows)


def calc_monthly_summary(sim_df, dataset_name, risk_pct):
    d = sim_df.copy()
    d['Month'] = d['CloseTime'].dt.to_period('M').astype(str)

    rows = []

    for month, sub in d.groupby('Month'):
        month_start = pd.Timestamp(f'{month}-01')
        start_equity = get_equity_before_period(sim_df, month_start)

        end_equity = sub.sort_values('CloseTime')['Equity'].iloc[-1]
        net_profit = end_equity - start_equity
        return_pct = net_profit / start_equity * 100 if start_equity > 0 else np.nan

        rows.append({
            'Dataset': dataset_name,
            'RiskPct': risk_pct,
            'RiskPctLabel': f'{risk_pct * 100:.1f}%',
            'Month': month,
            'Trades': len(sub),
            'StartEquity': round(start_equity, 0),
            'EndEquity': round(end_equity, 0),
            'NetProfitYen': round(net_profit, 0),
            'ReturnPct': round(return_pct, 2),
            'MaxDDYen': round(sub['DrawdownYen'].max(), 0),
            'MaxDDPct': round(sub['DrawdownPct'].max(), 2)
        })

    return pd.DataFrame(rows)

# ==========================================
# 7. 実行
# ==========================================

period_summaries = []
yearly_summaries = []
monthly_summaries = []
weekly_summaries = []

sim_outputs = {}

for risk_pct in RISK_PCTS:
    dataset_name = f'Global_H1_ATR_P70_Risk_{risk_pct * 100:.1f}pct'

    print('\n' + '=' * 90)
    print(f'Running risk compare: {dataset_name}')
    print('=' * 90)

    sim_df, weekly_df = run_weekly_fixed_risk_sim(df, dataset_name, risk_pct)

    if sim_df.empty:
        print(f'⚠️ No sim output: {dataset_name}')
        continue

    period_summary = calc_all_period_metrics(sim_df, weekly_df, dataset_name, risk_pct)
    yearly_summary = calc_yearly_summary(sim_df, dataset_name, risk_pct)
    monthly_summary = calc_monthly_summary(sim_df, dataset_name, risk_pct)

    period_summaries.append(period_summary)
    yearly_summaries.append(yearly_summary)
    monthly_summaries.append(monthly_summary)
    weekly_summaries.append(weekly_df)

    sim_outputs[dataset_name] = sim_df

    sim_df.to_csv(f'{OUT_DIR}/{dataset_name}_TradeLog.csv', index=False)
    weekly_df.to_csv(f'{OUT_DIR}/{dataset_name}_Weekly.csv', index=False)
    period_summary.to_csv(f'{OUT_DIR}/{dataset_name}_PeriodSummary.csv', index=False)
    yearly_summary.to_csv(f'{OUT_DIR}/{dataset_name}_YearlySummary.csv', index=False)
    monthly_summary.to_csv(f'{OUT_DIR}/{dataset_name}_MonthlySummary.csv', index=False)

    print(period_summary.to_string(index=False))

# ==========================================
# 8. 統合保存
# ==========================================

combined_period = pd.concat(period_summaries).reset_index(drop=True)
combined_yearly = pd.concat(yearly_summaries).reset_index(drop=True)
combined_monthly = pd.concat(monthly_summaries).reset_index(drop=True)
combined_weekly = pd.concat(weekly_summaries).reset_index(drop=True)

combined_period.to_csv(f'{OUT_DIR}/RiskCompare_Global_H1_ATR_P70_PeriodSummary.csv', index=False)
combined_yearly.to_csv(f'{OUT_DIR}/RiskCompare_Global_H1_ATR_P70_YearlySummary.csv', index=False)
combined_monthly.to_csv(f'{OUT_DIR}/RiskCompare_Global_H1_ATR_P70_MonthlySummary.csv', index=False)
combined_weekly.to_csv(f'{OUT_DIR}/RiskCompare_Global_H1_ATR_P70_WeeklySummary.csv', index=False)

# ワースト週・ワースト月ランキング
worst_weeks = combined_weekly.sort_values('WeekReturnPct', ascending=True).reset_index(drop=True)
worst_months = combined_monthly.sort_values('ReturnPct', ascending=True).reset_index(drop=True)

worst_weeks.to_csv(f'{OUT_DIR}/RiskCompare_Global_H1_ATR_P70_WorstWeeks.csv', index=False)
worst_months.to_csv(f'{OUT_DIR}/RiskCompare_Global_H1_ATR_P70_WorstMonths.csv', index=False)

# ==========================================
# 9. 表示
# ==========================================

print('\n' + '=' * 100)
print('Risk Compare Period Summary')
print('=' * 100)
print(combined_period.to_string(index=False))

print('\n' + '=' * 100)
print('Worst Weeks')
print('=' * 100)
print(worst_weeks.head(20).to_string(index=False))

print('\n' + '=' * 100)
print('Worst Months')
print('=' * 100)
print(worst_months.head(20).to_string(index=False))

# ==========================================
# 10. グラフ
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

print('\n✅ money_risk_compare_global_atr_p70_v1 completed.')
print(f'Output dir: {OUT_DIR}')
