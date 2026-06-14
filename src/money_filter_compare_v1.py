# ==========================================
# Time Entry Portfolio Lab
# money_filter_compare_v1.py
#
# 目的：
# - Filter v1 / Filter v2 の全候補を
#   pips評価ではなく、損失額固定型・週次複利の円ベースで再評価する
#
# 前提：
# - 初期資金：500,000円
# - 1トレードリスク：週初残高の2%
# - 複利更新：月曜06:00 JST
# - 同時保有：各トレード同じ週の固定リスク額
#
# 主な比較指標：
# - FinalEquity
# - NetProfitYen
# - MaxDDYen
# - MaxDDPct
# - Money RoMD
# - OOS Money RoMD
# - Q1 Money RoMD
# - Worst WeekReturnPct
#
# 入力：
# - /content/Portfolio_Integration_Results_v1_2_add_aussie_logic.csv
# - /content/filter_test_v2_range_atr/Filter_v2_Feature_Attached_Trades.csv
# - /content/filter_test_v2_range_atr/Filter_v2_Thresholds_StrictIS.csv
#
# 出力：
# - /content/money_filter_compare_v1/
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

OUT_DIR = '/content/money_filter_compare_v1'
os.makedirs(OUT_DIR, exist_ok=True)

# ==========================================
# 2. 入力CSV
# ==========================================

BASE_TRADE_CSV = '/content/Portfolio_Integration_Results_v1_2_add_aussie_logic.csv'

FILTER_V2_FEATURE_CSV = '/content/filter_test_v2_range_atr/Filter_v2_Feature_Attached_Trades.csv'
FILTER_V2_THRESHOLD_CSV = '/content/filter_test_v2_range_atr/Filter_v2_Thresholds_StrictIS.csv'

# Google Driveに保存している場合は、必要に応じて上のpathを変更してください。

if not os.path.exists(BASE_TRADE_CSV):
    raise FileNotFoundError(f'Base trade CSV not found: {BASE_TRADE_CSV}')

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
# 4. 読み込み
# ==========================================

base_df = pd.read_csv(BASE_TRADE_CSV)

base_df['EntryTime'] = pd.to_datetime(base_df['EntryTime'])
base_df['CloseTime'] = pd.to_datetime(base_df['CloseTime'])

base_df = base_df.sort_values(['EntryTime', 'CloseTime']).reset_index(drop=True)

required_cols = [
    'Strategy',
    'Pair',
    'Direction',
    'EntryTime',
    'CloseTime',
    'Pips',
    'SL'
]

missing_cols = [c for c in required_cols if c not in base_df.columns]

if missing_cols:
    raise ValueError(f'Base CSV missing columns: {missing_cols}')

print('✅ Base trade CSV loaded')
print(f'Rows: {len(base_df):,}')
print(f"Period: {base_df['CloseTime'].min()} 〜 {base_df['CloseTime'].max()}")

if os.path.exists(FILTER_V2_FEATURE_CSV):
    feature_df = pd.read_csv(FILTER_V2_FEATURE_CSV)
    feature_df['EntryTime'] = pd.to_datetime(feature_df['EntryTime'])
    feature_df['CloseTime'] = pd.to_datetime(feature_df['CloseTime'])
    feature_df = feature_df.sort_values(['EntryTime', 'CloseTime']).reset_index(drop=True)
    print('✅ Filter v2 feature CSV loaded')
else:
    feature_df = None
    print('⚠️ Filter v2 feature CSV not found. Filter v2 tests will be skipped.')

if os.path.exists(FILTER_V2_THRESHOLD_CSV):
    thresholds_df = pd.read_csv(FILTER_V2_THRESHOLD_CSV)
    print('✅ Filter v2 thresholds CSV loaded')
else:
    thresholds_df = None
    print('⚠️ Filter v2 thresholds CSV not found. Filter v2 tests will be skipped.')

# ==========================================
# 5. 週キー関数
# ==========================================

def get_trading_week_start(dt):
    dt = pd.Timestamp(dt)

    monday = dt.normalize() - pd.Timedelta(days=dt.weekday())
    week_start = monday + pd.Timedelta(hours=WEEK_ROLLOVER_HOUR)

    if dt < week_start:
        week_start = week_start - pd.Timedelta(days=7)

    return week_start

# ==========================================
# 6. エクスポージャー定義
# ==========================================

