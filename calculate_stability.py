import cmath
import numpy as np
from parse_qucs import parse_qucs_dat

freqs, data = parse_qucs_dat('lna_fm_98mhz_qucs_cpwg.dat')
print(f"Frequency range: {freqs[0]/1e6:.1f} to {freqs[-1]/1e6:.1f} MHz, {len(freqs)} points\n")

header = f"{'Freq(MHz)':<10} {'|S11|':<8} {'|S21|':<8} {'|S12|':<8} {'|S22|':<8} {'K':<8} {'|Delta|':<8} {'mu':<8} {'mu_prime':<8}"
print(header)
print("-" * len(header))

for i, f in enumerate(freqs):
    s11 = data['S[1,1]'][i]
    s21 = data['S[2,1]'][i]
    s12 = data['S[1,2]'][i]
    s22 = data['S[2,2]'][i]
    
    delta = s11 * s22 - s12 * s21
    k = (1.0 - abs(s11)**2 - abs(s22)**2 + abs(delta)**2) / (2.0 * abs(s12 * s21))
    
    # Edwards-Sinsky mu factors
    mu = (1.0 - abs(s11)**2) / (abs(s22 - delta * s11.conjugate()) + abs(s12 * s21))
    mu_prime = (1.0 - abs(s22)**2) / (abs(s11 - delta * s22.conjugate()) + abs(s12 * s21))
    
    # Load stability circle
    denom_L = abs(s22)**2 - abs(delta)**2
    cL = (s22 - delta * s11.conjugate()).conjugate() / denom_L
    rL = abs(s12 * s21 / denom_L)
    
    # Source stability circle
    denom_S = abs(s11)**2 - abs(delta)**2
    cS = (s11 - delta * s22.conjugate()).conjugate() / denom_S
    rS = abs(s12 * s21 / denom_S)
    
    if i % 10 == 0 or abs(f - 9.8e7) < 1e5:
        print(f"{f/1e6:<10.1f} {abs(s11):<8.4f} {abs(s21):<8.3f} {abs(s12):<8.4f} {abs(s22):<8.4f} {k:<8.3f} {abs(delta):<8.4f} {mu:<8.3f} {mu_prime:<8.3f}")

idx_98 = 0
for i, f in enumerate(freqs):
    if abs(f - 9.8e7) < 1e5:
        idx_98 = i
        break

f0 = freqs[idx_98]
s11 = data['S[1,1]'][idx_98]
s21 = data['S[2,1]'][idx_98]
s12 = data['S[1,2]'][idx_98]
s22 = data['S[2,2]'][idx_98]
delta = s11 * s22 - s12 * s21
k = (1.0 - abs(s11)**2 - abs(s22)**2 + abs(delta)**2) / (2.0 * abs(s12 * s21))
denom_L = abs(s22)**2 - abs(delta)**2
cL = (s22 - delta * s11.conjugate()).conjugate() / denom_L
rL = abs(s12 * s21 / denom_L)
denom_S = abs(s11)**2 - abs(delta)**2
cS = (s11 - delta * s22.conjugate()).conjugate() / denom_S
rS = abs(s12 * s21 / denom_S)
mu = (1.0 - abs(s11)**2) / (abs(s22 - delta * s11.conjugate()) + abs(s12 * s21))
mu_prime = (1.0 - abs(s22)**2) / (abs(s11 - delta * s22.conjugate()) + abs(s12 * s21))

print("\n--- Detailed stability at 98 MHz ---")
print(f"S11: {s11.real:+.4f} {s11.imag:+.4f}j  (|S11| = {abs(s11):.4f}, {20*cmath.log10(abs(s11)).real:.2f} dB)")
print(f"S21: {s21.real:+.4f} {s21.imag:+.4f}j  (|S21| = {abs(s21):.4f}, {20*cmath.log10(abs(s21)).real:.2f} dB)")
print(f"S12: {s12.real:+.4f} {s12.imag:+.4f}j  (|S12| = {abs(s12):.4f}, {20*cmath.log10(abs(s12)).real:.2f} dB)")
print(f"S22: {s22.real:+.4f} {s22.imag:+.4f}j  (|S22| = {abs(s22):.4f}, {20*cmath.log10(abs(s22)).real:.2f} dB)")
print(f"Delta: {delta.real:+.4f} {delta.imag:+.4f}j  (|Delta| = {abs(delta):.4f})")
print(f"K-factor: {k:.4f}")
print(f"mu (load stability):   {mu:.4f}")
print(f"mu' (source stability): {mu_prime:.4f}")
print(f"Load Stability Circle:   Center = {cL.real:.3f} + {cL.imag:.3f}j (|C_L|={abs(cL):.3f}), Radius R_L = {rL:.3f}")
print(f"Source Stability Circle: Center = {cS.real:.3f} + {cS.imag:.3f}j (|C_S|={abs(cS):.3f}), Radius R_S = {rS:.3f}")

print(f"Load circle min distance to origin: |C_L| - R_L = {abs(cL) - rL:.3f}")
print(f"Source circle min distance to origin: |C_S| - R_S = {abs(cS) - rS:.3f}")

