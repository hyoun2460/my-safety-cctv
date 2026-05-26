import streamlit as st
import time
import datetime
import os
import shutil
import cv2
import numpy as np

# ==============================================================================
# 0. 전역 레이아웃 및 환경 설정
# ==============================================================================
st.set_page_config(
    layout="wide", 
    page_title="AI 실시간 안전 관제 시스템", 
    page_icon="🚧",
    initial_sidebar_state="expanded"
)

# ==============================================================================
# 1. 전역 세션 상태(Session State) 및 파일 시스템 인프라 초기화
# ==============================================================================
# 🌐 [클라우드 배포 호환] 로컬 하드코딩 경로 대신 상대 경로 활용 권장
# 배포 시 폴더가 자동으로 생성되도록 유도
LOCAL_WORKSPACE = "./local_workspace"
HARD_EXAMPLES_DIR = os.path.join(LOCAL_WORKSPACE, "hard_examples")
os.makedirs(HARD_EXAMPLES_DIR, exist_ok=True)

VIDEO_SAMPLE_DIR = "./CCTV_samples"
os.makedirs(VIDEO_SAMPLE_DIR, exist_ok=True)

# 🎥 CCTV 영상별 현재 재생 프레임 위치 및 재생 상태 기억 전역 변수 (키 명칭 구조 통일)
for i in range(1, 5):
    if f"video_frame_cam{i}" not in st.session_state:
        st.session_state[f"video_frame_cam{i}"] = 0
    if f"cam{i}_is_playing" not in st.session_state:
        st.session_state[f"cam{i}_is_playing"] = True 

# 위험 이벤트 발생 트리거 상태 변수
if "event_triggered" not in st.session_state:
    st.session_state.event_triggered = False
if "triggered_cam_idx" not in st.session_state:
    st.session_state.triggered_cam_idx = None

# 공용 사고 로그 데이터베이스 시뮬레이션
if "logs" not in st.session_state:
    st.session_state.logs = [
        {"id": 1, "time": "14:22:05", "loc": "2구역 (타워크레인 하부)", "type": "안전모 미착용", "conf": "62%", "status": "대기", "img": "https://images.unsplash.com/photo-1504307651254-35680f356dfd?q=80&w=800"},
        {"id": 2, "time": "14:05:12", "loc": "1구역 (반입 차량 하역장)", "type": "중장비 접근 위험", "conf": "55%", "status": "대기", "img": "https://images.unsplash.com/photo-1541888946425-d81bb19240f5?q=80&w=800"},
        {"id": 3, "time": "13:50:44", "loc": "3구역 (A동 내부 공정)", "type": "작업자 쓰러짐 감지", "conf": "89%", "status": "대기", "img": "https://images.unsplash.com/photo-1581094288338-2314dddb7ece?q=80&w=800"},
    ]

if "selected_log_id" not in st.session_state:
    st.session_state.selected_log_id = 1

# MLOps 페이지 상태 변수
if "autolabel_triggered" not in st.session_state:
    st.session_state.autolabel_triggered = False
if "autolabel_progress" not in st.session_state:
    st.session_state.autolabel_progress = 0.0

# ==============================================================================
# 2. 통합 동적 사이드바 (리모컨 영역)
# ==============================================================================
st.sidebar.title("🏗️ AI 안전 관제 플랫폼")
st.sidebar.caption("v1.0.0 (Streamlit + AI Pipeline)")

page = st.sidebar.radio(
    "🧭 시스템 메뉴 선택", 
    ["Page 1. 실시간 CCTV 관제", "Page 2. AI 판정 및 로그 확인", "Page 3. AI 모델 확장 & 오토라벨링"]
)

st.sidebar.markdown("---")

# 메뉴별 서브 필터 분기
if page == "Page 1. 실시간 CCTV 관제":
    st.sidebar.subheader("📺 관제 화면 컨트롤")
    cctv_zone = st.sidebar.selectbox("카메라 그룹", ["전체 구역 일괄 보기", "1구역 (하역장)", "2구역 (크레인)", "3구역 (내부)"])
    # 🛠️ [버그 수정]: 오타(sidebar_mode) 제거 및 스코프(st.sidebar.radio -> radio) 수정
    view_mode = st.sidebar.radio("화면 분할 설정", ["CCTV 1대 (전체 화면)", "CCTV 2대 (가로 분할)", "CCTV 4대 (2x2 그리드)"])
    ai_overlay = st.sidebar.toggle("AI 뼈대 및 면적 오버레이", value=True)
    
    if st.session_state.event_triggered:
        if st.sidebar.button("🟢 현장 상황 조치 완료 (알림 해제)", type="primary"):
            st.session_state.event_triggered = False
            st.session_state.triggered_cam_idx = None
            st.rerun()

