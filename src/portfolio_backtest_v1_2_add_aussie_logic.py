# ==========================================
# Time Entry Portfolio Lab
# portfolio_backtest_v1_2_add_aussie_logic.py
#
# v1.2 Add Aussie Logic
#
# ベース：
# - v1.1.1 AJ Event Fix
# - クロス円16ロジック
# - AJイベントフィルターは6 events
#
# 追加：
# - EA：EUR/AUD Rev.4 4ロジック
# - GA：GBP/AUD 4ロジック
# - 中国実需系 4ロジック
#
# 合計：
# - クロス円16ロジック
# - オージー系12ロジック
# - 合計28ロジック
#
# 注意：
# 2015〜2026のカレンダー定義は、v1.1.1のものをそのまま使用してください。
# ==========================================

from google.colab import drive
import pandas as pd
import numpy as np
import glob
from calendar import monthrange
import matplotlib.pyplot as plt
import os

drive.mount('/content/drive')

# ==========================================
# 1. カレンダー定義
# ==========================================
# ここには v1.1.1 のカレンダー定義をそのまま貼ってください。
#
# 必要なリスト：
# US_CPI_DATES
# US_NFP_DATES
# BOJ_DATES
# FOMC_DATES
# BOE_DATES
# ECB_DATES
# RBA_DATES
# AUD_CPI_DATES
#
# v1.1.1で2026年分を追加済みなら、そのままでOKです。
# ==========================================

# ==========================================
# 1-B. イベントグループ
# ==========================================

EVENTS_4 = set(US_CPI_DATES + US_NFP_DATES + FOMC_DATES + BOJ_DATES)

EVENTS_5_EJ = EVENTS_4.union(set(ECB_DATES))

EVENTS_5_GJ = EVENTS_4.union(set(BOE_DATES))

# v1.1.1修正版：AJからECBを除外
EVENTS_6_AJ = EVENTS_4.union(set(RBA_DATES + AUD_CPI_DATES))

# v1.2追加：EA / GA / China系
EA_REV4_EVENTS = set(US_CPI_DATES + US_NFP_DATES + FOMC_DATES + ECB_DATES + RBA_DATES + AUD_CPI_DATES)

GA_EVENTS = set(US_CPI_DATES + US_NFP_DATES + FOMC_DATES + BOE_DATES + RBA_DATES + AUD_CPI_DATES)

AU_CHINA_EVENTS = set(RBA_DATES + AUD_CPI_DATES)

AJ_CHINA_EVENTS = set(BOJ_DATES + RBA_DATES + AUD_CPI_DATES)

EA_CHINA_EVENTS = set(RBA_DATES + AUD_CPI_DATES + ECB_DATES)

GA_CHINA_EVENTS = set(RBA_DATES + AUD_CPI_DATES + BOE_DATES)

# FOMC前日・当日停止用
FOMC_PREV_OR_TODAY = set()

for d in FOMC_DATES:
    dt = pd.Timestamp(d)
    FOMC_PREV_OR_TODAY.add(dt.strftime('%Y-%m-%d'))
    FOMC_PREV_OR_TODAY.add((dt - pd.Timedelta(days=1)).strftime('%Y-%m-%d'))

# 米国CPI発表週の水曜日
cpi_wednesdays = set()

for d in US_CPI_DATES:
    dt = pd.Timestamp(d)
    wed = dt - pd.Timedelta(days=dt.weekday()) + pd.Timedelta(days=2)
    cpi_wednesdays.add(wed.strftime('%Y-%m-%d'))

# ==========================================
# 1-C. 共通カレンダー関数
# ==========================================

def is_year_end(dt):
    return (dt.month == 12 and dt.day >= 25) or (dt.month == 1 and dt.day <= 3)


def is_calendar_month_end(dt):
    return dt.is_month_end


def get_last_biz_days(year, month, n=3):
    last_day = monthrange(year, month)[1]
    days = []

    for day in range(last_day, 0, -1):
        dt = pd.Timestamp(year=year, month=month, day=day)

        if dt.weekday() < 5:
            days.append(day)

        if len(days) >= n:
            break

    return set(days)


