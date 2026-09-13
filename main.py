import streamlit as st
import pandas as pd
import plotly.express as px

# ------------------------------------------------------------
# 기본 설정
# ------------------------------------------------------------
st.set_page_config(
    page_title="영화 데이터 그래프 도감 1 - 시간",
    page_icon="🎬",
    layout="wide",
)

DATA_URL = "https://raw.githubusercontent.com/greatsong/modudata/main/data/kobis_daily.csv"

# 따뜻한 색감 팔레트
WARM_COLORS = ["#E07A5F", "#F2CC8F", "#81B29A", "#3D405B", "#BC6C25"]


@st.cache_data
def load_data():
    df = pd.read_csv(DATA_URL)
    # 날짜(하이픈 없는 여덟 자리 숫자) -> 진짜 날짜 타입으로 변환
    df["날짜"] = pd.to_datetime(df["날짜"].astype(str), format="%Y%m%d")
    return df


df = load_data()

st.title("🎬 영화 데이터 그래프 도감 1 - 시간")
st.caption("KOBIS 일별 박스오피스 데이터를 시간의 흐름에 따라 살펴보는 그래프 모음집이에요.")

st.divider()

# ==============================================================
# 구역 1. 영화별 일별 관객수 변화
# ==============================================================
st.header("구역 1. 영화별 일별 관객수 변화")

movie_list = sorted(df["영화명"].unique())
selected_movie = st.selectbox("영화를 선택하세요", movie_list, key="movie_select_1")

movie_df = df[df["영화명"] == selected_movie].sort_values("날짜")

fig1 = px.line(
    movie_df,
    x="날짜",
    y="일관객",
    markers=True,
    title=f"'{selected_movie}'의 날짜별 일일 관객수 변화",
    color_discrete_sequence=[WARM_COLORS[0]],
)
fig1.update_traces(
    hovertemplate="날짜: %{x|%Y-%m-%d}<br>일일 관객수: %{y:,}명<extra></extra>"
)
fig1.update_layout(
    xaxis_title="날짜",
    yaxis_title="일일 관객수(명)",
    hovermode="x unified",
)

st.plotly_chart(fig1, use_container_width=True)

# TODO: 이 그래프로 알 수 있는 것을 여기에 한 문장으로 작성하세요.
st.info("📌 이 그래프로 알 수 있는 것: ")

st.divider()

# ==============================================================
# 구역 2. (다음 그래프를 추가할 자리)
# ==============================================================
# st.header("구역 2. ")
#
# (여기에 두 번째 그래프 코드를 추가하세요)
#
# st.info("📌 이 그래프로 알 수 있는 것: ")
#
# st.divider()

# ==============================================================
# 구역 3. (다음 그래프를 추가할 자리)
# ==============================================================
# st.header("구역 3. ")
#
# (여기에 세 번째 그래프 코드를 추가하세요)
#
# st.info("📌 이 그래프로 알 수 있는 것: ")
