#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
거래처별 주문 예측 및 캘린더 맵핑 시스템
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
from datetime import datetime, timedelta
import calendar
import warnings
warnings.filterwarnings('ignore')

# 한글 폰트 설정
font_path = '/usr/share/fonts/truetype/nanum/NanumGothic.ttf'
font_prop = fm.FontProperties(fname=font_path)
plt.rcParams['font.family'] = font_prop.get_name()
plt.rcParams['font.sans-serif'] = ['NanumGothic']
plt.rcParams['axes.unicode_minus'] = False
fm._load_fontmanager(try_read_cache=False)

print("=" * 80)
print("거래처별 주문 예측 및 캘린더 맵핑 시스템")
print("=" * 80)

# 데이터 로드
df = pd.read_csv('./processed_sales_data.csv', encoding='utf-8-sig')
df['일자_dt'] = pd.to_datetime(df['일자_dt'])

cycle_df = pd.read_csv('./major_customers_cycle.csv', encoding='utf-8-sig', index_col=0)

print(f"\n데이터 로드 완료")
print(f"전체 거래: {len(df)}건")
print(f"분석 대상 주요 거래처: {len(cycle_df)}개")

# 1. 거래처별 예상 주문일 계산
print("\n[1] 거래처별 다음 주문 예상일 계산")

def predict_next_order(customer_name, df, cycle_info):
    """거래처별 다음 주문 예상일 및 품목/수량/금액 예측"""

    customer_df = df[df['거래처명'] == customer_name].copy()

    if len(customer_df) == 0:
        return None

    # 최근 거래일
    last_order_date = customer_df['일자_dt'].max()

    # 평균 주기 (일)
    avg_cycle = cycle_info.get('평균주기(일)', np.nan)

    if pd.isna(avg_cycle):
        return None

    # 다음 주문 예상일 = 최근 거래일 + 평균 주기
    next_order_date = last_order_date + timedelta(days=int(avg_cycle))

    # 최근 3개월 거래 분석하여 품목/수량/금액 예측
    three_months_ago = datetime.now() - timedelta(days=90)
    recent_df = customer_df[customer_df['일자_dt'] >= three_months_ago]

    # 품목별 평균 수량 및 금액
    if len(recent_df) > 0:
        item_stats = recent_df.groupby('품  목').agg({
            '수량(kg)': ['mean', 'sum', 'count'],
            '공급가액': ['mean', 'sum']
        }).round(2)

        # 가장 많이 주문한 품목 (거래 빈도 기준)
        item_stats.columns = ['평균수량', '총수량', '거래횟수', '평균금액', '총금액']
        top_items = item_stats.sort_values('거래횟수', ascending=False).head(5)
    else:
        top_items = None

    # 평균 주문 금액
    avg_order_amount = customer_df.groupby('일자_dt')['공급가액'].sum().mean()

    # 평균 주문 수량
    avg_order_qty = customer_df.groupby('일자_dt')['수량(kg)'].sum().mean()

    return {
        '거래처명': customer_name,
        '최근주문일': last_order_date,
        '평균주기(일)': avg_cycle,
        '다음주문예상일': next_order_date,
        '예상금액': round(avg_order_amount, 0),
        '예상수량(kg)': round(avg_order_qty, 2),
        '주요품목': top_items,
        '총거래횟수': len(customer_df)
    }

# 모든 주요 거래처에 대해 예측
predictions = []
for customer in cycle_df.index:
    pred = predict_next_order(customer, df, cycle_df.loc[customer])
    if pred:
        predictions.append(pred)

# DataFrame으로 변환
pred_df = pd.DataFrame([{
    '거래처명': p['거래처명'],
    '최근주문일': p['최근주문일'],
    '평균주기(일)': p['평균주기(일)'],
    '다음주문예상일': p['다음주문예상일'],
    '예상금액': p['예상금액'],
    '예상수량(kg)': p['예상수량(kg)'],
    '총거래횟수': p['총거래횟수']
} for p in predictions])

