# ==========================================
# Time Entry Portfolio Lab
# analysis_2026_q1_v2_with_aussie.py
#
# 目的：
# - v1.2 Add Aussie Logic のトレード履歴CSVを読み込む
# - 2026 Q1の分析CSVを11個出力する
#
# 入力：
# /content/Portfolio_Integration_Results_v1_2_add_aussie_logic.csv
#
# 出力：
# /content/q1_2026_analysis_v2_with_aussie/
# ==========================================

from google.colab import drive
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os

drive.mount('/content/drive')

# ==========================================
# 1. 入力CSVパス
# ==========================================

CSV_PATH = '/content/Portfolio_Integration_Results_v1_2_add_aussie_logic.csv'

# Google Driveに置いている場合はこちらを使う
# CSV_PATH = '/content/drive/MyDrive/time-entry-portfolio-lab/results/v1_2_add_aussie_logic/Portfolio_Integration_Results_v1_2_add_aussie_logic.csv'

if not os.path.exists(CSV_PATH):
    raise FileNotFoundError(f'CSVが見つかりません: {CSV_PATH}')

# ==========================================
# 2. 読み込み
# ==========================================

df = pd.read_csv(CSV_PATH)

df['EntryTime'] = pd.to_datetime(df['EntryTime'])
df['CloseTime'] = pd.to_datetime(df['CloseTime'])

df = df.sort_values('CloseTime').reset_index(drop=True)

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
# 3. 分析対象期間
# ==========================================

Q1_START = pd.Timestamp('2026-01-01')
Q1_END = pd.Timestamp('2026-03-31 23:59:59')

df_q1 = df[
    (df['CloseTime'] >= Q1_START) &
    (df['CloseTime'] <= Q1_END)
].copy()

if df_q1.empty:
    raise ValueError('2026年Q1のトレードが見つかりません。')

df_q1 = df_q1.sort_values('CloseTime').reset_index(drop=True)

print('\n✅ Q1 2026 extracted')
print(f'Trades: {len(df_q1):,}')
print(f"Period: {df_q1['CloseTime'].min()} 〜 {df_q1['CloseTime'].max()}")

# ==========================================
# 4. グループ定義
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

df_q1['Group'] = df_q1['Strategy'].map(GROUP_MAP).fillna('Unknown')

# ==========================================
# 5. 共通集計関数
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
            'AvgPips': np.nan,
            'WinsPips': 0.0,
            'LossPips': 0.0
        }

    d = d.sort_values('CloseTime').copy()
    d['CumPips'] = d['Pips'].cumsum()
    d['MaxCumPips'] = d['CumPips'].cummax()
    d['Drawdown'] = d['MaxCumPips'] - d['CumPips']

    wins_pips = d[d['Pips'] > 0]['Pips'].sum()
    loss_pips = d[d['Pips'] < 0]['Pips'].sum()

    if loss_pips < 0:
        pf = wins_pips / abs(loss_pips)
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
        'AvgPips': round(avg_pips, 2),
        'WinsPips': round(wins_pips, 1),
        'LossPips': round(loss_pips, 1)
    }


def add_equity_columns(input_df):
    d = input_df.sort_values('CloseTime').copy()
    d['CumPips'] = d['Pips'].cumsum()
    d['MaxCumPips'] = d['CumPips'].cummax()
    d['Drawdown'] = d['MaxCumPips'] - d['CumPips']
    return d


# ==========================================
# 6. Total Summary
# ==========================================

df_total = pd.DataFrame([
    calc_metrics(df_q1, 'Q1 2026 Total v1.2 with Aussie')
])

print('\n' + '=' * 80)
print('🏆 Q1 2026 Total Summary')
print('=' * 80)
print(df_total.to_string(index=False))

# ==========================================
# 7. Strategy Summary
# ==========================================

strategy_rows = []

for strategy, sub in df_q1.groupby('Strategy'):
    strategy_rows.append(calc_metrics(sub, strategy))

df_strategy = pd.DataFrame(strategy_rows)
df_strategy = df_strategy.sort_values('TotalPips', ascending=True).reset_index(drop=True)

print('\n' + '=' * 80)
print('📊 Q1 2026 Strategy Summary')
print('=' * 80)
print(df_strategy.to_string(index=False))

# ==========================================
# 8. Monthly Summary
# ==========================================

df_q1['Month'] = df_q1['CloseTime'].dt.to_period('M').astype(str)

monthly_rows = []

for month, sub in df_q1.groupby('Month'):
    monthly_rows.append(calc_metrics(sub, month))

