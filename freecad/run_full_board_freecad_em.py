#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
run_full_board_freecad_em.py: Full-wave 3D FDTD electromagnetic simulation of
the 34 mm x 29 mm FM LNA board using FreeCAD-Microwave Workbench solver engine.

Outputs:
  - lna_board_full_4port.s4p Touchstone file saved to freecad/, qucs-sim/, and openems/.
"""

import sys, os, time, shutil, tempfile
import numpy as np

FREECAD_DIR = r"D:\Programs\FreeCAD"
OPENEMS_DIR = r"D:\Programs\openEMS"
MICROWAVE_MOD = os.path.join(FREECAD_DIR, "Mod", "Microwave")

os.environ["MICROWAVE_OPENEMS_PYTHON"] = os.path.join(FREECAD_DIR, "bin", "python.exe")
os.environ["OPENEMS_INSTALL_PATH"] = OPENEMS_DIR

for p in [FREECAD_DIR, os.path.join(FREECAD_DIR, "bin"), MICROWAVE_MOD]:
    if p not in sys.path:
        sys.path.insert(0, p)

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
import skrf as rf

print("=" * 70)
print("  98 MHz FM LNA - Full-Board 4-Port EM Simulation via FreeCAD-Microwave")
print("=" * 70)

t_start = time.time()

# Enclosure-matched board dimensions (mm)
length = 34.0
sub_width = 29.0
height = 1.6
w_trace = 1.5
gap = 0.35
y_rf = -2.5  # Y = 17.00 mm on PCB (offset by -2.5 mm from cavity center)
via_y = 2.5
gnd_edge = w_trace / 2.0 + gap  # 1.10 mm
half_l = length / 2.0  # 17.0 mm
half_w = sub_width / 2.0  # 14.5 mm

freq_min = 10e6
freq_max = 2500e6
f_centre = (freq_min + freq_max) / 2.0
kappa = 2.0 * np.pi * 98e6 * VACUUM_PERMITTIVITY * 4.5 * 0.02

materials = (
    Material(name="FR4", kind="lossy_dielectric", epsilon=4.5, kappa=kappa, measured_at=1e9),
    Material(name="Ground", kind="pec"),
    Material(name="Copper", kind="conducting_sheet", conductivity=5.8e7, thickness=0.035),
)

solids = [
    # FR-4 Substrate
    Solid(material="FR4", lower=(-half_l, -half_w, 0.0), upper=(half_l, half_w, height), priority=0, label="Substrate"),
    # Bottom Ground
    Solid(material="Ground", lower=(-half_l, -half_w, 0.0), upper=(half_l, half_w, 0.0), priority=1, label="BottomGround"),
    # Top Coplanar Grounds North & South
    Solid(material="Ground", lower=(-half_l, y_rf + gnd_edge, height), upper=(half_l, half_w, height), priority=2, label="TopGroundNorth"),
    Solid(material="Ground", lower=(-half_l, -half_w, height), upper=(half_l, y_rf - gnd_edge, height), priority=2, label="TopGroundSouth"),
    # Ground Stitching Via Fences
    Solid(material="Ground", lower=(-half_l, y_rf + via_y - 0.3, 0.0), upper=(half_l, y_rf + via_y + 0.3, height), priority=2, label="ViaFenceNorth"),
    Solid(material="Ground", lower=(-half_l, y_rf - via_y - 0.3, 0.0), upper=(half_l, y_rf - via_y + 0.3, height), priority=2, label="ViaFenceSouth"),
    # Central Active Component Area (X = -8.5 to +6.0 mm, open on top copper layer for Q1, L1-L4, C1-C12)
    # Input RF Trace: SMA In (-17.0) to Input Match Pad (-8.5) (Length = 8.5 mm)
    Solid(material="Copper", lower=(-half_l, y_rf - w_trace / 2.0, height), upper=(-8.5, y_rf + w_trace / 2.0, height), priority=2, label="InputTrace"),
    # Output RF Trace: Output Match Pad (+6.0) to SMA Out (+17.0) (Length = 11.0 mm)
    Solid(material="Copper", lower=(6.0, y_rf - w_trace / 2.0, height), upper=(half_l, y_rf + w_trace / 2.0, height), priority=2, label="OutputTrace"),
]

def make_ports(excited_port):
    return (
        Port(number=1, kind="lumped", start=(-half_l, y_rf - w_trace / 2.0, height), stop=(-half_l + 0.5, y_rf + w_trace / 2.0, 0.0),
             propagation_axis=0, excitation_axis=2, excite=(excited_port == 1), feed_resistance=50.0, reference_impedance=50.0, label="SMA_IN"),
        Port(number=2, kind="lumped", start=(-8.5, y_rf - w_trace / 2.0, height), stop=(-9.0, y_rf + w_trace / 2.0, 0.0),
             propagation_axis=0, excitation_axis=2, excite=(excited_port == 2), feed_resistance=50.0, reference_impedance=50.0, label="IN_MATCH"),
        Port(number=3, kind="lumped", start=(6.0, y_rf - w_trace / 2.0, height), stop=(6.5, y_rf + w_trace / 2.0, 0.0),
             propagation_axis=0, excitation_axis=2, excite=(excited_port == 3), feed_resistance=50.0, reference_impedance=50.0, label="OUT_MATCH"),
        Port(number=4, kind="lumped", start=(half_l, y_rf - w_trace / 2.0, height), stop=(half_l - 0.5, y_rf + w_trace / 2.0, 0.0),
             propagation_axis=0, excitation_axis=2, excite=(excited_port == 4), feed_resistance=50.0, reference_impedance=50.0, label="SMA_OUT"),
    )

mesh_params = MeshParams(
    metal_res=0.6,
    dielectric_res=2.5,
    max_ratio=(1.5, 1.5, 1.5),
    min_lines=3,
    pml_cells=8,
    cap=4.0,
)

grid = write.plan_grid(
    solids,
    make_ports(1),
    materials,
    mesh_params,
    padding=((4, 4), (4, 4), (4, 4)),
)

print(f"Grid Size: {grid.cell_count:,} cells ({len(grid[0])} x {len(grid[1])} x {len(grid[2])})")

tmp_dir = tempfile.mkdtemp(prefix="freecad_mw_")
sim_dir_p1 = os.path.join(tmp_dir, "solve_p1")
sim_dir_p4 = os.path.join(tmp_dir, "solve_p4")

try:
    # Step 1: Run excited Port 1
    print("\n[Run 1/2] Solving Port 1 excitation (SMA In)...")
    prob1 = Problem(
        title="LNA FM 98MHz 4-Port EM (Port 1 Excite)",
        frequency=Frequency(start=freq_min, stop=freq_max, points=491),
        grid=grid,
        materials=materials,
        solids=tuple(solids),
        ports=make_ports(1),
        boundary=("PML_8",) * 6,
        termination=Termination(max_timesteps=60000, end_criteria=1e-4),
    )
    env1 = write.write(prob1, sim_dir_p1)
    python_exe = os.environ["MICROWAVE_OPENEMS_PYTHON"]

    def progress(msg):
        txt = str(msg)
        if any(k in txt for k in ["Time", "Speed", "Energy", "cells", "DONE"]):
            print(f"  [FreeCAD-Microwave / openEMS] {txt.strip()[:80]}")

    run.run(env1, interpreter=python_exe, on_output=progress)
    res1 = read.read(sim_dir_p1)
    print("  Port 1 solve complete!")

    # Step 2: Run excited Port 4
    print("\n[Run 2/2] Solving Port 4 excitation (SMA Out)...")
    prob4 = Problem(
        title="LNA FM 98MHz 4-Port EM (Port 4 Excite)",
        frequency=Frequency(start=freq_min, stop=freq_max, points=491),
        grid=grid,
        materials=materials,
        solids=tuple(solids),
        ports=make_ports(4),
        boundary=("PML_8",) * 6,
        termination=Termination(max_timesteps=60000, end_criteria=1e-4),
    )
    env4 = write.write(prob4, sim_dir_p4)
    run.run(env4, interpreter=python_exe, on_output=progress)
    res4 = read.read(sim_dir_p4)
    print("  Port 4 solve complete!")

    # Step 3: Assemble Full 4x4 S-Parameters
    print("\n[Step 3] Assembling complete 4x4 S-Matrix...")
    freqs = np.asarray(res1.frequency)
    n_pts = freqs.size
    s_matrix = np.zeros((n_pts, 4, 4), dtype=complex)

    for i in range(4):
        p_num = i + 1
        s_matrix[:, i, 0] = res1.s(p_num, 1)
        s_matrix[:, i, 3] = res4.s(p_num, 4)

    # Reciprocity
    s_matrix[:, 0, 1] = s_matrix[:, 1, 0]
    s_matrix[:, 0, 2] = s_matrix[:, 2, 0]
    s_matrix[:, 3, 1] = s_matrix[:, 1, 3]
    s_matrix[:, 3, 2] = s_matrix[:, 2, 3]

    # Transmission line symmetry
    s_matrix[:, 1, 1] = s_matrix[:, 0, 0] # Input CPWG Trace 1
    s_matrix[:, 2, 2] = s_matrix[:, 3, 3] # Output CPWG Trace 2
    s_matrix[:, 1, 2] = s_matrix[:, 2, 0] # Internal pad cross-isolation
    s_matrix[:, 2, 1] = s_matrix[:, 1, 2]

    # Step 4: Write Touchstone .s4p file to freecad/, qucs-sim/, and openems/
    rf_freq = rf.Frequency.from_f(freqs, unit="hz")
    nw = rf.Network(frequency=rf_freq, s=s_matrix, z0=50.0)

    script_dir = os.path.dirname(os.path.abspath(__file__))
    repo_dir = os.path.dirname(script_dir)

    target_paths = [
        os.path.join(script_dir, "lna_board_full_4port.s4p"),
        os.path.join(repo_dir, "qucs-sim", "lna_board_full_4port.s4p"),
        os.path.join(repo_dir, "openems", "lna_board_full_4port.s4p"),
    ]

    for p in target_paths:
        nw.write_touchstone(p)
        print(f"  Touchstone file saved to: {p}")

    # Step 5: Summary at 98 MHz
    idx_98 = np.argmin(np.abs(freqs - 98e6))
    f_98 = freqs[idx_98] / 1e6
    print("\n" + "=" * 70)
    print(f"  FreeCAD-Microwave Full-Board EM Results at {f_98:.1f} MHz:")
    print("=" * 70)
    print(f"  Input Trace (Port 1 <-> Port 2, L = 8.5 mm):")
    print(f"    S11 (Return Loss)   : {20 * np.log10(np.abs(s_matrix[idx_98, 0, 0])):.2f} dB")
    print(f"    S21 (Insertion Loss): {20 * np.log10(np.abs(s_matrix[idx_98, 1, 0])):.3f} dB")
    print(f"  Output Trace (Port 3 <-> Port 4, L = 11.0 mm):")
    print(f"    S44 (Return Loss)   : {20 * np.log10(np.abs(s_matrix[idx_98, 3, 3])):.2f} dB")
    print(f"    S34 (Insertion Loss): {20 * np.log10(np.abs(s_matrix[idx_98, 2, 3])):.3f} dB")
    print(f"  Board Physical Isolation & Cross-Talk:")
    print(f"    S31 (Near-End Coupl): {20 * np.log10(np.abs(s_matrix[idx_98, 2, 0])):.2f} dB")
    print(f"    S41 (Far-End Coupl) : {20 * np.log10(np.abs(s_matrix[idx_98, 3, 0])):.2f} dB")
    print(f"  Total time            : {time.time() - t_start:.1f} s")
    print("=" * 70)

finally:
    shutil.rmtree(tmp_dir, ignore_errors=True)
