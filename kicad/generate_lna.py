import sys
import uuid
from pathlib import Path

# Add kicad_mcp_server to path
sys.path.insert(0, r'D:\Programs\kicad-mcp-server\src')
from kicad_mcp_server.tools.schematic_editor import (
    _find_symbol_library_file,
    _extract_symbol_from_kicad_sym,
    _convert_symbol_to_lib_symbols_format,
)

def u():
    return str(uuid.uuid4())

def build_schematic(output_path: Path):
    needed_symbols = [
        ('Connector', 'Conn_Coaxial'),
        ('Device', 'C'),
        ('Device', 'L'),
        ('Device', 'R'),
        ('Device', 'LED'),
        ('Device', 'D_Schottky'),
        ('Transistor_BJT', 'Q_NPN_BEC'),
        ('Connector_Generic', 'Conn_01x02'),
        ('Jumper', 'SolderJumper_2_Open'),
        ('power', 'VCC'),
        ('power', 'GND'),
        ('power', 'PWR_FLAG'),
    ]

    lib_sym_blocks = []
    for lib, sym in needed_symbols:
        p = _find_symbol_library_file(lib)
        if not p:
            raise FileNotFoundError(f'Cannot find library {lib}')
        block = _extract_symbol_from_kicad_sym(p, sym)
        if not block:
            raise ValueError(f'Cannot find symbol {sym} in {lib}')
        conv = _convert_symbol_to_lib_symbols_format(block, lib, sym)
        lib_sym_blocks.append(conv)

    lib_symbols_str = '\n'.join(lib_sym_blocks)

    components = []
    wires = []
    labels = []
    power_symbols = []
    junctions = []

    def add_wire(x1, y1, x2, y2):
        wires.append(f'''\t(wire
\t\t(pts
\t\t\t(xy {x1:.2f} {y1:.2f}) (xy {x2:.2f} {y2:.2f})
\t\t)
\t\t(stroke
\t\t\t(width 0)
\t\t\t(type solid)
\t\t)
\t\t(uuid \x22{u()}\x22)
\t)''')

    def add_junction(x, y):
        junctions.append(f'''\t(junction (at {x:.2f} {y:.2f}) (diameter 0) (color 0 0 0 0) (uuid \x22{u()}\x22))''')

    def add_label(text, x, y, angle=0):
        justify = 'left' if angle in [0, 90] else 'right'
        labels.append(f'''\t(label \x22{text}\x22
\t\t(at {x:.2f} {y:.2f} {angle})
\t\t(fields_autoplaced yes)
\t\t(effects
\t\t\t(font
\t\t\t\t(size 1.27 1.27)
\t\t\t)
\t\t\t(justify {justify} bottom)
\t\t)
\t\t(uuid \x22{u()}\x22)
\t)''')

    def add_pwr(lib_id, x, y, angle=0):
        val = lib_id.split(':')[1]
        ref = f'#{val}_{len(power_symbols)+1}'
        power_symbols.append(f'''\t(symbol
\t\t(lib_id \x22{lib_id}\x22)
\t\t(at {x:.2f} {y:.2f} {angle})
\t\t(unit 1)
\t\t(exclude_from_sim no)
\t\t(in_bom yes)
\t\t(on_board yes)
\t\t(dnp no)
\t\t(uuid \x22{u()}\x22)
\t\t(property \x22Reference\x22 \x22{ref}\x22
\t\t\t(at {x:.2f} {y-2.54:.2f} 0)
\t\t\t(effects
\t\t\t\t(font (size 1.27 1.27))
\t\t\t\t(hide yes)
\t\t\t)
\t\t)
\t\t(property \x22Value\x22 \x22{val}\x22
\t\t\t(at {x:.2f} {y+2.54:.2f} 0)
\t\t\t(effects
\t\t\t\t(font (size 1.27 1.27))
\t\t\t)
\t\t)
\t\t(property \x22Footprint\x22 \x22\x22
\t\t\t(at {x:.2f} {y:.2f} 0)
\t\t\t(effects
\t\t\t\t(font (size 1.27 1.27))
\t\t\t\t(hide yes)
\t\t\t)
\t\t)
\t\t(pin \x221\x22 (uuid \x22{u()}\x22))
\t\t(instances
\t\t\t(project \x22lna_fm_98mhz\x22
\t\t\t\t(path \x22/\x22
\t\t\t\t\t(reference \x22{ref}\x22)
\t\t\t\t\t(unit 1)
\t\t\t\t)
\t\t\t)
\t\t)
\t)''')

    def add_comp(ref, val, lib_id, footprint, x, y, angle, pin_count):
        pins_str = '\n'.join([f'\t\t(pin \x22{i+1}\x22 (uuid \x22{u()}\x22))' for i in range(pin_count)])
        components.append(f'''\t(symbol
\t\t(lib_id \x22{lib_id}\x22)
\t\t(at {x:.2f} {y:.2f} {angle})
\t\t(unit 1)
\t\t(exclude_from_sim no)
\t\t(in_bom yes)
\t\t(on_board yes)
\t\t(dnp no)
\t\t(uuid \x22{u()}\x22)
\t\t(property \x22Reference\x22 \x22{ref}\x22
\t\t\t(at {x+2.54:.2f} {y-2.54:.2f} 0)
\t\t\t(effects
\t\t\t\t(font (size 1.27 1.27))
\t\t\t)
\t\t)
\t\t(property \x22Value\x22 \x22{val}\x22
\t\t\t(at {x+2.54:.2f} {y+2.54:.2f} 0)
\t\t\t(effects
\t\t\t\t(font (size 1.27 1.27))
\t\t\t)
\t\t)
\t\t(property \x22Footprint\x22 \x22{footprint}\x22
\t\t\t(at {x:.2f} {y:.2f} 0)
\t\t\t(effects
\t\t\t\t(font (size 1.27 1.27))
\t\t\t\t(hide yes)
\t\t\t)
\t\t)
{pins_str}
\t\t(instances
\t\t\t(project \x22lna_fm_98mhz\x22
\t\t\t\t(path \x22/\x22
\t\t\t\t\t(reference \x22{ref}\x22)
\t\t\t\t\t(unit 1)
\t\t\t\t)
\t\t\t)
\t\t)
\t)''')

    # 1. RF INPUT SECTION (Merged BPF & Match: Shunt LC Tank L1 || C2 + Series Capacitor C1)
    # J1 at (35.56, 60.96): Pin 1 (30.48, 60.96), Pin 2 (35.56, 66.04)
    add_comp('J1', 'SMA_50R_IN', 'Connector:Conn_Coaxial', 'Connector_Coaxial:SMA_Samtec_SMA-J-P-H-ST-EM1_EdgeMount', 35.56, 60.96, 0, 2)
    add_wire(35.56, 66.04, 35.56, 68.58)
    add_pwr('power:GND', 35.56, 68.58)

    # Wire from J1 to L1 tank junction at (45.72, 60.96)
    add_wire(30.48, 60.96, 45.72, 60.96)
    add_label('RF_IN_50R', 33.02, 60.96)
    add_junction(45.72, 60.96)

    # L1 (22nH shunt tank inductor to GND, 0603 wirewound) at (45.72, 68.58), angle 180:
    # Pin 1 at (45.72, 64.77), Pin 2 at (45.72, 72.39)
    add_comp('L1', '22nH', 'Device:L', 'Inductor_SMD:L_0603_1608Metric', 45.72, 68.58, 180, 2)
    add_wire(45.72, 60.96, 45.72, 64.77)
    add_wire(45.72, 72.39, 45.72, 74.93)
    add_pwr('power:GND', 45.72, 74.93)

    # C2 (27pF shunt tank capacitor to GND, 0603 C0G) at (53.34, 68.58), angle 180:
    # Pin 1 at (53.34, 64.77), Pin 2 at (53.34, 72.39)
    add_wire(45.72, 60.96, 53.34, 60.96)
    add_junction(53.34, 60.96)
    add_comp('C2', '27pF', 'Device:C', 'Capacitor_SMD:C_0603_1608Metric', 53.34, 68.58, 180, 2)
    add_wire(53.34, 60.96, 53.34, 64.77)
    add_wire(53.34, 72.39, 53.34, 74.93)
    add_pwr('power:GND', 53.34, 74.93)

    # C1 (91pF series match & DC block, 0805) at (63.50, 60.96), angle 90:
    # Pin 1 at (59.69, 60.96), Pin 2 at (67.31, 60.96)
    add_wire(53.34, 60.96, 59.69, 60.96)
    add_comp('C1', '91pF', 'Device:C', 'Capacitor_SMD:C_0805_2012Metric', 63.50, 60.96, 90, 2)
    # Wire from C1 Pin 2 to Emitter Node
    add_wire(67.31, 60.96, 76.20, 60.96)
    add_junction(76.20, 60.96)
    add_label('EMITTER', 76.20, 60.96)

    # 2. TRANSISTOR MMBT5179 (Q1)
    # Q1 at (91.44, 66.04), angle 0
    # Pin 1 (Base) is at (91.44 - 5.08, 66.04) = (86.36, 66.04)
    # Pin 2 (Emitter) is at (91.44 + 2.54, 66.04 - 5.08) = (93.98, 60.96)
    # Pin 3 (Collector) is at (91.44 + 2.54, 66.04 + 5.08) = (93.98, 71.12)
    add_comp('Q1', 'MMBT5179', 'Transistor_BJT:Q_NPN_BEC', 'Package_TO_SOT_SMD:SOT-23', 91.44, 66.04, 0, 3)
    # Wire from Emitter node (76.20, 60.96) to Q1 Pin 2 (93.98, 60.96)
    add_wire(76.20, 60.96, 93.98, 60.96)

    # Emitter Bias Choke L2 (470nH) + R3 (200R) down to GND:
    # At x = 76.20, drop down to L2:
    add_wire(76.20, 60.96, 76.20, 74.93)
    add_comp('L2', '470nH', 'Device:L', 'Inductor_SMD:L_0603_1608Metric', 76.20, 78.74, 180, 2)
    add_wire(76.20, 82.55, 76.20, 87.63)
    add_comp('R3', '200R', 'Device:R', 'Resistor_SMD:R_0603_1608Metric', 76.20, 91.44, 180, 2)
    add_wire(76.20, 95.25, 76.20, 97.79)
    add_pwr('power:GND', 76.20, 97.79)

    # 3. BASE BIAS & RF GROUNDING (Elevated above RF input to eliminate overlap)
    # Q1 Pin 1 (Base) is at (86.36, 66.04)
    # Wire from Q1 Base up to y=35.56 and left across base components:
    add_wire(86.36, 66.04, 86.36, 35.56)
    add_wire(86.36, 35.56, 40.64, 35.56)
    add_junction(86.36, 35.56)
    add_label('BASE', 86.36, 35.56)

    # Base bias pull-up R1 (3.9k) to VCC (upwards to y=19.05):
    add_junction(40.64, 35.56)
    add_wire(40.64, 35.56, 40.64, 29.21)
    add_comp('R1', '3.9k', 'Device:R', 'Resistor_SMD:R_0603_1608Metric', 40.64, 25.40, 0, 2)
    add_wire(40.64, 21.59, 40.64, 19.05)
    add_pwr('power:VCC', 40.64, 19.05)

    # Base bias pull-down R2 (3.3k) to GND (downwards to y=48.26):
    add_junction(48.26, 35.56)
    add_wire(48.26, 35.56, 48.26, 38.10)
    add_comp('R2', '3.3k', 'Device:R', 'Resistor_SMD:R_0603_1608Metric', 48.26, 41.91, 180, 2)
    add_wire(48.26, 45.72, 48.26, 48.26)
    add_pwr('power:GND', 48.26, 48.26)

    # Base RF bypass capacitors C3 (100pF), C4 (1nF), C5 (100nF) down to GND at y=48.26:
    for i, (c_ref, c_val) in enumerate([('C3', '100pF'), ('C4', '1nF'), ('C5', '100nF')]):
        cx = 57.15 + (i * 8.89)
        add_junction(cx, 35.56)
        add_wire(cx, 35.56, cx, 38.10)
        add_comp(c_ref, c_val, 'Device:C', 'Capacitor_SMD:C_0805_2012Metric', cx, 41.91, 180, 2)
        add_wire(cx, 45.72, cx, 48.26)
        add_pwr('power:GND', cx, 48.26)

    # 4. COLLECTOR TUNED CIRCUIT & OUTPUT MATCH
    # Q1 Pin 3 (Collector) is at (93.98, 71.12)
    add_wire(93.98, 71.12, 104.14, 71.12)
    add_junction(104.14, 71.12)
    add_label('COLLECTOR', 104.14, 71.12)

    # 4. COLLECTOR TUNED CIRCUIT & OUTPUT MATCH (Merged LC Tank + L-Match)
    # L3 (150nH merged DC feed + tank/match shunt inductor) up to VCC at (104.14, 60.96):
    add_wire(104.14, 71.12, 104.14, 64.77)
    add_comp('L3', '150nH', 'Device:L', 'Inductor_SMD:L_0603_1608Metric', 104.14, 60.96, 0, 2)
    add_wire(104.14, 57.15, 104.14, 54.61)
    add_pwr('power:VCC', 104.14, 54.61)

    # C6 (6.8pF shunt tank capacitor / BPF image filter) down to GND:
    add_wire(104.14, 71.12, 104.14, 74.93)
    add_comp('C6', '6.8pF', 'Device:C', 'Capacitor_SMD:C_0805_2012Metric', 104.14, 78.74, 180, 2)
    add_wire(104.14, 82.55, 104.14, 85.09)
    add_pwr('power:GND', 104.14, 85.09)

    # C7 (10pF series L-match capacitor & DC block) at (121.92, 71.12), angle 90:
    # Pin 1 at (118.11, 71.12), Pin 2 at (125.73, 71.12)
    add_wire(104.14, 71.12, 118.11, 71.12)
    add_comp('C7', '10pF', 'Device:C', 'Capacitor_SMD:C_0805_2012Metric', 121.92, 71.12, 90, 2)

    # RF Out node at (142.24, 71.12)
    add_wire(125.73, 71.12, 142.24, 71.12)
    add_junction(142.24, 71.12)
    add_label('RF_OUT_50R', 142.24, 71.12)

    # 5. OUTPUT CONNECTOR J2 & BIAS-TEE
    # J2 at (157.48, 71.12), angle 0: Pin 1 at (152.40, 71.12), Pin 2 at (157.48, 76.20)
    add_comp('J2', 'SMA_50R_OUT_BIAS', 'Connector:Conn_Coaxial', 'Connector_Coaxial:SMA_Samtec_SMA-J-P-H-ST-EM1_EdgeMount', 157.48, 71.12, 0, 2)
    add_wire(142.24, 71.12, 152.40, 71.12)
    # J2 Pin 2 to GND
    add_wire(157.48, 76.20, 157.48, 78.74)
    add_pwr('power:GND', 157.48, 78.74)

    # Bias-Tee pick-off from (142.24, 71.12):
    # L4 (1uH RF Choke) down to (142.24, 88.90):
    add_wire(142.24, 71.12, 142.24, 85.09)
    add_comp('L4', '1uH', 'Device:L', 'Inductor_SMD:L_0603_1608Metric', 142.24, 88.90, 180, 2)

    # Bias-Tee DC node at (142.24, 97.79)
    add_wire(142.24, 92.71, 142.24, 97.79)
    add_junction(142.24, 97.79)
    add_label('BIAS_TEE_DC', 142.24, 97.79)

    # Decoupling caps on Bias-Tee DC line: C9 (100pF) and C10 (10nF) to GND
    for i, (c_ref, c_val) in enumerate([('C9', '100pF'), ('C10', '10nF')]):
        cx = 132.08 - (i * 7.62)
        add_wire(142.24 if i == 0 else cx + 7.62, 97.79, cx, 97.79)
        add_junction(cx, 97.79)
        add_comp(c_ref, c_val, 'Device:C', 'Capacitor_SMD:C_0805_2012Metric', cx, 105.41, 180, 2)
        add_wire(cx, 97.79, cx, 101.60)
        add_wire(cx, 109.22, cx, 111.76)
        add_pwr('power:GND', cx, 111.76)

    # D2 (BAT54) at (152.40, 97.79), angle 180: Pin 2 (Anode) at 148.59, Pin 1 (Cathode) at 156.21
    add_wire(142.24, 97.79, 148.59, 97.79)
    add_comp('D2', 'BAT54', 'Device:D_Schottky', 'Diode_SMD:D_SOD-123', 152.40, 97.79, 180, 2)

    # JP1 (Solder Jumper) in parallel with D2:
    # Placed at (152.40, 105.41), angle 0: Pin 1 at 147.32, Pin 2 at 157.48
    add_comp('JP1', 'BYPASS_D2', 'Jumper:SolderJumper_2_Open', 'Jumper:SolderJumper-2_P1.3mm_Open_Pad1.0x1.5mm', 152.40, 105.41, 0, 2)
    add_wire(144.78, 97.79, 144.78, 105.41)
    add_junction(144.78, 97.79)
    add_wire(144.78, 105.41, 147.32, 105.41)
    add_wire(157.48, 105.41, 160.02, 105.41)
    add_wire(160.02, 105.41, 160.02, 97.79)
    add_wire(156.21, 97.79, 162.56, 97.79)
    add_junction(160.02, 97.79)
    add_pwr('power:VCC', 162.56, 97.79)

    # 6. BATTERY WIRE SOLDER PADS & POWER DISTRIBUTION
    # J3 at (185.42, 60.96): Pin 1 at (180.34, 60.96), Pin 2 at (180.34, 63.50)
    add_comp('J3', 'BATTERY_PADS', 'Connector_Generic:Conn_01x02', 'Connector_PinHeader_2.54mm:PinHeader_1x02_P2.54mm_Vertical', 185.42, 60.96, 0, 2)
    add_wire(180.34, 63.50, 177.80, 63.50)
    add_pwr('power:GND', 177.80, 63.50)

    add_wire(180.34, 60.96, 187.96, 60.96)
    add_junction(187.96, 60.96)
    add_label('BAT_IN', 187.96, 60.96)

    add_wire(187.96, 60.96, 193.04, 60.96)
    add_comp('D1', 'BAT54', 'Device:D_Schottky', 'Diode_SMD:D_SOD-123', 196.85, 60.96, 180, 2)
    add_wire(200.66, 60.96, 208.28, 60.96)
    add_junction(208.28, 60.96)
    add_pwr('power:VCC', 208.28, 60.96)

    for i, (c_ref, c_val, c_fp) in enumerate([('C11', '10uF', 'Capacitor_SMD:C_0805_2012Metric'), ('C12', '100nF', 'Capacitor_SMD:C_0805_2012Metric')]):
        cx = 220.98 + (i * 12.70)
        add_pwr('power:VCC', cx, 69.85)
        add_wire(cx, 69.85, cx, 72.39)
        add_comp(c_ref, c_val, 'Device:C', c_fp, cx, 76.20, 0, 2)
        add_wire(cx, 80.01, cx, 82.55)
        add_pwr('power:GND', cx, 82.55)

    add_pwr('power:VCC', 246.38, 69.85)
    add_wire(246.38, 69.85, 246.38, 72.39)
    add_comp('R4', '2.2k', 'Device:R', 'Resistor_SMD:R_0603_1608Metric', 246.38, 76.20, 0, 2)
    add_wire(246.38, 80.01, 246.38, 83.82)
    add_comp('D3', 'LED_Green', 'Device:LED', 'LED_SMD:LED_0805_2012Metric', 246.38, 87.63, 90, 2)
    add_wire(246.38, 91.44, 246.38, 93.98)
    add_pwr('power:GND', 246.38, 93.98)

    add_pwr('power:PWR_FLAG', 208.28, 53.34, 0)
    add_wire(208.28, 53.34, 208.28, 60.96)

    add_pwr('power:PWR_FLAG', 177.80, 71.12, 0)
    add_wire(177.80, 71.12, 177.80, 63.50)

    sch_content = f'''(kicad_sch
\t(version 20250114)
\t(generator \x22eeschema\x22)
\t(generator_version \x2210.0\x22)
\t(uuid \x22{u()}\x22)
\t(paper \x22A4\x22)
\t(title_block
\t\t(title \x22Common Base FM LNA 98MHz (MMBT5179)\x22)
\t\t(date \x222026-09-07\x22)
\t\t(company \x22OpenSourceSDRLab Form Factor\x22)
\t\t(comment 1 \x22Center: 98MHz, BW: 20MHz (88-108MHz), 70R In, 50R Out\x22)
\t\t(comment 2 \x22Dual Power: Battery Wire Pads + Output SMA Bias-Tee\x22)
\t)
\t(lib_symbols
{lib_symbols_str}
\t)
{chr(10).join(junctions)}
{chr(10).join(wires)}
{chr(10).join(labels)}
{chr(10).join(power_symbols)}
{chr(10).join(components)}
\t(sheet_instances
\t\t(path \x22/\x22
\t\t\t(page \x221\x22)
\t\t)
\t)
\t(embedded_fonts no)
)
'''

    output_path.write_text(sch_content, encoding='utf-8')
    print(f'Schematic written successfully to {output_path}')

if __name__ == '__main__':
    out = Path('lna_fm_98mhz.kicad_sch')
    build_schematic(out)
