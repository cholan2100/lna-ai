import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import numpy as np
import os
from parse_qucs import parse_qucs_dat
import skrf as rf

script_dir = os.path.dirname(os.path.abspath(__file__))
repo_dir = os.path.dirname(script_dir)

# 1. Load QUCS Final Co-Simulation Data
dat_file = os.path.join(script_dir, 'lna_fm_98mhz_full_board_cosim.dat')
freqs_raw, data = parse_qucs_dat(dat_file)
freqs = np.array(freqs_raw) / 1e6 # MHz
s11 = np.array(data['S[1,1]'])
s21 = np.array(data['S[2,1]'])
s12 = np.array(data['S[1,2]'])
s22 = np.array(data['S[2,2]'])

# 98 MHz index
idx_98 = np.argmin(np.abs(freqs - 98.0))
f98 = freqs[idx_98]
s11_98 = s11[idx_98]
s21_98 = s21[idx_98]
s12_98 = s12[idx_98]
s22_98 = s22[idx_98]

z0 = 50.0
zin_98 = z0 * (1 + s11_98) / (1 - s11_98)
zout_98 = z0 * (1 + s22_98) / (1 - s22_98)
vswr_in_98 = (1 + np.abs(s11_98)) / (1 - np.abs(s11_98))

# Create Network object for skrf Smith chart plotting
s_matrix = np.zeros((len(freqs), 2, 2), dtype=complex)
s_matrix[:, 0, 0] = s11
s_matrix[:, 1, 0] = s21
s_matrix[:, 0, 1] = s12
s_matrix[:, 1, 1] = s22
nw = rf.Network(frequency=rf.Frequency.from_f(freqs * 1e6, unit='hz'), s=s_matrix, z0=50)

# Setup high-resolution figure with GridSpec
fig = plt.figure(figsize=(19, 10), dpi=200)
gs = gridspec.GridSpec(2, 2, width_ratios=[1.15, 1.0], height_ratios=[1, 1], wspace=0.22, hspace=0.28)

# -------------------------------------------------------------
# Panel 1: Cartesian Gain (S21) & Input Return Loss (S11)
# -------------------------------------------------------------
ax1 = fig.add_subplot(gs[0, 0])
ax1.plot(freqs, 20*np.log10(np.abs(s21)), color='#dc2626', lw=2.5, label=f'Forward Gain |S21| (Peak: {20*np.log10(np.abs(s21_98)):+.2f} dB)')
ax1.plot(freqs, 20*np.log10(np.abs(s11)), color='#2563eb', lw=2.2, label=f'Input Return Loss |S11| ({20*np.log10(np.abs(s11_98)):.2f} dB)')

# 98 MHz Markers
ax1.plot(98.0, 20*np.log10(np.abs(s21_98)), 'ro', markersize=8, markeredgecolor='black', markeredgewidth=1.5)
ax1.annotate(f'98 MHz: {20*np.log10(np.abs(s21_98)):+.2f} dB',
             xy=(98.0, 20*np.log10(np.abs(s21_98))), xytext=(120, 20*np.log10(np.abs(s21_98)) + 1.8),
             arrowprops=dict(facecolor='#dc2626', shrink=0.08, width=1.5, headwidth=6),
             fontsize=10.5, fontweight='bold', bbox=dict(boxstyle='round,pad=0.35', facecolor='#fee2e2', edgecolor='#dc2626', lw=1.5))

ax1.plot(98.0, 20*np.log10(np.abs(s11_98)), 'bo', markersize=8, markeredgecolor='black', markeredgewidth=1.5)
ax1.annotate(f'98 MHz: {20*np.log10(np.abs(s11_98)):.2f} dB\nVSWR {vswr_in_98:.2f}:1',
             xy=(98.0, 20*np.log10(np.abs(s11_98))), xytext=(125, 20*np.log10(np.abs(s11_98)) - 4.5),
             arrowprops=dict(facecolor='#2563eb', shrink=0.08, width=1.5, headwidth=6),
             fontsize=10, fontweight='bold', bbox=dict(boxstyle='round,pad=0.35', facecolor='#dbeafe', edgecolor='#2563eb', lw=1.5))

