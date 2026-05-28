import streamlit as st
import numpy as np
import cv2

# --- 1. 세션 상태 및 가상 데이터 초기화 ---
if "mock_logs" not in st.session_state:
    st.session_state.mock_logs = [
        {"id": "LOG-01", "tab": "위험", "time": "5/28 14:20:05", "channel": "CCTV 1대 (1공구)", "desc": "작업자 추락 의심 상황 발생", "status": "대기중", "media_type": "video", "feedback": ""},
        {"id": "LOG-02", "tab": "위험", "time": "5/28 16:42:10", "channel": "CCTV 3대 (적재구역)", "desc": "지게차 충돌 위험 감지", "status": "대기중", "media_type": "video", "feedback": ""},
        {"id": "LOG-03", "tab": "경고", "time": "5/28 09:15:22", "channel": "CCTV 2대 (안전통로)", "desc": "안전모 미착용 작업자 발견", "status": "대기중", "media_type": "image", "feedback": ""},
        {"id": "LOG-04", "tab": "경고", "time": "5/28 11:30:12", "channel": "CCTV 4대 (외곽펜스)", "desc": "안전조끼 미착용 작업자 발견", "status": "대기중", "media_type": "image", "feedback": ""},
        {"id": "LOG-05", "tab": "피드백", "time": "5/28 10:05:43", "channel": "CCTV 1대 (1공구)", "desc": "미탐지 신고 접수 (추락)", "status": "대기중", "media_type": "image", "feedback": ""}
    ]

if "selected_id_tracker" not in st.session_state:
    st.session_state.selected_id_tracker = st.session_state.mock_logs[0]["id"]

# --- 2. 카드 및 하이라이트 스타일 전용 CSS 주입 ---
st.markdown("""
    <style>
    /* 카드가 감싸고 있는 뼈대 스타일 보정 */
    [data-testid="stExpander"] {
        border: none !important;
        background: transparent !important;
        box-shadow: none !important;
    }
    
    /* 선택되지 않은 일반 카드 컨테이너 */
    .log-card-box {
        background-color: #1e293b;
        border: 2px solid #334155;
        border-radius: 6px;
        padding: 12px 16px;
        color: #f1f5f9;
    }
    
    /* 와이어프레임 핵심: 선택된 카드의 노란색 테두리 하이라이트 */
    .log-card-box-selected {
        background-color: #0f172a;
        border: 2px solid #FFD700 !important;
        border-radius: 6px;
        padding: 12px 16px;
        color: #ffffff;
        box-shadow: 0px 0px 10px rgba(255, 215, 0, 0.2);
    }
    
    .card-meta-line {
        font-size: 13px;
        color: #94a3b8;
        margin-bottom: 4px;
    }
    
    .card-title-line {
        font-size: 15px;
        font-weight: bold;
    }
    
    /* 대기중 초록색 테두리 뱃지 스타일 */
    .green-status-badge {
        border: 2px solid #22c55e;
        color: #22c55e;
        padding: 4px 10px;
        border-radius: 4px;
        font-weight: bold;
        font-size: 13px;
        text-align: center;
        display: inline-block;
    }
    
    .gray-status-badge {
        border: 2px solid #94a3b8;
        color: #94a3b8;
        padding: 4px 10px;
        border-radius: 4px;
        font-weight: bold;
        font-size: 13px;
        text-align: center;
        display: inline-block;
    }
    
    /* 기본 스트림릿 라디오/체크박스 패딩 보정 */
    div[data-testid="stHorizontalBlock"] {
        align-items: center !important;
    }
    </style>
""", unsafe_allow_html=True)

st.title("📈 위험/경고 로그 및 모델 피드백 관제소")

# --- 🖥️ 2분할 레이아웃 (좌: 45% / 우: 55%) ---
col_left, col_right = st.columns([45, 55])

# ⬅️ [좌측 구역] 관제 로그 목록 구역
with col_left:
    st.subheader("📋 관제 로그 목록 (List view)")
    
    tab_danger, tab_warn, tab_feedback = st.tabs(["🚨 위험 (Danger)", "⚠️ 경고 (Warning)", "🔍 피드백 (Feedback)"])
    
    hide_completed = st.checkbox("⬛ 피드백 완료된 로그 숨기기", value=False)
    
    cctv_dropdown = st.selectbox(
        "📅 필터링 / 채널 선택",
        ["전체 채널 보기", "CCTV 1대 (1공구)", "CCTV 2대 (안전통로)", "CCTV 3대 (적재구역)", "CCTV 4대 (외곽펜스)"]
    )
    
    st.markdown("---")
    
    def render_log_cards(target_tab_name):
        if cctv_dropdown == "전체 채널 보기":
            filtered_logs = [log for log in st.session_state.mock_logs if log["tab"] == target_tab_name]
        else:
            filtered_logs = [log for log in st.session_state.mock_logs if log["tab"] == target_tab_name and cctv_dropdown == log['channel']]
        
        if hide_completed:
            filtered_logs = [log for log in filtered_logs if log["status"] == "대기중"]
            
        if not filtered_logs:
            st.info("이 카테고리/채널에 표시할 로그가 없습니다.")
            return

        for log in filtered_logs:
            is_selected = (log["id"] == st.session_state.selected_id_tracker)
            box_style = "log-card-box-selected" if is_selected else "log-card-box"
            badge_style = "green-status-badge" if log["status"] == "대기중" else "gray-status-badge"
            
            # 💡 [해결 포인트] 쌩 버튼 대신, 상단에는 정보를 HTML로 완벽히 렌더링하고
            # 바로 하단에 카드 너비와 똑같은 가로형 '선택 버튼'을 밀착 배치하여 에러를 완전히 차단합니다.
            st.markdown(f"""
                <div class="{box_style}">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <div>
                            <div class="card-meta-line">🕒 {log['time']} | {log['channel']}</div>
                            <div class="card-title-line">{log['desc']}</div>
                        </div>
                        <div>
                            <span class="{badge_style}">{log['status']}</span>
                        </div>
                    </div>
                </div>
            """, unsafe_allow_html=True)
            
            # 카드의 ID를 투명하게 품은 콤팩트한 선택 트리거 버튼
            if st.button(f"👆 {log['id']} 상시 검증 및 분석 활성화", key=f"trigger_{log['id']}", use_container_width=True):
                st.session_state.selected_id_tracker = log["id"]
                st.rerun()
                
            st.markdown('<div style="margin-bottom: 5px;"></div>', unsafe_allow_html=True)

    with tab_danger:
        render_log_cards("위험")
    with tab_warn:
        render_log_cards("경고")
    with tab_feedback:
        render_log_cards("피드백")

# ➡️ [우측 구역] 미디어 분석 및 피드백 (와이어프레임 100% 동기화 구역)
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
            cv2.putText(img, f"CCTV VIDEO: {current_log['id']}", (40, 180), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            st.image(cv2.cvtColor(img, cv2.COLOR_BGR2RGB), use_container_width=True)
        else:
            st.markdown("#### 📸 플레이어 (스냅샷 시뮬레이션)")
            img = np.zeros((360, 640, 3), dtype=np.uint8) + 60
            cv2.rectangle(img, (10, 10), (630, 350), (0, 255, 255), 5)
            cv2.putText(img, f"CCTV IMAGE: {current_log['id']}", (40, 180), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
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
        
        # 3. 판정 버튼 및 한 줄 메모 구역
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
            
        feedback_input = st.text_input(
            "📝 메모", 
            value=current_log["feedback"],
            placeholder="모델 오인식 사유나 현장 특이사항을 입력하세요.",
            key=f"input_{current_log['id']}"
        )
        
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
