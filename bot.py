import streamlit as st
import requests
import FinanceDataReader as fdr
import datetime
import plotly.graph_objects as go

# 1. 통제실 UI 세팅
st.set_page_config(page_title="AI Quant Sniper", layout="wide")
st.title("🎯 AI 퀀트 통제실 (Radar 2.0)")

# 2. API 키 
NAVER_CLIENT_ID = st.secrets["NAVER_CLIENT_ID"]
NAVER_CLIENT_SECRET = st.secrets["NAVER_CLIENT_SECRET"]

# 3. [개선] 상장 주식 목록 캐싱 (초고속 자동완성을 위해 한 번만 불러와서 저장)
@st.cache_data
def get_stock_list():
    df = fdr.StockListing('KRX')
    return df[['Name', 'Code']].dropna()

krx_df = get_stock_list()
stock_names = krx_df['Name'].tolist()

# 4. [개선] 뉴스 필터링 강화 함수
def get_naver_news(stock_name):
    # '종목명 + 주식' 으로 검색어 좁히고, 최신순(date)으로 정렬
    query = f"{stock_name} 주식" 
    url = f"https://openapi.naver.com/v1/search/news.json?query={query}&display=5&sort=date"
    headers = {
        "X-Naver-Client-Id": NAVER_CLIENT_ID,
        "X-Naver-Client-Secret": NAVER_CLIENT_SECRET
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()['items']
    return None

st.write("---")

# 5. [개선] 스마트 자동완성 검색창 (일부만 쳐도 됨)
target_stock = st.selectbox(
    "🔍 타겟 종목 스캔 (초성 또는 글자 일부를 입력하세요):", 
    ["종목을 선택하세요"] + stock_names
)

if target_stock != "종목을 선택하세요":
    if st.button("🔴 정밀 레이더 가동", type="primary"):
        # 종목코드 추출
        ticker = krx_df[krx_df['Name'] == target_stock]['Code'].values[0]
        
        # 60일치 데이터 불러오기 (이동평균선 계산용)
        start_date = datetime.date.today() - datetime.timedelta(days=90)
        df = fdr.DataReader(ticker, start_date)
        
        if not df.empty:
            # 이평선 계산
            df['MA5'] = df['Close'].rolling(window=5).mean()
            df['MA20'] = df['Close'].rolling(window=20).mean()
            
            # 차트에 보여줄 최근 30일 데이터만 자르기
            df_chart = df.tail(30)
            
            # 최상단 전광판 (현재가 & 수익률)
            today_close = df['Close'].iloc[-1]
            prev_close = df['Close'].iloc[-2]
            change_pct = ((today_close - prev_close) / prev_close) * 100
            
            st.metric(label=f"🔥 {target_stock} 실시간 종가 (전일대비)", value=f"{today_close:,.0f}원", delta=f"{change_pct:.2f}%")
            
            col1, col2 = st.columns([6, 4])
            
            with col1:
                st.write("### 📈 세력선/생명선 추적 캔들 차트 (30일)")
                fig = go.Figure()
                # 양봉/음봉 캔들스틱
                fig.add_trace(go.Candlestick(x=df_chart.index, open=df_chart['Open'], high=df_chart['High'], low=df_chart['Low'], close=df_chart['Close'], name='주가', increasing_line_color='red', decreasing_line_color='blue'))
                # 5일선 / 20일선
                fig.add_trace(go.Scatter(x=df_chart.index, y=df_chart['MA5'], mode='lines', name='5일선(단기)', line=dict(color='orange', width=2)))
                fig.add_trace(go.Scatter(x=df_chart.index, y=df_chart['MA20'], mode='lines', name='20일선(세력)', line=dict(color='green', width=2)))
                
                # 차트 디자인 다듬기
                fig.update_layout(xaxis_rangeslider_visible=False, margin=dict(l=0, r=0, t=30, b=0), template="plotly_dark", height=400)
                st.plotly_chart(fig, use_container_width=True)
                
            with col2:
                st.write("### 📰 실시간 A급 뉴스 (최신순 필터링)")
                news_items = get_naver_news(target_stock)
                if news_items:
                    for item in news_items:
                        title = item['title'].replace('<b>', '').replace('</b>', '').replace('&quot;', '"').replace('&apos;', "'")
                        st.markdown(f"📍 [{title}]({item['link']})")
                        st.caption(f"발행: {item['pubDate'][5:22]}") # 시간 표시 추가
                else:
                    st.info("최근 관련 뉴스가 없습니다.")
