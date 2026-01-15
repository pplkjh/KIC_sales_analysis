#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
2026년 주문 예측 - 개연성 있는 예측 (최근 활성 거래처 기반)
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

print("=" * 80)
print("2026년 주문 예측 시스템 (개연성 기반)")
print("=" * 80)

# 데이터 로드
df = pd.read_csv('./processed_sales_data.csv', encoding='utf-8-sig')
df['일자_dt'] = pd.to_datetime(df['일자_dt'])

print(f"\n전체 거래 데이터: {len(df)}건")
print(f"데이터 기간: {df['일자_dt'].min().date()} ~ {df['일자_dt'].max().date()}")

# 1. 최근 활성 거래처 필터링 (2024년 이후 거래가 있는 곳만)
print("\n[1] 최근 활성 거래처 필터링")

cutoff_date = datetime(2024, 1, 1)
recent_df = df[df['일자_dt'] >= cutoff_date].copy()

active_customers = recent_df['거래처명'].unique()
print(f"2024년 이후 활성 거래처: {len(active_customers)}개")

# 2. 거래처별로 거래일 기준 주기 계산 (같은 날 = 1번 주문)
print("\n[2] 거래처별 주문 주기 분석")

def analyze_customer_pattern(customer_name, df_all, recent_df):
    """거래처별 주문 패턴 분석 - 거래일 기준"""

    customer_all = df_all[df_all['거래처명'] == customer_name].copy()
    customer_recent = recent_df[recent_df['거래처명'] == customer_name].copy()

    # 거래일 기준으로 그룹화 (같은 날 = 1번 주문)
    order_dates = sorted(customer_recent.groupby('일자_dt').size().index)

    if len(order_dates) < 3:  # 최소 3번 이상 주문한 곳만
        return None

    # 주기 계산
    intervals = [(order_dates[i+1] - order_dates[i]).days for i in range(len(order_dates)-1)]
    avg_cycle = np.mean(intervals)

    # 주기가 너무 길면 제외 (180일 이상 = 반년 이상)
    if avg_cycle > 180:
        return None

    # 최근 거래일
    last_order_date = order_dates[-1]

    # 품목별 분석 (최근 거래 기준)
    items_analysis = []

    for item in customer_recent['품  목'].unique():
        item_df = customer_recent[customer_recent['품  목'] == item]

        # 품목별 거래일
        item_order_dates = sorted(item_df.groupby('일자_dt').size().index)

        if len(item_order_dates) < 2:  # 최소 2번 이상 주문
            continue

        # 품목별 평균 수량 및 금액 (거래일별로 합산 후 평균)
        daily_item = item_df.groupby('일자_dt').agg({
            '수량(kg)': 'sum',
            '공급가액': 'sum'
        })

        avg_qty = daily_item['수량(kg)'].mean()
        avg_amount = daily_item['공급가액'].mean()

        # 과거 주문 이력 (최근 5회)
        past_orders = []
        for order_date in item_order_dates[-5:]:
            date_item = item_df[item_df['일자_dt'] == order_date]
            total_qty = date_item['수량(kg)'].sum()
            total_amount = date_item['공급가액'].sum()
            past_orders.append({
                '주문일': order_date,
                '수량': total_qty,
                '금액': total_amount
            })

        items_analysis.append({
            '품목': item,
            '거래횟수': len(item_order_dates),
            '평균수량(kg)': round(avg_qty, 2),
            '평균금액': round(avg_amount, 0),
            '최근주문일': item_order_dates[-1],
            '과거주문이력': past_orders
        })

    return {
        '거래처명': customer_name,
        '최근거래일': last_order_date,
        '총주문횟수': len(order_dates),
        '평균주기(일)': round(avg_cycle, 1),
        '주기표준편차': round(np.std(intervals), 1),
        '품목분석': sorted(items_analysis, key=lambda x: x['거래횟수'], reverse=True)
    }

# 활성 거래처 분석
customer_patterns = {}
for customer in active_customers:
    pattern = analyze_customer_pattern(customer, df, recent_df)
    if pattern and len(pattern['품목분석']) > 0:
        customer_patterns[customer] = pattern

print(f"예측 대상 거래처: {len(customer_patterns)}개")

# 3. 2026년 예측 생성
print("\n[3] 2026년 주문 예측 생성")

year_2026_start = datetime(2026, 1, 1)
year_2026_end = datetime(2026, 12, 31)

all_predictions = []

