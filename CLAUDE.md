# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Canon EOS 100D 카메라 모니터링 앱. USB로 사진 자동 다운로드 후 AI 변환(나노바나나) 또는 PNG 오버레이 합성. tkinter GUI 제공.

## Commands

```bash
# 앱 실행 (권장)
./start.command

# 수동 GUI 실행
python3 gui.py

# 카메라 연결 테스트
python3 -c "
from utils.camera import CameraConnection
camera = CameraConnection()
print('✅ Connected' if camera.connect() else '❌ Failed')
camera.disconnect()
"

# AI 변환 테스트 (나노바나나)
python3 test_nanobanana.py

# macOS 빌드
./build_mac.sh

# 의존성 설치
brew install libgphoto2 pkg-config
pip install -r requirements.txt
pip install google-genai  # AI 변환용
```

## Architecture

```
Camera (Canon 100D)
    ↓ USB (gphoto2)
CameraConnection.get_all_files()
    ↓
gui.py monitoring_loop()
    ↓ Download to downloaded_photos/
    ↓
┌───────────────────────────────────────┐
│ 처리 방식 선택                          │
├───────────────────────────────────────┤
│ [AI 변환]              [오버레이 합성]   │
│ AITransformer         ImageProcessor  │
│ (Gemini 2.5 Flash)    (Pillow RGBA)   │
└───────────────────────────────────────┘
    ↓
Save to processed_photos/
```

### Core Files

| 파일 | 역할 |
|------|------|
| `gui.py` | 메인 진입점. tkinter GUI, 백그라운드 모니터링 스레드 |
| `utils/camera.py` | `CameraConnection` - gphoto2 래퍼, 연결/다운로드 |
| `utils/image_processor.py` | `ImageProcessor` - Pillow RGBA 오버레이 합성 |
| `utils/ai_transformer.py` | `AITransformer` - Gemini API 래퍼 (계획) |
| `config.json` | 런타임 설정 (경로, 프롬프트, API 키) |
| `processed_files.json` | 처리 완료 파일 추적 (중복 방지) |

## macOS Camera Connection Issue

**문제**: macOS 데몬(`ptpcamerad`, `mscamerad-xpc`, `icdd`)이 USB 카메라 자동 점유

**에러**: `[-53] Could not claim the USB device`

**해결**: `start.command`가 `pkill -9`로 프로세스 강제 종료 후 3회 재시도. 실패 시 USB 케이블 물리적 재연결.

## AI 변환 (나노바나나)

**모델**: `gemini-2.5-flash-image` (Google Gemini)

**비용**: ~$0.039/장 (약 50원), 무료 티어 ~500장/일

**처리 시간**: ~10초/장

**핵심**: 프롬프트에 "원본 얼굴, 옷, 포즈는 절대 바꾸지 마" 필수

```python
# 테스트 코드 패턴
from google import genai
from google.genai import types
from PIL import Image

client = genai.Client(api_key="...")
response = client.models.generate_content(
    model="gemini-2.5-flash-image",
    contents=[prompt, Image.open(path)],
    config=types.GenerateContentConfig(response_modalities=["TEXT", "IMAGE"])
)
# 이미지 추출: part.inline_data.data
```

## Key Constraints

- **macOS only**: gphoto2가 Windows 미지원
- **JPG only**: RAW 파일 미지원
- **오버레이 RGBA 필수**: RGB 모드는 투명도 무시
- **카메라 연결 유지**: 모니터링 중 단일 연결 유지, 중지 시에만 해제

## Upgrade Plan

`plan.md` 참조 - PNG 오버레이 → AI 변환(나노바나나)으로 전환 계획
