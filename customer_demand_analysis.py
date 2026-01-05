#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
KIC ERP 데이터 분석 - 거래처 수요 예측 및 판매 주기 분석
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

# 한글 폰트 설정
plt.rcParams['font.family'] = 'NanumGothic'
plt.rcParams['axes.unicode_minus'] = False

print("=" * 80)
print("KIC ERP 데이터 분석 시작")
print("=" * 80)

# 1. 데이터 로드
print("\n[1] 데이터 로드 중...")

# 일별 판매 데이터 로드
try:
    df_daily_sales = pd.read_csv('./rawdata/00~25일별판매.csv', encoding='utf-8-sig')
    print(f"✓ 일별판매 데이터: {df_daily_sales.shape}")
except Exception as e:
    print(f"✗ 일별판매 데이터 로드 실패: {e}")
    df_daily_sales = None

# 라인별 판매현황 데이터 로드
try:
    df_line_sales = pd.read_csv('./rawdata/09~25라인별통합판매현황.csv', encoding='utf-8-sig')
    print(f"✓ 라인별 판매현황 데이터: {df_line_sales.shape}")
except Exception as e:
    print(f"✗ 라인별 판매현황 데이터 로드 실패: {e}")
    df_line_sales = None

# 거래처별 구매 데이터 로드
try:
    df_customer_purchase = pd.read_csv('./rawdata/00~25거래처별구매조회.csv', encoding='utf-8-sig')
    print(f"✓ 거래처별 구매 데이터: {df_customer_purchase.shape}")
except Exception as e:
    print(f"✗ 거래처별 구매 데이터 로드 실패: {e}")
    df_customer_purchase = None

# 2. 데이터 구조 파악
print("\n[2] 데이터 구조 파악")
print("\n--- 일별판매 데이터 ---")
if df_daily_sales is not None:
    print(f"컬럼: {list(df_daily_sales.columns)}")
    print(f"\n상위 5개 행:")
    print(df_daily_sales.head())
    print(f"\n데이터 타입:")
    print(df_daily_sales.dtypes)
    print(f"\n결측치:")
    print(df_daily_sales.isnull().sum())

print("\n--- 라인별 판매현황 데이터 ---")
if df_line_sales is not None:
    print(f"컬럼: {list(df_line_sales.columns)}")
    print(f"\n상위 5개 행:")
    print(df_line_sales.head())
    print(f"\n데이터 타입:")
    print(df_line_sales.dtypes)
    print(f"\n결측치:")
    print(df_line_sales.isnull().sum())

print("\n" + "=" * 80)
print("초기 데이터 로드 완료")
print("=" * 80)
