#!/usr/bin/env python3
"""카메라 연결 문제 진단 스크립트 - 새 연결 로직 테스트"""

import time
from utils.camera import CameraConnection
import gphoto2 as gp

print("=" * 50)
print("카메라 연결 진단 (개선된 로직)")
print("=" * 50)

print("\n[1] 현재 카메라 목록 확인")
try:
    cameras = gp.Camera.autodetect()
    print(f"    발견된 카메라: {len(cameras)}개")
    for name, port in cameras:
        print(f"    - {name} @ {port}")
except Exception as e:
    print(f"    오류: {e}")

print("\n[2] 새 연결 로직으로 10회 테스트")
success_count = 0

for i in range(10):
    cam = CameraConnection()
    if cam.connect():
        success_count += 1
        print(f"    시도 {i+1:2d}: ✅ 성공 - {cam.camera_name}")
        cam.disconnect()
    else:
        print(f"    시도 {i+1:2d}: ❌ 실패")
    time.sleep(0.3)

print("\n[3] 결과")
print(f"    성공: {success_count}/10 ({success_count * 10}%)")

if success_count >= 7:
    print("    상태: 🟢 양호")
elif success_count >= 4:
    print("    상태: 🟡 불안정")
else:
    print("    상태: 🔴 문제 있음")
    print("\n[4] 권장 조치")
    print("    1. iPhone USB 연결 해제")
    print("    2. Canon 카메라만 USB 연결")
    print("    3. USB 케이블 뽑았다가 다시 연결")
