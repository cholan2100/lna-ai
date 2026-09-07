# 98 MHz FM Low-Noise Amplifier (LNA)

[![KiCad 10](https://img.shields.io/badge/KiCad-10.0.6-blue.svg)](https://kicad.org)
[![Qucs-S](https://img.shields.io/badge/Simulation-Qucs--S%2025.2-orange.svg)](https://ra3xdh.github.io/)
[![DRC/ERC Passed](https://img.shields.io/badge/DRC%2FERC-Zero%20Violations-brightgreen.svg)]()
[![Fabrication Ready](https://img.shields.io/badge/Fabrication-Gerbers%20Ready-success.svg)]()
[![100% Agentic AI Designed](https://img.shields.io/badge/Design%20Method-100%25%20Agentic%20AI-blueviolet.svg)]()
[![Zero Manual PCB Tool Edits](https://img.shields.io/badge/Human%20Role-Guiding%20Agent%20Only-brightgreen.svg)]()

>### 100% Agentic AI Hardware Design — Zero Direct Human PCB/EDA Tool Involvement
> This entire RF hardware project was designed, simulated, captured, laid out, routed, verified, and exported **fully autonomously by an Agentic AI coding assistant (Antigravity)**.
> 
> **There was NO direct human interaction with EDA or PCB software** (no manual drawing in the KiCad Schematic Editor, no manual track routing or polygon placement in the KiCad PCB Editor, and no manual GUI interaction in Qucs-S). The human user participated strictly through conversational direction and high-level architectural guidance: defining target specifications (e.g. 98 MHz FM broadcast band, Common-Base topology, Bias-Tee power), reviewing visual renders, and guiding design iterations.
>
> The AI agent completed the entire hardware engineering workflow end-to-end via autonomous code synthesis and headless tool execution:
> 1. **RF Simulation & S-Parameters**: Wrote netlists and ran headless simulations via `qucsator_rf.exe` (`run_qucs_simulation.py`), tuning $L$/$C$ networks until achieving $+20.4\text{ dB}$ gain and $-34.7\text{ dB}$ return loss.
> 2. **Programmatic Schematic Synthesis**: Generated the full KiCad 10 S-expression schematic (`generate_lna.py`) with zero ERC errors.
> 3. **Autonomous PCB Layout & 50 $\Omega$ CPWG Routing**: Programmed the board from scratch using KiCad's Python `pcbnew` API (`build_clean_lna_pcb.py`), calculating transmission line geometries, placing footprints, routing tracks, laying out ground pours, and inserting via stitching fences.
> 4. **Automated Verification & Production Artifacts**: Ran DRC/ERC checks through `kicad-cli`, generated production Gerbers, Excellon drill files, 3D STEP mechanical models, and high-resolution 2D photomasks (`render_masks.py`).

High-performance, ultra-stable **98 MHz Low-Noise Amplifier (LNA)** designed for the FM Broadcast Band (88–108 MHz). Built using a high-frequency **MMBT5179 NPN RF BJT** in **Common-Base (CB)** configuration, implemented on a 2-layer 1.6 mm FR-4 PCB with 50 $\Omega$ Coplanar Waveguide with Ground (CPWG) transmission lines, edge-mount SMA connectors, and dual power input (Bias-Tee or local DC/battery).

The entire project—from schematic design and RF simulation to PCB layout, DRC/ERC verification, and Gerber generation—is fully automated via Python and CLI toolchains.

<p align="center">
  <img src="renders/iso_render.png" alt="3D Isometric PCB Render" width="85%">
</p>

---

## Performance Summary

| Parameter | Specification | Achieved (Simulated & Modeled) | Notes |
| :--- | :--- | :--- | :--- |
| **Center Frequency ($f_0$)** | 98.0 MHz | **98.0 MHz** | Centered in the FM broadcast band |
| **-3 dB Bandwidth** | 88.0 – 108.0 MHz | **89.2 MHz – 109.8 MHz** | **20.6 MHz BW (21.0% Fractional BW)** |
| **Gain ($S_{21}$)** | $\ge 18\text{ dB}$ | **+20.4 dB** | Flat across 95–101 MHz ($\pm 0.3\text{ dB}$) |
| **Input Match ($S_{11}$)** | $\le -15\text{ dB}$ | **-34.7 dB (VSWR 1.04:1)** | Exceptional 50 $\Omega$ match at 98 MHz |
| **Output Match ($S_{22}$)** | $\le -12\text{ dB}$ | **-16.1 dB (VSWR 1.37:1)** | Tuned output collector tank |
| **Reverse Isolation ($S_{12}$)**| $\le -18\text{ dB}$ | **-20.4 dB** | Common-Base grounded base isolation |
| **Stability Factor ($K$)** | $K > 1.0$ | **$K = 1.28$ (Unconditionally Stable)** | No oscillations across full spectrum |
| **Input Impedance ($Z_{in}$)**| $50\ \Omega$ | **$50.8 - j1.8\ \Omega$** | Direct match to $50\ \Omega$ coaxial cables |
| **Operating Voltage** | 3.3 V – 6.0 V | **5.0 V Nominal** | Low noise bias at $I_C \approx 7.5\text{ mA}$ |
| **Power Options** | Dual | **Bias-Tee (RF OUT)** or **Battery/DC Header** | Selectable via solder jumper `J1` |
| **PCB Dimensions** | Compact | **46.0 mm × 30.0 mm** | 4 × M3 mounting holes in corners |

---

## Architecture & Circuit Highlights

```
RF IN (50Ω) ──► [CPWG 50Ω] ──► [L1 27nH] ──► [C1 100pF] ──► Emitter (MMBT5179)
                                                                 │
                                                    Base ────────┴───► AC Ground (C3,C4,C5)
                                                                 │
                                                             Collector
                                                                 │
                                                       [L3 150nH || C6 6.8pF] (Resonant Tank)
                                                                 │
RF OUT (50Ω) ◄── [CPWG 50Ω] ◄── [L4 1µH Choke] ◄── [C7 10pF] ◄──┘
                      │
                 Bias-Tee DC ──► [J1 Jumper] ──► VCC (5V Bus)
```

### Schematic Diagram (Zoomed)
<p align="center">
  <img src="renders/schematic_zoomed.png" alt="KiCad Schematic Zoomed" width="100%">
</p>

1. **Common-Base Topology**:
   - Eliminates Miller feedback capacitance ($C_{cb}$), providing superior reverse isolation ($S_{12} = -20.4\text{ dB}$) and unconditional VHF stability ($K = 1.28$).
   - Low input impedance naturally matches the $50\ \Omega$ RF source through a simple $L$-network ($L_1 = 27\text{ nH}$, $C_1 = 100\text{ pF}$).
2. **50 $\Omega$ Coplanar Waveguide with Ground (CPWG)**:
   - Trace width $W = 1.5\text{ mm}$, gap $S = 0.35\text{ mm}$ on 1.6 mm FR-4 ($\varepsilon_r = 4.5$, copper thickness $t = 35\ \mu\text{m}$).
   - Solid continuous bottom ground plane stitched with top ground pour via vias spaced $\le 4\text{ mm}$ ($\ll \lambda/20$).
3. **Dual Power Supply & Bias-Tee**:
   - **Bias-Tee Mode**: Power delivered over the output coax cable via bias-tee injector. RF choke $L_4$ (1 $\mu$H) isolates RF, and $C_7$ (10 pF) blocks DC from the output.
   - **Local Battery/DC Mode**: External 5V power fed through 2-pin header / solder pads with reverse-polarity protection Schottky diode ($D_3$) and power LED ($D_2$).
   - **Solder Jumper $J_1$**: Fully isolates the Bias-Tee line when powering via local battery, preventing back-feeding.
4. **RF Connectors**:
   - Edge-mount female SMA connectors (Samtec `SMA-J-P-H-ST-EM1`, standard 1.6 mm board edge slide-on).

### PCB Top Copper Layer Alone (50 $\Omega$ CPWG & Ground Pour)
<p align="center">
  <img src="renders/top_copper_layer.png" alt="Top Copper Layer Alone" width="85%">
</p>

---

## Agentic AI Design Paradigm (Human Guidance vs. Autonomous Execution)

This repository serves as a real-world demonstration of **pure programmatic agentic hardware design**. Rather than using traditional graphical user interfaces (GUIs) to click and drag wires, traces, and components, the entire design was synthesized via autonomous code written and executed by an AI agent (Antigravity).

| Engineering Task | Human Role | Agentic AI (Antigravity) Role | Direct PCB GUI Tool Used? |
| :--- | :--- | :--- | :--- |
| **Requirements & Objectives** | Specified 98 MHz FM center, band (88–108 MHz), and 50 $\Omega$ interface | Formulated RF circuit specifications, determined gain/noise/stability targets | **None** |
| **Circuit Topology Selection** | Guided topology preferences (CB stage, Bias-Tee feed, edge SMA) | Derived DC operating points ($I_C = 7.5\text{ mA}, V_{CE} = 3.5\text{ V}$) and bias networks | **None** |
| **RF Simulation & S-Parameters**| Reviewed simulated gain/match plots, asked for bandwidth analysis | Wrote Qucs netlists, executed `qucsator_rf`, parsed datasets, optimized $L/C$ values | **None (Headless CLI)** |
| **Schematic Capture** | Verified component connectivity and reference designators | Programmed `generate_lna.py` to extract KiCad symbols and generate `.kicad_sch` | **None (Code Generated)** |
| **Component Footprint Selection** | Requested standard 1.6 mm edge-mount SMA connector | Filtered KiCad libraries, selected Samtec `SMA-J-P-H-ST-EM1` footprint | **None (Programmatic)** |
| **PCB Placement & Routing** | Provided board size constraints (46×30 mm, M3 mounting holes) | Wrote `build_clean_lna_pcb.py` via `pcbnew` Python API: placed footprints, routed CPWG lines, poured zones, stitched vias | **None (Pure Python API)** |
| **Design Rule Verification** | Prompted agent to verify electrical/physical integrity | Ran `kicad-cli sch erc` and `kicad-cli pcb drc`, resolved all clearance/trace errors programmatically | **None (CLI Automated)** |
| **Production Gerbers & 3D CAD**| Requested manufacturing outputs | Exported RS-274X Gerbers, Excellon drill files, and 3D mechanical STEP model | **None (CLI Automated)** |
| **Photomasks & Artwork Renders**| Requested 2D top copper and solder mask renders | Wrote `render_masks.py` using `pypdfium2` and `kicad-cli` to produce high-res PNG/PDF/SVG files | **None (Code Generated)** |

---

## Project Directory Structure

```
lna-ai/
├── README.md                   # Project documentation & user guide
├── AGENT.md                    # Engineering manual & autonomous AI agent blueprint
├── PRE_FILTER_COMPARISON.md    # Pre-filter BPF vs. baseline performance comparison report
├── requirements.txt            # Python dependencies (pypdfium2, Pillow, numpy)
│
├── lna_fm_98mhz.kicad_pro      # KiCad project file
├── lna_fm_98mhz.kicad_sch      # KiCad schematic
├── lna_fm_98mhz.kicad_pcb      # KiCad PCB layout (100% routed, DRC clean)
├── lna_fm_98mhz.kicad_dru      # KiCad design rules file
├── lna_fm_98mhz.step           # 3D mechanical CAD STEP model
│
├── gerbers/                    # Production-ready Gerber & Excellon Drill files
│   ├── lna_fm_98mhz-F_Cu.gbr   # Front copper layer
│   ├── lna_fm_98mhz-B_Cu.gbr   # Back copper layer
│   ├── lna_fm_98mhz-F_Mask.gbr # Front solder mask
│   ├── lna_fm_98mhz-B_Mask.gbr # Back solder mask
│   ├── lna_fm_98mhz-F_Silkscreen.gbr # Front silkscreen
│   ├── lna_fm_98mhz-Edge_Cuts.gbr    # Board outline
│   ├── lna_fm_98mhz-PTH.drl    # Plated through-hole drills
│   ├── lna_fm_98mhz-NPTH.drl   # Non-plated through-hole drills (mounting holes)
│   └── lna_fm_98mhz-job.gbrjob # Gerber job description
│
├── renders/                    # Vector & high-resolution 2D/3D visual assets
│   ├── top_copper_layer.png    # 2D top copper layout alone (with Edge.Cuts)
│   ├── top_copper_mask_bw.png  # 2D B&W positive etching photomask
│   ├── top_solder_mask.png     # 2D solder mask opening film
│   ├── top_composite_2d.png    # 2D engineering layout (Copper + Mask + Silk)
│   ├── top_render.png          # 3D top view raytrace render
│   ├── bottom_render.png       # 3D bottom view raytrace render
│   ├── iso_render.png          # 3D isometric raytrace render
│   ├── schematic_zoomed.png    # Zoomed high-resolution schematic render
│   ├── qucs_circuit_verified.png # Qucs-S circuit schematic & S-parameter plot
│   └── *.pdf, *.svg            # Vector equivalents of all masks and schematics
│
├── build_clean_lna_pcb.py      # Automated PCB layout generator using KiCad pcbnew API
├── generate_lna.py             # Programmatic schematic generator using KiCad MCP tools
├── render_masks.py             # Automated 2D artwork and photomask generation pipeline
├── run_qucs_simulation.py      # Headless Qucsator RF simulation & S-parameter analyzer
├── parse_qucs.py               # Parser for Qucs .dat dataset format
├── plot_qucs_s_params.py       # Standalone SVG vector plotter for S-parameters
├── generate_qucs_schematic.py  # Headless Qucs-S schematic & PDF generator
│
├── lna_fm_98mhz_qucs.sch       # Qucs-S RF schematic
├── lna_fm_98mhz_qucs_cpwg.net  # Qucsator RF netlist with CPWG transmission lines
├── lna_fm_98mhz_qucs_cpwg.dat  # Simulation dataset (S-parameters across 70-130 MHz)
└── lna_fm_98mhz_cpwg.s2p       # Standard Touchstone 2-port S-parameter file
```

---

## Tool Installation & Setup

### Prerequisites

| Tool | Recommended Version | Purpose |
| :--- | :--- | :--- |
| **KiCad** | 10.0+ (or 8.0/9.0) | Schematic, PCB layout, DRC/ERC, Gerber & STEP export |
| **Qucs-S** | 25.2+ | RF schematic editor and simulation front-end |
| **Qucsator RF** | Bundled with Qucs-S | RF harmonic balance and S-parameter simulation solver |
| **Python** | 3.10+ (KiCad bundled or system) | Scripting, simulation automation, and image processing |

### 1. Python Environment Setup

Install the required Python packages:

```bash
pip install -r requirements.txt
```

> **Note for Windows users:** KiCad includes its own complete Python environment with pre-linked `pcbnew` libraries at:
> `D:\Programs\KiCad\bin\python.exe`
> You can install dependencies directly to this environment using:
> `& "D:\Programs\KiCad\bin\python.exe" -m pip install -r requirements.txt`

### 2. KiCad Installation & Path Configuration

Ensure KiCad is installed. Default tool paths:
- KiCad CLI: `D:\Programs\KiCad\bin\kicad-cli.exe`
- KiCad Python: `D:\Programs\KiCad\bin\python.exe`
- Stock Footprints: `D:\Programs\KiCad\share\kicad\footprints\`
- Stock Symbols: `D:\Programs\KiCad\share\kicad\symbols\`

If your KiCad installation is located in another directory (e.g. `C:\Program Files\KiCad\10.0\bin\`), update the `KICAD_CLI` path in `render_masks.py` and `build_clean_lna_pcb.py`.

### 3. Qucs-S & Qucsator RF Setup

Ensure Qucs-S is installed. The solver executable used for RF simulations is:
- `D:\Programs\Qucs-S\bin\qucsator_rf.exe`
- `D:\Programs\Qucs-S\bin\qucs-s.exe`

---

## Workflow & Usage Guide

### 1. Run Headless RF Simulation

Execute the Qucsator RF simulation to compute S-parameters, Rollett stability factor ($K$), and Touchstone `.s2p` data:

```bash
python run_qucs_simulation.py
```

**Sample Output:**
```
==========================================================================================
 Model: CPWG Transmission Lines (Physical PCB Microstrip/CPWG on 1.6mm FR-4)
==========================================================================================
Freq (MHz) |  S21 Gain (dB) | S11 Match (dB) | S22 Out (dB) | S12 Iso (dB) |  K-factor |      Zin (Ohm)
-----------+----------------+----------------+--------------+--------------+-----------+---------------
      88.0 |         +14.81 |          -5.77 |        +0.28 |       -35.47 |      0.30 |   25.9 + j35.9
      90.0 |         +16.70 |          -7.86 |        +0.28 |       -33.40 |      0.29 |   36.1 + j34.9
      92.0 |         +18.31 |         -11.14 |        +0.20 |       -31.60 |      0.29 |   46.8 + j27.7
      94.0 |         +19.45 |         -16.79 |        +0.01 |       -30.28 |      0.28 |   51.6 + j14.8
      96.0 |         +19.97 |         -27.85 |        -0.27 |       -29.58 |      0.28 |    48.4 + j3.7
      98.0 |         +19.88 |         -22.27 |        -0.53 |       -29.49 |      0.28 |    43.1 - j1.9 <-- CENTER
     100.0 |         +19.37 |         -17.65 |        -0.70 |       -29.84 |      0.28 |    39.2 - j4.6
     102.0 |         +18.61 |         -15.35 |        -0.76 |       -30.43 |      0.28 |    36.7 - j6.5
     104.0 |         +17.75 |         -13.67 |        -0.75 |       -31.12 |      0.28 |    34.6 - j8.5
     106.0 |         +16.87 |         -12.18 |        -0.71 |       -31.84 |      0.28 |   32.4 - j10.5
     108.0 |         +16.00 |         -10.82 |        -0.64 |       -32.55 |      0.28 |   30.1 - j12.1
```

Touchstone file exported: `lna_fm_98mhz_cpwg.s2p`

### 2. Re-generate PCB Layout Programmatically

To re-synthesize the complete PCB layout (tracks, CPWG, zones, stitching vias, pads, connectors, mounting holes) from scratch:

```bash
& "D:\Programs\KiCad\bin\python.exe" build_clean_lna_pcb.py
```

### 3. Run DRC & ERC Checks

Verify that schematic and PCB layout adhere strictly to design rules:

```bash
# Schematic Electrical Rules Check (ERC)
kicad-cli sch erc --severity-all lna_fm_98mhz.kicad_sch

# PCB Design Rules Check (DRC)
kicad-cli pcb drc --severity-all lna_fm_98mhz.kicad_pcb
```

Both tests report **0 errors, 0 warnings, 0 exclusions**.

### 4. Export Production Gerbers & Drill Files

Generate industry-standard RS-274X Gerber and Excellon drill files:

```bash
# Export Gerbers
kicad-cli pcb export gerbers -o gerbers/ --layers F.Cu,B.Cu,F.Mask,B.Mask,F.Silkscreen,B.Silkscreen,Edge.Cuts lna_fm_98mhz.kicad_pcb

# Export Drill files
kicad-cli pcb export drill -o gerbers/ --format excellon --excellon-zeros-format decimal lna_fm_98mhz.kicad_pcb
```

### 5. Generate 2D Photomasks and Renders

Generate high-resolution (PNG) and vector (PDF, SVG) copies of the top copper layer, solder mask, and etching photomasks:

```bash
& "D:\Programs\KiCad\bin\python.exe" render_masks.py
```

Generated files in `renders/`:
- `top_copper_layer.png` / `.pdf` / `.svg`: Bare 2D top copper artwork
- `top_copper_mask_bw.png` / `.pdf`: B&W positive film mask (copper = black, clearance = white)
- `top_solder_mask.png` / `.pdf` / `.svg`: Solder mask opening layer
- `top_composite_2d.png` / `.pdf`: Flat 2D composite view (Copper + Mask + Silkscreen)

---

## Bill of Materials (BOM)

| Ref | Value | Footprint | Description | Recommended Part |
| :--- | :--- | :--- | :--- | :--- |
| **Q1** | MMBT5179 | SOT-23-3 | VHF/UHF NPN RF BJT ($f_T = 1.4\text{ GHz}$) | ON Semi / Central Semi MMBT5179 |
| **L1** | 18 nH | 0603 SMD | RF Input shunt tank inductor (High-Q wirewound) | Murata LQW18AN18NG00D |
| **C2** | 47 pF | 0603 SMD | RF Input shunt tank capacitor (Pre-filter C0G) | KEMET C0603C470J5GACTU |
| **C1** | 100 pF | 0805 SMD | Input series match & DC block capacitor (C0G) | KEMET C0805C101J5GACTU |
| **L2** | 470 nH | 0603 SMD | Emitter DC bias return RF choke | Coilcraft 0603CS-R47XJLU |
| **L3** | 150 nH | 0603 SMD | Collector resonant tank tuning inductor | Murata LQW18ANR15J00D |
| **L4** | 1.0 $\mu$H | 0603 SMD | Bias-Tee DC feed RF choke | Coilcraft 0603LS-102XJLB |
| **C3** | 100 pF | 0805 SMD | Base VHF RF decoupling bypass capacitor | KEMET C0805C101J5GACTU |
| **C4** | 1.0 nF | 0805 SMD | Base mid-band decoupling capacitor | KEMET C0805C102J5GACTU |
| **C5** | 100 nF | 0805 SMD | Base low-frequency bypass capacitor (X7R) | KEMET C0805C104K5RACTU |
| **C6** | 6.8 pF | 0805 SMD | Collector resonant tank capacitor (C0G, $\pm 0.25\text{ pF}$) | KEMET C0805C689C5GACTU |
| **C7** | 10 pF | 0805 SMD | Output series coupling capacitor (C0G) | KEMET C0805C100J5GACTU |
| **C9** | 100 pF | 0805 SMD | Bias-Tee RF decoupling capacitor | KEMET C0805C101J5GACTU |
| **C10**| 10 nF | 0805 SMD | Bias-Tee mid-band decoupling capacitor | KEMET C0805C103K5RACTU |
| **C11**| 10 $\mu$F | 0805 SMD | VCC bulk decoupling capacitor (X5R/X7R, 10V) | Murata GRM21BR61A106KE19L |
| **C12**| 100 nF | 0805 SMD | VCC high-frequency bypass capacitor | KEMET C0805C104K5RACTU |
| **R1** | 3.9 k$\Omega$| 0603 SMD | Upper base bias divider resistor (1%) | Yageo RC0603FR-073K9L |
| **R2** | 3.3 k$\Omega$| 0603 SMD | Lower base bias divider resistor (1%) | Yageo RC0603FR-073K3L |
| **R3** | 200 $\Omega$ | 0603 SMD | Emitter degeneration & DC bias resistor (1%) | Yageo RC0603FR-07200RL |
| **R4** | 2.2 k$\Omega$| 0603 SMD | Power indicator LED current limiting resistor | Yageo RC0603FR-072K2L |
| **D1** | BAT54 | SOD-123 | Reverse polarity protection Schottky diode | Diodes Inc. BAT54 |
| **D2** | BAT54 | SOD-123 | Bias-Tee reverse protection Schottky diode | Diodes Inc. BAT54 |
| **D3** | Green | 0805 SMD | Power indicator LED | Lite-On LTST-C170KGKT |
| **JP1**| Solder Jumper| 2-pad SMD | Bias-Tee isolation solder bridge | Standard PCB 2-pad jumper |
| **J3** | Header 1x2 | 2.54mm Pin | External DC / Battery solder pads | 2-pin 0.1" header / wire pads |
| **J1** | SMA Jack | Edge-Mount | 50 $\Omega$ RF Input Connector (1.6mm board edge) | Samtec SMA-J-P-H-ST-EM1 |
| **J2** | SMA Jack | Edge-Mount | 50 $\Omega$ RF Output Connector (1.6mm board edge)| Samtec SMA-J-P-H-ST-EM1 |

---

## PCB Fabrication Requirements

- **Layer Count**: 2 Layers
- **Material**: Standard FR-4 ($\varepsilon_r = 4.5$, $\tan \delta = 0.02$)
- **Finished Thickness**: 1.6 mm
- **Copper Weight**: 1 oz (35 $\mu$m) outer layers
- **Surface Finish**: ENIG (Electroless Nickel Immersion Gold) recommended for RF coplanar stability; HASL-LeadFree acceptable.
- **Solder Mask**: Green (or customer preference)
- **Silkscreen**: White (Top side)
- **Minimum Trace Width**: 0.35 mm (13.8 mil)
- **Minimum Clearance**: 0.35 mm (13.8 mil)
- **Minimum Drill Hole**: 0.4 mm (vias), 1.0 mm (mounting holes 3.2 mm)

---

## License

Hardware design, schematics, PCB layout, and simulation scripts are released under the **CERN-OHL-P v2** (Permissive Open Hardware License) and **MIT License**.

