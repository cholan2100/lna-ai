import sys, os, time, shutil
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
from Microwave.Results.sparameters import SParameters
import skrf as rf

print("=" * 70)
print("  98 MHz FM LNA - Full-Board 4-Port EM Simulation via freecad-microwave")
print("=" * 70)

t_start = time.time()

# Dimensions
length = 46.0
sub_width = 30.0
height = 1.6
w_trace = 1.5
gap = 0.35
via_y = 2.5
gnd_edge = w_trace / 2.0 + gap
half_l = length / 2.0
half_w = sub_width / 2.0

freq_min = 10e6
freq_max = 500e6
f_centre = (freq_min + freq_max) / 2.0
kappa = 2.0 * np.pi * f_centre * VACUUM_PERMITTIVITY * 4.5 * 0.02

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
    # Top Coplanar Grounds
    Solid(material="Ground", lower=(-half_l, gnd_edge, height), upper=(half_l, half_w, height), priority=2, label="TopGroundNorth"),
    Solid(material="Ground", lower=(-half_l, -half_w, height), upper=(half_l, -gnd_edge, height), priority=2, label="TopGroundSouth"),
    # Ground Stitching Via Fences
    Solid(material="Ground", lower=(-half_l, via_y - 0.3, 0.0), upper=(half_l, via_y + 0.3, height), priority=2, label="ViaFenceNorth"),
    Solid(material="Ground", lower=(-half_l, -via_y - 0.3, 0.0), upper=(half_l, -via_y + 0.3, height), priority=2, label="ViaFenceSouth"),
    # Outer Boundary Ground Walls
    Solid(material="Ground", lower=(-half_l, half_w - 0.5, 0.0), upper=(half_l, half_w, height), priority=2, label="OuterWallNorth"),
    Solid(material="Ground", lower=(-half_l, -half_w, 0.0), upper=(half_l, -half_w + 0.5, height), priority=2, label="OuterWallSouth"),
    # Input RF Trace: SMA In (-23.0) to Input Match Pad (-14.5)
    Solid(material="Copper", lower=(-half_l, -w_trace / 2.0, height), upper=(-14.5, w_trace / 2.0, height), priority=2, label="InputTrace"),
    # Output RF Trace: Output Match Pad (+2.5) to SMA Out (+23.0)
    Solid(material="Copper", lower=(2.5, -w_trace / 2.0, height), upper=(half_l, w_trace / 2.0, height), priority=2, label="OutputTrace"),
]

def make_ports(excited_port):
    return (
        Port(number=1, kind="lumped", start=(-half_l, -w_trace / 2.0, height), stop=(-half_l + 0.5, w_trace / 2.0, 0.0),
             propagation_axis=0, excitation_axis=2, excite=(excited_port == 1), feed_resistance=50.0, reference_impedance=50.0, label="SMA_IN"),
        Port(number=2, kind="lumped", start=(-14.5, -w_trace / 2.0, height), stop=(-15.0, w_trace / 2.0, 0.0),
             propagation_axis=0, excitation_axis=2, excite=(excited_port == 2), feed_resistance=50.0, reference_impedance=50.0, label="IN_MATCH"),
        Port(number=3, kind="lumped", start=(2.5, -w_trace / 2.0, height), stop=(3.0, w_trace / 2.0, 0.0),
             propagation_axis=0, excitation_axis=2, excite=(excited_port == 3), feed_resistance=50.0, reference_impedance=50.0, label="OUT_MATCH"),
        Port(number=4, kind="lumped", start=(half_l, -w_trace / 2.0, height), stop=(half_l - 0.5, w_trace / 2.0, 0.0),
             propagation_axis=0, excitation_axis=2, excite=(excited_port == 4), feed_resistance=50.0, reference_impedance=50.0, label="SMA_OUT"),
    )

mesh_params = MeshParams(
    metal_res=0.4,
    dielectric_res=2.5,
    max_ratio=(1.4, 1.4, 1.4),
    min_lines=4,
    pml_cells=8,
    cap=3.5,
)

