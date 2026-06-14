# ==========================================
# Time Entry Portfolio Lab
# money_filter_logic_atr_select_v1.py
#
# 目的：
# - H1 ATR P70 全体適用より良い、
#   ロジック別ATRフィルタ構成を探す
#
# 探索対象：
# - 各Strategyごとに
#   NONE / P70 / P75 / P80 / P85 / P90 / P95
#   の候補を比較する
#
# 評価軸：
# - Full MoneyRoMD
# - OOS MoneyRoMD
# - Q1 MoneyRoMD
# - MaxDDPct
# - NetProfitYen
# - WorstWeekReturnPct
# - RejectedRate
# - Plateau判定
#
# 注意：
# - Q1だけ良い候補は採用しない
# - FullとOOSの両方で悪化しない候補を優先
# - トレード数が少なすぎるロジックは保留
#
# 入力：
# - /content/filter_test_v2_range_atr/Filter_v2_Feature_Attached_Trades.csv
# - /content/filter_test_v2_range_atr/Filter_v2_Thresholds_StrictIS.csv
#
# 出力：
# - /content/money_filter_logic_atr_select_v1/
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
CANDIDATE_PERCENTILES = [None, 70, 75, 80, 85, 90, 95]

MIN_STRATEGY_TRADES_FULL = 100
MIN_STRATEGY_TRADES_OOS = 10
MIN_ACCEPTED_RATE = 0.40

OUT_DIR = '/content/money_filter_logic_atr_select_v1'
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

FULL_START = pd.Timestamp('2015-01-01')
FULL_END = pd.Timestamp('2026-03-31 23:59:59')

OOS_START = pd.Timestamp('2025-01-01')
OOS_END = pd.Timestamp('2026-03-31 23:59:59')

Q1_START = pd.Timestamp('2026-01-01')
Q1_END = pd.Timestamp('2026-03-31 23:59:59')

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
# 5. 閾値マップ
# ==========================================

def build_threshold_map(thresholds_df, feature, percentile):
    th = thresholds_df[
        (thresholds_df['Feature'] == feature) &
        (thresholds_df['Percentile'] == percentile)
    ].copy()

    return {
        row['Pair']: row['Threshold']
        for _, row in th.iterrows()
    }


THRESHOLD_MAPS = {}

for pct in CANDIDATE_PERCENTILES:
    if pct is None:
        continue

    THRESHOLD_MAPS[pct] = build_threshold_map(
        thresholds,
        TARGET_FEATURE,
        pct
    )

# ==========================================
# 6. 週キー関数
# ==========================================

def get_trading_week_start(dt):
    dt = pd.Timestamp(dt)

    monday = dt.normalize() - pd.Timedelta(days=dt.weekday())
    week_start = monday + pd.Timedelta(hours=WEEK_ROLLOVER_HOUR)

    if dt < week_start:
        week_start = week_start - pd.Timedelta(days=7)

    return week_start

# ==========================================
# 7. MoneySim本体
# ==========================================

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

# ==========================================
# 8. 集計関数
# ==========================================

def get_equity_before_period(sim_df, period_start):
    before = sim_df[sim_df['CloseTime'] < period_start].copy()

    if before.empty:
        return INITIAL_CAPITAL

    return before['Equity'].iloc[-1]


def calc_period_metrics(sim_df, weekly_df, dataset_name, period_label, start, end):
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


def calc_all_period_metrics(sim_df, weekly_df, dataset_name):
    rows = []

    for p in PERIODS:
        rows.append(
            calc_period_metrics(
                sim_df=sim_df,
                weekly_df=weekly_df,
                dataset_name=dataset_name,
                period_label=p['label'],
                start=p['start'],
                end=p['end']
            )
        )

    return pd.DataFrame(rows)


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
            'AvgPips': np.nan
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
        'AvgPips': round(d['Pips'].mean(), 2)
    }

# ==========================================
# 9. ATRフィルタ適用
# ==========================================