def is_month_end_3_biz_days(dt):
    last_biz_days = get_last_biz_days(dt.year, dt.month, 3)
    return dt.day in last_biz_days


def is_9_to_15(dt):
    return 9 <= dt.day <= 15


def is_25_to_month_end(dt):
    return dt.day >= 25


def is_weekday(dt):
    return dt.weekday() <= 4


def is_fomc_prev_or_today(date_str):
    return date_str in FOMC_PREV_OR_TODAY


# ==========================================
# 2. データロード関数
# ==========================================

def load_data(pair_name):
    files = glob.glob(f'/content/drive/MyDrive/MT5 data/*{pair_name}*.csv')

    if not files:
        print(f"⚠️ データファイルが見つかりません: {pair_name}")
        return None, None, None, None, None, None, None

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

    t = df['Datetime'].values
    o = df['Open'].values
    h = df['High'].values
    l = df['Low'].values

    idx = {pd.Timestamp(dt): i for i, dt in enumerate(t)}
    unique_dates = df['Datetime'].dt.normalize().unique()

    print(f"✅ Loaded {pair_name}: {len(df):,} bars / {df['Datetime'].min()} 〜 {df['Datetime'].max()}")

    return df, t, o, h, l, idx, unique_dates


# ==========================================
# 3. トレード抽出エンジン
# ==========================================

all_trades = []

def run_strategy(
    pair_str,
    strat_name,
    t,
    o,
    h,
    l,
    idx_map,
    unique_dates,
    is_long,
    spread,
    filter_func,
    wd_target,
    en_h,
    en_m,
    ex_h,
    ex_m,
    days_offset,
    sl,
    tp,
    is_uj_special=False,
    uj_mode=None,
    custom_date_rule=None
):
    if t is None:
        return

    for dt_np in unique_dates:
        dt = pd.Timestamp(dt_np)
        date_str = dt.strftime('%Y-%m-%d')
        wd = dt.weekday()

        current_en_h = en_h
        current_en_m = en_m
        current_sl = sl
        current_tp = tp

        # ------------------------------------------
        # UJ特殊稼働日判定
        # ------------------------------------------
        if is_uj_special:

            if uj_mode == 'short_core_calendar_end':
                if dt.day < 20:
                    continue

                if dt.day in [21, 22]:
                    continue

                if dt.month == 8:
                    continue

                if wd == 2:
                    continue

                if is_calendar_month_end(dt):
                    continue

                if dt.day in [20, 25, 30]:
                    current_en_h = 9
                    current_en_m = 55
                    current_sl = 20
                    current_tp = 50
                else:
                    current_en_h = 8
                    current_en_m = 4
                    current_sl = 50
                    current_tp = 999

            elif uj_mode == '25_onwards_wed_thu':
                if dt.day < 25:
                    continue

                if wd not in [2, 3]:
                    continue

            elif uj_mode == '3rd':
                if dt.day != 3:
                    continue

            elif uj_mode == 'aug_1_10':
                if dt.month != 8:
                    continue

                if dt.day > 10:
                    continue

            elif uj_mode == '10th_not_wed':
                if dt.day != 10:
                    continue

                if wd == 2:
                    continue

            else:
                continue

        else:
            if custom_date_rule is not None:
                if not custom_date_rule(dt):
                    continue
            else:
                if wd not in wd_target:
                    continue

        # ------------------------------------------
        # 指標・年末年始・個別停止フィルター
        # ------------------------------------------
        if filter_func(date_str, dt):
            continue

        en_dt = dt + pd.Timedelta(hours=current_en_h, minutes=current_en_m)
        ex_dt = dt + pd.Timedelta(days=days_offset, hours=ex_h, minutes=ex_m)

        if en_dt not in idx_map:
            continue

        s_idx = idx_map[en_dt]

        e_idx = None

        for offset in range(5):
            c_dt = ex_dt + pd.Timedelta(minutes=offset)

            if c_dt in idx_map:
                e_idx = idx_map[c_dt]
                break

        if e_idx is None:
            continue

        if s_idx >= e_idx:
            continue

        # ------------------------------------------
        # spread_mode = entry_adjust
        # ------------------------------------------
        if is_long:
            ep = o[s_idx] + spread
        else:
            ep = o[s_idx] - spread

        sl_val = current_sl * 0.01

        if current_tp == 999:
            tp_val = 999
        else:
            tp_val = current_tp * 0.01

        if is_long:
            sl_price = ep - sl_val
            tp_price = ep + tp_val
        else:
            sl_price = ep + sl_val
            tp_price = ep - tp_val

        pips = 0
        closed = False
        close_time = ex_dt
        exit_reason = 'TimeExit'

        # ------------------------------------------
        # SL/TP判定
        # same_bar_policy = sl_first
        # ------------------------------------------
        for i in range(s_idx, e_idx + 1):
            curr_h = h[i]
            curr_l = l[i]

            if is_long:
                if curr_l <= sl_price:
                    pips = -current_sl
                    closed = True
                    close_time = t[i]
                    exit_reason = 'SL'
                    break

                if current_tp != 999 and curr_h >= tp_price:
                    pips = current_tp
                    closed = True
                    close_time = t[i]
                    exit_reason = 'TP'
                    break

            else:
                if curr_h >= sl_price:
                    pips = -current_sl
                    closed = True
                    close_time = t[i]
                    exit_reason = 'SL'
                    break

                if current_tp != 999 and curr_l <= tp_price:
                    pips = current_tp
                    closed = True
                    close_time = t[i]
                    exit_reason = 'TP'
                    break

        if not closed:
            if is_long:
                pips = (o[e_idx] - ep) * 100
            else:
                pips = (ep - o[e_idx]) * 100

        all_trades.append({
            'Strategy': strat_name,
            'Pair': pair_str,
            'Direction': 'Long' if is_long else 'Short',
            'EntryTime': en_dt,
            'CloseTime': pd.Timestamp(close_time),
            'Pips': round(float(pips), 3),
            'ExitReason': exit_reason,
            'EntryHour': current_en_h,
            'EntryMinute': current_en_m,
            'SL': current_sl,
            'TP': current_tp,
            'Spread': spread
        })


