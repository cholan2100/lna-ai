import os
import subprocess
import pypdfium2 as pdfium
from PIL import Image, ImageChops

def generate_schematic():
    comps = []
    wires = []

    header = [
        "<Qucs Schematic 25.2.0>",
        "<Properties>",
        "  <View=-50,-80,1200,800,1,0,0>",
        "  <Grid=10,10,1>",
        "  <DataSet=lna_fm_98mhz_qucs.dat>",
        "  <DataDisplay=lna_fm_98mhz_qucs.dpl>",
        "  <OpenDisplay=1>",
        "  <Script=>",
        "  <RunScript=0>",
        "  <showFrame=0>",
        "  <FrameText0=Title>",
        "  <FrameText1=Drawn By:>",
        "  <FrameText2=Date:>",
        "  <FrameText3=Revision:>",
        "</Properties>",
        "<Symbol>",
        "</Symbol>",
        "<Components>"
    ]

    # Substrate
    comps.append('<SUBST Subst1 1 80 520 -30 24 0 0 "4.5" 1 "1.6 mm" 1 "35 um" 1 "0.02" 1 "1.72e-08" 0 "1.5e-07" 0>')

    # =========================================================================
    # 1. RF INPUT PATH (y = 260)
    # =========================================================================
    # Pac P1: cx=40, cy=290 (rot=0, mir=1). Top: (40, 260), Bot: (40, 320)
    comps.append('<Pac P1 1 40 290 -85 -20 0 1 "1" 1 "50 Ohm" 1 "0 dBm" 0 "98 MHz" 0 "26.85" 0 "true" 0>')
    comps.append('<GND * 1 40 320 0 0 0 0>')
    wires.append('<40 260 70 260 "" 0 0 0 "">')

    # CLIN TL_IN (8.5mm): cx=100, cy=260. Ports: (70, 260), (130, 260). Text placed well ABOVE (ty=-105)
    comps.append('<CLIN TL_IN 1 100 260 -26 -105 0 0 "Subst1" 0 "1.5 mm" 1 "0.35 mm" 1 "8.5 mm" 1 "Metal" 0 "no" 0>')
    wires.append('<130 260 180 260 "" 0 0 0 "">')

    # Node (180, 260): Shunt LC Tank BPF (L1 18nH || C2 47pF to GND)
    # L1: cx=180, cy=290. Top: (180, 260), Bot: (180, 320)
    comps.append('<L L1 1 180 290 -35 -26 0 1 "18 nH" 1 "" 0>')
    comps.append('<GND * 1 180 320 0 0 0 0>')

    # C2: cx=210, cy=290. Top: (210, 260), Bot: (210, 320)
    wires.append('<180 260 210 260 "" 0 0 0 "">')
    comps.append('<C C2 1 210 290 15 -26 0 1 "47 pF" 1 "" 0 "neutral" 0>')
    comps.append('<GND * 1 210 320 0 0 0 0>')

    # Series C1 (100pF): cx=260, cy=260. Ports: (230, 260), (290, 260). Text placed well ABOVE (ty=-55)
    wires.append('<210 260 230 260 "" 0 0 0 "">')
    comps.append('<C C1 1 260 260 -25 -55 0 0 "100 pF" 1 "" 0 "neutral" 0>')

    # From C1 (290, 260) to Emitter Choke Node (360, 260)
    wires.append('<290 260 360 260 "" 0 0 0 "">')

    # =========================================================================
    # 2. EMITTER NODE (360, 260)
    # =========================================================================
    # Emitter Choke L2 (470nH): cx=360, cy=290. Top: (360, 260), Bot: (360, 320)
    comps.append('<L L2 1 360 290 15 -26 0 1 "470 nH" 1 "" 0>')

    # Emitter Resistor R3 (200 Ohm): cx=360, cy=350. Top: (360, 320), Bot: (360, 380)
    comps.append('<R R3 1 360 350 15 -26 0 1 "200 Ohm" 1 "26.85" 0 "0.0" 0 "0.0" 0 "26.85" 0 "european" 0>')
    comps.append('<GND * 1 360 380 0 0 0 0>')

    # Connect Emitter Node (360, 260) directly to Q1 Emitter pin at (540, 260)
    wires.append('<360 260 540 260 "" 0 0 0 "">')

    # =========================================================================
    # 3. TRANSISTOR Q1 (MMBT5179): cx=540, cy=230, rot=0, mir=0
    # Base: (510, 230), Collector: (540, 200), Emitter: (540, 260)
    # =========================================================================
    bjt_props = '"npn" 0 "1e-14" 0 "1" 0 "1" 0 "0.1" 0 "0.01" 0 "50" 0 "10" 0 "1e-14" 0 "1.5" 0 "0" 0 "2" 0 "90" 0 "2" 0 "0" 0 "0" 0 "10" 0 "1" 0 "5" 0 "1.2e-12" 0 "0.7" 0 "0.33" 0 "1e-12" 0 "0.5" 0 "0.33" 0 "1" 0 "0" 0 "0.75" 0 "0.33" 0 "0.5" 0 "0.09e-9" 0 "10e-9" 0 "10" 0 "1" 0 "0.1" 0'
    comps.append(f'<_BJT Q1 1 540 230 15 10 0 0 {bjt_props}>')

    # =========================================================================
    # 4. BASE BIAS & RF BYPASS NETWORK
    # =========================================================================
    # Base pin is at (510, 230) -> wire straight up to Base rail at (510, 140)
    wires.append('<510 140 510 230 "" 0 0 0 "">')

    # Base rail segmented between every pin: cx=180, 260, 340, 420, 470, 510
    wires.append('<180 140 260 140 "" 0 0 0 "">')
    wires.append('<260 140 340 140 "" 0 0 0 "">')
    wires.append('<340 140 420 140 "" 0 0 0 "">')
    wires.append('<420 140 470 140 "" 0 0 0 "">')
    wires.append('<470 140 510 140 "" 0 0 0 "">')

    # Base Bypass Capacitors C3, C4, C5 (cx=180, 260, 340, cy=170)
    comps.append('<C C3 1 180 170 12 -15 0 1 "100 pF" 1 "" 0 "neutral" 0>')
    comps.append('<GND * 1 180 200 0 0 0 0>')

    comps.append('<C C4 1 260 170 12 -15 0 1 "1 nF" 1 "" 0 "neutral" 0>')
    comps.append('<GND * 1 260 200 0 0 0 0>')

    comps.append('<C C5 1 340 170 12 -15 0 1 "100 nF" 1 "" 0 "neutral" 0>')
    comps.append('<GND * 1 340 200 0 0 0 0>')

    # R2 (3.3 kOhm): Top (420, 140), Bot (420, 200) to GND
    comps.append('<R R2 1 420 170 15 -15 0 1 "3.3 kOhm" 1 "26.85" 0 "0.0" 0 "0.0" 0 "26.85" 0 "european" 0>')
    comps.append('<GND * 1 420 200 0 0 0 0>')

    # R1 (3.9 kOhm): cx=470, cy=105. Top: (470, 70), Bot: (470, 140)
    wires.append('<470 70 470 75 "" 0 0 0 "">')
    comps.append('<R R1 1 470 105 15 -26 0 1 "3.9 kOhm" 1 "26.85" 0 "0.0" 0 "0.0" 0 "26.85" 0 "european" 0>')
    wires.append('<470 135 470 140 "" 0 0 0 "">')

    # =========================================================================
    # VCC POWER SUPPLY & DECOUPLING (y = 70)
    # =========================================================================
    # Vdc VCC: cx=80, cy=100. Top: (80, 70), Bot: (80, 130) to GND
    comps.append('<Vdc VCC 1 80 100 -75 -20 0 1 "5 V" 1>')
    comps.append('<GND * 1 80 130 0 0 0 0>')

    # VCC Decoupling Capacitors C11 (10uF) and C12 (100nF)
    comps.append('<C C11 1 150 100 15 -20 0 1 "10 uF" 1 "" 0 "neutral" 0>')
    comps.append('<GND * 1 150 130 0 0 0 0>')

    comps.append('<C C12 1 240 100 15 -20 0 1 "100 nF" 1 "" 0 "neutral" 0>')
    comps.append('<GND * 1 240 130 0 0 0 0>')

    # VCC rail explicitly segmented between every single connected node:
    wires.append('<80 70 150 70 "" 0 0 0 "">')   # VCC to C11
    wires.append('<150 70 240 70 "" 0 0 0 "">')  # C11 to C12
    wires.append('<240 70 470 70 "" 0 0 0 "">')  # C12 to R1
    wires.append('<470 70 700 70 "" 0 0 0 "">')  # R1 to L3

    # =========================================================================
    # 5. COLLECTOR NODE & INTERCONNECT (y = 200)
    # =========================================================================
    # Q1 Collector pin at (540, 200) -> TL_COL left port at (570, 200)
    wires.append('<540 200 570 200 "" 0 0 0 "">')

    # CLIN TL_COL (6.6mm): cx=600, cy=200. Ports: (570, 200), (630, 200). Text ABOVE (ty=-105)
    comps.append('<CLIN TL_COL 1 600 200 -26 -105 0 0 "Subst1" 0 "1.0 mm" 1 "0.35 mm" 1 "6.6 mm" 1 "Metal" 0 "no" 0>')
    wires.append('<630 200 700 200 "" 0 0 0 "">')

    # =========================================================================
    # 6. COLLECTOR TUNED TANK (Node 700, 200)
    # =========================================================================
    # L3 (150nH): cx=700, cy=135. Top: (700, 105), Bot: (700, 165). Text on RIGHT (tx=15)
    wires.append('<700 70 700 105 "" 0 0 0 "">')
    comps.append('<L L3 1 700 135 15 -20 0 1 "150 nH" 1 "" 0>')
    wires.append('<700 165 700 200 "" 0 0 0 "">')

    # C6 (6.8pF): cx=700, cy=230. Top: (700, 200), Bot: (700, 260) to GND. Text on LEFT (tx=-65)
    comps.append('<C C6 1 700 230 -65 -15 0 1 "6.8 pF" 1 "" 0 "neutral" 0>')
    comps.append('<GND * 1 700 260 0 0 0 0>')

    # Series C7 (10pF): cx=780, cy=200. Ports: (750, 200), (810, 200). Text BELOW (ty=25)
    wires.append('<700 200 750 200 "" 0 0 0 "">')
    comps.append('<C C7 1 780 200 -25 25 0 0 "10 pF" 1 "" 0 "neutral" 0>')

    # =========================================================================
    # 7. OUTPUT CPWG SEGMENT 1 & BIAS-TEE
    # =========================================================================
    wires.append('<810 200 840 200 "" 0 0 0 "">')
    # TL_OUT1: cx=870, cy=200. Ports: (840, 200), (900, 200). Text placed ABOVE (ty=-105)
    comps.append('<CLIN TL_OUT1 1 870 200 -26 -105 0 0 "Subst1" 0 "1.5 mm" 1 "0.35 mm" 1 "9.55 mm" 1 "Metal" 0 "no" 0>')
    wires.append('<900 200 950 200 "" 0 0 0 "">')

    # Bias-Tee Choke L4 (1uH): cx=950, cy=235. Top: (950, 205), Bot: (950, 265). Text on RIGHT (tx=15)
    wires.append('<950 200 950 205 "" 0 0 0 "">')
    comps.append('<L L4 1 950 235 15 -20 0 1 "1 uH" 1 "" 0>')
    wires.append('<950 265 950 300 "" 0 0 0 "">')

    # Bias-Tee DC bus explicitly segmented at y = 300:
    wires.append('<950 300 1020 300 "" 0 0 0 "">')  # L4 to C9
    wires.append('<1020 300 1100 300 "" 0 0 0 "">') # C9 to C10
    wires.append('<1100 300 1180 300 "" 0 0 0 "">') # C10 to Rbt

    # C9 (100pF): cx=1020, cy=330. Top: (1020, 300), Bot: (1020, 360) to GND. Text RIGHT (tx=15)
    comps.append('<C C9 1 1020 330 15 -15 0 1 "100 pF" 1 "" 0 "neutral" 0>')
    comps.append('<GND * 1 1020 360 0 0 0 0>')

    # C10 (10nF): cx=1100, cy=330. Top: (1100, 300), Bot: (1100, 360) to GND. Text RIGHT (tx=15)
    comps.append('<C C10 1 1100 330 15 -15 0 1 "10 nF" 1 "" 0 "neutral" 0>')
    comps.append('<GND * 1 1100 360 0 0 0 0>')

    # Rbt (100kOhm): cx=1180, cy=330. Top: (1180, 300), Bot: (1180, 360) to GND. Text RIGHT (tx=15)
    comps.append('<R Rbt 1 1180 330 15 -15 0 1 "100 kOhm" 1 "26.85" 0 "0.0" 0 "0.0" 0 "26.85" 0 "european" 0>')
    comps.append('<GND * 1 1180 360 0 0 0 0>')

    # =========================================================================
    # 8. OUTPUT CPWG SEGMENT 2 & PORT P2
    # =========================================================================
    wires.append('<950 200 990 200 "" 0 0 0 "">')
    # TL_OUT2: cx=1020, cy=200. Ports: (990, 200), (1050, 200). Text placed ABOVE (ty=-105)
    comps.append('<CLIN TL_OUT2 1 1020 200 -26 -105 0 0 "Subst1" 0 "1.5 mm" 1 "0.35 mm" 1 "10.0 mm" 1 "Metal" 0 "no" 0>')
    wires.append('<1050 200 1100 200 "" 0 0 0 "">')

    # Pac P2: cx=1100, cy=230 (rot=0, mir=1). Top: (1100, 200), Bot: (1100, 260)
    comps.append('<Pac P2 1 1100 230 25 -20 0 1 "2" 1 "50 Ohm" 1 "0 dBm" 0 "98 MHz" 0 "26.85" 0 "true" 0>')
    comps.append('<GND * 1 1100 260 0 0 0 0>')

    # =========================================================================
    # 9. SIMULATION CONTROLS
    # =========================================================================
    comps.append('<.DC DC1 1 300 520 0 38 0 0 "26.85" 0 "0.001" 0 "1 pA" 0 "1 uV" 0 "no" 0 "150" 0 "no" 0 "none" 0 "CroutLU" 0>')
    comps.append('<.SP SP1 1 460 520 0 56 0 0 "lin" 1 "70 MHz" 1 "130 MHz" 1 "61" 1 "no" 0 "1" 0 "2" 0 "no" 0 "no" 0>')
    comps.append('<Eqn Eqn1 1 660 520 -28 15 0 0 "S11_dB=dB(S[1,1])" 1 "S21_dB=dB(S[2,1])" 1 "S12_dB=dB(S[1,2])" 1 "S22_dB=dB(S[2,2])" 1 "yes" 0>')

    content = header + comps + ["</Components>", "<Wires>"] + wires + ["</Wires>"]
    content.append("<Diagrams>")
    # Embed Cartesian S-parameter plot directly on the right side
    content.append('  <Rect 1260 120 400 320 3 #c0c0c0 1 00 1 7e+07 1e+07 1.3e+08 0 -40 10 30 1 -1 0.5 1 315 0 225 1 0 0 "Frequency [Hz]" "dB" "">')
    content.append('    <"S21_dB" #ff0000 0 3 0 0 0>')
    content.append('    <"S11_dB" #0000ff 0 3 0 0 0>')
    content.append('  </Rect>')
    content.append("</Diagrams>")
    content.append("<Paintings>")
    content.append('  <Text 40 -30 14 #000000 0 "Common-Base 98 MHz FM LNA - S-Parameter Simulation with CPWG Traces">')
    content.append('  <Text 40 -55 11 #0000ff 0 "LionCircuits 1.6mm FR-4: W=1.5mm, S=0.35mm (Z0=50 Ohm CPWG) | MMBT5179 CB Stage">')
    content.append("</Paintings>")

    return "\n".join(content) + "\n"

