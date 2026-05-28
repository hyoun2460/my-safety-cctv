import streamlit as st
import cv2
import numpy as np
import time
import random

st.title("🎥 실시간 CCTV 멀티 관제 (최대 4채널)")
st.markdown("CCTV 채널별 영상을 분석하여 작업자의 이상 행동 및 보호구 착용 여부를 실시간으로 모니터링합니다.")

# ⚙️ 사이드바 제어 및 설정
st.sidebar.markdown("## ⚙️ 멀티 CCTV 설정")

# 1. 활성화할 CCTV 개수 선택
cctv_count = st.sidebar.slider("활성화할 CCTV 대수", min_value=1, max_value=4, value=2)

# 가상의 샘플 영상 리스트 (나중에 data/ 폴더에 이 이름대로 넣으시면 됩니다)
sample_videos = {
    "샘플 영상 1 (정상 작업 구역)": "data/sample_cctv1.mp4",
    "샘플 영상 2 (추락 위험 구역)": "data/sample_cctv2.mp4",
    "샘플 영상 3 (충돌 위험 구역)": "data/sample_cctv3.mp4",
    "샘플 영상 4 (보호구 미착용 구역)": "data/sample_cctv4.mp4",
    "샘플 영상 5 (야간 감시 구역)": "data/sample_cctv5.mp4",
    "샘플 영상 6 (장비 이동 구역)": "data/sample_cctv6.mp4"
}

# 2. 선택한 개수만큼 사이드바에 영상 소스 선택 위젯 동적 생성
selected_sources = []
for i in range(cctv_count):
    st.sidebar.markdown(f"### 📺 {i+1}번 채널 설정")
    # 각 채널마다 서로 다른 샘플을 디폴트로 지정 (1번 채널엔 1번 영상, 2번 채널엔 2번 영상...)
    default_index = min(i, len(sample_videos) - 1)
    
    choice = st.sidebar.selectbox(
        f"{i+1}번 CCTV 영상 선택", 
        list(sample_videos.keys()), 
        index=default_index,
        key=f"cctv_src_{i}"
    )
    # 선택한 가상 파일 경로 저장
    selected_sources.append(sample_videos[choice])

# 3. 공통 감지 주기 설정
st.sidebar.markdown("---")
detection_fps = st.sidebar.slider("초당 AI 분석 횟수 (FPS)", min_value=1, max_value=5, value=2)

# 관제 버튼
start_button = st.sidebar.button("▶ 관제 시작", use_container_width=True)
stop_button = st.sidebar.button("⏹ 관제 종료", use_container_width=True)

# --- 🖥️ 메인 관제 화면 그리드(레이아웃) 생성 ---
# 화면을 2x2 격자로 나누기 위해 empty 껍데기들을 미리 배열 형태로 셋팅합니다.
placeholders = []
alert_placeholders = []

if cctv_count == 1:
    # 1대일 때는 화면 전체 활용
    placeholders.append(st.empty())
    alert_placeholders.append(st.empty())
elif cctv_count == 2:
    # 2대일 때는 가로로 2분할
    cols = st.columns(2)
    for col in cols:
        placeholders.append(col.empty())
        alert_placeholders.append(col.empty())
else:
    # 3~4대일 때는 2x2 격자 레이아웃
    row1 = st.columns(2)
    row2 = st.columns(2)
    
    placeholders.append(row1[0].empty()) # 1번 자리
    alert_placeholders.append(row1[0].empty())
    
    placeholders.append(row1[1].empty()) # 2번 자리
    alert_placeholders.append(row1[1].empty())
    
    placeholders.append(row2[0].empty()) # 3번 자리
    alert_placeholders.append(row2[0].empty())
    
    if cctv_count == 4:
        placeholders.append(row2[1].empty()) # 4번 자리
        alert_placeholders.append(row2[1].empty())


# --- 🔄 실시간 다중 재생 및 판단 루프 ---
if start_button:
    # 선택된 대수만큼 VideoCapture 객체 생성
    # (현재는 실제 파일이 없으므로 검은색 화면에 텍스트를 그리는 가상 캡처 시뮬레이션으로 대체합니다)
    caps = []
    video_fps = 30
    skip_interval = max(1, int(video_fps / detection_fps))
    
    frame_count = 0
    # 각 채널별 위험 상태를 기억할 리스트
    danger_states = [False] * cctv_count
    danger_messages = [""] * cctv_count

    # 테스트용 가상 프레임 생성기 (실제 파일이 없을 때 에러 방지용)
    def generate_mock_frame(channel_name, frame_num):
        # 640x480 크기의 빈 비디오 프레임 생성
        img = np.zeros((480, 640, 3), dtype=np.uint8) + 40 # 어두운 회색 배경
        # 현재 채널 정보 표시
        cv2.putText(img, f"CCTV: {channel_name}", (30, 220), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 255, 255), 2)
        cv2.putText(img, f"Frame: {frame_num}", (30, 270), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (150, 150, 150), 1)
        return img

    st.toast("다중 채널 관제를 시작합니다!", icon="🚀")

    # 가상 루프 실행
    while True:
        if stop_button:
            break
            
        frame_count += 1
        
        # 초당 N번 솎아내는 타이밍 체크
        is_eval_timing = (frame_count % skip_interval == 0)
        
        # 4대의 카메라를 순차적으로 스캔
        for idx in range(cctv_count):
            # 1. 파일이 없을 테니 가상 프레임 가져오기 (실제 구현 시엔 cap.read()가 들어갈 자리)
            file_name = selected_sources[idx].split("/")[-1]
            frame = generate_mock_frame(f"Channel {idx+1} ({file_name})", frame_count)
            
            # 2. AI 판단 타이밍일 때 채널별로 독립적인 위험 확률 부여
            if is_eval_timing:
                # 10%의 확률로 무작위 위험 발생 모의
                if random.random() < 0.10:
                    danger_states[idx] = True
                    danger_messages[idx] = random.choice([
                        f"🚨 [{idx+1}번 채널] 위험구역 작업자 추락 의심!", 
                        f"🚨 [{idx+1}번 채널] 미착용(안전모/조끼) 발견!"
                    ])
                else:
                    danger_states[idx] = False
            
            # 3. 위험 상태인 채널에 오버레이 덮어쓰기
            if danger_states[idx]:
                # 화면 테두리에 굵은 빨간 사각형 오버레이
                cv2.rectangle(frame, (10, 10), (630, 470), (0, 0, 255), 12)
                cv2.putText(frame, "EMERGENCY", (30, 70), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 0, 255), 3)
                # 영상 밑 껍데기에 경고문구 출력
                alert_placeholders[idx].error(danger_messages[idx])
            else:
                alert_placeholders[idx].empty()
                
            # 4. 각 격자 자리에 매핑된 placeholder에 이미지 뿌리기
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            placeholders[idx].image(frame_rgb, channels="RGB", use_container_width=True)
            
        # 프레임 간 격차 조절을 위한 미세한 딜레이 (4대 순회 연산 속도 고려)
        time.sleep(0.03)

    # 종료 후 청소
    for p in placeholders: p.empty()
    for a in alert_placeholders: a.empty()
    st.success("모든 CCTV 관제가 안전하게 종료되었습니다.")