def filter_strategy_by_percentile(strategy_df, percentile):
    d = strategy_df.copy()

    if percentile is None:
        d['ATR_Filter_Percentile'] = 'NONE'
        d['ATR_Filter_Threshold'] = np.nan
        d['ATR_Filter_Decision'] = 'Accepted'
        return d.copy(), pd.DataFrame()

    accepted_rows = []
    rejected_rows = []

    th_map = THRESHOLD_MAPS.get(percentile, {})

    for _, row in d.iterrows():
        pair = row['Pair']
        value = row[TARGET_FEATURE]
        threshold = th_map.get(pair, np.nan)

        row_dict = row.to_dict()
        row_dict['ATR_Filter_Percentile'] = percentile
        row_dict['ATR_Filter_Threshold'] = threshold

        if pd.isna(value) or pd.isna(threshold):
            row_dict['ATR_Filter_Decision'] = 'Rejected_Missing'
            row_dict['RejectReason'] = 'MissingATRorThreshold'
            rejected_rows.append(row_dict)
            continue

        if value > threshold:
            row_dict['ATR_Filter_Decision'] = 'Rejected'
            row_dict['RejectReason'] = f'H1_ATR_Over_P{percentile}'
            rejected_rows.append(row_dict)
        else:
            row_dict['ATR_Filter_Decision'] = 'Accepted'
            accepted_rows.append(row_dict)

    accepted = pd.DataFrame(accepted_rows)
    rejected = pd.DataFrame(rejected_rows)

    if not accepted.empty:
        accepted = accepted.sort_values('CloseTime').reset_index(drop=True)

    if not rejected.empty:
        rejected = rejected.sort_values('EntryTime').reset_index(drop=True)

    return accepted, rejected

# ==========================================
# 10. Strategy × Percentile 評価
# ==========================================

strategy_option_rows = []
strategy_option_period_rows = []

for strategy, strategy_df in df.groupby('Strategy'):
    strategy_df = strategy_df.copy()
    strategy_df = strategy_df.sort_values('CloseTime').reset_index(drop=True)

    base_count = len(strategy_df)
    base_pips = calc_pips_metrics(strategy_df, f'{strategy}_NONE')

    for pct in CANDIDATE_PERCENTILES:
        label_pct = 'NONE' if pct is None else f'P{pct}'
        option_name = f'{strategy}_{label_pct}'

        accepted, rejected = filter_strategy_by_percentile(strategy_df, pct)

        if accepted.empty:
            continue

        sim_df, weekly_df = run_weekly_fixed_risk_sim(accepted, option_name)

        if sim_df.empty:
            continue

        period_summary = calc_all_period_metrics(sim_df, weekly_df, option_name)
        strategy_option_period_rows.append(period_summary)

        full_row = period_summary[period_summary['Period'] == 'Full_2015_2026Q1'].iloc[0]
        oos_row = period_summary[period_summary['Period'] == 'StrictOOS_2025_2026Q1'].iloc[0]
        q1_row = period_summary[period_summary['Period'] == 'Q1_2026'].iloc[0]

        accepted_rate = len(accepted) / base_count if base_count > 0 else np.nan
        rejected_rate = len(rejected) / base_count if base_count > 0 else np.nan

        pips_m = calc_pips_metrics(accepted, option_name)

        full_trades = len(accepted)
        oos_trades = len(
            accepted[
                (accepted['CloseTime'] >= OOS_START) &
                (accepted['CloseTime'] <= OOS_END)
            ]
        )

        q1_trades = len(
            accepted[
                (accepted['CloseTime'] >= Q1_START) &
                (accepted['CloseTime'] <= Q1_END)
            ]
        )

        strategy_option_rows.append({
            'Strategy': strategy,
            'Group': strategy_df['Group'].iloc[0],
            'Option': label_pct,
            'Percentile': pct if pct is not None else 999,
            'BaseTrades': base_count,
            'AcceptedTrades': len(accepted),
            'RejectedTrades': len(rejected),
            'AcceptedRatePct': round(accepted_rate * 100, 2) if not pd.isna(accepted_rate) else np.nan,
            'RejectedRatePct': round(rejected_rate * 100, 2) if not pd.isna(rejected_rate) else np.nan,

            'Full_Trades': full_trades,
            'Full_MoneyRoMD': full_row['MoneyRoMD'],
            'Full_MaxDDPct': full_row['MaxDDPct'],
            'Full_NetProfitYen': full_row['NetProfitYen'],
            'Full_PF_Yen': full_row['PF_Yen'],
            'Full_WorstWeekReturnPct': full_row['WorstWeekReturnPct'],

            'OOS_Trades': oos_trades,
            'OOS_MoneyRoMD': oos_row['MoneyRoMD'],
            'OOS_MaxDDPct': oos_row['MaxDDPct'],
            'OOS_NetProfitYen': oos_row['NetProfitYen'],
            'OOS_PF_Yen': oos_row['PF_Yen'],
            'OOS_WorstWeekReturnPct': oos_row['WorstWeekReturnPct'],

            'Q1_Trades': q1_trades,
            'Q1_MoneyRoMD': q1_row['MoneyRoMD'],
            'Q1_MaxDDPct': q1_row['MaxDDPct'],
            'Q1_NetProfitYen': q1_row['NetProfitYen'],
            'Q1_PF_Yen': q1_row['PF_Yen'],
            'Q1_WorstWeekReturnPct': q1_row['WorstWeekReturnPct'],

            'Pips_Total': pips_m['TotalPips'],
            'Pips_PF': pips_m['PF'],
            'Pips_RoMD': pips_m['RoMD'],
            'Pips_Avg': pips_m['AvgPips']
        })

