#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
거래처 수요 예측 시각화 및 인사이트 생성
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

# 한글 폰트 설정
plt.rcParams['axes.unicode_minus'] = False

print("=" * 80)
print("거래처 수요 예측 시각화 및 인사이트")
print("=" * 80)

# 데이터 로드
df = pd.read_csv('./processed_sales_data.csv', encoding='utf-8-sig')
df['일자_dt'] = pd.to_datetime(df['일자_dt'])
df['연월'] = pd.to_datetime(df['연월'])

cycle_df = pd.read_csv('./major_customers_cycle.csv', encoding='utf-8-sig', index_col=0)

print(f"\n데이터 로드 완료")

# 시각화 디렉토리 생성
import os
if not os.path.exists('./visualizations'):
    os.makedirs('./visualizations')
    print("visualizations 폴더 생성")

# 1. 판매 주기별 거래처 분포
print("\n[1] 판매 주기별 거래처 분포 시각화")

def classify_cycle(avg_cycle):
    if pd.isna(avg_cycle):
        return '분류불가'
    elif avg_cycle <= 7:
        return '주간(≤7일)'
    elif avg_cycle <= 15:
        return '격주(8-15일)'
    elif avg_cycle <= 30:
        return '월간(16-30일)'
    elif avg_cycle <= 60:
        return '격월(31-60일)'
    elif avg_cycle <= 90:
        return '분기(61-90일)'
    else:
        return '장기(>90일)'

cycle_df['주기분류'] = cycle_df['평균주기(일)'].apply(classify_cycle)

plt.figure(figsize=(12, 6))
cycle_counts = cycle_df['주기분류'].value_counts()
colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7', '#DFE6E9']
plt.bar(range(len(cycle_counts)), cycle_counts.values, color=colors)
plt.xlabel('Sales Cycle Category', fontsize=12)
plt.ylabel('Number of Customers', fontsize=12)
plt.title('Distribution of Customers by Sales Cycle', fontsize=14, fontweight='bold')
plt.xticks(range(len(cycle_counts)), cycle_counts.index, rotation=45)
plt.tight_layout()
plt.savefig('./visualizations/01_sales_cycle_distribution.png', dpi=300, bbox_inches='tight')
print("저장: 01_sales_cycle_distribution.png")
plt.close()

# 2. 상위 20개 거래처 판매 추이
print("\n[2] 상위 20개 거래처 월별 판매 추이")

top_20_customers = cycle_df.head(20).index.tolist()
top_20_df = df[df['거래처명'].isin(top_20_customers)].copy()

monthly_sales = top_20_df.groupby([top_20_df['연월'], '거래처명'])['공급가액'].sum().reset_index()
monthly_sales['연월'] = pd.to_datetime(monthly_sales['연월'].astype(str))

# 상위 10개 거래처만 시각화 (가독성)
top_10_customers = cycle_df.head(10).index.tolist()
top_10_monthly = monthly_sales[monthly_sales['거래처명'].isin(top_10_customers)]

plt.figure(figsize=(16, 8))
for customer in top_10_customers:
    customer_data = top_10_monthly[top_10_monthly['거래처명'] == customer]
    if len(customer_data) > 0:
        plt.plot(customer_data['연월'], customer_data['공급가액'] / 1000000,
                marker='o', linewidth=2, markersize=4, label=customer, alpha=0.7)

plt.xlabel('Month', fontsize=12)
plt.ylabel('Sales Amount (Million KRW)', fontsize=12)
plt.title('Top 10 Customers - Monthly Sales Trend', fontsize=14, fontweight='bold')
plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=9)
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('./visualizations/02_top10_monthly_sales_trend.png', dpi=300, bbox_inches='tight')
print("저장: 02_top10_monthly_sales_trend.png")
plt.close()

# 3. 거래처별 수량 vs 금액 산점도
print("\n[3] 거래처별 월평균 거래량 vs 매출액")

plt.figure(figsize=(12, 8))
scatter_data = cycle_df.copy()
scatter_data = scatter_data[scatter_data['평균월거래량(kg)'].notna() & scatter_data['평균월매출액'].notna()]

colors_map = {
    '주간(≤7일)': '#FF6B6B',
    '격주(8-15일)': '#4ECDC4',
    '월간(16-30일)': '#45B7D1',
    '격월(31-60일)': '#96CEB4',
    '분기(61-90일)': '#FFEAA7',
    '장기(>90일)': '#DFE6E9'
}

for cycle_type in scatter_data['주기분류'].unique():
    cycle_data = scatter_data[scatter_data['주기분류'] == cycle_type]
    plt.scatter(cycle_data['평균월거래량(kg)'], cycle_data['평균월매출액'] / 1000000,
               s=100, alpha=0.6, c=colors_map.get(cycle_type, '#95a5a6'), label=cycle_type)

# 상위 5개 거래처 레이블 표시
top_5 = cycle_df.head(5)
for idx, row in top_5.iterrows():
    if pd.notna(row['평균월거래량(kg)']) and pd.notna(row['평균월매출액']):
        plt.annotate(idx[:15] + '...' if len(idx) > 15 else idx,
                    (row['평균월거래량(kg)'], row['평균월매출액'] / 1000000),
                    fontsize=8, alpha=0.8)

