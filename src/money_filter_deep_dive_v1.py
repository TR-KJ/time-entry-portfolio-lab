# ==========================================
# Time Entry Portfolio Lab
# money_filter_deep_dive_v1.py
#
# 目的：
# - MoneyFilterCompare v1 で最有力だった
#   V2_H1_ATR14_Pips_LTE_P70
#   を深掘りする
#
# 分析内容：
# 1. 採用トレード / 除外トレードの全体比較
# 2. ロジック別に、どれだけ除外されたか
# 3. 除外されたトレードの成績が本当に悪かったか
# 4. グループ別・ペア別・方向別の影響
# 5. Q1 2026 / OOS / Full の比較
# 6. MoneySim評価で、採用側と除外側を比較
#
# 前提：
# - 初期資金：500,000円
# - 1トレードリスク：週初残高の2%
# - 複利更新：月曜06:00 JST
#
# 入力：
# - /content/filter_test_v2_range_atr/Filter_v2_Feature_Attached_Trades.csv
# - /content/filter_test_v2_range_atr/Filter_v2_Thresholds_StrictIS.csv
#
# 出力：
# - /content/money_filter_deep_dive_v1/
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
WEEK_ROLLOVER_HOUR = 6

TARGET_FEATURE = 'H1_ATR14_Pips'
TARGET_PERCENTILE = 70

OUT_DIR = '/content/money_filter_deep_dive_v1'
os.makedirs(OUT_DIR, exist_ok=True)

FEATURE_CSV = '/content/filter_test_v2_range_atr/Filter_v2_Feature_Attached_Trades.csv'
THRESHOLD_CSV = '/content/filter_test_v2_range_atr/Filter_v2_Thresholds_StrictIS.csv'

if not os.path.exists(FEATURE_CSV):
    raise FileNotFoundError(f'Feature CSV not found: {FEATURE_CSV}')

if not os.path.exists(THRESHOLD_CSV):
    raise FileNotFoundError(f'Threshold CSV not found: {THRESHOLD_CSV}')

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
# 3. グループ定義
# ==========================================

CROSS_JPY = [
    '1_EJ_Log1',
    '2_EJ_NightBlitz_20',
    '3_EJ_NightBlitz_21',
    '4_GJ_Port_Log1',
    '5_GJ_Port_Log2',
    '6_GJ_Old_Mon',
    '7_GJ_Mon_Blitz',
    '8_AJ_Core1',
    '9_AJ_Core2',
    '10_AJ_SatA',
    '11_AJ_SatB',
    '12_UJ_Short_Core',
    '13_UJ_Fix_MidWeek',
    '14_UJ_Sat_3rd',
    '15_UJ_Sat_Aug',
    '16_UJ_T10A'
]

EA_REV4 = [
    '17_EA_1B_Wed_Short',
    '18_EA_2_MonWed_Short',
    '19_EA_3_WedThu_Long',
    '20_EA_1A_MonTue_Short'
]

GA = [
    '21_GA_B_3',
    '22_GA_C_2',
    '23_GA_F_2',
    '24_GA_D_1'
]

CHINA_DEMAND = [
    '25_AU_China_Demand',
    '26_AJ_China_Demand',
    '27_EA_China_Demand',
    '28_GA_China_Demand'
]

GROUP_MAP = {}

for s in CROSS_JPY:
    GROUP_MAP[s] = 'CrossJPY_16'

for s in EA_REV4:
    GROUP_MAP[s] = 'EA_Rev4'

for s in GA:
    GROUP_MAP[s] = 'GA'

for s in CHINA_DEMAND:
    GROUP_MAP[s] = 'China_Demand'

# ==========================================
# 4. 読み込み
# ==========================================

df = pd.read_csv(FEATURE_CSV)
thresholds = pd.read_csv(THRESHOLD_CSV)

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
    'SL',
    TARGET_FEATURE
]

missing_cols = [c for c in required_cols if c not in df.columns]

if missing_cols:
    raise ValueError(f'必要な列がありません: {missing_cols}')

