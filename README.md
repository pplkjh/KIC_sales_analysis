# KIC Sales Analysis Project

ERP 데이터 기반 거래처 수요 예측 및 판매 주기 분석 프로젝트

## 📂 프로젝트 구조

```
KIC_sales_analysis/
├── rawdata/                          # 원본 ERP 데이터
├── visualizations/                   # 생성된 시각화 파일
├── processed_sales_data.csv          # 정제된 판매 데이터
├── customer_sales_cycle.csv          # 거래처 판매 주기 분석
├── major_customers_cycle.csv         # 주요 거래처 분석
├── top_50_customers.csv              # 상위 50개 거래처 통계
├── customer_demand_analysis.py       # 초기 데이터 탐색
├── data_preprocessing.py             # 데이터 정제 스크립트
├── customer_cycle_analysis.py        # 판매 주기 분석
├── visualization_and_insights.py     # 시각화 생성
├── ANALYSIS_REPORT.md                # 📊 최종 분석 보고서
└── README.md                         # 프로젝트 설명
```

## 🎯 분석 목표

1. **거래처 수요 예측**: 과거 거래 패턴 기반 향후 수요 예측
2. **판매 주기 분석**: 거래처별 주문 주기 및 규칙성 파악
3. **고급 예측 모델 준비**: CatBoost, Random Forest 적용 기반 마련

## 📊 주요 분석 결과

- **총 거래처**: 544개
- **주요 거래처** (거래건수 ≥100): 64개
- **평균 판매 주기**: 38.9일
- **데이터 기간**: 2009-12 ~ 2026-01 (약 16년)

### 거래처 주기별 분류
- 주간거래 (≤7일): 8개
- 격주거래 (8-15일): 10개
- 월간거래 (16-30일): 18개
- 격월거래 (31-60일): 14개
- 분기거래 (61-90일): 7개
- 장기거래 (>90일): 7개

## 🚀 실행 방법

### 1. 환경 설정
```bash
pip install pandas numpy matplotlib seaborn scikit-learn openpyxl
```

### 2. 데이터 분석 실행
```bash
# 1단계: 데이터 정제
python data_preprocessing.py

# 2단계: 판매 주기 분석
python customer_cycle_analysis.py

# 3단계: 시각화 생성
python visualization_and_insights.py
```

## 📈 주요 산출물

### 분석 결과 파일
- `customer_sales_cycle.csv`: 전체 거래처 판매 주기 분석
- `major_customers_cycle.csv`: 주요 거래처 상세 분석
- `ANALYSIS_REPORT.md`: **종합 분석 보고서** ← 여기를 확인하세요!

### 시각화 (./visualizations/)
1. 판매 주기별 거래처 분포
2. 상위 10개 거래처 월별 판매 추이
3. 거래량 vs 매출액 분석
4. 최근 12개월 주요 거래처 패턴
5. 주기 규칙성별 비교
6. 연도별 거래 추이

## 📋 향후 계획

### Phase 2: 고급 예측 모델
- [ ] CatBoost 기반 수요 예측 모델 개발
- [ ] Random Forest 기반 매출 영향 요인 분석
- [ ] SARIMA/Prophet 시계열 예측 모델
- [ ] 실시간 예측 대시보드 구축

### Phase 3: 시스템 구축
- [ ] 자동 수요 예측 시스템
- [ ] 재고 최적화 알고리즘
- [ ] 거래처별 맞춤 영업 전략

## 🔍 상세 분석 결과

전체 분석 결과는 **[ANALYSIS_REPORT.md](./ANALYSIS_REPORT.md)** 를 참조하세요.

## 📞 Contact

분석 관련 문의: KIC Data Analytics Team

---

*Last Updated: 2026-01-05*