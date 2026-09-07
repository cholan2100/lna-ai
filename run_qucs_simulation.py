import cmath
import subprocess
import shutil
from pathlib import Path
from parse_qucs import parse_qucs_dat

def run_sim(netlist_path, dat_path):
    cmd = [r'D:\Programs\Qucs-S\bin\qucsator_rf.exe', '-i', str(netlist_path), '-o', str(dat_path)]
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        print(f"Error running Qucsator on {netlist_path}:\n{res.stderr}")
        return False
    return True

def analyze(dat_path, label="QUCS Simulation"):
    freqs, data = parse_qucs_dat(dat_path)
    print(f"\n==========================================================================================")
    print(f" {label}")
    print(f"==========================================================================================")
    print(f"{'Freq (MHz)':>10} | {'S21 Gain (dB)':>14} | {'S11 Match (dB)':>14} | {'S22 Out (dB)':>12} | {'S12 Iso (dB)':>12} | {'K-factor':>9} | {'Zin (Ohm)':>14}")
    print(f"{'-'*10}-+-{'-'*14}-+-{'-'*14}-+-{'-'*12}-+-{'-'*12}-+-{'-'*9}-+-{'-'*14}")

    f_mhz_list = [round(f / 1e6, 1) for f in freqs]
    highlight_freqs = [88.0, 90.0, 92.0, 94.0, 96.0, 98.0, 100.0, 102.0, 104.0, 106.0, 108.0]

    for f_target in highlight_freqs:
        if f_target in f_mhz_list:
            idx = f_mhz_list.index(f_target)
            s11 = data['S[1,1]'][idx]
            s21 = data['S[2,1]'][idx]
            s12 = data['S[1,2]'][idx]
            s22 = data['S[2,2]'][idx]

            s11_db = 20 * cmath.log10(abs(s11)).real
            s21_db = 20 * cmath.log10(abs(s21)).real
            s12_db = 20 * cmath.log10(abs(s12)).real
            s22_db = 20 * cmath.log10(abs(s22)).real

            # Stability K-factor & Delta
            delta = (s11 * s22) - (s12 * s21)
            denom = 2 * abs(s12 * s21)
            k = (1 - abs(s11)**2 - abs(s22)**2 + abs(delta)**2) / denom if denom > 0 else 999.0

            # Input impedance
            zin = 50.0 * (1.0 + s11) / (1.0 - s11)
            zin_str = f"{zin.real:.1f} {'+' if zin.imag >= 0 else '-'} j{abs(zin.imag):.1f}"

            marker = " <-- CENTER" if f_target == 98.0 else ""
            print(f"{f_target:10.1f} | {s21_db:+14.2f} | {s11_db:+14.2f} | {s22_db:+12.2f} | {s12_db:+12.2f} | {k:9.2f} | {zin_str:>14}{marker}")

    # Center frequency detailed analysis
    idx_98 = f_mhz_list.index(98.0)
    s11_98 = data['S[1,1]'][idx_98]
    s21_98 = data['S[2,1]'][idx_98]
    s12_98 = data['S[1,2]'][idx_98]
    s22_98 = data['S[2,2]'][idx_98]
    vswr_in = (1 + abs(s11_98)) / (1 - abs(s11_98))
    zin_98 = 50.0 * (1.0 + s11_98) / (1.0 - s11_98)
    zout_98 = 50.0 * (1.0 + s22_98) / (1.0 - s22_98)

    print(f"\n--- Detailed Summary at 98.0 MHz (FM Center) ---")
    print(f"  * S21 (Transducer Power Gain): {20*cmath.log10(abs(s21_98)).real:+.2f} dB (Linear Mag = {abs(s21_98):.2f}, Phase = {cmath.phase(s21_98)*180/3.14159:+.1f}°)")
    print(f"  * S11 (Input Return Loss)    : {20*cmath.log10(abs(s11_98)).real:+.2f} dB (Input VSWR = {vswr_in:.2f}:1)")
    print(f"  * Input Impedance Zin        : {zin_98.real:.2f} + j{zin_98.imag:.2f} Ohm")
    print(f"  * S12 (Reverse Isolation)    : {20*cmath.log10(abs(s12_98)).real:+.2f} dB")
    print(f"  * S22 (Output Match)         : {20*cmath.log10(abs(s22_98)).real:+.2f} dB")
    print(f"  * Output Impedance Zout      : {zout_98.real:.2f} + j{zout_98.imag:.2f} Ohm")

def main():
    print("Running QUCS Simulation with CPWG Transmission Line Models...")
    if run_sim('lna_fm_98mhz_qucs_cpwg.net', 'lna_fm_98mhz_qucs_cpwg.dat'):
        analyze('lna_fm_98mhz_qucs_cpwg.dat', "Model: CPWG Transmission Lines (Physical PCB Microstrip/CPWG on 1.6mm FR-4)")

    # Also export Touchstone .s2p file
    cmd_conv = [r'D:\Programs\Qucs-S\bin\qucsconv_rf.exe', '-if', 'qucsdata', '-of', 'touchstone', '-i', 'lna_fm_98mhz_qucs_cpwg.dat', '-o', 'lna_fm_98mhz_cpwg.s2p']
    subprocess.run(cmd_conv, capture_output=True)
    print("\n[OK] Touchstone s2p exported to: lna_fm_98mhz_cpwg.s2p")

    # Run plot script
    cmd_plot = [r'D:\Programs\KiCad\bin\python.exe', 'plot_qucs_s_params.py']
    subprocess.run(cmd_plot, capture_output=True)
    print("[OK] S-Parameter plot updated: qucs_s_parameters_cpwg.svg")

if __name__ == '__main__':
    main()

