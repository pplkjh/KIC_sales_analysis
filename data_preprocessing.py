#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
데이터 정제 및 전처리
"""

import pandas as pd
import numpy as np
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

print("=" * 80)
print("데이터 정제 및 전처리 시작")
print("=" * 80)

# 데이터 로드
df_line_sales = pd.read_csv('./rawdata/09~25라인별통합판매현황.csv', encoding='utf-8-sig')
print(f"\n원본 데이터: {df_line_sales.shape}")

# 1. 집계 행 제거 (거래처명이 NaN인 행)
df_clean = df_line_sales[df_line_sales['거래처명'].notna()].copy()
print(f"집계 행 제거 후: {df_clean.shape}")

# 2. 날짜 형식 변환 함수
def parse_date(date_str):
    """다양한 날짜 형식을 datetime으로 변환"""
    try:
        if pd.isna(date_str):
            return None
        date_str = str(date_str).strip()

        # YYYYMMDD 형식
        if len(date_str) == 8 and date_str.isdigit():
            return pd.to_datetime(date_str, format='%Y%m%d')
        # YYYY/MM/DD 형식
        elif '/' in date_str:
            return pd.to_datetime(date_str, format='%Y/%m/%d')
        # YYYY-MM-DD 형식
        elif '-' in date_str:
            return pd.to_datetime(date_str)
        else:
            return None
    except:
        return None

# 날짜 변환
df_clean['일자_dt'] = df_clean['일자'].apply(parse_date)

# 날짜 변환 실패 행 확인
failed_dates = df_clean[df_clean['일자_dt'].isna()]
print(f"\n날짜 변환 실패: {len(failed_dates)}건")
if len(failed_dates) > 0:
    print(f"실패 예시: {failed_dates['일자'].head()}")

# 날짜 변환 성공한 데이터만 사용
df_clean = df_clean[df_clean['일자_dt'].notna()].copy()
print(f"날짜 변환 후: {df_clean.shape}")

# 3. 연도, 월, 분기 추출
df_clean['연도'] = df_clean['일자_dt'].dt.year
df_clean['월'] = df_clean['일자_dt'].dt.month
df_clean['분기'] = df_clean['일자_dt'].dt.quarter
df_clean['연월'] = df_clean['일자_dt'].dt.to_period('M')
df_clean['요일'] = df_clean['일자_dt'].dt.dayofweek  # 0=월요일, 6=일요일

# 4. 데이터 기간 확인
print(f"\n데이터 기간: {df_clean['일자_dt'].min()} ~ {df_clean['일자_dt'].max()}")
print(f"총 {(df_clean['일자_dt'].max() - df_clean['일자_dt'].min()).days}일")

# 5. 거래처별 통계
print("\n[거래처별 통계]")
customer_stats = df_clean.groupby('거래처명').agg({
    '일자_dt': ['count', 'min', 'max'],
    '수량(kg)': 'sum',
    '공급가액': 'sum'
}).round(2)
customer_stats.columns = ['거래건수', '최초거래일', '최근거래일', '총수량(kg)', '총공급가액']
customer_stats = customer_stats.sort_values('거래건수', ascending=False)
print(f"\n총 거래처 수: {len(customer_stats)}")
print(f"\n상위 20개 거래처:")
print(customer_stats.head(20))

# 6. 연도별 거래 현황
print("\n[연도별 거래 현황]")
yearly_stats = df_clean.groupby('연도').agg({
    '거래처명': 'nunique',
    '일자_dt': 'count',
    '수량(kg)': 'sum',
    '공급가액': 'sum'
}).round(2)
yearly_stats.columns = ['거래처수', '거래건수', '총수량(kg)', '총공급가액']
print(yearly_stats)

# 7. 정제된 데이터 저장
df_clean.to_csv('./processed_sales_data.csv', index=False, encoding='utf-8-sig')
print(f"\n정제된 데이터 저장 완료: processed_sales_data.csv ({df_clean.shape})")

# 8. 주요 거래처 리스트 저장
top_customers = customer_stats.head(50)
top_customers.to_csv('./top_50_customers.csv', encoding='utf-8-sig')
print(f"상위 50개 거래처 리스트 저장: top_50_customers.csv")

print("\n" + "=" * 80)
print("데이터 정제 완료")
print("=" * 80)