df['Group'] = df['Strategy'].map(GROUP_MAP).fillna('Unknown')

print('✅ Feature attached trades loaded')
print(f'Rows: {len(df):,}')
print(f"Period: {df['CloseTime'].min()} 〜 {df['CloseTime'].max()}")

# ==========================================
# 5. P70閾値付与
# ==========================================

target_thresholds = thresholds[
    (thresholds['Feature'] == TARGET_FEATURE) &
    (thresholds['Percentile'] == TARGET_PERCENTILE)
].copy()

threshold_map = {
    row['Pair']: row['Threshold']
    for _, row in target_thresholds.iterrows()
}

df['H1_ATR_P70_Threshold'] = df['Pair'].map(threshold_map)

df['FilterDecision'] = np.where(
    df[TARGET_FEATURE] <= df['H1_ATR_P70_Threshold'],
    'Accepted',
    'Rejected'
)

df.loc[
    df[TARGET_FEATURE].isna() | df['H1_ATR_P70_Threshold'].isna(),
    'FilterDecision'
] = 'Rejected_Missing'

df['ATR_to_Threshold_Ratio'] = df[TARGET_FEATURE] / df['H1_ATR_P70_Threshold']

accepted_df = df[df['FilterDecision'] == 'Accepted'].copy()
rejected_df = df[df['FilterDecision'] != 'Accepted'].copy()

print('\n✅ Filter applied')
print(f'Accepted: {len(accepted_df):,}')
print(f'Rejected: {len(rejected_df):,}')
print(f'Rejected rate: {len(rejected_df) / len(df) * 100:.2f}%')

# ==========================================
# 6. pips集計関数
# ==========================================

def calc_pips_metrics(input_df, label):
    d = input_df.copy()

    if d.empty:
        return {
            'Label': label,
            'Trades': 0,
            'WinRate': np.nan,
            'PF': np.nan,
            'TotalPips': 0,
            'MaxDD': 0,
            'RoMD': np.nan,
            'AvgPips': np.nan,
            'WinsPips': 0,
            'LossPips': 0
        }

    d = d.sort_values('CloseTime').copy()
    d['CumPips'] = d['Pips'].cumsum()
    d['MaxCumPips'] = d['CumPips'].cummax()
    d['Drawdown'] = d['MaxCumPips'] - d['CumPips']

    wins = d[d['Pips'] > 0]['Pips'].sum()
    losses = d[d['Pips'] < 0]['Pips'].sum()

    pf = wins / abs(losses) if losses < 0 else np.nan

    total = d['Pips'].sum()
    max_dd = d['Drawdown'].max()
    romd = total / max_dd if max_dd > 0 else np.nan
    win_rate = len(d[d['Pips'] > 0]) / len(d) * 100

    return {
        'Label': label,
        'Trades': len(d),
        'WinRate': round(win_rate, 2),
        'PF': round(pf, 3) if not pd.isna(pf) else np.nan,
        'TotalPips': round(total, 1),
        'MaxDD': round(max_dd, 1),
        'RoMD': round(romd, 2) if not pd.isna(romd) else np.nan,
        'AvgPips': round(d['Pips'].mean(), 2),
        'WinsPips': round(wins, 1),
        'LossPips': round(losses, 1)
    }


def calc_period_pips_summary(input_df, prefix):
    rows = []

    for p in PERIODS:
        sub = input_df[
            (input_df['CloseTime'] >= p['start']) &
            (input_df['CloseTime'] <= p['end'])
        ].copy()

        rows.append(calc_pips_metrics(sub, f'{prefix}_{p["label"]}'))

    return pd.DataFrame(rows)

# ==========================================
# 7. MoneySim関数
# ==========================================

def get_trading_week_start(dt):
    dt = pd.Timestamp(dt)

    monday = dt.normalize() - pd.Timedelta(days=dt.weekday())
    week_start = monday + pd.Timedelta(hours=WEEK_ROLLOVER_HOUR)

    if dt < week_start:
        week_start = week_start - pd.Timedelta(days=7)

    return week_start


