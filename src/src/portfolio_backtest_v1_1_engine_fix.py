# ==========================================
# Time Entry Portfolio Lab
# portfolio_backtest_v1_1_engine_fix.py
#
# v1.1 Engine Fix
# 対象：現行マスター16ロジック
#
# 修正内容：
# - UJ_Short_Coreはカレンダー末日停止を正式採用
# - UJ_Short_Core通常日Entryを08:04へ修正
# - UJ_Short_Core通常日は SL50 / TPなし へ修正
# - UJ_Short_Coreゴトー日は SL20 / TP50
# - UJ_Fix_MidWeekは水曜・木曜で維持
# - 12A/12B二重計上を廃止
# - SL/TP同一足到達時はSL優先
# - スプレッド処理は現行方式 entry_adjust を維持
# ==========================================

from google.colab import drive
import pandas as pd
import numpy as np
import glob
from calendar import monthrange
import matplotlib.pyplot as plt

drive.mount('/content/drive')

# ==========================================
# 1. カレンダー定義
# ==========================================
US_CPI_DATES = ['2015-01-16', '2015-02-26', '2015-03-24', '2015-04-17', '2015-05-22', '2015-06-18', '2015-07-17', '2015-08-19', '2015-09-16', '2015-10-15', '2015-11-17', '2015-12-15', '2016-01-20', '2016-02-19', '2016-03-16', '2016-04-14', '2016-05-17', '2016-06-16', '2016-07-15', '2016-08-16', '2016-09-16', '2016-10-18', '2016-11-17', '2016-12-15', '2017-01-18', '2017-02-15', '2017-03-15', '2017-04-14', '2017-05-12', '2017-06-14', '2017-07-14', '2017-08-11', '2017-09-14', '2017-10-13', '2017-11-15', '2017-12-13', '2018-01-12', '2018-02-14', '2018-03-13', '2018-04-11', '2018-05-10', '2018-06-12', '2018-07-12', '2018-08-10', '2018-09-13', '2018-10-11', '2018-11-14', '2018-12-12', '2019-01-11', '2019-02-13', '2019-03-12', '2019-04-10', '2019-05-10', '2019-06-12', '2019-07-11', '2019-08-13', '2019-09-12', '2019-10-10', '2019-11-13', '2019-12-11', '2020-01-14', '2020-02-13', '2020-03-11', '2020-04-10', '2020-05-12', '2020-06-10', '2020-07-14', '2020-08-12', '2020-09-11', '2020-10-13', '2020-11-12', '2020-12-10', '2021-01-13', '2021-02-10', '2021-03-10', '2021-04-13', '2021-05-12', '2021-06-10', '2021-07-13', '2021-08-11', '2021-09-14', '2021-10-13', '2021-11-10', '2021-12-10', '2022-01-12', '2022-02-10', '2022-03-10', '2022-04-12', '2022-05-11', '2022-06-10', '2022-07-13', '2022-08-10', '2022-09-13', '2022-10-13', '2022-11-10', '2022-12-13', '2023-01-12', '2023-02-14', '2023-03-14', '2023-04-12', '2023-05-10', '2023-06-13', '2023-07-12', '2023-08-10', '2023-09-13', '2023-10-12', '2023-11-14', '2023-12-12', '2024-01-11', '2024-02-13', '2024-03-12', '2024-04-10', '2024-05-15', '2024-06-12', '2024-07-11', '2024-08-14', '2024-09-11', '2024-10-10', '2024-11-13', '2024-12-11', '2025-01-15', '2025-02-12', '2025-03-12', '2025-04-09', '2025-05-14', '2025-06-11', '2025-07-16', '2025-08-13', '2025-09-10', '2025-10-16', '2025-11-13', '2025-12-10']
US_NFP_DATES = ['2015-01-09', '2015-02-06', '2015-03-06', '2015-04-03', '2015-05-08', '2015-06-05', '2015-07-02', '2015-08-07', '2015-09-04', '2015-10-02', '2015-11-06', '2015-12-04', '2016-01-08', '2016-02-05', '2016-03-04', '2016-04-01', '2016-05-06', '2016-06-03', '2016-07-08', '2016-08-05', '2016-09-02', '2016-10-07', '2016-11-04', '2016-12-02', '2017-01-06', '2017-02-03', '2017-03-10', '2017-04-07', '2017-05-05', '2017-06-02', '2017-07-07', '2017-08-04', '2017-09-01', '2017-10-06', '2017-11-03', '2017-12-08', '2018-01-05', '2018-02-02', '2018-03-09', '2018-04-06', '2018-05-04', '2018-06-01', '2018-07-06', '2018-08-03', '2018-09-07', '2018-10-05', '2018-11-02', '2018-12-07', '2019-01-04', '2019-02-01', '2019-03-08', '2019-04-05', '2019-05-03', '2019-06-07', '2019-07-05', '2019-08-02', '2019-09-06', '2019-10-04', '2019-11-01', '2019-12-06', '2020-01-10', '2020-02-07', '2020-03-06', '2020-04-03', '2020-05-08', '2020-06-05', '2020-07-02', '2020-08-07', '2020-09-04', '2020-10-02', '2020-11-06', '2020-12-04', '2021-01-08', '2021-02-05', '2021-03-05', '2021-04-02', '2021-05-07', '2021-06-04', '2021-07-02', '2021-08-06', '2021-09-03', '2021-10-08', '2021-11-05', '2021-12-03', '2022-01-07', '2022-02-04', '2022-03-04', '2022-04-01', '2022-05-06', '2022-06-03', '2022-07-08', '2022-08-05', '2022-09-02', '2022-10-07', '2022-11-04', '2022-12-02', '2023-01-06', '2023-02-03', '2023-03-10', '2023-04-07', '2023-05-05', '2023-06-02', '2023-07-07', '2023-08-04', '2023-09-01', '2023-10-06', '2023-11-03', '2023-12-08', '2024-01-05', '2024-02-02', '2024-03-08', '2024-04-05', '2024-05-03', '2024-06-07', '2024-07-05', '2024-08-02', '2024-09-06', '2024-10-04', '2024-11-01', '2024-12-06', '2025-01-10', '2025-02-07', '2025-03-07', '2025-04-04', '2025-05-02', '2025-06-06', '2025-07-03', '2025-08-01', '2025-09-05', '2025-10-03', '2025-11-07', '2025-12-05']
BOJ_DATES = ['2015-01-21', '2015-02-18', '2015-03-17', '2015-04-08', '2015-04-30', '2015-05-22', '2015-06-19', '2015-07-15', '2015-08-07', '2015-09-15', '2015-10-07', '2015-10-30', '2015-11-19', '2015-12-18', '2016-01-29', '2016-03-15', '2016-04-28', '2016-06-16', '2016-07-29', '2016-09-21', '2016-11-01', '2016-12-20', '2017-01-31', '2017-03-16', '2017-04-27', '2017-06-16', '2017-07-20', '2017-09-21', '2017-10-31', '2017-12-21', '2018-01-23', '2018-03-09', '2018-04-27', '2018-06-15', '2018-07-31', '2018-09-19', '2018-10-31', '2018-12-20', '2019-01-23', '2019-03-15', '2019-04-25', '2019-06-20', '2019-07-30', '2019-09-19', '2019-10-31', '2019-12-19', '2020-01-21', '2020-03-16', '2020-04-27', '2020-05-22', '2020-06-16', '2020-07-15', '2020-09-17', '2020-10-29', '2020-12-18', '2021-01-21', '2021-03-19', '2021-04-27', '2021-06-18', '2021-07-16', '2021-09-22', '2021-10-28', '2021-12-17', '2022-01-18', '2022-03-18', '2022-04-28', '2022-06-17', '2022-07-21', '2022-09-22', '2022-10-28', '2022-12-20', '2023-01-18', '2023-03-10', '2023-04-28', '2023-06-16', '2023-07-28', '2023-09-22', '2023-10-31', '2023-12-19', '2024-01-23', '2024-03-19', '2024-04-26', '2024-06-14', '2024-07-31', '2024-09-20', '2024-10-31', '2024-12-19', '2025-01-24', '2025-03-19', '2025-04-25', '2025-06-17', '2025-07-31', '2025-09-19', '2025-10-31', '2025-12-19']
FOMC_DATES = ['2015-01-28', '2015-03-18', '2015-04-29', '2015-06-17', '2015-07-29', '2015-09-17', '2015-10-28', '2015-12-16', '2016-01-27', '2016-03-16', '2016-04-27', '2016-06-15', '2016-07-27', '2016-09-21', '2016-11-02', '2016-12-14', '2017-02-01', '2017-03-15', '2017-05-03', '2017-06-14', '2017-07-26', '2017-09-20', '2017-11-01', '2017-12-13', '2018-01-31', '2018-03-21', '2018-05-02', '2018-06-13', '2018-08-01', '2018-09-26', '2018-11-08', '2018-12-19', '2019-01-30', '2019-03-20', '2019-05-01', '2019-06-19', '2019-07-31', '2019-09-18', '2019-10-30', '2019-12-11', '2020-01-29', '2020-03-03', '2020-03-15', '2020-04-29', '2020-06-10', '2020-07-29', '2020-09-16', '2020-11-05', '2020-12-16', '2021-01-27', '2021-03-17', '2021-04-28', '2021-06-16', '2021-07-28', '2021-09-22', '2021-11-03', '2021-12-15', '2022-01-26', '2022-03-16', '2022-05-04', '2022-06-15', '2022-07-27', '2022-09-21', '2022-11-02', '2022-12-14', '2023-02-01', '2023-03-22', '2023-05-03', '2023-06-14', '2023-07-26', '2023-09-20', '2023-11-01', '2023-12-13', '2024-01-31', '2024-03-20', '2024-05-01', '2024-06-12', '2024-07-31', '2024-09-18', '2024-11-07', '2024-12-18', '2025-01-29', '2025-03-19', '2025-05-07', '2025-06-18', '2025-07-30', '2025-09-17', '2025-10-29', '2025-12-10']
BOE_DATES = ['2015-01-08', '2015-02-05', '2015-03-05', '2015-04-09', '2015-05-11', '2015-06-04', '2015-07-09', '2015-08-06', '2015-09-10', '2015-10-08', '2015-11-05', '2015-12-10', '2016-01-14', '2016-02-04', '2016-03-17', '2016-04-14', '2016-05-12', '2016-06-16', '2016-07-14', '2016-08-04', '2016-09-15', '2016-10-13', '2016-11-03', '2016-12-15', '2017-02-02', '2017-03-16', '2017-05-11', '2017-06-15', '2017-08-03', '2017-09-14', '2017-11-02', '2017-12-14', '2018-02-08', '2018-03-22', '2018-05-10', '2018-06-21', '2018-08-02', '2018-09-13', '2018-11-01', '2018-12-20', '2019-02-07', '2019-03-21', '2019-05-02', '2019-06-20', '2019-08-01', '2019-09-19', '2019-11-07', '2019-12-19', '2020-01-30', '2020-03-11', '2020-03-19', '2020-03-26', '2020-05-07', '2020-06-18', '2020-08-06', '2020-09-17', '2020-11-05', '2020-12-17', '2021-02-04', '2021-03-18', '2021-05-06', '2021-06-24', '2021-08-05', '2021-09-23', '2021-11-04', '2021-12-16', '2022-02-03', '2022-03-17', '2022-05-05', '2022-06-16', '2022-08-04', '2022-09-22', '2022-11-03', '2022-12-15', '2023-02-02', '2023-03-23', '2023-05-11', '2023-06-22', '2023-08-03', '2023-09-21', '2023-11-02', '2023-12-14', '2024-02-01', '2024-03-21', '2024-05-09', '2024-06-20', '2024-08-01', '2024-09-19', '2024-11-07', '2024-12-19', '2025-02-06', '2025-03-20', '2025-05-08', '2025-06-19', '2025-08-07', '2025-09-18', '2025-11-06', '2025-12-18']
ECB_DATES = ['2015-01-22', '2015-03-05', '2015-04-15', '2015-06-03', '2015-07-16', '2015-09-03', '2015-10-22', '2015-12-03', '2016-01-21', '2016-03-10', '2016-04-21', '2016-06-02', '2016-07-21', '2016-09-08', '2016-10-20', '2016-12-08', '2017-01-19', '2017-03-09', '2017-04-27', '2017-06-08', '2017-07-20', '2017-09-07', '2017-10-26', '2017-12-14', '2018-01-25', '2018-03-08', '2018-04-26', '2018-06-14', '2018-07-26', '2018-09-13', '2018-10-25', '2018-12-13', '2019-01-24', '2019-03-07', '2019-04-10', '2019-06-06', '2019-07-25', '2019-09-12', '2019-10-24', '2019-12-12', '2020-01-23', '2020-03-12', '2020-04-30', '2020-06-04', '2020-07-16', '2020-09-10', '2020-10-29', '2020-12-10', '2021-01-21', '2021-03-11', '2021-04-22', '2021-06-10', '2021-07-22', '2021-09-09', '2021-10-28', '2021-12-16', '2022-02-03', '2022-03-10', '2022-04-14', '2022-06-09', '2022-07-21', '2022-09-08', '2022-10-27', '2022-12-15', '2023-02-02', '2023-03-16', '2023-05-04', '2023-06-15', '2023-07-27', '2023-09-14', '2023-10-26', '2023-12-14', '2024-01-25', '2024-03-07', '2024-04-11', '2024-06-06', '2024-07-18', '2024-09-12', '2024-10-17', '2024-12-12', '2025-01-30', '2025-03-06', '2025-04-17', '2025-06-05', '2025-07-24', '2025-09-11', '2025-10-30', '2025-12-18']
RBA_DATES = ['2015-02-03', '2015-03-03', '2015-04-07', '2015-05-05', '2015-06-02', '2015-07-07', '2015-08-04', '2015-09-01', '2015-10-06', '2015-11-03', '2015-12-01', '2016-02-02', '2016-03-01', '2016-04-05', '2016-05-03', '2016-06-07', '2016-07-05', '2016-08-02', '2016-09-06', '2016-10-04', '2016-11-01', '2016-12-06', '2017-02-07', '2017-03-07', '2017-04-04', '2017-05-02', '2017-06-06', '2017-07-04', '2017-08-01', '2017-09-05', '2017-10-03', '2017-11-07', '2017-12-05', '2018-02-06', '2018-03-06', '2018-04-03', '2018-05-01', '2018-06-05', '2018-07-03', '2018-08-07', '2018-09-04', '2018-10-02', '2018-11-06', '2018-12-04', '2019-02-05', '2019-03-05', '2019-04-02', '2019-05-07', '2019-06-04', '2019-07-02', '2019-08-06', '2019-09-03', '2019-10-01', '2019-11-05', '2019-12-03', '2020-02-04', '2020-03-03', '2020-04-07', '2020-05-05', '2020-06-02', '2020-07-07', '2020-08-04', '2020-09-01', '2020-10-06', '2020-11-03', '2020-12-01', '2021-02-02', '2021-03-02', '2021-04-06', '2021-05-04', '2021-06-01', '2021-07-06', '2021-08-03', '2021-09-07', '2021-10-05', '2021-11-02', '2021-12-07', '2022-02-01', '2022-03-01', '2022-04-05', '2022-05-03', '2022-06-07', '2022-07-05', '2022-08-02', '2022-09-06', '2022-10-04', '2022-11-01', '2022-12-06', '2023-02-07', '2023-03-07', '2023-04-04', '2023-05-02', '2023-06-06', '2023-07-04', '2023-08-01', '2023-09-05', '2023-10-03', '2023-11-07', '2023-12-05', '2024-02-06', '2024-03-19', '2024-05-07', '2024-06-18', '2024-08-06', '2024-09-24', '2024-11-05', '2024-12-10', '2025-02-18', '2025-04-01', '2025-05-20', '2025-07-08', '2025-08-12', '2025-09-30', '2025-11-04', '2025-12-09']
AUD_CPI_DATES = ['2015-01-28', '2015-04-22', '2015-07-22', '2015-10-28', '2016-01-27', '2016-04-27', '2016-07-27', '2016-10-26', '2017-01-25', '2017-04-26', '2017-07-26', '2017-10-25', '2018-01-31', '2018-04-24', '2018-07-25', '2018-10-31', '2019-01-30', '2019-04-24', '2019-07-31', '2019-10-30', '2020-01-29', '2020-04-29', '2020-07-29', '2020-10-28', '2021-01-27', '2021-04-28', '2021-07-28', '2021-10-27', '2022-01-25', '2022-04-27', '2022-07-27', '2022-10-26', '2023-01-25', '2023-04-26', '2023-07-26', '2023-10-25', '2024-01-31', '2024-04-24', '2024-07-31', '2024-10-30', '2025-01-29', '2025-04-30', '2025-07-30', '2025-10-29']