# ==========================================
# 4. フィルター関数
# ==========================================

def filter_ea_rev4(date_str, dt):
    if is_year_end(dt):
        return True

    if dt.month == 10:
        return True

    if is_month_end_3_biz_days(dt):
        return True

    if date_str in EA_REV4_EVENTS:
        return True

    return False


def filter_ga(date_str, dt):
    if is_year_end(dt):
        return True

    if date_str in GA_EVENTS:
        return True

    return False


def filter_au_china(date_str, dt):
    if is_year_end(dt):
        return True

    if dt.month in [8, 10]:
        return True

    if date_str in AU_CHINA_EVENTS:
        return True

    if is_fomc_prev_or_today(date_str):
        return True

    return False


def filter_aj_china(date_str, dt):
    if is_year_end(dt):
        return True

    if dt.month in [2, 8, 10]:
        return True

    if date_str in AJ_CHINA_EVENTS:
        return True

    return False


def filter_ea_china(date_str, dt):
    if is_year_end(dt):
        return True

    if dt.month in [8, 10]:
        return True

    if date_str in EA_CHINA_EVENTS:
        return True

    if is_fomc_prev_or_today(date_str):
        return True

    return False


def filter_ga_china(date_str, dt):
    if is_year_end(dt):
        return True

    if dt.month in [8, 10]:
        return True

    if date_str in GA_CHINA_EVENTS:
        return True

    if is_fomc_prev_or_today(date_str):
        return True

    return False


# ==========================================
# 5. 集計関数
# ==========================================

def calc_summary(df, label):
    if df.empty:
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

    df = df.sort_values('CloseTime').copy()
    df['CumPips'] = df['Pips'].cumsum()
    df['MaxCumPips'] = df['CumPips'].cummax()
    df['Drawdown'] = df['MaxCumPips'] - df['CumPips']

    wins = df[df['Pips'] > 0]['Pips'].sum()
    losses = df[df['Pips'] < 0]['Pips'].sum()

    if losses < 0:
        pf = wins / abs(losses)
    else:
        pf = np.nan

    total_pips = df['Pips'].sum()
    max_dd = df['Drawdown'].max()

    if max_dd > 0:
        romd = total_pips / max_dd
    else:
        romd = np.nan

    win_rate = len(df[df['Pips'] > 0]) / len(df) * 100
    avg_pips = df['Pips'].mean()

    return {
        'Label': label,
        'Trades': len(df),
        'WinRate': round(win_rate, 2),
        'PF': round(pf, 3) if not pd.isna(pf) else np.nan,
        'TotalPips': round(total_pips, 1),
        'MaxDD': round(max_dd, 1),
        'RoMD': round(romd, 2) if not pd.isna(romd) else np.nan,
        'AvgPips': round(avg_pips, 2)
    }


