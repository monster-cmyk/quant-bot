import streamlit as st
import requests
import FinanceDataReader as fdr
import datetime

# 1. 통제실 UI 기본 세팅
st.set_page_config(page_title="AI Quant Sniper Base", layout="wide")
st.title("🎯 AI 퀀트 통제실 (Radar System ON)")

# 2. 금고에서 네이버 API 키 꺼내오기
NAVER_CLIENT_ID = st.secrets["NAVER_CLIENT_ID"]
NAVER_CLIENT_SECRET = st.secrets["NAVER_CLIENT_SECRET"]

# 3. 레이더 기능 함수: 뉴스 긁어오기
def get_naver_news(query):
    url = f"https://openapi.naver.com/v1/search/news.json?query={query}&display=5&sort=sim"
    headers = {
        "X-Naver-Client-Id": NAVER_CLIENT_ID,
        "X-Naver-Client-Secret": NAVER_CLIENT_SECRET
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()['items']
    else:
        return None

# 4. 화면 레이아웃 (주가 & 뉴스)
st.write("---")
st.subheader("🔍 타겟 종목 스캐너")

# 사용자 입력창
target_stock = st.text_input("타겟 종목 이름을 입력하세요 (예: 실리콘투, 리가켐바이오):", "실리콘투")

col1, col2 = st.columns(2)

if st.button("레이더 가동"):
    with col1:
        st.write(f"### 📈 {target_stock} 최근 5일 주가 흐름")
        try:
            # 주가 데이터 가져오기 (종목명으로)
            df_krx = fdr.StockListing('KRX')
            ticker = df_krx[df_krx['Name'] == target_stock]['Code'].values[0]
            start_date = datetime.date.today() - datetime.timedelta(days=10)
            df = fdr.DataReader(ticker, start_date)
            st.dataframe(df.tail(5)[['Open', 'High', 'Low', 'Close', 'Volume']])
        except:
            st.error("종목명을 정확히 입력하거나 주가 데이터를 불러올 수 없습니다.")

    with col2:
        st.write(f"### 📰 {target_stock} 실시간 주요 뉴스")
        news_items = get_naver_news(target_stock)
        if news_items:
            for item in news_items:
                # 불필요한 HTML 태그 제거
                title = item['title'].replace('<b>', '').replace('</b>', '').replace('&quot;', '"')
                st.markdown(f"- [{title}]({item['link']})")
        else:
            st.error("뉴스를 불러오는 데 실패했습니다.")
