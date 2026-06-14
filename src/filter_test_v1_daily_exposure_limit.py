# ==========================================
# Time Entry Portfolio Lab
# filter_test_v1_daily_exposure_limit.py
#
# 目的：
# - v1.2 Add Aussie Logic のトレード履歴CSVを読み込む
# - 同日トレード数制限
# - JPY方向エクスポージャー制限
# - AUD方向エクスポージャー制限
# を後処理で検証する
#
# 入力：
# /content/Portfolio_Integration_Results_v1_2_add_aussie_logic.csv
#
# 出力：
# /content/filter_test_v1_daily_exposure_limit/
# ==========================================

from google.colab import drive
import pandas as pd
import numpy as np
import os

drive.mount('/content/drive')

# ==========================================
# 1. 入力CSV
# ==========================================

CSV_PATH = '/content/Portfolio_Integration_Results_v1_2_add_aussie_logic.csv'

# Google Driveに置いている場合はこちらに変更
# CSV_PATH = '/content/drive/MyDrive/time-entry-portfolio-lab/results/v1_2_add_aussie_logic/Portfolio_Integration_Results_v1_2_add_aussie_logic.csv'

if not os.path.exists(CSV_PATH):
    raise FileNotFoundError(f'CSVが見つかりません: {CSV_PATH}')

df = pd.read_csv(CSV_PATH)

df['EntryTime'] = pd.to_datetime(df['EntryTime'])
df['CloseTime'] = pd.to_datetime(df['CloseTime'])

df = df.sort_values(['EntryTime', 'CloseTime']).reset_index(drop=True)

required_cols = [
    'Strategy',
    'Pair',
    'Direction',
    'EntryTime',
    'CloseTime',
    'Pips'
]

missing_cols = [c for c in required_cols if c not in df.columns]

if missing_cols:
    raise ValueError(f'必要な列がありません: {missing_cols}')

print('✅ CSV loaded')
print(f'Rows: {len(df):,}')
print(f"Period: {df['CloseTime'].min()} 〜 {df['CloseTime'].max()}")

# ==========================================
# 2. 分析期間
# ==========================================

# まずは全期間で検証する
FULL_START = pd.Timestamp('2015-01-01')
FULL_END = pd.Timestamp('2026-03-31 23:59:59')

# Strict OOSも確認
STRICT_OOS_START = pd.Timestamp('2025-01-01')
STRICT_OOS_END = pd.Timestamp('2026-03-31 23:59:59')

# Q1 2026も確認
Q1_START = pd.Timestamp('2026-01-01')
Q1_END = pd.Timestamp('2026-03-31 23:59:59')

df = df[
    (df['CloseTime'] >= FULL_START) &
    (df['CloseTime'] <= FULL_END)
].copy()

# ==========================================
# 3. 方向エクスポージャー定義
# ==========================================

def get_jpy_exposure(pair, direction):
    """
    JPY方向を返す。
    JPY売り = クロス円Long / USDJPY Long
    JPY買い = クロス円Short / USDJPY Short
    JPYを含まないペアは None
    """
    if pair not in ['EJ', 'GJ', 'AJ', 'UJ']:
        return None

    if direction == 'Long':
        return 'JPY_Sell'

    if direction == 'Short':
        return 'JPY_Buy'

    return None


def get_aud_exposure(pair, direction):
    """
    AUD方向を返す。
    AUD買い：
      AUDJPY Long
      AUDUSD Long
      EURAUD Short
      GBPAUD Short

    AUD売り：
      AUDJPY Short
      AUDUSD Short
      EURAUD Long
      GBPAUD Long
    """
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


def get_gbp_exposure(pair, direction):
    """
    参考用：GBP方向
    GBP買い：
      GBPJPY Long
      GBPAUD Long

    GBP売り：
      GBPJPY Short
      GBPAUD Short
    """
    if pair == 'GJ':
        if direction == 'Long':
            return 'GBP_Buy'
        if direction == 'Short':
            return 'GBP_Sell'

    if pair == 'GA':
        if direction == 'Long':
            return 'GBP_Buy'
        if direction == 'Short':
            return 'GBP_Sell'

    return None


