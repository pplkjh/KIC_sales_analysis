#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
거래처 수요 패턴 및 판매 주기 분석
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

# 한글 폰트 설정 (matplotlib에서 한글 표시)
plt.rcParams['axes.unicode_minus'] = False

print("=" * 80)
print("거래처 수요 패턴 및 판매 주기 분석")
print("=" * 80)

# 데이터 로드
df = pd.read_csv('./processed_sales_data.csv', encoding='utf-8-sig')
df['일자_dt'] = pd.to_datetime(df['일자_dt'])
df['연월'] = pd.to_datetime(df['연월'])

print(f"\n데이터: {df.shape}")

# 1. 거래처별 판매 주기 계산
print("\n[1] 거래처별 판매 주기 계산")

def calculate_customer_cycle(customer_df):
    """거래처별 판매 주기 분석"""
    # 거래일 정렬
    dates = sorted(customer_df['일자_dt'].unique())

    if len(dates) < 2:
        return {
            '거래건수': len(customer_df),
            '거래일수': len(dates),
            '평균주기(일)': np.nan,
            '중앙값주기(일)': np.nan,
            '표준편차(일)': np.nan,
            '최소주기(일)': np.nan,
            '최대주기(일)': np.nan,
            '최초거래일': dates[0] if len(dates) > 0 else None,
            '최근거래일': dates[-1] if len(dates) > 0 else None,
            '총거래기간(일)': 0,
            '평균월거래량(kg)': customer_df.groupby(customer_df['일자_dt'].dt.to_period('M'))['수량(kg)'].sum().mean(),
            '평균월매출액': customer_df.groupby(customer_df['일자_dt'].dt.to_period('M'))['공급가액'].sum().mean(),
            '주기규칙성': 'N/A'
        }

    # 거래 간격 계산 (일 단위)
    intervals = [(dates[i+1] - dates[i]).days for i in range(len(dates)-1)]

    # 총 거래기간
    total_days = (dates[-1] - dates[0]).days

    # 월별 평균 거래량/매출
    monthly_qty = customer_df.groupby(customer_df['일자_dt'].dt.to_period('M'))['수량(kg)'].sum().mean()
    monthly_sales = customer_df.groupby(customer_df['일자_dt'].dt.to_period('M'))['공급가액'].sum().mean()

    # 주기 규칙성 판단 (표준편차가 평균의 50% 이하면 '규칙적')
    std_dev = np.std(intervals)
    mean_interval = np.mean(intervals)
    regularity = '규칙적' if std_dev < mean_interval * 0.5 else '불규칙적'

    return {
        '거래건수': len(customer_df),
        '거래일수': len(dates),
        '평균주기(일)': round(mean_interval, 1),
        '중앙값주기(일)': round(np.median(intervals), 1),
        '표준편차(일)': round(std_dev, 1),
        '최소주기(일)': min(intervals),
        '최대주기(일)': max(intervals),
        '최초거래일': dates[0],
        '최근거래일': dates[-1],
        '총거래기간(일)': total_days,
        '평균월거래량(kg)': round(monthly_qty, 2),
        '평균월매출액': round(monthly_sales, 0),
        '주기규칙성': regularity
    }

# 거래처별 분석
print("거래처별 판매 주기 계산 중...")
customer_cycles = {}
for customer in df['거래처명'].unique():
    customer_df = df[df['거래처명'] == customer]
    customer_cycles[customer] = calculate_customer_cycle(customer_df)

# DataFrame으로 변환
cycle_df = pd.DataFrame(customer_cycles).T
cycle_df = cycle_df.sort_values('거래건수', ascending=False)

# 2. 주요 거래처 분석 (거래건수 100건 이상)
major_customers = cycle_df[cycle_df['거래건수'] >= 100].copy()
print(f"\n주요 거래처 수 (거래건수 100건 이상): {len(major_customers)}")

# 3. 결과 저장
cycle_df.to_csv('./customer_sales_cycle.csv', encoding='utf-8-sig')
print(f"\n전체 거래처 판매 주기 분석 저장: customer_sales_cycle.csv")

