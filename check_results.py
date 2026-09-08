import numpy as np
import os

dat_file = "lna_fm_98mhz_full_board_cosim.dat"
with open(dat_file, "r") as f:
    lines = f.readlines()

data = {}
current_var = None
current_vals = []

for line in lines:
    line = line.strip()
    if line.startswith("<indep ") or line.startswith("<dep "):
        parts = line.split()
        current_var = parts[1]
        current_vals = []
    elif line.startswith("</indep>") or line.startswith("</dep>"):
        if current_var:
            data[current_var] = np.array(current_vals)
            current_var = None
    elif current_var is not None and line:
        # Check if line contains numbers
        tokens = line.split()
        for tok in tokens:
            try:
                if "j" in tok:
                    val = complex(tok)
                elif "/" in tok:
                    # e.g. 1.23/45.6 deg
                    r, deg = tok.split("/")
                    val = float(r) * np.exp(1j * np.radians(float(deg)))
                else:
                    val = float(tok)
                current_vals.append(val)
            except ValueError:
                pass

print("Variables in DAT file:")
print(list(data.keys()))

freqs = data.get("frequency", None)
if freqs is not None:
    idx_98 = np.argmin(np.abs(freqs - 98e6))
    f_val = freqs[idx_98]
    
    s11 = data["S[1,1]"][idx_98]
    s21 = data["S[2,1]"][idx_98]
    s12 = data["S[1,2]"][idx_98]
    s22 = data["S[2,2]"][idx_98]
    
    s11_db = 20 * np.log10(np.abs(s11))
    s21_db = 20 * np.log10(np.abs(s21))
    s12_db = 20 * np.log10(np.abs(s12))
    s22_db = 20 * np.log10(np.abs(s22))
    
    # Stability across band
    s11_all = data["S[1,1]"]
    s21_all = data["S[2,1]"]
    s12_all = data["S[1,2]"]
    s22_all = data["S[2,2]"]
    
    delta = s11_all * s22_all - s12_all * s21_all
    k_factor = (1.0 - np.abs(s11_all)**2 - np.abs(s22_all)**2 + np.abs(delta)**2) / (2.0 * np.abs(s12_all * s21_all))
    b1_factor = 1.0 + np.abs(s11_all)**2 - np.abs(s22_all)**2 - np.abs(delta)**2
    
    print("\n" + "=" * 70)
    print(f"  FULL-BOARD CO-SIMULATION RF PERFORMANCE at {f_val/1e6:.2f} MHz")
    print("=" * 70)
    print(f"  Gain S21            : {s21_db:+.2f} dB (mag = {np.abs(s21):.2f})")
    print(f"  Input Return Loss S11 : {s11_db:.2f} dB (VSWR = {(1+np.abs(s11))/(1-np.abs(s11)):.3f}:1)")
    print(f"  Output Return Loss S22: {s22_db:.2f} dB (VSWR = {(1+np.abs(s22))/(1-np.abs(s22)):.3f}:1)")
    print(f"  Reverse Isolation S12 : {s12_db:.2f} dB")
    print(f"  Stability Factor K    : {k_factor[idx_98]:.3f} (Unconditional: K > 1 = {k_factor[idx_98] > 1})")
    print(f"  Delta Magnitude       : {np.abs(delta[idx_98]):.4f} (Unconditional: |Delta| < 1 = {np.abs(delta[idx_98]) < 1})")
    print(f"  B1 Factor             : {b1_factor[idx_98]:.4f} (Unconditional: B1 > 0 = {b1_factor[idx_98] > 0})")
    print(f"  Min K across 10-500MHz: {np.min(k_factor):.3f}")
    print(f"  Max |Delta| across band: {np.max(np.abs(delta)):.4f}")
    print("=" * 70)