# ==========================================
# 1-A. 2026年 重要イベント・経済指標カレンダー
# ==========================================

FOMC_2026_DATES = [
    '2026-01-28', '2026-03-18', '2026-04-29', '2026-06-17',
    '2026-07-29', '2026-09-16', '2026-10-28', '2026-12-09'
]

US_NFP_2026_DATES = [
    '2026-01-09', '2026-02-06', '2026-03-06', '2026-04-03',
    '2026-05-01', '2026-06-05', '2026-07-02', '2026-08-07',
    '2026-09-04', '2026-10-02', '2026-11-06', '2026-12-04'
]

US_CPI_2026_DATES = [
    '2026-01-14', '2026-02-11', '2026-03-11', '2026-04-15',
    '2026-05-13', '2026-06-10', '2026-07-15', '2026-08-12',
    '2026-09-16', '2026-10-14', '2026-11-12', '2026-12-16'
]

BOJ_2026_DATES = [
    '2026-01-23', '2026-03-19', '2026-04-28', '2026-06-16',
    '2026-07-31', '2026-09-18', '2026-10-30', '2026-12-18'
]

BOE_2026_DATES = [
    '2026-02-05', '2026-03-19', '2026-04-30', '2026-06-18',
    '2026-07-30', '2026-09-17', '2026-11-05', '2026-12-17'
]