def get_eur_exposure(pair, direction):
    """
    参考用：EUR方向
    EUR買い：
      EURJPY Long
      EURAUD Long

    EUR売り：
      EURJPY Short
      EURAUD Short
    """
    if pair == 'EJ':
        if direction == 'Long':
            return 'EUR_Buy'
        if direction == 'Short':
            return 'EUR_Sell'

    if pair == 'EA':
        if direction == 'Long':
            return 'EUR_Buy'
        if direction == 'Short':
            return 'EUR_Sell'

    return None


df['EntryDate'] = df['EntryTime'].dt.date
df['JPYExposure'] = df.apply(lambda r: get_jpy_exposure(r['Pair'], r['Direction']), axis=1)
df['AUDExposure'] = df.apply(lambda r: get_aud_exposure(r['Pair'], r['Direction']), axis=1)
df['GBPExposure'] = df.apply(lambda r: get_gbp_exposure(r['Pair'], r['Direction']), axis=1)
df['EURExposure'] = df.apply(lambda r: get_eur_exposure(r['Pair'], r['Direction']), axis=1)

# ==========================================
# 4. 集計関数
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
    rows = []

    rows.append(calc_metrics(input_df, f'{label_prefix}_Full'))

    strict_oos = input_df[
        (input_df['CloseTime'] >= STRICT_OOS_START) &
        (input_df['CloseTime'] <= STRICT_OOS_END)
    ].copy()

    q1 = input_df[
        (input_df['CloseTime'] >= Q1_START) &
        (input_df['CloseTime'] <= Q1_END)
    ].copy()

    rows.append(calc_metrics(strict_oos, f'{label_prefix}_StrictOOS_2025_to_2026Q1'))
    rows.append(calc_metrics(q1, f'{label_prefix}_Q1_2026'))

    return rows


# ==========================================
# 5. フィルタ適用関数
# ==========================================

def apply_daily_exposure_filter(
    input_df,
    max_trades_per_day=None,
    max_jpy_same_direction=None,
    max_aud_same_direction=None,
    max_gbp_same_direction=None,
    max_eur_same_direction=None,
    priority_mode='entry_time'
):
    """
    EntryDateごとにトレードを採用/除外する。

    priority_mode:
      entry_time = EntryTimeが早い順に採用
      long_term_rank = 簡易優先順位で採用
    """

    d = input_df.copy()

    if priority_mode == 'long_term_rank':
        d['Priority'] = d['Strategy'].map(STRATEGY_PRIORITY).fillna(999)
        d = d.sort_values(['EntryDate', 'Priority', 'EntryTime', 'CloseTime']).copy()
    else:
        d = d.sort_values(['EntryDate', 'EntryTime', 'CloseTime']).copy()

    accepted_rows = []
    rejected_rows = []

    for entry_date, day_df in d.groupby('EntryDate'):
        accepted_count = 0

        jpy_counts = {}
        aud_counts = {}
        gbp_counts = {}
        eur_counts = {}

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

            if reject_reason is None and max_gbp_same_direction is not None:
                exp = row['GBPExposure']

                if exp is not None:
                    current_count = gbp_counts.get(exp, 0)

                    if current_count >= max_gbp_same_direction:
                        reject_reason = f'MaxGBP_{exp}'

            if reject_reason is None and max_eur_same_direction is not None:
                exp = row['EURExposure']

                if exp is not None:
                    current_count = eur_counts.get(exp, 0)

                    if current_count >= max_eur_same_direction:
                        reject_reason = f'MaxEUR_{exp}'

            row_dict = row.to_dict()

            if reject_reason is None:
                accepted_rows.append(row_dict)
                accepted_count += 1

                if row['JPYExposure'] is not None:
                    jpy_counts[row['JPYExposure']] = jpy_counts.get(row['JPYExposure'], 0) + 1

                if row['AUDExposure'] is not None:
                    aud_counts[row['AUDExposure']] = aud_counts.get(row['AUDExposure'], 0) + 1

                if row['GBPExposure'] is not None:
                    gbp_counts[row['GBPExposure']] = gbp_counts.get(row['GBPExposure'], 0) + 1

                if row['EURExposure'] is not None:
                    eur_counts[row['EURExposure']] = eur_counts.get(row['EURExposure'], 0) + 1

            else:
                row_dict['RejectReason'] = reject_reason
                rejected_rows.append(row_dict)

    accepted_df = pd.DataFrame(accepted_rows)
    rejected_df = pd.DataFrame(rejected_rows)

    if not accepted_df.empty:
        accepted_df = accepted_df.sort_values('CloseTime').reset_index(drop=True)

    if not rejected_df.empty:
        rejected_df = rejected_df.sort_values('EntryTime').reset_index(drop=True)

    return accepted_df, rejected_df