for customer, pattern in customer_patterns.items():
    last_order = pattern['최근거래일']
    avg_cycle = pattern['평균주기(일)']

    # 다음 예상 주문일 계산
    next_order_date = last_order + timedelta(days=int(avg_cycle))

    # 2026년 내 모든 예상 주문일
    while next_order_date <= year_2026_end:
        if next_order_date >= year_2026_start:
            # 이 날짜에 예상되는 품목들
            for item_info in pattern['품목분석']:
                # 과거 주문 이력 문자열로 변환
                past_orders_str = '; '.join([
                    f"{po['주문일'].strftime('%Y-%m-%d')} ({po['수량']:.0f}kg, {po['금액']:,.0f}원)"
                    for po in item_info['과거주문이력']
                ])

                all_predictions.append({
                    '예상주문일': next_order_date,
                    '거래처명': customer,
                    '최근거래일': last_order,
                    '평균주기(일)': avg_cycle,
                    '총주문횟수': pattern['총주문횟수'],
                    '품목': item_info['품목'],
                    '품목거래횟수': item_info['거래횟수'],
                    '예상수량(kg)': item_info['평균수량(kg)'],
                    '예상금액': item_info['평균금액'],
                    '과거주문이력': past_orders_str
                })

        next_order_date = next_order_date + timedelta(days=int(avg_cycle))

# DataFrame 생성
pred_df = pd.DataFrame(all_predictions)
pred_df = pred_df.sort_values(['예상주문일', '거래처명', '품목'])

print(f"총 예측 건수: {len(pred_df)}건 (품목 단위)")

# 4. 결과 저장
print("\n[4] 결과 저장")

# 상세 예측 저장
pred_df.to_csv('./2026_order_predictions_detailed.csv', index=False, encoding='utf-8-sig')
print(f"상세 예측 저장: 2026_order_predictions_detailed.csv ({len(pred_df)}건)")

# 거래처별 요약 (날짜별)
summary_df = pred_df.groupby(['예상주문일', '거래처명']).agg({
    '최근거래일': 'first',
    '평균주기(일)': 'first',
    '총주문횟수': 'first',
    '품목': lambda x: ', '.join(x.astype(str)[:3]) + (f' 외 {len(x)-3}개' if len(x) > 3 else ''),
    '예상수량(kg)': 'sum',
    '예상금액': 'sum'
}).reset_index()

summary_df.to_csv('./2026_order_predictions_summary.csv', index=False, encoding='utf-8-sig')
print(f"거래처별 요약 저장: 2026_order_predictions_summary.csv ({len(summary_df)}건)")

# 월별 통계
monthly_stats = pred_df.copy()
monthly_stats['월'] = monthly_stats['예상주문일'].dt.month
monthly_summary = monthly_stats.groupby('월').agg({
    '거래처명': 'nunique',
    '예상주문일': lambda x: x.dt.date.nunique(),
    '예상수량(kg)': 'sum',
    '예상금액': 'sum'
}).round(0)
monthly_summary.columns = ['거래처수', '예상주문일수', '예상총수량(kg)', '예상총금액']
monthly_summary.to_csv('./2026_monthly_summary.csv', encoding='utf-8-sig')
print(f"월별 요약 저장: 2026_monthly_summary.csv")

# 5. 통계 출력
print("\n" + "=" * 80)
print("2026년 예측 통계")
print("=" * 80)

total_amount = pred_df['예상금액'].sum()
total_qty = pred_df['예상수량(kg)'].sum()
total_customers = pred_df['거래처명'].nunique()
total_orders = summary_df.shape[0]

print(f"\n📊 전체 통계")
print(f"  - 예측 대상 거래처: {total_customers}개 (2024년 이후 활성)")
print(f"  - 예상 주문 건수: {total_orders}건")
print(f"  - 예상 품목 건수: {len(pred_df)}건")
print(f"  - 예상 총 매출액: {total_amount:,.0f}원 ({total_amount/100000000:.1f}억원)")
print(f"  - 예상 총 출하량: {total_qty:,.0f}kg ({total_qty/1000:.1f}톤)")

print(f"\n📅 월별 요약")
print(monthly_summary)

# 6. 1월 미리보기
print("\n" + "=" * 80)
print("2026년 1월 예상 주문 미리보기 (상위 30건)")
print("=" * 80)

jan_orders = summary_df[summary_df['예상주문일'].dt.month == 1].head(30)
print(jan_orders[['예상주문일', '거래처명', '최근거래일', '평균주기(일)', '품목', '예상수량(kg)', '예상금액']].to_string(index=False))

# 7. 품목별 예측 예시
print("\n" + "=" * 80)
print("품목별 예측 예시 (과거 이력 포함)")
print("=" * 80)

sample = pred_df.head(5)
for idx, row in sample.iterrows():
    print(f"\n{row['예상주문일'].strftime('%Y-%m-%d')} - {row['거래처명']}")
    print(f"  품목: {row['품목']}")
    print(f"  예상수량: {row['예상수량(kg)']}kg")
    print(f"  예상금액: {row['예상금액']:,.0f}원")
    print(f"  과거이력: {row['과거주문이력'][:150]}...")

print("\n" + "=" * 80)
print("예측 완료!")
print("=" * 80)
print("\n생성된 파일:")
print("1. 2026_order_predictions_detailed.csv - 품목별 상세 예측 + 과거 주문 이력")
print("2. 2026_order_predictions_summary.csv - 거래처별 날짜별 요약")
print("3. 2026_monthly_summary.csv - 월별 통계")