strategy_options = pd.DataFrame(strategy_option_rows)

if strategy_option_period_rows:
    strategy_option_period_summary = pd.concat(strategy_option_period_rows).reset_index(drop=True)
else:
    strategy_option_period_summary = pd.DataFrame()

# ==========================================
# 11. ベース差分付与
# ==========================================

def add_strategy_base_deltas(options_df):
    d = options_df.copy()

    delta_rows = []

    for strategy, sub in d.groupby('Strategy'):
        base = sub[sub['Option'] == 'NONE']

        if base.empty:
            continue

        base = base.iloc[0]

        for _, row in sub.iterrows():
            r = row.to_dict()

            for col in [
                'Full_MoneyRoMD',
                'Full_MaxDDPct',
                'Full_NetProfitYen',
                'OOS_MoneyRoMD',
                'OOS_MaxDDPct',
                'OOS_NetProfitYen',
                'Q1_MoneyRoMD',
                'Q1_MaxDDPct',
                'Q1_NetProfitYen'
            ]:
                r[f'Delta_{col}'] = row[col] - base[col]

            delta_rows.append(r)

    return pd.DataFrame(delta_rows)


strategy_options = add_strategy_base_deltas(strategy_options)

# ==========================================
# 12. プラトー判定
# ==========================================

def classify_plateau(strategy_sub):
    """
    P70〜P95のOOS MoneyRoMDを中心に、なだらかに良い領域があるかを見る。
    厳密な統計判定ではなく、過剰最適化チェック用の実務判定。
    """
    pct_sub = strategy_sub[strategy_sub['Option'] != 'NONE'].copy()

    if pct_sub.empty:
        return {
            'PlateauFlag': 'NoATRChoices',
            'PlateauOptions': '',
            'PlateauCount': 0,
            'BestOptionByOOS': '',
            'BestOOSMoneyRoMD': np.nan
        }

    pct_sub = pct_sub.sort_values('Percentile').reset_index(drop=True)

    valid = pct_sub[
        (pct_sub['OOS_Trades'] >= MIN_STRATEGY_TRADES_OOS) &
        (pct_sub['AcceptedRatePct'] >= MIN_ACCEPTED_RATE * 100)
    ].copy()

    if valid.empty:
        best = pct_sub.sort_values('OOS_MoneyRoMD', ascending=False).iloc[0]

        return {
            'PlateauFlag': 'TooFewValidChoices',
            'PlateauOptions': '',
            'PlateauCount': 0,
            'BestOptionByOOS': best['Option'],
            'BestOOSMoneyRoMD': best['OOS_MoneyRoMD']
        }

    best_oos = valid['OOS_MoneyRoMD'].max()
    best_row = valid[valid['OOS_MoneyRoMD'] == best_oos].iloc[0]

    # ベストの90%以上のOOS MoneyRoMDを持つ候補をプラトー候補にする
    if pd.isna(best_oos) or best_oos <= 0:
        near_best = valid.iloc[0:0].copy()
    else:
        near_best = valid[valid['OOS_MoneyRoMD'] >= best_oos * 0.90].copy()

    plateau_options = near_best['Option'].tolist()
    plateau_count = len(plateau_options)

    # 隣接するパーセンタイルが2つ以上あればPlateau扱い
    pct_values = []

    for opt in plateau_options:
        if isinstance(opt, str) and opt.startswith('P'):
            pct_values.append(int(opt.replace('P', '')))

    pct_values = sorted(pct_values)

    has_adjacent = False

    for i in range(1, len(pct_values)):
        if pct_values[i] - pct_values[i - 1] == 5:
            has_adjacent = True

    if plateau_count >= 3:
        flag = 'StrongPlateau'
    elif plateau_count >= 2 and has_adjacent:
        flag = 'Plateau'
    elif plateau_count >= 2:
        flag = 'WeakPlateau'
    else:
        flag = 'SinglePeak'

    return {
        'PlateauFlag': flag,
        'PlateauOptions': ','.join(plateau_options),
        'PlateauCount': plateau_count,
        'BestOptionByOOS': best_row['Option'],
        'BestOOSMoneyRoMD': best_row['OOS_MoneyRoMD']
    }


