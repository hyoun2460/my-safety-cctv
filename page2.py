import streamlit as st
import numpy as np
import cv2

# 가상의 로그 데이터 생성 (세션 상태 유지)
if "mock_logs" not in st.session_state:
    st.session_state.mock_logs = {
        "🚨 위험 로그 (사고)": [
            {"id": "D1", "time": "2026-05-28 09:15:22", "channel": "1번 채널", "type": "추락 사고 의심", "media_type": "video", "status": "대기 중", "feedback": ""},
            {"id": "D2", "time": "2026-05-27 16:42:10", "channel": "3번 채널", "type": "장비 충돌 사고", "media_type": "video", "status": "정탐 처리됨", "feedback": "장비 후진 중 작업자 충돌 확인"}
        ],
        "⚠️ 경고 로그 (미착용)": [
            {"id": "W1", "time": "2026-05-28 10:20:05", "channel": "2번 채널", "type": "안전모 미착용", "media_type": "image", "status": "대기 중", "feedback": ""},
            {"id": "W2", "time": "2026-05-28 08:05:43", "channel": "4번 채널", "type": "안전조끼 미착용", "media_type": "image", "status": "오탐 처리됨", "feedback": "조끼 물체 오인식"}
        ],
        "🔍 미탐지 피드백": [
            {"id": "F1", "time": "2026-05-27 11:30:12", "channel": "1번 채널", "type": "추락 미탐지 피드백", "media_type": "image", "status": "대기 중", "feedback": ""},
            {"id": "F2", "time": "2026-05-26 14:15:55", "channel": "2번 채널", "type": "안전모 미탐지 피드백", "media_type": "image", "status": "대기 중", "feedback": ""}
        ]
    }

st.title("📈 위험/경고 로그 및 모델 피드백 관제소")
st.markdown("현장에서 감지된 이상 로그를 검토하고, 모델 개선을 위한 정탐/오탐 피드백을 기록합니다.")

# --- 🖥️ 화면 2분할 구조 설정 (좌측 45%, 우측 55%) ---
col_left, col_right = st.columns([45, 55])