# Shaded FM broadcast band
ax1.axvspan(88, 108, color='#fef08a', alpha=0.35, label='FM Broadcast Band (88 - 108 MHz)')
ax1.axhline(-10, color='gray', linestyle=':', lw=1.2, label='-10 dB Return Loss (VSWR 2:1)')
ax1.set_title('(A) Forward Gain |S21| & Input Match |S11| vs Frequency', fontsize=12.5, fontweight='bold', pad=10)
ax1.set_ylabel('Magnitude (dB)', fontsize=11, fontweight='bold')
ax1.set_xlim(10, 500)
ax1.set_ylim(-35, 25)
ax1.grid(True, linestyle='--', alpha=0.55)
ax1.legend(loc='upper right', fontsize=9.5, framealpha=0.92)

# -------------------------------------------------------------
# Panel 2: Cartesian Reverse Isolation (S12) & Output Match (S22)
# -------------------------------------------------------------
ax2 = fig.add_subplot(gs[1, 0])
ax2.plot(freqs, 20*np.log10(np.abs(s12)), color='#059669', lw=2.2, label=f'Reverse Isolation |S12| ({20*np.log10(np.abs(s12_98)):.2f} dB)')
ax2.plot(freqs, 20*np.log10(np.abs(s22)), color='#9333ea', lw=2.2, label=f'Output Reflection |S22| ({20*np.log10(np.abs(s22_98)):.2f} dB)')

# 98 MHz Markers
ax2.plot(98.0, 20*np.log10(np.abs(s12_98)), 'go', markersize=8, markeredgecolor='black', markeredgewidth=1.5)
ax2.annotate(f'98 MHz: {20*np.log10(np.abs(s12_98)):.2f} dB\n(High Isolation)',
             xy=(98.0, 20*np.log10(np.abs(s12_98))), xytext=(120, 20*np.log10(np.abs(s12_98)) + 5),
             arrowprops=dict(facecolor='#059669', shrink=0.08, width=1.5, headwidth=6),
             fontsize=10, fontweight='bold', bbox=dict(boxstyle='round,pad=0.35', facecolor='#d1fae5', edgecolor='#059669', lw=1.5))

ax2.plot(98.0, 20*np.log10(np.abs(s22_98)), 'mo', markersize=8, markeredgecolor='black', markeredgewidth=1.5)
ax2.annotate(f'98 MHz: {20*np.log10(np.abs(s22_98)):.2f} dB\n(Open-Collector Match)',
             xy=(98.0, 20*np.log10(np.abs(s22_98))), xytext=(120, 20*np.log10(np.abs(s22_98)) - 10),
             arrowprops=dict(facecolor='#9333ea', shrink=0.08, width=1.5, headwidth=6),
             fontsize=10, fontweight='bold', bbox=dict(boxstyle='round,pad=0.35', facecolor='#f3e8ff', edgecolor='#9333ea', lw=1.5))

ax2.axvspan(88, 108, color='#fef08a', alpha=0.35)
ax2.set_title('(B) Reverse Isolation |S12| & Output Reflection |S22| vs Frequency', fontsize=12.5, fontweight='bold', pad=10)
ax2.set_xlabel('Frequency (MHz)', fontsize=11, fontweight='bold')
ax2.set_ylabel('Magnitude (dB)', fontsize=11, fontweight='bold')
ax2.set_xlim(10, 500)
ax2.set_ylim(-65, 5)
ax2.grid(True, linestyle='--', alpha=0.55)
ax2.legend(loc='lower right', fontsize=9.5, framealpha=0.92)