def run_weekly_fixed_risk_sim(trades_df, dataset_name):
    t = trades_df.copy()

    t['EntryTime'] = pd.to_datetime(t['EntryTime'])
    t['CloseTime'] = pd.to_datetime(t['CloseTime'])

    t = t.sort_values(['EntryTime', 'CloseTime']).reset_index(drop=True)

    t = t.dropna(subset=['SL']).copy()
    t = t[t['SL'] > 0].copy()

    if t.empty:
        return pd.DataFrame(), pd.DataFrame()

    t['TradingWeekStart'] = t['EntryTime'].apply(get_trading_week_start)

    weeks = sorted(t['TradingWeekStart'].unique())

    current_balance = INITIAL_CAPITAL

    all_rows = []
    weekly_rows = []

    for week_start in weeks:
        week_df = t[t['TradingWeekStart'] == week_start].copy()
        week_df = week_df.sort_values(['EntryTime', 'CloseTime']).reset_index(drop=True)

        week_start_balance = current_balance
        risk_amount = week_start_balance * RISK_PER_TRADE_PCT
        week_pnl = 0

        for _, row in week_df.iterrows():
            r_multiple = row['Pips'] / row['SL']
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

    sim = pd.DataFrame(all_rows)
    weekly = pd.DataFrame(weekly_rows)

    if sim.empty:
        return sim, weekly

    sim = sim.sort_values('CloseTime').reset_index(drop=True)
    sim['Equity'] = INITIAL_CAPITAL + sim['YenPnL'].cumsum()
    sim['PeakEquity'] = sim['Equity'].cummax()
    sim['DrawdownYen'] = sim['PeakEquity'] - sim['Equity']
    sim['DrawdownPct'] = sim['DrawdownYen'] / sim['PeakEquity'] * 100

    return sim, weekly


def get_equity_before_period(sim_df, period_start):
    before = sim_df[sim_df['CloseTime'] < period_start].copy()

    if before.empty:
        return INITIAL_CAPITAL

    return before['Equity'].iloc[-1]


def calc_money_period_metrics(sim_df, weekly_df, dataset_name, period_label, start, end):
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
            'AvgWeekReturnPct': np.nan
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
    else:
        worst_week = np.nan
        best_week = np.nan
        avg_week = np.nan

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
        'MoneyRoMD': round(money_romd, 2) if not pd.isna(money_romd) else np.nan,
        'PF_Yen': round(pf_yen, 3) if not pd.isna(pf_yen) else np.nan,
        'WorstWeekReturnPct': round(worst_week, 2) if not pd.isna(worst_week) else np.nan,
        'BestWeekReturnPct': round(best_week, 2) if not pd.isna(best_week) else np.nan,
        'AvgWeekReturnPct': round(avg_week, 2) if not pd.isna(avg_week) else np.nan
    }


def calc_money_period_summary(sim_df, weekly_df, dataset_name):
    rows = []

    for p in PERIODS:
        rows.append(
            calc_money_period_metrics(
                sim_df,
                weekly_df,
                dataset_name,
                p['label'],
                p['start'],
                p['end']
            )
        )

    return pd.DataFrame(rows)

# ==========================================
# 8. 全体比較
# ==========================================

base_pips_period = calc_period_pips_summary(df, 'Base')
accepted_pips_period = calc_period_pips_summary(accepted_df, 'Accepted_H1_ATR_P70')
rejected_pips_period = calc_period_pips_summary(rejected_df, 'Rejected_H1_ATR_P70')

pips_period_summary = pd.concat([
    base_pips_period,
    accepted_pips_period,
    rejected_pips_period
]).reset_index(drop=True)

base_sim, base_weekly = run_weekly_fixed_risk_sim(df, 'Base')
accepted_sim, accepted_weekly = run_weekly_fixed_risk_sim(accepted_df, 'Accepted_H1_ATR_P70')
rejected_sim, rejected_weekly = run_weekly_fixed_risk_sim(rejected_df, 'Rejected_H1_ATR_P70')

