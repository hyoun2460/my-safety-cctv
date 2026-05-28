import streamlit as st
import numpy as np
import cv2

# --- 1. 세션 상태 초기화 (오타 완벽 수정) ---
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

# --- 2. 디자인 전용 CSS 주입 ---
st.markdown("""
    <style>
    .log-card {
        background-color: #1e293b;
        border: 2px solid #334155;
        border-radius: 10px;
        padding: 15px;
        margin-bottom: 12px;
        color: #f1f5f9;
    }
    .log-card-selected {
        background-color: #262730;
        border: 2px solid #FFD700 !important;
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
    .status-badge {
        font-weight: bold;
        padding: 2px 6px;
        border-radius: 4px;
    }
    .status-pending { color: #38bdf8; }
    .status-done { color: #facc15; }
    </style>
""", unsafe_allow_html=True)

st.title("📈 위험/경고 로그 및 모델 피드백 관제소")

# --- 🖥️ 2분할 레이아웃 ---
col_left, col_right = st.columns([45, 55])

# ⬅️ [좌측 구역]
with col_left:
    st.subheader("📋 관제 로그 목록 (List view)")
    
    tab_danger, tab_warn, tab_feedback = st.tabs(["🚨 위험 (Danger)", "⚠️ 경고 (Warning)", "🔍 피드백 (Feedback)"])
    
    cctv_dropdown = st.selectbox(
        "📅 필터링 / 채널 선택",
        ["CCTV 1대 (Area 1)", "CCTV 2대 (Safety Path)", "CCTV 3대 (Stacking Area)", "CCTV 4대 (Outer Fence)"]
    )
    
    st.markdown("---")
    
    def render_log_cards(target_tab_name):
        filtered_logs = [log for log in st.session_state.mock_logs if log["tab"] == target_tab_name and cctv_dropdown in log['channel']]
        
        if not filtered_logs:
            st.info("이 카테고리/채널에 대기 중인 로그가 없습니다.")
            return

        for log in filtered_logs:
            is_selected = (log["id"] == st.session_state.selected_id_tracker)
            card_style = "log-card-selected" if is_selected else "log-card"
            
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
            
            if st.button(f"📄 상세 보기: {log['id']}", key=f"btn_select_{log['id']}", use_container_width=True):
                st.session_state.selected_id_tracker = log["id"]
                st.rerun()

    with tab_danger:
        render_log_cards("위험")
    with tab_warn:
        render_log_cards("경고")
    with tab_feedback:
        render_log_cards("피드백")

# ➡️ [우측 구역]
with col_right:
    st.subheader("🔍 실시간 로그 데이터 검증")
    
    current_log = next((log for log in st.session_state.mock_logs if log["id"] == st.session_state.selected_id_tracker), None)
    
    if current_log:
        st.info(f"📄 파일 코드: **{current_log['id']}** | 위치: **{current_log['channel']}**")
        
        if current_log["media_type"] == "video":
            st.markdown("#### 📹 사고 녹화 영상 플레이어")
            img = np.zeros((360, 640, 3), dtype=np.uint8) + 50
            cv2.rectangle(img, (10, 10), (630, 350), (0, 0, 255), 6)
            cv2.putText(img, f"▶ CCTV VIDEO ({current_log['id']})", (50, 160), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 255, 255), 2)
            st.image(cv2.cvtColor(img, cv2.COLOR_BGR2RGB), use_container_width=True)
        else:
            st.markdown("#### 📸 알림 스냅샷 이미지")
            img = np.zeros((360, 640, 3), dtype=np.uint8) + 70
            cv2.rectangle(img, (10, 10), (630, 350), (0, 255, 255), 6)
            cv2.putText(img, f"📸 CCTV IMAGE ({current_log['id']})", (50, 180), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 255, 255), 2)
            st.image(cv2.cvtColor(img, cv2.COLOR_BGR2RGB), use_container_width=True)
            
        st.markdown("---")
        st.markdown("#### ✍️ 탐지 결과 판정 및 피드백")
        
        btn_col1, btn_col2, btn_col3 = st.columns(3)
        if btn_col1.button("🎯 정탐 (True Pos.)", use_container_width=True, key=f"tp_{current_log['id']}"):
            current_log["status"] = "True Pos."
            st.rerun()
        if btn_col2.button("❌ 오탐 (False Pos.)", use_container_width=True, key=f"fp_{current_log['id']}"):
            current_log["status"] = "False Pos."
            st.rerun()
        if btn_col3.button("📤 현장 공유", use_container_width=True, key=f"share_{current_log['id']}"):
            st.toast("현장 안전 관리자 앱으로 데이터를 전송했습니다.")
            
        feedback_input = st.text_input(
            "피드백 간단하게 한 줄 메모", 
            value=current_log["feedback"],
            placeholder="예: 오인식 사유 / 실제 낙상 사고 매칭 완료.",
            key=f"input_{current_log['id']}"
        )
        
        if st.button("💾 피드백 및 판정 저장", type="primary", use_container_width=True, key=f"save_{current_log['id']}"):
            current_log["feedback"] = feedback_input
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
