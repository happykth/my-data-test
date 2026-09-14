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

# 이 그래프로 알 수 있는 것을 직접 입력할 수 있는 칸
st.text_area(
    "📌 이 그래프로 알 수 있는 것",
    placeholder="이 그래프를 보고 알 수 있는 점을 한 문장으로 적어보세요.",
    key="insight_1",
)

st.divider()

# ==============================================================
# 구역 2. 관객수 상위 5편의 날짜별 변화 비교
# ==============================================================
st.header("구역 2. 관객수 상위 5편의 날짜별 변화 비교")

# 기간 전체 일관객 합계 기준 상위 5편 선정
top5_movies = (
    df.groupby("영화명")["일관객"].sum().sort_values(ascending=False).head(5).index.tolist()
)

top5_df = df[df["영화명"].isin(top5_movies)].sort_values("날짜")

fig2 = px.line(
    top5_df,
    x="날짜",
    y="일관객",
    color="영화명",
    markers=True,
    title="일관객 합계 상위 5편의 날짜별 일일 관객수",
    color_discrete_sequence=WARM_COLORS,
    category_orders={"영화명": top5_movies},
)
fig2.update_traces(
    hovertemplate="%{fullData.name}<br>날짜: %{x|%Y-%m-%d}<br>일일 관객수: %{y:,}명<extra></extra>"
)
fig2.update_layout(
    xaxis_title="날짜",
    yaxis_title="일일 관객수(명)",
    hovermode="x unified",
    legend_title_text="영화명 (클릭해서 켜고 끄기)",
)

st.plotly_chart(fig2, use_container_width=True)

st.text_area(
    "📌 이 그래프로 알 수 있는 것",
    placeholder="이 그래프를 보고 알 수 있는 점을 한 문장으로 적어보세요.",
    key="insight_2",
)

st.divider()

# ==============================================================
# 구역 3. 날짜별 박스오피스 10위권 총 관객수
# ==============================================================
st.header("구역 3. 날짜별 박스오피스 10위권 총 관객수")

daily_total = df.groupby("날짜")["일관객"].sum().reset_index()

fig3 = px.area(
    daily_total,
    x="날짜",
    y="일관객",
    title="날짜별 박스오피스 10위권 총 관객수",
    color_discrete_sequence=[WARM_COLORS[2]],
)
fig3.update_traces(
    hovertemplate="날짜: %{x|%Y-%m-%d}<br>총 관객수: %{y:,}명<extra></extra>"
)
fig3.update_layout(
    xaxis_title="날짜",
    yaxis_title="10위권 총 관객수(명)",
    hovermode="x unified",
)

# 총 관객수가 가장 컸던 3일 표시
top3_days = daily_total.sort_values("일관객", ascending=False).head(3)

for _, row in top3_days.iterrows():
    fig3.add_annotation(
        x=row["날짜"],
        y=row["일관객"],
        text=row["날짜"].strftime("%Y-%m-%d"),
        showarrow=True,
        arrowhead=2,
        ax=0,
        ay=-40,
        font=dict(color=WARM_COLORS[3]),
        bgcolor="rgba(255,255,255,0.8)",
    )

fig3.add_scatter(
    x=top3_days["날짜"],
    y=top3_days["일관객"],
    mode="markers",
    marker=dict(color=WARM_COLORS[0], size=12, symbol="star"),
    hovertemplate="날짜: %{x|%Y-%m-%d}<br>총 관객수: %{y:,}명<extra></extra>",
    showlegend=False,
    name="",
)

st.plotly_chart(fig3, use_container_width=True)

st.text_area(
    "📌 이 그래프로 알 수 있는 것",
    placeholder="이 그래프를 보고 알 수 있는 점을 한 문장으로 적어보세요.",
    key="insight_3",
)

st.divider()

# ==============================================================
# 구역 4. 누적 관객수 TOP 10 영화
# ==============================================================
st.header("구역 4. 누적 관객수 TOP 10 영화")

movie_summary = (
    df.groupby("영화명")
    .agg(총관객=("일관객", "sum"), 순위진입일수=("날짜", "count"))
    .reset_index()
)
top10_movies = movie_summary.sort_values("총관객", ascending=False).head(10)
# 관객 많은 영화가 위로 가도록 정렬 (막대그래프는 아래→위 순서라 오름차순으로 뒤집어줌)
top10_movies = top10_movies.sort_values("총관객", ascending=True)

fig4 = px.bar(
    top10_movies,
    x="총관객",
    y="영화명",
    orientation="h",
    title="이 기간 일관객 합계 TOP 10 영화",
    color_discrete_sequence=[WARM_COLORS[4]],
    custom_data=["순위진입일수"],
)
fig4.update_traces(
    hovertemplate="%{y}<br>총 관객수: %{x:,}명<br>10위권 진입 일수: %{customdata[0]}일<extra></extra>"
)
fig4.update_layout(
    xaxis_title="총 관객수(명)",
    yaxis_title="",
)

st.plotly_chart(fig4, use_container_width=True)

st.text_area(
    "📌 이 그래프로 알 수 있는 것",
    placeholder="이 그래프를 보고 알 수 있는 점을 한 문장으로 적어보세요.",
    key="insight_4",
)
