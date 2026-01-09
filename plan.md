# Canon 100D 사진 앱 - AI 심령사진 변환 업그레이드 계획

## 목표
카메라에서 다운로드한 사진을 AI API로 "심령사진" 스타일로 변환

---

## API 선택: 나노바나나 (Google Gemini 2.5 Flash Image)

### 선택 이유
- ✅ **테스트 결과 최고 품질** - 인물/배경 완벽 유지, 효과만 추가
- ✅ **한국어 프롬프트 지원** - 자연스러운 지시 가능
- ✅ **합리적 가격** - 이미지당 약 $0.039 (약 50원)

### 비용 예상

| 사용량 | 월 비용 | 비고 |
|--------|---------|------|
| 100장/월 | ~$4 (약 5,000원) | 소규모 사용 |
| 500장/월 | ~$20 (약 26,000원) | 중간 사용 |
| 1,000장/월 | ~$39 (약 51,000원) | 대규모 사용 |

### 가격 상세
- **이미지당**: $0.039 (1,290 output tokens × $30/1M tokens)
- **무료 티어**: Google AI Studio에서 1,500장/일 (테스트용)
- **경쟁사 비교**: DALL-E 3 ($0.040), Midjourney ($0.28)보다 저렴하거나 동등

---

## AI 프롬프트

### 메인 프롬프트 (한국어 - 테스트 검증됨)
```
이 사진을 심령사진처럼 편집해줘:
1. 인형의 눈을 붉게 빛나는 악마의 눈으로 바꿔줘
2. 사람들 주변 어두운 배경에 희미하게 일렁이는 유령 형체를 추가해줘
3. 원본 사람들의 얼굴, 옷, 포즈는 절대 바꾸지 마
4. 전체적으로 오싹한 분위기로
```

### 핵심 포인트
- **원본 유지 강조** 필수: "얼굴, 옷, 포즈는 절대 바꾸지 마"
- 나노바나나는 이 지시를 잘 따름

---

## 구현 범위

### 새로 생성할 파일
| 파일 | 용도 |
|------|------|
| `utils/ai_transformer.py` | Gemini API 래퍼 클래스 |

### 수정할 파일
| 파일 | 변경 내용 |
|------|----------|
| `config.json` | AI 설정 섹션 추가 |
| `gui.py` | 오버레이 UI 제거, AI 프롬프트 편집 UI 추가 |
| `requirements.txt` | `google-genai` 추가 |

### 제거
- `utils/image_processor.py`의 `composite_image()` 사용 중단
- GUI의 오버레이 선택 UI 제거

---

## config.json 신규 스키마

```json
{
  "ai": {
    "provider": "gemini",
    "api_key": "AIzaSy...",
    "model": "gemini-2.5-flash-image",
    "prompt": "이 사진을 심령사진처럼 편집해줘:\n1. 인형의 눈을 붉게 빛나는 악마의 눈으로 바꿔줘\n2. 사람들 주변 어두운 배경에 희미하게 일렁이는 유령 형체를 추가해줘\n3. 원본 사람들의 얼굴, 옷, 포즈는 절대 바꾸지 마\n4. 전체적으로 오싹한 분위기로",
    "timeout_seconds": 120
  },
  "processing": {
    "sequential_naming": true,
    "naming_prefix": "ghost_"
  }
}
```

---

## 핵심 클래스 설계

### AITransformer (`utils/ai_transformer.py`)

```python
from google import genai
from google.genai import types
from PIL import Image

class AITransformer:
    def __init__(self, config: dict):
        self.client = genai.Client(api_key=config['ai']['api_key'])
        self.model = config['ai'].get('model', 'gemini-2.5-flash-image')
        self.prompt = config['ai']['prompt']
        self.timeout = config['ai'].get('timeout_seconds', 120)

    def transform_image(self, input_path: str, output_path: str) -> bool:
        """이미지를 AI로 변환하고 저장"""
        image = Image.open(input_path)

        response = self.client.models.generate_content(
            model=self.model,
            contents=[self.prompt, image],
            config=types.GenerateContentConfig(
                response_modalities=["TEXT", "IMAGE"]
            )
        )

        for part in response.parts:
            if part.inline_data is not None:
                with open(output_path, "wb") as f:
                    f.write(part.inline_data.data)
                return True
        return False

    def get_next_filename(self, output_folder: str, prefix: str = "ghost_") -> str:
        """다음 순차 파일명 생성"""
        # ghost_001.png, ghost_002.png, ...
        pass
```

### 처리 흐름

```
원본 다운로드 → AITransformer.transform_image()
    ├─ PIL로 이미지 로드
    ├─ Gemini API 요청 (프롬프트 + 이미지)
    ├─ 응답에서 이미지 데이터 추출
    └─ processed_photos/ghost_XXX.png 저장
```

---

## GUI 변경

### 제거
- 오버레이 이미지 선택 프레임

### 추가
- AI 설정 프레임:
  - API Key 입력 (마스킹)
  - 프롬프트 편집 (Text 위젯, 여러 줄)
  - "설정 저장" 버튼
  - 비용 표시 (예상 월 비용)

---

## 구현 단계

### Phase 1: 기반 구조
- [ ] `utils/ai_transformer.py` 생성
- [ ] `AITransformer` 클래스 구현
- [ ] `config.json` AI 섹션 추가

### Phase 2: API 연동
- [ ] google-genai SDK 설치
- [ ] Gemini API 호출 구현
- [ ] 에러 처리 (타임아웃, 인증 실패, 할당량 초과)

### Phase 3: GUI 업데이트
- [ ] 오버레이 UI 제거
- [ ] AI 설정 프레임 추가
- [ ] 프롬프트 편집 기능

### Phase 4: 통합
- [ ] `monitoring_loop`에서 `AITransformer` 호출
- [ ] 순차 파일명 저장 (ghost_001.png...)
- [ ] 전체 흐름 테스트

---

## 검증 방법

1. **단위 테스트**: `test_nanobanana.py` 실행 - 완료 ✅
2. **통합 테스트**: 카메라 → 다운로드 → AI 변환 → 저장 전체 흐름
3. **GUI 테스트**: 프롬프트 편집 후 저장 → config.json 반영 확인

---

## 의존성 추가

```
# requirements.txt
google-genai>=1.0.0
Pillow>=10.0.0
```

---

## 참고 자료

- [Gemini API 가격](https://ai.google.dev/gemini-api/docs/pricing)
- [Gemini 이미지 생성 문서](https://ai.google.dev/gemini-api/docs/image-generation)
- [나노바나나 가이드](https://blog.laozhang.ai/api-guides/gemini-25-flash-image-api/)
