import streamlit as st
import time
import numpy as np
import cv2

st.title("🔄 신규 클래스 확장 및 오토 라벨링 시스템")
st.markdown("기존 모델에 없던 새 객체(예: 안전조끼)를 추가하기 위해, CCTV 아카이브 데이터와 특징 이미지를 활용해 자동 정답지(Label)를 생성합니다.")

# 🛠️ 3단계 파이프라인 레이아웃 구성
st.markdown("---")
st.subheader("🛠️ STEP 1: 신규 클래스 정의 및 특징 이미지 지정")

col1, col2 = st.columns(2)

with col1:
    # 1. 추가할 클래스명 입력
    new_class_name = st.text_input("1. 추가할 클래스 이름 입력 (영문)", value="safety_vest", placeholder="예: safety_vest, gas_mask")
    
    # 2. CCTV 데이터 아카이브 선택 (회원님 아이디어 반영: 1주치 데이터 존재 명시)
    cctv_archive = st.selectbox(
        "2. 오토 라벨링을 진행할 CCTV 저장고 선택",
        ["최근 1주일 데이터 (2026-05-22 ~ 2026-05-28) 💾", "특정 날짜 구역 지정", "직접 원본 영상 업로드"]
    )

with col2:
    # 3. 타겟 특징 이미지 업로드 기획 (회원님 아이디어 반영!)
    st.markdown("**3. 오토 라벨링 가이드용 특징 이미지 업로드**")
    st.caption("AI가 1주치 데이터에서 타겟을 정확히 식별할 수 있도록, 해당 물체(예: 조끼)의 크롭 이미지 1장을 등록해주세요.")
    
    uploaded_feature_img = st.file_uploader("특징 스냅샷 이미지 업로드 (.jpg, .png)", type=["jpg", "png"])

st.markdown("---")

# 🔄 STEP 2: 오토 라벨링 시뮬레이션 구역
st.subheader("🤖 STEP 2: 기존 모델(YOLO/Pose) 기반 오토 라벨링 가동")

if uploaded_feature_img is not None:
    st.success(f"✅ 타겟 이미지 접수 완료! [{new_class_name}] 스캔 알고리즘이 준비되었습니다.")
    
    # 시연을 위한 가동 버튼
    if st.button("🚀 1주일치 CCTV 데이터 오토 라벨링 시작", type="primary", use_container_width=True):
        
        # 프로그레스 바와 로그 출력을 위한 플레이스홀더
        progress_bar = st.progress(0)
        status_text = st.empty()
        log_box = st.empty()
        
        # 가상 오토 라벨링 로그 생성
        mock_logs = [
            f"[INFO] {cctv_archive} 스캔 시작...",
            "[Model] Human Pose Estimation 가동: 영상 내 'Person' 객체 추출 중...",
            f"[Match] 업로드된 특징 이미지와 사람 상체(Upper Body) 유사도 대조 시작...",
            "[Success] 1일차 데이터 완료: safety_vest 라벨 142개 생성 완료.",
            "[Success] 3일차 데이터 완료: safety_vest 라벨 310개 생성 완료.",
            "[Success] 5일차 데이터 완료: safety_vest 라벨 185개 생성 완료.",
            "[Success] 7일차 데이터 완료: 총 892개의 새로운 데이터셋 정답지(.txt) 구축 성공!"
        ]
        
        # 가상 진행 루프
        for percent_complete in range(100):
            time.sleep(0.03) # 속도 조절
            progress_bar.progress(percent_complete + 1)
            status_text.text(f"⏳ CCTV 프레임 분석 및 라벨 매칭 중... ({percent_complete + 1}%)")
            
            # 진행도에 따라 로그를 동적으로 노출
            if percent_complete == 10:
                log_box.code(mock_logs[0] + "\n" + mock_logs[1])
            elif percent_complete == 40:
                log_box.code("\n".join(mock_logs[:4]))
            elif percent_complete == 70:
                log_box.code("\n".join(mock_logs[:5]))
                
        status_text.text("✅ 오토 라벨링 완료!")
        log_box.code("\n".join(mock_logs))
        st.session_state.auto_label_done = True

st.markdown("---")

# 📦 STEP 3: 모델 병합 및 패키징 구역
st.subheader("📦 STEP 3: 기존 모델 v2.0과 데이터셋 병합 및 추출")

if st.session_state.get("auto_label_done", False):
    st.info(f"기존 클래스(안전모, 사람) 데이터셋과 신규 오토 라벨링된 [{new_class_name}] 데이터셋의 구조적 병합이 완료되었습니다.")
    
    # 재학습 전략 선택 위젯
    merge_strategy = st.radio(
        "개인 VS Code(GPU 환경)로 가져갈 재학습 훈련 전략 선택",
        [
            "🔄 전체 데이터셋 통합 후 전면 재학습 (Full Retrain) - 권장",
            "🎯 기존 가중치 고정 후 마지막 레이어만 확장 (Fine-tuning)"
        ]
    )
    
    # 최종 다운로드/패키징 버튼
    if st.button("💾 VS Code 이사용 dataset.yaml 및 데이터셋 패키징", use_container_width=True):
        st.toast("📌 dataset.yaml 및 라벨 파일 묶음 패키징 완료! 내 컴퓨터에서 바로 학습을 재개할 수 있습니다.", icon="✅")
        
        # 가상 구조도 표출
        st.markdown("#### 📂 생성된 이사 전용 데이터셋 폴더 구조 예시")
        st.code(f"""
my-safety-dataset/
├── dataset.yaml       # 클래스 정의 (0: person, 1: helmet, 2: {new_class_name})
├── train/
│   ├── images/        # 기존 이미지 + 1주치 골라낸 이미지
│   └── labels/        # 기존 라벨 + 새로 생성된 오토 라벨 (.txt)
└── val/
    ├── images/
    └── labels/
        """)
else:
    st.caption("💡 STEP 1에서 특징 이미지를 업로드하고 STEP 2의 오토 라벨링을 실행하면 데이터셋 병합 및 패키징 메뉴가 활성화됩니다.")
