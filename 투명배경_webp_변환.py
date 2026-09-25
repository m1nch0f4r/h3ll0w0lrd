"""
투명배경(RGBA) PNG를 안전하게 WebP로 변환하는 스크립트.

- 실제 투명도(실루엣)는 그대로 유지
- 알파 채널의 최하위 2비트만 강제로 스크럽하여
  스텔스 메타데이터(LSB 스테가노그래피)를 물리적으로 파괴
- 시각적 변화는 256단계 중 평균 1단계 수준 (육안 무감지)

사용법:
    python 투명배경_webp_변환.py

같은 폴더 안의 모든 .png 파일을 처리해서 .webp로 저장하고,
원본 PNG는 "원본_PNG" 하위 폴더로 자동 이동합니다.
"""

import subprocess
from pathlib import Path
from PIL import Image
import numpy as np

INPUT_DIR = Path(".")
BACKUP_DIR = INPUT_DIR / "원본_PNG"
BACKUP_DIR.mkdir(exist_ok=True)

QUALITY = 85  # RGB 압축 품질 (0~100)

def scrub_alpha_lsb(png_path: Path) -> Path:
    """알파 채널 최하위 2비트를 스크럽한 임시 PNG 생성"""
    img = Image.open(png_path).convert("RGBA")
    arr = np.array(img)
    alpha = arr[:, :, 3].astype(np.int32)
    # 4의 배수로 반올림 (최하위 2비트 제거 효과)
    scrubbed = ((alpha + 2) // 4 * 4).clip(0, 255).astype(np.uint8)
    arr[:, :, 3] = scrubbed
    temp_path = png_path.with_name(png_path.stem + "_scrubbed_temp.png")
    Image.fromarray(arr, mode="RGBA").save(temp_path)
    return temp_path

def main():
    png_files = list(INPUT_DIR.glob("*.png"))
    if not png_files:
        print("PNG 파일을 찾지 못했습니다.")
        return

    for png_path in png_files:
        print(f"처리 중: {png_path.name}")
        temp_path = scrub_alpha_lsb(png_path)
        webp_path = png_path.with_suffix(".webp")

        subprocess.run([
            "cwebp", "-q", str(QUALITY), "-metadata", "none",
            str(temp_path), "-o", str(webp_path)
        ], check=True, capture_output=True)

        temp_path.unlink()  # 임시 파일 삭제
        png_path.rename(BACKUP_DIR / png_path.name)  # 원본 PNG 백업 폴더로 이동

    print(f"\n완료: {len(png_files)}개 파일 처리됨")
    print(f"원본 PNG는 '{BACKUP_DIR}' 폴더로 이동되었습니다.")

if __name__ == "__main__":
    main()