ECB_2026_DATES = [
    '2026-02-05', '2026-03-19', '2026-04-30', '2026-06-11',
    '2026-07-23', '2026-09-10', '2026-10-29', '2026-12-17'
]

RBA_2026_DATES = [
    '2026-02-03', '2026-03-17', '2026-05-05', '2026-06-16',
    '2026-08-04', '2026-09-22', '2026-11-03', '2026-12-08'
]

AUD_CPI_2026_DATES = [
    '2026-01-28', '2026-04-29', '2026-07-29', '2026-10-28'
]

# 既存の2015〜2025年リストに2026年分を追加
US_CPI_DATES = US_CPI_DATES + US_CPI_2026_DATES
US_NFP_DATES = US_NFP_DATES + US_NFP_2026_DATES
BOJ_DATES = BOJ_DATES + BOJ_2026_DATES
FOMC_DATES = FOMC_DATES + FOMC_2026_DATES
BOE_DATES = BOE_DATES + BOE_2026_DATES
ECB_DATES = ECB_DATES + ECB_2026_DATES
RBA_DATES = RBA_DATES + RBA_2026_DATES
AUD_CPI_DATES = AUD_CPI_DATES + AUD_CPI_2026_DATES

# ==========================================
# 1-B. イベントグループ
# ==========================================

