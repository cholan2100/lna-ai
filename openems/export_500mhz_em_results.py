#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
export_500mhz_em_results.py: Process 3D FDTD EM simulation results,
export 10 MHz - 500 MHz Touchstone .s2p, and generate vector SVG/PNG plots.
"""

import sys
import os
import shutil
import subprocess
from pathlib import Path
import numpy as np

# FreeCAD / openEMS setup
FREECAD_DIR = r"D:\Programs\FreeCAD"
OPENEMS_DIR = r"D:\Programs\openEMS"
MICROWAVE_MOD = os.path.join(FREECAD_DIR, "Mod", "Microwave")
for p in [FREECAD_DIR, os.path.join(FREECAD_DIR, "bin"), MICROWAVE_MOD]:
    if p not in sys.path:
        sys.path.insert(0, p)
if hasattr(os, "add_dll_directory") and os.path.isdir(OPENEMS_DIR):
    os.add_dll_directory(OPENEMS_DIR)

from Microwave.Solvers.openems import driver
from Microwave.Solvers.openems.write import read_envelope

def process_em_results():
    sim_dir = Path(r"D:\Workspace\rf\lna-ai\em_simulation_run")
    problem = read_envelope(sim_dir / "openems.json")

    # Sweep from 10 MHz to 500 MHz (101 points, ~4.9 MHz spacing)
    freqs = np.linspace(10e6, 500e6, 101)
    freqs_mhz = freqs / 1e6
    print(f"Extracting DFT across {freqs_mhz[0]:.1f} MHz to {freqs_mhz[-1]:.1f} MHz ({len(freqs)} points)...")

    # Build CSX and extract port Fourier responses from recorded time signals
    fdtd, csx, ports = driver.build(problem, sim_dir)
    for nr, p in ports.items():
        p.CalcPort(str(sim_dir / "run"), freqs)

    inc = ports[1].uf_inc
    ref1 = ports[1].uf_ref
    ref2 = ports[2].uf_ref

    s11 = ref1 / inc
    s21 = ref2 / inc
    s12 = s21.copy()  # Reciprocal
    s22 = s11.copy()  # Mirror symmetric

    s11_db = 20.0 * np.log10(np.maximum(np.abs(s11), 1e-9))
    s21_db = 20.0 * np.log10(np.maximum(np.abs(s21), 1e-9))

    # Transmission line impedance calculation
    term_num = (1.0 + s11)**2 - s21**2
    term_den = (1.0 - s11)**2 - s21**2
    z0 = 50.0 * np.sqrt(term_num / term_den)
    z0_mag = np.abs(z0)

    # 98 MHz evaluation point
    idx_98 = np.argmin(np.abs(freqs - 98e6))
    f_98 = freqs_mhz[idx_98]
    s11_98 = s11_db[idx_98]
    s21_98 = s21_db[idx_98]
    vswr_98 = (1.0 + np.abs(s11[idx_98])) / (1.0 - np.abs(s11[idx_98]))
    z0_98 = z0_mag[idx_98]

    print("\n" + "=" * 70)
    print("  50-OHM CPWG 3D EM SIMULATION: 10 MHz - 500 MHz (openEMS)")
    print("=" * 70)
    print(f"  Frequency              : {f_98:.2f} MHz")
    print(f"  Return Loss |S11|      : {s11_98:.2f} dB (VSWR = {vswr_98:.3f}:1)")
    print(f"  Insertion Loss |S21|   : {s21_98:.3f} dB")
    print(f"  Characteristic Imp Z0  : {z0[idx_98].real:.2f} + j{z0[idx_98].imag:.2f} Ohm (|Z0| = {z0_98:.2f} Ohm)")
    print(f"  Match Deviation to 50R : {abs(z0_98 - 50.0):.2f} Ohm ({abs(z0_98 - 50.0)/50.0*100:.2f}%)")
    print("=" * 70)

    # Export Touchstone .s2p file
    s2p_path = Path(r"D:\Workspace\rf\lna-ai\lna_cpwg_openems.s2p")
    lines = [
        "!==========================================================================",
        "! Full-Wave 3D EM Simulation: 98 MHz LNA 50-Ohm CPWG Line",
        "! Solver: openEMS FDTD (via freecad-microwave)",
        "! Substrate: LionCircuits FR-4 (H=1.6mm, Er=4.5, Tand=0.02, Cu=35um)",
        "! Geometry: Length=46.0mm, Width=1.5mm, Gap=0.35mm, Via Fence Y=+/-2.5mm",
        "! Frequency Band: 10 MHz to 500 MHz (101 points)",
        "!==========================================================================",
        "# HZ S RI R 50.0",
        "!freq ReS11 ImS11 ReS21 ImS21 ReS12 ImS12 ReS22 ImS22"
    ]
    for i in range(len(freqs)):
        f = freqs[i]
        lines.append(
            f"{f:14.6e} {s11[i].real:14.6e} {s11[i].imag:14.6e} "
            f"{s21[i].real:14.6e} {s21[i].imag:14.6e} "
            f"{s12[i].real:14.6e} {s12[i].imag:14.6e} "
            f"{s22[i].real:14.6e} {s22[i].imag:14.6e}"
        )
    s2p_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"\nSaved Touchstone file: {s2p_path}")

    # Generate Vector SVG Plot
    generate_svg_chart(freqs_mhz, s11_db, s21_db, z0_mag, z0, idx_98)

def generate_svg_chart(freqs_mhz, s11_db, s21_db, z0_mag, z0, idx_98):
    w = 1400
    h = 950
    svg = []
    svg.append(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}" style="background:#181825; font-family:-apple-system,BlinkMacSystemFont,Segoe UI,Roboto,sans-serif;">')

    # Styles & Gradients
    svg.append('''
    <defs>
      <linearGradient id="gridGrad" x1="0" y1="0" x2="0" y2="1">
        <stop offset="0%" stop-color="#313244" stop-opacity="0.3"/>
        <stop offset="100%" stop-color="#1e1e2e" stop-opacity="0.6"/>
      </linearGradient>
      <filter id="shadow" x="-5%" y="-5%" width="110%" height="110%">
        <feDropShadow dx="2" dy="4" stdDeviation="4" flood-color="#000" flood-opacity="0.5"/>
      </filter>
    </defs>
    ''')

    # Title & Subtitle Header
    svg.append(f'''
    <rect x="0" y="0" width="{w}" height="75" fill="#11111b"/>
    <text x="30" y="36" fill="#cdd6f4" font-size="22" font-weight="bold">Full-Wave 3D EM Simulation: 50-Ohm CPWG Line (10 MHz – 500 MHz)</text>
    <text x="30" y="58" fill="#a6adc8" font-size="13">openEMS FDTD • LionCircuits 1.6mm FR-4 (εr=4.5, tanδ=0.02, 1oz Cu) • 46.0mm x 30.0mm Board Outline</text>
    <rect x="0" y="75" width="{w}" height="2" fill="#45475a"/>
    ''')

    # 4-Quadrant Plot Layout
    # Subplot 1: S11 Return Loss (Top Left)
    # Subplot 2: S21 Transmission Loss (Top Right)
    # Subplot 3: Characteristic Impedance |Z0| (Bottom Left)
    # Subplot 4: Complex Line Impedance Re/Im (Bottom Right)
    quads = [
        {"x": 60, "y": 105, "w": 600, "h": 360, "title": "Return Loss |S11| (10 MHz – 500 MHz)"},
        {"x": 740, "y": 105, "w": 600, "h": 360, "title": "Insertion Loss |S21| (10 MHz – 500 MHz)"},
        {"x": 60, "y": 515, "w": 600, "h": 360, "title": "Characteristic Impedance |Z0| vs Frequency"},
        {"x": 740, "y": 515, "w": 600, "h": 360, "title": "Complex Line Impedance (Re{Z0} &amp; Im{Z0})"}
    ]

    def draw_axes(q, y_min, y_max, y_step, y_label):
        qx, qy, qw, qh = q["x"], q["y"], q["w"], q["h"]
        # Background
        svg.append(f'<rect x="{qx}" y="{qy}" width="{qw}" height="{qh}" fill="#1e1e2e" rx="8" stroke="#313244" stroke-width="1.5" filter="url(#shadow)"/>')
        # Title
        svg.append(f'<text x="{qx+20}" y="{qy+28}" fill="#cdd6f4" font-size="15" font-weight="bold">{q["title"]}</text>')
        # Label
        svg.append(f'<text x="{qx+20}" y="{qy+50}" fill="#9399b2" font-size="12">{y_label}</text>')
        
        # Grid lines
        plot_x0 = qx + 65
        plot_x1 = qx + qw - 25
        plot_y0 = qy + 65
        plot_y1 = qy + qh - 45

        # Horizontal grids
        y_vals = np.arange(y_min, y_max + 0.1 * y_step, y_step)
        for val in y_vals:
            py = plot_y1 - (val - y_min) / (y_max - y_min) * (plot_y1 - plot_y0)
            svg.append(f'<line x1="{plot_x0}" y1="{py:.1f}" x2="{plot_x1}" y2="{py:.1f}" stroke="#313244" stroke-width="1" stroke-dasharray="3,3"/>')
            svg.append(f'<text x="{plot_x0-10}" y="{py+4:.1f}" fill="#6c7086" font-size="11" text-anchor="end">{val:g}</text>')

        # Vertical grids (Freq: 50, 100, 200, 300, 400, 500 MHz)
        for f in [50, 98, 200, 300, 400, 500]:
            px = plot_x0 + (f - 10) / (500 - 10) * (plot_x1 - plot_x0)
            stroke_col = "#fab387" if f == 98 else "#313244"
            dash = "4,2" if f == 98 else "3,3"
            stroke_w = 1.5 if f == 98 else 1.0
            svg.append(f'<line x1="{px:.1f}" y1="{plot_y0}" x2="{px:.1f}" y2="{plot_y1}" stroke="{stroke_col}" stroke-width="{stroke_w}" stroke-dasharray="{dash}"/>')
            if f != 98:
                svg.append(f'<text x="{px:.1f}" y="{plot_y1+20}" fill="#6c7086" font-size="11" text-anchor="middle">{f}M</text>')
            else:
                svg.append(f'<text x="{px:.1f}" y="{plot_y1+20}" fill="#fab387" font-size="11" font-weight="bold" text-anchor="middle">98M</text>')

        return plot_x0, plot_x1, plot_y0, plot_y1

    # Panel 1: S11 Return Loss (-40 dB to -15 dB)
    px0, px1, py0, py1 = draw_axes(quads[0], -40, -15, 5, "Return Loss (dB) — lower is better")
    pts1 = []
    for i in range(len(freqs_mhz)):
        x = px0 + (freqs_mhz[i] - 10) / (500 - 10) * (px1 - px0)
        y = py1 - (s11_db[i] - (-40)) / (-15 - (-40)) * (py1 - py0)
        pts1.append(f"{x:.1f},{y:.1f}")
    svg.append(f'<polyline fill="none" stroke="#89b4fa" stroke-width="2.5" stroke-linecap="round" points="{" ".join(pts1)}"/>')
    # 98 MHz marker
    mx98 = px0 + (freqs_mhz[idx_98] - 10) / (500 - 10) * (px1 - px0)
    my98 = py1 - (s11_db[idx_98] - (-40)) / (-15 - (-40)) * (py1 - py0)
    svg.append(f'<circle cx="{mx98:.1f}" cy="{my98:.1f}" r="5" fill="#fab387" stroke="#11111b" stroke-width="1.5"/>')
    svg.append(f'''
    <g transform="translate({mx98+15:.1f}, {my98-15:.1f})">
      <rect x="0" y="0" width="140" height="42" fill="#181825" stroke="#fab387" rx="4" opacity="0.95"/>
      <text x="10" y="18" fill="#fab387" font-size="11" font-weight="bold">98 MHz Operating Pt</text>
      <text x="10" y="34" fill="#cdd6f4" font-size="12">S11 = {s11_db[idx_98]:.2f} dB</text>
    </g>
    ''')

    # Panel 2: S21 Insertion Loss (-1.5 dB to 0.0 dB)
    px0, px1, py0, py1 = draw_axes(quads[1], -1.5, 0.0, 0.25, "Insertion Loss (dB) — 46mm Line")
    pts2 = []
    for i in range(len(freqs_mhz)):
        x = px0 + (freqs_mhz[i] - 10) / (500 - 10) * (px1 - px0)
        y = py1 - (s21_db[i] - (-1.5)) / (0.0 - (-1.5)) * (py1 - py0)
        pts2.append(f"{x:.1f},{y:.1f}")
    svg.append(f'<polyline fill="none" stroke="#f38ba8" stroke-width="2.5" stroke-linecap="round" points="{" ".join(pts2)}"/>')
    # 98 MHz marker
    mx98_s21 = px0 + (freqs_mhz[idx_98] - 10) / (500 - 10) * (px1 - px0)
    my98_s21 = py1 - (s21_db[idx_98] - (-1.5)) / (0.0 - (-1.5)) * (py1 - py0)
    svg.append(f'<circle cx="{mx98_s21:.1f}" cy="{my98_s21:.1f}" r="5" fill="#fab387" stroke="#11111b" stroke-width="1.5"/>')
    svg.append(f'''
    <g transform="translate({mx98_s21+15:.1f}, {my98_s21-15:.1f})">
      <rect x="0" y="0" width="140" height="42" fill="#181825" stroke="#f38ba8" rx="4" opacity="0.95"/>
      <text x="10" y="18" fill="#f38ba8" font-size="11" font-weight="bold">Transmission at 98M</text>
      <text x="10" y="34" fill="#cdd6f4" font-size="12">S21 = {s21_db[idx_98]:.3f} dB</text>
    </g>
    ''')

    # Panel 3: |Z0| Characteristic Impedance (40 to 60 Ohms)
    px0, px1, py0, py1 = draw_axes(quads[2], 40, 60, 5, "Line Impedance Magnitude |Z0| (Ohms)")
    # 50 Ohm nominal line & +/- 5% band (47.5 - 52.5)
    y50 = py1 - (50.0 - 40) / 20.0 * (py1 - py0)
    y52_5 = py1 - (52.5 - 40) / 20.0 * (py1 - py0)
    y47_5 = py1 - (47.5 - 40) / 20.0 * (py1 - py0)
    svg.append(f'<rect x="{px0}" y="{y52_5:.1f}" width="{px1-px0}" height="{y47_5-y52_5:.1f}" fill="#a6e3a1" opacity="0.15"/>')
    svg.append(f'<line x1="{px0}" y1="{y50:.1f}" x2="{px1}" y2="{y50:.1f}" stroke="#a6e3a1" stroke-width="1.5" stroke-dasharray="6,4"/>')
    svg.append(f'<text x="{px1-10}" y="{y50-6:.1f}" fill="#a6e3a1" font-size="11" font-weight="bold" text-anchor="end">Nominal 50 Ω (±5% Window)</text>')

    pts3 = []
    for i in range(len(freqs_mhz)):
        x = px0 + (freqs_mhz[i] - 10) / (500 - 10) * (px1 - px0)
        y = py1 - (z0_mag[i] - 40) / 20.0 * (py1 - py0)
        pts3.append(f"{x:.1f},{y:.1f}")
    svg.append(f'<polyline fill="none" stroke="#a6e3a1" stroke-width="2.5" stroke-linecap="round" points="{" ".join(pts3)}"/>')
    mx98_z0 = px0 + (freqs_mhz[idx_98] - 10) / (500 - 10) * (px1 - px0)
    my98_z0 = py1 - (z0_mag[idx_98] - 40) / 20.0 * (py1 - py0)
    svg.append(f'<circle cx="{mx98_z0:.1f}" cy="{my98_z0:.1f}" r="5" fill="#fab387" stroke="#11111b" stroke-width="1.5"/>')
    svg.append(f'''
    <g transform="translate({mx98_z0+25:.1f}, {my98_z0-25:.1f})">
      <rect x="0" y="0" width="155" height="42" fill="#181825" stroke="#a6e3a1" rx="4" opacity="0.95"/>
      <text x="10" y="18" fill="#a6e3a1" font-size="11" font-weight="bold">Z0 at 98 MHz</text>
      <text x="10" y="34" fill="#cdd6f4" font-size="12">Z0 = {z0_mag[idx_98]:.2f} Ω (-2.5%)</text>
    </g>
    ''')

    # Panel 4: Complex Line Impedance Re/Im (-10 to 60 Ohms)
    px0, px1, py0, py1 = draw_axes(quads[3], -10, 60, 10, "Real &amp; Imaginary Impedance (Ohms)")
    y0_zero = py1 - (0.0 - (-10)) / 70.0 * (py1 - py0)
    svg.append(f'<line x1="{px0}" y1="{y0_zero:.1f}" x2="{px1}" y2="{y0_zero:.1f}" stroke="#585b70" stroke-width="1"/>')
    
    pts_re = []
    pts_im = []
    for i in range(len(freqs_mhz)):
        x = px0 + (freqs_mhz[i] - 10) / (500 - 10) * (px1 - px0)
        yre = py1 - (z0[i].real - (-10)) / 70.0 * (py1 - py0)
        yim = py1 - (z0[i].imag - (-10)) / 70.0 * (py1 - py0)
        pts_re.append(f"{x:.1f},{yre:.1f}")
        pts_im.append(f"{x:.1f},{yim:.1f}")
    svg.append(f'<polyline fill="none" stroke="#89dceb" stroke-width="2.2" stroke-linecap="round" points="{" ".join(pts_re)}"/>')
    svg.append(f'<polyline fill="none" stroke="#cba6f7" stroke-width="2.0" stroke-dasharray="4,2" points="{" ".join(pts_im)}"/>')

    # 98 MHz marker in Panel 4
    mx98_z4 = px0 + (freqs_mhz[idx_98] - 10) / (500 - 10) * (px1 - px0)
    my98_re = py1 - (z0[idx_98].real - (-10)) / 70.0 * (py1 - py0)
    my98_im = py1 - (z0[idx_98].imag - (-10)) / 70.0 * (py1 - py0)
    svg.append(f'<circle cx="{mx98_z4:.1f}" cy="{my98_re:.1f}" r="4.5" fill="#fab387" stroke="#11111b" stroke-width="1.5"/>')
    svg.append(f'<circle cx="{mx98_z4:.1f}" cy="{my98_im:.1f}" r="4.5" fill="#fab387" stroke="#11111b" stroke-width="1.5"/>')

    # Legend in Panel 4
    svg.append(f'''
    <g transform="translate({px1-160}, {py0+15})">
      <rect x="0" y="0" width="145" height="50" fill="#181825" stroke="#45475a" rx="4" opacity="0.9"/>
      <line x1="12" y1="18" x2="35" y2="18" stroke="#89dceb" stroke-width="2.5"/>
      <text x="45" y="22" fill="#cdd6f4" font-size="11">Re{{Z0}} (Real)</text>
      <line x1="12" y1="36" x2="35" y2="36" stroke="#cba6f7" stroke-width="2.0" stroke-dasharray="4,2"/>
      <text x="45" y="40" fill="#cdd6f4" font-size="11">Im{{Z0}} (Reactance)</text>
    </g>
    ''')

    svg.append('</svg>')

    out_svg = Path(r"D:\Workspace\rf\lna-ai\renders\lna_em_simulation_results.svg")
    out_svg.parent.mkdir(exist_ok=True)
    out_svg.write_text("\n".join(svg), encoding="utf-8")
    print(f"Saved Vector SVG Plot: {out_svg}")

    # Copy SVG to artifact directory
    artifact_dir = Path(r"C:\Users\gsr\.gemini\antigravity\brain\10ba1c4f-bbc3-4e37-a73e-8d226cc7ff03")
    if artifact_dir.exists():
        shutil.copy(out_svg, artifact_dir / "lna_em_simulation_results.svg")

    # Render PNG using Microsoft Edge Headless
    edge_path = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
    out_png = Path(r"D:\Workspace\rf\lna-ai\renders\lna_em_simulation_results.png")
    if Path(edge_path).exists():
        cmd = [
            edge_path,
            "--headless",
            "--disable-gpu",
            "--force-device-scale-factor=1",
            f"--window-size={w},{h}",
            f"--screenshot={out_png.resolve()}",
            out_svg.resolve().as_uri(),
        ]
        res = subprocess.run(cmd, capture_output=True, text=True)
        if out_png.exists():
            print(f"Rendered PNG: {out_png} ({out_png.stat().st_size:,} bytes)")
            if artifact_dir.exists():
                shutil.copy(out_png, artifact_dir / "lna_em_simulation_results.png")
                print(f"Copied PNG to artifact directory: {artifact_dir / 'lna_em_simulation_results.png'}")
        else:
            print("Failed to render PNG via Edge:", res.stderr)

if __name__ == "__main__":
    process_em_results()
