import streamlit as st
import numpy as np
import cv2
import datetime

# 가상의 로그 데이터 생성 (실제 구현 시에는 이 데이터가 SQLite DB나 로그 폴더에서 로드됩니다)
if "mock_logs" not in st.session_state:
    st.session_state.mock_logs = {
        "위험 (사고)": [
            {"id": "D1", "time": "2026-05-28 09:15:22", "channel": "1번 채널", "type": "추락 사고 의심", "media_type": "video", "status": "대기 중", "feedback": ""},
            {"id": "D2", "time": "2026-05-27 16:42:10", "channel": "3번 채널", "type": "장비 충돌 사고", "media_type": "video", "status": "정탐 처리됨", "feedback": "장비 후진 중 작업자 충돌 확인"}
        ],
        "경고 (미착용)": [
            {"id": "W1", "time": "2026-05-28 10:20:05", "channel": "2번 채널", "type": "안전모 미착용", "media_type": "image", "status": "대기 중", "feedback": ""},
            {"id": "W2", "time": "2026-05-28 08:05:43", "channel": "4번 채널", "type": "안전조끼 미착용", "media_type": "image", "status": "오탐 처리됨", "feedback": "조끼 물체 오인식"}
        ],
        "피드백 (미탐지)": [
            {"id": "F1", "time": "2026-05-27 11:30:12", "channel": "1번 채널", "type": "추락 미탐지 피드백", "media_type": "image", "status": "대기 중", "feedback": ""},
            {"id": "F2", "time": "2026-05-26 14:15:55", "channel": "2번 채널", "type": "안전모 미탐지 피드백", "media_type": "image", "status": "대기 중", "feedback": ""}
        ]
    }

st.title("📈 위험/경고 로그 및 모델 피드백 관제소")
st.markdown("현장에서 감지된 이상 로그를 검토하고, 모델 개선을 위한 정탐/오탐 피드백을 기록합니다.")

# --- 🖥️ 화면 2분할 구조 설정 (좌측 45%, 우측 55%) ---
col_left, col_right = st.columns([45, 55])

