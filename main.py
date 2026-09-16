import datetime
import requests
import pandas as pd
import streamlit as st
from datetime import timezone, timedelta

# 페이지 기본 설정 (타이틀 및 레이아웃 넓게)
st.set_page_config(page_title="어제의 박스오피스", layout="wide")

st.title("🎬 어제의 박스오피스")

# 1. 한국 시간(KST) 기준 어제 날짜 계산 (서버 시차가 달라도 KST 고정)
kst = timezone(timedelta(hours=9))
yesterday = datetime.datetime.now(kst) - timedelta(days=1)
target_date_str = yesterday.strftime("%Y%m%d")
display_date_str = yesterday.strftime("%Y년 %m월 %d일")

st.write(f"📅 **기준 일자:** {display_date_str}")

# 2. API 호출 함수 (1시간 캐싱 적용)
@st.cache_data(ttl=3600)
def fetch_box_office_data(api_key, target_dt):
    url = "https://www.kobis.or.kr/kobisopenapi/webservice/rest/boxoffice/searchDailyBoxOfficeList.json"
    params = {"key": api_key, "targetDt": target_dt}
    
    try:
        response = requests.get(url, params=params, timeout=10)
        # 네트워크 오류 등으로 상태 코드가 200이 아닌 경우
        if response.status_code != 200:
            return None, f"서버 통신 실패 (상태 코드: {response.status_code})"
        
        data = response.json()
        
        # KOBIS 특유의 오류 응답 (faultInfo가 포함된 경우)
        if "faultInfo" in data:
            message = data["faultInfo"].get("message", "인증키 또는 요청 오류가 발생했습니다.")
            return None, f"API 오류: {message}"
        
        box_office_result = data.get("boxOfficeResult", {})
        movie_list = box_office_result.get("dailyBoxOfficeList", [])
        
        # 목록이 비어있는 경우
        if not movie_list:
            return None, "해당 날짜의 영화 목록 데이터가 비어있습니다."
            
        return movie_list, None

    except Exception as e:
        return None, f"데이터를 불러오는 중 예외가 발생했습니다: {str(e)}"

# 3. Streamlit Secrets에서 API 키 가져오기
api_key = st.secrets.get("KOBIS_KEY")

if not api_key:
    st.error("🚨 **API 키를 찾을 수 없습니다.**")
    st.info("""
    **확인해야 할 사항:**
    1. Streamlit Cloud의 **Secrets** 설정에 `KOBIS_KEY = "발급받은_키"` 형태로 입력되어 있는지 확인하세요.
    2. 로컬에서 실행 중이라면 `.streamlit/secrets.toml` 파일에 키가 설정되어 있는지 확인하세요.
    """)
else:
    # 데이터 불러오기 실행
    movie_list, error_message = fetch_box_office_data(api_key, target_date_str)
    
    if error_message:
        st.error(f"🚨 **데이터를 가져오지 못했습니다.**")
        st.warning(f"**상세 원인:** {error_message}")
        st.info("""
        **💡 해결 가이드:**
        * API 키가 올바르게 입력되었는지 확인하세요 (공백 주의).
        * 영화진흥위원회(KOBIS) 개발자 센터에서 일일 호출한도가 초과되지 않았는지 확인하세요.
        * 한국시간 기준 새벽 시간에는 어제 자 집계가 아직 완료되지 않았을 수 있습니다.
        """)
    else:
        # 4. 데이터 가공 및 수치형 변환
        df = pd.DataFrame(movie_list)
        
        # 문자열 데이터를 정수형(int) 데이터로 변환
        numeric_columns = ["rank", "audiCnt", "audiAcc", "scrnCnt", "rankInten", "showCnt"]
        for col in numeric_columns:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(int)

        # 5. 1위 영화 지표 카드 표시 (st.metric 사용)
        top_1 = df[df["rank"] == 1].iloc[0]
        st.subheader(f"🥇 오늘의 1위: {top_1['movieNm']}")
        
        col1, col2, col3 = st.columns(3)
        col1.metric("일일 관객수", f"{top_1['audiCnt']:,} 명", delta=f"전날 대비 {top_1['rankInten']}위")
        col2.metric("누적 관객수", f"{top_1['audiAcc']:,} 명")
        col3.metric("스크린수", f"{top_1['scrnCnt']:,} 개")

        st.divider()

        # 6. 상위 5개 영화 관객수 막대그래프
        st.subheader("📊 관객수 상위 5개 영화")
        top_5_df = df.sort_values(by="rank").head(5)
        
        # 막대그래프 생성을 위해 차트용 DataFrame 구성
        chart_data = top_5_df.set_index("movieNm")[["audiCnt"]]
        chart_data.columns = ["일일 관객수"]
        st.bar_chart(chart_data)

        st.divider()

        # 7. 전체 박스오피스 순위 표
        st.subheader("📋 전체 박스오피스 순위")
        
        # 표시할 컬럼 정리 및 이름 변경
        display_df = df[["rank", "movieNm", "openDt", "audiCnt", "audiAcc", "scrnCnt"]].copy()
        display_df.columns = ["순위", "영화명", "개봉일", "관객수", "누적관객", "스크린수"]
        
        # 숫자 포맷 적용 (천 단위 쉼표) 및 출력
        st.dataframe(
            display_df.style.format({
                "관객수": "{:,}",
                "누적관객": "{:,}",
                "스크린수": "{:,}"
            }),
            use_container_width=True,
            hide_index=True
        )
