import streamlit as st
import numpy as np
import cv2

# 1. 가상의 로그 데이터 세팅 (상태 관리를 위해 세션 내에 보존)
if "mock_logs" not in st.session_state:
    st.session_state.mock_logs = [
        {"id": "LOG-01", "tab": "위험", "time": "14:20:05", "channel": "CCTV 1대 (1공구)", "desc": "작업자 추락 의심 상황 발생", "status": "대기 중", "media_type": "video", "feedback": ""},
        {"id": "LOG-02", "tab": "위험", "time": "16:42:10", "channel": "CCTV 3대 (적재구역)", "desc": "지게차 충돌 위험 감지", "status": "대기 중", "media_type": "video", "feedback": ""},
        {"id": "LOG-03", "tab": "경고", "time": "09:15:22", "channel": "CCTV 2대 (안전통로)", "desc": "안전모 미착용 작업자 발견", "status": "대기 중", "media_type": "image", "status": "대기 중", "feedback": ""},
        {"id": "LOG-04", "tab": "경고", "time": "11:30:12", "channel": "CCTV 4대 (외곽펜스)", "desc": "안전조끼 미착용 작업자 발견", "status": "대기 중", "media_type": "image", "status": "대기 중", "feedback": ""},
        {"id": "LOG-05", "tab": "피드백", "time": "10:05:43", "channel": "CCTV 1대 (1공구)", "desc": "미탐지 신고 접수 (추락)", "status": "대기 중", "media_type": "image", "status": "대기 중", "feedback": ""},
    ]

# 현재 어떤 로그가 선택되어 있는지 추적하기 위한 세션 변수 (기본값은 첫 번째 로그)
if "selected_log_id" not in st.session_state:
    st.session_state.selected_log_id = st.session_state.mock_logs[0]["id"]

# 2. 와이어프레임에 맞춘 노란색 테두리 및 카드 스타일 전용 CSS 주입
st.markdown("""
    <style>
    /* 기본 카드 스타일 (무채색) */
    .log-card {
        background-color: #1e293b;
        border: 2px solid #334155;
        border-radius: 10px;
        padding: 15px;
        margin-bottom: 12px;
        color: #f1f5f9;
    }
    /* 그림 그리신 것처럼 선택된 카드만 노란색 테두리로 강조 */
    .log-card-selected {
        background-color: #0f172a;
        border: 2px solid #FFD700 !important; /* 노란색 굵은 테두리 */
        border-radius: 10px;
        padding: 15px;
        margin-bottom: 12px;
        color: #ffffff;
        box-shadow: 0px 0px 10px rgba(255, 215, 0, 0.3);
    }
    .card-header {
        font-size: 14px;
        color: #94a3b8;
        display: flex;
        justify-content: space-between;
        margin-bottom: 5px;
    }
    .card-body {
        font-size: 16px;
        font-weight: bold;
    }
    </style>
""", unsafe_allow_html=True)

st.title("📈 위험/경고 로그 및 모델 피드백 관제소")

# --- 🖥️ 와이어프레임 기반 2분할 레이아웃 (좌: 45% / 우: 55%) ---
col_left, col_right = st.columns([45, 55])

# ⬅️ [좌측 구역] 위험, 경고, 피드백 구역 나누기 및 카드 리스트
with col_left:
    st.subheader("📋 관제 로그 목록")
    
    # 3개의 카테고리 구역 나누기 (상단 탭)
    tab_danger, tab_warn, tab_feedback = st.tabs(["🚨 위험 (사고)", "⚠️ 경고 (미착용)", "🔍 피드백 (미탐지)"])
    
    # 각 탭에 맞춰서 보여줄 로그 필터링 규칙 정의
    def render_log_cards(target_tab_name):
        filtered_logs = [log for log in st.session_state.mock_logs if log["tab"] == target_tab_name]
        
        if not filtered_logs:
            st.info("이 카테고리에 대기 중인 로그가 없습니다.")
            return

        for log in filtered_logs:
            # 현재 이 카드가 사용자가 선택한 카드인지 판별
            is_selected = (log["id"] == st.session_state.selected_id_tracker)
            card_style = "log-card-selected" if is_selected else "log-card"
            
            # HTML로 카드 커스텀 디자인 렌더링
            st.markdown(f"""
                <div class="{card_style}">
                    <div class="card-header">
                        <span>🕒 {log['time']} | {log['channel']}</span>
                        <span style="color: {'#FFD700' if is_selected else '#38bdf8'}; font-weight:bold;">[{log['status']}]</span>
                    </div>
                    <div class="card-body">
                        {log['desc']}
                    </div>
                </div>
            """, unsafe_allow_html=True)
            
            # 카드를 클릭해서 바꿀 수 있도록 카드 밑에 작은 선택 버튼 배치
            if st.button(f"👉 {log['id']} 선택하기", key=f"btn_select_{log['id']}", use_container_width=True):
                st.session_state.selected_id_tracker = log["id"]
                st.rerun()

    # 각 탭 안을 그리기 전, 세션 값이 유실되지 않도록 트래커 변수 확보
    if "selected_id_tracker" not in st.session_state:
        st.session_state.selected_id_tracker = st.session_state.selected_log_id

    with tab_danger:
        render_log_cards("위험")
    with tab_warn:
        render_log_cards("경고")
    with tab_feedback:
        render_log_cards("피드백")