money_period_summary = pd.concat([
    calc_money_period_summary(base_sim, base_weekly, 'Base'),
    calc_money_period_summary(accepted_sim, accepted_weekly, 'Accepted_H1_ATR_P70'),
    calc_money_period_summary(rejected_sim, rejected_weekly, 'Rejected_H1_ATR_P70')
]).reset_index(drop=True)

# ==========================================
# 9. カテゴリ別：採用/除外 比較
# ==========================================

def category_decision_summary(input_df, category_col):
    rows = []

    grouped = input_df.groupby([category_col, 'FilterDecision'])

    for keys, sub in grouped:
        category_value = keys[0]
        decision = keys[1]

        m = calc_pips_metrics(sub, f'{category_value}_{decision}')

        rows.append({
            'CategoryColumn': category_col,
            'Category': category_value,
            'Decision': decision,
            'Trades': m['Trades'],
            'WinRate': m['WinRate'],
            'PF': m['PF'],
            'TotalPips': m['TotalPips'],
            'MaxDD': m['MaxDD'],
            'RoMD': m['RoMD'],
            'AvgPips': m['AvgPips']
        })

    result = pd.DataFrame(rows)

    if not result.empty:
        result = result.sort_values(['CategoryColumn', 'Category', 'Decision'])

    return result


strategy_decision_summary = category_decision_summary(df, 'Strategy')
group_decision_summary = category_decision_summary(df, 'Group')
pair_decision_summary = category_decision_summary(df, 'Pair')
direction_decision_summary = category_decision_summary(df, 'Direction')

# ==========================================
# 10. ロジック別 除外率・除外損益
# ==========================================

strategy_rows = []

for strategy, sub in df.groupby('Strategy'):
    total_trades = len(sub)

    accepted = sub[sub['FilterDecision'] == 'Accepted'].copy()
    rejected = sub[sub['FilterDecision'] != 'Accepted'].copy()

    accepted_pips = accepted['Pips'].sum()
    rejected_pips = rejected['Pips'].sum()

    strategy_rows.append({
        'Strategy': strategy,
        'Group': sub['Group'].iloc[0],
        'TotalTrades': total_trades,
        'AcceptedTrades': len(accepted),
        'RejectedTrades': len(rejected),
        'RejectedRatePct': round(len(rejected) / total_trades * 100, 2) if total_trades > 0 else np.nan,
        'TotalPips_All': round(sub['Pips'].sum(), 1),
        'TotalPips_Accepted': round(accepted_pips, 1),
        'TotalPips_Rejected': round(rejected_pips, 1),
        'AvgPips_All': round(sub['Pips'].mean(), 2),
        'AvgPips_Accepted': round(accepted['Pips'].mean(), 2) if not accepted.empty else np.nan,
        'AvgPips_Rejected': round(rejected['Pips'].mean(), 2) if not rejected.empty else np.nan
    })

strategy_exclusion_impact = pd.DataFrame(strategy_rows)
strategy_exclusion_impact = strategy_exclusion_impact.sort_values('TotalPips_Rejected', ascending=True).reset_index(drop=True)

# ==========================================
# 11. Q1 2026 深掘り
# ==========================================

q1_df = df[
    (df['CloseTime'] >= pd.Timestamp('2026-01-01')) &
    (df['CloseTime'] <= pd.Timestamp('2026-03-31 23:59:59'))
].copy()

q1_strategy_decision_summary = category_decision_summary(q1_df, 'Strategy')
q1_group_decision_summary = category_decision_summary(q1_df, 'Group')
q1_pair_decision_summary = category_decision_summary(q1_df, 'Pair')

q1_daily_rows = []

q1_df['CloseDate'] = q1_df['CloseTime'].dt.date