# 가상 이미지 생성 함수 (실제 파일이 없을 때 우측 화면에 띄워줄 용도)
def get_mock_media(text, is_video=False):
    img = np.zeros((480, 640, 3), dtype=np.uint8) + 60  # 회색 배경
    # 경고창 레이아웃 느낌 내기
    color = (0, 0, 255) if "위험" in text or "사고" in text else (0, 255, 255)
    cv2.rectangle(img, (15, 15), (625, 465), color, 5)
    
    cv2.putText(img, f"[MEDIA PREVIEW]", (50, 80), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 255, 255), 2)
    cv2.putText(img, text, (50, 200), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
    cv2.putText(img, "※ 테스트용 가상 미디어 프레임", (50, 420), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (150, 150, 150), 1)
    
    if is_video:
        cv2.putText(img, "▶ VIDEO PLAYING (Simulation)", (50, 260), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        
    return cv2.cvtColor(img, cv2.COLOR_BGR2RGB)


# ⬅️ [좌측 구역] 로그 목록 및 피드백 입력창
with col_left:
    st.subheader("📋 관제 로그 카테고리")
    
    # 1. 기획하신대로 3개의 구역을 Tab으로 분리
    tab_danger, tab_warn, tab_feedback = st.tabs(["🚨 위험 로그 (사고)", "⚠️ 경고 로그 (미착용)", "🔍 미탐지 피드백"])
    
    selected_log = None
    category_key = ""
    
    # --- 위험 로그 탭 ---
    with tab_danger:
        category_key = "위험 (사고)"
        danger_list = st.session_state.mock_logs[category_key]
        # 라디오 버튼 형태로 로그 선택
        log_options = [f"[{log['status']}] {log['time']} | {log['channel']} - {log['type']}" for log in danger_list]
        if log_options:
            selected_idx = st.radio("위험 로그 목록을 선택하세요", range(len(log_options)), key="radio_danger")
            selected_log = danger_list[selected_idx]
            
    # --- 경고 로그 탭 ---
    with tab_warn:
        # 탭 전환 시 혼선 방지를 위해 라디오 버튼 선택 시 세션 상태와 연동되게끔 단독 처리 유도
        category_key_w = "경고 (미착용)"
        warn_list = st.session_state.mock_logs[category_key_w]
        log_options_w = [f"[{log['status']}] {log['time']} | {log['channel']} - {log['type']}" for log in warn_list]
        if log_options_w:
            selected_idx_w = st.radio("경고 로그 목록을 선택하세요", range(len(log_options_w)), key="radio_warn")
            # 복잡한 컨테이너 조건 없이 깔끔하게 매핑
            selected_log = warn_list[selected_idx_w]
            category_key = category_key_w
        warn_list = st.session_state.mock_logs[category_key_w]
        log_options_w = [f"[{log['status']}] {log['time']} | {log['channel']} - {log['type']}" for log in warn_list]
        if log_options_w:
            selected_idx_w = st.radio("경고 로그 목록을 선택하세요", range(len(log_options_w)), key="radio_warn")
            # 라디오가 서로 다른 탭에 있으므로, 현재 활성화되어 쳐다보고 있는 로그를 셋팅
            if st.container(): # 콘텐트 바인딩
                selected_log = warn_list[selected_idx_w]
                category_key = category_key_w

    # --- 미탐지 피드백 탭 ---
    with tab_feedback:
        category_key_f = "피드백 (미탐지)"
        fb_list = st.session_state.mock_logs[category_key_f]
        log_options_f = [f"[{log['status']}] {log['time']} | {log['channel']} - {log['type']}" for log in fb_list]
        if log_options_f:
            selected_idx_f = st.radio("미탐지 피드백 목록을 선택하세요", range(len(log_options_f)), key="radio_fb")
            selected_log = fb_list[selected_idx_f]
            category_key = category_key_f

    st.markdown("---")
    
    # 2. 피드백 입력 섹션 (선택한 로그가 있을 때 동적 표시)
    if selected_log:
        st.subheader("✍️ 데이터 피드백 입력")
        st.info(f"선택된 로그 ID: **{selected_log['id']}** ({selected_log['type']})")
        
        # 정탐, 오탐, 공유 가로 버튼 레이아웃
        btn_col1, btn_col2, btn_col3 = st.columns(3)
        
        if btn_col1.button("🎯 정탐 (True Positive)", use_container_width=True):
            selected_log['status'] = "정탐 처리됨"
            st.success("해당 로그가 정탐(실제 사고/경고)으로 분류되었습니다.")
            
        if btn_col2.button("❌ 오탐 (False Positive)", use_container_width=True):
            selected_log['status'] = "오탐 처리됨"
            st.error("해당 로그가 오탐(모델 에러)으로 분류되었습니다. (v3.0 재학습 데이터셋 후보)")
            
        if btn_col3.button("📤 현장 공유", use_container_width=True):
            st.toast("🚨 해당 관제 데이터가 안전관리 본부 및 현장 관리자에게 공유되었습니다.", icon="ℹ️")
            
        # 한 줄 피드백 입력창
        feedback_text = st.text_input(
            "모델 개선 및 현장 특이사항 메모 (한 줄 피드백)", 
            value=selected_log['feedback'],
            placeholder="예: 안전모가 아니라 흰색 두건인데 오인식함. / 실제 낙상 사고 매칭 완료."
        )
        
        if st.button("💾 피드백 저장", type="primary", use_container_width=True):
            selected_log['feedback'] = feedback_text
            st.toast("피드백 데이터가 가상 DB에 안전하게 기록되었습니다!", icon="✅")
            st.rerun() # 변경 사항 즉시 반영


# ➡️ [우측 구역] 미디어 확인 창 및 디테일 정보
with col_right:
    st.subheader("🔍 실시간 로그 미디어 확인")
    
    if selected_log:
        # 상단에 상태 카드 노출
        card_col1, card_col2 = st.columns(2)
        card_col1.metric("발생 시각", selected_log['time'].split(" ")[1])
        card_col2.metric("처리 상태", selected_log['status'])
        
        # 기획안 반영: 위험(사고) 구역은 동영상으로, 나머지는 이미지로 표출 유도
        if selected_log['media_type'] == "video":
            st.markdown("#### 📹 사고 전후 10초 녹화 영상 플레이어")
            # 💡 나중에 실제 mp4 파일이 준비되면 아래 주석을 풀고 사용하시면 됩니다.
            # st.video(f"data/logs/{selected_log['id']}.mp4")
            
            # 현재는 파일이 없으므로 시뮬레이션 프레임 매핑
            mock_img = get_mock_media(f"{selected_log['channel']} - {selected_log['type']}\n[10초 이벤트 비디오 파일 매핑 자리]", is_video=True)
            st.image(mock_img, use_container_width=True)
            
        else:
            st.markdown("#### 📸 알림 순간 포착 이미지")
            # 💡 나중에 실제 png/jpg 파일이 준비되면 아래 주석을 풀고 사용하시면 됩니다.
            # st.image(f"data/logs/{selected_log['id']}.png")
            
            mock_img = get_mock_media(f"{selected_log['channel']} - {selected_log['type']}\n[AI 추론 바운딩박스 오버레이 스냅샷]")
            st.image(mock_img, use_container_width=True)
            
        # 상세 요약 메타데이터 표출
        st.markdown("#### 📋 세부 메타데이터 요약")
        metadata = {
            "로그 고유 고드": selected_log['id'],
            "현장 감지 채널": selected_log['channel'],
            "이벤트 카테고리": category_key,
            "시스템 탐지 결과": selected_log['type'],
            "작성된 주석(피드백)": selected_log['feedback'] if selected_log['feedback'] else "등록된 피드백 없음"
        }
        st.json(metadata)
        
    else:
        st.info("왼쪽 목록에서 로그를 선택하시면 상세 화면과 영상/이미지를 확인할 수 있습니다.")
