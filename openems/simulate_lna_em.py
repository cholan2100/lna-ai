#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
simulate_lna_em.py: Full-Wave 3D EM Simulation of 50-Ohm CPWG Transmission Line
using freecad-microwave and openEMS.

Project: 98 MHz FM Low-Noise Amplifier (LNA)
Stackup: LionCircuits 1.6mm FR-4 (er=4.5, tand=0.02, 1oz copper 35um)
Geometry: Coplanar Waveguide with Ground (CPWG)
          Length L = 46.0 mm (SMA IN to SMA OUT)
          Substrate Width = 30.0 mm
          Substrate Height = 1.6 mm
          Center Trace Width W = 1.5 mm
          Ground Gap S = 0.35 mm
          Via Fence Flanking at Y = +/- 2.5 mm
"""

import sys
import os
import shutil
import tempfile
import numpy as np

# Ensure environment variables and paths are set
FREECAD_DIR = r"D:\Programs\FreeCAD"
OPENEMS_DIR = r"D:\Programs\openEMS"
MICROWAVE_MOD = os.path.join(FREECAD_DIR, "Mod", "Microwave")

os.environ["MICROWAVE_OPENEMS_PYTHON"] = os.path.join(FREECAD_DIR, "bin", "python.exe")
os.environ["OPENEMS_INSTALL_PATH"] = OPENEMS_DIR

for p in [FREECAD_DIR, os.path.join(FREECAD_DIR, "bin"), MICROWAVE_MOD]:
    if p not in sys.path:
        sys.path.insert(0, p)

# Fix Windows DLL loading for openEMS/CSXCAD
if hasattr(os, "add_dll_directory") and os.path.isdir(OPENEMS_DIR):
    try:
        os.add_dll_directory(OPENEMS_DIR)
    except Exception:
        pass

from Microwave.Solvers.openems import preflight, read, run, write
from Microwave.Solvers.openems.materials import VACUUM_PERMITTIVITY
from Microwave.Solvers.openems.mesh import MeshParams
from Microwave.Solvers.openems.model import (
    Frequency,
    Material,
    Port,
    Problem,
    Solid,
    Termination,
)
from Microwave.Results.sparameters import SParameters, MIRROR

def build_cpwg_problem() -> Problem:
    """Build the 3D FDTD problem for the 46mm 50-ohm CPWG transmission line."""
    # Physical dimensions in mm
    length = 46.0          # Board length (X: -23.0 to +23.0)
    sub_width = 30.0       # Board width  (Y: -15.0 to +15.0)
    height = 1.6           # FR-4 thickness (Z: 0.0 to 1.6)
    w_trace = 1.5          # 50-ohm CPWG trace width
    gap = 0.35             # Coplanar ground gap
    via_y = 2.5            # Distance of via fence from centerline
    gnd_edge = w_trace / 2.0 + gap  # Start of top ground plane (1.10 mm)

    half_l = length / 2.0
    half_w = sub_width / 2.0

    # Electrical parameters
    eps_r = 4.5
    loss_tangent = 0.02
    copper_sigma = 5.8e7
    copper_t = 0.035       # 35 um (1 oz)

    # Frequency band: 10 MHz to 3.0 GHz (includes 98 MHz fundamental + harmonics)
    freq_min = 10e6
    freq_max = 3000e6
    f_centre = (freq_min + freq_max) / 2.0
    kappa = 2.0 * np.pi * f_centre * VACUUM_PERMITTIVITY * eps_r * loss_tangent

    materials = (
        Material(
            name="FR4",
            kind="lossy_dielectric",
            epsilon=eps_r,
            kappa=kappa,
            measured_at=1e9,
        ),
        Material(name="Ground", kind="pec"),
        Material(
            name="Copper",
            kind="conducting_sheet",
            conductivity=copper_sigma,
            thickness=copper_t,
        ),
    )

    solids = [
        # 1. FR-4 Substrate
        Solid(
            material="FR4",
            lower=(-half_l, -half_w, 0.0),
            upper=(half_l, half_w, height),
            priority=0,
            label="Substrate",
        ),
        # 2. Bottom Solid Ground Plane (Z = 0)
        Solid(
            material="Ground",
            lower=(-half_l, -half_w, 0.0),
            upper=(half_l, half_w, 0.0),
            priority=1,
            label="BottomGround",
        ),
        # 3. Top Center CPWG RF Trace (Z = 1.6 mm)
        Solid(
            material="Copper",
            lower=(-half_l, -w_trace / 2.0, height),
            upper=(half_l, w_trace / 2.0, height),
            priority=2,
            label="CenterTrace",
        ),
        # 4. Top Coplanar Ground Planes (Z = 1.6 mm)
        Solid(
            material="Ground",
            lower=(-half_l, gnd_edge, height),
            upper=(half_l, half_w, height),
            priority=2,
            label="TopGroundNorth",
        ),
        Solid(
            material="Ground",
            lower=(-half_l, -half_w, height),
            upper=(half_l, -gnd_edge, height),
            priority=2,
            label="TopGroundSouth",
        ),
        # 5. Flanking Ground Stitching Via Fence (Connecting top & bottom ground)
        Solid(
            material="Ground",
            lower=(-half_l, via_y - 0.3, 0.0),
            upper=(half_l, via_y + 0.3, height),
            priority=2,
            label="ViaFenceNorth",
        ),
        Solid(
            material="Ground",
            lower=(-half_l, -via_y - 0.3, 0.0),
            upper=(half_l, -via_y + 0.3, height),
            priority=2,
            label="ViaFenceSouth",
        ),
        # 6. Outer Boundary Ground Walls
        Solid(
            material="Ground",
            lower=(-half_l, half_w - 0.5, 0.0),
            upper=(half_l, half_w, height),
            priority=2,
            label="OuterWallNorth",
        ),
        Solid(
            material="Ground",
            lower=(-half_l, -half_w, 0.0),
            upper=(half_l, -half_w + 0.5, height),
            priority=2,
            label="OuterWallSouth",
        ),
    ]

    # Ports: Lumped Ports at input and output ends, 50-ohm reference
    port_gap = 0.5  # Port cell length along X
    ports = (
        Port(
            number=1,
            kind="lumped",
            start=(-half_l, -w_trace / 2.0, height),
            stop=(-half_l + port_gap, w_trace / 2.0, 0.0),
            propagation_axis=0,
            excitation_axis=2,
            excite=True,
            feed_resistance=50.0,
            reference_impedance=50.0,
            label="SMA_IN_50R",
        ),
        Port(
            number=2,
            kind="lumped",
            start=(half_l, -w_trace / 2.0, height),
            stop=(half_l - port_gap, w_trace / 2.0, 0.0),
            propagation_axis=0,
            excitation_axis=2,
            excite=False,
            feed_resistance=50.0,
            reference_impedance=50.0,
            label="SMA_OUT_50R",
        ),
    )

    # Graded rectilinear Yee grid
    mesh_params = MeshParams(
        metal_res=0.25,          # 6 cells across 1.5mm trace
        dielectric_res=2.0,      # Bulk dielectric resolution
        max_ratio=(1.4, 1.4, 1.4),
        min_lines=4,
        pml_cells=8,
        cap=3.5,
    )

    grid = write.plan_grid(
        solids,
        ports,
        materials,
        mesh_params,
        padding=((8, 8), (8, 8), (8, 8)),
    )

    problem = Problem(
        title="LNA FM 98MHz 50-Ohm CPWG Line",
        frequency=Frequency(start=freq_min, stop=freq_max, points=151),
        grid=grid,
        materials=materials,
        solids=tuple(solids),
        ports=ports,
        boundary=("PML_8",) * 6,
        termination=Termination(max_timesteps=35000, end_criteria=1e-4),
    )

    return problem

def run_simulation():
    print("=" * 70)
    print("  98 MHz FM LNA - Full-Wave 3D EM Simulation (openEMS & freecad-microwave)")
    print("=" * 70)

    problem = build_cpwg_problem()
    print(f"Structure: 46.0 mm x 30.0 mm x 1.6 mm CPWG (W=1.5mm, S=0.35mm)")
    print(f"Grid Size: nx={len(problem.grid[0])}, ny={len(problem.grid[1])}, nz={len(problem.grid[2])}")
    print(f"Total FDTD Cells: {problem.grid.cell_count:,}")
    print(f"Frequency Sweep: {problem.frequency.start / 1e6:.1f} MHz to {problem.frequency.stop / 1e6:.1f} MHz ({problem.frequency.points} points)")

    # Run Preflight validation
    print("\nRunning preflight model checks...")
    findings = preflight.check(problem)
    preflight.refuse_if_blocked(findings)
    for f in findings:
        print(f"  [{f.severity}] {f.subjects}: {f.message}")

    # Solve with openEMS
    sim_dir = os.path.join(os.getcwd(), "em_simulation_run")
    os.makedirs(sim_dir, exist_ok=True)
    print(f"\nWriting FDTD simulation envelope to:\n  {sim_dir}")
    envelope = write.write(problem, sim_dir)

    print("\nLaunching openEMS solver subprocess...")
    python_exe = os.environ["MICROWAVE_OPENEMS_PYTHON"]

    def progress_callback(marker_or_text):
        msg = str(marker_or_text)
        if any(k in msg for k in ["FDTD", "Time", "progress", "cells", "Speed", "DONE"]):
            print(f"  [openEMS] {msg.strip()[:85]}")

    run.run(envelope, interpreter=python_exe, on_output=progress_callback)

    print("\nSimulation complete! Reading results...")
    result = read.read(sim_dir)

    # S-Parameters assembly with mirror symmetry
    sp = SParameters.from_runs([result], reference=50.0, symmetry=MIRROR)

    # Save Touchstone .s2p file
    s2p_file = os.path.join(os.getcwd(), "lna_cpwg_openems.s2p")
    sp.write_touchstone(os.path.splitext(s2p_file)[0])
    print(f"Exported Touchstone 2-port file:\n  {s2p_file}")

    # Post-process results
    freqs = sp.frequency
    freqs_mhz = freqs / 1e6
    s11 = sp.parameter(1, 1)
    s21 = sp.parameter(2, 1)

    s11_db = 20.0 * np.log10(np.maximum(np.abs(s11), 1e-9))
    s21_db = 20.0 * np.log10(np.maximum(np.abs(s21), 1e-9))

    # Calculate Characteristic Impedance Z0(f) from transmission line S-parameters:
    # Z0 = Z_ref * sqrt( ((1 + S11)^2 - S21^2) / ((1 - S11)^2 - S21^2) )
    term_num = (1.0 + s11)**2 - s21**2
    term_den = (1.0 - s11)**2 - s21**2
    z0_complex = 50.0 * np.sqrt(term_num / term_den)
    z0_mag = np.abs(z0_complex)

    # Find index closest to 98 MHz
    idx_98 = np.argmin(np.abs(freqs - 98e6))
    f_98 = freqs_mhz[idx_98]
    s11_98 = s11_db[idx_98]
    s21_98 = s21_db[idx_98]
    vswr_98 = (1.0 + np.abs(s11[idx_98])) / (1.0 - np.abs(s11[idx_98]))
    z0_98 = z0_mag[idx_98]
    z0_real_98 = z0_complex[idx_98].real
    z0_imag_98 = z0_complex[idx_98].imag

    print("\n" + "=" * 70)
    print("  SIMULATION RESULTS AT 98 MHz FM OPERATING POINT")
    print("=" * 70)
    print(f"  Frequency              : {f_98:.2f} MHz")
    print(f"  Return Loss |S11|      : {s11_98:.2f} dB (VSWR = {vswr_98:.3f}:1)")
    print(f"  Insertion Loss |S21|   : {s21_98:.3f} dB")
    print(f"  Characteristic Imp Z0  : {z0_real_98:.2f} + j{z0_imag_98:.2f} Ohm (|Z0| = {z0_98:.2f} Ohm)")
    print(f"  Match Deviation to 50R : {abs(z0_98 - 50.0):.2f} Ohm ({abs(z0_98 - 50.0)/50.0*100:.2f}%)")
    print("=" * 70)

    # Additional spot frequencies
    print("\nVHF / UHF Harmonic Performance:")
    print("  Freq (MHz) | S11 (dB) | S21 (dB) | |Z0| (Ohm) | VSWR")
    print("  " + "-" * 52)
    for target_f in [98e6, 196e6, 294e6, 500e6, 1000e6, 2000e6]:
        idx = np.argmin(np.abs(freqs - target_f))
        vswr = (1.0 + np.abs(s11[idx])) / (1.0 - np.abs(s11[idx]))
        print(f"  {freqs_mhz[idx]:9.1f}  | {s11_db[idx]:8.2f} | {s21_db[idx]:8.3f} | {z0_mag[idx]:10.2f} | {vswr:6.2f}:1")

    # Generate Publication-Quality Plots
    generate_plots(freqs_mhz, s11_db, s21_db, z0_mag, z0_complex, idx_98)

def generate_plots(freqs_mhz, s11_db, s21_db, z0_mag, z0_complex, idx_98):
    """Plot S-parameters and characteristic impedance."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle("Full-Wave 3D EM Simulation: 50-Ohm CPWG Transmission Line (openEMS)", fontsize=14, fontweight="bold", y=0.98)

    # Color scheme
    c_s11 = "#1f77b4"
    c_s21 = "#d62728"
    c_z0 = "#2ca02c"
    c_marker = "#ff7f0e"

    # Subplot 1: Wideband S-Parameters (10 MHz to 3 GHz)
    ax1 = axes[0, 0]
    ax1.plot(freqs_mhz, s11_db, label="$S_{11}$ Return Loss", color=c_s11, linewidth=2)
    ax1.plot(freqs_mhz, s21_db, label="$S_{21}$ Insertion Loss", color=c_s21, linewidth=2)
    ax1.axvline(freqs_mhz[idx_98], color="gray", linestyle="--", alpha=0.6, label="98 MHz FM")
    ax1.scatter([freqs_mhz[idx_98]], [s11_db[idx_98]], color=c_marker, s=80, zorder=5)
    ax1.scatter([freqs_mhz[idx_98]], [s21_db[idx_98]], color=c_marker, s=80, zorder=5)
    ax1.set_title("Wideband S-Parameters (10 MHz - 3 GHz)", fontweight="bold")
    ax1.set_xlabel("Frequency (MHz)")
    ax1.set_ylabel("Magnitude (dB)")
    ax1.set_ylim(-50, 2)
    ax1.grid(True, linestyle=":", alpha=0.7)
    ax1.legend(loc="lower left", framealpha=0.9)

    # Subplot 2: Zoomed-in Response around 98 MHz (10 MHz to 500 MHz)
    mask_vhf = freqs_mhz <= 500.0
    ax2 = axes[0, 1]
    ax2.plot(freqs_mhz[mask_vhf], s11_db[mask_vhf], label="$S_{11}$ (dB)", color=c_s11, linewidth=2.5)
    ax2.plot(freqs_mhz[mask_vhf], s21_db[mask_vhf], label="$S_{21}$ (dB)", color=c_s21, linewidth=2.5)
    ax2.axvline(freqs_mhz[idx_98], color="gray", linestyle="--", alpha=0.6)
    ax2.annotate(
        f"98 MHz:\n$S_{{11}} = {s11_db[idx_98]:.1f}$ dB\n$S_{{21}} = {s21_db[idx_98]:.3f}$ dB",
        xy=(freqs_mhz[idx_98], s11_db[idx_98]),
        xytext=(freqs_mhz[idx_98] + 40, s11_db[idx_98] - 5),
        arrowprops=dict(facecolor="black", shrink=0.08, width=1, headwidth=6),
        fontsize=10,
        bbox=dict(boxstyle="round,pad=0.3", fc="yellow", alpha=0.4),
    )
    ax2.set_title("VHF Band Detail (10 MHz - 500 MHz)", fontweight="bold")
    ax2.set_xlabel("Frequency (MHz)")
    ax2.set_ylabel("Magnitude (dB)")
    ax2.set_ylim(-45, 1)
    ax2.grid(True, linestyle=":", alpha=0.7)
    ax2.legend(loc="lower left", framealpha=0.9)

    # Subplot 3: Characteristic Impedance |Z0| vs Frequency
    ax3 = axes[1, 0]
    ax3.plot(freqs_mhz, z0_mag, label="Extracted $|Z_0|$", color=c_z0, linewidth=2)
    ax3.axhline(50.0, color="black", linestyle="--", linewidth=1.2, label="Nominal 50 $\Omega$")
    ax3.fill_between(freqs_mhz, 48.0, 52.0, color="gray", alpha=0.15, label="$\pm 4\%$ Tolerance")
    ax3.scatter([freqs_mhz[idx_98]], [z0_mag[idx_98]], color=c_marker, s=80, zorder=5)
    ax3.annotate(
        f"$Z_0(98\\text{{MHz}}) = {z0_mag[idx_98]:.2f}\ \\Omega$",
        xy=(freqs_mhz[idx_98], z0_mag[idx_98]),
        xytext=(freqs_mhz[idx_98] + 200, z0_mag[idx_98] + 2.5),
        arrowprops=dict(facecolor="black", shrink=0.08, width=1, headwidth=6),
        fontsize=10,
        bbox=dict(boxstyle="round,pad=0.3", fc="lightgreen", alpha=0.4),
    )
    ax3.set_title("CPWG Characteristic Impedance $Z_0(f)$", fontweight="bold")
    ax3.set_xlabel("Frequency (MHz)")
    ax3.set_ylabel("Impedance ($\Omega$)")
    ax3.set_ylim(40, 60)
    ax3.grid(True, linestyle=":", alpha=0.7)
    ax3.legend(loc="upper right", framealpha=0.9)

    # Subplot 4: Complex Line Impedance (Real & Imaginary)
    ax4 = axes[1, 1]
    ax4.plot(freqs_mhz, [z.real for z in z0_complex], label="Re{$Z_0$}", color="#2b5c8f", linewidth=2)
    ax4.plot(freqs_mhz, [z.imag for z in z0_complex], label="Im{$Z_0$}", color="#c0392b", linestyle=":", linewidth=2)
    ax4.axhline(50.0, color="black", linestyle="--", linewidth=1.0)
    ax4.axhline(0.0, color="gray", linestyle="-", linewidth=0.8)
    ax4.scatter([freqs_mhz[idx_98]], [z0_complex[idx_98].real], color=c_marker, s=80, zorder=5)
    ax4.set_title("Complex Line Impedance (Re & Im)", fontweight="bold")
    ax4.set_xlabel("Frequency (MHz)")
    ax4.set_ylabel("Impedance ($\Omega$)")
    ax4.set_ylim(-10, 65)
    ax4.grid(True, linestyle=":", alpha=0.7)
    ax4.legend(loc="upper right", framealpha=0.9)

    plt.tight_layout()
    output_png = os.path.join(os.getcwd(), "lna_em_simulation_results.png")
    plt.savefig(output_png, dpi=180)
    print(f"Generated comparison plot:\n  {output_png}")

    # Also copy to artifact directory if available
    artifact_dir = r"C:\Users\gsr\.gemini\antigravity\brain\10ba1c4f-bbc3-4e37-a73e-8d226cc7ff03"
    if os.path.isdir(artifact_dir):
        dest_png = os.path.join(artifact_dir, "lna_em_simulation_results.png")
        shutil.copyfile(output_png, dest_png)
        print(f"Copied plot to artifact directory:\n  {dest_png}")

if __name__ == "__main__":
    run_simulation()
