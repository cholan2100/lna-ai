import sys, os, time, shutil
import numpy as np
import CSXCAD, openEMS
import skrf as rf

print("=" * 70)
print("  98 MHz FM LNA - Full-Board 4-Port 3D EM Simulation (openEMS)")
print("=" * 70)

t_start = time.time()

# Frequency parameters
f_min = 10e6
f_max = 500e6
n_points = 491
freqs = np.linspace(f_min, f_max, n_points)
f0 = 1500e6
fc = 1450e6

# Board physical dimensions (mm)
length = 46.0
sub_width = 30.0
height = 1.6
w_trace = 1.5
gap = 0.35
via_y = 2.5
gnd_edge = w_trace / 2.0 + gap
half_l = length / 2.0
half_w = sub_width / 2.0

# Material parameters
eps_r = 4.5
tand = 0.02
copper_sigma = 5.8e7
copper_t = 0.035e-3
kappa = 2.0 * np.pi * f0 * 8.854187817e-12 * eps_r * tand

def build_model(excited_port_idx):
    csx = CSXCAD.ContinuousStructure()
    grid = csx.GetGrid()
    grid.SetDeltaUnit(1e-3)

    # Grid lines
    x_keys = [-28.0, -23.0, -22.5, -15.0, -14.5, 0.0, 2.5, 3.0, 22.5, 23.0, 28.0]
    for x in x_keys: grid.AddLine('x', x)
    grid.SmoothMeshLines('x', 0.6, 1.4)

    y_keys = [-20.0, -15.0, -2.8, -2.2, -1.10, -0.75, 0.0, 0.75, 1.10, 2.2, 2.8, 15.0, 20.0]
    for y in y_keys: grid.AddLine('y', y)
    grid.SmoothMeshLines('y', 0.4, 1.4)

    z_keys = [0.0, 0.4, 0.8, 1.2, 1.6, 2.3, 3.5, 5.5, 8.5, 13.0]
    for z in z_keys: grid.AddLine('z', z)

    # Substrate
    fr4 = csx.AddMaterial('FR4', epsilon=eps_r, kappa=kappa)
    fr4.AddBox([-half_l, -half_w, 0.0], [half_l, half_w, height], priority=0)

    # Ground planes
    gnd = csx.AddMetal('Ground')
    gnd.AddBox([-half_l, -half_w, 0.0], [half_l, half_w, 0.0], priority=1)
    gnd.AddBox([-half_l, gnd_edge, height], [half_l, half_w, height], priority=2)
    gnd.AddBox([-half_l, -half_w, height], [half_l, -gnd_edge, height], priority=2)
    gnd.AddBox([-half_l, via_y - 0.3, 0.0], [half_l, via_y + 0.3, height], priority=2)
    gnd.AddBox([-half_l, -via_y - 0.3, 0.0], [half_l, -via_y + 0.3, height], priority=2)

    # Copper Traces
    cu = csx.AddConductingSheet('Copper', conductivity=copper_sigma, thickness=copper_t)
    # Input Trace: X = -23.0 to -14.5 mm (L = 8.5 mm)
    cu.AddBox([-half_l, -w_trace / 2.0, height], [-14.5, w_trace / 2.0, height], priority=2)
    # Output Trace: X = +2.5 to +23.0 mm (L = 20.5 mm)
    cu.AddBox([2.5, -w_trace / 2.0, height], [half_l, w_trace / 2.0, height], priority=2)

    # FDTD Solver
    fdtd = openEMS.openEMS(NrTS=25000, EndCriteria=1e-4)
    fdtd.SetGaussExcite(f0, fc)
    fdtd.SetBoundaryCond(['PML_8', 'PML_8', 'PML_8', 'PML_8', 'PEC', 'PML_8'])
    fdtd.SetCSX(csx)

    # 4 Lumped Ports
    p1 = fdtd.AddLumpedPort(1, 50.0, [-half_l, -w_trace / 2.0, height], [-half_l + 0.5, w_trace / 2.0, 0.0], 2, excite=(1 if excited_port_idx == 1 else 0))
    p2 = fdtd.AddLumpedPort(2, 50.0, [-14.5, -w_trace / 2.0, height], [-15.0, w_trace / 2.0, 0.0], 2, excite=(1 if excited_port_idx == 2 else 0))
    p3 = fdtd.AddLumpedPort(3, 50.0, [2.5, -w_trace / 2.0, height], [3.0, w_trace / 2.0, 0.0], 2, excite=(1 if excited_port_idx == 3 else 0))
    p4 = fdtd.AddLumpedPort(4, 50.0, [half_l, -w_trace / 2.0, height], [half_l - 0.5, w_trace / 2.0, 0.0], 2, excite=(1 if excited_port_idx == 4 else 0))

    return csx, fdtd, [p1, p2, p3, p4]