elif page == "Page 2. AI 판정 및 로그 확인":
    st.sidebar.subheader("🔍 이력 필터링")
    date_filter = st.sidebar.date_input("조회 날짜", datetime.date.today())
    min_conf = st.sidebar.slider("최저 정확도(Confidence) 필터", 0.0, 1.0, 0.50)

elif page == "Page 3. AI 모델 확장 & 오토라벨링":
    st.sidebar.subheader("🤖 MLOps 파이프라인 제어")
    engine_ver = st.sidebar.selectbox("기반 베이스 모델 선택", ["YOLOv8-Pose (사내 최적화)", "YOLOv8-Detection (장비전용)"])

# ==============================================================================
# 3. 메인 콘텐츠 영역 (선택된 페이지 렌더링)
# ==============================================================================

if page == "Page 1. 실시간 CCTV 관제":
    st.caption(f"📍 현재 관제 구역: {cctv_zone} | 🕒 실시간 타임스탬프: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    video_paths = {
        "cam1": os.path.join(VIDEO_SAMPLE_DIR, "cam1.mp4"),
        "cam2": os.path.join(VIDEO_SAMPLE_DIR, "cam2.mp4"),
        "cam3": os.path.join(VIDEO_SAMPLE_DIR, "cam3.mp4"),
        "cam4": os.path.join(VIDEO_SAMPLE_DIR, "cam4.mp4")
    }
    
    fallback_imgs = {
        "cam1": "https://images.unsplash.com/photo-1541888946425-d81bb19240f5?q=80&w=800",
        "cam2": "https://images.unsplash.com/photo-1504307651254-35680f356dfd?q=80&w=800",
        "cam3": "https://images.unsplash.com/photo-1581094288338-2314dddb7ece?q=80&w=800",
        "cam4": "https://images.unsplash.com/photo-1504198453319-5ce911bafcde?q=80&w=800"
    }

    # 🎥 [백엔드 프레임 연산 함수] 안전망 강화 및 변수 키 일치화
    def get_cctv_frame(cam_key):
        v_path = video_paths[cam_key]
        session_key = f"video_frame_{cam_key}"
        
        if os.path.exists(v_path):
            cap = cv2.VideoCapture(v_path)
            cap.set(cv2.CAP_PROP_POS_FRAMES, st.session_state[session_key])
            ret, frame = cap.read()
            
            if ret:
                st.session_state[session_key] += 1
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                cap.release()
                return frame, True
            else:
                st.session_state[session_key] = 0
                cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                _, frame = cap.read()
                cap.release()
                if frame is not None:
                    return cv2.cvtColor(frame, cv2.COLOR_BGR2RGB), True
        
        # 🛠️ [안전 보완]: 영상 파일이 없을 때 오버레이 에러 방지를 위해 빈 이미지 어레이 전달 처리 가능
        # 여기서는 기획을 살리기 위해 URL을 반환하되 주석으로 예외 핸들링 명시
        return fallback_imgs[cam_key], False

    # 🚨 위험 이벤트 발생 강제 즉시 송출 모드
    if st.session_state.event_triggered:
        st.error(f"🚨 [위험 이벤트 강제 즉시 송출] CAM 0{st.session_state.triggered_cam_idx} 구역에 심각한 현장 사고 정황이 포착되었습니다.")
        
        target_key = f"cam{st.session_state.triggered_cam_idx}"
        img_data, is_video = get_cctv_frame(target_key)
        
        # 🛠️ [안전망]: URL 데이터 상태일 때 cv2.rectangle이 터지는 버그 방지 조건문 강화
        if is_video and ai_overlay and isinstance(img_data, np.ndarray):
            h, w, _ = img_data.shape
            cv2.rectangle(img_data, (10, 10), (w-10, h-10), (255, 0, 0), 12)
        
        st.image(img_data, width='stretch', caption=f"⚠️ [CAM 0{st.session_state.triggered_cam_idx}] 사고 다발 구역 정밀 오버레이 모니터링 중")
        time.sleep(0.05) 
        st.rerun()

    # 🟢 평상시 모드
    else:
        if view_mode == "CCTV 1대 (전체 화면)":
            img, _ = get_cctv_frame("cam1")
            st.image(img, width='stretch', caption="[CAM 01] 하역장 메인 트랙")
            
        elif view_mode == "CCTV 2대 (가로 분할)":
            col1, col2 = st.columns(2)
            img1, _ = get_cctv_frame("cam1")
            img2, _ = get_cctv_frame("cam2")
            with col1: st.image(img1, width='stretch', caption="[CAM 01] 자재 하역장")
            with col2: st.image(img2, width='stretch', caption="[CAM 02] 크레인 작업반경")
            
        elif view_mode == "CCTV 4대 (2x2 그리드)":
            row1_col1, row1_col2 = st.columns(2)
            row2_col1, row2_col2 = st.columns(2)
            img1, _ = get_cctv_frame("cam1")
            img2, _ = get_cctv_frame("cam2")
            img3, _ = get_cctv_frame("cam3")
            img4, _ = get_cctv_frame("cam4")
            with row1_col1: st.image(img1, width='stretch', caption="[CAM 01] 자재 하역장")
            with row1_col2: st.image(img2, width='stretch', caption="[CAM 02] 타워크레인 하부")
            with row2_col1: st.image(img3, width='stretch', caption="[CAM 03] 내부 마감 공정")
            with row2_col2: st.image(img4, width='stretch', caption="[CAM 04] 외곽 보안 울타리")

        if any(os.path.exists(path) for path in video_paths.values()):
            time.sleep(0.05)
            st.rerun()

        st.markdown("---")
        ctrl_col1, ctrl_col2, ctrl_col3 = st.columns([8, 1, 1])
        with ctrl_col2:
            if st.button("🚨 위험 감지 테스트", use_container_width=True):
                st.session_state.event_triggered = True
                st.session_state.triggered_cam_idx = 2
                st.toast("🚨 [위험 상황 감지] 2구역 긴급 팝업 모드로 강제 전환합니다!", icon="🔥")
                st.rerun()
        with ctrl_col3:
            with st.popover("⚙️ 화면 제어", use_container_width=True):
                # 🛠️ [버그 수정]: st.small -> st.caption으로 변경
                st.caption("신속 제어 센터")
                st.checkbox("IR 야간 모드", value=False)
                st.checkbox("스트리밍 고화질(HD) 고정", value=True)