# -------------------------------------------------------------
# Panel 3: RF Smith Chart (S11 & S22 loci)
# -------------------------------------------------------------
ax3 = fig.add_subplot(gs[:, 1])

# Plot Smith chart via skrf
rf.plotting.plot_smith(s=s11, ax=ax3, color='#2563eb', lw=2.8, label='S11 Locus (10 - 500 MHz)',
                       chart_type='z', draw_labels=True)
rf.plotting.plot_smith(s=s22, ax=ax3, color='#9333ea', lw=2.2, label='S22 Locus (10 - 500 MHz)',
                       chart_type='z', draw_labels=False)

# Mark 98 MHz on Smith Chart
# In complex plane of reflection coefficient: x = real(gamma), y = imag(gamma)
gamma_in_x = s11_98.real
gamma_in_y = s11_98.imag
gamma_out_x = s22_98.real
gamma_out_y = s22_98.imag

ax3.plot(gamma_in_x, gamma_in_y, 'o', color='#2563eb', markersize=10, markeredgecolor='black', markeredgewidth=2, zorder=10)
ax3.plot(gamma_out_x, gamma_out_y, 'o', color='#9333ea', markersize=10, markeredgecolor='black', markeredgewidth=2, zorder=10)

# Center 50 Ohm reference point
ax3.plot(0, 0, 'k+', markersize=12, markeredgewidth=2, label='50 Ω Center (Γ = 0)', zorder=9)

# Callout annotation for S11 (Z_in)
ax3.annotate(f'S11 (98 MHz):\nΓ = {s11_98.real:+.3f} + j({s11_98.imag:+.3f})\nZ_in = {zin_98.real:.1f} + j({zin_98.imag:.1f}) Ω\nVSWR = {vswr_in_98:.2f}:1\n|S11| = {20*np.log10(np.abs(s11_98)):.2f} dB',
             xy=(gamma_in_x, gamma_in_y), xytext=(gamma_in_x + 0.35, gamma_in_y - 0.40),
             arrowprops=dict(arrowstyle='->', lw=2, color='#2563eb', connectionstyle='arc3,rad=-0.2'),
             fontsize=10.5, fontweight='bold',
             bbox=dict(boxstyle='round,pad=0.5', facecolor='#eff6ff', edgecolor='#2563eb', lw=2, alpha=0.95), zorder=15)

# Callout annotation for S22 (Z_out)
ax3.annotate(f'S22 (98 MHz):\nΓ = {s22_98.real:+.3f} + j({s22_98.imag:+.3f})\nZ_out = {zout_98.real:.1f} + j({zout_98.imag:.1f}) Ω\n|S22| = {20*np.log10(np.abs(s22_98)):.2f} dB',
             xy=(gamma_out_x, gamma_out_y), xytext=(gamma_out_x - 0.05, gamma_out_y + 0.30),
             arrowprops=dict(arrowstyle='->', lw=2, color='#9333ea', connectionstyle='arc3,rad=0.15'),
             fontsize=10, fontweight='bold',
             bbox=dict(boxstyle='round,pad=0.5', facecolor='#faf5ff', edgecolor='#9333ea', lw=2, alpha=0.95), zorder=15)

ax3.set_title('(C) Impedance Smith Chart: S11 (Input) & S22 (Output)', fontsize=13, fontweight='bold', pad=12)
ax3.legend(loc='lower left', fontsize=10, framealpha=0.95)

# Master Title Banner
plt.suptitle('98 MHz FM Low-Noise Amplifier: Final QUCS Co-Simulation Results\nMultiport Simulation Using 4-Port Full-Board openEMS Touchstone Model (lna_board_full_4port.s4p)',
             fontsize=15, fontweight='bold', y=0.985)

out_fig = os.path.join(repo_dir, 'renders', 'final_qucs_cosim_s_params_and_smith.png')
plt.savefig(out_fig, bbox_inches='tight', dpi=220)
plt.close()
print(f'Successfully created {out_fig}')
