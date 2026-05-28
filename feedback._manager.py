import os
import csv
from datetime import datetime

# 피드백 데이터를 저장할 파일 경로 설정 (루트 폴더에 자동으로 생성됩니다)
FEEDBACK_FILE_PATH = "data/feedback_logs.csv"

def init_feedback_system():
    """피드백 저장용 폴더와 파일이 없으면 자동으로 초기화하는 함수"""
    # data 폴더가 없으면 생성
    if not os.path.exists("data"):
        os.makedirs("data")
        
    # 오답노트 이미지/라벨 격리용 폴더 구조 미리 만들어두기
    if not os.path.exists("data/feedback_dataset/images"):
        os.makedirs("data/feedback_dataset/images")
    if not os.path.exists("data/feedback_dataset/labels"):
        os.makedirs("data/feedback_dataset/labels")

    # CSV 파일이 없으면 헤더(컬럼명)를 넣어서 생성
    if not os.path.exists(FEEDBACK_FILE_PATH):
        with open(FEEDBACK_FILE_PATH, mode="w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["log_id", "timestamp", "channel", "event_type", "status", "user_feedback"])

def save_user_feedback(log_id, channel, event_type, status, feedback_text):
    """
    사용자가 입력한 피드백을 백엔드 CSV 파일에 누적 저장하는 함수
    """
    # 폴더 및 파일 체크
    init_feedback_system()
    
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # CSV 파일에 데이터 추가 (Append 모드)
    with open(FEEDBACK_FILE_PATH, mode="a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([log_id, current_time, channel, event_type, status, feedback_text])
        
    print(f"[Backend] 로그 {log_id}에 대한 피드백이 성공적으로 기록되었습니다.")
    
    # 💡 [나중에 살릴 뼈대] 오탐(False)일 때 라벨 수정 및 파일 복사 로직 코딩 구역
    if "오탐" in status:
        # 1. 원본 이미지와 라벨 파일(.txt)을 끄집어낸다.
        # 2. data/feedback_dataset/ 폴더로 복사(shutil.copy)한다.
        # 3. .txt 파일을 열어 오인식된 클래스 번호를 수정하거나 삭제하는 스트링 연산을 한다.
        pass
