#!/bin/bash
# Canon 100D GUI 실행 스크립트

# 스크립트가 있는 디렉토리로 이동
cd "$(dirname "$0")"

# 카메라 프로세스 정리
echo "🔄 카메라 점유 프로세스 확인 중..."
killall "Image Capture" 2>/dev/null
killall ptpcamerad 2>/dev/null
echo "✅ 카메라 프로세스 정리 완료"
echo ""

# GUI 실행
echo "🚀 Canon 100D GUI 시작..."
./venv/bin/python gui.py

# GUI 종료 시
echo ""
echo "👋 프로그램 종료됨"