# ==========================================
# 6. 戦略優先順位
# ==========================================
# まずは「entry_time優先」を基本にする。
# long_term_rankを使う場合の簡易順位。
# 長期成績が強かったものを上に置く。
# 必要に応じて後で調整する。

STRATEGY_PRIORITY = {
    '1_EJ_Log1': 10,
    '5_GJ_Port_Log2': 11,
    '19_EA_3_WedThu_Long': 12,
    '3_EJ_NightBlitz_21': 13,
    '2_EJ_NightBlitz_20': 14,
    '4_GJ_Port_Log1': 15,
    '12_UJ_Short_Core': 16,
    '17_EA_1B_Wed_Short': 17,
    '27_EA_China_Demand': 18,
    '28_GA_China_Demand': 19,
    '26_AJ_China_Demand': 20,
    '9_AJ_Core2': 21,
    '18_EA_2_MonWed_Short': 22,
    '7_GJ_Mon_Blitz': 23,
    '22_GA_C_2': 24,
    '13_UJ_Fix_MidWeek': 25,
    '23_GA_F_2': 26,
    '21_GA_B_3': 27,
    '20_EA_1A_MonTue_Short': 28,
    '11_AJ_SatB': 29,
    '24_GA_D_1': 30,
    '14_UJ_Sat_3rd': 31,
    '6_GJ_Old_Mon': 32,
    '15_UJ_Sat_Aug': 33,
    '25_AU_China_Demand': 34,
    '10_AJ_SatA': 35,
    '8_AJ_Core1': 36
}

# ==========================================
# 7. テスト条件
# ==========================================

test_configs = []

# Base
test_configs.append({
    'name': 'Base_NoFilter',
    'max_trades_per_day': None,
    'max_jpy_same_direction': None,
    'max_aud_same_direction': None,
    'max_gbp_same_direction': None,
    'max_eur_same_direction': None,
    'priority_mode': 'entry_time'
})

# 同日トレード数のみ
for max_trades in [3, 4, 5, 6, 7, 8]:
    test_configs.append({
        'name': f'MaxTrades_{max_trades}',
        'max_trades_per_day': max_trades,
        'max_jpy_same_direction': None,
        'max_aud_same_direction': None,
        'max_gbp_same_direction': None,
        'max_eur_same_direction': None,
        'priority_mode': 'entry_time'
    })

# JPY方向のみ
for max_jpy in [1, 2, 3]:
    test_configs.append({
        'name': f'MaxJPYSameDir_{max_jpy}',
        'max_trades_per_day': None,
        'max_jpy_same_direction': max_jpy,
        'max_aud_same_direction': None,
        'max_gbp_same_direction': None,
        'max_eur_same_direction': None,
        'priority_mode': 'entry_time'
    })

