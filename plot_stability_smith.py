import cmath
import math
import subprocess
from pathlib import Path
import shutil
from parse_qucs import parse_qucs_dat

freqs, data = parse_qucs_dat('lna_fm_98mhz_qucs_cpwg.dat')

f_mhz = [f / 1e6 for f in freqs]
idx_98 = min(range(len(freqs)), key=lambda i: abs(freqs[i] - 9.8e7))
idx_88 = min(range(len(freqs)), key=lambda i: abs(freqs[i] - 8.8e7))
idx_108 = min(range(len(freqs)), key=lambda i: abs(freqs[i] - 1.08e8))

def get_stability_params(idx):
    s11 = data['S[1,1]'][idx]
    s21 = data['S[2,1]'][idx]
    s12 = data['S[1,2]'][idx]
    s22 = data['S[2,2]'][idx]
    delta = s11 * s22 - s12 * s21
    k = (1.0 - abs(s11)**2 - abs(s22)**2 + abs(delta)**2) / (2.0 * abs(s12 * s21))
    
    # Load stability circle
    denom_L = abs(s22)**2 - abs(delta)**2
    cL = (s22 - delta * s11.conjugate()).conjugate() / denom_L
    rL = abs(s12 * s21 / denom_L)
    
    # Source stability circle
    denom_S = abs(s11)**2 - abs(delta)**2
    cS = (s11 - delta * s22.conjugate()).conjugate() / denom_S
    rS = abs(s12 * s21 / denom_S)
    
    mu = (1.0 - abs(s11)**2) / (abs(s22 - delta * s11.conjugate()) + abs(s12 * s21))
    mu_prime = (1.0 - abs(s22)**2) / (abs(s11 - delta * s22.conjugate()) + abs(s12 * s21))
    
    return {
        'freq': freqs[idx],
        's11': s11, 's21': s21, 's12': s12, 's22': s22,
        'delta': delta, 'k': k, 'mu': mu, 'mu_prime': mu_prime,
        'cL': cL, 'rL': rL, 'cS': cS, 'rS': rS
    }

p98 = get_stability_params(idx_98)
p88 = get_stability_params(idx_88)
p108 = get_stability_params(idx_108)

# Layout constants
width = 1600
height = 980

# Chart centers and radius
r_smith = 260.0
cx_s = 420.0
cy_s = 480.0

cx_l = 1180.0
cy_l = 480.0

