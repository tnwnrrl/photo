#!/bin/bash
# 카메라 강제 연결 스크립트 - 더 aggressive한 버전

cd "$(dirname "$0")"

echo "🔧 카메라 강제 연결 시도..."
echo ""

# 1. 모든 카메라 프로세스 PID 찾아서 강제 종료
echo "1️⃣ 모든 카메라 프로세스 강제 종료..."
pkill -9 -f "ptpcamerad"
pkill -9 -f "mscamerad"
pkill -9 -f "icdd"
pkill -9 -f "cameracaptured"
pkill -9 -f "appleh16camerad"
killall -9 "Image Capture" 2>/dev/null

echo "   ✓ 프로세스 종료 완료"
sleep 1

# 2. 즉시 카메라 연결 시도 (프로세스 재시작 전)
echo ""
echo "2️⃣ 카메라 연결 시도 (프로세스 재시작 전)..."

./venv/bin/python -c "
import sys
sys.path.insert(0, '.')
from utils.camera import CameraConnection
import time

try:
    camera = CameraConnection()
    if camera.connect():
        print('✅ 카메라 연결 성공!')
        print(f'   모델: {camera.camera_name}')

        # 파일 개수 확인
        files = camera.get_file_list()
        print(f'   카메라 내 파일: {len(files)}개')

        camera.disconnect()
        print('')
        print('==================================================')
        print('✅ 연결 성공! 이제 GUI를 실행하세요:')
        print('   더블클릭: run_gui.command')
        print('   또는 터미널: python gui.py')
        print('==================================================')
        sys.exit(0)
    else:
        print('❌ 카메라 연결 실패')
        sys.exit(1)
except Exception as e:
    print(f'❌ 오류: {e}')
    sys.exit(1)
"

if [ $? -eq 0 ]; then
    exit 0
fi

# 3. 실패 시 재시도
echo ""
echo "3️⃣ 재시도 중..."
sleep 2

# 다시 프로세스 종료
pkill -9 -f "ptpcamerad"
pkill -9 -f "mscamerad"
sleep 1

./venv/bin/python -c "
import sys
sys.path.insert(0, '.')
from utils.camera import CameraConnection

try:
    camera = CameraConnection()
    if camera.connect():
        print('✅ 재시도 성공!')
        print(f'   모델: {camera.camera_name}')
        camera.disconnect()
        print('')
        print('GUI 실행: run_gui.command 더블클릭')
        sys.exit(0)
    else:
        print('❌ 재시도도 실패')
        sys.exit(1)
except Exception as e:
    print(f'❌ 재시도 오류: {e}')
    sys.exit(1)
"

if [ $? -ne 0 ]; then
    echo ""
    echo "=================================================="
    echo "❌ 연결 실패"
    echo "=================================================="
    echo ""
    echo "💡 추가 해결 방법:"
    echo "   1. 카메라 전원을 끄고 다시 켜기"
    echo "   2. 다른 USB 포트에 연결"
    echo "   3. USB 허브 사용 중이면 Mac에 직접 연결"
    echo "   4. Mac 재부팅 (최후의 수단)"
    echo ""
fi
