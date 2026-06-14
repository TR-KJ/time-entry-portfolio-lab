# ==========================================
# Time Entry Portfolio Lab
# filter_test_v2_range_atr.py
#
# 目的：
# - v1.2 Add Aussie Logic のトレード履歴CSVを読み込む
# - 各トレードのEntry時点で使える値幅・ATR特徴量を付与
# - 以下のフィルタを後処理で検証する
#
# 1. 前日値幅フィルタ
# 2. 直近24時間値幅フィルタ
# 3. 当日00:00〜Entry前値幅フィルタ
# 4. H1 ATR(14) 上位◯%停止
# 5. H1 ATRレジーム別成績
#
# 入力：
# /content/Portfolio_Integration_Results_v1_2_add_aussie_logic.csv
#
# 出力：
# /content/filter_test_v2_range_atr/
# ==========================================

from google.colab import drive
import pandas as pd
import numpy as np
import glob
import os

drive.mount('/content/drive')

# ==========================================
# 1. パス設定
# ==========================================

TRADE_CSV_PATH = '/content/Portfolio_Integration_Results_v1_2_add_aussie_logic.csv'

# Google Driveに置いている場合はこちらに変更
# TRADE_CSV_PATH = '/content/drive/MyDrive/time-entry-portfolio-lab/results/v1_2_add_aussie_logic/Portfolio_Integration_Results_v1_2_add_aussie_logic.csv'

OUT_DIR = '/content/filter_test_v2_range_atr'
os.makedirs(OUT_DIR, exist_ok=True)

if not os.path.exists(TRADE_CSV_PATH):
    raise FileNotFoundError(f'トレード履歴CSVが見つかりません: {TRADE_CSV_PATH}')

# ==========================================
# 2. 基本設定
# ==========================================

PAIR_FILE_KEY = {
    'EJ': 'eurjpy_m1',
    'GJ': 'gbpjpy_m1',
    'AJ': 'audjpy_m1',
    'UJ': 'usdjpy_m1',
    'EA': 'euraud_m1',
    'GA': 'gbpaud_m1',
    'AU': 'audusd_m1',
}

PAIR_PIP_SIZE = {
    'EJ': 0.01,
    'GJ': 0.01,
    'AJ': 0.01,
    'UJ': 0.01,
    'EA': 0.0001,
    'GA': 0.0001,
    'AU': 0.0001,
}

STRICT_IS_END = pd.Timestamp('2024-12-31 23:59:59')
STRICT_OOS_START = pd.Timestamp('2025-01-01')
STRICT_OOS_END = pd.Timestamp('2026-03-31 23:59:59')
Q1_START = pd.Timestamp('2026-01-01')
Q1_END = pd.Timestamp('2026-03-31 23:59:59')

PERCENTILES = [70, 75, 80, 85, 90, 95]

# ==========================================
# 3. トレード履歴読み込み
# ==========================================

trades = pd.read_csv(TRADE_CSV_PATH)

trades['EntryTime'] = pd.to_datetime(trades['EntryTime'])
trades['CloseTime'] = pd.to_datetime(trades['CloseTime'])

trades = trades.sort_values(['EntryTime', 'CloseTime']).reset_index(drop=True)

required_cols = [
    'Strategy',
    'Pair',
    'Direction',
    'EntryTime',
    'CloseTime',
    'Pips'
]

missing_cols = [c for c in required_cols if c not in trades.columns]

if missing_cols:
    raise ValueError(f'必要な列がありません: {missing_cols}')

print('✅ Trade CSV loaded')
print(f'Rows: {len(trades):,}')
print(f"Period: {trades['CloseTime'].min()} 〜 {trades['CloseTime'].max()}")

# ==========================================
# 4. M1データ読み込み
# ==========================================