for date, sub in q1_df.groupby('CloseDate'):
    total = calc_pips_metrics(sub, str(date))
    accepted = calc_pips_metrics(sub[sub['FilterDecision'] == 'Accepted'], str(date))
    rejected = calc_pips_metrics(sub[sub['FilterDecision'] != 'Accepted'], str(date))

    q1_daily_rows.append({
        'Date': date,
        'Trades_All': total['Trades'],
        'Pips_All': total['TotalPips'],
        'Trades_Accepted': accepted['Trades'],
        'Pips_Accepted': accepted['TotalPips'],
        'Trades_Rejected': rejected['Trades'],
        'Pips_Rejected': rejected['TotalPips'],
        'ImprovementByRejecting': round(accepted['TotalPips'] - total['TotalPips'], 1)
    })

q1_daily_impact = pd.DataFrame(q1_daily_rows)
q1_daily_impact = q1_daily_impact.sort_values('ImprovementByRejecting', ascending=False).reset_index(drop=True)

# ==========================================
# 12. ATR帯別成績
# ==========================================

# ratioで分類
def classify_atr_ratio(ratio):
    if pd.isna(ratio):
        return 'Unknown'
    if ratio <= 0.70:
        return 'VeryLow'
    if ratio <= 0.90:
        return 'Low'
    if ratio <= 1.00:
        return 'NearThreshold'
    if ratio <= 1.20:
        return 'OverSlightly'
    if ratio <= 1.50:
        return 'High'
    return 'VeryHigh'


df['ATRRatioBucket'] = df['ATR_to_Threshold_Ratio'].apply(classify_atr_ratio)

atr_bucket_rows = []

for bucket, sub in df.groupby('ATRRatioBucket'):
    m = calc_pips_metrics(sub, bucket)

    atr_bucket_rows.append({
        'ATRRatioBucket': bucket,
        'Trades': m['Trades'],
        'WinRate': m['WinRate'],
        'PF': m['PF'],
        'TotalPips': m['TotalPips'],
        'MaxDD': m['MaxDD'],
        'RoMD': m['RoMD'],
        'AvgPips': m['AvgPips']
    })

atr_bucket_summary = pd.DataFrame(atr_bucket_rows)
atr_bucket_summary = atr_bucket_summary.sort_values('ATRRatioBucket').reset_index(drop=True)

# ==========================================
# 13. 保存
# ==========================================

df.to_csv(f'{OUT_DIR}/DeepDive_H1_ATR_P70_All_Trades_With_Decision.csv', index=False)
accepted_df.to_csv(f'{OUT_DIR}/DeepDive_H1_ATR_P70_Accepted_Trades.csv', index=False)
rejected_df.to_csv(f'{OUT_DIR}/DeepDive_H1_ATR_P70_Rejected_Trades.csv', index=False)

pips_period_summary.to_csv(f'{OUT_DIR}/DeepDive_H1_ATR_P70_Pips_Period_Summary.csv', index=False)
money_period_summary.to_csv(f'{OUT_DIR}/DeepDive_H1_ATR_P70_Money_Period_Summary.csv', index=False)

strategy_decision_summary.to_csv(f'{OUT_DIR}/DeepDive_H1_ATR_P70_Strategy_Decision_Summary.csv', index=False)
group_decision_summary.to_csv(f'{OUT_DIR}/DeepDive_H1_ATR_P70_Group_Decision_Summary.csv', index=False)
pair_decision_summary.to_csv(f'{OUT_DIR}/DeepDive_H1_ATR_P70_Pair_Decision_Summary.csv', index=False)
direction_decision_summary.to_csv(f'{OUT_DIR}/DeepDive_H1_ATR_P70_Direction_Decision_Summary.csv', index=False)

strategy_exclusion_impact.to_csv(f'{OUT_DIR}/DeepDive_H1_ATR_P70_Strategy_Exclusion_Impact.csv', index=False)

q1_strategy_decision_summary.to_csv(f'{OUT_DIR}/DeepDive_H1_ATR_P70_Q1_Strategy_Decision_Summary.csv', index=False)
q1_group_decision_summary.to_csv(f'{OUT_DIR}/DeepDive_H1_ATR_P70_Q1_Group_Decision_Summary.csv', index=False)
q1_pair_decision_summary.to_csv(f'{OUT_DIR}/DeepDive_H1_ATR_P70_Q1_Pair_Decision_Summary.csv', index=False)
q1_daily_impact.to_csv(f'{OUT_DIR}/DeepDive_H1_ATR_P70_Q1_Daily_Impact.csv', index=False)

