#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
run_pipeline.py: Master End-to-End Orchestrator for 98 MHz FM LNA
Workflow: KiCad -> FreeCAD -> FreeCAD-Microwave -> Qucs-S

Usage:
  python run_pipeline.py            # Runs verification, FreeCAD model build, Qucs co-sim, and plotting
  python run_pipeline.py --solve-em # Also runs the full-wave 3D FDTD EM solver via FreeCAD-Microwave
"""

import sys
import os
import subprocess
import argparse
import time

REPO_DIR = os.path.dirname(os.path.abspath(__file__))
FREECAD_PYTHON = r"D:\Programs\FreeCAD\bin\python.exe"
KICAD_PYTHON = r"D:\Programs\KiCad\bin\python.exe"
QUCSATOR = r"D:\Programs\Qucs-S\bin\qucsator_rf.exe"

def run_step(title, cmd, cwd=REPO_DIR):
    print("\n" + "=" * 75)
    print(f"  [STEP] {title}")
    print("=" * 75)
    t0 = time.time()
    res = subprocess.run(cmd, cwd=cwd, text=True, capture_output=True)
    dt = time.time() - t0
    if res.stdout:
        print(res.stdout.strip())
    if res.returncode != 0:
        if res.stderr:
            print("[STDERR]", res.stderr.strip())
        print(f"\n[FAILED] Step failed with return code {res.returncode} ({dt:.1f}s)")
        sys.exit(res.returncode)
    else:
        print(f"\n[SUCCESS] Completed in {dt:.1f}s")

def main():
    parser = argparse.ArgumentParser(description="End-to-End KiCad -> FreeCAD -> FreeCAD-Microwave -> Qucs-S Pipeline")
    parser.add_argument("--solve-em", action="store_true", help="Run full 3D FDTD EM solve via FreeCAD-Microwave (~25 min)")
    args = parser.parse_args()

    print("*" * 75)
    print("  98 MHz FM Low-Noise Amplifier (LNA)")
    print("  Complete Multi-Physics Toolchain Orchestrator")
    print("  KiCad -> FreeCAD -> FreeCAD-Microwave -> Qucs-S")
    print("*" * 75)

    # 1. KiCad Verification
    kicad_pcb = os.path.join(REPO_DIR, "kicad", "lna_fm_98mhz.kicad_pcb")
    if os.path.exists(kicad_pcb):
        print(f"[KiCad PCB]: Found {kicad_pcb} ({os.path.getsize(kicad_pcb)} bytes)")
    else:
        print(f"[ERROR]: KiCad PCB not found at {kicad_pcb}")
        sys.exit(1)

    # 2. FreeCAD 3D Microwave Workbench Model Build
    run_step(
        "Build Native FreeCAD-Microwave Model (.FCStd)",
        [FREECAD_PYTHON, os.path.join("freecad", "build_freecad_microwave_model.py")]
    )

    # 3. FreeCAD-Microwave Full-Board EM Solve (if requested or missing)
    s4p_file = os.path.join(REPO_DIR, "qucs-sim", "lna_board_full_4port.s4p")
    if args.solve_em or not os.path.exists(s4p_file):
        run_step(
            "Solve 4-Port Board EM via FreeCAD-Microwave / openEMS",
            [FREECAD_PYTHON, os.path.join("freecad", "run_full_board_freecad_em.py")]
        )
    else:
        print("\n" + "=" * 75)
        print("  [STEP] FreeCAD-Microwave 4-Port EM Touchstone (.s4p)")
        print("=" * 75)
        print(f"  Found existing Touchstone model: {s4p_file} ({os.path.getsize(s4p_file)} bytes)")
        print("  (Use '--solve-em' to re-run the full 3D FDTD solver)")

    # 4. Qucs-S Active Circuit Co-Simulation
    run_step(
        "Run Active Circuit Co-Simulation in Qucs-S",
        [FREECAD_PYTHON, os.path.join("qucs-sim", "run_full_board_cosim.py")]
    )

    # 5. Plot Comparison & Performance Curves
    run_step(
        "Generate Co-Simulation Comparison Plots",
        [FREECAD_PYTHON, os.path.join("qucs-sim", "plot_full_board_cosim_results.py")]
    )
    run_step(
        "Generate Smith Chart & S-Parameter Curves",
        [FREECAD_PYTHON, os.path.join("qucs-sim", "plot_smith_and_cartesian.py")]
    )

    print("\n" + "*" * 75)
    print("  ALL PIPELINE STEPS COMPLETED SUCCESSFULLY!")
    print(f"  - FreeCAD Model  : freecad/lna_fm_98mhz_microwave.FCStd")
    print(f"  - Touchstone S4P : freecad/lna_board_full_4port.s4p")
    print(f"  - Qucs-S Co-Sim  : qucs-sim/lna_fm_98mhz_full_board_cosim.dat")
    print(f"  - Plots Rendered : renders/lna_full_board_cosim_results.png")
    print(f"                   : renders/final_qucs_cosim_s_params_and_smith.png")
    print("*" * 75)

if __name__ == "__main__":
    main()