def load_m1_data(pair_key):
    files = glob.glob(f'/content/drive/MyDrive/MT5 data/*{pair_key}*.csv')

    if not files:
        print(f'⚠️ M1データが見つかりません: {pair_key}')
        return None

    df_list = []

    for f in files:
        tmp = pd.read_csv(
            f,
            names=['Date', 'Time', 'Open', 'High', 'Low', 'Close', 'TickVol', 'Vol', 'Spread'],
            header=0,
            sep='\t'
        )
        df_list.append(tmp)

    df = pd.concat(df_list)

    df['Datetime'] = pd.to_datetime(df['Date'] + ' ' + df['Time'])

    df['Datetime'] = (
        df['Datetime']
        .dt.tz_localize('Europe/Helsinki')
        .dt.tz_convert('Asia/Tokyo')
        .dt.tz_localize(None)
    )

    df = df.drop_duplicates(subset=['Datetime'])
    df = df.sort_values('Datetime')
    df = df.reset_index(drop=True)

    df = df[['Datetime', 'Open', 'High', 'Low', 'Close']].copy()

    print(f"✅ Loaded {pair_key}: {len(df):,} bars / {df['Datetime'].min()} 〜 {df['Datetime'].max()}")

    return df


price_data = {}

for pair, key in PAIR_FILE_KEY.items():
    price_data[pair] = load_m1_data(key)

# ==========================================
# 5. 特徴量作成
# ==========================================

def build_pair_features(pair, df_m1):
    if df_m1 is None or df_m1.empty:
        return None

    pip_size = PAIR_PIP_SIZE[pair]

    df = df_m1.copy()
    df = df.sort_values('Datetime').reset_index(drop=True)
    df['Date'] = df['Datetime'].dt.date

    # 日足値幅
    daily = (
        df
        .groupby('Date')
        .agg(
            DayHigh=('High', 'max'),
            DayLow=('Low', 'min')
        )
        .reset_index()
    )

    daily['PrevDayHigh'] = daily['DayHigh'].shift(1)
    daily['PrevDayLow'] = daily['DayLow'].shift(1)
    daily['PrevDayRangePips'] = (daily['PrevDayHigh'] - daily['PrevDayLow']) / pip_size

    prev_day_map = daily.set_index('Date')['PrevDayRangePips'].to_dict()

    # H1 ATR(14)
    h1 = (
        df
        .set_index('Datetime')
        .resample('1H')
        .agg(
            Open=('Open', 'first'),
            High=('High', 'max'),
            Low=('Low', 'min'),
            Close=('Close', 'last')
        )
        .dropna()
        .reset_index()
    )

    h1['PrevClose'] = h1['Close'].shift(1)

    h1['TR1'] = h1['High'] - h1['Low']
    h1['TR2'] = (h1['High'] - h1['PrevClose']).abs()
    h1['TR3'] = (h1['Low'] - h1['PrevClose']).abs()

    h1['TR'] = h1[['TR1', 'TR2', 'TR3']].max(axis=1)
    h1['ATR14'] = h1['TR'].rolling(14).mean()
    h1['ATR14Pips'] = h1['ATR14'] / pip_size

    # Entry時点では未確定のH1足を見ないように、1本前のH1 ATRを使う
    h1['ATR14Pips_Completed'] = h1['ATR14Pips'].shift(1)

    h1_times = h1['Datetime'].values
    h1_atr_values = h1['ATR14Pips_Completed'].values

    # M1配列
    times = df['Datetime'].values
    highs = df['High'].values
    lows = df['Low'].values

    return {
        'pair': pair,
        'pip_size': pip_size,
        'm1': df,
        'times': times,
        'highs': highs,
        'lows': lows,
        'prev_day_map': prev_day_map,
        'h1_times': h1_times,
        'h1_atr_values': h1_atr_values,
    }


pair_features = {}

for pair, df_m1 in price_data.items():
    pair_features[pair] = build_pair_features(pair, df_m1)

# ==========================================
# 6. 各トレードに特徴量付与
# ==========================================

