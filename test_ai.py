#!/usr/bin/env python3
"""Stability AI 심령사진 변환 테스트"""

import requests
import base64
from pathlib import Path

API_KEY = "sk-5r779RvKAzIe8hV3uKTnVEiyNMtEQIOuGda9nRdGNXih8Fv5"
INPUT_IMAGE = "/Users/jjh/Downloads/test.jpeg"
OUTPUT_IMAGE = "/Users/jjh/Downloads/test_ghost.png"

PROMPT = """Keep the original people, faces, poses, background and objects exactly the same.
Only add subtle supernatural effects:
1. Make the stuffed animal's eyes glow red with faint ominous aura
2. Add very subtle ghostly translucent apparitions in the dark background areas only
Preserve all original details, faces must remain identical"""

NEGATIVE_PROMPT = "different people, changed faces, altered poses, different clothing, different background, cartoon, anime"

def main():
    print("=== Stability AI 심령사진 테스트 ===")

    # 1. 이미지 로드
    print(f"\n1. 입력 이미지 로드: {INPUT_IMAGE}")
    with open(INPUT_IMAGE, "rb") as f:
        image_data = f.read()
    print(f"   이미지 크기: {len(image_data) / 1024:.1f} KB")

    # 2. API 호출 (image-to-image)
    print("\n2. Stability AI API 호출 중...")

    response = requests.post(
        "https://api.stability.ai/v2beta/stable-image/generate/sd3",
        headers={
            "Authorization": f"Bearer {API_KEY}",
            "Accept": "image/*"
        },
        files={
            "image": ("test.jpeg", image_data, "image/jpeg"),
        },
        data={
            "prompt": PROMPT,
            "negative_prompt": NEGATIVE_PROMPT,
            "strength": 0.35,
            "mode": "image-to-image",
            "output_format": "png",
            "model": "sd3.5-large"
        }
    )

    print(f"   응답 상태: {response.status_code}")

    if response.status_code == 200:
        # 3. 결과 저장
        with open(OUTPUT_IMAGE, "wb") as f:
            f.write(response.content)
        print(f"\n3. 변환 완료!")
        print(f"   출력 파일: {OUTPUT_IMAGE}")
        print(f"   파일 크기: {len(response.content) / 1024:.1f} KB")
    else:
        print(f"\n오류 발생:")
        print(response.text)

if __name__ == "__main__":
    main()