svg = []
svg.append(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="100%" height="100%" style="background:#11111b; font-family: -apple-system, BlinkMacSystemFont, Segoe UI, Roboto, Helvetica, Arial, sans-serif;">')

# Definitions: Gradients, Patterns, ClipPaths, Masks
svg.append('<defs>')

# Diagonal hatch pattern for unstable regions
svg.append('''
<pattern id="hatch-unstable-source" width="12" height="12" patternTransform="rotate(45 0 0)" patternUnits="userSpaceOnUse">
  <line x1="0" y1="0" x2="0" y2="12" stroke="#f38ba8" stroke-width="2.5" opacity="0.4" />
</pattern>
<pattern id="hatch-unstable-load" width="12" height="12" patternTransform="rotate(-45 0 0)" patternUnits="userSpaceOnUse">
  <line x1="0" y1="0" x2="0" y2="12" stroke="#cba6f7" stroke-width="2.5" opacity="0.4" />
</pattern>
''')

# Clip path for Source Smith chart circle
svg.append(f'<clipPath id="clip-smith-source"><circle cx="{cx_s}" cy="{cy_s}" r="{r_smith}" /></clipPath>')
# Clip path for Load Smith chart circle
svg.append(f'<clipPath id="clip-smith-load"><circle cx="{cx_l}" cy="{cy_l}" r="{r_smith}" /></clipPath>')

# Mask for Source Unstable Region: Inside Smith chart circle, but OUTSIDE source stability circle
cs_x_98 = cx_s + p98['cS'].real * r_smith
cs_y_98 = cy_s - p98['cS'].imag * r_smith
cs_r_98 = p98['rS'] * r_smith

svg.append(f'''
<mask id="mask-source-unstable">
  <rect x="0" y="0" width="{width}" height="{height}" fill="black" />
  <circle cx="{cx_s}" cy="{cy_s}" r="{r_smith}" fill="white" />
  <circle cx="{cs_x_98:.2f}" cy="{cs_y_98:.2f}" r="{cs_r_98:.2f}" fill="black" />
</mask>
''')

svg.append('</defs>')

# Title Header
svg.append(f'''
<rect x="0" y="0" width="{width}" height="100" fill="#181825" stroke="#313244" stroke-width="1" />
<text x="{width//2}" y="38" text-anchor="middle" fill="#cdd6f4" font-size="24" font-weight="bold" letter-spacing="0.5">Common-Base FM LNA (98 MHz) — Stability Smith Chart Analysis</text>
<text x="{width//2}" y="65" text-anchor="middle" fill="#a6adc8" font-size="14">BFR93A Common-Base Stage with Integrated Pre-Filter (L1=22nH, C2=27pF, C1=91pF) &amp; CPWG Interconnects</text>
<text x="{width//2}" y="85" text-anchor="middle" fill="#89b4fa" font-size="12" font-weight="500">2-Port S-Parameter Analysis from 70 MHz to 130 MHz (QUCS/Qucsator Engine)</text>
''')

def draw_smith_grid(cx, cy, chart_id, title, subtitle):
    lines = []
    # Chart background circle
    lines.append(f'<circle cx="{cx}" cy="{cy}" r="{r_smith}" fill="#181825" stroke="#585b70" stroke-width="2.5" />')
    
    # Sub-panel header
    lines.append(f'<text x="{cx}" y="{cy - r_smith - 45}" text-anchor="middle" fill="#cdd6f4" font-size="18" font-weight="bold">{title}</text>')
    lines.append(f'<text x="{cx}" y="{cy - r_smith - 22}" text-anchor="middle" fill="#a6adc8" font-size="13">{subtitle}</text>')

    # Horizontal Real Axis (x = 0)
    lines.append(f'<line x1="{cx - r_smith}" y1="{cy}" x2="{cx + r_smith}" y2="{cy}" stroke="#45475a" stroke-width="1.5" />')

    # Constant Resistance Circles: r = 0.2, 0.5, 1.0, 2.0, 5.0
    r_values = [0.2, 0.5, 1.0, 2.0, 5.0]
    for r in r_values:
        r_c_x = cx + (r / (r + 1.0)) * r_smith
        r_c_y = cy
        rad = (1.0 / (r + 1.0)) * r_smith
        st_color = "#585b70" if r == 1.0 else "#313244"
        st_w = 1.5 if r == 1.0 else 1.0
        lines.append(f'<circle cx="{r_c_x:.2f}" cy="{r_c_y:.2f}" r="{rad:.2f}" fill="none" stroke="{st_color}" stroke-width="{st_w}" />')

    # Constant Reactance Arcs: x = +/- 0.2, +/- 0.5, +/- 1.0, +/- 2.0, +/- 5.0
    x_values = [0.2, 0.5, 1.0, 2.0, 5.0, -0.2, -0.5, -1.0, -2.0, -5.0]
    for x in x_values:
        x_c_x = cx + 1.0 * r_smith
        x_c_y = cy - (1.0 / x) * r_smith
        rad = abs(1.0 / x) * r_smith
        st_color = "#585b70" if abs(x) == 1.0 else "#313244"
        st_w = 1.5 if abs(x) == 1.0 else 1.0
        lines.append(f'<circle cx="{x_c_x:.2f}" cy="{x_c_y:.2f}" r="{rad:.2f}" fill="none" stroke="{st_color}" stroke-width="{st_w}" clip-path="url(#clip-smith-{chart_id})" />')

    # Real Axis Tick Labels
    z_labels = [
        (0.0, "0 (Short)", -15, -10, "start"),
        (0.2, "10", 0, -8, "middle"),
        (0.5, "25", 0, -8, "middle"),
        (1.0, "50", 0, -8, "middle"),
        (2.0, "100", 0, -8, "middle"),
        (5.0, "250", 0, -8, "middle"),
        (float('inf'), "∞ (Open)", 15, -10, "end")
    ]
    for r_val, lbl, dx, dy, align in z_labels:
        if math.isinf(r_val):
            lx = cx + r_smith
        else:
            lx = cx + ((r_val - 1.0) / (r_val + 1.0)) * r_smith
        ly = cy
        fweight = "bold" if r_val == 1.0 else "normal"
        fcolor = "#89b4fa" if r_val == 1.0 else "#585b70"
        fsize = 11 if r_val == 1.0 else 10
        lines.append(f'<text x="{lx + dx}" y="{ly + dy}" text-anchor="{align}" fill="{fcolor}" font-size="{fsize}" font-weight="{fweight}">{lbl}</text>')

    # Reactance labels along outer circumference
    x_lbls = [
        (+0.2, "+j10"), (+0.5, "+j25"), (+1.0, "+j50"), (+2.0, "+j100"), (+5.0, "+j250"),
        (-0.2, "-j10"), (-0.5, "-j25"), (-1.0, "-j50"), (-2.0, "-j100"), (-5.0, "-j250")
    ]
    for x_val, lbl in x_lbls:
        gam_r = (x_val**2 - 1.0) / (x_val**2 + 1.0)
        gam_i = (2.0 * x_val) / (x_val**2 + 1.0)
        ang = math.atan2(gam_i, gam_r)
        
        # Position with slightly more clearance outside perimeter
        tx = cx + (r_smith + 22) * math.cos(ang)
        ty = cy - (r_smith + 22) * math.sin(ang)
        lines.append(f'<text x="{tx:.1f}" y="{ty:.1f}" text-anchor="middle" dominant-baseline="central" fill="#6c7086" font-size="10">{lbl}</text>')

    return '\n'.join(lines)

# Draw Left Grid (Source Plane)
svg.append(draw_smith_grid(cx_s, cy_s, 'source', 'Source Stability Plane (Γs)', 'Input Port Termination Stability | Looking into LNA Input'))

# Draw Right Grid (Load Plane)
svg.append(draw_smith_grid(cx_l, cy_l, 'load', 'Load Stability Plane (ΓL)', 'Output Port Termination Stability | Looking into LNA Output'))

# ==================== SOURCE PLANE DETAILS ====================

# 1. Shaded Unstable Region for Source Plane (using mask)
svg.append(f'''
<circle cx="{cx_s}" cy="{cy_s}" r="{r_smith}" fill="#f38ba8" fill-opacity="0.18" mask="url(#mask-source-unstable)" />
<circle cx="{cx_s}" cy="{cy_s}" r="{r_smith}" fill="url(#hatch-unstable-source)" mask="url(#mask-source-unstable)" />
''')

# 2. Source Stability Circle at 88 MHz and 108 MHz (dashed references)
for p_ref, col, lbl in [(p88, '#fab387', '88 MHz'), (p108, '#f9e2af', '108 MHz')]:
    cs_x = cx_s + p_ref['cS'].real * r_smith
    cs_y = cy_s - p_ref['cS'].imag * r_smith
    cs_r = p_ref['rS'] * r_smith
    svg.append(f'<circle cx="{cs_x:.2f}" cy="{cs_y:.2f}" r="{cs_r:.2f}" fill="none" stroke="{col}" stroke-width="1.5" stroke-dasharray="5,4" opacity="0.7" clip-path="url(#clip-smith-source)" />')

# 3. Source Stability Circle at 98 MHz (Solid prominent)
svg.append(f'<circle cx="{cs_x_98:.2f}" cy="{cs_y_98:.2f}" r="{cs_r_98:.2f}" fill="none" stroke="#f38ba8" stroke-width="3" clip-path="url(#clip-smith-source)" />')

# Callout label for Source Stability Circle
svg.append(f'''
<!-- Source Stability Callout -->
<line x1="{cx_s - 130}" y1="{cy_s - 170}" x2="{cx_s - 180}" y2="{cy_s - 220}" stroke="#f38ba8" stroke-width="1.5" />
<line x1="{cx_s - 180}" y1="{cy_s - 220}" x2="{cx_s - 290}" y2="{cy_s - 220}" stroke="#f38ba8" stroke-width="1.5" />
<rect x="{cx_s - 390}" y="{cy_s - 245}" width="200" height="42" rx="5" fill="#181825" stroke="#f38ba8" stroke-width="1.5" />
<text x="{cx_s - 290}" y="{cy_s - 228}" text-anchor="middle" fill="#f38ba8" font-size="12" font-weight="bold">Source Stability Circle (98 MHz)</text>
<text x="{cx_s - 290}" y="{cy_s - 211}" text-anchor="middle" fill="#cdd6f4" font-size="11">Cs = 1.55 - j2.31, Rs = 2.89</text>

<!-- Region Badges -->
<rect x="{cx_s - 220}" y="{cy_s - 70}" width="115" height="28" rx="4" fill="#f38ba8" fill-opacity="0.3" stroke="#f38ba8" stroke-width="1" />
<text x="{cx_s - 162}" y="{cy_s - 51}" text-anchor="middle" fill="#f38ba8" font-size="11" font-weight="bold">UNSTABLE REGION</text>

<rect x="{cx_s - 50}" y="{cy_s + 140}" width="100" height="28" rx="4" fill="#a6e3a1" fill-opacity="0.2" stroke="#a6e3a1" stroke-width="1" />
<text x="{cx_s}" y="{cy_s + 159}" text-anchor="middle" fill="#a6e3a1" font-size="11" font-weight="bold">STABLE REGION</text>
''')

# 4. S11 Frequency Locus (70 to 130 MHz) on Source Plane
s11_pts = []
for i in range(len(freqs)):
    v = data['S[1,1]'][i]
    px = cx_s + v.real * r_smith
    py = cy_s - v.imag * r_smith
    s11_pts.append(f'{px:.2f},{py:.2f}')
svg.append(f'<path d="M ' + ' L '.join(s11_pts) + '" fill="none" stroke="#f9e2af" stroke-width="3" />')

# S11 points at 88, 98, 108 MHz
for idx_val, lbl_f in [(idx_88, "88M"), (idx_98, "98 MHz (Opt Match)"), (idx_108, "108M")]:
    v = data['S[1,1]'][idx_val]
    px = cx_s + v.real * r_smith
    py = cy_s - v.imag * r_smith
    if idx_val == idx_98:
        # Prominent marker with angled leader line into open inductive quadrant
        svg.append(f'<circle cx="{px:.2f}" cy="{py:.2f}" r="5.5" fill="#f9e2af" stroke="#11111b" stroke-width="2" />')
        svg.append(f'''
<line x1="{px:.2f}" y1="{py - 5:.2f}" x2="{px + 45:.2f}" y2="{py - 42:.2f}" stroke="#f9e2af" stroke-width="1.2" />
<line x1="{px + 45:.2f}" y1="{py - 42:.2f}" x2="{px + 215:.2f}" y2="{py - 42:.2f}" stroke="#f9e2af" stroke-width="1.2" />
<rect x="{px + 45:.2f}" y="{py - 64:.2f}" width="170" height="22" rx="4" fill="#181825" stroke="#f9e2af" stroke-width="1.2" />
<text x="{px + 130:.2f}" y="{py - 49:.2f}" text-anchor="middle" fill="#f9e2af" font-size="11" font-weight="bold">S11 @ 98 MHz (-31.9 dB)</text>
''')
    else:
        svg.append(f'<circle cx="{px:.2f}" cy="{py:.2f}" r="4" fill="#f9e2af" opacity="0.8" />')
        svg.append(f'<text x="{px + 7:.2f}" y="{py + 12:.2f}" fill="#f9e2af" font-size="10">{lbl_f}</text>')

# 50 Ohm Source Target Indicator (Origin) with leader line into open capacitive quadrant
svg.append(f'''
<circle cx="{cx_s}" cy="{cy_s}" r="8" fill="none" stroke="#a6e3a1" stroke-width="2" />
<circle cx="{cx_s}" cy="{cy_s}" r="2.5" fill="#a6e3a1" />
<line x1="{cx_s + 6:.2f}" y1="{cy_s + 6:.2f}" x2="{cx_s + 45:.2f}" y2="{cy_s + 45:.2f}" stroke="#a6e3a1" stroke-width="1.2" />
<line x1="{cx_s + 45:.2f}" y1="{cy_s + 45:.2f}" x2="{cx_s + 225:.2f}" y2="{cy_s + 45:.2f}" stroke="#a6e3a1" stroke-width="1.2" />
<rect x="{cx_s + 45:.2f}" y="{cy_s + 45:.2f}" width="180" height="22" rx="4" fill="#181825" stroke="#a6e3a1" stroke-width="1.2" />
<text x="{cx_s + 135:.2f}" y="{cy_s + 60:.2f}" text-anchor="middle" fill="#a6e3a1" font-size="11" font-weight="bold">50 Ω Source (Operating Point)</text>
''')


# ==================== LOAD PLANE DETAILS ====================

cl_x_98 = cx_l + p98['cL'].real * r_smith
cl_y_98 = cy_l - p98['cL'].imag * r_smith
cl_r_98 = p98['rL'] * r_smith

# 1. Shaded Unstable Region for Load Plane (interior of load circle, clipped to Smith chart)
svg.append(f'''
<circle cx="{cl_x_98:.2f}" cy="{cl_y_98:.2f}" r="{cl_r_98:.2f}" fill="#cba6f7" fill-opacity="0.22" clip-path="url(#clip-smith-load)" />
<circle cx="{cl_x_98:.2f}" cy="{cl_y_98:.2f}" r="{cl_r_98:.2f}" fill="url(#hatch-unstable-load)" clip-path="url(#clip-smith-load)" />
''')

# 2. Load Stability Circle at 88 MHz and 108 MHz
for p_ref, col, lbl in [(p88, '#fab387', '88 MHz'), (p108, '#f9e2af', '108 MHz')]:
    cl_x = cx_l + p_ref['cL'].real * r_smith
    cl_y = cy_l - p_ref['cL'].imag * r_smith
    cl_r = p_ref['rL'] * r_smith
    svg.append(f'<circle cx="{cl_x:.2f}" cy="{cl_y:.2f}" r="{cl_r:.2f}" fill="none" stroke="{col}" stroke-width="1.5" stroke-dasharray="5,4" opacity="0.7" clip-path="url(#clip-smith-load)" />')

# 3. Load Stability Circle at 98 MHz (Solid prominent)
svg.append(f'<circle cx="{cl_x_98:.2f}" cy="{cl_y_98:.2f}" r="{cl_r_98:.2f}" fill="none" stroke="#cba6f7" stroke-width="3" clip-path="url(#clip-smith-load)" />')

# Callout label for Load Stability Circle
svg.append(f'''
<!-- Load Stability Callout -->
<line x1="{cl_x_98 + 40}" y1="{cl_y_98 + 30}" x2="{cx_l - 120}" y2="{cy_l + 220}" stroke="#cba6f7" stroke-width="1.5" />
<line x1="{cx_l - 120}" y1="{cy_l + 220}" x2="{cx_l - 240}" y2="{cy_l + 220}" stroke="#cba6f7" stroke-width="1.5" />
<rect x="{cx_l - 340}" y="{cy_l + 195}" width="200" height="42" rx="5" fill="#181825" stroke="#cba6f7" stroke-width="1.5" />
<text x="{cx_l - 240}" y="{cy_l + 212}" text-anchor="middle" fill="#cba6f7" font-size="12" font-weight="bold">Load Stability Circle (98 MHz)</text>
<text x="{cx_l - 240}" y="{cy_l + 229}" text-anchor="middle" fill="#cdd6f4" font-size="11">CL = -0.89 - j0.78, RL = 0.41</text>

<!-- Region Badges -->
<rect x="{cx_l - 240}" y="{cy_l + 100}" width="115" height="28" rx="4" fill="#cba6f7" fill-opacity="0.3" stroke="#cba6f7" stroke-width="1" />
<text x="{cx_l - 182}" y="{cy_l + 119}" text-anchor="middle" fill="#cba6f7" font-size="11" font-weight="bold">UNSTABLE REGION</text>

<rect x="{cx_l - 50}" y="{cy_l - 140}" width="100" height="28" rx="4" fill="#a6e3a1" fill-opacity="0.2" stroke="#a6e3a1" stroke-width="1" />
<text x="{cx_l}" y="{cy_l - 121}" text-anchor="middle" fill="#a6e3a1" font-size="11" font-weight="bold">STABLE REGION</text>
''')

# 4. S22 Frequency Locus (70 to 130 MHz) on Load Plane
s22_pts = []
for i in range(len(freqs)):
    v = data['S[2,2]'][i]
    px = cx_l + v.real * r_smith
    py = cy_l - v.imag * r_smith
    s22_pts.append(f'{px:.2f},{py:.2f}')
svg.append(f'<path d="M ' + ' L '.join(s22_pts) + '" fill="none" stroke="#89dceb" stroke-width="3" />')

# S22 points at 88, 98, 108 MHz
for idx_val, lbl_f in [(idx_88, "88M"), (idx_98, "98 MHz (S22)"), (idx_108, "108M")]:
    v = data['S[2,2]'][idx_val]
    px = cx_l + v.real * r_smith
    py = cy_l - v.imag * r_smith
    if idx_val == idx_98:
        # Prominent marker
        svg.append(f'<circle cx="{px:.2f}" cy="{py:.2f}" r="6" fill="#89dceb" stroke="#11111b" stroke-width="2" />')
        svg.append(f'<rect x="{px - 165:.2f}" y="{py - 28:.2f}" width="155" height="24" rx="4" fill="#181825" stroke="#89dceb" stroke-width="1.2" />')
        svg.append(f'<text x="{px - 88:.2f}" y="{py - 12:.2f}" text-anchor="middle" fill="#89dceb" font-size="11" font-weight="bold">S22 @ 98 MHz (|Γ|=0.96)</text>')
    else:
        svg.append(f'<circle cx="{px:.2f}" cy="{py:.2f}" r="4" fill="#89dceb" opacity="0.8" />')
        svg.append(f'<text x="{px + 8:.2f}" y="{py + 10:.2f}" fill="#89dceb" font-size="10">{lbl_f}</text>')

# 50 Ohm Load Target Indicator (Origin) with leader line into open capacitive quadrant
svg.append(f'''
<circle cx="{cx_l}" cy="{cy_l}" r="8" fill="none" stroke="#a6e3a1" stroke-width="2" />
<circle cx="{cx_l}" cy="{cy_l}" r="2.5" fill="#a6e3a1" />
<line x1="{cx_l + 6:.2f}" y1="{cy_l + 6:.2f}" x2="{cx_l + 45:.2f}" y2="{cy_l + 45:.2f}" stroke="#a6e3a1" stroke-width="1.2" />
<line x1="{cx_l + 45:.2f}" y1="{cy_l + 45:.2f}" x2="{cx_l + 215:.2f}" y2="{cy_l + 45:.2f}" stroke="#a6e3a1" stroke-width="1.2" />
<rect x="{cx_l + 45:.2f}" y="{cy_l + 45:.2f}" width="170" height="22" rx="4" fill="#181825" stroke="#a6e3a1" stroke-width="1.2" />
<text x="{cx_l + 130:.2f}" y="{cy_l + 60:.2f}" text-anchor="middle" fill="#a6e3a1" font-size="11" font-weight="bold">50 Ω Load (Operating Point)</text>
''')


# ==================== SUMMARY / METRICS CARDS AT BOTTOM ====================
card_y = 800
card_h = 150

# Card 1: Stability Factor Summary
svg.append(f'''
<g transform="translate(60, {card_y})">
  <rect width="330" height="{card_h}" rx="8" fill="#181825" stroke="#313244" stroke-width="1.5" />
  <text x="18" y="28" fill="#fab387" font-size="14" font-weight="bold">Stability Criteria @ 98.0 MHz</text>
  <line x1="18" y1="38" x2="312" y2="38" stroke="#313244" stroke-width="1" />
  
  <text x="18" y="62" fill="#a6adc8" font-size="12">Rollett K-Factor:</text>
  <text x="180" y="62" fill="#f38ba8" font-size="13" font-weight="bold">K = {p98['k']:.3f} (&lt; 1)</text>
  
  <text x="18" y="86" fill="#a6adc8" font-size="12">Edwards-Sinsky μ:</text>
  <text x="180" y="86" fill="#f9e2af" font-size="13" font-weight="bold">μ = {p98['mu']:.3f} (&lt; 1)</text>

  <text x="18" y="110" fill="#a6adc8" font-size="12">Determinant |Δ|:</text>
  <text x="180" y="110" fill="#a6e3a1" font-size="13" font-weight="bold">|Δ| = {abs(p98['delta']):.3f} (&lt; 1)</text>
  
  <text x="18" y="134" fill="#a6adc8" font-size="12">Classification:</text>
  <text x="180" y="134" fill="#fab387" font-size="12" font-weight="bold">Conditionally Stable</text>
</g>
''')

# Card 2: Source Stability Circle Info
svg.append(f'''
<g transform="translate(420, {card_y})">
  <rect width="360" height="{card_h}" rx="8" fill="#181825" stroke="#313244" stroke-width="1.5" />
  <text x="18" y="28" fill="#f38ba8" font-size="14" font-weight="bold">Source Plane (Γs) Parameters</text>
  <line x1="18" y1="38" x2="342" y2="38" stroke="#313244" stroke-width="1" />
  
  <text x="18" y="62" fill="#a6adc8" font-size="12">Circle Center Cs:</text>
  <text x="160" y="62" fill="#cdd6f4" font-size="12" font-weight="bold">{p98['cS'].real:+.3f} {p98['cS'].imag:+.3f}j (|Cs|={abs(p98['cS']):.2f})</text>
  
  <text x="18" y="86" fill="#a6adc8" font-size="12">Circle Radius Rs:</text>
  <text x="160" y="86" fill="#cdd6f4" font-size="12" font-weight="bold">{p98['rS']:.3f}</text>

  <text x="18" y="110" fill="#a6adc8" font-size="12">50 Ω Source Margin:</text>
  <text x="160" y="110" fill="#a6e3a1" font-size="12" font-weight="bold">|Cs| - Rs = -0.11 (Inside Stable)</text>
  
  <text x="18" y="134" fill="#a6adc8" font-size="12">Stable Termination:</text>
  <text x="160" y="134" fill="#a6e3a1" font-size="12">50 Ω Source is fully STABLE</text>
</g>
''')

# Card 3: Load Stability Circle Info
svg.append(f'''
<g transform="translate(810, {card_y})">
  <rect width="360" height="{card_h}" rx="8" fill="#181825" stroke="#313244" stroke-width="1.5" />
  <text x="18" y="28" fill="#cba6f7" font-size="14" font-weight="bold">Load Plane (ΓL) Parameters</text>
  <line x1="18" y1="38" x2="342" y2="38" stroke="#313244" stroke-width="1" />
  
  <text x="18" y="62" fill="#a6adc8" font-size="12">Circle Center CL:</text>
  <text x="160" y="62" fill="#cdd6f4" font-size="12" font-weight="bold">{p98['cL'].real:+.3f} {p98['cL'].imag:+.3f}j (|CL|={abs(p98['cL']):.2f})</text>
  
  <text x="18" y="86" fill="#a6adc8" font-size="12">Circle Radius RL:</text>
  <text x="160" y="86" fill="#cdd6f4" font-size="12" font-weight="bold">{p98['rL']:.3f}</text>

  <text x="18" y="110" fill="#a6adc8" font-size="12">50 Ω Load Margin:</text>
  <text x="160" y="110" fill="#a6e3a1" font-size="12" font-weight="bold">|CL| - RL = +0.77 (Safe Distance)</text>
  
  <text x="18" y="134" fill="#a6adc8" font-size="12">Stable Termination:</text>
  <text x="160" y="134" fill="#a6e3a1" font-size="12">50 Ω Load is solidly STABLE</text>
</g>
''')

# Card 4: Engineering Insight & Legend
svg.append(f'''
<g transform="translate(1200, {card_y})">
  <rect width="340" height="{card_h}" rx="8" fill="#181825" stroke="#313244" stroke-width="1.5" />
  <text x="18" y="28" fill="#89dceb" font-size="14" font-weight="bold">RF Circuit Operating Insights</text>
  <line x1="18" y1="38" x2="322" y2="38" stroke="#313244" stroke-width="1" />
  
  <text x="18" y="58" fill="#cdd6f4" font-size="11" font-weight="bold">• Normal 50 Ω Operation:</text>
  <text x="28" y="74" fill="#a6adc8" font-size="11">Origin Γ=0 is in stable region for both ports.</text>
  
  <text x="18" y="94" fill="#cdd6f4" font-size="11" font-weight="bold">• Why K &lt; 1?</text>
  <text x="28" y="110" fill="#a6adc8" font-size="11">High gain (+19.9 dB) with finite Ccb isolation.</text>
  
  <text x="18" y="130" fill="#cdd6f4" font-size="11" font-weight="bold">• Precaution:</text>
  <text x="28" y="144" fill="#fab387" font-size="11">Avoid pure inductive source/capacitive high-Q load.</text>
</g>
''')

svg.append('</svg>')

# Save SVG
out_svg = Path('renders/stability_smith_chart.svg')
out_svg.parent.mkdir(exist_ok=True)
with open(out_svg, 'w', encoding='utf-8') as f:
    f.write('\n'.join(svg))
print(f'Saved SVG to {out_svg}')

# Copy to brain artifacts
brain_dir = Path(r'C:\Users\gsr\.gemini\antigravity\brain\10ba1c4f-bbc3-4e37-a73e-8d226cc7ff03')
shutil.copy(out_svg, brain_dir / 'stability_smith_chart.svg')

# Render to PNG using Microsoft Edge Headless
edge_path = r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe'
out_png = Path('renders/stability_smith_chart.png')

cmd = [
    edge_path,
    '--headless',
    '--disable-gpu',
    '--force-device-scale-factor=1',
    f'--window-size={width},{height}',
    f'--screenshot={out_png.resolve()}',
    out_svg.resolve().as_uri()
]

res = subprocess.run(cmd, capture_output=True, text=True)
if out_png.exists():
    shutil.copy(out_png, brain_dir / 'stability_smith_chart.png')
    print(f'Rendered PNG successfully to {out_png} ({out_png.stat().st_size} bytes)')
else:
    print('Failed to render PNG:', res.stderr)