def range_pips_between(feature, start_time, end_time):
    times = feature['times']
    highs = feature['highs']
    lows = feature['lows']
    pip_size = feature['pip_size']

    start_np = np.datetime64(start_time)
    end_np = np.datetime64(end_time)

    left = np.searchsorted(times, start_np, side='left')
    right = np.searchsorted(times, end_np, side='right')

    if left >= right:
        return np.nan

    max_high = np.nanmax(highs[left:right])
    min_low = np.nanmin(lows[left:right])

    return (max_high - min_low) / pip_size


def get_completed_h1_atr(feature, entry_time):
    h1_times = feature['h1_times']
    atr_values = feature['h1_atr_values']

    entry_np = np.datetime64(entry_time)

    idx = np.searchsorted(h1_times, entry_np, side='right') - 1

    if idx < 0:
        return np.nan

    atr = atr_values[idx]

    if pd.isna(atr):
        return np.nan

    return float(atr)


feature_rows = []

for _, row in trades.iterrows():
    pair = row['Pair']
    entry_time = row['EntryTime']
    entry_date = entry_time.date()

    feature = pair_features.get(pair)

    if feature is None:
        prev_day_range = np.nan
        range_24h = np.nan
        range_day_to_entry = np.nan
        h1_atr14 = np.nan
    else:
        prev_day_range = feature['prev_day_map'].get(entry_date, np.nan)

        start_24h = entry_time - pd.Timedelta(hours=24)
        range_24h = range_pips_between(feature, start_24h, entry_time - pd.Timedelta(minutes=1))

        start_day = pd.Timestamp(entry_date)
        range_day_to_entry = range_pips_between(feature, start_day, entry_time - pd.Timedelta(minutes=1))

        h1_atr14 = get_completed_h1_atr(feature, entry_time)

    feature_rows.append({
        'PrevDayRangePips': round(prev_day_range, 3) if not pd.isna(prev_day_range) else np.nan,
        'Range24hPips': round(range_24h, 3) if not pd.isna(range_24h) else np.nan,
        'DayToEntryRangePips': round(range_day_to_entry, 3) if not pd.isna(range_day_to_entry) else np.nan,
        'H1_ATR14_Pips': round(h1_atr14, 3) if not pd.isna(h1_atr14) else np.nan,
    })

features_df = pd.DataFrame(feature_rows)

df = pd.concat([trades.reset_index(drop=True), features_df], axis=1)

df['EntryDate'] = df['EntryTime'].dt.date

print('\n✅ Features attached')
print(df[['Pair', 'Strategy', 'EntryTime', 'PrevDayRangePips', 'Range24hPips', 'DayToEntryRangePips', 'H1_ATR14_Pips']].head().to_string(index=False))

# ==========================================
# 7. 集計関数
# ==========================================

def calc_metrics(input_df, label='Total'):
    d = input_df.copy()

    if d.empty:
        return {
            'Label': label,
            'Trades': 0,
            'WinRate': np.nan,
            'PF': np.nan,
            'TotalPips': 0.0,
            'MaxDD': 0.0,
            'RoMD': np.nan,
            'AvgPips': np.nan
        }

    d = d.sort_values('CloseTime').copy()
    d['CumPips'] = d['Pips'].cumsum()
    d['MaxCumPips'] = d['CumPips'].cummax()
    d['Drawdown'] = d['MaxCumPips'] - d['CumPips']

    wins = d[d['Pips'] > 0]['Pips'].sum()
    losses = d[d['Pips'] < 0]['Pips'].sum()

    if losses < 0:
        pf = wins / abs(losses)
    else:
        pf = np.nan

    total_pips = d['Pips'].sum()
    max_dd = d['Drawdown'].max()

    if max_dd > 0:
        romd = total_pips / max_dd
    else:
        romd = np.nan

    win_rate = len(d[d['Pips'] > 0]) / len(d) * 100
    avg_pips = d['Pips'].mean()

    return {
        'Label': label,
        'Trades': len(d),
        'WinRate': round(win_rate, 2),
        'PF': round(pf, 3) if not pd.isna(pf) else np.nan,
        'TotalPips': round(total_pips, 1),
        'MaxDD': round(max_dd, 1),
        'RoMD': round(romd, 2) if not pd.isna(romd) else np.nan,
        'AvgPips': round(avg_pips, 2)
    }


