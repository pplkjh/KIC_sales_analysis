#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
2026년 생산 계획 수준 수요 예측 시스템
- 거래처×품목 조합별 안정성 분류
- 주문 규칙성 점수 및 예측 신뢰도 산출
- 일별 출하 스케줄 생성
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from scipy import stats
import warnings
warnings.filterwarnings('ignore')

print("=" * 80)
print("2026년 생산 계획 수준 수요 예측 시스템")
print("=" * 80)

# ========================================
# 1. 데이터 로딩 및 정제
# ========================================
print("\n[1단계] 데이터 로딩 및 정제")

df = pd.read_csv('./processed_sales_data.csv', encoding='utf-8-sig')
df['일자_dt'] = pd.to_datetime(df['일자_dt'])

print(f"전체 거래 데이터: {len(df):,}건")
print(f"기간: {df['일자_dt'].min().date()} ~ {df['일자_dt'].max().date()}")
print(f"거래처 수: {df['거래처명'].nunique():,}개")
print(f"품목 수: {df['품  목'].nunique():,}개")

# 최근 2년 데이터 중심 분석 (2024-2026)
recent_cutoff = datetime(2024, 1, 1)
df_recent = df[df['일자_dt'] >= recent_cutoff].copy()

print(f"\n2024년 이후 데이터: {len(df_recent):,}건")

# ========================================
# 2. 거래처×품목 조합별 안정성 분석
# ========================================
print("\n[2단계] 거래처×품목 조합별 안정성 분석")

def analyze_customer_product_stability(group_df):
    """거래처×품목 조합의 안정성 분석"""

    # 거래일 기준 그룹화 (같은 날 = 1번 주문)
    daily_orders = group_df.groupby('일자_dt').agg({
        '수량(kg)': 'sum',
        '공급가액': 'sum'
    }).reset_index()

    order_dates = sorted(daily_orders['일자_dt'].tolist())
    n_orders = len(order_dates)

    if n_orders < 2:
        return None

    # 주문 간격 계산
    intervals = [(order_dates[i+1] - order_dates[i]).days for i in range(n_orders-1)]

    # 기본 통계
    avg_interval = np.mean(intervals)
    std_interval = np.std(intervals)
    cv_interval = std_interval / avg_interval if avg_interval > 0 else 999

    # 최근성
    last_order_date = order_dates[-1]
    days_since_last = (datetime.now() - last_order_date).days

    # 수량 안정성
    quantities = daily_orders['수량(kg)'].values
    avg_qty = np.mean(quantities)
    std_qty = np.std(quantities)
    cv_qty = std_qty / avg_qty if avg_qty > 0 else 999

    # 주문 규칙성 점수 (0-100)
    # - 낮은 CV = 높은 점수
    # - 많은 주문횟수 = 높은 점수
    # - 최근 주문 = 높은 점수

    interval_score = max(0, 100 - cv_interval * 100)  # CV가 낮을수록 높은 점수
    frequency_score = min(100, n_orders * 10)  # 10회 이상이면 100점
    recency_score = max(0, 100 - days_since_last / 3.65)  # 1년 이내면 높은 점수

    regularity_score = (interval_score * 0.5 +
                       frequency_score * 0.3 +
                       recency_score * 0.2)

    # 거래 유형 분류
    if regularity_score >= 70 and n_orders >= 6 and days_since_last <= 90:
        transaction_type = '안정'
    elif regularity_score >= 50 and n_orders >= 3 and days_since_last <= 180:
        transaction_type = '불규칙'
    elif days_since_last > 180:
        transaction_type = '휴면'
    else:
        transaction_type = '일회성'

    return {
        '주문횟수': n_orders,
        '평균주기(일)': round(avg_interval, 1),
        '주기표준편차': round(std_interval, 1),
        '주기CV': round(cv_interval, 2),
        '평균수량(kg)': round(avg_qty, 2),
        '수량표준편차': round(std_qty, 2),
        '수량CV': round(cv_qty, 2),
        '최근주문일': last_order_date,
        '경과일수': days_since_last,
        '주문규칙성점수': round(regularity_score, 1),
        '거래유형': transaction_type,
        '주문일자리스트': order_dates
    }