atr_bucket_summary.to_csv(f'{OUT_DIR}/DeepDive_H1_ATR_P70_ATR_Ratio_Bucket_Summary.csv', index=False)

base_sim.to_csv(f'{OUT_DIR}/DeepDive_H1_ATR_P70_Base_MoneySim_TradeLog.csv', index=False)
accepted_sim.to_csv(f'{OUT_DIR}/DeepDive_H1_ATR_P70_Accepted_MoneySim_TradeLog.csv', index=False)
rejected_sim.to_csv(f'{OUT_DIR}/DeepDive_H1_ATR_P70_Rejected_MoneySim_TradeLog.csv', index=False)

base_weekly.to_csv(f'{OUT_DIR}/DeepDive_H1_ATR_P70_Base_MoneySim_Weekly.csv', index=False)
accepted_weekly.to_csv(f'{OUT_DIR}/DeepDive_H1_ATR_P70_Accepted_MoneySim_Weekly.csv', index=False)
rejected_weekly.to_csv(f'{OUT_DIR}/DeepDive_H1_ATR_P70_Rejected_MoneySim_Weekly.csv', index=False)

print('\n' + '=' * 100)
print('✅ Deep Dive CSV保存完了')
print('=' * 100)
print(f'Output dir: {OUT_DIR}')
print('Main files:')
print('- DeepDive_H1_ATR_P70_Pips_Period_Summary.csv')
print('- DeepDive_H1_ATR_P70_Money_Period_Summary.csv')
print('- DeepDive_H1_ATR_P70_Strategy_Exclusion_Impact.csv')
print('- DeepDive_H1_ATR_P70_Q1_Daily_Impact.csv')
print('- DeepDive_H1_ATR_P70_ATR_Ratio_Bucket_Summary.csv')

# ==========================================
# 14. 簡易表示
# ==========================================

print('\n' + '=' * 100)
print('Pips Period Summary')
print('=' * 100)
print(pips_period_summary.to_string(index=False))

print('\n' + '=' * 100)
print('Money Period Summary')
print('=' * 100)
print(money_period_summary.to_string(index=False))

print('\n' + '=' * 100)
print('Strategy Exclusion Impact - Worst Rejected First')
print('=' * 100)
print(strategy_exclusion_impact.head(20).to_string(index=False))

print('\n' + '=' * 100)
print('Q1 Daily Impact - Improvement by Rejecting')
print('=' * 100)
print(q1_daily_impact.head(20).to_string(index=False))

print('\n' + '=' * 100)
print('ATR Ratio Bucket Summary')
print('=' * 100)
print(atr_bucket_summary.to_string(index=False))

# ==========================================
# 15. グラフ
# ==========================================

plt.figure(figsize=(14, 5))
plt.plot(base_sim['CloseTime'], base_sim['Equity'], label='Base')
plt.plot(accepted_sim['CloseTime'], accepted_sim['Equity'], label='Accepted H1 ATR P70')
plt.title('MoneySim Equity Curve - Base vs H1 ATR P70 Accepted')
plt.xlabel('CloseTime')
plt.ylabel('Equity JPY')
plt.legend()
plt.grid(True)
plt.show()

plt.figure(figsize=(14, 5))
plt.plot(base_sim['CloseTime'], base_sim['DrawdownPct'], label='Base')
plt.plot(accepted_sim['CloseTime'], accepted_sim['DrawdownPct'], label='Accepted H1 ATR P70')
plt.title('MoneySim Drawdown % - Base vs H1 ATR P70 Accepted')
plt.xlabel('CloseTime')
plt.ylabel('Drawdown %')
plt.legend()
plt.grid(True)
plt.show()

print('\n✅ money_filter_deep_dive_v1 completed.')
