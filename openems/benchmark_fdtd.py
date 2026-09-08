import time, os, numpy as np
import openEMS, CSXCAD
from openEMS.ports import LumpedPort

t0 = time.time()
csx = CSXCAD.ContinuousStructure()
fdtd = openEMS.openEMS(EndCriteria=1e-3)
fdtd.SetCSX(csx)

f_min = 10e6
f_max = 500e6
f0 = 250e6
fc = 240e6
fdtd.SetGaussExcite(f0, fc)
fdtd.SetBoundaryCond(["PML_8", "PML_8", "PML_8", "PML_8", "PEC", "PML_8"])

# Grid
grid = csx.GetGrid()
grid.SetDeltaUnit(1e-3)
x_keys = [-28.0, -23.0, -22.5, -16.5, -14.5, -11.5, -7.0, -5.0, -2.0, 2.5, 22.5, 23.0, 28.0]
for x in x_keys: grid.AddLine("x", x)
grid.SmoothMeshLines("x", 0.7, 1.4)

y_keys = [-20.0, -15.0, -2.5, -1.1, -0.75, 0.0, 0.75, 1.1, 2.5, 15.0, 20.0]
for y in y_keys: grid.AddLine("y", y)
grid.SmoothMeshLines("y", 0.45, 1.4)

z_lines = np.array([-8.0, -3.0, 0.0, 0.5, 1.0, 1.6, 2.6, 5.0, 10.0])
grid.SetLines("z", z_lines)

nx = grid.GetQtyLines("x")
ny = grid.GetQtyLines("y")
nz = grid.GetQtyLines("z")
print(f"Mesh size: {nx} x {ny} x {nz} = {nx*ny*nz:,} cells")

# Material
fr4 = csx.AddMaterial("FR4", epsilon=4.5, kappa=2*np.pi*f0*8.854e-12*4.5*0.02)
fr4.AddBox([-23.0, -15.0, 0.0], [23.0, 15.0, 1.6])
cu = csx.AddConductingSheet("Copper", conductivity=5.8e7, thickness=35e-6)
cu.AddBox([-23.0, -0.75, 1.6], [23.0, 0.75, 1.6])

p1 = fdtd.AddLumpedPort(1, 50.0, [-23.0, -0.75, 1.6], [-22.5, 0.75, 0.0], 2, excite=1)
p2 = fdtd.AddLumpedPort(2, 50.0, [23.0, -0.75, 1.6], [22.5, 0.75, 0.0], 2, excite=0)

fdtd.SetNumberOfTimeSteps(2000)
sim_path = "tmp_bench_sim"
if not os.path.exists(sim_path): os.makedirs(sim_path)
csx.Write2XML(os.path.join(sim_path, "bench.xml"))
print("Starting benchmark run (2000 timesteps)...")
t_run = time.time()
fdtd.Run(sim_path, verbose=1)
t_end = time.time()
print(f"Benchmark completed in {t_end - t_run:.2f} s ({t_end - t0:.2f} s total)")