def period_metrics(input_df, label_prefix):
    full = calc_metrics(input_df, f'{label_prefix}_Full')

    oos_df = input_df[
        (input_df['CloseTime'] >= STRICT_OOS_START) &
        (input_df['CloseTime'] <= STRICT_OOS_END)
    ].copy()

    q1_df = input_df[
        (input_df['CloseTime'] >= Q1_START) &
        (input_df['CloseTime'] <= Q1_END)
    ].copy()

    oos = calc_metrics(oos_df, f'{label_prefix}_StrictOOS')
    q1 = calc_metrics(q1_df, f'{label_prefix}_Q1')

    return full, oos, q1

# ==========================================
# 8. 閾値作成
# ==========================================
# 過剰最適化を避けるため、閾値はStrict IS 2015〜2024のトレードから作る

df_is = df[df['CloseTime'] <= STRICT_IS_END].copy()

FEATURES = [
    'PrevDayRangePips',
    'Range24hPips',
    'DayToEntryRangePips',
    'H1_ATR14_Pips'
]

threshold_rows = []

for pair, pair_df in df_is.groupby('Pair'):
    for feature in FEATURES:
        values = pair_df[feature].dropna()

        if values.empty:
            continue

        for pct in PERCENTILES:
            threshold = np.percentile(values, pct)

            threshold_rows.append({
                'Pair': pair,
                'Feature': feature,
                'Percentile': pct,
                'Threshold': round(float(threshold), 3)
            })

thresholds_df = pd.DataFrame(threshold_rows)

print('\n✅ Thresholds created from Strict IS')
print(thresholds_df.head(20).to_string(index=False))

# ==========================================
# 9. フィルタ適用関数
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
        value = row[feature]
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
# 10. フィルタテスト実行
# ==========================================

base_full, base_oos, base_q1 = period_metrics(df, 'Base')

result_rows = []
accepted_map = {}
rejected_map = {}

# Base
result_rows.append({
    'Config': 'Base_NoFilter',
    'Feature': None,
    'Percentile': None,
    'Full_Trades': base_full['Trades'],
    'Full_PF': base_full['PF'],
    'Full_TotalPips': base_full['TotalPips'],
    'Full_MaxDD': base_full['MaxDD'],
    'Full_RoMD': base_full['RoMD'],
    'OOS_Trades': base_oos['Trades'],
    'OOS_PF': base_oos['PF'],
    'OOS_TotalPips': base_oos['TotalPips'],
    'OOS_MaxDD': base_oos['MaxDD'],
    'OOS_RoMD': base_oos['RoMD'],
    'Q1_Trades': base_q1['Trades'],
    'Q1_PF': base_q1['PF'],
    'Q1_TotalPips': base_q1['TotalPips'],
    'Q1_MaxDD': base_q1['MaxDD'],
    'Q1_RoMD': base_q1['RoMD'],
    'RejectedTrades': 0,
    'RejectedRatePct': 0.0,
    'Delta_Full_TotalPips': 0.0,
    'Delta_Full_MaxDD': 0.0,
    'Delta_Full_RoMD': 0.0,
    'Delta_OOS_TotalPips': 0.0,
    'Delta_OOS_MaxDD': 0.0,
    'Delta_OOS_RoMD': 0.0,
    'Delta_Q1_TotalPips': 0.0,
    'Delta_Q1_MaxDD': 0.0,
    'Delta_Q1_RoMD': 0.0
})

accepted_map['Base_NoFilter'] = df.copy()
rejected_map['Base_NoFilter'] = pd.DataFrame()