# 가상 이미지 생성 함수 (우측 렌더링용)
def get_mock_media(text, is_video=False):
    img = np.zeros((480, 640, 3), dtype=np.uint8) + 60  # 회색 배경
    color = (0, 0, 255) if "위험" in text or "사고" in text else (0, 255, 255)
    cv2.rectangle(img, (15, 15), (625, 465), color, 5)
    
    cv2.putText(img, f"[MEDIA PREVIEW]", (50, 80), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 255, 255), 2)
    cv2.putText(img, text, (50, 200), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
    cv2.putText(img, "※ 테스트용 가상 미디어 프레임", (50, 420), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (150, 150, 150), 1)
    
    if is_video:
        cv2.putText(img, "▶ VIDEO PLAYING (Simulation)", (50, 260), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        
    return cv2.cvtColor(img, cv2.COLOR_BGR2RGB)


# ⬅️ [좌측 구역] 로그 목록 및 피드백 입력창
with col_left:
    st.subheader("📋 관제 로그 카테고리")
    
    # 중복 위젯 에러를 막기 위해 상단 탭에서 카테고리 선택 후, 라디오 버튼은 '단 하나'만 렌더링되게 변경
    # --- page2.py 수정 예시 ---
    categories = ["🚨 위험 로그 (사고)", "⚠️ 경고 로그 (미착용)", "🔍 미탐지 피드백"]
    selected_tab = st.radio("검토할 카테고리를 선택하세요", categories, horizontal=True, key="main_category_tab")
    
    # 💡 [추가] 사이드바 또는 상단에 숨김 토글 스위치 배치
    hide_completed = st.checkbox("✅ 피드백 완료된 로그 숨기기", value=False)
    
    st.markdown("---")
    
    # 기본 데이터 리스트 가져오기
    raw_log_list = st.session_state.mock_logs[selected_tab]
    
    # 💡 [핵심] 사용자가 체크박스를 켰다면 '대기 중'인 것만 솎아내고, 껐다면 전체를 보여줌
    if hide_completed:
        log_list = [log for log in raw_log_list if log['status'] == "대기 중"]
    else:
        log_list = raw_log_list
        
    # 이후 목록 띄우는 코드는 기존과 동일하게 흘러감...
    log_options = [f"[{log['status']}] {log['time']} | {log['channel']} - {log['type']}" for log in log_list]
    
    selected_log = None
    if log_options:
        selected_idx = st.radio("상세 검토할 로그를 선택하세요", range(len(log_options)), key="log_selector_widget")
        selected_log = log_list[selected_idx]
    
    st.markdown("---")
    
    # 피드백 입력 섹션
    if selected_log:
        st.subheader("✍️ 데이터 피드백 입력")
        st.info(f"선택된 로그 ID: **{selected_log['id']}** ({selected_log['type']})")
        
        btn_col1, btn_col2, btn_col3 = st.columns(3)
        
        if btn_col1.button("🎯 정탐 (True)", use_container_width=True, key=f"btn_true_{selected_log['id']}"):
            selected_log['status'] = "정탐 처리됨"
            st.success("정탐으로 분류되었습니다.")
            st.rerun()
            
        if btn_col2.button("❌ 오탐 (False)", use_container_width=True, key=f"btn_false_{selected_log['id']}"):
            selected_log['status'] = "오탐 처리됨"
            st.error("오탐으로 분류되었습니다.")
            st.rerun()
            
        if btn_col3.button("📤 현장 공유", use_container_width=True, key=f"btn_share_{selected_log['id']}"):
            st.toast("🚨 해당 관제 데이터가 현장 관리자에게 공유되었습니다.", icon="ℹ️")
            
        # 한 줄 피드백 입력창
        feedback_text = st.text_input(
            "모델 개선 및 현장 특이사항 메모 (한 줄 피드백)", 
            value=selected_log['feedback'],
            placeholder="예: 객체 오인식 / 실제 낙상 사고 매칭 완료.",
            key=f"text_fb_{selected_log['id']}" # 각 로그별 고유 키 매핑으로 충돌 방지
        )
        
        # --- page2.py 내의 기존 버튼 코드 수정 ---
        if st.button("💾 피드백 저장", type="primary", use_container_width=True, key=f"btn_save_{selected_log['id']}"):
            selected_log['feedback'] = feedback_text
            
            # 💡 [여기서 백엔드 파일의 함수를 호출!]
            import feedback_manager
            feedback_manager.save_user_feedback(
                log_id=selected_log['id'],
                channel=selected_log['channel'],
                event_type=selected_log['type'],
                status=selected_log['status'],
                feedback_text=feedback_text
            )
            
            st.toast("피드백 데이터가 백엔드 CSV 파일에 안전하게 기록되었습니다!", icon="✅")
            st.rerun()


# ➡️ [우측 구역] 미디어 확인 창 및 디테일 정보
with col_right:
    st.subheader("🔍 실시간 로그 미디어 확인")
    
    if selected_log:
        card_col1, card_col2 = st.columns(2)
        card_col1.metric("발생 시각", selected_log['time'].split(" ")[1])
        card_col2.metric("처리 상태", selected_log['status'])
        
        if selected_log['media_type'] == "video":
            st.markdown("#### 📹 사고 전후 10초 녹화 영상 플레이어")
            mock_img = get_mock_media(f"{selected_log['channel']} - {selected_log['type']}\n[10초 이벤트 비디오 파일 매핑 자리]", is_video=True)
            st.image(mock_img, use_container_width=True)
        else:
            st.markdown("#### 📸 알림 순간 포착 이미지")
            mock_img = get_mock_media(f"{selected_log['channel']} - {selected_log['type']}\n[AI 추론 바운딩박스 오버레이 스냅샷]")
            st.image(mock_img, use_container_width=True)
            
        st.markdown("#### 📋 세부 메타데이터 요약")
        metadata = {
            "로그 고유 코드": selected_log['id'],
            "현장 감지 채널": selected_log['channel'],
            "이벤트 카테고리": selected_tab,
            "시스템 탐지 결과": selected_log['type'],
            "작성된 주석(피드백)": selected_log['feedback'] if selected_log['feedback'] else "등록된 피드백 없음"
        }
        st.json(metadata)
    else:
        st.info("왼쪽 목록에서 로그를 선택하시면 상세 화면과 영상/이미지를 확인할 수 있습니다.")