def print_summary_table(df_res):
    periods = [
        {
            'label': 'Full 2015-01 to 2026-03',
            'start': '2015-01-01',
            'end': '2026-03-31 23:59:59'
        },
        {
            'label': 'Legacy IS 2015-01 to 2025-12',
            'start': '2015-01-01',
            'end': '2025-12-31 23:59:59'
        },
        {
            'label': 'Legacy OOS 2026-01 to 2026-03',
            'start': '2026-01-01',
            'end': '2026-03-31 23:59:59'
        },
        {
            'label': 'Strict IS 2015-01 to 2024-12',
            'start': '2015-01-01',
            'end': '2024-12-31 23:59:59'
        },
        {
            'label': 'Strict OOS 2025-01 to 2026-03',
            'start': '2025-01-01',
            'end': '2026-03-31 23:59:59'
        }
    ]

    summaries = []

    for p in periods:
        start = pd.Timestamp(p['start'])
        end = pd.Timestamp(p['end'])

        df_p = df_res[
            (df_res['CloseTime'] >= start) &
            (df_res['CloseTime'] <= end)
        ].copy()

        summaries.append(calc_summary(df_p, p['label']))

    df_summary = pd.DataFrame(summaries)

    print("\n" + "=" * 80)
    print("🏆 Period Summary")
    print("=" * 80)
    print(df_summary.to_string(index=False))

    return df_summary


def print_strategy_summary(df_res):
    rows = []

    for strategy, df_s in df_res.groupby('Strategy'):
        rows.append(calc_summary(df_s, strategy))

    df_strategy = pd.DataFrame(rows)
    df_strategy = df_strategy.sort_values('TotalPips', ascending=False)

    print("\n" + "=" * 80)
    print("📊 Strategy Summary")
    print("=" * 80)
    print(df_strategy.to_string(index=False))

    return df_strategy


def print_yearly_summary(df_res):
    df_res = df_res.copy()
    df_res['Year'] = df_res['CloseTime'].dt.year

    yearly = df_res.groupby('Year')['Pips'].sum().round(1)

    print("\n" + "=" * 80)
    print("📅 Yearly Pips")
    print("=" * 80)
    print(yearly.to_string())

    return yearly


def print_exit_reason_summary(df_res):
    exit_summary = (
        df_res
        .groupby(['Strategy', 'ExitReason'])
        .size()
        .reset_index(name='Count')
        .sort_values(['Strategy', 'ExitReason'])
    )

    print("\n" + "=" * 80)
    print("🚪 Exit Reason Summary")
    print("=" * 80)
    print(exit_summary.to_string(index=False))

    return exit_summary