for feature in FEATURES:
    for pct in PERCENTILES:
        config_name = f'{feature}_LTE_P{pct}'

        accepted, rejected = apply_upper_percentile_filter(
            df,
            thresholds_df,
            feature,
            pct
        )

        full_m, oos_m, q1_m = period_metrics(accepted, config_name)

        row = {
            'Config': config_name,
            'Feature': feature,
            'Percentile': pct,

            'Full_Trades': full_m['Trades'],
            'Full_PF': full_m['PF'],
            'Full_TotalPips': full_m['TotalPips'],
            'Full_MaxDD': full_m['MaxDD'],
            'Full_RoMD': full_m['RoMD'],

            'OOS_Trades': oos_m['Trades'],
            'OOS_PF': oos_m['PF'],
            'OOS_TotalPips': oos_m['TotalPips'],
            'OOS_MaxDD': oos_m['MaxDD'],
            'OOS_RoMD': oos_m['RoMD'],

            'Q1_Trades': q1_m['Trades'],
            'Q1_PF': q1_m['PF'],
            'Q1_TotalPips': q1_m['TotalPips'],
            'Q1_MaxDD': q1_m['MaxDD'],
            'Q1_RoMD': q1_m['RoMD'],

            'RejectedTrades': len(rejected),
            'RejectedRatePct': round(len(rejected) / len(df) * 100, 2)
        }

        row['Delta_Full_TotalPips'] = round(row['Full_TotalPips'] - base_full['TotalPips'], 1)
        row['Delta_Full_MaxDD'] = round(row['Full_MaxDD'] - base_full['MaxDD'], 1)
        row['Delta_Full_RoMD'] = round(row['Full_RoMD'] - base_full['RoMD'], 2)

        row['Delta_OOS_TotalPips'] = round(row['OOS_TotalPips'] - base_oos['TotalPips'], 1)
        row['Delta_OOS_MaxDD'] = round(row['OOS_MaxDD'] - base_oos['MaxDD'], 1)
        row['Delta_OOS_RoMD'] = round(row['OOS_RoMD'] - base_oos['RoMD'], 2)

        row['Delta_Q1_TotalPips'] = round(row['Q1_TotalPips'] - base_q1['TotalPips'], 1)
        row['Delta_Q1_MaxDD'] = round(row['Q1_MaxDD'] - base_q1['MaxDD'], 1)
        row['Delta_Q1_RoMD'] = round(row['Q1_RoMD'] - base_q1['RoMD'], 2)

        result_rows.append(row)
        accepted_map[config_name] = accepted
        rejected_map[config_name] = rejected

results = pd.DataFrame(result_rows)

# ==========================================
# 11. ATRレジーム別成績
# ==========================================

atr_thresholds = thresholds_df[
    thresholds_df['Feature'] == 'H1_ATR14_Pips'
].copy()

atr_q25 = {}

for pair, pair_df in df_is.groupby('Pair'):
    vals = pair_df['H1_ATR14_Pips'].dropna()

    if vals.empty:
        continue

    atr_q25[pair] = {
        'P25': np.percentile(vals, 25),
        'P50': np.percentile(vals, 50),
        'P75': np.percentile(vals, 75),
    }


def classify_atr_regime(row):
    pair = row['Pair']
    val = row['H1_ATR14_Pips']

    if pair not in atr_q25:
        return 'Unknown'

    if pd.isna(val):
        return 'Unknown'

    q = atr_q25[pair]

    if val <= q['P25']:
        return 'Low'
    elif val <= q['P50']:
        return 'NormalLow'
    elif val <= q['P75']:
        return 'NormalHigh'
    else:
        return 'High'


df_regime = df.copy()
df_regime['ATRRegime'] = df_regime.apply(classify_atr_regime, axis=1)

regime_rows = []

for keys, sub in df_regime.groupby(['Pair', 'ATRRegime']):
    pair = keys[0]
    regime = keys[1]
    regime_rows.append(calc_metrics(sub, f'{pair}_{regime}'))

atr_regime_pair_summary = pd.DataFrame(regime_rows)
atr_regime_pair_summary = atr_regime_pair_summary.sort_values(['Label']).reset_index(drop=True)

strategy_regime_rows = []

for keys, sub in df_regime.groupby(['Strategy', 'ATRRegime']):
    strategy = keys[0]
    regime = keys[1]
    strategy_regime_rows.append(calc_metrics(sub, f'{strategy}_{regime}'))

