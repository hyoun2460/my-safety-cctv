import streamlit as st

st.set_page_config(
    page_title="산업안전 모니터링 시스템",
    page_icon="🚨",
    layout="wide"
)

# 1. 페이지 정의 (현재 존재하는 파일만 우선 등록)
page1 = st.Page("page1.py", title="실시간 CCTV 관제", icon="🎥")
page2 = st.Page("page2.py", title="모델 성능 개선 피드백", icon="📈")
page3 = st.Page("page3.py", title="새 클래스 학습 및 DB", icon="🔄")

# 2. 내비게이션 실행 (우선 1번 페이지만 사이드바에 나타납니다)
pg = st.navigation([page1, page2]) 
pg.run()
