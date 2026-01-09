#!/usr/bin/env python3
"""Stability AI Inpainting 테스트 - 인형 눈만 변경"""

import requests
from PIL import Image, ImageDraw
import io

API_KEY = "sk-5r779RvKAzIe8hV3uKTnVEiyNMtEQIOuGda9nRdGNXih8Fv5"
INPUT_IMAGE = "/Users/jjh/Downloads/test.jpeg"
MASK_IMAGE = "/Users/jjh/Downloads/mask.png"
OUTPUT_IMAGE = "/Users/jjh/Downloads/test_inpaint.png"

def create_mask():
    """인형 눈 위치에 마스크 생성"""
    # 원본 이미지 크기 확인
    img = Image.open(INPUT_IMAGE)
    width, height = img.size
    print(f"원본 이미지 크기: {width} x {height}")

    # 검은 배경 마스크 (검은색 = 유지, 흰색 = 변경)
    mask = Image.new("L", (width, height), 0)
    draw = ImageDraw.Draw(mask)

    # 인형 눈 위치 추정 (이미지 중앙 하단)
    # 인형이 대략 중앙에 있고, 눈은 인형 얼굴 상단부
    center_x = width // 2
    eye_y = int(height * 0.58)  # 약 58% 높이

    # 왼쪽 눈, 오른쪽 눈 (타원형)
    eye_width = 25
    eye_height = 20
    eye_gap = 35

    # 왼쪽 눈
    left_eye = (center_x - eye_gap - eye_width, eye_y - eye_height,
                center_x - eye_gap + eye_width, eye_y + eye_height)
    # 오른쪽 눈
    right_eye = (center_x + eye_gap - eye_width, eye_y - eye_height,
                 center_x + eye_gap + eye_width, eye_y + eye_height)

    draw.ellipse(left_eye, fill=255)
    draw.ellipse(right_eye, fill=255)

    mask.save(MASK_IMAGE)
    print(f"마스크 저장: {MASK_IMAGE}")
    return mask

def main():
    print("=== Stability AI Inpainting 테스트 ===\n")

    # 1. 마스크 생성
    print("1. 마스크 생성 중...")
    create_mask()

    # 2. 이미지 로드
    print("\n2. 이미지 로드...")
    with open(INPUT_IMAGE, "rb") as f:
        image_data = f.read()
    with open(MASK_IMAGE, "rb") as f:
        mask_data = f.read()

    # 3. Inpainting API 호출
    print("\n3. Stability AI Inpainting API 호출 중...")

    response = requests.post(
        "https://api.stability.ai/v2beta/stable-image/edit/inpaint",
        headers={
            "Authorization": f"Bearer {API_KEY}",
            "Accept": "image/*"
        },
        files={
            "image": ("image.jpeg", image_data, "image/jpeg"),
            "mask": ("mask.png", mask_data, "image/png"),
        },
        data={
            "prompt": "glowing red demonic eyes, evil sinister red glowing eyes, horror, ominous",
            "negative_prompt": "normal eyes, brown eyes, black eyes, cute, friendly",
            "output_format": "png",
        }
    )

    print(f"   응답 상태: {response.status_code}")

    if response.status_code == 200:
        with open(OUTPUT_IMAGE, "wb") as f:
            f.write(response.content)
        print(f"\n4. 변환 완료!")
        print(f"   출력 파일: {OUTPUT_IMAGE}")
    else:
        print(f"\n오류:")
        print(response.text)

if __name__ == "__main__":
    main()
