#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
2026년 전체 주문 예측 - 날짜별, 거래처별, 품목별 상세 예측
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

print("=" * 80)
print("2026년 전체 주문 예측 시스템")
print("=" * 80)

# 데이터 로드
df = pd.read_csv('./processed_sales_data.csv', encoding='utf-8-sig')
df['일자_dt'] = pd.to_datetime(df['일자_dt'])

cycle_df = pd.read_csv('./major_customers_cycle.csv', encoding='utf-8-sig', index_col=0)

print(f"\n데이터 로드 완료")
print(f"전체 거래: {len(df)}건")
print(f"분석 대상 주요 거래처: {len(cycle_df)}개")

# 2026년 시작일과 종료일
year_2026_start = datetime(2026, 1, 1)
year_2026_end = datetime(2026, 12, 31)

print(f"\n예측 기간: {year_2026_start.date()} ~ {year_2026_end.date()}")

# 1. 거래처별 2026년 전체 예상 주문 계산
print("\n[1] 거래처별 2026년 전체 예상 주문 계산 중...")

def predict_all_orders_2026(customer_name, df, cycle_info):
    """거래처의 2026년 전체 예상 주문 계산"""

    customer_df = df[df['거래처명'] == customer_name].copy()

    if len(customer_df) == 0:
        return []

    # 최근 거래일
    last_order_date = customer_df['일자_dt'].max()

    # 평균 주기 (일)
    avg_cycle = cycle_info.get('평균주기(일)', np.nan)

    if pd.isna(avg_cycle) or avg_cycle <= 0:
        return []

    # 최근 3개월 거래 분석하여 품목 정보 추출
    three_months_ago = datetime.now() - timedelta(days=90)
    recent_df = customer_df[customer_df['일자_dt'] >= three_months_ago]

    # 품목별 평균 수량 및 금액
    if len(recent_df) > 0:
        item_stats = recent_df.groupby('품  목').agg({
            '수량(kg)': ['mean', 'count'],
            '공급가액': 'mean'
        }).round(2)
        item_stats.columns = ['평균수량', '거래횟수', '평균금액']
        item_stats = item_stats.sort_values('거래횟수', ascending=False)
    else:
        # 최근 3개월 데이터가 없으면 전체 데이터 사용
        item_stats = customer_df.groupby('품  목').agg({
            '수량(kg)': ['mean', 'count'],
            '공급가액': 'mean'
        }).round(2)
        item_stats.columns = ['평균수량', '거래횟수', '평균금액']
        item_stats = item_stats.sort_values('거래횟수', ascending=False)

    # 2026년 전체 예상 주문일 계산
    predicted_orders = []

    # 첫 번째 예상일 = 최근 거래일 + 평균 주기
    next_order_date = last_order_date + timedelta(days=int(avg_cycle))

    # 2026년 내의 모든 예상 주문일 계산
    while next_order_date <= year_2026_end:
        if next_order_date >= year_2026_start:
            # 해당 날짜의 예상 주문 정보
            for item, row in item_stats.iterrows():
                predicted_orders.append({
                    '예상주문일': next_order_date,
                    '거래처명': customer_name,
                    '최근거래일': last_order_date,
                    '평균주기(일)': avg_cycle,
                    '품목': item,
                    '예상수량(kg)': row['평균수량'],
                    '예상금액': row['평균금액'],
                    '품목거래빈도': row['거래횟수']
                })

        # 다음 주문일 = 현재 예상일 + 평균 주기
        next_order_date = next_order_date + timedelta(days=int(avg_cycle))

    return predicted_orders

# 모든 주요 거래처에 대해 2026년 예측
all_predictions = []
customer_count = 0

for customer in cycle_df.index:
    predictions = predict_all_orders_2026(customer, df, cycle_df.loc[customer])
    if predictions:
        all_predictions.extend(predictions)
        customer_count += 1

print(f"예측 완료: {customer_count}개 거래처")
print(f"총 예상 주문 건수 (품목 단위): {len(all_predictions)}건")

# DataFrame으로 변환
pred_2026_df = pd.DataFrame(all_predictions)