df_monthly = pd.DataFrame(monthly_rows)
df_monthly = df_monthly.sort_values('Label').reset_index(drop=True)

print('\n' + '=' * 80)
print('📅 Q1 2026 Monthly Summary')
print('=' * 80)
print(df_monthly.to_string(index=False))

# ==========================================
# 9. Daily Summary
# ==========================================

df_q1['Date'] = df_q1['CloseTime'].dt.date

daily_rows = []

for date, sub in df_q1.groupby('Date'):
    daily_rows.append(calc_metrics(sub, str(date)))

df_daily = pd.DataFrame(daily_rows)
df_daily = df_daily.sort_values('TotalPips', ascending=True).reset_index(drop=True)

print('\n' + '=' * 80)
print('📉 Q1 2026 Daily Summary - Worst First')
print('=' * 80)
print(df_daily.head(20).to_string(index=False))

# ==========================================
# 10. Exclusion Test
# ==========================================

base_metrics = calc_metrics(df_q1, 'Base')

exclusion_rows = []

for strategy in sorted(df_q1['Strategy'].unique()):
    sub = df_q1[df_q1['Strategy'] != strategy].copy()
    m = calc_metrics(sub, f'Exclude {strategy}')

    m['ExcludedStrategy'] = strategy
    m['DeltaTotalPips'] = round(m['TotalPips'] - base_metrics['TotalPips'], 1)

    if not pd.isna(m['MaxDD']) and not pd.isna(base_metrics['MaxDD']):
        m['DeltaMaxDD'] = round(m['MaxDD'] - base_metrics['MaxDD'], 1)
    else:
        m['DeltaMaxDD'] = np.nan

    if not pd.isna(m['PF']) and not pd.isna(base_metrics['PF']):
        m['DeltaPF'] = round(m['PF'] - base_metrics['PF'], 3)
    else:
        m['DeltaPF'] = np.nan

    if not pd.isna(m['RoMD']) and not pd.isna(base_metrics['RoMD']):
        m['DeltaRoMD'] = round(m['RoMD'] - base_metrics['RoMD'], 2)
    else:
        m['DeltaRoMD'] = np.nan

    exclusion_rows.append(m)

df_exclusion = pd.DataFrame(exclusion_rows)

df_exclusion = df_exclusion[
    [
        'ExcludedStrategy',
        'Trades',
        'WinRate',
        'PF',
        'TotalPips',
        'MaxDD',
        'RoMD',
        'DeltaTotalPips',
        'DeltaMaxDD',
        'DeltaPF',
        'DeltaRoMD'
    ]
]

df_exclusion = df_exclusion.sort_values('DeltaRoMD', ascending=False).reset_index(drop=True)

print('\n' + '=' * 80)
print('🧪 Q1 2026 Exclusion Test')
print('=' * 80)
print(df_exclusion.to_string(index=False))

# ==========================================
# 11. Drawdown Timeline
# ==========================================

df_dd = add_equity_columns(df_q1)

max_dd = df_dd['Drawdown'].max()
max_dd_row = df_dd[df_dd['Drawdown'] == max_dd].iloc[0]

dd_bottom_time = max_dd_row['CloseTime']
dd_peak_value = max_dd_row['MaxCumPips']
dd_bottom_value = max_dd_row['CumPips']

peak_rows = df_dd[
    (df_dd['CloseTime'] <= dd_bottom_time) &
    (df_dd['CumPips'] == dd_peak_value)
]

if not peak_rows.empty:
    dd_peak_time = peak_rows.iloc[-1]['CloseTime']
else:
    dd_peak_time = df_dd.iloc[0]['CloseTime']

print('\n' + '=' * 80)
print('📉 Q1 2026 Max Drawdown Info')
print('=' * 80)
print(f'MaxDD       : {max_dd:.1f} pips')
print(f'Peak Time   : {dd_peak_time}')
print(f'Bottom Time : {dd_bottom_time}')
print(f'Peak Equity : {dd_peak_value:.1f}')
print(f'Bottom Eq   : {dd_bottom_value:.1f}')

# ==========================================
# 12. Drawdown Window Trades
# ==========================================

df_dd_window = df_q1[
    (df_q1['CloseTime'] >= dd_peak_time) &
    (df_q1['CloseTime'] <= dd_bottom_time)
].copy()

df_dd_window = df_dd_window.sort_values('CloseTime').reset_index(drop=True)

print('\n' + '=' * 80)
print('🧨 Q1 2026 Drawdown Window Trades')
print('=' * 80)

if df_dd_window.empty:
    print('DD window trades not found.')