atr_regime_strategy_summary = pd.DataFrame(strategy_regime_rows)
atr_regime_strategy_summary = atr_regime_strategy_summary.sort_values(['Label']).reset_index(drop=True)

# ==========================================
# 12. ランキング
# ==========================================

rank_full = results.sort_values(
    ['Full_RoMD', 'OOS_RoMD', 'Q1_RoMD'],
    ascending=[False, False, False]
).reset_index(drop=True)

rank_oos = results.sort_values(
    ['OOS_RoMD', 'Full_RoMD', 'Q1_RoMD'],
    ascending=[False, False, False]
).reset_index(drop=True)

rank_q1 = results.sort_values(
    ['Q1_RoMD', 'OOS_RoMD', 'Full_RoMD'],
    ascending=[False, False, False]
).reset_index(drop=True)

print('\n' + '=' * 100)
print('🏆 Filter v2 Ranking by Full RoMD')
print('=' * 100)
print(rank_full.head(20).to_string(index=False))

print('\n' + '=' * 100)
print('🏆 Filter v2 Ranking by OOS RoMD')
print('=' * 100)
print(rank_oos.head(20).to_string(index=False))

print('\n' + '=' * 100)
print('🏆 Filter v2 Ranking by Q1 RoMD')
print('=' * 100)
print(rank_q1.head(20).to_string(index=False))

# ==========================================
# 13. Best候補保存
# ==========================================

best_config = rank_oos.iloc[0]['Config']

best_accepted = accepted_map[best_config].copy()
best_rejected = rejected_map[best_config].copy()

print('\n' + '=' * 100)
print('✅ Best Config by OOS RoMD')
print('=' * 100)
print(best_config)

# ==========================================
# 14. CSV保存
# ==========================================

df.to_csv(f'{OUT_DIR}/Filter_v2_Feature_Attached_Trades.csv', index=False)
thresholds_df.to_csv(f'{OUT_DIR}/Filter_v2_Thresholds_StrictIS.csv', index=False)
results.to_csv(f'{OUT_DIR}/Filter_v2_All_Results.csv', index=False)
rank_full.to_csv(f'{OUT_DIR}/Filter_v2_Ranking_Full_RoMD.csv', index=False)
rank_oos.to_csv(f'{OUT_DIR}/Filter_v2_Ranking_OOS_RoMD.csv', index=False)
rank_q1.to_csv(f'{OUT_DIR}/Filter_v2_Ranking_Q1_RoMD.csv', index=False)
atr_regime_pair_summary.to_csv(f'{OUT_DIR}/Filter_v2_ATR_Regime_Pair_Summary.csv', index=False)
atr_regime_strategy_summary.to_csv(f'{OUT_DIR}/Filter_v2_ATR_Regime_Strategy_Summary.csv', index=False)
best_accepted.to_csv(f'{OUT_DIR}/Filter_v2_Best_Accepted_Trades.csv', index=False)

if not best_rejected.empty:
    best_rejected.to_csv(f'{OUT_DIR}/Filter_v2_Best_Rejected_Trades.csv', index=False)

print('\n' + '=' * 100)
print('✅ CSV保存完了')
print('=' * 100)
print(f'Output dir: {OUT_DIR}')
print('Saved files:')
print('- Filter_v2_Feature_Attached_Trades.csv')
print('- Filter_v2_Thresholds_StrictIS.csv')
print('- Filter_v2_All_Results.csv')
print('- Filter_v2_Ranking_Full_RoMD.csv')
print('- Filter_v2_Ranking_OOS_RoMD.csv')
print('- Filter_v2_Ranking_Q1_RoMD.csv')
print('- Filter_v2_ATR_Regime_Pair_Summary.csv')
print('- Filter_v2_ATR_Regime_Strategy_Summary.csv')
print('- Filter_v2_Best_Accepted_Trades.csv')
print('- Filter_v2_Best_Rejected_Trades.csv')