# AUD方向のみ
for max_aud in [1, 2, 3]:
    test_configs.append({
        'name': f'MaxAUDSameDir_{max_aud}',
        'max_trades_per_day': None,
        'max_jpy_same_direction': None,
        'max_aud_same_direction': max_aud,
        'max_gbp_same_direction': None,
        'max_eur_same_direction': None,
        'priority_mode': 'entry_time'
    })

# JPY + AUD
for max_jpy in [1, 2, 3]:
    for max_aud in [1, 2, 3]:
        test_configs.append({
            'name': f'MaxJPY_{max_jpy}_MaxAUD_{max_aud}',
            'max_trades_per_day': None,
            'max_jpy_same_direction': max_jpy,
            'max_aud_same_direction': max_aud,
            'max_gbp_same_direction': None,
            'max_eur_same_direction': None,
            'priority_mode': 'entry_time'
        })

# 日トレード数 + JPY + AUD
for max_trades in [4, 5, 6, 7]:
    for max_jpy in [2, 3]:
        for max_aud in [2, 3]:
            test_configs.append({
                'name': f'MaxTrades_{max_trades}_JPY_{max_jpy}_AUD_{max_aud}',
                'max_trades_per_day': max_trades,
                'max_jpy_same_direction': max_jpy,
                'max_aud_same_direction': max_aud,
                'max_gbp_same_direction': None,
                'max_eur_same_direction': None,
                'priority_mode': 'entry_time'
            })

# long_term_rank優先版も少しだけ確認
for max_trades in [4, 5, 6]:
    test_configs.append({
        'name': f'Rank_MaxTrades_{max_trades}_JPY_2_AUD_2',
        'max_trades_per_day': max_trades,
        'max_jpy_same_direction': 2,
        'max_aud_same_direction': 2,
        'max_gbp_same_direction': None,
        'max_eur_same_direction': None,
        'priority_mode': 'long_term_rank'
    })

# ==========================================
# 8. テスト実行
# ==========================================

result_rows = []
accepted_map = {}
rejected_map = {}

base_full = calc_metrics(df, 'Base_Full')
base_oos = calc_metrics(
    df[
        (df['CloseTime'] >= STRICT_OOS_START) &
        (df['CloseTime'] <= STRICT_OOS_END)
    ],
    'Base_StrictOOS'
)
base_q1 = calc_metrics(
    df[
        (df['CloseTime'] >= Q1_START) &
        (df['CloseTime'] <= Q1_END)
    ],
    'Base_Q1'
)

