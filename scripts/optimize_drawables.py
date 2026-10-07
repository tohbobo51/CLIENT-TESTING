#!/usr/bin/env python3
"""
optimize_drawables.py
Converts large PNG assets in Android res/drawable directories to WebP to reduce APK size.
Works with cwebp, ffmpeg, or python Pillow if available.
"""

from pathlib import Path
import os
import shutil
import subprocess
import sys

def optimize_res_directory(res_dir: Path) -> None:
    if not res_dir.exists():
        print(f"[!] Directory {res_dir} not found.")
        return

    # Check available tool
    has_cwebp = shutil.which("cwebp") is not None
    
    # Try importing PIL
    has_pil = False
    try:
        from PIL import Image
        has_pil = True
    except ImportError:
        pass

    print(f"[*] Optimizing drawables in {res_dir} (cwebp={has_cwebp}, PIL={has_pil})")

    png_files = list(res_dir.rglob("*.png"))
    converted_count = 0
    saved_bytes = 0

    for png_path in png_files:
        # Skip small icons < 40KB to avoid any compatibility quirk with legacy 9-patch
        file_size = png_path.stat().st_size
        if file_size < 40 * 1024 or png_path.name.endswith(".9.png"):
            continue

        webp_path = png_path.with_suffix(".webp")
        converted = False

        if has_cwebp:
            ret = subprocess.run(["cwebp", "-q", "85", str(png_path), "-o", str(webp_path)],
                                 stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            converted = (ret.returncode == 0)
        elif has_pil:
            try:
                with Image.open(png_path) as img:
                    img.save(webp_path, "WEBP", quality=85)
                converted = True
            except Exception as e:
                print(f"[!] PIL failed on {png_path.name}: {e}")

        if converted and webp_path.exists():
            new_size = webp_path.stat().st_size
            if new_size < file_size:
                saved = file_size - new_size
                saved_bytes += saved
                png_path.unlink() # Remove old png
                converted_count += 1
                print(f"    [+] {png_path.name}: {file_size//1024}KB -> {new_size//1024}KB (saved {saved//1024}KB)")
            else:
                webp_path.unlink() # Keep original if webp is larger

    print(f"[*] Optimized {converted_count} images. Total saved: {saved_bytes // 1024} KB")

def main() -> None:
    root = Path(sys.argv[1] if len(sys.argv) > 1 else "client").resolve()
    res_dir = root / "app/src/main/res"
    optimize_res_directory(res_dir)

if __name__ == "__main__":
    main()
