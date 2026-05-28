import streamlit as st
import time
import numpy as np
import cv2

# --- 1. 세션 상태 초기화 ---
if "page3_locked" not in st.session_state:
    st.session_state.page3_locked = False
if "pipeline_progress" not in st.session_state:
    st.session_state.pipeline_progress = 0
if "low_accuracy_triggered" not in st.session_state:
    st.session_state.low_accuracy_triggered = False
if "ref_images" not in st.session_state:
    st.session_state.ref_images = [
        {"name": "helmet", "color": (0, 255, 255)},
        {"name": "person", "color": (255, 0, 0)}
    ]

# --- 2. 초기화 경고 팝업창 (st.dialog) 정의 ---
@st.dialog("⚠️ 모델 및 파이프라인 초기화 경고")
def show_reset_warning_dialog():
    st.error("지금까지의 학습 및 오토 라벨링 작업을 중지하고 모든 데이터를 초기화합니다.")
    st.warning("초기화된 임시 모델 및 정답지(.txt)는 다시 복구할 수 없습니다. 정말 진행하시겠습니까?")
    
    col_dialog1, col_dialog2 = st.columns(2)
    if col_dialog1.button("💥 네, 전면 초기화합니다", type="primary", use_container_width=True):
        # 모든 상태 리셋
        st.session_state.page3_locked = False
        st.session_state.pipeline_progress = 0
        st.session_state.low_accuracy_triggered = False
        st.toast("🔄 시스템이 전면 초기화되었습니다. 입력창 잠금이 해제됩니다.")
        st.rerun()
    if col_dialog2.button("취소", type="secondary", use_container_width=True):
        st.rerun()

# --- 3. 스타일 커스텀 CSS 주입 ---
st.markdown("""
    <style>
    /* 잠금 상태일 때의 시각적 경고 테두리 */
    .lock-status-container {
        border: 2px dashed #ef4444;
        padding: 10px;
        border-radius: 6px;
        text-align: center;
        background-color: rgba(239, 68, 68, 0.1);
        color: #ef4444;
        font-weight: bold;
        margin-bottom: 15px;
    }
    /* 인포박스 스타일 */
    .accuracy-warning-box {
        background-color: #7f1d1d;
        border: 2px solid #ef4444;
        color: #fca5a5;
        padding: 12px;
        border-radius: 6px;
        font-weight: bold;
        text-align: center;
        margin-bottom: 15px;
    }
    </style>
""", unsafe_allow_html=True)

st.title("🔄 새 클래스 확장 및 오토 라벨링 시스템")
st.caption("기존 탐지 가중치를 유지한 채 신규 객체를 확장하고, 신뢰도가 낮은 구간은 인간 관제사의 개입(Human-in-the-Loop)을 통해 검증합니다.")

# --- 🖥️ 좌우 2분할 레이아웃 배치 ---
col_left, col_right = st.columns([45, 55])