def get_jpy_exposure(pair, direction):
    if pair not in ['EJ', 'GJ', 'AJ', 'UJ']:
        return None

    if direction == 'Long':
        return 'JPY_Sell'

    if direction == 'Short':
        return 'JPY_Buy'

    return None


def get_aud_exposure(pair, direction):
    if pair == 'AJ':
        if direction == 'Long':
            return 'AUD_Buy'
        if direction == 'Short':
            return 'AUD_Sell'

    if pair == 'AU':
        if direction == 'Long':
            return 'AUD_Buy'
        if direction == 'Short':
            return 'AUD_Sell'

    if pair == 'EA':
        if direction == 'Long':
            return 'AUD_Sell'
        if direction == 'Short':
            return 'AUD_Buy'

    if pair == 'GA':
        if direction == 'Long':
            return 'AUD_Sell'
        if direction == 'Short':
            return 'AUD_Buy'

    return None


def attach_exposure_columns(df):
    d = df.copy()
    d['EntryDate'] = d['EntryTime'].dt.date
    d['JPYExposure'] = d.apply(lambda r: get_jpy_exposure(r['Pair'], r['Direction']), axis=1)
    d['AUDExposure'] = d.apply(lambda r: get_aud_exposure(r['Pair'], r['Direction']), axis=1)
    return d

base_df = attach_exposure_columns(base_df)

if feature_df is not None:
    feature_df = attach_exposure_columns(feature_df)

# ==========================================
# 7. MoneySim本体
# ==========================================

def run_weekly_fixed_risk_sim(trades_df, dataset_name):
    df = trades_df.copy()

    df['EntryTime'] = pd.to_datetime(df['EntryTime'])
    df['CloseTime'] = pd.to_datetime(df['CloseTime'])

    df = df.sort_values(['EntryTime', 'CloseTime']).reset_index(drop=True)

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

    sim_df['Equity'] = INITIAL_CAPITAL + sim_df['YenPnL'].cumsum()
    sim_df['PeakEquity'] = sim_df['Equity'].cummax()
    sim_df['DrawdownYen'] = sim_df['PeakEquity'] - sim_df['Equity']
    sim_df['DrawdownPct'] = sim_df['DrawdownYen'] / sim_df['PeakEquity'] * 100
    sim_df['TradeReturnPctOnWeekStart'] = sim_df['YenPnL'] / sim_df['WeekStartBalance'] * 100

    return sim_df, weekly_df

# ==========================================
# 8. 期間集計
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
            'WinRate': np.nan,
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

    win_rate = len(d[d['YenPnL'] > 0]) / len(d) * 100

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
        'WinRate': round(win_rate, 2),
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

# ==========================================
# 9. Filter v1 再構築
# ==========================================

def apply_daily_exposure_filter(
    input_df,
    max_trades_per_day=None,
    max_jpy_same_direction=None,
    max_aud_same_direction=None
):
    d = input_df.copy()
    d = d.sort_values(['EntryDate', 'EntryTime', 'CloseTime']).copy()

    accepted_rows = []
    rejected_rows = []

    for entry_date, day_df in d.groupby('EntryDate'):
        accepted_count = 0
        jpy_counts = {}
        aud_counts = {}

        for _, row in day_df.iterrows():
            reject_reason = None

            if max_trades_per_day is not None:
                if accepted_count >= max_trades_per_day:
                    reject_reason = 'MaxTradesPerDay'

            if reject_reason is None and max_jpy_same_direction is not None:
                exp = row['JPYExposure']

                if exp is not None:
                    current_count = jpy_counts.get(exp, 0)

                    if current_count >= max_jpy_same_direction:
                        reject_reason = f'MaxJPY_{exp}'

            if reject_reason is None and max_aud_same_direction is not None:
                exp = row['AUDExposure']

                if exp is not None:
                    current_count = aud_counts.get(exp, 0)

                    if current_count >= max_aud_same_direction:
                        reject_reason = f'MaxAUD_{exp}'

            row_dict = row.to_dict()

            if reject_reason is None:
                accepted_rows.append(row_dict)
                accepted_count += 1

                if row['JPYExposure'] is not None:
                    jpy_counts[row['JPYExposure']] = jpy_counts.get(row['JPYExposure'], 0) + 1

                if row['AUDExposure'] is not None:
                    aud_counts[row['AUDExposure']] = aud_counts.get(row['AUDExposure'], 0) + 1

            else:
                row_dict['RejectReason'] = reject_reason
                rejected_rows.append(row_dict)

    accepted = pd.DataFrame(accepted_rows)
    rejected = pd.DataFrame(rejected_rows)

    if not accepted.empty:
        accepted = accepted.sort_values('CloseTime').reset_index(drop=True)

    if not rejected.empty:
        rejected = rejected.sort_values('EntryTime').reset_index(drop=True)

    return accepted, rejected

