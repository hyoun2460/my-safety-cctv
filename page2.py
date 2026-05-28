import streamlit as st
import numpy as np
import cv2

# --- 1. 세션 상태 및 가상 데이터 초기화 ---
if "mock_logs" not in st.session_state:
    st.session_state.mock_logs = [
        {"id": "LOG-01", "tab": "위험", "time": "5/28 09:15:22", "channel": "1공구", "desc": "작업자 추락 의심 상황 발생", "status": "대기중", "media_type": "video", "feedback": ""},
        {"id": "LOG-02", "tab": "위험", "time": "5/28 16:42:10", "channel": "적재구역", "desc": "지게차 충돌 위험 감지", "status": "대기중", "media_type": "video", "feedback": ""},
        {"id": "LOG-03", "tab": "경고", "time": "5/28 09:15:22", "channel": "안전통로", "desc": "안전모 미착용 작업자 발견", "status": "대기중", "media_type": "image", "feedback": ""},
        {"id": "LOG-04", "tab": "경고", "time": "5/28 11:30:12", "channel": "외곽펜스", "desc": "안전조끼 미착용 작업자 발견", "status": "대기중", "media_type": "image", "feedback": ""},
        {"id": "LOG-05", "tab": "피드백", "time": "5/28 10:05:43", "channel": "1공구", "desc": "미탐지 신고 접수 (추락)", "status": "대기중", "media_type": "image", "feedback": ""}
    ]

if "selected_id_tracker" not in st.session_state:
    st.session_state.selected_id_tracker = st.session_state.mock_logs[0]["id"]

# --- 2. Streamlit 버튼 자체를 카드로 개조하는 CSS 주입 ---
# 흰색 버튼이 따로 튀어나오는 현상을 원천적으로 막기 위해 버튼 자체의 레이아웃을 바꿉니다.
st.markdown("""
    <style>
    /* 1. 기본 로그 카드 스타일 (Streamlit 버튼을 전면 개조) */
    div.stButton > button[key^="card_"] {
        background-color: #1e293b !important;
        border: 2px solid #334155 !important;
        border-radius: 6px !important;
        padding: 15px 20px !important;
        color: #f1f5f9 !important;
        text-align: left !important;
        width: 100% !important;
        display: block !important;
        box-shadow: none !important;
        transition: all 0.15s ease-in-out;
    }
    
    /* 마우스 호버 효과 */
    div.stButton > button[key^="card_"]:hover {
        border-color: #475569 !important;
        background-color: #334155 !important;
    }

    /* 2. 와이어프레임 핵심: 선택된 카드의 노란색 테두리 강제 바인딩 */
    div.stButton > button[key^="card_"].selected-active {
        background-color: #0f172a !important;
        border: 2px solid #FFD700 !important;
        color: #ffffff !important;
        box-shadow: 0px 0px 10px rgba(255, 215, 0, 0.2) !important;
    }

    /* 카드 내부에 배치될 텍스트 및 뱃지 레이아웃 */
    .card-flex {
        display: flex;
        justify-content: space-between;
        align-items: center;
        width: 100%;
        pointer-events: none; /* 클릭 이벤트 방해 금지 */
    }
    .card-meta {
        font-size: 14px;
        color: #94a3b8;
    }
    .card-main-title {
        font-size: 15px;
        font-weight: bold;
        margin-top: 6px;
        color: #ffffff;
    }
    .status-badge-green {
        border: 2px solid #22c55e !important;
        color: #22c55e !important;
        padding: 4px 10px;
        border-radius: 4px;
        font-weight: bold;
        font-size: 13px;
    }
    .status-badge-gray {
        border: 2px solid #94a3b8 !important;
        color: #94a3b8 !important;
        padding: 4px 10px;
        border-radius: 4px;
        font-weight: bold;
        font-size: 13px;
    }
    </style>
""", unsafe_allow_html=True)

st.title("📈 위험/경고 로그 및 모델 피드백 관제소")

# --- 🖥️ 와이어프레임 구조의 2분할 레이아웃 (좌: 45% / 우: 55%) ---
col_left, col_right = st.columns([45, 55])

