import numpy as np
from parse_qucs import parse_qucs_dat

freqs, data = parse_qucs_dat("lna_fm_98mhz_full_board_cosim.dat")
freqs = np.array(freqs)

s11 = np.array(data["S[1,1]"])
s21 = np.array(data["S[2,1]"])
s12 = np.array(data["S[1,2]"])
s22 = np.array(data["S[2,2]"])

# Calculate Rollett Stability Factor K and Delta
delta = s11 * s22 - s12 * s21
k_factor = (1.0 - np.abs(s11)**2 - np.abs(s22)**2 + np.abs(delta)**2) / (2.0 * np.abs(s12 * s21))
b1_factor = 1.0 + np.abs(s11)**2 - np.abs(s22)**2 - np.abs(delta)**2
mu1 = (1.0 - np.abs(s11)**2) / (np.abs(s22 - np.conj(s11) * delta) + np.abs(s12 * s21))

idx_98 = np.argmin(np.abs(freqs - 98e6))

print("=" * 70)
print(f"  FULL-BOARD CO-SIMULATION STABILITY & RF PERFORMANCE (10 - 500 MHz)")
print("=" * 70)
print(f"  Operating Frequency : {freqs[idx_98]/1e6:.1f} MHz")
print(f"  Gain S21            : {20*np.log10(np.abs(s21[idx_98])):+.2f} dB")
print(f"  Input Return Loss   : {20*np.log10(np.abs(s11[idx_98])):.2f} dB (VSWR = {(1+np.abs(s11[idx_98]))/(1-np.abs(s11[idx_98])):.3f}:1)")
print(f"  Reverse Isolation   : {20*np.log10(np.abs(s12[idx_98])):.2f} dB")
print(f"  Rollett Factor K    : {k_factor[idx_98]:.3f} (Unconditional: K > 1 = {k_factor[idx_98] > 1})")
print(f"  Delta |Delta|       : {np.abs(delta[idx_98]):.4f} (Unconditional: |Delta| < 1 = {np.abs(delta[idx_98]) < 1})")
print(f"  Mu1 Factor          : {mu1[idx_98]:.3f} (Unconditional: Mu1 > 1 = {mu1[idx_98] > 1})")
print(f"  Min K across band   : {np.min(k_factor):.3f}")
print(f"  Max |Delta| across  : {np.max(np.abs(delta)):.4f}")
print("=" * 70)

# Bandwidth check (-3 dB from peak)
peak_idx = np.argmax(np.abs(s21))
peak_gain_db = 20 * np.log10(np.abs(s21[peak_idx]))
peak_freq = freqs[peak_idx] / 1e6

cutoff_mask = 20 * np.log10(np.abs(s21)) >= (peak_gain_db - 3.0)
bw_freqs = freqs[cutoff_mask] / 1e6
bw = bw_freqs[-1] - bw_freqs[0]

print(f"  Peak Gain           : {peak_gain_db:+.2f} dB at {peak_freq:.1f} MHz")
print(f"  -3dB Bandwidth      : {bw:.1f} MHz ({bw_freqs[0]:.1f} to {bw_freqs[-1]:.1f} MHz)")
print("=" * 70)