# 거래처×품목 조합별 분석
print("거래처×품목 조합 분석 중...")
customer_product_analysis = {}

for (customer, product), group in df_recent.groupby(['거래처명', '품  목']):
    analysis = analyze_customer_product_stability(group)
    if analysis:
        customer_product_analysis[(customer, product)] = analysis

print(f"분석 완료: {len(customer_product_analysis):,}개 조합")

# 거래 유형별 통계
type_counts = {}
for analysis in customer_product_analysis.values():
    t = analysis['거래유형']
    type_counts[t] = type_counts.get(t, 0) + 1

print("\n거래 유형별 분포:")
for t, count in sorted(type_counts.items()):
    print(f"  {t}: {count:,}개")

# ========================================
# 3. 예측 대상 선정 (안정 + 불규칙)
# ========================================
print("\n[3단계] 예측 대상 선정")

forecast_targets = {
    key: val for key, val in customer_product_analysis.items()
    if val['거래유형'] in ['안정', '불규칙'] and val['주문규칙성점수'] >= 40
}

print(f"예측 대상: {len(forecast_targets):,}개 조합")
print(f"  - 안정: {sum(1 for v in forecast_targets.values() if v['거래유형'] == '안정'):,}개")
print(f"  - 불규칙: {sum(1 for v in forecast_targets.values() if v['거래유형'] == '불규칙'):,}개")

# ========================================
# 4. 2026년 예측 생성
# ========================================
print("\n[4단계] 2026년 예측 생성")

def generate_2026_forecast(customer, product, analysis_data):
    """2026년 예측 생성"""

    avg_interval = analysis_data['평균주기(일)']
    last_order = analysis_data['최근주문일']
    avg_qty = analysis_data['평균수량(kg)']
    std_qty = analysis_data['수량표준편차']

    # 계절성 분석 (월별 패턴)
    order_dates = analysis_data['주문일자리스트']
    monthly_pattern = {}
    for date in order_dates:
        month = date.month
        monthly_pattern[month] = monthly_pattern.get(month, 0) + 1

    # 월별 가중치 계산
    total_orders = sum(monthly_pattern.values())
    monthly_weight = {m: monthly_pattern.get(m, 0) / total_orders
                     for m in range(1, 13)}

    # 2026년 예측
    predictions = []

    # 첫 예측일 = 최근 주문일 + 평균 주기
    next_date = last_order + timedelta(days=int(avg_interval))

    year_2026_start = datetime(2026, 1, 1)
    year_2026_end = datetime(2026, 12, 31)

    while next_date <= year_2026_end:
        if next_date >= year_2026_start:
            # 계절성 반영된 수량 예측
            month_weight = monthly_weight.get(next_date.month, 1.0)
            seasonal_factor = month_weight / (1.0 / 12)  # 평균 대비 비율

            predicted_qty = avg_qty * seasonal_factor

            # 수량 변동성 고려 (± 10%)
            qty_variation = np.random.normal(0, std_qty * 0.1)
            final_qty = max(0, predicted_qty + qty_variation)

            # 예측 신뢰도 계산
            confidence = analysis_data['주문규칙성점수']

            # 최근성 보정
            days_from_last = (next_date - last_order).days
            if days_from_last > 180:
                confidence *= 0.8
            elif days_from_last > 90:
                confidence *= 0.9

            predictions.append({
                '날짜': next_date,
                '거래처': customer,
                '품목': product,
                '수량': round(final_qty, 2),
                '예측신뢰도': round(confidence, 1),
                '거래유형': analysis_data['거래유형'],
                '최근거래일': last_order,
                '평균주기(일)': avg_interval
            })

        next_date = next_date + timedelta(days=int(avg_interval))

    return predictions

# 모든 예측 생성
all_predictions = []