if len(pred_2026_df) > 0:
    # 날짜순 정렬
    pred_2026_df = pred_2026_df.sort_values(['예상주문일', '거래처명', '품목'])

    # 날짜 형식 추가
    pred_2026_df['연'] = pred_2026_df['예상주문일'].dt.year
    pred_2026_df['월'] = pred_2026_df['예상주문일'].dt.month
    pred_2026_df['일'] = pred_2026_df['예상주문일'].dt.day
    pred_2026_df['요일'] = pred_2026_df['예상주문일'].dt.day_name()

    # 요일을 한글로 변환
    weekday_map = {
        'Monday': '월요일',
        'Tuesday': '화요일',
        'Wednesday': '수요일',
        'Thursday': '목요일',
        'Friday': '금요일',
        'Saturday': '토요일',
        'Sunday': '일요일'
    }
    pred_2026_df['요일'] = pred_2026_df['요일'].map(weekday_map)

    # 2. 결과 저장
    print("\n[2] 결과 저장")

    # 날짜별 품목별 상세 예측
    output_df = pred_2026_df[['예상주문일', '연', '월', '일', '요일', '거래처명', '최근거래일', '평균주기(일)',
                               '품목', '예상수량(kg)', '예상금액', '품목거래빈도']].copy()
    output_df.to_csv('./2026_order_predictions_detailed.csv', index=False, encoding='utf-8-sig')
    print(f"2026년 전체 상세 예측 저장: 2026_order_predictions_detailed.csv")
    print(f"  - 총 {len(output_df)}건의 품목별 예상 주문")
    print(f"  - 최근거래일, 평균주기(일) 정보 포함")

    # 날짜별 거래처별 요약 (같은 날짜, 같은 거래처의 품목들을 그룹화)
    date_customer_summary = pred_2026_df.groupby(['예상주문일', '거래처명']).agg({
        '최근거래일': 'first',
        '평균주기(일)': 'first',
        '품목': lambda x: ', '.join(x.astype(str).head(3).tolist()) + (f' 외 {len(x)-3}개' if len(x) > 3 else ''),
        '예상수량(kg)': 'sum',
        '예상금액': 'sum'
    }).round(0).reset_index()

    date_customer_summary['연'] = date_customer_summary['예상주문일'].dt.year
    date_customer_summary['월'] = date_customer_summary['예상주문일'].dt.month
    date_customer_summary['일'] = date_customer_summary['예상주문일'].dt.day
    date_customer_summary = date_customer_summary[['예상주문일', '연', '월', '일', '거래처명', '최근거래일', '평균주기(일)',
                                                     '품목', '예상수량(kg)', '예상금액']]

    date_customer_summary.to_csv('./2026_order_predictions_by_customer.csv', index=False, encoding='utf-8-sig')
    print(f"거래처별 요약 저장: 2026_order_predictions_by_customer.csv")
    print(f"  - 총 {len(date_customer_summary)}건의 예상 주문")
    print(f"  - 최근거래일, 평균주기(일) 정보 포함")

    # 월별 요약
    monthly_summary = pred_2026_df.groupby('월').agg({
        '거래처명': 'nunique',
        '품목': 'count',
        '예상수량(kg)': 'sum',
        '예상금액': 'sum'
    }).round(0)
    monthly_summary.columns = ['예상거래처수', '예상주문건수(품목)', '예상총수량(kg)', '예상총금액']
    monthly_summary.to_csv('./2026_monthly_summary.csv', encoding='utf-8-sig')
    print(f"월별 요약 저장: 2026_monthly_summary.csv")

    # 3. 통계 출력
    print("\n" + "=" * 80)
    print("2026년 예측 통계")
    print("=" * 80)

    total_orders = len(date_customer_summary)
    total_items = len(pred_2026_df)
    total_customers = pred_2026_df['거래처명'].nunique()
    total_amount = pred_2026_df['예상금액'].sum()
    total_qty = pred_2026_df['예상수량(kg)'].sum()

    print(f"\n📊 전체 통계")
    print(f"  - 예상 거래처 수: {total_customers}개")
    print(f"  - 예상 주문 건수: {total_orders}건")
    print(f"  - 예상 품목 건수: {total_items}건")
    print(f"  - 예상 총 매출액: {total_amount:,.0f}원 ({total_amount/100000000:.1f}억원)")
    print(f"  - 예상 총 출하량: {total_qty:,.0f}kg ({total_qty/1000:.1f}톤)")

    print(f"\n📅 월별 요약")
    print(monthly_summary)

    # 4. 상위 예상 주문 미리보기
    print("\n" + "=" * 80)
    print("2026년 1월~3월 예상 주문 미리보기 (상위 50건)")
    print("=" * 80)

    q1_orders = date_customer_summary[date_customer_summary['월'] <= 3].head(50)
    print(q1_orders.to_string(index=False))

    # 5. 거래처별 예상 주문 횟수
    print("\n" + "=" * 80)
    print("거래처별 2026년 예상 주문 횟수 (상위 30개)")
    print("=" * 80)

    customer_order_count = date_customer_summary.groupby('거래처명').agg({
        '예상주문일': 'count',
        '예상금액': 'sum'
    }).round(0)
    customer_order_count.columns = ['예상주문횟수', '예상총매출액']
    customer_order_count = customer_order_count.sort_values('예상주문횟수', ascending=False)
    print(customer_order_count.head(30))

    customer_order_count.to_csv('./2026_customer_order_frequency.csv', encoding='utf-8-sig')
    print(f"\n거래처별 주문 빈도 저장: 2026_customer_order_frequency.csv")

    print("\n" + "=" * 80)
    print("2026년 전체 예측 완료!")
    print("=" * 80)
    print("\n생성된 파일:")
    print("1. 2026_order_predictions_detailed.csv - 품목별 상세 예측 (날짜순)")
    print("2. 2026_order_predictions_by_customer.csv - 거래처별 요약")
    print("3. 2026_monthly_summary.csv - 월별 요약")
    print("4. 2026_customer_order_frequency.csv - 거래처별 주문 빈도")

else:
    print("\n예측 결과가 없습니다.")
