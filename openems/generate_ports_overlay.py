# -*- coding: utf-8 -*-
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from PIL import Image
import numpy as np

import os
script_dir = os.path.dirname(os.path.abspath(__file__))
repo_dir = os.path.dirname(script_dir)

# Load base image
im = Image.open(os.path.join(repo_dir, 'renders', 'top_render.png'))
w, h = im.size

fig, ax = plt.subplots(figsize=(18, 10.5), dpi=150)
ax.imshow(im)

# Calibration parameters for 34 mm x 29 mm board (Y_RF = 17.00 mm)
x0 = 419.0
scale_x = 33.92
y_rf = 672.8  # Y = 17.00 mm in KiCad (aligned with enclosure SMA cutouts)

# Ports coordinates in pixels
p1_x = x0 + 0.0 * scale_x       # X = -17.0 mm openEMS (KiCad 0.0 mm)
p2_x = x0 + 8.5 * scale_x       # X = -8.5 mm openEMS (KiCad 8.5 mm)
p3_x = x0 + 23.0 * scale_x      # X = +6.0 mm openEMS (KiCad 23.0 mm)
p4_x = x0 + 34.0 * scale_x      # X = +17.0 mm openEMS (KiCad 34.0 mm)

# Draw Input Trace highlight (Port 1 to Port 2)
trace_in = patches.Rectangle((p1_x, y_rf - 25), p2_x - p1_x, 50, 
                             linewidth=2.5, edgecolor='#00f0ff', facecolor='#00f0ff', alpha=0.35, zorder=3)
ax.add_patch(trace_in)

# Draw Output Trace highlight (Port 3 to Port 4)
trace_out = patches.Rectangle((p3_x, y_rf - 25), p4_x - p3_x, 50, 
                              linewidth=2.5, edgecolor='#00f0ff', facecolor='#00f0ff', alpha=0.35, zorder=3)
ax.add_patch(trace_out)

# Draw Central Ground / Isolation Zone (Port 2 to Port 3)
iso_zone = patches.Rectangle((p2_x, y_rf - 150), p3_x - p2_x, 300, 
                             linewidth=2, edgecolor='#ffaa00', facecolor='#ffaa00', alpha=0.18, linestyle='--', zorder=3)
ax.add_patch(iso_zone)

# Draw Ports with high-visibility markers
ports = [
    (1, p1_x, y_rf, 'Port 1: SMA RF In', '-17.0 mm', '0.0 mm', '#ff2222', (p1_x - 140, y_rf - 280)),
    (2, p2_x, y_rf, 'Port 2: In Match Pad', '-8.5 mm', '8.5 mm', '#ff8800', (p2_x - 40, y_rf - 340)),
    (3, p3_x, y_rf, 'Port 3: Out Match Pad', '+6.0 mm', '23.0 mm', '#00e676', (p3_x + 40, y_rf - 340)),
    (4, p4_x, y_rf, 'Port 4: SMA RF Out', '+17.0 mm', '34.0 mm', '#ff2222', (p4_x + 140, y_rf - 280)),
]

for p_num, px, py, name, x_em, x_kc, color, callout_pos in ports:
    # Outer target ring
    ax.add_patch(patches.Circle((px, py), 28, edgecolor=color, facecolor='none', linewidth=3.5, zorder=5))
    ax.add_patch(patches.Circle((px, py), 12, edgecolor='#ffffff', facecolor=color, linewidth=2, zorder=6))
    ax.scatter([px], [py], color='#ffffff', s=25, zorder=7)
    
    # Callout text box
    callout_text = f'PORT {p_num}\n{name}\nopenEMS X = {x_em}\nKiCad X = {x_kc}\nZ0 = 50 Ohm'
    ax.annotate(callout_text,
                xy=(px, py), xycoords='data',
                xytext=callout_pos, textcoords='data',
                bbox=dict(boxstyle='round,pad=0.6', fc='#111a24', ec=color, lw=2.5, alpha=0.92),
                arrowprops=dict(arrowstyle='->', connectionstyle='arc3,rad=0.15', color=color, lw=2.5),
                fontsize=11, fontweight='bold', color='#ffffff', ha='center', va='center', zorder=10)

# Add annotations for traces
ax.text((p1_x + p2_x)/2, y_rf + 85, 'INPUT CPWG TRACE\nL = 8.5 mm (Loss: 0.13 dB)', 
        ha='center', va='center', color='#00f0ff', fontsize=11, fontweight='bold',
        bbox=dict(boxstyle='round,pad=0.4', fc='#0b1924', ec='#00f0ff', lw=1.5, alpha=0.85), zorder=8)

ax.text((p3_x + p4_x)/2, y_rf + 85, 'OUTPUT CPWG TRACE\nL = 11.0 mm (Loss: 0.15 dB)', 
        ha='center', va='center', color='#00f0ff', fontsize=11, fontweight='bold',
        bbox=dict(boxstyle='round,pad=0.4', fc='#0b1924', ec='#00f0ff', lw=1.5, alpha=0.85), zorder=8)

ax.text((p2_x + p3_x)/2, y_rf + 215, 'ACTIVE CIRCUIT & MATCHING ZONE\nVia Fence & Ground Isolation (~76 dB S41 / S31)', 
        ha='center', va='center', color='#ffcc00', fontsize=11, fontweight='bold',
        bbox=dict(boxstyle='round,pad=0.4', fc='#1f1a08', ec='#ffaa00', lw=1.5, alpha=0.85), zorder=8)

# Title & Metadata Banner
ax.text(w/2, 60, 'openEMS 3D FDTD Electromagnetic Port Locations on Physical PCB (34x29mm)', 
        ha='center', va='center', color='#ffffff', fontsize=18, fontweight='bold',
        bbox=dict(boxstyle='square,pad=0.6', fc='#0a1520', ec='#00d084', lw=2, alpha=0.95), zorder=10)

# Legend Box
legend_text = (
    'PORT DEFINITIONS IN 4-PORT TOUCHSTONE MODEL (lna_board_full_4port.s4p):\n'
    '  * Port 1 (X = -17.0 mm): SMA RF Input end-launch interface (50 Ohm to generator)\n'
    '  * Port 2 (X = -8.5 mm): Input Match Pad (interface to discrete L1, C2, C1)\n'
    '  * Port 3 (X = +6.0 mm): Output Match Pad (interface to discrete C7 and collector tank)\n'
    '  * Port 4 (X = +17.0 mm): SMA RF Output end-launch interface (50 Ohm to receiver & bias-tee)\n'
    '  * Ref Port (GND): Solid copper ground pours on Layer 1 & Layer 2 + stitched via fence'
)
ax.text(w/2, h - 70, legend_text, 
        ha='center', va='center', color='#e0f2fe', fontsize=10.5, family='monospace',
        bbox=dict(boxstyle='round,pad=0.6', fc='#0a1118', ec='#38bdf8', lw=1.8, alpha=0.95), zorder=10)
ax.text(w/2, h - 70, legend_text, 
        ha='center', va='center', color='#e0f2fe', fontsize=10.5, family='monospace',
        bbox=dict(boxstyle='round,pad=0.6', fc='#0a1118', ec='#38bdf8', lw=1.8, alpha=0.95), zorder=10)

ax.set_xlim(0, w)
ax.set_ylim(h, 0)
ax.axis('off')
plt.tight_layout()

out_path = os.path.join(repo_dir, 'renders', 'openems_ports_pcb_overlay.png')
plt.savefig(out_path, bbox_inches='tight', pad_inches=0.1, dpi=160)
plt.close()
print(f'Successfully generated {out_path}')