# ==========================================
# 10. Filter v2 再構築
# ==========================================

def apply_upper_percentile_filter(input_df, thresholds, feature, percentile):
    d = input_df.copy()

    th = thresholds[
        (thresholds['Feature'] == feature) &
        (thresholds['Percentile'] == percentile)
    ].copy()

    th_map = {
        row['Pair']: row['Threshold']
        for _, row in th.iterrows()
    }

    accepted_rows = []
    rejected_rows = []

    for _, row in d.iterrows():
        pair = row['Pair']
        value = row.get(feature, np.nan)
        threshold = th_map.get(pair, np.nan)

        row_dict = row.to_dict()
        row_dict['FilterFeature'] = feature
        row_dict['FilterPercentile'] = percentile
        row_dict['FilterThreshold'] = threshold

        if pd.isna(value) or pd.isna(threshold):
            row_dict['RejectReason'] = 'MissingFeatureOrThreshold'
            rejected_rows.append(row_dict)
            continue

        if value > threshold:
            row_dict['RejectReason'] = f'{feature}_Over_P{percentile}'
            rejected_rows.append(row_dict)
        else:
            accepted_rows.append(row_dict)

    accepted = pd.DataFrame(accepted_rows)
    rejected = pd.DataFrame(rejected_rows)

    if not accepted.empty:
        accepted = accepted.sort_values('CloseTime').reset_index(drop=True)

    if not rejected.empty:
        rejected = rejected.sort_values('EntryTime').reset_index(drop=True)

    return accepted, rejected

# ==========================================
# 11. テスト候補作成
# ==========================================

configs = []

configs.append({
    'name': 'Base_NoFilter',
    'type': 'base',
    'source': 'base'
})

# Filter v1候補
configs.append({
    'name': 'V1_MaxJPYSameDir_3',
    'type': 'v1',
    'max_trades_per_day': None,
    'max_jpy_same_direction': 3,
    'max_aud_same_direction': None
})

configs.append({
    'name': 'V1_MaxTrades_7',
    'type': 'v1',
    'max_trades_per_day': 7,
    'max_jpy_same_direction': None,
    'max_aud_same_direction': None
})

configs.append({
    'name': 'V1_MaxTrades_7_JPY_3_AUD_3',
    'type': 'v1',
    'max_trades_per_day': 7,
    'max_jpy_same_direction': 3,
    'max_aud_same_direction': 3
})

# Filter v1を広めに追加
for max_trades in [5, 6, 7, 8]:
    for max_jpy in [2, 3]:
        for max_aud in [2, 3]:
            configs.append({
                'name': f'V1_MaxTrades_{max_trades}_JPY_{max_jpy}_AUD_{max_aud}',
                'type': 'v1',
                'max_trades_per_day': max_trades,
                'max_jpy_same_direction': max_jpy,
                'max_aud_same_direction': max_aud
            })

# Filter v2候補
if feature_df is not None and thresholds_df is not None:
    v2_features = [
        'PrevDayRangePips',
        'Range24hPips',
        'DayToEntryRangePips',
        'H1_ATR14_Pips'
    ]

    v2_percentiles = [70, 75, 80, 85, 90, 95]

    for feature in v2_features:
        for pct in v2_percentiles:
            configs.append({
                'name': f'V2_{feature}_LTE_P{pct}',
                'type': 'v2',
                'feature': feature,
                'percentile': pct
            })

# 重複名削除
seen = set()
unique_configs = []

for cfg in configs:
    if cfg['name'] not in seen:
        unique_configs.append(cfg)
        seen.add(cfg['name'])

configs = unique_configs

print(f'✅ Configs prepared: {len(configs)}')

# ==========================================
# 12. 実行
# ==========================================

all_period_rows = []
all_weekly_rows = []
summary_rows = []

accepted_outputs = {}
rejected_outputs = {}

