import streamlit as st
import cv2
import numpy as np
import time
import random

st.title("🎥 실시간 CCTV 안전 관제")
st.markdown("CCTV 영상을 분석하여 작업자의 이상 행동 및 보호구 착용 여부를 실시간으로 모니터링합니다.")

# ⚙️ 기존 app.py에 있던 사이드바 메뉴를 page1.py 내부로 이사
st.sidebar.markdown("## ⚙️ CCTV 제어 및 설정")

# 비디오 소스 선택 위젯
video_source = st.sidebar.selectbox(
    "CCTV 영상 소스 선택", 
    ["샘플 비디오 (0번 웹캠 대체)", "직접 영상 경로 입력"]
)

# 선택에 따른 소스 경로 지정
if video_source == "샘플 비디오 (0번 웹캠 대체)":
    video_path = 0  # 내장 웹캠 혹은 테스트용 0번
else:
    video_path = st.sidebar.text_input("테스트 비디오 파일 경로 입력", "data/sample_cctv.mp4")

# 감지 주기 설정 (최적화 방향성 검증용)
st.sidebar.markdown("---")
detection_fps = st.sidebar.slider("초당 AI 분석 횟수 (FPS)", min_value=1, max_value=5, value=2)

# 관제 시작 버튼
start_button = st.sidebar.button("▶ 관제 시작", use_container_width=True)
stop_button = st.sidebar.button("⏹ 관제 종료", use_container_width=True)

# 실시간 화면을 그려줄 껍데기(Placeholder) 생성
frame_placeholder = st.empty()
alert_placeholder = st.empty()

# 실행 로직
if start_button:
    cap = cv2.VideoCapture(video_path)
    
    if not cap.isOpened():
        st.error(f"영상 소스({video_path})를 열 수 없습니다. 경로를 확인해주세요.")
    else:
        video_fps = cap.get(cv2.CAP_PROP_FPS)
        if video_fps == 0 or video_fps is None:
            video_fps = 30  # 웹캠 등 FPS 측정이 안 될 경우 기본값
            
        # 몇 프레임마다 검증할 것인지 계산 (예: 원래 30fps / 설정 2fps = 15프레임마다)
        skip_interval = max(1, int(video_fps / detection_fps))
        
        frame_count = 0
        is_danger = False
        danger_msg = ""

        # 루프 시작
        while cap.isOpened():
            # 사용자가 종료 버튼을 누르면 루프 탈출
            if stop_button:
                break
                
            ret, frame = cap.read()
            if not ret:
                st.info("영상이 종료되었거나 프레임을 읽을 수 없습니다.")
                break
                
            frame_count += 1
            
            # --- [핵심] 초당 N번만 솎아내서 판단하는 로직 ---
            if frame_count % skip_interval == 0:
                # 💡 [모델 완성 전 판단 단계] 15% 확률로 위험 상황 발생 모의 가상화
                if random.random() < 0.15: 
                    is_danger = True
                    danger_msg = random.choice([
                        "🚨 위험: 작업자 쓰러짐/추락 위험 감지!", 
                        "🚨 주의: 안전모 미착용 작업자가 구역 내에 있습니다!"
                    ])
                else:
                    is_danger = False
            
            # --- 시각화 오버레이 처리 ---
            if is_danger:
                # 위험할 때만 화면 테두리에 굵은 빨간색 사각형 오버레이
                h, w, _ = frame.shape
                cv2.rectangle(frame, (20, 20), (w-20, h-20), (0, 0, 255), 8)
                cv2.putText(frame, "RISK DETECTED", (40, 80), cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 0, 255), 4)
                
                # 영상 바로 아래 경고창 노출
                alert_placeholder.error(danger_msg)
            else:
                alert_placeholder.empty()
                
            # 화면 출력
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            frame_placeholder.image(frame_rgb, channels="RGB", use_container_width=True)
            
            # 원본 영상 속도와 동기화를 위한 약간의 타임 슬립
            time.sleep(1 / video_fps)
            
        cap.release()
        frame_placeholder.empty()
        alert_placeholder.empty()
        st.success("CCTV 관제가 안전하게 종료되었습니다.")
