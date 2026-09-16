import datetime
import requests
import pandas as pd
import streamlit as st
from datetime import timezone, timedelta

# 페이지 기본 설정 (타이틀 및 레이아웃 넓게)
st.set_page_config(page_title="박스오피스조회", layout="wide")

st.title("🎬 일별 박스오피스 조회")

# 1. 한국 시간(KST) 기준 어제 날짜 계산 (선택 가능한 최대 날짜)
kst = timezone(timedelta(hours=9))
today_kst = datetime.datetime.now(kst).date()
max_allowed_date = today_kst - timedelta(days=1)  # 오늘 건 집계 전이므로 어제까지 선택 가능

# 2. 사이드바 또는 메인 화면에 달력 날짜 선택 UI 구성
selected_date = st.date_input(
    "📅 조회할 날짜를 선택하세요 (어제 날짜까지 선택 가능)",
    value=max_allowed_date,
    max_value=max_allowed_date
)

# API 요청용 yyyymmdd 형식 문자열
target_date_str = selected_date.strftime("%Y%m%d")
display_date_str = selected_date.strftime("%Y년 %m월 %d일")

st.write(f"🔍 **조회 기준 일자:** {display_date_str}")


# 3. API 호출 함수 (1시간 캐싱 적용)
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
            return None, "그날은 아직 집계 전입니다."
            
        return movie_list, None

    except Exception as e:
        return None, f"데이터를 불러오는 중 예외가 발생했습니다: {str(e)}"


# 4. Streamlit Secrets에서 API 키 가져오기
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
        # 영화 목록이 비어있거나 집계 전인 경우
        if error_message == "그날은 아직 집계 전입니다.":
            st.warning(f"ℹ️ **{error_message}**")
        else:
            st.error(f"🚨 **데이터를 가져오지 못했습니다.**")
            st.warning(f"**상세 원인:** {error_message}")
            st.info("""
            **💡 해결 가이드:**
            * API 키가 올바르게 입력되었는지 확인하세요 (공백 주의).
            * 영화진흥위원회(KOBIS) 개발자 센터에서 일일 호출한도가 초과되지 않았는지 확인하세요.
            """)
    else:
        # 5. 데이터 가공 및 수치형 변환
        df = pd.DataFrame(movie_list)
        
        # 문자열 데이터를 정수형(int) 데이터로 변환
        numeric_columns = ["rank", "audiCnt", "audiAcc", "scrnCnt", "rankInten", "showCnt"]
        for col in numeric_columns:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(int)

        # 6. 순위 증감(rankInten) 및 누적관객 100만 이상 트로피 서식 가공
        def format_movie_name(row):
            title = row["movieNm"]
            # 누적관객이 100만 명(1,000,000) 이상이면 트로피 이모지 부착
            if row["audiAcc"] >= 1_000_000:
                title = f"🏆 {title}"
            return title

        def format_rank_change(inten):
            if inten > 0:
                # 오른 영화: 빨간 위 화살표
                return f"🔺 +{inten}"
            elif inten < 0:
                # 내린 영화: 파란 아래 화살표
                return f"🔹 {inten}"
            else:
                return "-"

        df["formatted_movieNm"] = df.apply(format_movie_name, axis=1)
        df["formatted_rankInten"] = df["rankInten"].apply(format_rank_change)

        # 7. 1위 영화 지표 카드 표시 (st.metric 사용)
        top_1 = df[df["rank"] == 1].iloc[0]
        st.subheader(f"🥇 오늘의 1위: {top_1['formatted_movieNm']}")
        
        col1, col2, col3 = st.columns(3)
        col1.metric("일일 관객수", f"{top_1['audiCnt']:,} 명", delta=top_1['formatted_rankInten'])
        col2.metric("누적 관객수", f"{top_1['audiAcc']:,} 명")
        col3.metric("스크린수", f"{top_1['scrnCnt']:,} 개")

        st.divider()

        # 8. 상위 5개 영화 관객수 막대그래프
        st.subheader("📊 관객수 상위 5개 영화")
        top_5_df = df.sort_values(by="rank").head(5)
        
        # 막대그래프용 데이터셋 (영화명에 트로피 반영)
        chart_data = top_5_df.set_index("formatted_movieNm")[["audiCnt"]]
        chart_data.columns = ["일일 관객수"]
        st.bar_chart(chart_data)

        st.divider()

        # 9. 전체 박스오피스 순위 표
        st.subheader("📋 전체 박스오피스 순위")
        
        # 표시할 컬럼 정리 및 이름 변경
        display_df = df[["rank", "formatted_rankInten", "formatted_movieNm", "openDt", "audiCnt", "audiAcc", "scrnCnt"]].copy()
        display_df.columns = ["순위", "순위증감", "영화명", "개봉일", "관객수", "누적관객", "스크린수"]
        
        # 천 단위 쉼표 포맷 적용 후 테이블 출력
        st.dataframe(
            display_df.style.format({
                "관객수": "{:,}",
                "누적관객": "{:,}",
                "스크린수": "{:,}"
            }),
            use_container_width=True,
            hide_index=True
        )