for cfg in configs:
    name = cfg['name']
    cfg_type = cfg['type']

    print('\n' + '=' * 100)
    print(f'Running Money Filter Compare: {name}')
    print('=' * 100)

    if cfg_type == 'base':
        accepted = base_df.copy()
        rejected = pd.DataFrame()

    elif cfg_type == 'v1':
        accepted, rejected = apply_daily_exposure_filter(
            base_df,
            max_trades_per_day=cfg['max_trades_per_day'],
            max_jpy_same_direction=cfg['max_jpy_same_direction'],
            max_aud_same_direction=cfg['max_aud_same_direction']
        )

    elif cfg_type == 'v2':
        if feature_df is None or thresholds_df is None:
            print(f'⚠️ skip v2 config because feature/threshold CSV missing: {name}')
            continue

        accepted, rejected = apply_upper_percentile_filter(
            feature_df,
            thresholds_df,
            feature=cfg['feature'],
            percentile=cfg['percentile']
        )

    else:
        continue

    if accepted.empty:
        print(f'⚠️ accepted trades empty: {name}')
        continue

    sim_df, weekly_df = run_weekly_fixed_risk_sim(accepted, name)

    if sim_df.empty:
        print(f'⚠️ sim empty: {name}')
        continue

    period_summary = calc_all_period_metrics(sim_df, weekly_df, name)

    all_period_rows.append(period_summary)

    weekly_df['Config'] = name
    all_weekly_rows.append(weekly_df)

    # ランキング用に横持ち化
    row = {
        'Config': name,
        'Type': cfg_type,
        'AcceptedTrades': len(accepted),
        'RejectedTrades': len(rejected),
        'RejectedRatePct': round(len(rejected) / (len(accepted) + len(rejected)) * 100, 2) if (len(accepted) + len(rejected)) > 0 else 0
    }

    for _, p in period_summary.iterrows():
        period = p['Period']

        prefix = None

        if period == 'Full_2015_2026Q1':
            prefix = 'Full'
        elif period == 'StrictIS_2015_2024':
            prefix = 'IS'
        elif period == 'StrictOOS_2025_2026Q1':
            prefix = 'OOS'
        elif period == 'Q1_2026':
            prefix = 'Q1'

        if prefix is not None:
            row[f'{prefix}_Trades'] = p['Trades']
            row[f'{prefix}_EndEquity'] = p['EndEquity']
            row[f'{prefix}_NetProfitYen'] = p['NetProfitYen']
            row[f'{prefix}_ReturnPct'] = p['ReturnPct']
            row[f'{prefix}_MaxDDYen'] = p['MaxDDYen']
            row[f'{prefix}_MaxDDPct'] = p['MaxDDPct']
            row[f'{prefix}_MoneyRoMD'] = p['MoneyRoMD']
            row[f'{prefix}_PF_Yen'] = p['PF_Yen']
            row[f'{prefix}_WorstWeekReturnPct'] = p['WorstWeekReturnPct']

    summary_rows.append(row)

    accepted_outputs[name] = accepted
    rejected_outputs[name] = rejected

# ==========================================
# 13. 統合・ランキング
# ==========================================

combined_period = pd.concat(all_period_rows).reset_index(drop=True)
combined_weekly = pd.concat(all_weekly_rows).reset_index(drop=True)
summary = pd.DataFrame(summary_rows)

# Base差分
base_row = summary[summary['Config'] == 'Base_NoFilter'].iloc[0]

for col in [
    'Full_NetProfitYen',
    'Full_MaxDDPct',
    'Full_MoneyRoMD',
    'OOS_NetProfitYen',
    'OOS_MaxDDPct',
    'OOS_MoneyRoMD',
    'Q1_NetProfitYen',
    'Q1_MaxDDPct',
    'Q1_MoneyRoMD'
]:
    if col in summary.columns:
        summary[f'Delta_{col}'] = summary[col] - base_row[col]

# ランキング
rank_full = summary.sort_values(
    ['Full_MoneyRoMD', 'OOS_MoneyRoMD', 'Q1_MoneyRoMD'],
    ascending=[False, False, False]
).reset_index(drop=True)

rank_oos = summary.sort_values(
    ['OOS_MoneyRoMD', 'Full_MoneyRoMD', 'Q1_MoneyRoMD'],
    ascending=[False, False, False]
).reset_index(drop=True)

