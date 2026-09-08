import matplotlib.pyplot as plt
import numpy as np
import os
from parse_qucs import parse_qucs_dat
import skrf as rf

print("Generating full-board co-simulation comparison plots...")

# 1. Load data
freqs_fb, data_fb = parse_qucs_dat("lna_fm_98mhz_full_board_cosim.dat")
freqs_fb = np.array(freqs_fb) / 1e6 # MHz

s11_fb = np.array(data_fb["S[1,1]"])
s21_fb = np.array(data_fb["S[2,1]"])
s12_fb = np.array(data_fb["S[1,2]"])
s22_fb = np.array(data_fb["S[2,2]"])

# Load Option A data
freqs_oa, data_oa = parse_qucs_dat("lna_fm_98mhz_cosim.dat")
freqs_oa = np.array(freqs_oa) / 1e6 # MHz
s11_oa = np.array(data_oa["S[1,1]"])
s21_oa = np.array(data_oa["S[2,1]"])

# Load Baseline data
freqs_base, data_base = parse_qucs_dat("lna_fm_98mhz_qucs.dat")
freqs_base = np.array(freqs_base) / 1e6 # MHz
s11_base = np.array(data_base["S[1,1]"])
s21_base = np.array(data_base["S[2,1]"])

# Load 4-port S-parameters directly for cross-talk
nw_4p = rf.Network("lna_board_full_4port.s4p")
f_4p = nw_4p.f / 1e6
s31_iso = 20 * np.log10(np.abs(nw_4p.s[:, 2, 0]))
s41_iso = 20 * np.log10(np.abs(nw_4p.s[:, 3, 0]))

# Stability for full board
delta_fb = s11_fb * s22_fb - s12_fb * s21_fb
k_fb = (1.0 - np.abs(s11_fb)**2 - np.abs(s22_fb)**2 + np.abs(delta_fb)**2) / (2.0 * np.abs(s12_fb * s21_fb))

# Create 2x2 multi-panel figure
plt.style.use('seaborn-v0_8-whitegrid' if 'seaborn-v0_8-whitegrid' in plt.style.available else 'default')
fig, axs = plt.subplots(2, 2, figsize=(15, 11), dpi=300)

# Panel 1: Gain S21 (dB)
ax1 = axs[0, 0]
ax1.plot(freqs_fb, 20*np.log10(np.abs(s21_fb)), 'r-', lw=2.5, label="Full-Board 4-Port EM Co-Sim (.s4p)")
ax1.plot(freqs_oa, 20*np.log10(np.abs(s21_oa)), 'g--', lw=2.0, label="Option A Hierarchical EM Co-Sim (.s2p)")
ax1.plot(freqs_base, 20*np.log10(np.abs(s21_base)), 'b:', lw=1.8, label="Ideal Schematic Baseline")

idx_98 = np.argmin(np.abs(freqs_fb - 98.0))
g_98 = 20*np.log10(np.abs(s21_fb[idx_98]))
ax1.plot(98.0, g_98, 'ro', markersize=8)
ax1.annotate(f"98 MHz: {g_98:+.2f} dB", xy=(98.0, g_98), xytext=(120, g_98 + 1.5),
             arrowprops=dict(facecolor='red', shrink=0.08, width=1.5, headwidth=6),
             fontsize=10, fontweight='bold', bbox=dict(boxstyle='round,pad=0.3', facecolor='yellow', alpha=0.6))

ax1.set_title("Forward Gain |S21| vs Frequency (10 - 500 MHz)", fontsize=12, fontweight='bold')
ax1.set_xlabel("Frequency (MHz)", fontsize=10)
ax1.set_ylabel("Gain (dB)", fontsize=10)
ax1.set_xlim(10, 500)
ax1.set_ylim(-35, 25)
ax1.axvspan(88, 108, color='orange', alpha=0.15, label="FM Broadcast Band (88-108 MHz)")
ax1.legend(loc="lower right", fontsize=9)
ax1.grid(True, linestyle='--', alpha=0.6)

