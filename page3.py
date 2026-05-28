import streamlit as st
import time
import numpy as np
import cv2
from PIL import Image

st.title("🔄 신규 클래스 확장 및 오토 라벨링 시스템")

# --- 세션 상태 초기화 ---
if "reference_images" not in st.session_state:
    # 기본 데모용 레퍼런스 이미지 리스트 (이름, 샘플색상)
    st.session_state.reference_images = [
        {"name": "helmet", "color": (0, 255, 255)}, # 노란색 안전모 대용
        {"name": "person", "color": (255, 0, 0)}    # 파란색 사람 대용
    ]
if "pipeline_running" not in st.session_state:
    st.session_state.pipeline_running = False
if "auto_label_done" not in st.session_state:
    st.session_state.auto_label_done = False

# --- STEP 1: 데이터 소스 및 클래스 정의 ---
st.markdown("---")
st.subheader("🛠️ STEP 1: 데이터 소스 정의 및 신규 클래스 지정")

# 1. 데이터 소스 선택 (CCTV 스캔 vs 외부 데이터셋) - 회원님 아이디어 반영
data_source = st.radio(
    "데이터 확보 방식을 선택하세요",
    ["📡 CCTV 아카이브 스캔 (오토라벨링 필요)", "📂 이미 라벨링된 외부 데이터셋 직접 업로드 (CCTV 스캔 패스)"],
    disabled=st.session_state.pipeline_running # 작업 중이면 잠금
)

col1, col2 = st.columns(2)

with col1:
    new_class_name = st.text_input(
        "추가할 클래스 이름 (영문)", 
        value="safety_vest", 
        disabled=st.session_state.pipeline_running
    )
    
    # CCTV 스캔을 선택했을 때만 아카이브 선택창 활성화
    if "CCTV 아카이브" in data_source:
        cctv_archive = st.selectbox(
            "오토 라벨링을 진행할 CCTV 저장고",
            ["최근 1주일 데이터 (2026-05-22 ~ 2026-05-28) 💾", "특정 채널 지정"],
            disabled=st.session_state.pipeline_running
        )
    else:
        st.caption("💡 외부 데이터셋을 업로드하므로 CCTV 아카이브를 참조하지 않습니다.")

with col2:
    if "CCTV 아카이브" in data_source:
        st.markdown("**오토 라벨링 가이드용 특징 이미지 업로드**")
        uploaded_feature_img = st.file_uploader(
            "특징 스냅샷 (.jpg, .png)", 
            type=["jpg", "png"],
            disabled=st.session_state.pipeline_running
        )
        
        # 이미지를 올리면 실시간으로 하단 레퍼런스 세션에 추가하는 로직
        if uploaded_feature_img and not st.session_state.pipeline_running:
            # 중복 추가 방지
            if not any(img["name"] == new_class_name for img in st.session_state.reference_images):
                st.session_state.reference_images.append({"name": new_class_name, "color": (0, 255, 0)})
                st.toast(f"✅ 레퍼런스 목록에 [{new_class_name}] 타겟 이미지가 등록되었습니다!")
    else:
        st.markdown("**자체 데이터셋 파일 업로드**")
        uploaded_zip = st.file_uploader(
            "YOLO 포맷 데이터셋 업로드 (.zip)", 
            type=["zip"],
            disabled=st.session_state.pipeline_running
        )

# --- 등록된 타겟 이미지 레퍼런스 그리드 (실시간 반영 구역) ---
st.markdown("#### 🎯 현재 등록된 타겟 이미지 레퍼런스")
ref_cols = st.columns(5)
for idx, ref in enumerate(st.session_state.reference_images):
    with ref_cols[idx % 5]:
        # 가상 이미지 블록 그리기
        img_box = np.zeros((80, 100, 3), dtype=np.uint8)
        cv2.putText(img_box, "IMG", (30, 45), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (100, 100, 100), 1)
        cv2.rectangle(img_box, (5, 5), (95, 75), ref["color"], 3) # 클래스별 고유 색상 테두리
        st.image(img_box, use_container_width=True)
        st.caption(f"🏷️ {ref['name']}")

# --- STEP 2: 파이프라인 제어 및 제어 락(Lock) ---
st.markdown("---")
st.subheader("🤖 STEP 2: 파이프라인 구동 제어")

if "CCTV 아카이브" in data_source:
    # CCTV 모드일 때 구동 제어
    if not st.session_state.pipeline_running:
        if st.button("🚀 오토 라벨링 파이프라인 시작", type="primary", use_container_width=True):
            st.session_state.pipeline_running = True
            st.rerun()
    else:
        st.warning("⚠️ 현재 오토 라벨링 작업이 백엔드에서 단독 구동 중입니다. 데이터 오염을 막기 위해 입력창이 잠금(Lock)되었습니다.")
        if st.button("🛑 작업 중단 및 입력창 잠금 해제", type="secondary", use_container_width=True):
            st.session_state.pipeline_running = False
            st.rerun()
            
        # 가상 게이지 및 로그 연출
        progress_bar = st.progress(0)
        status_text = st.empty()
        for i in range(100):
            time.sleep(0.02)
            progress_bar.progress(i + 1)
            status_text.text(f"⏳ CCTV 프레임 분석 및 유사도 매칭 중... ({i+1}%)")
        status_text.text("✅ 1주일치 CCTV 오토 라벨링 정답지 빌드 완료!")
        st.session_state.pipeline_running = False
        st.session_state.auto_label_done = True
        st.rerun()
else:
    # 외부 데이터셋 직접 업로드 모드일 때
    if uploaded_zip:
        st.success("📂 외부 데이터셋 압축 파일이 정상적으로 인식되었습니다.")
        if st.button("📦 데이터셋 무결성 검사 및 로드", type="primary", use_container_width=True):
            with st.spinner("데이터셋 압축 해제 및 .yaml 구조 파싱 중..."):
                time.sleep(1.5)
            st.success("✅ 검사 완료! 기존 모델과 충돌 없는 완벽한 구조입니다.")
            st.session_state.auto_label_done = True

# --- STEP 3: 최종 패키징 ---
st.markdown("---")
st.subheader("📦 STEP 3: 재학습 데이터셋 패키징")

if st.session_state.auto_label_done:
    st.info(f"기존 지식과 신규 [{new_class_name}] 마이그레이션이 완료되었습니다. 내 컴퓨터(VS Code)로 이사할 준비가 되었습니다.")
    if st.button("💾 VS Code 전용 dataset.yaml 및 데이터셋 추출", use_container_width=True):
        st.toast("패키징 다운로드 준비 완료!", icon="✅")
        st.code(f"""
# 구조가 자동으로 병합된 dataset.yaml 예시
names:
  0: person
  1: helmet
  2: {new_class_name}   # 자동으로 추가된 새 도메인 클래스!
        """)
else:
    st.caption("💡 STEP 2 작업을 완료하면 최종 패키징 및 다운로드 메뉴가 활성화됩니다.")
