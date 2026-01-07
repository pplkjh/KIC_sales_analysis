# KIC Sales Analysis Project

ERP 데이터 기반 거래처 수요 예측 및 판매 주기 분석 프로젝트

## 📂 프로젝트 구조

```
KIC_sales_analysis/
├── rawdata/                                    # 원본 ERP 데이터
├── visualizations/                             # 생성된 시각화 파일
│   ├── order_prediction_calendar.png          # 📅 주문 예측 캘린더
│   └── ...                                     # 기타 시각화
├── processed_sales_data.csv                    # 정제된 판매 데이터
├── customer_sales_cycle.csv                    # 거래처 판매 주기 분석
├── major_customers_cycle.csv                   # 주요 거래처 분석
├── customer_order_predictions.csv              # 🎯 거래처별 예상 주문일
├── customer_order_predictions_detailed.csv     # 🎯 품목별 상세 예측
├── weekly_order_forecast.csv                   # 주간별 예측 요약
├── data_preprocessing.py                       # 데이터 정제 스크립트
├── customer_cycle_analysis.py                  # 판매 주기 분석
├── visualization_and_insights.py               # 시각화 생성
├── order_prediction_calendar.py                # 🎯 주문 예측 시스템
├── ANALYSIS_REPORT.md                          # 📊 최종 분석 보고서
└── README.md                                   # 프로젝트 설명
```

## 🎯 분석 목표

1. **거래처 수요 예측**: 과거 거래 패턴 기반 향후 수요 예측
2. **판매 주기 분석**: 거래처별 주문 주기 및 규칙성 파악
3. **고급 예측 모델 준비**: CatBoost, Random Forest 적용 기반 마련

## 📊 주요 분석 결과

### 거래처 분석
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

### 🎯 주문 예측 결과 (향후 30일)
- **예상 주문**: 19건
- **예상 총 매출액**: 1억 970만원
- **예상 총 출하량**: 55,578kg
- **거래처별 예상일, 품목, 수량, 금액 정보 제공**

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

# 4단계: 🎯 주문 예측 캘린더 생성 (NEW!)
python order_prediction_calendar.py
```

## 📈 주요 산출물

### 분석 결과 파일
- `customer_sales_cycle.csv`: 전체 거래처 판매 주기 분석
- `major_customers_cycle.csv`: 주요 거래처 상세 분석
- `ANALYSIS_REPORT.md`: **종합 분석 보고서** ← 여기를 확인하세요!

### 🎯 주문 예측 파일 (NEW!)
- `customer_order_predictions.csv`: **거래처별 다음 주문 예상일**
  - 거래처명, 최근주문일, 평균주기, 다음주문예상일, 예상금액, 예상수량
- `customer_order_predictions_detailed.csv`: **품목별 상세 예측**
  - 거래처별로 어떤 품목이 얼마나 나갈지 예측
  - 품목, 평균수량, 평균금액, 거래횟수 포함
- `weekly_order_forecast.csv`: 주간별 예상 주문 요약

### 시각화 (./visualizations/)
1. 판매 주기별 거래처 분포 (수치 표시)
2. 상위 10개 거래처 월별 판매 추이
3. 거래량 vs 매출액 분석
4. 최근 12개월 주요 거래처 패턴
5. 주기 규칙성별 비교
6. 연도별 거래 추이
7. **📅 주문 예측 캘린더 (NEW!)** - 향후 2개월 예상 주문 일정

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