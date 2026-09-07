"""
render_masks.py - Automated 2D Artwork and Photomask Generation Pipeline
=======================================================================
Generates high-resolution raster (PNG) and vector (PDF, SVG) exports of:
  1. Top Solder Mask (F.Mask openings)
  2. Top Copper Photomask (B&W Positive film for etching/inspection)
  3. Top Copper Photomask (B&W Negative film for dry film / toner transfer)
  4. Top Copper Layer alone (F.Cu artwork with CPWG traces and GND plane)
  5. 2D Composite Engineering Preview (F.Cu + F.Mask + F.Silkscreen + Edge.Cuts)

Dependencies:
  - kicad-cli (KiCad 10+)
  - pypdfium2
  - Pillow (PIL)
  - numpy
"""

import subprocess
from pathlib import Path
import pypdfium2 as pdfium
import numpy as np
from PIL import Image, ImageOps

KICAD_CLI = r"D:\Programs\KiCad\bin\kicad-cli.exe"
PCB_PATH = Path(__file__).resolve().parent / "lna_fm_98mhz.kicad_pcb"
RENDERS_DIR = Path(__file__).resolve().parent / "renders"

def export_pdfs():
    """Export vector PDFs from KiCad CLI for all required mask layers."""
    RENDERS_DIR.mkdir(parents=True, exist_ok=True)

    jobs = [
        # (filename, layers, black_and_white, negative, bg_color)
        ("top_copper_layer.pdf", ["F.Cu", "Edge.Cuts"], False, False, "#ffffff"),
        ("top_copper_mask_pos.pdf", ["F.Cu", "Edge.Cuts"], True, False, "#ffffff"),
        ("top_copper_mask_neg.pdf", ["F.Cu", "Edge.Cuts"], True, True, "#000000"),
        ("top_solder_mask.pdf", ["F.Mask", "Edge.Cuts"], True, False, "#ffffff"),
        ("top_composite_2d.pdf", ["F.Cu", "F.Mask", "F.Silkscreen", "Edge.Cuts"], False, False, "#ffffff"),
    ]

    for filename, layers, bw, neg, bg_col in jobs:
        out_pdf = RENDERS_DIR / filename
        cmd = [
            KICAD_CLI, "pcb", "export", "pdf",
            "--layers", ",".join(layers),
            "--drill-shape-opt", "2",
            "--mode-single",
            "--bg-color", bg_col,
            "-o", str(out_pdf)
        ]
        if bw:
            cmd.append("--black-and-white")
        if neg:
            cmd.append("--negative")
        cmd.append(str(PCB_PATH))

        print(f"Exporting PDF: {filename}...")
        subprocess.run(cmd, check=True)

def export_svgs():
    """Export vector SVGs from KiCad CLI with exact board bounding box."""
    jobs = [
        ("top_copper_layer.svg", ["F.Cu", "Edge.Cuts"], False),
        ("top_solder_mask.svg", ["F.Mask", "Edge.Cuts"], False),
    ]

    for filename, layers, bw in jobs:
        out_svg = RENDERS_DIR / filename
        cmd = [
            KICAD_CLI, "pcb", "export", "svg",
            "--layers", ",".join(layers),
            "--page-size-mode", "2",
            "--exclude-drawing-sheet",
            "--drill-shape-opt", "2",
            "--mode-single",
            "-o", str(out_svg)
        ]
        if bw:
            cmd.append("--black-and-white")
        cmd.append(str(PCB_PATH))

        print(f"Exporting SVG: {filename}...")
        subprocess.run(cmd, check=True)