plateau_rows = []

for strategy, sub in strategy_options.groupby('Strategy'):
    result = classify_plateau(sub)
    result['Strategy'] = strategy
    result['Group'] = sub['Group'].iloc[0]
    plateau_rows.append(result)

plateau_summary = pd.DataFrame(plateau_rows)

# ==========================================
# 13. ロジック別推奨Option選定
# ==========================================

def choose_strategy_option(strategy_sub, plateau_info):
    """
    選定方針：
    - Full/OOSが両方悪化しすぎない
    - Q1だけ改善のものは避ける
    - OOSトレード数が少ないものは避ける
    - プラトーがある場合は、ベスト単発ではなくプラトー内の中庸を選ぶ
    - 迷ったらNONE
    """
    sub = strategy_sub.copy()

    base = sub[sub['Option'] == 'NONE']

    if base.empty:
        return {
            'SelectedOption': 'NONE',
            'SelectionReason': 'BaseMissing'
        }

    base = base.iloc[0]

    # 母数が少ないロジックは保留
    if base['BaseTrades'] < MIN_STRATEGY_TRADES_FULL:
        return {
            'SelectedOption': 'NONE',
            'SelectionReason': 'Hold_TooFewFullTrades'
        }

    # OOSが少なすぎるロジックは保留
    if base['OOS_Trades'] < MIN_STRATEGY_TRADES_OOS:
        return {
            'SelectedOption': 'NONE',
            'SelectionReason': 'Hold_TooFewOOSTrades'
        }

    candidates = sub[sub['Option'] != 'NONE'].copy()

    if candidates.empty:
        return {
            'SelectedOption': 'NONE',
            'SelectionReason': 'NoATRCandidates'
        }

    # 基本条件
    candidates = candidates[
        (candidates['OOS_Trades'] >= MIN_STRATEGY_TRADES_OOS) &
        (candidates['AcceptedRatePct'] >= MIN_ACCEPTED_RATE * 100)
    ].copy()

    if candidates.empty:
        return {
            'SelectedOption': 'NONE',
            'SelectionReason': 'NoCandidateAfterTradeRateFilter'
        }

    # FullとOOSの両方でMoneyRoMDがBase以上、またはDDが大きく改善
    candidates['Full_OK'] = candidates['Full_MoneyRoMD'] >= base['Full_MoneyRoMD'] * 0.95
    candidates['OOS_OK'] = candidates['OOS_MoneyRoMD'] >= base['OOS_MoneyRoMD'] * 0.95

    candidates['Full_DD_OK'] = candidates['Full_MaxDDPct'] <= base['Full_MaxDDPct']
    candidates['OOS_DD_OK'] = candidates['OOS_MaxDDPct'] <= base['OOS_MaxDDPct']

    candidates['Q1_Only_Risk'] = (
        (candidates['Q1_MoneyRoMD'] > base['Q1_MoneyRoMD']) &
        (candidates['Full_MoneyRoMD'] < base['Full_MoneyRoMD'] * 0.95) &
        (candidates['OOS_MoneyRoMD'] < base['OOS_MoneyRoMD'] * 0.95)
    )

    candidates = candidates[
        (candidates['Q1_Only_Risk'] == False) &
        (
            (
                (candidates['Full_OK']) &
                (candidates['OOS_OK'])
            ) |
            (
                (candidates['Full_DD_OK']) &
                (candidates['OOS_DD_OK']) &
                (candidates['OOS_MoneyRoMD'] >= base['OOS_MoneyRoMD'])
            )
        )
    ].copy()

    if candidates.empty:
        return {
            'SelectedOption': 'NONE',
            'SelectionReason': 'NoRobustCandidate'
        }

    # プラトーがある場合は、プラトー内候補を優先
    plateau_options = []

    if isinstance(plateau_info.get('PlateauOptions', ''), str):
        if plateau_info.get('PlateauOptions', '') != '':
            plateau_options = plateau_info['PlateauOptions'].split(',')

    plateau_candidates = candidates[candidates['Option'].isin(plateau_options)].copy()

    if not plateau_candidates.empty:
        # プラトー内でOOS MoneyRoMD上位、かつDD低めを選ぶ
        plateau_candidates['Score'] = (
            plateau_candidates['OOS_MoneyRoMD'].fillna(0) * 2.0 +
            plateau_candidates['Full_MoneyRoMD'].fillna(0) * 1.0 +
            plateau_candidates['Q1_MoneyRoMD'].fillna(0) * 0.5 -
            plateau_candidates['OOS_MaxDDPct'].fillna(0) * 0.05
        )

        selected = plateau_candidates.sort_values('Score', ascending=False).iloc[0]

        return {
            'SelectedOption': selected['Option'],
            'SelectionReason': f'PlateauBased_{plateau_info.get("PlateauFlag", "")}'
        }

    # プラトーがなければ、単発ピークは避けて控えめに選ぶ
    candidates['Score'] = (
        candidates['OOS_MoneyRoMD'].fillna(0) * 2.0 +
        candidates['Full_MoneyRoMD'].fillna(0) * 1.0 +
        candidates['Q1_MoneyRoMD'].fillna(0) * 0.25 -
        candidates['OOS_MaxDDPct'].fillna(0) * 0.05
    )

    selected = candidates.sort_values('Score', ascending=False).iloc[0]

    if plateau_info.get('PlateauFlag') == 'SinglePeak':
        return {
            'SelectedOption': 'NONE',
            'SelectionReason': 'AvoidSinglePeak'
        }

    return {
        'SelectedOption': selected['Option'],
        'SelectionReason': 'ScoreBasedNoPlateau'
    }