major_customers.to_csv('./major_customers_cycle.csv', encoding='utf-8-sig')
print(f"주요 거래처 판매 주기 분석 저장: major_customers_cycle.csv")

# 4. 주요 통계
print("\n" + "=" * 80)
print("주요 거래처 판매 주기 통계")
print("=" * 80)
print(f"\n상위 30개 주요 거래처:")
print(major_customers.head(30)[['거래건수', '거래일수', '평균주기(일)', '중앙값주기(일)',
                                '표준편차(일)', '주기규칙성', '평균월거래량(kg)', '평균월매출액']])

# 5. 주기별 거래처 분류
print("\n" + "=" * 80)
print("판매 주기별 거래처 분류")
print("=" * 80)

major_with_cycle = major_customers[major_customers['평균주기(일)'].notna()].copy()

# 주기별 분류
def classify_cycle(avg_cycle):
    if pd.isna(avg_cycle):
        return '분류불가'
    elif avg_cycle <= 7:
        return '주간거래 (≤7일)'
    elif avg_cycle <= 15:
        return '격주거래 (8-15일)'
    elif avg_cycle <= 30:
        return '월간거래 (16-30일)'
    elif avg_cycle <= 60:
        return '격월거래 (31-60일)'
    elif avg_cycle <= 90:
        return '분기거래 (61-90일)'
    else:
        return '장기거래 (>90일)'

major_with_cycle['주기분류'] = major_with_cycle['평균주기(일)'].apply(classify_cycle)

cycle_summary = major_with_cycle.groupby('주기분류').agg({
    '거래건수': 'count',
    '평균주기(일)': 'mean',
    '평균월거래량(kg)': 'sum',
    '평균월매출액': 'sum'
}).round(2)
cycle_summary.columns = ['거래처수', '평균주기(일)', '월거래량합계(kg)', '월매출액합계']
print(cycle_summary)

# 6. 규칙성별 분류
print("\n" + "=" * 80)
print("주기 규칙성별 거래처 분류")
print("=" * 80)

regularity_summary = major_customers.groupby('주기규칙성').agg({
    '거래건수': 'count',
    '평균주기(일)': 'mean',
    '평균월거래량(kg)': 'sum',
    '평균월매출액': 'sum'
}).round(2)
regularity_summary.columns = ['거래처수', '평균주기(일)', '월거래량합계(kg)', '월매출액합계']
print(regularity_summary)

# 7. 최근 활동 거래처 분석 (최근 6개월 이내 거래)
print("\n" + "=" * 80)
print("최근 활동 거래처 분석 (최근 6개월 이내 거래)")
print("=" * 80)

recent_date = df['일자_dt'].max()
six_months_ago = recent_date - timedelta(days=180)

recent_customers = major_customers[major_customers['최근거래일'] >= six_months_ago].copy()
print(f"\n최근 6개월 이내 거래 거래처: {len(recent_customers)}개")
print(f"\n상위 20개 최근 활동 거래처:")
print(recent_customers.head(20)[['거래건수', '평균주기(일)', '주기규칙성',
                                 '최근거래일', '평균월거래량(kg)', '평균월매출액']])

# 8. 결과 요약
print("\n" + "=" * 80)
print("분석 결과 요약")
print("=" * 80)
print(f"• 전체 거래처 수: {len(cycle_df)}개")
print(f"• 주요 거래처 수 (거래건수 ≥100): {len(major_customers)}개")
print(f"• 최근 6개월 이내 활동 거래처: {len(recent_customers)}개")
print(f"• 규칙적 거래 패턴 거래처: {len(major_customers[major_customers['주기규칙성'] == '규칙적'])}개")
print(f"• 평균 거래 주기: {major_with_cycle['평균주기(일)'].mean():.1f}일")
print(f"• 중앙값 거래 주기: {major_with_cycle['평균주기(일)'].median():.1f}일")

print("\n" + "=" * 80)
print("거래처 판매 주기 분석 완료")
print("=" * 80)