elif page == "Page 2. AI 판정 및 로그 확인":
    st.title("🔍 사건사고 판정 및 이력 검증 시스템")
    st.caption("AI의 판단 신뢰도가 모호한 스냅샷을 검증하고 오탐 데이터를 격리하는 화면입니다.")
    st.markdown("---")
    
    left_layout, right_layout = st.columns([4, 6])
    
    with left_layout:
        st.subheader("📋 검증 대기 및 조치 목록")
        for log in st.session_state.logs:
            is_checked = log["status"] in ["정탐 판정완료", "오탐 분류완료"]
            
            with st.container(border=True):
                if is_checked:
                    st.markdown(f"~~**[{log['status']}]** {log['time']} | {log['loc']} - {log['type']}~~")
                    if st.button("↩️ 판정 롤백(되돌리기)", key=f"rb_{log['id']}", size="small"):
                        log["status"] = "대기"
                        st.toast("사고 로그가 다시 대기 상태로 복구되었습니다.", icon="↩️")
                        st.rerun()
                else:
                    col_info, col_action = st.columns([3, 1])
                    with col_info:
                        st.markdown(f"⚠️ **{log['type']}** (정확도: :red[{log['conf']}])")
                        st.caption(f"발생: {log['time']} | 위치: {log['loc']}")
                    with col_action:
                        if st.button("상세보기 🔍", key=f"view_{log['id']}", use_container_width=True):
                            st.session_state.selected_log_id = log["id"]
                            st.rerun()

    with right_layout:
        st.subheader("🖼️ 선택 항목 스냅샷 검증")
        target_log = next(l for l in st.session_state.logs if l["id"] == st.session_state.selected_log_id)
        
        with st.container(border=True):
            st.markdown(f"### 위치: {target_log['loc']} 당시 스냅샷")
            st.image(target_log["img"], width='stretch')
            st.write(f"**상세 메타데이터:** {target_log['time']} / {target_log['type']} (AI 예측 신뢰도: {target_log['conf']})")
            
            if target_log["status"] == "대기":
                st.markdown("정탐/오탐 여부를 확정해 주세요.")
                fail_reason = st.text_input("오탐 분류 사유 기입 (선택사항)", placeholder="예: 주황색 드럼통을 사람 안전모로 오인함")
                
                act_btn1, act_btn2, act_btn3 = st.columns(3)
                with act_btn1:
                    if st.button("✅ 정탐 (실제 상황)", type="primary", use_container_width=True):
                        target_log["status"] = "정탐 판정완료"
                        st.toast("정상적으로 확인 처리되었습니다.", icon="✅")
                        st.rerun()
                with act_btn2:
                    if st.button("❌ 오탐 (AI 오판)", type="secondary", use_container_width=True):
                        target_log["status"] = "오탐 분류완료"
                        
                        clean_type = "bumping" if "부딪힘" in target_log["type"] else "helmet"
                        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                        filename = f"{clean_type}_cam_{target_log['id']}_{timestamp}.jpg"
                        target_path = os.path.join(HARD_EXAMPLES_DIR, filename)
                        
                        with open(target_path, "w") as f:
                            f.write("Fake image context for active learning backup.")
                        
                        st.toast(f"📁 오탐 데이터가 공유 폴더에 백업되었습니다!", icon="📁")
                        st.rerun()
                with act_btn3:
                    st.button("🔗 현장 긴급공유", use_container_width=True)
            else:
                st.success(f"이 조치 건은 이미 **[{target_log['status']}]** 상태입니다.")