selection_rows = []

for strategy, sub in strategy_options.groupby('Strategy'):
    pinfo_row = plateau_summary[plateau_summary['Strategy'] == strategy]

    if pinfo_row.empty:
        pinfo = {}
    else:
        pinfo = pinfo_row.iloc[0].to_dict()

    selected = choose_strategy_option(sub, pinfo)

    base = sub[sub['Option'] == 'NONE'].iloc[0]

    selected_row = sub[sub['Option'] == selected['SelectedOption']]

    if selected_row.empty:
        selected_metrics = base
    else:
        selected_metrics = selected_row.iloc[0]

    selection_rows.append({
        'Strategy': strategy,
        'Group': sub['Group'].iloc[0],
        'SelectedOption': selected['SelectedOption'],
        'SelectionReason': selected['SelectionReason'],
        'PlateauFlag': pinfo.get('PlateauFlag', ''),
        'PlateauOptions': pinfo.get('PlateauOptions', ''),
        'Base_Full_MoneyRoMD': base['Full_MoneyRoMD'],
        'Selected_Full_MoneyRoMD': selected_metrics['Full_MoneyRoMD'],
        'Base_OOS_MoneyRoMD': base['OOS_MoneyRoMD'],
        'Selected_OOS_MoneyRoMD': selected_metrics['OOS_MoneyRoMD'],
        'Base_Q1_MoneyRoMD': base['Q1_MoneyRoMD'],
        'Selected_Q1_MoneyRoMD': selected_metrics['Q1_MoneyRoMD'],
        'Base_Full_MaxDDPct': base['Full_MaxDDPct'],
        'Selected_Full_MaxDDPct': selected_metrics['Full_MaxDDPct'],
        'Base_OOS_MaxDDPct': base['OOS_MaxDDPct'],
        'Selected_OOS_MaxDDPct': selected_metrics['OOS_MaxDDPct'],
        'Base_Q1_MaxDDPct': base['Q1_MaxDDPct'],
        'Selected_Q1_MaxDDPct': selected_metrics['Q1_MaxDDPct'],
        'AcceptedRatePct': selected_metrics['AcceptedRatePct']
    })