rank_q1 = summary.sort_values(
    ['Q1_MoneyRoMD', 'OOS_MoneyRoMD', 'Full_MoneyRoMD'],
    ascending=[False, False, False]
).reset_index(drop=True)

# MaxDDPct低い順も見る
rank_dd = summary.sort_values(
    ['OOS_MaxDDPct', 'Q1_MaxDDPct', 'Full_MaxDDPct'],
    ascending=[True, True, True]
).reset_index(drop=True)

print('\n' + '=' * 100)
print('🏆 Money Filter Compare v1 - Ranking by Full MoneyRoMD')
print('=' * 100)
print(rank_full.head(20).to_string(index=False))

print('\n' + '=' * 100)
print('🏆 Money Filter Compare v1 - Ranking by OOS MoneyRoMD')
print('=' * 100)
print(rank_oos.head(20).to_string(index=False))

print('\n' + '=' * 100)
print('🏆 Money Filter Compare v1 - Ranking by Q1 MoneyRoMD')
print('=' * 100)
print(rank_q1.head(20).to_string(index=False))

print('\n' + '=' * 100)
print('🛡 Money Filter Compare v1 - Ranking by Low OOS MaxDDPct')
print('=' * 100)
print(rank_dd.head(20).to_string(index=False))

# ==========================================
# 14. Best候補保存
# ==========================================

best_oos_config = rank_oos.iloc[0]['Config']
best_full_config = rank_full.iloc[0]['Config']
best_q1_config = rank_q1.iloc[0]['Config']

print('\n' + '=' * 100)
print('✅ Best configs')
print('=' * 100)
print(f'Best by Full MoneyRoMD: {best_full_config}')
print(f'Best by OOS MoneyRoMD : {best_oos_config}')
print(f'Best by Q1 MoneyRoMD  : {best_q1_config}')

# ==========================================
# 15. CSV保存
# ==========================================

combined_period.to_csv(f'{OUT_DIR}/MoneyFilterCompare_v1_Combined_PeriodSummary.csv', index=False)
combined_weekly.to_csv(f'{OUT_DIR}/MoneyFilterCompare_v1_Combined_Weekly.csv', index=False)
summary.to_csv(f'{OUT_DIR}/MoneyFilterCompare_v1_All_Results.csv', index=False)

rank_full.to_csv(f'{OUT_DIR}/MoneyFilterCompare_v1_Ranking_Full_MoneyRoMD.csv', index=False)
rank_oos.to_csv(f'{OUT_DIR}/MoneyFilterCompare_v1_Ranking_OOS_MoneyRoMD.csv', index=False)
rank_q1.to_csv(f'{OUT_DIR}/MoneyFilterCompare_v1_Ranking_Q1_MoneyRoMD.csv', index=False)
rank_dd.to_csv(f'{OUT_DIR}/MoneyFilterCompare_v1_Ranking_Low_OOS_MaxDDPct.csv', index=False)

# Best Accepted / Rejected 保存
for best_name in [best_full_config, best_oos_config, best_q1_config]:
    safe_name = best_name.replace('/', '_').replace(' ', '_')

    if best_name in accepted_outputs:
        accepted_outputs[best_name].to_csv(f'{OUT_DIR}/{safe_name}_Accepted_Trades.csv', index=False)

    if best_name in rejected_outputs and not rejected_outputs[best_name].empty:
        rejected_outputs[best_name].to_csv(f'{OUT_DIR}/{safe_name}_Rejected_Trades.csv', index=False)

print('\n' + '=' * 100)
print('✅ CSV保存完了')
print('=' * 100)
print(f'Output dir: {OUT_DIR}')
print('Saved files:')
print('- MoneyFilterCompare_v1_Combined_PeriodSummary.csv')
print('- MoneyFilterCompare_v1_Combined_Weekly.csv')
print('- MoneyFilterCompare_v1_All_Results.csv')
print('- MoneyFilterCompare_v1_Ranking_Full_MoneyRoMD.csv')
print('- MoneyFilterCompare_v1_Ranking_OOS_MoneyRoMD.csv')
print('- MoneyFilterCompare_v1_Ranking_Q1_MoneyRoMD.csv')
print('- MoneyFilterCompare_v1_Ranking_Low_OOS_MaxDDPct.csv')
print('- Best config Accepted / Rejected Trades CSV')