def render_and_crop(pdf_name, png_name, is_dark_bg=False, scale=12, pad=60):
    """Render PDF to high-resolution PNG with exact board bounds and symmetric margins."""
    pdf_path = RENDERS_DIR / pdf_name
    doc = pdfium.PdfDocument(str(pdf_path))
    page = doc[0]
    img = page.render(scale=scale).to_pil()
    arr = np.array(img)

    if is_dark_bg:
        mask = np.any(arr > 10, axis=-1)
    else:
        mask = np.any(arr < 245, axis=-1)

    y_indices, x_indices = np.where(mask)
    if len(y_indices) == 0:
        print(f"Warning: No content found in {pdf_name}")
        return

    x_min, x_max = x_indices.min(), x_indices.max()
    y_min, y_max = y_indices.min(), y_indices.max()

    # Crop to exact board outline
    board_crop = img.crop((x_min, y_min, x_max + 1, y_max + 1))

    # Add uniform symmetric border on all sides
    bg_color = (0, 0, 0) if is_dark_bg else (255, 255, 255)
    padded = ImageOps.expand(board_crop, border=pad, fill=bg_color)

    out_png = RENDERS_DIR / png_name
    padded.save(out_png)
    print(f"Generated {png_name} ({padded.size[0]}x{padded.size[1]} px)")

def export_schematic_renders():
    """Export vector and high-resolution cropped raster renders of KiCad schematic."""
    sch_path = Path(__file__).resolve().parent / "lna_fm_98mhz.kicad_sch"
    out_pdf = RENDERS_DIR / "schematic.pdf"
    clean_pdf = RENDERS_DIR / "schematic_clean.pdf"

    # Full schematic PDF with title sheet
    subprocess.run([KICAD_CLI, "sch", "export", "pdf", "-o", str(out_pdf), str(sch_path)], check=True)
    # Full schematic SVG
    subprocess.run([KICAD_CLI, "sch", "export", "svg", "-o", str(RENDERS_DIR), str(sch_path)], check=True)
    gen_svg = RENDERS_DIR / "lna_fm_98mhz.svg"
    if gen_svg.exists():
        import shutil
        shutil.move(str(gen_svg), str(RENDERS_DIR / "schematic.svg"))

    # Clean schematic PDF without sheet border for cropped zoom
    subprocess.run([KICAD_CLI, "sch", "export", "pdf", "-e", "-o", str(clean_pdf), str(sch_path)], check=True)
    doc = pdfium.PdfDocument(str(clean_pdf))
    page = doc[0]
    img = page.render(scale=5).to_pil()
    arr = np.array(img)
    bg_color = arr[0, 0]
    diff = np.abs(arr.astype(int) - bg_color.astype(int))
    mask = np.any(diff > 15, axis=-1)
    y_idx, x_idx = np.where(mask)
    cropped = img.crop((x_idx.min(), y_idx.min(), x_idx.max() + 1, y_idx.max() + 1))
    padded = ImageOps.expand(cropped, border=60, fill=tuple(bg_color[:3]))
    out_png = RENDERS_DIR / "schematic_zoomed.png"
    padded.save(out_png)
    print(f"Generated schematic_zoomed.png ({padded.size[0]}x{padded.size[1]} px)")
    doc.close()
    if clean_pdf.exists():
        try:
            clean_pdf.unlink()
        except OSError:
            pass

def main():
    print("=== Starting 2D Artwork & Mask Generation ===")
    export_pdfs()
    export_svgs()

    print("\n=== Rasterizing High-Resolution PNGs ===")
    render_and_crop("top_copper_layer.pdf", "top_copper_layer.png", is_dark_bg=False)
    render_and_crop("top_copper_mask_pos.pdf", "top_copper_mask_bw.png", is_dark_bg=False)
    render_and_crop("top_copper_mask_neg.pdf", "top_copper_mask_neg.png", is_dark_bg=True)
    render_and_crop("top_solder_mask.pdf", "top_solder_mask.png", is_dark_bg=False)
    render_and_crop("top_composite_2d.pdf", "top_composite_2d.png", is_dark_bg=False)

    print("\n=== Exporting Schematic Vector & Zoomed Artwork ===")
    export_schematic_renders()

    print("\nAll renders generated successfully in 'renders/' directory.")

if __name__ == "__main__":
    main()