elif page == "Page 3. AI 모델 확장 & 오토라벨링":
    st.title("🤖 AI 기능 확장 및 오토라벨링 자동화 파이프라인")
    st.caption("새로운 객체를 추가할 때 데이터 수집 현황을 모니터링하고 최종 학습 완료된 가중치를 배포하는 MLOps 화면입니다.")
    st.markdown("---")
    
    step1, step2, step3 = st.tabs(["💬 1단계. 기능 요청 & 진단", "🏷️ 2단계. 오토라벨링 실시간 검수", "📊 3단계. 성적표 비교 & 현장 배포"])
    
    with step1:
        st.subheader("새로운 보안 관제 항목 클래스 정의")
        chat_query = st.chat_input("이곳에 필요한 기능을 요청하세요. (예: 현장에 '안전조끼' 인식 기능 추가해줘)")
        
        if chat_query:
            st.session_state.autolabel_triggered = True
            st.session_state.autolabel_progress = 0.0
            st.rerun()
            
        if st.session_state.autolabel_triggered:
            st.success(f"🤖 AI 진단 센터: 가동 가능 상태 확인")
            m1, m2, m3 = st.columns(3)
            m1.metric("현장 수집 이미지 총량", "1,450 장", "실시간 자동 수집됨")
            m2.metric("라벨링 완료 데이터", "250 장", "인간 검수 완료")
            m3.metric("미라벨링 (자동화 대상)", "1,200 장", "오토라벨링 엔진 대기 중", delta_color="inverse")
            
            if st.button("🚀 1,200장 오토라벨링 파이프라인 즉시 가동", type="primary"):
                st.session_state.autolabel_progress = 0.01 
                st.rerun()

    with step2:
        st.subheader("AI 오토라벨링 자동 박스 생성 검수")
        if st.session_state.autolabel_triggered and st.session_state.autolabel_progress > 0:
            if st.session_state.autolabel_progress < 1.0:
                st.session_state.autolabel_progress += 0.15 
                if st.session_state.autolabel_progress > 1.0:
                    st.session_state.autolabel_progress = 1.0
                time.sleep(0.4)
                st.rerun()

            st.progress(st.session_state.autolabel_progress, text=f"현재 오토라벨링 가상 진행률: {int(st.session_state.autolabel_progress * 100)}% 완료")
            
            sub_col1, sub_col2 = st.columns([4, 6])
            with sub_col1:
                st.info("📋 인간의 최종 검수가 필요한 이미지 리스트")
                for i in range(1, 4):
                    st.markdown(f"📦 **AutoLabel_SafetyVest_{i:03d}.jpg**")
                    st.button("승인 및 교정 완료", key=f"label_chk_{i}")
            with sub_col2:
                st.subheader("라벨링 이미지 미리보기")
                st.image("https://images.unsplash.com/photo-1581094288338-2314dddb7ece?q=80&w=800", width='stretch')
        else:
            st.warning("🔒 1단계에서 파이프라인을 가동해야 활성화되는 탭입니다.")

    with step3:
        st.subheader("신·구 딥러닝 모델 성능 분석표")
        if st.session_state.autolabel_triggered and st.session_state.autolabel_progress >= 1.0:
            st.markdown("재학습 성능 지표 대조")
            
            stat1, stat2, stat3 = st.columns(3)
            stat1.metric("모델 정확도 (mAP50-95)", "88.4 %", "+4.2% 향상", delta_color="normal")
            stat2.metric("미착용 감지 재현율(Recall)", "91.2 %", "+1.1% 보존")
            stat3.metric("추론 속도 (FPS)", "45 FPS", "-2 FPS")
            
            st.markdown("---")
            if st.button("🔴 신규 AI 안전 모델 현장 CCTV 시스템 적용 및 배포", type="primary", use_container_width=True):
                st.balloons()
                st.success("🎉 배포 완료! 실시간 CCTV 관제 엔진이 신규 모델로 업데이트되었습니다.")
        else:
            st.warning("🔒 학습 완료 전까지 비활성화됩니다.")