for (customer, product), analysis in forecast_targets.items():
    predictions = generate_2026_forecast(customer, product, analysis)
    all_predictions.extend(predictions)

print(f"총 예측 건수: {len(all_predictions):,}건")

# ========================================
# 5. 최종 출력 생성
# ========================================
print("\n[5단계] 최종 출력 생성")

# DataFrame 생성
forecast_df = pd.DataFrame(all_predictions)
forecast_df = forecast_df.sort_values('날짜').reset_index(drop=True)

# 통계
print(f"\n=== 2026년 예측 통계 ===")
print(f"예측 건수: {len(forecast_df):,}건")
print(f"거래처 수: {forecast_df['거래처'].nunique():,}개")
print(f"품목 수: {forecast_df['품목'].nunique():,}개")
print(f"예상 총 수량: {forecast_df['수량'].sum():,.0f}kg")

# 신뢰도별 분포
print(f"\n예측 신뢰도 분포:")
print(f"  고신뢰 (80-100점): {len(forecast_df[forecast_df['예측신뢰도'] >= 80]):,}건")
print(f"  중신뢰 (60-79점): {len(forecast_df[(forecast_df['예측신뢰도'] >= 60) & (forecast_df['예측신뢰도'] < 80)]):,}건")
print(f"  저신뢰 (<60점): {len(forecast_df[forecast_df['예측신뢰도'] < 60]):,}건")

# 월별 통계
monthly_stats = forecast_df.groupby(forecast_df['날짜'].dt.month).agg({
    '거래처': 'nunique',
    '수량': 'sum',
    '예측신뢰도': 'mean'
}).round(1)
monthly_stats.columns = ['거래처수', '예상수량(kg)', '평균신뢰도']
print(f"\n월별 예측:")
print(monthly_stats)

# 파일 저장
forecast_df.to_csv('./2026_생산계획_예측.csv', index=False, encoding='utf-8-sig')
print(f"\n✅ 저장 완료: 2026_생산계획_예측.csv")

# 고신뢰도 예측만 별도 저장
high_confidence = forecast_df[forecast_df['예측신뢰도'] >= 70].copy()
high_confidence.to_csv('./2026_고신뢰도_예측.csv', index=False, encoding='utf-8-sig')
print(f"✅ 저장 완료: 2026_고신뢰도_예측.csv ({len(high_confidence):,}건)")

# 거래처×품목 분석 결과 저장
analysis_df = pd.DataFrame([
    {
        '거래처': k[0],
        '품목': k[1],
        '주문횟수': v['주문횟수'],
        '평균주기(일)': v['평균주기(일)'],
        '주기표준편차': v['주기표준편차'],
        '평균수량(kg)': v['평균수량(kg)'],
        '최근주문일': v['최근주문일'],
        '경과일수': v['경과일수'],
        '주문규칙성점수': v['주문규칙성점수'],
        '거래유형': v['거래유형']
    }
    for k, v in customer_product_analysis.items()
])
analysis_df = analysis_df.sort_values('주문규칙성점수', ascending=False)
analysis_df.to_csv('./거래처품목_안정성분석.csv', index=False, encoding='utf-8-sig')
print(f"✅ 저장 완료: 거래처품목_안정성분석.csv")

# 1월 미리보기
print(f"\n=== 2026년 1월 예측 미리보기 (상위 20건) ===")
jan_forecast = forecast_df[forecast_df['날짜'].dt.month == 1].head(20)
print(jan_forecast[['날짜', '거래처', '품목', '수량', '예측신뢰도', '거래유형']].to_string(index=False))

print("\n" + "=" * 80)
print("✅ 2026년 생산 계획 수준 예측 완료!")
print("=" * 80)
print("\n생성 파일:")
print("1. 2026_생산계획_예측.csv - 전체 예측 (한글 컬럼명)")
print("2. 2026_고신뢰도_예측.csv - 신뢰도 70점 이상")
print("3. 거래처품목_안정성분석.csv - 안정성 분석 결과")
