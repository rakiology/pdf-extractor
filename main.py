import os
import subprocess
import base64
import re
from pathlib import Path
import cv2
import numpy as np
import platform

def get_inkscape_path():
    return os.environ.get("INKSCAPE_PATH") or (
        r"C:\Program Files\Inkscape\bin\inkscape.exe" if platform.system() == "Windows" else "inkscape"
    )

def convert_pdf_to_svgs(pdf_path, output_dir="output_svgs"):
    INKSCAPE_PATH = get_inkscape_path()
    os.makedirs(output_dir, exist_ok=True)
    print(f"[INFO] Converting PDF to SVG using Inkscape at: {INKSCAPE_PATH}")

    from PyPDF2 import PdfReader
    reader = PdfReader(pdf_path)
    page_count = len(reader.pages)
    print(f"[INFO] PDF has {page_count} page(s)")

    valid_svgs = []

    for i in range(1, page_count + 1):
        output_svg = os.path.join(output_dir, f"page_{i}.svg")
        print(f"[INFO] Processing page {i} -> {output_svg}")

        try:
            result = subprocess.run([
                INKSCAPE_PATH,
                f"--pages={i}",
                pdf_path,
                "--export-type=svg",
                "--export-embed-images",  # embed PNGs
                "--export-filename", output_svg
            ], check=True, capture_output=True, text=True)
            print(f"[✓] Inkscape output: {result.stdout.strip()}")
        except subprocess.CalledProcessError as e:
            print(f"[❌] Inkscape failed on page {i}: {e.stderr.strip()}")
            continue

        try:
            with open(output_svg, 'r', encoding='utf-8') as f:
                svg_content = f.read()
        except Exception as e:
            print(f"[⚠️] Failed to read SVG {output_svg}: {e}")
            continue

        has_content = any(tag in svg_content for tag in ['<image', '<path', '<g'])
        is_black_rect = (
            svg_content.count('<rect') == 1 and
            any(c in svg_content for c in ['fill="#000000"', 'fill:#000000', 'fill="#000"', 'fill:#000"'])
        )

        if has_content and not is_black_rect:
            valid_svgs.append(output_svg)
            print(f"[✓] Valid SVG: {output_svg}")
        else:
            print(f"[→] Skipped SVG: {output_svg} (black/empty)")
            os.remove(output_svg)
    
    print(f"[INFO] Total valid SVGs: {len(valid_svgs)}")
    return valid_svgs

def extract_base64_images_from_svg(svg_path, output_dir=None):
    print(f"[INFO] Extracting base64 images from {svg_path}")
    with open(svg_path, "r", encoding="utf-8") as f:
        svg = f.read()

    matches = re.findall(r'data:image/png;base64,([A-Za-z0-9+/=]+)', svg)
    print(f"[INFO] Found {len(matches)} base64 PNG(s)")

    results = []
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    human_found = False
    sig_count = 1
    black_threshold = 10

    for i, match in enumerate(matches[:3]):
        print(f"[→] Decoding image #{i+1}")
        try:
            image_data = base64.b64decode(match)
            nparr = np.frombuffer(image_data, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            if img is None:
                print(f"[✗] Could not decode image #{i+1}")
                continue

            if (img < black_threshold).all():
                print(f"[→] Image #{i+1} skipped (all black)")
                continue

            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            faces = face_cascade.detectMultiScale(gray, 1.1, 4)
            if len(faces) > 0 and not human_found:
                print(f"[✓] Human face detected in image #{i+1}")
                results.append({"type": "human", "base64": match})
                human_found = True
            else:
                print(f"[✓] Signature #{sig_count} detected")
                results.append({"type": f"signature{sig_count}", "base64": match})
                sig_count += 1

            if len(results) == 2:
                print("[✓] Max 2 images reached, stopping.")
                break
        except Exception as e:
            print(f"[❌] Failed to process image #{i+1}: {e}")
    
    print(f"[INFO] Returning {len(results)} image(s)")
    return results

def extract_text_from_pdf(pdf_path):
    print(f"[INFO] Extracting text from {pdf_path}")
    from PyPDF2 import PdfReader
    reader = PdfReader(pdf_path)
    text = ""
    for i, page in enumerate(reader.pages):
        page_text = page.extract_text() or ""
        print(f"[→] Page {i+1}: {len(page_text)} characters")
        text += page_text
    return text

def extract_signatures_from_pdf(pdf_path):
    print(f"[INFO] extract_signatures_from_pdf: {pdf_path}")
    svg_dir = "output_svgs"
    signature_dir = "extracted_signatures"

    svg_paths = convert_pdf_to_svgs(pdf_path, svg_dir)
    all_signatures = []

    for svg in svg_paths:
        signatures = extract_base64_images_from_svg(svg, signature_dir)
        all_signatures.extend(signatures)

    print(f"[✓] Done: Extracted {len(all_signatures)} signature(s)")
    return all_signatures

def extract_all_from_pdf(pdf_path):
    print(f"[INFO] extract_all_from_pdf: {pdf_path}")
    svg_dir = "output_svgs"
    svg_paths = convert_pdf_to_svgs(pdf_path, svg_dir)
    images = []
    for svg in svg_paths:
        images.extend(extract_base64_images_from_svg(svg))
    text = extract_text_from_pdf(pdf_path)
    return {"images": images, "text": text}

if __name__ == "__main__":
    test_path = "e82245d0ff93266c.pdf"
    print("[TEST] Running extract_signatures_from_pdf...")
    extract_signatures_from_pdf(test_path)