plt.xlabel('Avg Monthly Quantity (kg)', fontsize=12)
plt.ylabel('Avg Monthly Sales (Million KRW)', fontsize=12)
plt.title('Customer Analysis: Quantity vs Sales by Cycle Type', fontsize=14, fontweight='bold')
plt.legend(fontsize=9)
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('./visualizations/03_quantity_vs_sales.png', dpi=300, bbox_inches='tight')
print("저장: 03_quantity_vs_sales.png")
plt.close()

# 4. 최근 12개월 주요 거래처 판매 패턴
print("\n[4] 최근 12개월 주요 거래처 판매 패턴")

recent_12m = df['일자_dt'].max() - timedelta(days=365)
recent_df = df[df['일자_dt'] >= recent_12m].copy()

top_5_recent = recent_df.groupby('거래처명')['공급가액'].sum().sort_values(ascending=False).head(5).index

fig, axes = plt.subplots(5, 1, figsize=(14, 12))
for i, customer in enumerate(top_5_recent):
    customer_data = recent_df[recent_df['거래처명'] == customer]
    daily_sales = customer_data.groupby('일자_dt')['공급가액'].sum().reset_index()

    axes[i].plot(daily_sales['일자_dt'], daily_sales['공급가액'] / 1000000,
                marker='o', linewidth=2, markersize=3, color='#3498db')
    axes[i].set_title(f'{customer} - Recent 12 Months Sales Pattern',
                     fontsize=11, fontweight='bold')
    axes[i].set_ylabel('Sales\n(Million KRW)', fontsize=9)
    axes[i].grid(True, alpha=0.3)

    # 평균선 추가
    avg_sales = daily_sales['공급가액'].mean() / 1000000
    axes[i].axhline(y=avg_sales, color='r', linestyle='--', alpha=0.5, label=f'Avg: {avg_sales:.1f}M')
    axes[i].legend(fontsize=8)

axes[4].set_xlabel('Date', fontsize=10)
plt.tight_layout()
plt.savefig('./visualizations/04_recent_12months_pattern.png', dpi=300, bbox_inches='tight')
print("저장: 04_recent_12months_pattern.png")
plt.close()

# 5. 주기 규칙성별 비교
print("\n[5] 주기 규칙성별 거래처 비교")

fig, axes = plt.subplots(1, 2, figsize=(14, 6))

# 규칙성별 거래처 수
regularity_counts = cycle_df['주기규칙성'].value_counts()
axes[0].pie(regularity_counts.values, labels=regularity_counts.index,
           autopct='%1.1f%%', startangle=90, colors=['#3498db', '#e74c3c'])
axes[0].set_title('Customer Distribution by Regularity', fontsize=12, fontweight='bold')

# 규칙성별 평균 매출액
regularity_sales = cycle_df.groupby('주기규칙성')['평균월매출액'].sum() / 1000000
axes[1].bar(range(len(regularity_sales)), regularity_sales.values,
           color=['#3498db', '#e74c3c'])
axes[1].set_xticks(range(len(regularity_sales)))
axes[1].set_xticklabels(regularity_sales.index)
axes[1].set_ylabel('Total Monthly Sales (Million KRW)', fontsize=10)
axes[1].set_title('Total Monthly Sales by Regularity', fontsize=12, fontweight='bold')
axes[1].grid(True, alpha=0.3, axis='y')

plt.tight_layout()
plt.savefig('./visualizations/05_regularity_comparison.png', dpi=300, bbox_inches='tight')
print("저장: 05_regularity_comparison.png")
plt.close()

# 6. 연도별 거래 추이
print("\n[6] 연도별 거래 추이")

yearly_stats = df.groupby('연도').agg({
    '거래처명': 'nunique',
    '공급가액': 'sum',
    '수량(kg)': 'sum'
}).reset_index()

yearly_stats = yearly_stats[yearly_stats['연도'] < 2026]  # 2026년 제외 (불완전)

fig, axes = plt.subplots(2, 1, figsize=(14, 10))

# 매출액 추이
axes[0].plot(yearly_stats['연도'], yearly_stats['공급가액'] / 1000000000,
            marker='o', linewidth=3, markersize=8, color='#2ecc71')
axes[0].fill_between(yearly_stats['연도'], yearly_stats['공급가액'] / 1000000000,
                     alpha=0.3, color='#2ecc71')
axes[0].set_ylabel('Sales (Billion KRW)', fontsize=11)
axes[0].set_title('Annual Sales Trend', fontsize=13, fontweight='bold')
axes[0].grid(True, alpha=0.3)

# 거래처 수 추이
ax2 = axes[0].twinx()
ax2.plot(yearly_stats['연도'], yearly_stats['거래처명'],
        marker='s', linewidth=2, markersize=6, color='#e74c3c', linestyle='--')
ax2.set_ylabel('Number of Customers', fontsize=11, color='#e74c3c')
ax2.tick_params(axis='y', labelcolor='#e74c3c')

# 수량 추이
axes[1].bar(yearly_stats['연도'], yearly_stats['수량(kg)'] / 1000000,
           color='#3498db', alpha=0.7)
axes[1].set_xlabel('Year', fontsize=11)
axes[1].set_ylabel('Quantity (Ton)', fontsize=11)
axes[1].set_title('Annual Sales Quantity Trend', fontsize=13, fontweight='bold')
axes[1].grid(True, alpha=0.3, axis='y')

plt.tight_layout()
plt.savefig('./visualizations/06_yearly_trend.png', dpi=300, bbox_inches='tight')
print("저장: 06_yearly_trend.png")
plt.close()

print("\n" + "=" * 80)
print("모든 시각화 완료: ./visualizations/ 폴더 확인")
print("=" * 80)