# ⬅️ [좌측 구역] 데이터 빌드업 및 제어 락 (LOCK 대상 영역)
with col_left:
    st.subheader("🛠️ 1. DATA & FEATURE INPUT")
    
    # 현재 잠금 상태 알림창
    if st.session_state.page3_locked:
        st.markdown('<div class="lock-status-container">🔒 현재 파이프라인 가동 중 (입력창 잠김)</div>', unsafe_allow_html=True)
        
    # [1단계] 추가 클래스 정보 기획 및 설명 글 작성 칸
    st.markdown("#### 🏷️ Class Definition & Features")
    new_class = st.text_input("추가할 클래스 이름 (영문)", value="safety_vest", disabled=st.session_state.page3_locked)
    class_desc = st.text_area("클래스 설명 및 감지 목적 정의", value="현장 작업자의 안전조끼 미착용 상태를 식별하기 위한 신규 도메인 데이터셋.", disabled=st.session_state.page3_locked)
    
    uploaded_feature = st.file_uploader("세부 특징 스냅샷 업로드 (.jpg, .png)", type=["jpg", "png"], disabled=st.session_state.page3_locked)
    
    # 특징 이미지 업로드 시 실시간 레퍼런스 데이터셋 그리드에 누적 (회원님 기획)
    if uploaded_feature and not st.session_state.page3_locked:
        if not any(img["name"] == new_class for img in st.session_state.ref_images):
            st.session_state.ref_images.append({"name": new_class, "color": (0, 255, 0)})
            st.toast(f"🎯 레퍼런스 그리드에 {new_class} 타겟이 실시간 누적되었습니다.")

    st.markdown("---")
    
    # [2단계] 데이터셋 보유 유무에 따른 분기 로직 (회원님 기획)
    st.markdown("#### 📂 Dataset Configuration")
    has_dataset = st.checkbox("이미 라벨링된 외부 데이터셋(.zip) 보유 중", value=False, disabled=st.session_state.page3_locked)
    
    if has_dataset:
        st.file_uploader("YOLO 포맷 데이터셋 업로드 (.zip)", type=["zip"], disabled=st.session_state.page3_locked)
    else:
        cctv_select = st.selectbox(
            "자동 추출용 아카이브 CCTV 데이터 선택",
            ["최근 1주일 아카이브 (5/22 ~ 5/28) 💾", "특정 채널 지정 스캔"],
            disabled=st.session_state.page3_locked
        )

    st.markdown("---")
    
    # [3단계] 입력 완료 마감 LOCK 버튼
    if not st.session_state.page3_locked:
        if st.button("🔒 입력 완료 및 파이프라인 잠금", type="primary", use_container_width=True):
            st.session_state.page3_locked = True
            st.rerun()
            
    # 레퍼런스 라이브러리 그리드 시각화 (좌측 하단 상시 노출)
    st.markdown("#### 🎯 Reference Library Grid")
    ref_cols = st.columns(4)
    for idx, ref in enumerate(st.session_state.ref_images):
        with ref_cols[idx % 4]:
            img_box = np.zeros((70, 90, 3), dtype=np.uint8) + 40
            cv2.rectangle(img_box, (4, 4), (86, 66), ref["color"], 2)
            cv2.putText(img_box, "REF", (28, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (150, 150, 150), 1)
            st.image(img_box, use_container_width=True)
            st.caption(f"🏷️ {ref['name']}")


# ➡️ [우측 구역] 파이프라인 가동 시뮬레이션 및 예외 처리 검증단
with col_right:
    st.subheader("🤖 2. PIPELINE STATUS & CONTROL")
    
    if not st.session_state.page3_locked:
        st.info("💡 좌측 구역에서 설정을 마친 후 [🔒 잠금] 버튼을 누르면 오토 라벨링 및 모델 제어 파트가 활성화됩니다.")
    else:
        # [3단계 오른쪽] 변경 필요 시 안전하게 경고창을 띄우는 초기화 버튼 기획
        if st.button("🔓 잠금 해제 및 작업 초기화", type="secondary", use_container_width=True):
            show_reset_warning_dialog() # 팝업 경고창 띄우기
            
        st.markdown("---")
        
        # 모델 학습 및 가상 진행 시뮬레이터 구동 버튼
        if st.session_state.pipeline_progress == 0:
            if st.button("🚀 오토 라벨링 및 학습 파이프라인 실행", type="primary", use_container_width=True):
                st.session_state.pipeline_progress = 45 # 45% 진행된 시점으로 즉시 이동 (시연용)
                st.rerun()
                
        if st.session_state.pipeline_progress > 0:
            st.markdown("#### 📈 Overall Progress")
            st.progress(st.session_state.pipeline_progress)
            
            if st.session_state.pipeline_progress < 100:
                st.caption(f"⏳ 가상 모델 훈련 및 데이터셋 오토 맵핑 중... ({st.session_state.pipeline_progress}%)")
                
                # 시연 중 특정 시점(예: 45%)에서 정확도가 떨어지는 예외 상황 강제 발동
                if st.session_state.pipeline_progress == 45:
                    st.session_state.low_accuracy_triggered = True
            
            # [4단계] 정확도가 저하되어 인간 참여형 피드백창(Page 2 양식) 등판 (회원님 기획)
            if st.session_state.low_accuracy_triggered:
                st.markdown('<div class="accuracy-warning-box">⚠️ Model Accuracy: Low (61%). Human Verification Req.</div>', unsafe_allow_html=True)
                
                # 검증용 난해한 예외 프레임 시각화
                st.markdown("##### 📷 검증 필요 프레임 (CCTV 1대 - 야간 가시성 저하 구간)")
                img_fail = np.zeros((200, 500, 3), dtype=np.uint8) + 30
                cv2.rectangle(img_fail, (180, 40), (320, 170), (0, 255, 255), 3) # 노란색 애매한 박스
                cv2.putText(img_fail, "Unclear Target: safety_vest?", (190, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 255, 255), 1)
                st.image(cv2.cvtColor(img_fail, cv2.COLOR_BGR2RGB), use_container_width=True)
                
                # Page 2 인터페이스 재활용 단 배치
                btn_p3_1, btn_p3_2, btn_p3_3 = st.columns(3)
                if btn_p3_1.button("🎯 정탐 (True 라벨 승인)", use_container_width=True):
                    st.success("인간 관제사 승인: 정답지(.txt) 강제 빌드 세팅 완료.")
                    st.session_state.pipeline_progress = 100 # 검증 완료 처리하여 패스
                    st.session_state.low_accuracy_triggered = False
                    st.rerun()
                if btn_col2_fp := btn_p3_2.button("❌ 오탐 (데이터 제외)", use_container_width=True):
                    st.warning("라벨링 제외: 해당 비정형 데이터는 학습 예외 처리되었습니다.")
                    st.session_state.pipeline_progress = 100
                    st.session_state.low_accuracy_triggered = False
                    st.rerun()
                btn_p3_3.button("📤 공유", use_container_width=True)
                
                st.text_input("📝 인간 참여 수정 메모", placeholder="조도 저하로 인한 조끼 반사광 오인식 유발 처리 완료.")
                
            if st.session_state.pipeline_progress == 100:
                st.success("🎉 신규 클래스 확장 데이터셋 및 YAML 빌드 완료!")
                st.code(f"""
# 📂 최종 컴파일된 dataset.yaml 구조
names:
  0: person
  1: helmet
  2: {new_class}  # 자동으로 병합 마이그레이션된 새 도메인 클래스!
                """)