def print_group_summary(df_res):
    group_map = {}

    cross_jpy = [
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

    ea_rev4 = [
        '17_EA_1B_Wed_Short',
        '18_EA_2_MonWed_Short',
        '19_EA_3_WedThu_Long',
        '20_EA_1A_MonTue_Short'
    ]

    ga = [
        '21_GA_B_3',
        '22_GA_C_2',
        '23_GA_F_2',
        '24_GA_D_1'
    ]

    china = [
        '25_AU_China_Demand',
        '26_AJ_China_Demand',
        '27_EA_China_Demand',
        '28_GA_China_Demand'
    ]

    for s in cross_jpy:
        group_map[s] = 'CrossJPY_16'

    for s in ea_rev4:
        group_map[s] = 'EA_Rev4'

    for s in ga:
        group_map[s] = 'GA'

    for s in china:
        group_map[s] = 'China_Demand'

    df_res = df_res.copy()
    df_res['Group'] = df_res['Strategy'].map(group_map).fillna('Unknown')

    rows = []

    for group, df_g in df_res.groupby('Group'):
        rows.append(calc_summary(df_g, group))

    df_group = pd.DataFrame(rows)
    df_group = df_group.sort_values('TotalPips', ascending=False)

    print("\n" + "=" * 80)
    print("🧩 Group Summary")
    print("=" * 80)
    print(df_group.to_string(index=False))

    return df_group


# ==========================================
# 6. データロード
# ==========================================

print("全通貨ペアデータロード中...")

_, t_ej, o_ej, h_ej, l_ej, idx_ej, dates_ej = load_data('eurjpy_m1')
_, t_gj, o_gj, h_gj, l_gj, idx_gj, dates_gj = load_data('gbpjpy_m1')
_, t_aj, o_aj, h_aj, l_aj, idx_aj, dates_aj = load_data('audjpy_m1')
_, t_uj, o_uj, h_uj, l_uj, idx_uj, dates_uj = load_data('usdjpy_m1')

_, t_ea, o_ea, h_ea, l_ea, idx_ea, dates_ea = load_data('euraud_m1')
_, t_ga, o_ga, h_ga, l_ga, idx_ga, dates_ga = load_data('gbpaud_m1')
_, t_au, o_au, h_au, l_au, idx_au, dates_au = load_data('audusd_m1')

print("\nバックテスト実行中...")


# ==========================================
# 7. クロス円16ロジック
# ==========================================

# --- EJ ---
run_strategy('EJ', '1_EJ_Log1', t_ej, o_ej, h_ej, l_ej, idx_ej, dates_ej, True, 0.010, lambda ds, dt: is_year_end(dt) or dt.month == 2 or dt.day == 1 or ds in cpi_wednesdays, [0, 2], 13, 55, 4, 55, 1, 70, 250)

run_strategy('EJ', '2_EJ_NightBlitz_20', t_ej, o_ej, h_ej, l_ej, idx_ej, dates_ej, True, 0.010, lambda ds, dt: is_year_end(dt) or ds in EVENTS_5_EJ, [0, 2], 20, 56, 4, 45, 1, 45, 70)

run_strategy('EJ', '3_EJ_NightBlitz_21', t_ej, o_ej, h_ej, l_ej, idx_ej, dates_ej, True, 0.010, lambda ds, dt: is_year_end(dt) or ds in EVENTS_5_EJ, [0, 2], 21, 56, 5, 27, 1, 75, 70)

# --- GJ ---
run_strategy('GJ', '4_GJ_Port_Log1', t_gj, o_gj, h_gj, l_gj, idx_gj, dates_gj, True, 0.020, lambda ds, dt: is_year_end(dt) or dt.month == 12 or dt.day in [1, 2, 29, 30, 31], [1, 2], 0, 0, 8, 55, 0, 130, 90)

run_strategy('GJ', '5_GJ_Port_Log2', t_gj, o_gj, h_gj, l_gj, idx_gj, dates_gj, False, 0.020, lambda ds, dt: is_year_end(dt) or ds in EVENTS_5_GJ or dt.day in [18, 19, 27], [1, 3, 4], 9, 55, 23, 55, 0, 90, 999)

run_strategy('GJ', '6_GJ_Old_Mon', t_gj, o_gj, h_gj, l_gj, idx_gj, dates_gj, True, 0.020, lambda ds, dt: is_year_end(dt) or ds in EVENTS_5_GJ or dt.month in [1, 2], [0], 15, 45, 22, 50, 0, 50, 210)

run_strategy('GJ', '7_GJ_Mon_Blitz', t_gj, o_gj, h_gj, l_gj, idx_gj, dates_gj, True, 0.020, lambda ds, dt: is_year_end(dt) or ds in EVENTS_5_GJ, [0], 18, 2, 23, 2, 0, 130, 250)

# --- AJ ---
run_strategy('AJ', '8_AJ_Core1', t_aj, o_aj, h_aj, l_aj, idx_aj, dates_aj, True, 0.015, lambda ds, dt: is_year_end(dt) or ds in EVENTS_6_AJ, [0], 8, 1, 22, 46, 0, 70, 110)

run_strategy('AJ', '9_AJ_Core2', t_aj, o_aj, h_aj, l_aj, idx_aj, dates_aj, False, 0.015, lambda ds, dt: is_year_end(dt) or ds in EVENTS_6_AJ or dt.month in [6, 9] or dt.day in [1, 20] or dt.day >= 26, [3], 17, 14, 1, 14, 1, 30, 80)

run_strategy('AJ', '10_AJ_SatA', t_aj, o_aj, h_aj, l_aj, idx_aj, dates_aj, False, 0.015, lambda ds, dt: is_year_end(dt) or ds in EVENTS_6_AJ, [4], 10, 58, 13, 51, 0, 50, 25)

run_strategy('AJ', '11_AJ_SatB', t_aj, o_aj, h_aj, l_aj, idx_aj, dates_aj, False, 0.015, lambda ds, dt: is_year_end(dt) or ds in EVENTS_6_AJ, [4], 18, 57, 1, 43, 1, 55, 95)

# --- UJ ---
f_uj_4 = lambda ds, dt: is_year_end(dt) or ds in EVENTS_4

run_strategy('UJ', '12_UJ_Short_Core', t_uj, o_uj, h_uj, l_uj, idx_uj, dates_uj, False, 0.005, f_uj_4, [], 9, 55, 14, 56, 0, 20, 50, True, 'short_core_calendar_end')

run_strategy('UJ', '13_UJ_Fix_MidWeek', t_uj, o_uj, h_uj, l_uj, idx_uj, dates_uj, True, 0.005, f_uj_4, [], 18, 4, 22, 3, 0, 95, 95, True, '25_onwards_wed_thu')

run_strategy('UJ', '14_UJ_Sat_3rd', t_uj, o_uj, h_uj, l_uj, idx_uj, dates_uj, False, 0.005, f_uj_4, [], 20, 1, 3, 8, 1, 45, 70, True, '3rd')

run_strategy('UJ', '15_UJ_Sat_Aug', t_uj, o_uj, h_uj, l_uj, idx_uj, dates_uj, False, 0.005, f_uj_4, [], 19, 0, 23, 30, 0, 20, 35, True, 'aug_1_10')

run_strategy('UJ', '16_UJ_T10A', t_uj, o_uj, h_uj, l_uj, idx_uj, dates_uj, True, 0.005, lambda ds, dt: is_year_end(dt) or ds in BOJ_DATES, [], 2, 58, 9, 50, 0, 45, 110, True, '10th_not_wed')


# ==========================================
# 8. v1.2追加：EA Rev.4 4ロジック
# ==========================================

run_strategy('EA', '17_EA_1B_Wed_Short', t_ea, o_ea, h_ea, l_ea, idx_ea, dates_ea, False, 0.015, lambda ds, dt: filter_ea_rev4(ds, dt) or dt.month == 8, [2], 9, 59, 20, 58, 0, 70, 175)

run_strategy('EA', '18_EA_2_MonWed_Short', t_ea, o_ea, h_ea, l_ea, idx_ea, dates_ea, False, 0.015, lambda ds, dt: filter_ea_rev4(ds, dt) or dt.month in [1, 8], [0, 1, 2], 9, 59, 5, 26, 1, 90, 180)

run_strategy('EA', '19_EA_3_WedThu_Long', t_ea, o_ea, h_ea, l_ea, idx_ea, dates_ea, True, 0.015, filter_ea_rev4, [2, 3], 20, 56, 10, 0, 1, 90, 999)

run_strategy('EA', '20_EA_1A_MonTue_Short', t_ea, o_ea, h_ea, l_ea, idx_ea, dates_ea, False, 0.015, lambda ds, dt: filter_ea_rev4(ds, dt) or dt.month == 8, [0, 1], 10, 1, 16, 0, 0, 50, 125)


# ==========================================
# 9. v1.2追加：GA 4ロジック
# ==========================================

run_strategy('GA', '21_GA_B_3', t_ga, o_ga, h_ga, l_ga, idx_ga, dates_ga, True, 0.020, filter_ga, [0], 21, 2, 10, 0, 1, 220, 100)

run_strategy('GA', '22_GA_C_2', t_ga, o_ga, h_ga, l_ga, idx_ga, dates_ga, True, 0.020, filter_ga, [3], 16, 56, 1, 15, 1, 70, 80)

run_strategy('GA', '23_GA_F_2', t_ga, o_ga, h_ga, l_ga, idx_ga, dates_ga, False, 0.020, filter_ga, [4], 19, 42, 22, 45, 0, 90, 200)

run_strategy('GA', '24_GA_D_1', t_ga, o_ga, h_ga, l_ga, idx_ga, dates_ga, True, 0.020, filter_ga, [4], 22, 44, 3, 8, 1, 90, 200)


# ==========================================
# 10. v1.2追加：中国実需系 4ロジック
# ==========================================

au_china_rule = lambda dt: is_weekday(dt) and (is_9_to_15(dt) or is_25_to_month_end(dt))

aj_china_rule = lambda dt: is_weekday(dt) and is_9_to_15(dt)

ea_china_rule = lambda dt: is_weekday(dt) and is_9_to_15(dt)

ga_china_rule = lambda dt: is_weekday(dt) and is_9_to_15(dt)

run_strategy('AU', '25_AU_China_Demand', t_au, o_au, h_au, l_au, idx_au, dates_au, True, 0.00015, filter_au_china, [], 10, 0, 15, 50, 0, 40, 40, False, None, au_china_rule)

run_strategy('AJ', '26_AJ_China_Demand', t_aj, o_aj, h_aj, l_aj, idx_aj, dates_aj, True, 0.015, filter_aj_china, [], 10, 0, 15, 50, 0, 45, 80, False, None, aj_china_rule)

run_strategy('EA', '27_EA_China_Demand', t_ea, o_ea, h_ea, l_ea, idx_ea, dates_ea, False, 0.015, filter_ea_china, [], 10, 0, 15, 50, 0, 60, 60, False, None, ea_china_rule)

run_strategy('GA', '28_GA_China_Demand', t_ga, o_ga, h_ga, l_ga, idx_ga, dates_ga, False, 0.020, filter_ga_china, [], 10, 0, 16, 10, 0, 75, 70, False, None, ga_china_rule)


# ==========================================
# 11. 集計・保存
# ==========================================

if all_trades:
    df_res = pd.DataFrame(all_trades)
    df_res = df_res.sort_values('CloseTime').reset_index(drop=True)

    df_res['CumPips'] = df_res['Pips'].cumsum()
    df_res['MaxCumPips'] = df_res['CumPips'].cummax()
    df_res['Drawdown'] = df_res['MaxCumPips'] - df_res['CumPips']

    print("\n" + "=" * 80)
    print("🏆 Portfolio Integration Test v1.2 Add Aussie Logic")
    print("=" * 80)

    df_period_summary = print_summary_table(df_res)
    df_strategy_summary = print_strategy_summary(df_res)
    yearly = print_yearly_summary(df_res)
    exit_summary = print_exit_reason_summary(df_res)
    group_summary = print_group_summary(df_res)

    output_trade_log = '/content/Portfolio_Integration_Results_v1_2_add_aussie_logic.csv'
    output_period_summary = '/content/Portfolio_Period_Summary_v1_2_add_aussie_logic.csv'
    output_strategy_summary = '/content/Portfolio_Strategy_Summary_v1_2_add_aussie_logic.csv'
    output_exit_summary = '/content/Portfolio_ExitReason_Summary_v1_2_add_aussie_logic.csv'
    output_group_summary = '/content/Portfolio_Group_Summary_v1_2_add_aussie_logic.csv'

    df_res.to_csv(output_trade_log, index=False)
    df_period_summary.to_csv(output_period_summary, index=False)
    df_strategy_summary.to_csv(output_strategy_summary, index=False)
    exit_summary.to_csv(output_exit_summary, index=False)
    group_summary.to_csv(output_group_summary, index=False)

    print("\n" + "=" * 80)
    print("✅ CSV保存完了")
    print("=" * 80)
    print(f"Trade Log       : {output_trade_log}")
    print(f"Period Summary  : {output_period_summary}")
    print(f"Strategy Summary: {output_strategy_summary}")
    print(f"Exit Summary    : {output_exit_summary}")
    print(f"Group Summary   : {output_group_summary}")

else:
    print("トレードが生成されませんでした。")