strategy_selection = pd.DataFrame(selection_rows)

# ==========================================
# 14. 選定結果でポートフォリオ再構築
# ==========================================

def apply_logic_specific_selection(input_df, selection_df):
    accepted_rows = []
    rejected_rows = []

    selection_map = {
        row['Strategy']: row['SelectedOption']
        for _, row in selection_df.iterrows()
    }

    for _, row in input_df.iterrows():
        strategy = row['Strategy']
        option = selection_map.get(strategy, 'NONE')

        row_dict = row.to_dict()
        row_dict['LogicATR_SelectedOption'] = option

        if option == 'NONE':
            row_dict['LogicATR_Decision'] = 'Accepted'
            accepted_rows.append(row_dict)
            continue

        pct = int(option.replace('P', ''))
        pair = row['Pair']
        value = row[TARGET_FEATURE]
        threshold = THRESHOLD_MAPS[pct].get(pair, np.nan)

        row_dict['LogicATR_Threshold'] = threshold

        if pd.isna(value) or pd.isna(threshold):
            row_dict['LogicATR_Decision'] = 'Rejected_Missing'
            row_dict['RejectReason'] = 'MissingATRorThreshold'
            rejected_rows.append(row_dict)
            continue

        if value > threshold:
            row_dict['LogicATR_Decision'] = 'Rejected'
            row_dict['RejectReason'] = f'H1_ATR_Over_{option}'
            rejected_rows.append(row_dict)
        else:
            row_dict['LogicATR_Decision'] = 'Accepted'
            accepted_rows.append(row_dict)

    accepted = pd.DataFrame(accepted_rows)
    rejected = pd.DataFrame(rejected_rows)

    if not accepted.empty:
        accepted = accepted.sort_values('CloseTime').reset_index(drop=True)

    if not rejected.empty:
        rejected = rejected.sort_values('EntryTime').reset_index(drop=True)

    return accepted, rejected


logic_atr_accepted, logic_atr_rejected = apply_logic_specific_selection(df, strategy_selection)

# ==========================================
# 15. 比較用ポートフォリオ作成
# ==========================================

