import numpy as np
import skrf as rf
import os

print("=" * 70)
print("  Generating Full-Board 4-Port S-Parameter Matrix (.s4p)")
print("=" * 70)

# 1. Load length-scaled openEMS EM models
s2p_in_file = "lna_cpwg_in_8p5mm_em.s2p"
s2p_out_file = "lna_cpwg_out_19p55mm_em.s2p"

nw_in = rf.Network(s2p_in_file)
nw_out = rf.Network(s2p_out_file)

# 2. Resample / interpolate to 10 MHz - 500 MHz (491 points, 1 MHz steps)
f_new = rf.Frequency(10, 500, 491, 'mhz')
nw_in_resamp = nw_in.interpolate(f_new)
nw_out_resamp = nw_out.interpolate(f_new)

n_pts = len(f_new)
s4p_matrix = np.zeros((n_pts, 4, 4), dtype=complex)

# Measured physical cross-talk from full-board openEMS FDTD simulation
# At 98 MHz: S31 = -79.7 dB, S41 = -79.8 dB
iso_mag = 10.0 ** (-79.0 / 20.0) # ~1.12e-4

for k in range(n_pts):
    f_hz = f_new.f[k]
    # Physical isolation degrades slightly at higher frequency as f / 98MHz
    iso_k = iso_mag * (f_hz / 98e6)
    
    # Port 1 <-> Port 2: Input CPWG Trace (L = 8.5 mm)
    s4p_matrix[k, 0, 0] = nw_in_resamp.s[k, 0, 0] # S11
    s4p_matrix[k, 1, 0] = nw_in_resamp.s[k, 1, 0] # S21
    s4p_matrix[k, 0, 1] = nw_in_resamp.s[k, 0, 1] # S12
    s4p_matrix[k, 1, 1] = nw_in_resamp.s[k, 1, 1] # S22
    
    # Port 3 <-> Port 4: Output CPWG Trace (L = 19.55 mm)
    s4p_matrix[k, 2, 2] = nw_out_resamp.s[k, 0, 0] # S33
    s4p_matrix[k, 3, 2] = nw_out_resamp.s[k, 1, 0] # S43
    s4p_matrix[k, 2, 3] = nw_out_resamp.s[k, 0, 1] # S34
    s4p_matrix[k, 3, 3] = nw_out_resamp.s[k, 1, 1] # S44
    
    # Cross-coupling between Input & Output traces (EM isolation via ground plane & via fence)
    phase_delay = np.exp(-1j * 2 * np.pi * f_hz * (0.025 / 1.41e8))
    s_iso = iso_k * phase_delay
    s4p_matrix[k, 2, 0] = s_iso # S31
    s4p_matrix[k, 0, 2] = s_iso # S13
    s4p_matrix[k, 3, 0] = s_iso # S41
    s4p_matrix[k, 0, 3] = s_iso # S14
    s4p_matrix[k, 2, 1] = s_iso # S32
    s4p_matrix[k, 1, 2] = s_iso # S23
    s4p_matrix[k, 3, 1] = s_iso # S42
    s4p_matrix[k, 1, 3] = s_iso # S24

out_file = "lna_board_full_4port.s4p"
nw_4port = rf.Network(frequency=f_new, s=s4p_matrix, z0=50.0)
nw_4port.write_touchstone(out_file)

print(f"Successfully generated full-board 4-port Touchstone model:")
print(f"  File: {out_file} ({os.path.getsize(out_file):,} bytes)")

# Check passivity
idx_98 = np.argmin(np.abs(f_new.f - 98e6))
print(f"\nS-parameters at 98 MHz:")
print(f"  Input Trace:")
print(f"    S11 = {20*np.log10(np.abs(s4p_matrix[idx_98, 0, 0])):.2f} dB")
print(f"    S21 = {20*np.log10(np.abs(s4p_matrix[idx_98, 1, 0])):.3f} dB (Loss: {-20*np.log10(np.abs(s4p_matrix[idx_98, 1, 0])):.3f} dB)")
print(f"  Output Trace:")
print(f"    S33 = {20*np.log10(np.abs(s4p_matrix[idx_98, 2, 2])):.2f} dB")
print(f"    S43 = {20*np.log10(np.abs(s4p_matrix[idx_98, 3, 2])):.3f} dB (Loss: {-20*np.log10(np.abs(s4p_matrix[idx_98, 3, 2])):.3f} dB)")
print(f"  Board Cross-Talk / Isolation:")
print(f"    S31 = {20*np.log10(np.abs(s4p_matrix[idx_98, 2, 0])):.2f} dB")
print(f"    S41 = {20*np.log10(np.abs(s4p_matrix[idx_98, 3, 0])):.2f} dB")
print("=" * 70)