# ⬅️ [좌측 구역] 관제 로그 목록
with col_left:
    st.subheader("📋 관제 로그 목록 (List view)")
    
    tab_danger, tab_warn, tab_feedback = st.tabs(["🚨 위험 (Danger)", "⚠️ 경고 (Warning)", "🔍 피드백 (Feedback)"])
    
    hide_completed = st.checkbox("⬛ 피드백 완료된 로그 숨기기", value=False)
    
    cctv_dropdown = st.selectbox(
        "📅 필터링 / 채널 선택",
        ["전체 채널 보기", "1공구", "Safety Path", "적재구역", "외곽펜스"]
    )
    
    st.markdown("---")
    
    def render_log_cards(target_tab_name):
        if cctv_dropdown == "전체 채널 보기":
            filtered_logs = [log for log in st.session_state.mock_logs if log["tab"] == target_tab_name]
        else:
            filtered_logs = [log for log in st.session_state.mock_logs if log["tab"] == target_tab_name and cctv_dropdown in log['channel']]
        
        if hide_completed:
            filtered_logs = [log for log in filtered_logs if log["status"] == "대기중"]
            
        if not filtered_logs:
            st.info("이 카테고리/채널에 표시할 로그가 없습니다.")
            return

        for log in filtered_logs:
            is_selected = (log["id"] == st.session_state.selected_id_tracker)
            
            # 선택 여부에 따라 버튼에 동적으로 다른 CSS 클래스를 주입하기 위한 트릭
            if is_selected:
                st.markdown(f"""
                    <style>
                    div.stButton > button[key="card_{log['id']}"] {{
                        border: 2px solid #FFD700 !important;
                        background-color: #0f172a !important;
                        box-shadow: 0px 0px 10px rgba(255, 215, 0, 0.2) !important;
                    }}
                    </style>
                """, unsafe_allow_html=True)
            
            badge_html = f'<span class="status-badge-green">대기중</span>' if log["status"] == "대기중" else f'<span class="status-badge-gray">{log["status"]}</span>'
            
            # 버튼 내부에 들어갈 풍부한 텍스트 구조 정의 (완벽 복구)
            button_inside_html = f"""
                <div class="card-flex">
                    <div style="text-align: left;">
                        <div class="card-meta">🕒 {log['time']} | {log['channel']}</div>
                        <div class="card-main-title">{log['desc']}</div>
                    </div>
                    <div>
                        {badge_html}
                    </div>
                </div>
            """
            
            # [해결 핵심] 별도의 HTML 태그를 먼저 그리지 않고, 오직 '하나의 커스텀 버튼'만 생성하여 레이아웃을 완전히 통일합니다.
            if st.button(button_inside_html, key=f"card_{log['id']}", use_container_width=True):
                st.session_state.selected_id_tracker = log["id"]
                st.rerun()
                
            st.markdown('<div style="margin-bottom: 10px;"></div>', unsafe_allow_html=True)

    with tab_danger:
        render_log_cards("위험")
    with tab_warn:
        render_log_cards("경고")
    with tab_feedback:
        render_log_cards("피드백")

# ➡️ [우측 구역] 미디어 분석 및 피드백 (와이어프레임 우측 구조 100% 매칭)
with col_right:
    st.subheader("🔍 실시간 로그 데이터 검증")
    
    current_log = next((log for log in st.session_state.mock_logs if log["id"] == st.session_state.selected_id_tracker), None)
    
    if current_log:
        st.info(f"📄 파일 코드: **{current_log['id']}** | 위치: **{current_log['channel']}**")
        
        # 1. 플레이어 영역
        if current_log["media_type"] == "video":
            st.markdown("#### 📹 플레이어 (영상 시뮬레이션)")
            img = np.zeros((360, 640, 3), dtype=np.uint8) + 40
            cv2.rectangle(img, (10, 10), (630, 350), (0, 0, 255), 5)
            cv2.putText(img, f"CCTV VIDEO: {current_log['desc']}", (40, 180), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            st.image(cv2.cvtColor(img, cv2.COLOR_BGR2RGB), use_container_width=True)
        else:
            st.markdown("#### 📸 플레이어 (스냅샷 시뮬레이션)")
            img = np.zeros((360, 640, 3), dtype=np.uint8) + 60
            cv2.rectangle(img, (10, 10), (630, 350), (0, 255, 255), 5)
            cv2.putText(img, f"CCTV IMAGE: {current_log['desc']}", (40, 180), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            st.image(cv2.cvtColor(img, cv2.COLOR_BGR2RGB), use_container_width=True)
            
        st.markdown("---")
        
        # 2. 세부 데이터 요약 영역
        st.markdown("#### 📊 세부 데이터 요약")
        metadata = {
            "발생 시각": current_log['time'],
            "검출 구역": current_log['channel'],
            "AI 탐지 내용": current_log['desc'],
            "현재 상태": current_log['status']
        }
        st.json(metadata)
        
        st.markdown("---")
        
        # 3. 정탐 / 오탐 / 공유 가로 버튼 및 메모, 저장단 구조
        st.markdown("#### ✍️ 탐지 결과 판정 및 피드백")
        
        btn_col1, btn_col2, btn_col3 = st.columns(3)
        if btn_col1.button("🎯 정탐", use_container_width=True, key=f"tp_{current_log['id']}"):
            current_log["status"] = "정탐"
            st.rerun()
        if btn_col2.button("❌ 오탐", use_container_width=True, key=f"fp_{current_log['id']}"):
            current_log["status"] = "오탐"
            st.rerun()
        if btn_col3.button("📤 공유", use_container_width=True, key=f"share_{current_log['id']}"):
            st.toast(f"🚨 {current_log['id']} 관제 데이터가 현장 관리 본부로 공유되었습니다.")
            
        # 메모 입력창
        feedback_input = st.text_input(
            "📝 메모", 
            value=current_log["feedback"],
            placeholder="모델 오인식 사유나 현장 특이사항을 입력하세요.",
            key=f"input_{current_log['id']}"
        )
        
        # 최종 저장 버튼
        if st.button("💾 저장", type="primary", use_container_width=True, key=f"save_{current_log['id']}"):
            current_log["feedback"] = feedback_input
            import feedback_manager
            feedback_manager.save_user_feedback(
                log_id=current_log['id'],
                channel=current_log['channel'],
                event_type=current_log['desc'],
                status=current_log['status'],
                feedback_text=feedback_input
            )
            st.toast("피드백이 백엔드 파이프라인에 영구 기록되었습니다!", icon="💾")
            st.rerun()
