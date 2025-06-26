import os
import subprocess
import base64
import re
from pathlib import Path
import cv2
import numpy as np

def convert_pdf_to_svgs(pdf_path, output_dir="output_svgs"):
    INKSCAPE_PATH = r"C:\Program Files\Inkscape\bin\inkscape.exe"  # Adjust if different
    os.makedirs(output_dir, exist_ok=True)
    print(f"Converting PDF to SVG pages...")

    # Inkscape CLI uses 1-based indexing for PDF pages
    page_count = get_pdf_page_count(pdf_path)
    valid_svgs = []

    for i in range(1, page_count + 1):
        output_svg = os.path.join(output_dir, f"page_{i}.svg")
        subprocess.run([
            INKSCAPE_PATH,
            f"--pages={i}",
            pdf_path,
            "--export-type=svg",
            "--export-filename", output_svg
        ], check=True)
        with open(output_svg, 'r', encoding='utf-8') as f:
            svg_content = f.read()
        # Improved heuristic: skip if only a single black rect or no content
        has_content = any(tag in svg_content for tag in ['<image', '<path', '<g'])
        is_black_rect = (
            svg_content.count('<rect') == 1 and
            ('fill="#000000"' in svg_content or 'fill:#000000' in svg_content or 'fill="#000"' in svg_content or 'fill:#000"' in svg_content)
        )
        if has_content and not is_black_rect:
            valid_svgs.append(output_svg)
            print(f"Saved SVG: {output_svg}")
        else:
            print(f"Skipped black/empty SVG: {output_svg}")
            os.remove(output_svg)
    
    return valid_svgs

def get_pdf_page_count(pdf_path):
    from PyPDF2 import PdfReader
    reader = PdfReader(pdf_path)
    return len(reader.pages)

def extract_base64_images_from_svg(svg_path, output_dir=None):
    with open(svg_path, "r", encoding="utf-8") as f:
        svg = f.read()

    matches = re.findall(r'data:image/png;base64,([A-Za-z0-9+/=]+)', svg)
    results = []
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    human_found = False
    sig_count = 1
    black_threshold = 10  # pixel intensity threshold for black

    # Only process up to 3 images, but will filter out black ones
    for i, match in enumerate(matches[:3]):
        image_data = base64.b64decode(match)
        nparr = np.frombuffer(image_data, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if img is None:
            continue
        # Check if image is (almost) all black
        if (img < black_threshold).all():
            continue  # skip black image
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, 1.1, 4)
        if len(faces) > 0 and not human_found:
            results.append({"type": "human", "base64": match})
            human_found = True
        else:
            results.append({"type": f"signature{sig_count}", "base64": match})
            sig_count += 1
        if len(results) == 2:
            break  # Only output 2 images
    return results

def extract_text_from_pdf(pdf_path):
    from PyPDF2 import PdfReader
    reader = PdfReader(pdf_path)
    text = ""
    for page in reader.pages:
        text += page.extract_text() or ""
    return text

def extract_signatures_from_pdf(pdf_path):
    svg_dir = "output_svgs"
    signature_dir = "extracted_signatures"
    
    svg_paths = convert_pdf_to_svgs(pdf_path, svg_dir)
    all_signatures = []

    for svg in svg_paths:
        signatures = extract_base64_images_from_svg(svg, signature_dir)
        all_signatures.extend(signatures)
    
    print(f"\n✅ Done: Extracted {len(all_signatures)} signature image(s).")
    return all_signatures

def extract_all_from_pdf(pdf_path):
    svg_dir = "output_svgs"
    svg_paths = convert_pdf_to_svgs(pdf_path, svg_dir)
    images = []
    for svg in svg_paths:
        images.extend(extract_base64_images_from_svg(svg))
    text = extract_text_from_pdf(pdf_path)
    return {"images": images, "text": text}

# Example usage
if __name__ == "__main__":
    pdf_path = "e82245d0ff93266c.pdf"  # Replace with your file
    extract_signatures_from_pdf(pdf_path)
