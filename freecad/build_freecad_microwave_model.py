#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build_freecad_microwave_model.py: Generates native FreeCAD project file (.FCStd)
with complete 3D EM model for FreeCAD-Microwave Workbench.

Board Specifications (Enclosure Matched):
  - Substrate Dimensions: 34.00 mm x 29.00 mm x 1.60 mm
  - Corner Fillets: 4x R = 3.00 mm
  - Substrate Material: FR-4 (er = 4.5, tand = 0.02)
  - Metallization: 1 oz Copper (35 um, sigma = 5.8e7 S/m)
  - RF Transmission Line: 50-Ohm CPWG (W = 1.50 mm, S = 0.35 mm)
  - RF Centerline: Y_RF = 17.00 mm (y_rf = -2.50 mm relative to center)
  - Ports:
      Port 1: SMA RF In (X = -17.00 mm)
      Port 2: Input Pre-Filter / Emitter Match Pad (X = -8.50 mm)
      Port 3: Output Collector Tank Pad (X = +6.00 mm)
      Port 4: SMA RF Out (X = +17.00 mm)
"""

import sys, os

FREECAD_DIR = r"D:\Programs\FreeCAD"
MICROWAVE_MOD = os.path.join(FREECAD_DIR, "Mod", "Microwave")

for p in [FREECAD_DIR, os.path.join(FREECAD_DIR, "bin"), MICROWAVE_MOD]:
    if p not in sys.path:
        sys.path.insert(0, p)

import FreeCAD, Part
from Microwave.Objects.analysis import createEMAnalysis, solver_of
from Microwave.Objects.materials import createEMMaterial, createEMMaterialBinding
from Microwave.Objects.ports import createEMPortLumped

def build_model(out_fcstd=None):
    if out_fcstd is None:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        out_fcstd = os.path.join(script_dir, "lna_fm_98mhz_microwave.FCStd")

    print(f"Building FreeCAD-Microwave 3D model...")
    doc = FreeCAD.newDocument("lna_fm_98mhz_microwave")

    # Dimensions (mm)
    length = 34.0
    width = 29.0
    height = 1.6
    w_trace = 1.5
    gap = 0.35
    y_rf = -2.5       # Y = 17.0 mm on PCB (offset from center)
    gnd_edge = w_trace / 2.0 + gap  # 1.10 mm from trace centerline
    via_y = 2.5       # Stitching via centerline offset

    half_l = length / 2.0  # 17.0 mm
    half_w = width / 2.0   # 14.5 mm

    # 1. Substrate
    sub = doc.addObject("Part::Box", "Substrate")
    sub.Length, sub.Width, sub.Height = length, width, height
    sub.Placement.Base = FreeCAD.Vector(-half_l, -half_w, 0.0)

    # 2. Bottom Solid Ground Plane
    bot_gnd = doc.addObject("Part::Plane", "BottomGround")
    bot_gnd.Length, bot_gnd.Width = length, width
    bot_gnd.Placement.Base = FreeCAD.Vector(-half_l, -half_w, 0.0)

    # 3. Top Coplanar Ground North (above RF trace)
    gnd_north_w = half_w - (y_rf + gnd_edge)
    gnd_north = doc.addObject("Part::Plane", "TopGroundNorth")
    gnd_north.Length, gnd_north.Width = length, gnd_north_w
    gnd_north.Placement.Base = FreeCAD.Vector(-half_l, y_rf + gnd_edge, height)

    # 4. Top Coplanar Ground South (below RF trace)
    gnd_south_w = (y_rf - gnd_edge) - (-half_w)
    gnd_south = doc.addObject("Part::Plane", "TopGroundSouth")
    gnd_south.Length, gnd_south.Width = length, gnd_south_w
    gnd_south.Placement.Base = FreeCAD.Vector(-half_l, -half_w, height)

    # 5. Active Component Cavity (X = -8.5 to +6.0 mm, ungrounded top layer for Q1, L1-L4, C1-C12)

    # 6. Input CPWG Trace: SMA In (-17.0) to In Match Pad (-8.5)
    in_len = 8.5
    trace_in = doc.addObject("Part::Plane", "InputTrace_CPWG")
    trace_in.Length, trace_in.Width = in_len, w_trace
    trace_in.Placement.Base = FreeCAD.Vector(-half_l, y_rf - w_trace / 2.0, height)

    # 7. Output CPWG Trace: Out Match Pad (+6.0) to SMA Out (+17.0)
    out_len = half_l - 6.0 # 11.0 mm
    trace_out = doc.addObject("Part::Plane", "OutputTrace_CPWG")
    trace_out.Length, trace_out.Width = out_len, w_trace
    trace_out.Placement.Base = FreeCAD.Vector(6.0, y_rf - w_trace / 2.0, height)

    # 8. Ground Via Fence North
    via_north = doc.addObject("Part::Box", "ViaFenceNorth")
    via_north.Length, via_north.Width, via_north.Height = length, 0.6, height
    via_north.Placement.Base = FreeCAD.Vector(-half_l, y_rf + via_y - 0.3, 0.0)

    # 9. Ground Via Fence South
    via_south = doc.addObject("Part::Box", "ViaFenceSouth")
    via_south.Length, via_south.Width, via_south.Height = length, 0.6, height
    via_south.Placement.Base = FreeCAD.Vector(-half_l, y_rf - via_y - 0.3, 0.0)

    # 10. M2 Mounting Holes (Corner Standoffs)
    holes = [
        (-14.0, -11.5),
        (14.0, -11.5),
        (-14.0, 11.5),
        (14.0, 11.5)
    ]
    for i, (hx, hy) in enumerate(holes, 1):
        hole = doc.addObject("Part::Cylinder", f"MountingHole_M2_{i}")
        hole.Radius = 1.1 # 2.2 mm drill
        hole.Height = height
        hole.Placement.Base = FreeCAD.Vector(hx, hy, 0.0)

    doc.recompute()

    # =========================================================================
    # Microwave Workbench Setup (Analysis, Materials, Bindings, Ports)
    # =========================================================================
    analysis = createEMAnalysis(doc)
    analysis.Label = "98 MHz FM LNA 3D EM Analysis"
    analysis.FrequencyStart = "10 MHz"
    analysis.FrequencyStop = "500 MHz"
    analysis.NumFrequencyPoints = 491

    solver = solver_of(analysis)
    if solver:
        solver.MaxTimesteps = 25000

    # Materials
    fr4 = createEMMaterial("FR4", doc=doc)
    fr4.Label = "FR4"
    fr4.MaterialType = "Dielectric"
    fr4.Permittivity = 4.5
    fr4.LossTangent = 0.02

    copper = createEMMaterial("Copper", doc=doc)
    copper.Label = "Copper"
    copper.MaterialType = "ConductingSheet"
    copper.Conductivity = 5.8e7
    copper.Thickness = 0.035

    pec_gnd = createEMMaterial("GroundPEC", doc=doc)
    pec_gnd.Label = "GroundPEC"
    pec_gnd.MaterialType = "ConductingSheet"
    pec_gnd.Conductivity = 1e9

    # Material Bindings
    bindings = [
        ("SubstrateBinding", fr4, sub),
        ("BottomGroundBinding", pec_gnd, bot_gnd),
        ("TopGroundNorthBinding", copper, gnd_north),
        ("TopGroundSouthBinding", copper, gnd_south),
        ("InputTraceBinding", copper, trace_in),
        ("OutputTraceBinding", copper, trace_out),
        ("ViaFenceNorthBinding", pec_gnd, via_north),
        ("ViaFenceSouthBinding", pec_gnd, via_south),
    ]

    for bname, bmat, btarget in bindings:
        b = createEMMaterialBinding(bname)
        b.Label = bname
        b.Material = bmat
        b.References = [(btarget, [""])]
        analysis.addObject(b)

    # 4 Ports (Lumped 50-Ohm Ports across Dielectric)
    port_specs = [
        (1, "Port1_SMA_IN", -half_l, y_rf, True),
        (2, "Port2_IN_MATCH", -8.5, y_rf, False),
        (3, "Port3_OUT_MATCH", 6.0, y_rf, False),
        (4, "Port4_SMA_OUT", half_l, y_rf, False),
    ]

    for num, pname, px, py, is_excite in port_specs:
        port = createEMPortLumped(pname, doc=doc)
        port.Label = pname
        port.Number = num
        port.Resistance = 50.0
        port.ReferenceImpedance = 50.0
        port.Excitation = is_excite
        port.ExcitationAxis = "Z"
        port.Placement.Base = FreeCAD.Vector(px, py, 0.0)
        analysis.addObject(port)

    doc.recompute()
    doc.saveAs(out_fcstd)
    print(f"SUCCESS: FreeCAD-Microwave model saved to: {out_fcstd}")
    print(f"Document contains {len(doc.Objects)} objects with full EM Analysis, Materials, and 4 Ports.")
    FreeCAD.closeDocument("lna_fm_98mhz_microwave")
    return out_fcstd

if __name__ == "__main__":
    build_model()
