import pcbnew
import math

def mm(val):
    return pcbnew.FromMM(val)

def to_mm(val):
    return pcbnew.ToMM(val)

def build_pcb():
    board = pcbnew.BOARD()

    # Design Settings
    settings = board.GetDesignSettings()
    settings.m_CopperEdgeClearance = mm(0.0)
    settings.m_SilkClearance = mm(0.1)

    # =========================================================================
    # 1. Edge.Cuts Outline: 34.0 mm x 29.0 mm (OpenSourceSDRLab Form Factor)
    # =========================================================================
    rect = [(0.0, 0.0), (34.0, 0.0), (34.0, 29.0), (0.0, 29.0), (0.0, 0.0)]
    for i in range(len(rect) - 1):
        s = pcbnew.PCB_SHAPE(board)
        s.SetShape(pcbnew.SHAPE_T_SEGMENT)
        s.SetLayer(pcbnew.Edge_Cuts)
        s.SetStart(pcbnew.VECTOR2I(mm(rect[i][0]), mm(rect[i][1])))
        s.SetEnd(pcbnew.VECTOR2I(mm(rect[i+1][0]), mm(rect[i+1][1])))
        s.SetWidth(mm(0.15))
        board.Add(s)

    # =========================================================================
    # 2. Add Nets
    # =========================================================================
    net_names = [
        'GND', 'VCC', '/RF_IN_50R', '/RF_OUT_50R', '/EMITTER', '/BASE',
        '/COLLECTOR', '/BIAS_TEE_DC', '/BAT_IN',
        'Net-(L2-Pad2)', 'Net-(D3-Pad2)'
    ]
    for n in net_names:
        board.Add(pcbnew.NETINFO_ITEM(board, n))

    def get_net(name):
        return board.FindNet(name)

    def place_fp(lib, name, ref, val, x, y, angle=0):
        path = fr'D:\Programs\KiCad\share\kicad\footprints\{lib}.pretty'
        fp = pcbnew.FootprintLoad(path, name)
        if not fp:
            raise FileNotFoundError(f'Cannot load {lib}:{name}')
        fp.SetReference(ref)
        fp.SetValue(val)
        fp.SetPosition(pcbnew.VECTOR2I(mm(x), mm(y)))
        fp.SetOrientation(pcbnew.EDA_ANGLE(angle, pcbnew.DEGREES_T))
        fp.Reference().SetVisible(False)
        fp.Value().SetVisible(False)
        board.Add(fp)
        return fp

    def set_net(fp, pad_num, net_name):
        p = fp.FindPadByNumber(str(pad_num))
        if p:
            p.SetNet(get_net(net_name))
        else:
            raise ValueError(f"Pad {pad_num} not found on {fp.GetReference()}")

    def add_seg(x1, y1, x2, y2, w_mm, net_name, layer=pcbnew.F_Cu):
        t = pcbnew.PCB_TRACK(board)
        t.SetStart(pcbnew.VECTOR2I(mm(x1), mm(y1)))
        t.SetEnd(pcbnew.VECTOR2I(mm(x2), mm(y2)))
        t.SetWidth(mm(w_mm))
        t.SetLayer(layer)
        t.SetNet(get_net(net_name))
        board.Add(t)
        return t

    def add_via(x, y, net_name='GND', drill=0.3, size=0.6):
        v = pcbnew.PCB_VIA(board)
        v.SetPosition(pcbnew.VECTOR2I(mm(x), mm(y)))
        v.SetDrill(mm(drill))
        v.SetWidth(mm(size))
        v.SetViaType(pcbnew.VIATYPE_THROUGH)
        v.SetNet(get_net(net_name))
        board.Add(v)
        return v

    def pad_pos(fp, num):
        p = fp.FindPadByNumber(str(num))
        pos = p.GetPosition()
        return round(to_mm(pos.x), 4), round(to_mm(pos.y), 4)

    # =========================================================================
    # 3. Mounting Holes (4x M2 plated pads at corners: 2.5mm margin)
    # =========================================================================
    for i, (hx, hy) in enumerate([(2.5, 2.5), (31.5, 2.5), (2.5, 26.5), (31.5, 26.5)]):
        h = place_fp('MountingHole', 'MountingHole_2.2mm_M2_Pad', f'H{i+1}', 'M2', hx, hy)
        for p in h.Pads():
            p.SetNet(get_net('GND'))
            p.SetLocalZoneConnection(pcbnew.ZONE_CONNECTION_FULL)

    # =========================================================================
    # 4. Connectors (RF Centerline: Y = 14.50 mm)
    # =========================================================================
    # J1: SMA Input (50R) at (2.1, 14.50), angle 180 (collar flush at board edge X=0)
    j1 = place_fp('Connector_Coaxial', 'SMA_Samtec_SMA-J-P-H-ST-EM1_EdgeMount', 'J1', 'SMA_50R_IN', 2.1, 14.50, 180)
    set_net(j1, 1, '/RF_IN_50R')
    for p in j1.Pads():
        if p.GetNumber() == '2':
            p.SetNet(get_net('GND'))
            p.SetLocalZoneConnection(pcbnew.ZONE_CONNECTION_FULL)

    # J2: SMA Output + Bias Tee (50R) at (31.90, 14.50), angle 0 (collar flush at board edge X=34)
    j2 = place_fp('Connector_Coaxial', 'SMA_Samtec_SMA-J-P-H-ST-EM1_EdgeMount', 'J2', 'SMA_50R_OUT', 31.90, 14.50, 0)
    set_net(j2, 1, '/RF_OUT_50R')
    for p in j2.Pads():
        if p.GetNumber() == '2':
            p.SetNet(get_net('GND'))
            p.SetLocalZoneConnection(pcbnew.ZONE_CONNECTION_FULL)

    # J3: Battery / DC power solder pads at (19.0, 3.2), angle 90:
    # Centered in the 15mm-23mm OpenSourceSDRLab USB port opening
    j3 = place_fp('Connector_PinHeader_2.54mm', 'PinHeader_1x02_P2.54mm_Vertical', 'J3', 'BAT_PADS', 19.0, 3.2, 90)
    set_net(j3, 1, '/BAT_IN')
    set_net(j3, 2, 'GND')
    j3.FindPadByNumber('2').SetLocalZoneConnection(pcbnew.ZONE_CONNECTION_FULL)

    # D1: BAT54 Battery Protection Diode at (13.0, 3.2), angle 0: Pad 1 (Cathode, VCC) at 11.35, Pad 2 (Anode, /BAT_IN) at 14.65
    d1 = place_fp('Diode_SMD', 'D_SOD-123', 'D1', 'BAT54', 13.0, 3.2, 0)
    set_net(d1, 1, 'VCC')
    set_net(d1, 2, '/BAT_IN')

    # D3 LED at (8.0, 1.8), angle 0: Pad 1 (Cathode) at 7.05, Pad 2 (Anode) at 8.95
    d3 = place_fp('LED_SMD', 'LED_0805_2012Metric', 'D3', 'LED', 8.0, 1.8, 0)
    set_net(d3, 1, 'GND')
    set_net(d3, 2, 'Net-(D3-Pad2)')

    # R4 LED Resistor at (8.95, 4.8), angle 90: Pad 2 (Top) at 4.025, Pad 1 (Bottom, VCC) at 5.575
    r4 = place_fp('Resistor_SMD', 'R_0603_1608Metric', 'R4', '2.2k', 8.95, 4.8, 90)
    set_net(r4, 1, 'VCC')
    set_net(r4, 2, 'Net-(D3-Pad2)')

    # =========================================================================
    # 5. RF Input Matching Section (Pre-Filter BPF + 50R Match):
    # =========================================================================
    c2 = place_fp('Capacitor_SMD', 'C_0603_1608Metric', 'C2', '27pF', 5.8, 17.0, 270)
    set_net(c2, 1, '/RF_IN_50R')
    set_net(c2, 2, 'GND')

    l1 = place_fp('Inductor_SMD', 'L_0603_1608Metric', 'L1', '22nH', 7.8, 17.0, 270)
    set_net(l1, 1, '/RF_IN_50R')
    set_net(l1, 2, 'GND')

    c1 = place_fp('Capacitor_SMD', 'C_0805_2012Metric', 'C1', '91pF', 10.5, 15.45, 0)
    set_net(c1, 1, '/RF_IN_50R')
    set_net(c1, 2, '/EMITTER')

    # =========================================================================
    # 6. Active Stage Q1 (MMBT5179, SOT-23) at (15.5, 14.50), angle 0
    # =========================================================================
    q1 = place_fp('Package_TO_SOT_SMD', 'SOT-23', 'Q1', 'MMBT5179', 15.5, 14.50, 0)
    set_net(q1, 1, '/BASE')
    set_net(q1, 2, '/EMITTER')
    set_net(q1, 3, '/COLLECTOR')

    # Emitter RFC & Bias Resistor:
    l2 = place_fp('Inductor_SMD', 'L_0603_1608Metric', 'L2', '470nH', 13.0, 19.5, 270)
    set_net(l2, 1, '/EMITTER')
    set_net(l2, 2, 'Net-(L2-Pad2)')

    r3 = place_fp('Resistor_SMD', 'R_0603_1608Metric', 'R3', '200R', 13.0, 23.5, 270)
    set_net(r3, 1, 'Net-(L2-Pad2)')
    set_net(r3, 2, 'GND')

    # Base Bypass & Bias Network:
    c3 = place_fp('Capacitor_SMD', 'C_0805_2012Metric', 'C3', '100pF', 14.562, 11.05, 90)
    set_net(c3, 1, '/BASE')
    set_net(c3, 2, 'GND')

    c4 = place_fp('Capacitor_SMD', 'C_0805_2012Metric', 'C4', '1nF', 12.2, 11.05, 90)
    set_net(c4, 1, '/BASE')
    set_net(c4, 2, 'GND')

    c5 = place_fp('Capacitor_SMD', 'C_0805_2012Metric', 'C5', '100nF', 9.8, 11.05, 90)
    set_net(c5, 1, '/BASE')
    set_net(c5, 2, 'GND')

    r2 = place_fp('Resistor_SMD', 'R_0603_1608Metric', 'R2', '3.3k', 7.8, 11.225, 90)
    set_net(r2, 1, '/BASE')
    set_net(r2, 2, 'GND')

    r1 = place_fp('Resistor_SMD', 'R_0603_1608Metric', 'R1', '3.9k', 6.2, 11.225, 90)
    set_net(r1, 1, '/BASE')
    set_net(r1, 2, 'VCC')

    # =========================================================================
    # 7. Collector Tuned Tank & Output Matching:
    # =========================================================================
    l3 = place_fp('Inductor_SMD', 'L_0603_1608Metric', 'L3', '150nH', 19.0, 11.225, 90)
    set_net(l3, 1, '/COLLECTOR')
    set_net(l3, 2, 'VCC')

    c6 = place_fp('Capacitor_SMD', 'C_0805_2012Metric', 'C6', '6.8pF', 19.0, 18.0, 270)
    set_net(c6, 1, '/COLLECTOR')
    set_net(c6, 2, 'GND')

    c7 = place_fp('Capacitor_SMD', 'C_0805_2012Metric', 'C7', '10pF', 22.0, 14.50, 0)
    set_net(c7, 1, '/COLLECTOR')
    set_net(c7, 2, '/RF_OUT_50R')

    # =========================================================================
    # 8. Bias Tee Section (Zero Courtyard Overlap, Zero Crossing):
    # =========================================================================
    # L4 Bias Tee Choke at (25.0, 11.50), angle 0 (Horizontal):
    # Pad 1 (/RF_OUT_50R, Left) at 24.212, Pad 2 (/BIAS_TEE_DC, Right) at 25.788
    l4 = place_fp('Inductor_SMD', 'L_0603_1608Metric', 'L4', '1uH', 25.0, 11.50, 0)
    set_net(l4, 1, '/RF_OUT_50R')
    set_net(l4, 2, '/BIAS_TEE_DC')

    # C10 10nF Bias Tee Low-Freq Bypass at (24.0, 8.6), angle 90:
    # Pad 1 (/BIAS_TEE_DC, Bottom) at 9.55, Pad 2 (GND, Top) at 7.65
    c10 = place_fp('Capacitor_SMD', 'C_0805_2012Metric', 'C10', '10nF', 24.0, 8.6, 90)
    set_net(c10, 1, '/BIAS_TEE_DC')
    set_net(c10, 2, 'GND')
    c10.FindPadByNumber('2').SetLocalZoneConnection(pcbnew.ZONE_CONNECTION_FULL)

    # C9 100pF Bias Tee RF Bypass at (26.5, 8.6), angle 90:
    # Pad 1 (/BIAS_TEE_DC, Bottom) at 9.55, Pad 2 (GND, Top) at 7.65
    c9 = place_fp('Capacitor_SMD', 'C_0805_2012Metric', 'C9', '100pF', 26.5, 8.6, 90)
    set_net(c9, 1, '/BIAS_TEE_DC')
    set_net(c9, 2, 'GND')
    c9.FindPadByNumber('2').SetLocalZoneConnection(pcbnew.ZONE_CONNECTION_FULL)

    # D2 BAT54 Bias Tee Isolation Diode at (26.0, 2.4), angle 0 (Horizontal):
    # Pad 1 (Cathode, VCC, Left) at 24.35, Pad 2 (Anode, /BIAS_TEE_DC, Right) at 27.65
    d2 = place_fp('Diode_SMD', 'D_SOD-123', 'D2', 'BAT54', 26.0, 2.4, 0)
    set_net(d2, 1, 'VCC')
    set_net(d2, 2, '/BIAS_TEE_DC')

    # JP1 Solder Jumper at (26.0, 5.0), angle 180 (Horizontal):
    # Pad 1 (/BIAS_TEE_DC, Right) at 26.65, Pad 2 (VCC, Left) at 25.35
    jp1 = place_fp('Jumper', 'SolderJumper-2_P1.3mm_Open_RoundedPad1.0x1.5mm', 'JP1', 'SolderJumper_Open', 26.0, 5.0, 180)
    set_net(jp1, 1, '/BIAS_TEE_DC')
    set_net(jp1, 2, 'VCC')

    # =========================================================================
    # 9. Power Decoupling (VCC Bulk & High-Frequency)
    # =========================================================================
    c11 = place_fp('Capacitor_SMD', 'C_0805_2012Metric', 'C11', '10uF', 13.0, 7.0, 270)
    set_net(c11, 1, 'VCC')
    set_net(c11, 2, 'GND')

    c12 = place_fp('Capacitor_SMD', 'C_0603_1608Metric', 'C12', '100nF', 15.5, 7.0, 270)
    set_net(c12, 1, 'VCC')
    set_net(c12, 2, 'GND')

    # =========================================================================
    # COPPER TRACE ROUTING
    # =========================================================================
    # 1. /RF_IN_50R: Continuous 50-ohm CPWG line (width 1.5mm)
    p_j1_1 = pad_pos(j1, 1)
    p_c2_1 = pad_pos(c2, 1)
    p_l1_1 = pad_pos(l1, 1)
    p_c1_1 = pad_pos(c1, 1)

    add_seg(p_j1_1[0], 14.50, 7.8, 14.50, 1.5, '/RF_IN_50R')
    add_seg(5.8, 14.50, p_c2_1[0], p_c2_1[1], 0.6, '/RF_IN_50R')
    add_seg(7.8, 14.50, p_l1_1[0], p_l1_1[1], 0.6, '/RF_IN_50R')
    add_seg(7.8, 14.50, 8.75, 15.45, 0.6, '/RF_IN_50R')
    add_seg(8.75, 15.45, p_c1_1[0], 15.45, 0.6, '/RF_IN_50R')

    # 2. /EMITTER: Straight horizontal connection from C1 pad 2 straight into Q1 Emitter pad 2
    p_c1_2 = pad_pos(c1, 2)
    p_q1_2 = pad_pos(q1, 2)
    p_l2_1 = pad_pos(l2, 1)
    add_seg(p_c1_2[0], 15.45, p_q1_2[0], 15.45, 0.5, '/EMITTER')
    add_seg(p_l2_1[0], 15.45, p_l2_1[0], p_l2_1[1], 0.4, '/EMITTER')

    # 3. Net-(L2-Pad2): L2 to R3
    p_l2_2 = pad_pos(l2, 2)
    p_r3_1 = pad_pos(r3, 1)
    add_seg(p_l2_2[0], p_l2_2[1], p_r3_1[0], p_r3_1[1], 0.4, 'Net-(L2-Pad2)')

    # 4. /BASE: Base bus along Y=12.00 connecting Q1.1, C3, C4, C5, R2, R1
    p_q1_1 = pad_pos(q1, 1)
    p_c3_1 = pad_pos(c3, 1)
    p_c4_1 = pad_pos(c4, 1)
    p_c5_1 = pad_pos(c5, 1)
    p_r2_1 = pad_pos(r2, 1)
    p_r1_1 = pad_pos(r1, 1)
    add_seg(p_q1_1[0], p_q1_1[1], p_q1_1[0], 12.00, 0.5, '/BASE')
    add_seg(p_r1_1[0], 12.00, p_q1_1[0], 12.00, 0.4, '/BASE')

    # 5. /COLLECTOR: Resonant tank node at (19.0, 14.50)
    p_q1_3 = pad_pos(q1, 3)
    p_c7_1 = pad_pos(c7, 1)
    p_l3_1 = pad_pos(l3, 1)
    p_c6_1 = pad_pos(c6, 1)
    add_seg(p_q1_3[0], 14.50, p_c7_1[0], 14.50, 0.5, '/COLLECTOR')
    add_seg(19.0, 14.50, p_l3_1[0], p_l3_1[1], 0.5, '/COLLECTOR')
    add_seg(19.0, 14.50, p_c6_1[0], p_c6_1[1], 0.5, '/COLLECTOR')

    # 6. /RF_OUT_50R: Output 50-ohm CPWG line (width 1.5mm)
    p_c7_2 = pad_pos(c7, 2)
    p_j2_1 = pad_pos(j2, 1)
    p_l4_1 = pad_pos(l4, 1)
    add_seg(p_c7_2[0], 14.50, p_j2_1[0], 14.50, 1.5, '/RF_OUT_50R')
    add_seg(p_l4_1[0], 14.50, p_l4_1[0], p_l4_1[1], 0.5, '/RF_OUT_50R')

    # 7. /BIAS_TEE_DC: L4 to C10, C9, JP1, D2
    p_l4_2 = pad_pos(l4, 2)
    p_c10_1 = pad_pos(c10, 1)
    p_c9_1 = pad_pos(c9, 1)
    p_d2_2 = pad_pos(d2, 2)
    p_jp1_1 = pad_pos(jp1, 1)
    # L4.2 (25.788, 11.5) up to horizontal bus at Y=9.55
    add_seg(p_l4_2[0], p_l4_2[1], p_l4_2[0], 9.55, 0.4, '/BIAS_TEE_DC')
    # Horizontal bus along Y=9.55 connecting C10.1 (24.0, 9.55) to C9.1 (26.5, 9.55) and right to X=27.65
    add_seg(p_c10_1[0], p_c10_1[1], p_c9_1[0], p_c9_1[1], 0.4, '/BIAS_TEE_DC')
    add_seg(p_c9_1[0], p_c9_1[1], 27.65, 9.55, 0.4, '/BIAS_TEE_DC')
    # Vertical trace up along X=27.65 to D2.2 (27.65, 2.4) and branch to JP1.1 (26.65, 5.0)
    add_seg(27.65, 9.55, p_d2_2[0], p_d2_2[1], 0.4, '/BIAS_TEE_DC')
    add_seg(p_jp1_1[0], p_jp1_1[1], 27.65, p_jp1_1[1], 0.4, '/BIAS_TEE_DC')

    # 8. /BAT_IN: straight horizontal trace from J3 pad 1 (17.73, 3.2) to D1 pad 2 (14.65, 3.2)
    p_j3_1 = pad_pos(j3, 1)
    p_d1_2 = pad_pos(d1, 2)
    add_seg(p_j3_1[0], p_j3_1[1], p_d1_2[0], p_d1_2[1], 0.6, '/BAT_IN')

    # 9. Net-(D3-Pad2): straight vertical trace from R4 pad 2 (8.95, 4.025) to D3 pad 2 (8.95, 1.8)
    p_r4_2 = pad_pos(r4, 2)
    p_d3_2 = pad_pos(d3, 2)
    add_seg(p_r4_2[0], p_r4_2[1], p_d3_2[0], p_d3_2[1], 0.35, 'Net-(D3-Pad2)')

    # 10. VCC Rail: Main bus at Y=6.0 from X=6.2 across to X=24.35, then north to D2.1 and JP1.2
    p_r1_2 = pad_pos(r1, 2)
    p_d1_1 = pad_pos(d1, 1)
    p_l3_2 = pad_pos(l3, 2)
    p_c11_1 = pad_pos(c11, 1)
    p_c12_1 = pad_pos(c12, 1)
    p_r4_1 = pad_pos(r4, 1)
    p_d2_1 = pad_pos(d2, 1)
    p_jp1_2 = pad_pos(jp1, 2)

    # Main horizontal VCC backbone along Y=6.0 from X=6.2 to X=24.35
    add_seg(p_r1_2[0], 6.0, 24.35, 6.0, 0.5, 'VCC')

    # Connect VCC pins to backbone:
    add_seg(p_r1_2[0], p_r1_2[1], p_r1_2[0], 6.0, 0.4, 'VCC')
    add_seg(p_r4_1[0], p_r4_1[1], p_r4_1[0], 6.0, 0.4, 'VCC')
    add_seg(p_d1_1[0], p_d1_1[1], p_d1_1[0], 6.0, 0.6, 'VCC')
    add_seg(p_c11_1[0], p_c11_1[1], p_c11_1[0], 6.0, 0.5, 'VCC')
    add_seg(p_c12_1[0], p_c12_1[1], p_c12_1[0], 6.0, 0.5, 'VCC')
    add_seg(p_l3_2[0], p_l3_2[1], p_l3_2[0], 6.0, 0.5, 'VCC')

    # Vertical VCC trace from Y=6.0 north along X=24.35 to D2.1 (24.35, 2.4) and branch to JP1.2 (25.35, 5.0)
    add_seg(24.35, 6.0, p_d2_1[0], p_d2_1[1], 0.5, 'VCC')
    add_seg(24.35, p_jp1_2[1], p_jp1_2[0], p_jp1_2[1], 0.4, 'VCC')

    # =========================================================================
    # GROUND CONNECTIONS & VIAS
    # =========================================================================
    def connect_gnd(fp, pad_num, via_x, via_y):
        pos = pad_pos(fp, pad_num)
        add_via(via_x, via_y, 'GND')
        add_seg(pos[0], pos[1], via_x, via_y, 0.4, 'GND')

    connect_gnd(c2, 2, 5.8, 19.5)
    connect_gnd(l1, 2, 7.8, 19.5)
    connect_gnd(r3, 2, 13.0, 26.0)
    connect_gnd(c3, 2, 14.562, 8.5)
    connect_gnd(c4, 2, 12.2, 8.5)
    connect_gnd(c5, 2, 9.8, 8.5)
    connect_gnd(r2, 2, 7.8, 8.5)
    connect_gnd(c6, 2, 19.0, 20.5)
    # Shared central GND via at (25.25, 7.65) connecting C10.2 and C9.2 (bounded strictly between X=24.0 and X=26.5)
    add_via(25.25, 7.65, 'GND')
    add_seg(24.0, 7.65, 26.5, 7.65, 0.4, 'GND')

    connect_gnd(c11, 2, 13.0, 9.5)
    connect_gnd(c12, 2, 15.5, 9.5)
    connect_gnd(d3, 1, 5.5, 1.8)

    # =========================================================================
    # RF VIA FENCING & BOARD STITCHING (34mm x 29mm)
    # =========================================================================
    rf_fence = [
        # --- 1. RF Input CPWG Fencing (J1 to Q1 Emitter) ---
        (2.0, 12.0),
        (2.0, 17.0), (4.0, 17.0), (9.8, 17.5),

        # --- 2. Q1 Stage Flanking Vias ---
        (16.5, 12.0), (16.5, 17.0),
        (21.0, 12.0), (21.0, 17.0),

        # --- 3. 50-Ohm Output CPWG Fencing (C7 to J2 SMA) ---
        # North Side (Y = 12.0 mm)
        (22.5, 12.0), (28.5, 12.0),
        # South Side (Y = 17.0 mm)
        (23.5, 17.0), (26.0, 17.0), (28.5, 17.0),

        # --- 4. Perimeter Ground Stitching ---
        # South Ground Zone (Y = 27.0 mm)
        (6.0, 27.0), (10.0, 27.0), (15.5, 27.0), (19.0, 27.0), (23.0, 27.0), (26.5, 27.0), (29.5, 27.0),
        # North Ground Zone (Y = 1.0 mm)
        (4.0, 1.0), (13.0, 1.0),
        # Left Edge Stitching (X = 1.5 mm)
        (1.5, 6.0), (1.5, 9.0), (1.5, 20.0), (1.5, 23.0),
        # Right Edge Stitching (X = 32.5 mm)
        (32.5, 9.0), (32.5, 20.0), (32.5, 23.0)
    ]
    for vx, vy in rf_fence:
        add_via(vx, vy, 'GND')

    # =========================================================================
    # SOLID GROUND PLANES (F.Cu and B.Cu)
    # =========================================================================
    for layer in [pcbnew.F_Cu, pcbnew.B_Cu]:
        zone = pcbnew.ZONE(board)
        zone.SetLayer(layer)
        zone.SetNet(get_net('GND'))
        zone.SetPadConnection(pcbnew.ZONE_CONNECTION_THERMAL)
        poly = pcbnew.SHAPE_LINE_CHAIN()
        poly.Append(mm(0.0), mm(0.0))
        poly.Append(mm(34.0), mm(0.0))
        poly.Append(mm(34.0), mm(29.0))
        poly.Append(mm(0.0), mm(29.0))
        poly.SetClosed(True)
        zone.AddPolygon(poly)
        zone.SetMinThickness(mm(0.2))
        board.Add(zone)

    # Fill zones
    filler = pcbnew.ZONE_FILLER(board)
    filler.Fill(board.Zones())

    # =========================================================================
    # SILKSCREEN LABELS
    # =========================================================================
    def add_text(text, x, y, size=0.9, thickness=0.14, layer=pcbnew.F_SilkS):
        txt = pcbnew.PCB_TEXT(board)
        txt.SetText(text)
        txt.SetPosition(pcbnew.VECTOR2I(mm(x), mm(y)))
        txt.SetTextSize(pcbnew.VECTOR2I(mm(size), mm(size)))
        txt.SetTextThickness(mm(thickness))
        txt.SetLayer(layer)
        board.Add(txt)

    add_text('98MHz FM LNA', 23.5, 24.2, 1.0, 0.15)
    add_text('MMBT5179 (CB)', 23.5, 25.8, 0.85, 0.13)
    add_text('BIAS-TEE', 23.5, 27.2, 0.80, 0.13)
    add_text('IN 50R', 4.5, 22.0, 0.80, 0.13)
    add_text('OUT 50R', 29.5, 20.5, 0.80, 0.13)

    add_text('+', 17.73, 1.2, 0.80, 0.13)
    add_text('-', 20.27, 1.2, 0.80, 0.13)
    add_text('BAT', 17.73, 5.8, 0.80, 0.13)
    add_text('GND', 20.27, 5.8, 0.80, 0.13)

    silk_map = {
        'C2':  (5.8, 19.5, 0.80, 0.13),
        'L1':  (9.2, 17.0, 0.80, 0.13),
        'C1':  (10.5, 14.0, 0.80, 0.13),
        'Q1':  (17.5, 16.0, 0.80, 0.13),
        'L2':  (11.6, 19.5, 0.80, 0.13),
        'R3':  (11.6, 23.5, 0.80, 0.13),
        'C3':  (16.0, 11.05, 0.80, 0.13),
        'C4':  (12.2, 13.5, 0.80, 0.13),
        'C5':  (9.8, 8.2, 0.80, 0.13),
        'R2':  (7.8, 13.5, 0.80, 0.13),
        'R1':  (5.0, 11.2, 0.80, 0.13),
        'L3':  (20.5, 11.2, 0.80, 0.13),
        'C6':  (20.8, 18.0, 0.80, 0.13),
        'C7':  (22.0, 16.2, 0.80, 0.13),
        'L4':  (28.0, 11.5, 0.80, 0.13),
        'C9':  (28.2, 8.6, 0.80, 0.13),
        'C10': (22.2, 8.6, 0.80, 0.13),
        'D2':  (26.0, 0.7, 0.80, 0.13),
        'JP1': (29.5, 5.0, 0.80, 0.13),
        'D1':  (13.0, 1.0, 0.80, 0.13),
        'C11': (11.4, 7.0, 0.80, 0.13),
        'C12': (17.5, 8.5, 0.80, 0.13),
        'R4':  (7.4, 4.8, 0.80, 0.13),
        'D3':  (5.8, 3.8, 0.80, 0.13),
    }

    for ref_name, (sx, sy, sz, sth) in silk_map.items():
        fp_item = board.FindFootprintByReference(ref_name)
        if fp_item:
            rf = fp_item.Reference()
            rf.SetVisible(True)
            rf.SetPosition(pcbnew.VECTOR2I(mm(sx), mm(sy)))
            rf.SetTextSize(pcbnew.VECTOR2I(mm(sz), mm(sz)))
            rf.SetTextThickness(mm(sth))
            rf.SetLayer(pcbnew.F_SilkS)

    board.Save('lna_fm_98mhz.kicad_pcb')
    print('Clean PCB (34x29mm) successfully built and saved with component silkscreen!')

if __name__ == '__main__':
    build_pcb()