for cfg in test_configs:
    name = cfg['name']

    if name == 'Base_NoFilter':
        accepted_df = df.copy()
        rejected_df = pd.DataFrame()
    else:
        accepted_df, rejected_df = apply_daily_exposure_filter(
            df,
            max_trades_per_day=cfg['max_trades_per_day'],
            max_jpy_same_direction=cfg['max_jpy_same_direction'],
            max_aud_same_direction=cfg['max_aud_same_direction'],
            max_gbp_same_direction=cfg['max_gbp_same_direction'],
            max_eur_same_direction=cfg['max_eur_same_direction'],
            priority_mode=cfg['priority_mode']
        )

    accepted_map[name] = accepted_df
    rejected_map[name] = rejected_df

    full_m = calc_metrics(accepted_df, f'{name}_Full')

    oos_df = accepted_df[
        (accepted_df['CloseTime'] >= STRICT_OOS_START) &
        (accepted_df['CloseTime'] <= STRICT_OOS_END)
    ].copy()

    q1_df = accepted_df[
        (accepted_df['CloseTime'] >= Q1_START) &
        (accepted_df['CloseTime'] <= Q1_END)
    ].copy()

    oos_m = calc_metrics(oos_df, f'{name}_StrictOOS')
    q1_m = calc_metrics(q1_df, f'{name}_Q1')

    row = {
        'Config': name,
        'PriorityMode': cfg['priority_mode'],
        'MaxTradesPerDay': cfg['max_trades_per_day'],
        'MaxJPYSameDirection': cfg['max_jpy_same_direction'],
        'MaxAUDSameDirection': cfg['max_aud_same_direction'],
        'MaxGBPSameDirection': cfg['max_gbp_same_direction'],
        'MaxEURSameDirection': cfg['max_eur_same_direction'],

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

        'RejectedTrades': len(rejected_df),
        'RejectedRatePct': round(len(rejected_df) / len(df) * 100, 2)
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

df_results = pd.DataFrame(result_rows)

# ==========================================
# 9. ランキング
# ==========================================

# まずはFullで大きく崩れていないものを重視
df_rank_full = df_results.sort_values(
    ['Full_RoMD', 'OOS_RoMD', 'Q1_RoMD'],
    ascending=[False, False, False]
).reset_index(drop=True)

df_rank_oos = df_results.sort_values(
    ['OOS_RoMD', 'Full_RoMD', 'Q1_RoMD'],
    ascending=[False, False, False]
).reset_index(drop=True)

df_rank_q1 = df_results.sort_values(
    ['Q1_RoMD', 'OOS_RoMD', 'Full_RoMD'],
    ascending=[False, False, False]
).reset_index(drop=True)

print('\n' + '=' * 100)
print('🏆 Filter Test v1 - Ranking by Full RoMD')
print('=' * 100)
print(df_rank_full.head(20).to_string(index=False))

print('\n' + '=' * 100)
print('🏆 Filter Test v1 - Ranking by OOS RoMD')
print('=' * 100)
print(df_rank_oos.head(20).to_string(index=False))

print('\n' + '=' * 100)
print('🏆 Filter Test v1 - Ranking by Q1 RoMD')
print('=' * 100)
print(df_rank_q1.head(20).to_string(index=False))

# ==========================================
# 10. Best候補を保存
# ==========================================

# 採用候補は、FullもOOSも見て選ぶ。
# ここでは暫定で OOS_RoMD 最高のものをBestとする。
best_config = df_rank_oos.iloc[0]['Config']

best_accepted = accepted_map[best_config].copy()
best_rejected = rejected_map[best_config].copy()

print('\n' + '=' * 100)
print('✅ Best Config by OOS RoMD')
print('=' * 100)
print(best_config)

# ==========================================
# 11. CSV保存
# ==========================================

out_dir = '/content/filter_test_v1_daily_exposure_limit'
os.makedirs(out_dir, exist_ok=True)

df_results.to_csv(f'{out_dir}/Filter_Test_v1_All_Results.csv', index=False)
df_rank_full.to_csv(f'{out_dir}/Filter_Test_v1_Ranking_Full_RoMD.csv', index=False)
df_rank_oos.to_csv(f'{out_dir}/Filter_Test_v1_Ranking_OOS_RoMD.csv', index=False)
df_rank_q1.to_csv(f'{out_dir}/Filter_Test_v1_Ranking_Q1_RoMD.csv', index=False)
best_accepted.to_csv(f'{out_dir}/Filter_Test_v1_Best_Accepted_Trades.csv', index=False)

if not best_rejected.empty:
    best_rejected.to_csv(f'{out_dir}/Filter_Test_v1_Best_Rejected_Trades.csv', index=False)

print('\n' + '=' * 100)
print('✅ CSV保存完了')
print('=' * 100)
print(f'Output dir: {out_dir}')
print('Saved files:')
print('- Filter_Test_v1_All_Results.csv')
print('- Filter_Test_v1_Ranking_Full_RoMD.csv')
print('- Filter_Test_v1_Ranking_OOS_RoMD.csv')
print('- Filter_Test_v1_Ranking_Q1_RoMD.csv')
print('- Filter_Test_v1_Best_Accepted_Trades.csv')
print('- Filter_Test_v1_Best_Rejected_Trades.csv')