def apply_global_atr_filter(input_df, percentile):
    accepted_rows = []
    rejected_rows = []

    th_map = THRESHOLD_MAPS[percentile]

    for _, row in input_df.iterrows():
        pair = row['Pair']
        value = row[TARGET_FEATURE]
        threshold = th_map.get(pair, np.nan)

        row_dict = row.to_dict()
        row_dict['GlobalATR_Percentile'] = percentile
        row_dict['GlobalATR_Threshold'] = threshold

        if pd.isna(value) or pd.isna(threshold):
            row_dict['GlobalATR_Decision'] = 'Rejected_Missing'
            row_dict['RejectReason'] = 'MissingATRorThreshold'
            rejected_rows.append(row_dict)
            continue

        if value > threshold:
            row_dict['GlobalATR_Decision'] = 'Rejected'
            row_dict['RejectReason'] = f'H1_ATR_Over_P{percentile}'
            rejected_rows.append(row_dict)
        else:
            row_dict['GlobalATR_Decision'] = 'Accepted'
            accepted_rows.append(row_dict)

    accepted = pd.DataFrame(accepted_rows)
    rejected = pd.DataFrame(rejected_rows)

    if not accepted.empty:
        accepted = accepted.sort_values('CloseTime').reset_index(drop=True)

    if not rejected.empty:
        rejected = rejected.sort_values('EntryTime').reset_index(drop=True)

    return accepted, rejected


global_p70_accepted, global_p70_rejected = apply_global_atr_filter(df, 70)
global_p75_accepted, global_p75_rejected = apply_global_atr_filter(df, 75)
global_p80_accepted, global_p80_rejected = apply_global_atr_filter(df, 80)

portfolio_sets = [
    {
        'Name': 'Base_NoFilter',
        'Accepted': df.copy(),
        'Rejected': pd.DataFrame()
    },
    {
        'Name': 'Global_H1_ATR_P70',
        'Accepted': global_p70_accepted,
        'Rejected': global_p70_rejected
    },
    {
        'Name': 'Global_H1_ATR_P75',
        'Accepted': global_p75_accepted,
        'Rejected': global_p75_rejected
    },
    {
        'Name': 'Global_H1_ATR_P80',
        'Accepted': global_p80_accepted,
        'Rejected': global_p80_rejected
    },
    {
        'Name': 'LogicSpecific_ATR_Selected',
        'Accepted': logic_atr_accepted,
        'Rejected': logic_atr_rejected
    }
]

portfolio_period_rows = []
portfolio_summary_rows = []
portfolio_weekly_rows = []

sim_outputs = {}

for item in portfolio_sets:
    name = item['Name']
    accepted = item['Accepted']
    rejected = item['Rejected']

    sim_df, weekly_df = run_weekly_fixed_risk_sim(accepted, name)

    if sim_df.empty:
        continue

    period_summary = calc_all_period_metrics(sim_df, weekly_df, name)
    portfolio_period_rows.append(period_summary)

    weekly_df['PortfolioSet'] = name
    portfolio_weekly_rows.append(weekly_df)

    sim_outputs[name] = sim_df

    full_row = period_summary[period_summary['Period'] == 'Full_2015_2026Q1'].iloc[0]
    oos_row = period_summary[period_summary['Period'] == 'StrictOOS_2025_2026Q1'].iloc[0]
    q1_row = period_summary[period_summary['Period'] == 'Q1_2026'].iloc[0]

    portfolio_summary_rows.append({
        'PortfolioSet': name,
        'AcceptedTrades': len(accepted),
        'RejectedTrades': len(rejected),
        'RejectedRatePct': round(len(rejected) / (len(accepted) + len(rejected)) * 100, 2) if (len(accepted) + len(rejected)) > 0 else 0,

        'Full_NetProfitYen': full_row['NetProfitYen'],
        'Full_MaxDDPct': full_row['MaxDDPct'],
        'Full_MoneyRoMD': full_row['MoneyRoMD'],
        'Full_WorstWeekReturnPct': full_row['WorstWeekReturnPct'],

        'OOS_NetProfitYen': oos_row['NetProfitYen'],
        'OOS_MaxDDPct': oos_row['MaxDDPct'],
        'OOS_MoneyRoMD': oos_row['MoneyRoMD'],
        'OOS_WorstWeekReturnPct': oos_row['WorstWeekReturnPct'],

        'Q1_NetProfitYen': q1_row['NetProfitYen'],
        'Q1_MaxDDPct': q1_row['MaxDDPct'],
        'Q1_MoneyRoMD': q1_row['MoneyRoMD'],
        'Q1_WorstWeekReturnPct': q1_row['WorstWeekReturnPct']
    })