EVENTS_4 = set(US_CPI_DATES + US_NFP_DATES + FOMC_DATES + BOJ_DATES)

EVENTS_5_EJ = EVENTS_4.union(set(ECB_DATES))

EVENTS_5_GJ = EVENTS_4.union(set(BOE_DATES))

EVENTS_7_AJ = EVENTS_4.union(set(ECB_DATES + RBA_DATES + AUD_CPI_DATES))

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


def is_last_biz_day(dt):
    last_day = monthrange(dt.year, dt.month)[1]
    last_dt = pd.Timestamp(year=dt.year, month=dt.month, day=last_day)

    if last_dt.weekday() == 5:
        last_biz = last_day - 1
    elif last_dt.weekday() == 6:
        last_biz = last_day - 2
    else:
        last_biz = last_day

    return dt.day == last_biz


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

    # MT5サーバー時間をEurope/Helsinkiとして扱い、JSTへ変換
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
    uj_mode=None
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

            # UJ_Short_Core 本命仕様
            # カレンダー末日停止
            # 21日、22日停止
            # 水曜停止
            # 8月停止
            # ゴトー日は 09:55 / SL20 / TP50
            # 通常日は 08:04 / SL50 / TPなし
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

            # UJ_Fix_MidWeek
            # 毎月25日以降の水曜・木曜
            elif uj_mode == '25_onwards_wed_thu':
                if dt.day < 25:
                    continue

                if wd not in [2, 3]:
                    continue

            # UJ_Sat_3rd
            elif uj_mode == '3rd':
                if dt.day != 3:
                    continue

            # UJ_Sat_Aug
            elif uj_mode == 'aug_1_10':
                if dt.month != 8:
                    continue

                if dt.day > 10:
                    continue

            # UJ_T10A
            # 毎月10日のみ、水曜なら停止
            elif uj_mode == '10th_not_wed':
                if dt.day != 10:
                    continue

                if wd == 2:
                    continue

            else:
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

        # 決済時刻がピッタリ存在しない場合、最大4分後まで許容
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
        # 約定価格
        # spread_mode = entry_adjust
        # LongはEntry価格を上にずらす
        # ShortはEntry価格を下にずらす
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

        # ------------------------------------------
        # 時間決済
        # ------------------------------------------
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
# 4. 集計関数
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
            'end': '2026-03-31'
        },
        {
            'label': 'Legacy IS 2015-01 to 2025-12',
            'start': '2015-01-01',
            'end': '2025-12-31'
        },
        {
            'label': 'Legacy OOS 2026-01 to 2026-03',
            'start': '2026-01-01',
            'end': '2026-03-31'
        },
        {
            'label': 'Strict IS 2015-01 to 2024-12',
            'start': '2015-01-01',
            'end': '2024-12-31'
        },
        {
            'label': 'Strict OOS 2025-01 to 2026-03',
            'start': '2025-01-01',
            'end': '2026-03-31'
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


# ==========================================
# 5. 実行部
# ==========================================

print("全通貨ペアデータロード中...")

_, t_ej, o_ej, h_ej, l_ej, idx_ej, dates_ej = load_data('eurjpy_m1')
_, t_gj, o_gj, h_gj, l_gj, idx_gj, dates_gj = load_data('gbpjpy_m1')
_, t_aj, o_aj, h_aj, l_aj, idx_aj, dates_aj = load_data('audjpy_m1')
_, t_uj, o_uj, h_uj, l_uj, idx_uj, dates_uj = load_data('usdjpy_m1')

print("\nバックテスト実行中...")

# ==========================================
# EJ
# Spread 0.010
# ==========================================

run_strategy(
    'EJ',
    '1_EJ_Log1',
    t_ej,
    o_ej,
    h_ej,
    l_ej,
    idx_ej,
    dates_ej,
    True,
    0.010,
    lambda ds, dt: is_year_end(dt) or dt.month == 2 or dt.day == 1 or ds in cpi_wednesdays,
    [0, 2],
    13,
    55,
    4,
    55,
    1,
    70,
    250
)

run_strategy(
    'EJ',
    '2_EJ_NightBlitz_20',
    t_ej,
    o_ej,
    h_ej,
    l_ej,
    idx_ej,
    dates_ej,
    True,
    0.010,
    lambda ds, dt: is_year_end(dt) or ds in EVENTS_5_EJ,
    [0, 2],
    20,
    56,
    4,
    45,
    1,
    45,
    70
)

run_strategy(
    'EJ',
    '3_EJ_NightBlitz_21',
    t_ej,
    o_ej,
    h_ej,
    l_ej,
    idx_ej,
    dates_ej,
    True,
    0.010,
    lambda ds, dt: is_year_end(dt) or ds in EVENTS_5_EJ,
    [0, 2],
    21,
    56,
    5,
    27,
    1,
    75,
    70
)

# ==========================================
# GJ
# Spread 0.020
# ==========================================

run_strategy(
    'GJ',
    '4_GJ_Port_Log1',
    t_gj,
    o_gj,
    h_gj,
    l_gj,
    idx_gj,
    dates_gj,
    True,
    0.020,
    lambda ds, dt: is_year_end(dt) or dt.month == 12 or dt.day in [1, 2, 29, 30, 31],
    [1, 2],
    0,
    0,
    8,
    55,
    0,
    130,
    90
)

run_strategy(
    'GJ',
    '5_GJ_Port_Log2',
    t_gj,
    o_gj,
    h_gj,
    l_gj,
    idx_gj,
    dates_gj,
    False,
    0.020,
    lambda ds, dt: is_year_end(dt) or ds in EVENTS_5_GJ or dt.day in [18, 19, 27],
    [1, 3, 4],
    9,
    55,
    23,
    55,
    0,
    90,
    999
)

run_strategy(
    'GJ',
    '6_GJ_Old_Mon',
    t_gj,
    o_gj,
    h_gj,
    l_gj,
    idx_gj,
    dates_gj,
    True,
    0.020,
    lambda ds, dt: is_year_end(dt) or ds in EVENTS_5_GJ or dt.month in [1, 2],
    [0],
    15,
    45,
    22,
    50,
    0,
    50,
    210
)

run_strategy(
    'GJ',
    '7_GJ_Mon_Blitz',
    t_gj,
    o_gj,
    h_gj,
    l_gj,
    idx_gj,
    dates_gj,
    True,
    0.020,
    lambda ds, dt: is_year_end(dt) or ds in EVENTS_5_GJ,
    [0],
    18,
    2,
    23,
    2,
    0,
    130,
    250
)

# ==========================================
# AJ
# Spread 0.015
# ==========================================

run_strategy(
    'AJ',
    '8_AJ_Core1',
    t_aj,
    o_aj,
    h_aj,
    l_aj,
    idx_aj,
    dates_aj,
    True,
    0.015,
    lambda ds, dt: is_year_end(dt) or ds in EVENTS_7_AJ,
    [0],
    8,
    1,
    22,
    46,
    0,
    70,
    110
)

run_strategy(
    'AJ',
    '9_AJ_Core2',
    t_aj,
    o_aj,
    h_aj,
    l_aj,
    idx_aj,
    dates_aj,
    False,
    0.015,
    lambda ds, dt: is_year_end(dt) or ds in EVENTS_7_AJ or dt.month in [6, 9] or dt.day in [1, 20] or dt.day >= 26,
    [3],
    17,
    14,
    1,
    14,
    1,
    30,
    80
)

run_strategy(
    'AJ',
    '10_AJ_SatA',
    t_aj,
    o_aj,
    h_aj,
    l_aj,
    idx_aj,
    dates_aj,
    False,
    0.015,
    lambda ds, dt: is_year_end(dt) or ds in EVENTS_7_AJ,
    [4],
    10,
    58,
    13,
    51,
    0,
    50,
    25
)

run_strategy(
    'AJ',
    '11_AJ_SatB',
    t_aj,
    o_aj,
    h_aj,
    l_aj,
    idx_aj,
    dates_aj,
    False,
    0.015,
    lambda ds, dt: is_year_end(dt) or ds in EVENTS_7_AJ,
    [4],
    18,
    57,
    1,
    43,
    1,
    55,
    95
)

# ==========================================
# UJ
# Spread 0.005
# ==========================================

f_uj_4 = lambda ds, dt: is_year_end(dt) or ds in EVENTS_4

run_strategy(
    'UJ',
    '12_UJ_Short_Core',
    t_uj,
    o_uj,
    h_uj,
    l_uj,
    idx_uj,
    dates_uj,
    False,
    0.005,
    f_uj_4,
    [],
    9,
    55,
    14,
    56,
    0,
    20,
    50,
    True,
    'short_core_calendar_end'
)

run_strategy(
    'UJ',
    '13_UJ_Fix_MidWeek',
    t_uj,
    o_uj,
    h_uj,
    l_uj,
    idx_uj,
    dates_uj,
    True,
    0.005,
    f_uj_4,
    [],
    18,
    4,
    22,
    3,
    0,
    95,
    95,
    True,
    '25_onwards_wed_thu'
)

run_strategy(
    'UJ',
    '14_UJ_Sat_3rd',
    t_uj,
    o_uj,
    h_uj,
    l_uj,
    idx_uj,
    dates_uj,
    False,
    0.005,
    f_uj_4,
    [],
    20,
    1,
    3,
    8,
    1,
    45,
    70,
    True,
    '3rd'
)

run_strategy(
    'UJ',
    '15_UJ_Sat_Aug',
    t_uj,
    o_uj,
    h_uj,
    l_uj,
    idx_uj,
    dates_uj,
    False,
    0.005,
    f_uj_4,
    [],
    19,
    0,
    23,
    30,
    0,
    20,
    35,
    True,
    'aug_1_10'
)

run_strategy(
    'UJ',
    '16_UJ_T10A',
    t_uj,
    o_uj,
    h_uj,
    l_uj,
    idx_uj,
    dates_uj,
    True,
    0.005,
    lambda ds, dt: is_year_end(dt) or ds in BOJ_DATES,
    [],
    2,
    58,
    9,
    50,
    0,
    45,
    110,
    True,
    '10th_not_wed'
)

# ==========================================
# 6. 集計・保存
# ==========================================

if all_trades:
    df_res = pd.DataFrame(all_trades)
    df_res = df_res.sort_values('CloseTime').reset_index(drop=True)

    df_res['CumPips'] = df_res['Pips'].cumsum()
    df_res['MaxCumPips'] = df_res['CumPips'].cummax()
    df_res['Drawdown'] = df_res['MaxCumPips'] - df_res['CumPips']

    print("\n" + "=" * 80)
    print("🏆 Portfolio Integration Test v1.1 Engine Fix")
    print("=" * 80)

    df_period_summary = print_summary_table(df_res)
    df_strategy_summary = print_strategy_summary(df_res)
    yearly = print_yearly_summary(df_res)
    exit_summary = print_exit_reason_summary(df_res)

    output_trade_log = '/content/Portfolio_Integration_Results_v1_1_engine_fix.csv'
    output_period_summary = '/content/Portfolio_Period_Summary_v1_1_engine_fix.csv'
    output_strategy_summary = '/content/Portfolio_Strategy_Summary_v1_1_engine_fix.csv'
    output_exit_summary = '/content/Portfolio_ExitReason_Summary_v1_1_engine_fix.csv'

    df_res.to_csv(output_trade_log, index=False)
    df_period_summary.to_csv(output_period_summary, index=False)
    df_strategy_summary.to_csv(output_strategy_summary, index=False)
    exit_summary.to_csv(output_exit_summary, index=False)

    print("\n" + "=" * 80)
    print("✅ CSV保存完了")
    print("=" * 80)
    print(f"Trade Log       : {output_trade_log}")
    print(f"Period Summary  : {output_period_summary}")
    print(f"Strategy Summary: {output_strategy_summary}")
    print(f"Exit Summary    : {output_exit_summary}")

else:
    print("トレードが生成されませんでした。")
