#!/bin/bash
# 카메라 연결 문제 해결 스크립트

echo "🔧 카메라 연결 문제 해결 중..."

# 1. 모든 카메라 관련 프로세스 강제 종료
echo "1️⃣ 카메라 점유 프로세스 종료..."
killall "Image Capture" 2>/dev/null
killall ptpcamerad 2>/dev/null
killall icdd 2>/dev/null
killall cameracaptured 2>/dev/null
pkill -f "mscamerad" 2>/dev/null

# 2. 잠시 대기 (프로세스가 완전히 종료될 시간)
sleep 2

# 3. 재시작된 프로세스 다시 종료
echo "2️⃣ 재시작된 프로세스 재종료..."
killall ptpcamerad 2>/dev/null
pkill -f "mscamerad" 2>/dev/null

sleep 1

# 4. 카메라 연결 테스트
echo "3️⃣ 카메라 연결 테스트..."
cd "$(dirname "$0")"
./venv/bin/python -c "
from utils.camera import CameraConnection

try:
    with CameraConnection() as camera:
        if camera.is_connected:
            print('✅ 카메라 연결 성공!')
            print(f'   모델: {camera.camera_name}')
        else:
            print('❌ 카메라 연결 실패')
            print('')
            print('💡 해결 방법:')
            print('   1. 카메라 USB 케이블을 뽑았다가 다시 연결')
            print('   2. 5초 대기')
            print('   3. 이 스크립트를 다시 실행: ./fix_camera.sh')
except Exception as e:
    print(f'❌ 오류: {e}')
    print('')
    print('💡 해결 방법:')
    print('   1. 카메라 USB 케이블을 뽑았다가 다시 연결')
    print('   2. 5초 대기')
    print('   3. 이 스크립트를 다시 실행: ./fix_camera.sh')
"

echo ""
echo "=================================================="
echo "카메라 연결이 성공하면 GUI를 실행하세요:"
echo "   python gui.py"
echo "=================================================="
