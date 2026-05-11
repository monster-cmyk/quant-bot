import streamlit as st
import requests
import FinanceDataReader as fdr
import datetime
import plotly.graph_objects as go

# 1. 통제실 UI 세팅
st.set_page_config(page_title="AI Quant Sniper", layout="wide")
st.title("🎯 AI 퀀트 통제실 (Radar 2.1 - 긴급복구)")

# 2. API 키 
NAVER_CLIENT_ID = st.secrets["NAVER_CLIENT_ID"]
NAVER_CLIENT_SECRET = st.secrets["NAVER_CLIENT_SECRET"]

# 3. 뉴스 필터링 함수
def get_naver_news(stock_name):
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

# 4. [수정] 입력 방식 변경 (에러 방지용)
col_input1, col_input2 = st.columns([2, 1])
with col_input1:
    target_name = st.text_input("🔍 종목명을 입력하세요 (뉴스 검색용):", "실리콘투")
with col_input2:
    target_code = st.text_input("🔢 종목코드를 입력하세요 (차트용):", "252270")
    st.caption("실리콘투: 252270 / 리가켐: 141080")

if st.button("🔴 정밀 레이더 가동", type="primary"):
    # 90일치 데이터 불러오기
    start_date = datetime.date.today() - datetime.timedelta(days=90)
    
    try:
        df = fdr.DataReader(target_code, start_date)
        
        if not df.empty:
            # 이평선 계산
            df['MA5'] = df['Close'].rolling(window=5).mean()
            df['MA20'] = df['Close'].rolling(window=20).mean()
            df_chart = df.tail(30)
            
            # 전광판
            today_close = df['Close'].iloc[-1]
            prev_close = df['Close'].iloc[-2]
            change_pct = ((today_close - prev_close) / prev_close) * 100
            st.metric(label=f"🔥 {target_name} 종가", value=f"{today_close:,.0f}원", delta=f"{change_pct:.2f}%")
            
            col1, col2 = st.columns([6, 4])
            with col1:
                st.write("### 📈 캔들 차트 (MA5/MA20)")
                fig = go.Figure()
                fig.add_trace(go.Candlestick(x=df_chart.index, open=df_chart['Open'], high=df_chart['High'], low=df_chart['Low'], close=df_chart['Close'], name='주가'))
                fig.add_trace(go.Scatter(x=df_chart.index, y=df_chart['MA5'], name='5일선', line=dict(color='orange')))
                fig.add_trace(go.Scatter(x=df_chart.index, y=df_chart['MA20'], name='20일선', line=dict(color='green')))
                fig.update_layout(xaxis_rangeslider_visible=False, template="plotly_dark", height=400)
                st.plotly_chart(fig, use_container_width=True)
                
            with col2:
                st.write("### 📰 실시간 뉴스")
                news_items = get_naver_news(target_name)
                if news_items:
                    for item in news_items:
                        title = item['title'].replace('<b>', '').replace('</b>', '').replace('&quot;', '"')
                        st.markdown(f"📍 [{title}]({item['link']})")
                else:
                    st.info("뉴스를 불러올 수 없습니다.")
    except:
        st.error("종목 코드가 올바르지 않거나 데이터를 가져올 수 없습니다.")
