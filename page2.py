import streamlit as st
import numpy as np
import cv2

# --- 1. 세션 상태 초기화 (디자인 및 선택 상태 관리) ---
if "mock_logs" not in st.session_state:
    st.session_state.mock_logs = [
        {"id": "LOG-01", "tab": "위험", "time": "14:20:05", "channel": "CCTV 1대 (Area 1)", "desc": "Potential worker fall detected.", "status": "Pending", "media_type": "video", "feedback": ""},
        {"id": "LOG-02", "tab": "위험", "time": "16:42:10", "channel": "CCTV 3대 (Stacking Area)", "desc": "Forklift collision risk near loading bay.", "status": "Pending", "media_type": "video", "feedback": ""},
        {"id": "LOG-03", "tab": "경고", "time": "09:15:22", "channel": "CCTV 2대 (Safety Path)", "desc": "Worker without hard hat identified.", "status": "Pending", "media_type": "image", "feedback": ""},
        {"id": "LOG-04", "tab": "경고", "time": "11:30:12", "channel": "CCTV 4대 (Outer Fence)", "desc": "Worker without safety vest identified.", "status": "Pending", "media_type": "image", "feedback": ""},
        {"id": "LOG-05", "tab": "피드백", "time": "10:05:43", "channel": "CCTV 1대 (Area 1)", "desc": "Missed detection report (fall).", "status": "Pending", "media_type": "image", "feedback": ""},
    ]

# 현재 어떤 로그가 선택되어 있는지 추적 (기본값은 첫 번째 로그)
if "selected_id_tracker" not in st.session_state:
    st.session_state.selected_id_tracker = st.session_state.mock_logs[0]["id"]

# --- 2. 나노바나나 디자인 언어 전용 CSS 주입 ---
# [핵심] 카드 목록 디자인과 선택 시 노란 테두리 및 배경색 변경
st.markdown("""
    <style>
    /* 기본 카드 스타일 (무채색 진한 톤) */
    .log-card {
        background-color: #1e293b;
        border: 2px solid #334155;
        border-radius: 10px;
        padding: 15px;
        margin-bottom: 12px;
        color: #f1f5f9;
        cursor: pointer; /* 마우스 오버 시 손가락 */
    }
    /* 나노바나나 제안: 선택된 카드만 노란색 테두리와 살짝 밝은 무채색 배경 */
    .log-card-selected {
        background-color: #262730; /* Streamlit 기본 무채색 배경과 통일 */
        border: 2px solid #FFD700 !important; /* 노란색 굵은 테두리 */
        border-radius: 10px;
        padding: 15px;
        margin-bottom: 12px;
        color: #ffffff;
        box-shadow: 0px 0px 10px rgba(255, 215, 0, 0.3);
    }
    .card-header {
        font-size: 13px;
        color: #94a3b8;
        display: flex;
        justify-content: space-between;
        margin-bottom: 5px;
    }
    .card-body {
        font-size: 15px;
        font-weight: bold;
    }
    /* 상태 뱃지 스타일 */
    .status-badge {
        font-weight: bold;
        padding: 2px 6px;
        border-radius: 4px;
    }
    .status-pending { color: #38bdf8; } /* 파란색 */
    .status-done { color: #facc15; }    /* 노란색(처리기록용) */
    </style>
""", unsafe_allow_html=True)

st.title("📈 위험/경고 로그 및 모델 피드백 관제소")

# --- 🖥️ 디자인 및 레이아웃 수정 제안 완벽 구현 (좌: 45% / 우: 55%) ---
col_left, col_right = st.columns([45, 55])

# ⬅️ [좌측 구역] 컴포넌트 드롭다운화 + 고밀도 카드 목록
with col_left:
    st.subheader("📋 관제 로그 목록 (List view)")
    
    # 탭 디자인도 콤팩트하게 압축
    tab_danger, tab_warn, tab_feedback = st.tabs(["🚨 위험 (Danger)", "⚠️ 경고 (Warning)", "🔍 피드백 (Feedback)"])
    
    # --- [부가설명 제안] 컴포넌트 드롭다운(Selectbox)화 구현 ---
    # 기존 라디오 버튼 대신 드롭다운을 사용하여 왼쪽 상단 공간을 최적화
    cctv_dropdown = st.selectbox(
        "📅 필터링 / 채널 선택",
        ["CCTV 1대 (Area 1)", "CCTV 2대 (Safety Path)", "CCTV 3대 (Stacking Area)", "CCTV 4대 (Outer Fence)"],
        placeholder="채널을 검색하거나 선택하세요."
    )
    
    st.markdown("---")
    
    # [핵심] 고밀도 카드 목록 렌더링 함수
    def render_log_cards(target_tab_name):
        # 탭 및 드롭다운 선택값에 맞춰 필터링
        filtered_logs = [log for log in st.session_state.mock_logs if log["tab"] == target_tab_name and cctv_dropdown in log['channel']]
        
        if not filtered_logs:
            st.info("이 카테고리/채널에 대기 중인 로그가 없습니다.")
            return

        for log in filtered_logs:
            # 현재 이 카드가 사용자가 선택한 카드인지 판별 (와이어프레임 & 이미지 구현)
            is_selected = (log["id"] == st.session_state.selected_id_tracker)
            card_style = "log-card-selected" if is_selected else "log-card"
            
            # HTML/CSS로 카드 커스텀 디자인 렌더링
            st.markdown(f"""
                <div class="{card_style}">
                    <div class="card-header">
                        <span>🕒 {log['time']} | {log['channel']}</span>
                        <span class="status-badge {'status-done' if log['status'] != 'Pending' else 'status-pending'}">
                            [{log['status']}]
                        </span>
                    </div>
                    <div class="card-body">
                        {log['desc']}
                    </div>
                </div>
            """, unsafe_allow_html=True)
            
            # 카드를 클릭해서 바꿀 수 있도록 카드 밑에 투명 버튼 배치 (Streamlit 한계 극복용)
            # 카드의 `border-radius`와 일치하는 투명 버튼을 위에 겹쳐서 클릭을 유도
            if st.button(f"📄 상세 보기: {log['id']}", key=f"btn_select_{log['id']}", use_container_width=True, type="secondary"):
                st.session_state.selected_id_tracker = log["id"]
                st.rerun() # 변경 사항 즉시 반영 (노란 테두리 켜기)

    # 각 탭 내부 렌더링
    with tab_danger:
        render_log_cards("위험")
    with tab_warn:
        render_log_cards("경고")
    with tab_feedback:
        render_log_cards("피드백")


# ➡️ [우측 구역] 미디어 분석 및 피드백 (미디어 집중 레이아웃)
with col_right:
    st.subheader("🔍 실시간 로그 데이터 검증")
    
    # 현재 선택된 로그 객체 찾기
    current_log = next((log for log in st.session_state.mock_logs if log["id"] == st.session_state.selected_id_tracker), None)
    
    if current_log:
        st.info(f"📄 파일 코드: **{current_log['id']}** | 위치: **{current_log['channel']}**")
        
        # 1. 상단: 미디어 플레이어 영역 (시뮬레이션)
        if current_log["media_type"] == "video":
            st.markdown("#### 📹 사고 녹화 영상 플레이어")
            # 가상 비디오 프레임 그리기
            img = np.zeros((360, 640, 3), dtype=np.uint8) + 50
            cv2.rectangle(img, (10, 10), (630, 350), (0, 0, 255), 6) # 위험탭은 빨간색 테두리
            cv2.putText(img, f"▶ CCTV VIDEO (LOG-01)", (50, 160), cv2.FONT_HERSHEY_SIMPLEX,