# 날짜순 정렬
pred_df = pred_df.sort_values('다음주문예상일')

print(f"\n예측 완료: {len(pred_df)}개 거래처")

# 2. 향후 3개월 예상 주문 캘린더
print("\n[2] 향후 3개월 예상 주문 캘린더 생성")

# 오늘부터 90일간의 예측
today = datetime.now()
end_date = today + timedelta(days=90)

# 해당 기간 내 예상 주문만 필터링
calendar_df = pred_df[(pred_df['다음주문예상일'] >= today) &
                      (pred_df['다음주문예상일'] <= end_date)].copy()

print(f"향후 90일 이내 예상 주문: {len(calendar_df)}건")

# 3. 결과 저장
print("\n[3] 결과 저장")

# 전체 예측 결과
pred_df.to_csv('./customer_order_predictions.csv', index=False, encoding='utf-8-sig')
print(f"전체 예측 결과 저장: customer_order_predictions.csv")

# 상세 품목 정보 저장
detailed_predictions = []
for pred in predictions:
    customer = pred['거래처명']
    if pred['주요품목'] is not None and len(pred['주요품목']) > 0:
        for item, row in pred['주요품목'].iterrows():
            detailed_predictions.append({
                '거래처명': customer,
                '다음주문예상일': pred['다음주문예상일'],
                '품목': item,
                '평균수량(kg)': row['평균수량'],
                '평균금액': row['평균금액'],
                '거래횟수': row['거래횟수']
            })

if detailed_predictions:
    detail_df = pd.DataFrame(detailed_predictions)
    detail_df = detail_df.sort_values(['다음주문예상일', '거래처명'])
    detail_df.to_csv('./customer_order_predictions_detailed.csv', index=False, encoding='utf-8-sig')
    print(f"상세 품목 예측 저장: customer_order_predictions_detailed.csv")

# 4. 주간별 예상 주문 요약
print("\n[4] 주간별 예상 주문 요약")

calendar_df['예상주'] = calendar_df['다음주문예상일'].dt.to_period('W')
weekly_summary = calendar_df.groupby('예상주').agg({
    '거래처명': 'count',
    '예상금액': 'sum',
    '예상수량(kg)': 'sum'
}).round(0)
weekly_summary.columns = ['예상주문건수', '예상매출액', '예상출하량(kg)']

print(weekly_summary)

weekly_summary.to_csv('./weekly_order_forecast.csv', encoding='utf-8-sig')
print(f"\n주간별 예측 저장: weekly_order_forecast.csv")

# 5. 향후 30일 예상 주문 상세 리스트
print("\n" + "=" * 80)
print("향후 30일 이내 예상 주문 상세")
print("=" * 80)

next_30_days = pred_df[(pred_df['다음주문예상일'] >= today) &
                       (pred_df['다음주문예상일'] <= today + timedelta(days=30))].copy()

print(f"\n향후 30일 예상 주문: {len(next_30_days)}건")
print(f"예상 총 매출액: {next_30_days['예상금액'].sum():,.0f}원")
print(f"예상 총 출하량: {next_30_days['예상수량(kg)'].sum():,.0f}kg")

if len(next_30_days) > 0:
    print(f"\n상위 20개 예상 주문:")
    print(next_30_days.head(20)[['거래처명', '다음주문예상일', '예상금액', '예상수량(kg)', '평균주기(일)']])

# 6. 시각화: 향후 30일 캘린더
print("\n[5] 캘린더 시각화 생성")

import matplotlib.patches as mpatches
from matplotlib.patches import Rectangle

# 향후 30일 데이터
next_30 = next_30_days.copy()
next_30['일'] = next_30['다음주문예상일'].dt.day
next_30['월'] = next_30['다음주문예상일'].dt.month

# 현재 월과 다음 월
current_month = today.month
current_year = today.year