portfolio_period_summary = pd.concat(portfolio_period_rows).reset_index(drop=True)
portfolio_summary = pd.DataFrame(portfolio_summary_rows)

if portfolio_weekly_rows:
    portfolio_weekly = pd.concat(portfolio_weekly_rows).reset_index(drop=True)
else:
    portfolio_weekly = pd.DataFrame()

# ==========================================
# 16. 保存
# ==========================================

strategy_options.to_csv(f'{OUT_DIR}/LogicATR_Strategy_Option_Evaluation.csv', index=False)
strategy_option_period_summary.to_csv(f'{OUT_DIR}/LogicATR_Strategy_Option_PeriodSummary.csv', index=False)
plateau_summary.to_csv(f'{OUT_DIR}/LogicATR_Plateau_Summary.csv', index=False)
strategy_selection.to_csv(f'{OUT_DIR}/LogicATR_Strategy_Selection.csv', index=False)

logic_atr_accepted.to_csv(f'{OUT_DIR}/LogicATR_Selected_Accepted_Trades.csv', index=False)
logic_atr_rejected.to_csv(f'{OUT_DIR}/LogicATR_Selected_Rejected_Trades.csv', index=False)

portfolio_summary.to_csv(f'{OUT_DIR}/LogicATR_Portfolio_Comparison_Summary.csv', index=False)
portfolio_period_summary.to_csv(f'{OUT_DIR}/LogicATR_Portfolio_Comparison_PeriodSummary.csv', index=False)
portfolio_weekly.to_csv(f'{OUT_DIR}/LogicATR_Portfolio_Comparison_Weekly.csv', index=False)

global_p70_accepted.to_csv(f'{OUT_DIR}/Global_H1_ATR_P70_Accepted_Trades.csv', index=False)
global_p70_rejected.to_csv(f'{OUT_DIR}/Global_H1_ATR_P70_Rejected_Trades.csv', index=False)

print('\n' + '=' * 100)
print('✅ Logic ATR Select v1 CSV保存完了')
print('=' * 100)
print(f'Output dir: {OUT_DIR}')
print('Main files:')
print('- LogicATR_Strategy_Option_Evaluation.csv')
print('- LogicATR_Plateau_Summary.csv')
print('- LogicATR_Strategy_Selection.csv')
print('- LogicATR_Portfolio_Comparison_Summary.csv')
print('- LogicATR_Portfolio_Comparison_PeriodSummary.csv')
print('- LogicATR_Selected_Accepted_Trades.csv')
print('- LogicATR_Selected_Rejected_Trades.csv')

# ==========================================
# 17. 表示
# ==========================================

print('\n' + '=' * 100)
print('Portfolio Comparison Summary')
print('=' * 100)
print(portfolio_summary.sort_values('OOS_MoneyRoMD', ascending=False).to_string(index=False))

print('\n' + '=' * 100)
print('Strategy Selection')
print('=' * 100)
print(strategy_selection.to_string(index=False))

print('\n' + '=' * 100)
print('Plateau Summary')
print('=' * 100)
print(plateau_summary.to_string(index=False))

# ==========================================
# 18. グラフ
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

print('\n✅ money_filter_logic_atr_select_v1 completed.')