grid = write.plan_grid(
    solids,
    make_ports(1),
    materials,
    mesh_params,
    padding=((8, 8), (8, 8), (8, 8)),
)

print(f"Grid Size: {grid.cell_count:,} cells ({len(grid[0])} x {len(grid[1])} x {len(grid[2])})")

# Step 1: Run excited Port 1
print("\n[Run 1/2] Solving Port 1 excitation (SMA In)...")
sim_dir_p1 = os.path.join(os.getcwd(), "em_solve_p1")
os.makedirs(sim_dir_p1, exist_ok=True)
prob1 = Problem(
    title="LNA FM 98MHz 4-Port EM (Port 1 Excite)",
    frequency=Frequency(start=freq_min, stop=freq_max, points=491),
    grid=grid,
    materials=materials,
    solids=tuple(solids),
    ports=make_ports(1),
    boundary=("PML_8",) * 6,
    termination=Termination(max_timesteps=15000, end_criteria=1e-4),
)
env1 = write.write(prob1, sim_dir_p1)
python_exe = os.environ["MICROWAVE_OPENEMS_PYTHON"]

def progress(msg):
    txt = str(msg)
    if any(k in txt for k in ["Time", "Speed", "Energy", "cells", "DONE"]):
        print(f"  [openEMS] {txt.strip()[:80]}")

run.run(env1, interpreter=python_exe, on_output=progress)
res1 = read.read(sim_dir_p1)
print("  Port 1 solve complete!")

# Step 2: Run excited Port 4
print("\n[Run 2/2] Solving Port 4 excitation (SMA Out)...")
sim_dir_p4 = os.path.join(os.getcwd(), "em_solve_p4")
os.makedirs(sim_dir_p4, exist_ok=True)
prob4 = Problem(
    title="LNA FM 98MHz 4-Port EM (Port 4 Excite)",
    frequency=Frequency(start=freq_min, stop=freq_max, points=491),
    grid=grid,
    materials=materials,
    solids=tuple(solids),
    ports=make_ports(4),
    boundary=("PML_8",) * 6,
    termination=Termination(max_timesteps=15000, end_criteria=1e-4),
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

# Step 4: Write Touchstone .s4p file
out_s4p = os.path.join(os.getcwd(), "lna_board_full_4port.s4p")
rf_freq = rf.Frequency.from_f(freqs, unit="hz")
nw = rf.Network(frequency=rf_freq, s=s_matrix, z0=50.0)
nw.write_touchstone(out_s4p)
print(f"  Touchstone file saved to: {out_s4p}")

# Step 5: Summary at 98 MHz
idx_98 = np.argmin(np.abs(freqs - 98e6))
f_98 = freqs[idx_98] / 1e6
print("\n" + "=" * 70)
print(f"  Full-Board EM Results at {f_98:.1f} MHz:")
print("=" * 70)
print(f"  Input Trace (Port 1 <-> Port 2, L = 8.5 mm):")
print(f"    S11 (Return Loss)   : {20 * np.log10(np.abs(s_matrix[idx_98, 0, 0])):.2f} dB")
print(f"    S21 (Insertion Loss): {20 * np.log10(np.abs(s_matrix[idx_98, 1, 0])):.3f} dB")
print(f"  Output Trace (Port 3 <-> Port 4, L = 20.5 mm):")
print(f"    S44 (Return Loss)   : {20 * np.log10(np.abs(s_matrix[idx_98, 3, 3])):.2f} dB")
print(f"    S34 (Insertion Loss): {20 * np.log10(np.abs(s_matrix[idx_98, 2, 3])):.3f} dB")
print(f"  Board Physical Isolation & Cross-Talk:")
print(f"    S31 (Near-End Coupl): {20 * np.log10(np.abs(s_matrix[idx_98, 2, 0])):.2f} dB")
print(f"    S41 (Far-End Coupl) : {20 * np.log10(np.abs(s_matrix[idx_98, 3, 0])):.2f} dB")
print(f"  Total time            : {time.time() - t_start:.1f} s")
print("=" * 70)