fig, axes = plt.subplots(1, 2, figsize=(20, 10))

for idx, month_offset in enumerate([0, 1]):
    ax = axes[idx]

    # 해당 월
    target_date = today + timedelta(days=30*month_offset)
    target_month = target_date.month
    target_year = target_date.year

    # 캘린더 생성
    cal = calendar.monthcalendar(target_year, target_month)

    # 빈 캘린더 그리기
    ax.set_xlim(0, 7)
    ax.set_ylim(0, len(cal))
    ax.set_aspect('equal')
    ax.axis('off')

    # 제목
    month_name = f"{target_year}년 {target_month}월"
    ax.text(3.5, len(cal) + 0.3, month_name,
            ha='center', fontsize=16, fontweight='bold')

    # 요일 헤더
    days = ['월', '화', '수', '목', '금', '토', '일']
    for i, day in enumerate(days):
        ax.text(i + 0.5, len(cal) - 0.3, day,
                ha='center', va='center', fontsize=11, fontweight='bold')

    # 날짜 그리기
    for week_idx, week in enumerate(cal):
        for day_idx, day in enumerate(week):
            if day == 0:
                continue

            y = len(cal) - week_idx - 1
            x = day_idx

            # 사각형 그리기
            rect = Rectangle((x, y), 1, 1, linewidth=1,
                           edgecolor='gray', facecolor='white')
            ax.add_patch(rect)

            # 날짜 표시
            ax.text(x + 0.5, y + 0.8, str(day),
                   ha='center', va='top', fontsize=10)

            # 해당 날짜에 예상 주문이 있는지 확인
            orders_on_day = next_30[(next_30['월'] == target_month) &
                                   (next_30['일'] == day)]

            if len(orders_on_day) > 0:
                # 주문 개수 표시
                order_count = len(orders_on_day)
                total_amount = orders_on_day['예상금액'].sum() / 1000000  # 백만원

                # 배경색 변경 (금액에 따라)
                if total_amount >= 50:
                    color = '#FF6B6B'  # 빨강 (5천만원 이상)
                elif total_amount >= 20:
                    color = '#FFD93D'  # 노랑 (2천만원 이상)
                else:
                    color = '#95E1D3'  # 연두 (2천만원 미만)

                rect.set_facecolor(color)
                rect.set_alpha(0.5)

                # 주문 정보 표시
                ax.text(x + 0.5, y + 0.5, f'{order_count}건',
                       ha='center', va='center', fontsize=9, fontweight='bold')
                ax.text(x + 0.5, y + 0.2, f'{total_amount:.0f}M',
                       ha='center', va='center', fontsize=8)

# 범례
legend_elements = [
    mpatches.Patch(facecolor='#FF6B6B', alpha=0.5, label='5천만원 이상'),
    mpatches.Patch(facecolor='#FFD93D', alpha=0.5, label='2천만원~5천만원'),
    mpatches.Patch(facecolor='#95E1D3', alpha=0.5, label='2천만원 미만')
]
fig.legend(handles=legend_elements, loc='upper center', ncol=3,
          fontsize=11, bbox_to_anchor=(0.5, 0.02))

plt.suptitle('거래처 예상 주문 캘린더 (향후 2개월)',
            fontsize=18, fontweight='bold', y=0.98)
plt.tight_layout(rect=[0, 0.03, 1, 0.96])
plt.savefig('./visualizations/order_prediction_calendar.png', dpi=300, bbox_inches='tight')
print("저장: order_prediction_calendar.png")
plt.close()

print("\n" + "=" * 80)
print("예측 및 캘린더 생성 완료!")
print("=" * 80)
print("\n생성된 파일:")
print("1. customer_order_predictions.csv - 전체 거래처 예측")
print("2. customer_order_predictions_detailed.csv - 품목별 상세 예측")
print("3. weekly_order_forecast.csv - 주간별 예측 요약")
print("4. visualizations/order_prediction_calendar.png - 캘린더 시각화")
