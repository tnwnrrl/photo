#!/usr/bin/env python3
"""나노바나나 (Gemini 2.5 Flash Image) 테스트"""

from google import genai
from google.genai import types
from PIL import Image
import os

API_KEY = "AIzaSyC7vE-qt98sfkyX34DGZcdl8C0ZqOmkh3c"
INPUT_IMAGE = "/Users/jjh/Downloads/test.jpeg"
OUTPUT_IMAGE = "/Users/jjh/Downloads/test_nanobanana.png"

PROMPT = """이 사진을 심령사진처럼 편집해줘:
1. 인형의 눈을 붉게 빛나는 악마의 눈으로 바꿔줘
2. 사람들 주변 어두운 배경에 희미하게 일렁이는 유령 형체를 추가해줘
3. 원본 사람들의 얼굴, 옷, 포즈는 절대 바꾸지 마
4. 전체적으로 오싹한 분위기로"""

def main():
    print("=== 나노바나나 (Gemini) 심령사진 테스트 ===\n")

    # 1. 클라이언트 초기화
    print("1. Gemini 클라이언트 초기화...")
    client = genai.Client(api_key=API_KEY)

    # 2. 이미지 로드
    print(f"2. 이미지 로드: {INPUT_IMAGE}")
    image = Image.open(INPUT_IMAGE)
    print(f"   크기: {image.size}")

    # 3. API 호출
    print("\n3. 나노바나나 API 호출 중...")
    print(f"   프롬프트: {PROMPT[:50]}...")

    response = client.models.generate_content(
        model="gemini-2.5-flash-image",
        contents=[PROMPT, image],
        config=types.GenerateContentConfig(
            response_modalities=["TEXT", "IMAGE"]
        )
    )

    # 4. 결과 처리
    print("\n4. 결과 처리...")
    for part in response.parts:
        if part.text is not None:
            print(f"   텍스트 응답: {part.text}")
        elif part.inline_data is not None:
            # Blob 객체에서 이미지 데이터 추출
            image_data = part.inline_data.data
            with open(OUTPUT_IMAGE, "wb") as f:
                f.write(image_data)
            print(f"   이미지 저장: {OUTPUT_IMAGE}")

    print("\n완료!")

if __name__ == "__main__":
    main()