if __name__ == "__main__":
    sch_path = r"D:\Workspace\rf\lna-ai\lna_fm_98mhz_qucs.sch"
    pdf_path = r"D:\Workspace\rf\lna-ai\renders\qucs_circuit.pdf"
    png_path = r"D:\Workspace\rf\lna-ai\renders\qucs_circuit_verified.png"

    sch_data = generate_schematic()
    with open(sch_path, "w") as f:
        f.write(sch_data)
    print("Updated schematic written to:", sch_path)

    # Run qucs-s print to PDF
    cmd = [
        r"D:\Programs\Qucs-S\bin\qucs-s.exe",
        "-p",
        "-i", sch_path,
        "-o", pdf_path,
        "--orin", "landscape",
        "--color", "RGB",
        "--page", "A4"
    ]
    subprocess.run(cmd, check=True)
    print("Printed PDF successfully!")

    # Render PDF with pdfium at 4x scale (ultra crisp high-DPI)
    doc = pdfium.PdfDocument(pdf_path)
    img = doc[0].render(scale=4).to_pil()

    # Smart crop with clean margins
    bg = Image.new(img.mode, img.size, (255, 255, 255))
    diff = ImageChops.difference(img, bg)
    bbox = diff.getbbox()
    if bbox:
        pad = 60
        crop_box = (
            max(0, bbox[0] - pad),
            max(0, bbox[1] - pad),
            min(img.width, bbox[2] + pad),
            min(img.height, bbox[3] + pad)
        )
        img = img.crop(crop_box)

    img.save(png_path)
    print(f"High-res PNG saved to {png_path}, size: {img.size}")