# ➡️ [우측 구역] 미디어 플레이어 + 한 줄 피드백 칸
with col_right:
    st.subheader("🔍 실시간 로그 데이터 검증")
    
    # 현재 선택된 로그 객체 찾기
    current_log = next((log for log in st.session_state.mock_logs if log["id"] == st.session_state.selected_id_tracker), None)
    
    if current_log:
        st.info(f"선택된 파일 코드: **{current_log['id']}** | 위치: **{current_log['channel']}**")
        
        # 1. 와이어프레임의 상단: 동영상/이미지 플레이어 영역
        if current_log["media_type"] == "video":
            st.markdown("#### 📹 사고 녹화 영상 플레이어")
            # 가상 비디오 프레임 그리기
            img = np.zeros((360, 640, 3), dtype=np.uint8) + 50
            cv2.rectangle(img, (10, 10), (630, 350), (0, 0, 255), 6)
            cv2.putText(img, f"VIDEO: {current_log['id']}", (50, 160), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 255, 255), 2)
            cv2.putText(img, "▶ Click to view (Simulation)", (50, 210), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            st.image(cv2.cvtColor(img, cv2.COLOR_BGR2RGB), use_container_width=True)
        else:
            st.markdown("#### 📸 알림 스냅샷 이미지")
            img = np.zeros((360, 640, 3), dtype=np.uint8) + 70
            cv2.rectangle(img, (10, 10), (630, 350), (0, 255, 255), 6)
            cv2.putText(img, f"IMAGE: {current_log['id']}", (50, 180), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 255, 255), 2)
            st.image(cv2.cvtColor(img, cv2.COLOR_BGR2RGB), use_container_width=True)
            
        st.markdown("---")
        
        # 2. 와이어프레임의 하단: 정탐/오탐/공유 버튼 묶음 및 한 줄 피드백 칸
        st.markdown("#### ✍️ 탐지 결과 판정 및 피드백")
        
        # 가로로 버튼 3개 배치
        btn_col1, btn_col2, btn_col3 = st.columns(3)
        if btn_col1.button("🎯 정탐 (True)", use_container_width=True, key=f"t_{current_log['id']}"):
            current_log["status"] = "정탐"
            st.rerun()
        if btn_col2.button("❌ 오탐 (False)", use_container_width=True, key=f"f_{current_log['id']}"):
            current_log["status"] = "오탐"
            st.rerun()
        if btn_col3.button("📤 현장 공유", use_container_width=True, key=f"s_{current_log['id']}"):
            st.toast("현장 안전 관리자 앱으로 데이터를 전송했습니다.")
            
        # 한 줄 피드백 쓸 수 있는 칸
        feedback_input = st.text_input(
            "피드백 간단하게 한 줄 메모", 
            value=current_log["feedback"],
            placeholder="여기에 모델 오인식 사유나 특이사항을 적으세요.",
            key=f"input_{current_log['id']}"
        )
        
        if st.button("💾 피드백 및 판정 저장", type="primary", use_container_width=True, key=f"save_{current_log['id']}"):
            current_log["feedback"] = feedback_input
            
            # 이전 단계에서 만든 백엔드 파일 연동
            import feedback_manager
            feedback_manager.save_user_feedback(
                log_id=current_log['id'],
                channel=current_log['channel'],
                event_type=current_log['desc'],
                status=current_log['status'],
                feedback_text=feedback_input
            )
            st.toast("가상 DB(CSV)에 피드백이 영구 기록되었습니다!", icon="💾")
            st.rerun()