# Panel 2: Return Loss S11 (dB) & VSWR
ax2 = axs[0, 1]
ax2.plot(freqs_fb, 20*np.log10(np.abs(s11_fb)), 'r-', lw=2.5, label="Full-Board EM |S11|")
ax2.plot(freqs_oa, 20*np.log10(np.abs(s11_oa)), 'g--', lw=2.0, label="Option A |S11|")
ax2.plot(freqs_base, 20*np.log10(np.abs(s11_base)), 'b:', lw=1.8, label="Ideal Baseline |S11|")

rl_98 = 20*np.log10(np.abs(s11_fb[idx_98]))
vswr_98 = (1 + np.abs(s11_fb[idx_98])) / (1 - np.abs(s11_fb[idx_98]))
ax2.plot(98.0, rl_98, 'ro', markersize=8)
ax2.annotate(f"98 MHz: {rl_98:.1f} dB\n(VSWR {vswr_98:.3f}:1)", xy=(98.0, rl_98), xytext=(120, rl_98 + 8),
             arrowprops=dict(facecolor='red', shrink=0.08, width=1.5, headwidth=6),
             fontsize=10, fontweight='bold', bbox=dict(boxstyle='round,pad=0.3', facecolor='cyan', alpha=0.4))

ax2.axhline(-10.0, color='gray', linestyle=':', label="VSWR 2.0:1 (-9.54 dB)")
ax2.axhline(-20.0, color='darkgray', linestyle='--', label="VSWR 1.22:1 (-20 dB)")
ax2.set_title("Input Return Loss |S11| vs Frequency", fontsize=12, fontweight='bold')
ax2.set_xlabel("Frequency (MHz)", fontsize=10)
ax2.set_ylabel("Return Loss (dB)", fontsize=10)
ax2.set_xlim(10, 500)
ax2.set_ylim(-45, 0)
ax2.legend(loc="lower left", fontsize=9)
ax2.grid(True, linestyle='--', alpha=0.6)

# Panel 3: Reverse Isolation S12 & Substrate Cross-Talk S41 / S31
ax3 = axs[1, 0]
ax3.plot(freqs_fb, 20*np.log10(np.abs(s12_fb)), 'm-', lw=2.2, label="LNA Reverse Isolation |S12| (Circuit)")
ax3.plot(f_4p, s31_iso, 'c--', lw=2.0, label="PCB Substrate Near-End Cross-Talk |S31| (EM)")
ax3.plot(f_4p, s41_iso, 'b-.', lw=2.0, label="PCB Substrate Far-End Cross-Talk |S41| (EM)")

ax3.set_title("Reverse Isolation & Substrate Cross-Talk Isolation", fontsize=12, fontweight='bold')
ax3.set_xlabel("Frequency (MHz)", fontsize=10)
ax3.set_ylabel("Isolation (dB)", fontsize=10)
ax3.set_xlim(10, 500)
ax3.set_ylim(-100, -10)
ax3.legend(loc="upper right", fontsize=9)
ax3.grid(True, linestyle='--', alpha=0.6)

# Panel 4: Rollett Stability Factor K & |Delta|
ax4 = axs[1, 1]
ax4.plot(freqs_fb, k_fb, 'darkorange', lw=2.2, label="Rollett Factor K")
ax4.plot(freqs_fb, np.abs(delta_fb), 'purple', lw=2.0, label="|Delta|")
ax4.axhline(1.0, color='red', linestyle='--', label="K = 1.0 (Stability Threshold)")

ax4.set_title("Full-Board Stability Metrics (K & |Delta|)", fontsize=12, fontweight='bold')
ax4.set_xlabel("Frequency (MHz)", fontsize=10)
ax4.set_ylabel("Factor Value", fontsize=10)
ax4.set_xlim(10, 500)
ax4.set_ylim(0, 4.0)
ax4.legend(loc="upper right", fontsize=9)
ax4.grid(True, linestyle='--', alpha=0.6)

plt.suptitle("98 MHz FM Low-Noise Amplifier: Full-Board 3D EM Co-Simulation (openEMS + QUCS)\nOption 1: 4-Port Active-Interface Touchstone S4P Model",
             fontsize=14, fontweight='bold', y=0.98)

plt.tight_layout(rect=[0, 0, 1, 0.95])
out_img = os.path.join("renders", "lna_full_board_cosim_results.png")
plt.savefig(out_img, bbox_inches='tight')
print(f"Saved comparison plot to: {out_img}")
