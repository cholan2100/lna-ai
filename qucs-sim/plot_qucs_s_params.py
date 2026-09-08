import cmath
from parse_qucs import parse_qucs_dat

freqs, data = parse_qucs_dat('lna_fm_98mhz_qucs_cpwg.dat')

f_mhz = [f / 1e6 for f in freqs]
s11_db = [20 * cmath.log10(abs(v)).real for v in data['S[1,1]']]
s21_db = [20 * cmath.log10(abs(v)).real for v in data['S[2,1]']]
s12_db = [20 * cmath.log10(abs(v)).real for v in data['S[1,2]']]
s22_db = [20 * cmath.log10(abs(v)).real for v in data['S[2,2]']]

width = 800
height = 500
pad_l = 70
pad_r = 40
pad_t = 60
pad_b = 60

plot_w = width - pad_l - pad_r
plot_h = height - pad_t - pad_b

y_min = -45.0
y_max = +25.0
x_min = 70.0
x_max = 130.0

def to_x(f):
    return pad_l + (f - x_min) / (x_max - x_min) * plot_w

def to_y(db):
    clamped = max(y_min, min(y_max, db))
    return pad_t + (y_max - clamped) / (y_max - y_min) * plot_h

svg = []
svg.append(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="100%" height="100%" style="background:#1e1e2e; font-family: -apple-system, BlinkMacSystemFont, Segoe UI, Roboto, Helvetica, Arial, sans-serif;">')

svg.append(f'<text x="{width//2}" y="30" text-anchor="middle" fill="#cdd6f4" font-size="18" font-weight="bold">Common-Base 98 MHz FM LNA ? QUCS S-Parameters with CPWG Lines</text>')
svg.append(f'<text x="{width//2}" y="48" text-anchor="middle" fill="#a6adc8" font-size="12">Coplanar Waveguide Models: 1.6mm FR-4, W=1.5mm, S=0.35mm (Z0 = 50 Ohm CPWG)</text>')

fm_x1 = to_x(88.0)
fm_x2 = to_x(108.0)
svg.append(f'<rect x="{fm_x1}" y="{pad_t}" width="{fm_x2 - fm_x1}" height="{plot_h}" fill="#a6e3a1" fill-opacity="0.08" stroke="#a6e3a1" stroke-dasharray="4,4" stroke-width="1"/>')
svg.append(f'<text x="{(fm_x1 + fm_x2)/2}" y="{pad_t + 20}" text-anchor="middle" fill="#a6e3a1" font-size="12" font-weight="600">FM Broadcast Band (88?108 MHz)</text>')

for f in range(70, 131, 10):
    x = to_x(f)
    svg.append(f'<line x1="{x}" y1="{pad_t}" x2="{x}" y2="{pad_t + plot_h}" stroke="#313244" stroke-width="1"/>')
    svg.append(f'<text x="{x}" y="{pad_t + plot_h + 20}" text-anchor="middle" fill="#a6adc8" font-size="12">{f} MHz</text>')

for db in range(-40, 26, 10):
    y = to_y(db)
    stroke_color = "#45475a" if db == 0 else "#313244"
    stroke_w = 1.5 if db == 0 else 1.0
    svg.append(f'<line x1="{pad_l}" y1="{y}" x2="{pad_l + plot_w}" y2="{y}" stroke="{stroke_color}" stroke-width="{stroke_w}"/>')
    svg.append(f'<text x="{pad_l - 10}" y="{y + 4}" text-anchor="end" fill="#a6adc8" font-size="12">{db:+d} dB</text>')

svg.append(f'<rect x="{pad_l}" y="{pad_t}" width="{plot_w}" height="{plot_h}" fill="none" stroke="#45475a" stroke-width="1.5"/>')

fc_x = to_x(98.0)
svg.append(f'<line x1="{fc_x}" y1="{pad_t}" x2="{fc_x}" y2="{pad_t + plot_h}" stroke="#fab387" stroke-dasharray="3,3" stroke-width="1.5"/>')
svg.append(f'<text x="{fc_x}" y="{pad_t + plot_h - 10}" text-anchor="middle" fill="#fab387" font-size="11">98.0 MHz</text>')

def make_path(y_vals):
    pts = []
    for f, v in zip(f_mhz, y_vals):
        pts.append(f'{to_x(f):.2f},{to_y(v):.2f}')
    return 'M ' + ' L '.join(pts)

svg.append(f'<path d="{make_path(s12_db)}" fill="none" stroke="#89b4fa" stroke-width="2" stroke-dasharray="6,3"/>')
svg.append(f'<path d="{make_path(s22_db)}" fill="none" stroke="#f38ba8" stroke-width="2" stroke-dasharray="4,2"/>')
svg.append(f'<path d="{make_path(s11_db)}" fill="none" stroke="#f9e2af" stroke-width="2.5"/>')
svg.append(f'<path d="{make_path(s21_db)}" fill="none" stroke="#a6e3a1" stroke-width="3"/>')

idx_98 = f_mhz.index(98.0)
m_x = to_x(98.0)
m_y = to_y(s21_db[idx_98])
svg.append(f'<circle cx="{m_x:.2f}" cy="{m_y:.2f}" r="5" fill="#a6e3a1" stroke="#1e1e2e" stroke-width="2"/>')
svg.append(f'<rect x="{m_x + 8:.2f}" y="{m_y - 24:.2f}" width="140" height="22" rx="4" fill="#313244" stroke="#a6e3a1" stroke-width="1"/>')
svg.append(f'<text x="{m_x + 14:.2f}" y="{m_y - 9:.2f}" fill="#a6e3a1" font-size="12" font-weight="bold">S21 = +{s21_db[idx_98]:.2f} dB</text>')

# Also add S11 marker at 98 MHz
m11_y = to_y(s11_db[idx_98])
svg.append(f'<circle cx="{m_x:.2f}" cy="{m11_y:.2f}" r="5" fill="#f9e2af" stroke="#1e1e2e" stroke-width="2"/>')
svg.append(f'<rect x="{m_x + 8:.2f}" y="{m11_y - 10:.2f}" width="140" height="22" rx="4" fill="#313244" stroke="#f9e2af" stroke-width="1"/>')
svg.append(f'<text x="{m_x + 14:.2f}" y="{m11_y + 5:.2f}" fill="#f9e2af" font-size="12" font-weight="bold">S11 = {s11_db[idx_98]:.2f} dB</text>')

leg_y = pad_t + 15
leg_x = pad_l + 15
svg.append(f'<g transform="translate({leg_x}, {leg_y})">')
svg.append(f'<rect width="185" height="95" rx="6" fill="#181825" fill-opacity="0.9" stroke="#313244" stroke-width="1"/>')

svg.append(f'<line x1="15" y1="20" x2="45" y2="20" stroke="#a6e3a1" stroke-width="3"/>')
svg.append(f'<text x="55" y="24" fill="#cdd6f4" font-size="12" font-weight="bold">S21 Gain ({s21_db[idx_98]:+.1f} dB)</text>')
svg.append(f'<line x1="15" y1="40" x2="45" y2="40" stroke="#f9e2af" stroke-width="2.5"/>')
svg.append(f'<text x="55" y="44" fill="#cdd6f4" font-size="12" font-weight="bold">S11 Match ({s11_db[idx_98]:+.1f} dB)</text>')
svg.append(f'<line x1="15" y1="60" x2="45" y2="60" stroke="#f38ba8" stroke-width="2" stroke-dasharray="4,2"/>')
svg.append(f'<text x="55" y="64" fill="#cdd6f4" font-size="12">S22 Output ({s22_db[idx_98]:+.1f} dB)</text>')
svg.append(f'<line x1="15" y1="80" x2="45" y2="80" stroke="#89b4fa" stroke-width="2" stroke-dasharray="6,3"/>')
svg.append(f'<text x="55" y="84" fill="#cdd6f4" font-size="12">S12 Isol ({s12_db[idx_98]:+.1f} dB)</text>')
svg.append(f'</g>')

svg.append('</svg>')

from pathlib import Path
import shutil
Path('renders').mkdir(exist_ok=True)
out_path = Path('renders/qucs_s_parameters_cpwg.svg')
with open(out_path, 'w') as f:
    f.write('\n'.join(svg))

shutil.copy(out_path, r'C:\Users\gsr\.gemini\antigravity\brain\10ba1c4f-bbc3-4e37-a73e-8d226cc7ff03\qucs_s_parameters_cpwg.svg')
print('Plot saved successfully in renders/!')