else:
    print(df_dd_window[['Strategy', 'Group', 'Pair', 'Direction', 'EntryTime', 'CloseTime', 'Pips', 'ExitReason']].to_string(index=False))

# ==========================================
# 13. Group Summary
# ==========================================

group_rows = []

for group, sub in df_q1.groupby('Group'):
    group_rows.append(calc_metrics(sub, group))

df_group = pd.DataFrame(group_rows)
df_group = df_group.sort_values('TotalPips', ascending=False).reset_index(drop=True)

print('\n' + '=' * 80)
print('🧩 Q1 2026 Group Summary')
print('=' * 80)
print(df_group.to_string(index=False))

# ==========================================
# 14. Pair Summary
# ==========================================

pair_rows = []

for pair, sub in df_q1.groupby('Pair'):
    pair_rows.append(calc_metrics(sub, pair))

df_pair = pd.DataFrame(pair_rows)
df_pair = df_pair.sort_values('TotalPips', ascending=True).reset_index(drop=True)

print('\n' + '=' * 80)
print('💱 Q1 2026 Pair Summary')
print('=' * 80)
print(df_pair.to_string(index=False))

# ==========================================
# 15. Direction Summary
# ==========================================

direction_rows = []

for direction, sub in df_q1.groupby('Direction'):
    direction_rows.append(calc_metrics(sub, direction))

df_direction = pd.DataFrame(direction_rows)
df_direction = df_direction.sort_values('TotalPips', ascending=True).reset_index(drop=True)

print('\n' + '=' * 80)
print('↕️ Q1 2026 Direction Summary')
print('=' * 80)
print(df_direction.to_string(index=False))

# ==========================================
# 16. Pair Direction Summary
# ==========================================

pair_direction_rows = []

for keys, sub in df_q1.groupby(['Pair', 'Direction']):
    pair = keys[0]
    direction = keys[1]
    pair_direction_rows.append(calc_metrics(sub, f'{pair}_{direction}'))

df_pair_direction = pd.DataFrame(pair_direction_rows)
df_pair_direction = df_pair_direction.sort_values('TotalPips', ascending=True).reset_index(drop=True)

print('\n' + '=' * 80)
print('💱↕️ Q1 2026 Pair Direction Summary')
print('=' * 80)
print(df_pair_direction.to_string(index=False))

# ==========================================
# 17. CSV保存
# ==========================================

out_dir = '/content/q1_2026_analysis_v2_with_aussie'
os.makedirs(out_dir, exist_ok=True)

df_total.to_csv(f'{out_dir}/Q1_2026_Total_Summary.csv', index=False)
df_strategy.to_csv(f'{out_dir}/Q1_2026_Strategy_Summary.csv', index=False)
df_monthly.to_csv(f'{out_dir}/Q1_2026_Monthly_Summary.csv', index=False)
df_daily.to_csv(f'{out_dir}/Q1_2026_Daily_Summary.csv', index=False)
df_exclusion.to_csv(f'{out_dir}/Q1_2026_Exclusion_Test.csv', index=False)
df_dd.to_csv(f'{out_dir}/Q1_2026_Drawdown_Timeline.csv', index=False)
df_dd_window.to_csv(f'{out_dir}/Q1_2026_Drawdown_Window_Trades.csv', index=False)
df_group.to_csv(f'{out_dir}/Q1_2026_Group_Summary.csv', index=False)
df_pair.to_csv(f'{out_dir}/Q1_2026_Pair_Summary.csv', index=False)
df_direction.to_csv(f'{out_dir}/Q1_2026_Direction_Summary.csv', index=False)
df_pair_direction.to_csv(f'{out_dir}/Q1_2026_Pair_Direction_Summary.csv', index=False)

print('\n' + '=' * 80)
print('✅ Q1 2026 v2 CSV保存完了')
print('=' * 80)
print(f'Output dir: {out_dir}')

# ==========================================
# 18. グラフ表示
# ==========================================

plt.figure(figsize=(14, 5))
plt.plot(df_dd['CloseTime'], df_dd['CumPips'])
plt.title('Q1 2026 Equity Curve - v1.2 with Aussie')
plt.xlabel('CloseTime')
plt.ylabel('Cum Pips')
plt.grid(True)
plt.show()

plt.figure(figsize=(14, 5))
plt.plot(df_dd['CloseTime'], df_dd['Drawdown'])
plt.title('Q1 2026 Drawdown Curve - v1.2 with Aussie')
plt.xlabel('CloseTime')
plt.ylabel('Drawdown Pips')
plt.grid(True)
plt.show()

print('\n✅ Q1 2026 v2 analysis completed.')