# Step 1: Run Port 1 excitation (drives Input Trace from SMA In)
print("\n[Step 1/2] Simulating Port 1 excitation (SMA In)...")
sim_dir_p1 = os.path.join(os.getcwd(), "em_run_p1")
os.makedirs(sim_dir_p1, exist_ok=True)
csx1, fdtd1, ports1 = build_model(excited_port_idx=1)
csx1.Write2XML(os.path.join(sim_dir_p1, "structure.xml"))
t1 = time.time()
fdtd1.Run(sim_dir_p1, cleanup=True, verbose=1)
print(f"  Port 1 run finished in {time.time() - t1:.1f} s")

for p in ports1:
    p.CalcPort(sim_dir_p1, freqs)

v_inc1 = ports1[0].uf_inc
s11 = ports1[0].uf_ref / v_inc1
s21 = ports1[1].uf_ref / v_inc1
s31 = ports1[2].uf_ref / v_inc1
s41 = ports1[3].uf_ref / v_inc1

# Step 2: Run Port 4 excitation (drives Output Trace from SMA Out)
print("\n[Step 2/2] Simulating Port 4 excitation (SMA Out)...")
sim_dir_p4 = os.path.join(os.getcwd(), "em_run_p4")
os.makedirs(sim_dir_p4, exist_ok=True)
csx4, fdtd4, ports4 = build_model(excited_port_idx=4)
csx4.Write2XML(os.path.join(sim_dir_p4, "structure.xml"))
t4 = time.time()
fdtd4.Run(sim_dir_p4, cleanup=True, verbose=1)
print(f"  Port 4 run finished in {time.time() - t4:.1f} s")

for p in ports4:
    p.CalcPort(sim_dir_p4, freqs)

v_inc4 = ports4[3].uf_inc
s14 = ports4[0].uf_ref / v_inc4
s24 = ports4[1].uf_ref / v_inc4
s34 = ports4[2].uf_ref / v_inc4
s44 = ports4[3].uf_ref / v_inc4

# Step 3: Assemble Full 4x4 S-Matrix with physical symmetry & reciprocity
print("\n[Step 3] Assembling 4x4 S-Parameter Matrix across 10 MHz to 500 MHz...")
s_matrix = np.zeros((n_points, 4, 4), dtype=complex)

# Column 1 (excited Port 1)
s_matrix[:, 0, 0] = s11
s_matrix[:, 1, 0] = s21
s_matrix[:, 2, 0] = s31
s_matrix[:, 3, 0] = s41

# Column 4 (excited Port 4)
s_matrix[:, 0, 3] = s14
s_matrix[:, 1, 3] = s24
s_matrix[:, 2, 3] = s34
s_matrix[:, 3, 3] = s44

# Reciprocity (S_ij = S_ji)
s_matrix[:, 0, 1] = s21
s_matrix[:, 0, 2] = s31
s_matrix[:, 3, 1] = s24
s_matrix[:, 3, 2] = s34

# Physical trace symmetry:
# Trace 1 is a uniform CPWG line: S22 = S11
s_matrix[:, 1, 1] = s11

# Trace 2 is a uniform CPWG line: S33 = S44
s_matrix[:, 2, 2] = s44

# Cross-isolation between internal pads (symmetric reciprocal coupling):
s_matrix[:, 1, 2] = s31
s_matrix[:, 2, 1] = s31

# Step 4: Write Touchstone .s4p file using skrf
out_s4p = os.path.join(os.getcwd(), "lna_board_full_4port.s4p")
rf_freq = rf.Frequency.from_f(freqs, unit='hz')
nw = rf.Network(frequency=rf_freq, s=s_matrix, z0=50.0)
nw.write_touchstone(out_s4p)
print(f"  Touchstone file exported successfully:\n    {out_s4p}")

# Step 5: Print summary at 98 MHz
idx_98 = np.argmin(np.abs(freqs - 98e6))
f_98 = freqs[idx_98] / 1e6
print("\n" + "=" * 70)
print(f"  EM Results at {f_98:.2f} MHz:")
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
print(f"  Total solve time      : {time.time() - t_start:.1f} s")
print("=" * 70)
