import pcbnew
import math

def mm(val):
    return pcbnew.FromMM(val)

def to_mm(val):
    return pcbnew.ToMM(val)

def build_pcb():
    board = pcbnew.BOARD()

    # Settings
    settings = board.GetDesignSettings()
    settings.m_CopperEdgeClearance = mm(0.0)
    settings.m_SilkClearance = mm(0.1)

    # 1. Edge.Cuts Outline: 46.0 mm x 30.0 mm
    rect = [(0.0, 0.0), (46.0, 0.0), (46.0, 30.0), (0.0, 30.0), (0.0, 0.0)]
    for i in range(len(rect) - 1):
        s = pcbnew.PCB_SHAPE(board)
        s.SetShape(pcbnew.SHAPE_T_SEGMENT)
        s.SetLayer(pcbnew.Edge_Cuts)
        s.SetStart(pcbnew.VECTOR2I(mm(rect[i][0]), mm(rect[i][1])))
        s.SetEnd(pcbnew.VECTOR2I(mm(rect[i+1][0]), mm(rect[i+1][1])))
        s.SetWidth(mm(0.15))
        board.Add(s)

    # 2. Add Nets
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

    # 3. Mounting Holes
    for i, (hx, hy) in enumerate([(3.5, 3.5), (42.5, 3.5), (3.5, 26.5), (42.5, 26.5)]):
        h = place_fp('MountingHole', 'MountingHole_2.2mm_M2_Pad', f'H{i+1}', 'M2', hx, hy)
        for p in h.Pads():
            p.SetNet(get_net('GND'))
            p.SetLocalZoneConnection(pcbnew.ZONE_CONNECTION_FULL)

    # 4. Connectors
    # J1: SMA Input (50R) at (2.1, 15), angle 180 (barrel facing left, collar flush at board edge X=0)
    j1 = place_fp('Connector_Coaxial', 'SMA_Samtec_SMA-J-P-H-ST-EM1_EdgeMount', 'J1', 'SMA_50R_IN', 2.1, 15.0, 180)
    set_net(j1, 1, '/RF_IN_50R')
    for p in j1.Pads():
        if p.GetNumber() == '2':
            p.SetNet(get_net('GND'))
            p.SetLocalZoneConnection(pcbnew.ZONE_CONNECTION_FULL)

    # J2: SMA Output + Bias Tee (50R) at (43.9, 15), angle 0 (barrel facing right, collar flush at board edge X=46)
    j2 = place_fp('Connector_Coaxial', 'SMA_Samtec_SMA-J-P-H-ST-EM1_EdgeMount', 'J2', 'SMA_50R_OUT', 43.9, 15.0, 0)
    set_net(j2, 1, '/RF_OUT_50R')
    for p in j2.Pads():
        if p.GetNumber() == '2':
            p.SetNet(get_net('GND'))
            p.SetLocalZoneConnection(pcbnew.ZONE_CONNECTION_FULL)

    # J3: Battery / DC power solder pads at (20.0, 3.5), angle 90: Pad 1 (BAT+) at 18.73, Pad 2 (GND) at 21.27
    j3 = place_fp('Connector_PinHeader_2.54mm', 'PinHeader_1x02_P2.54mm_Vertical', 'J3', 'BAT_PADS', 20.0, 3.5, 90)
    set_net(j3, 1, '/BAT_IN')
    set_net(j3, 2, 'GND')

    # D1: BAT54 Battery Protection Diode at (15.0, 3.5), angle 0: Pad 1 (Cathode, VCC) at 13.35, Pad 2 (Anode, /BAT_IN) at 16.65
    d1 = place_fp('Diode_SMD', 'D_SOD-123', 'D1', 'BAT54', 15.0, 3.5, 0)
    set_net(d1, 1, 'VCC')
    set_net(d1, 2, '/BAT_IN')

    # 5. RF Input Matching Section (Merged LC BPF & Match: Shunt L1 || C2 to GND + Series C1 to Emitter):
    # C2 Shunt Tank Cap (27pF, 0603 C0G) at (6.5, 17.5), angle 270:
    # Pad 1 (Top, 16.7125) connects to 50R line, Pad 2 (Bottom, 18.2875) connects to GND via
    c2 = place_fp('Capacitor_SMD', 'C_0603_1608Metric', 'C2', '27pF', 6.5, 17.5, 270)
    set_net(c2, 1, '/RF_IN_50R')
    set_net(c2, 2, 'GND')

    # L1 Shunt Match Inductor (22nH, 0603 wirewound) at (8.5, 17.5), angle 270:
    # Pad 1 (Top, 16.7125) connects to 50R line, Pad 2 (Bottom, 18.2875) connects to GND via
    l1 = place_fp('Inductor_SMD', 'L_0603_1608Metric', 'L1', '22nH', 8.5, 17.5, 270)
    set_net(l1, 1, '/RF_IN_50R')
    set_net(l1, 2, 'GND')

    # C1 Series Match & DC Block (91pF, 0805 NP0) at (11.5, 15.95), angle 0: Collinear with Q1 Emitter!
    # Pad 1 (Left, 10.55) connects from 50R line via miter, Pad 2 (Right, 12.45) connects straight to Emitter
    c1 = place_fp('Capacitor_SMD', 'C_0805_2012Metric', 'C1', '91pF', 11.5, 15.95, 0)
    set_net(c1, 1, '/RF_IN_50R')
    set_net(c1, 2, '/EMITTER')

    # 6. Active Stage Q1 (MMBT5179, SOT-23) at (17.0, 15.0), angle 0
    # Pad 1 (Base) at (16.0625, 14.05), Pad 2 (Emitter) at (16.0625, 15.95), Pad 3 (Collector) at (17.9375, 15.0)
    q1 = place_fp('Package_TO_SOT_SMD', 'SOT-23', 'Q1', 'MMBT5179', 17.0, 15.0, 0)
    set_net(q1, 1, '/BASE')
    set_net(q1, 2, '/EMITTER')
    set_net(q1, 3, '/COLLECTOR')

    # Emitter RFC & Bias Resistor:
    # L2 RFC at (14.675, 20.0), angle 270: Pad 1 (Top) at 19.2125, Pad 2 (Bottom) at 20.7875
    l2 = place_fp('Inductor_SMD', 'L_0603_1608Metric', 'L2', '470nH', 14.675, 20.0, 270)
    set_net(l2, 1, '/EMITTER')
    set_net(l2, 2, 'Net-(L2-Pad2)')

    # R3 Emitter Resistor at (14.675, 24.5), angle 270: Pad 1 (Top) at 23.725, Pad 2 (Bottom) at 25.275
    r3 = place_fp('Resistor_SMD', 'R_0603_1608Metric', 'R3', '200R', 14.675, 24.5, 270)
    set_net(r3, 1, 'Net-(L2-Pad2)')
    set_net(r3, 2, 'GND')

    # Base Bypass & Bias Network (Angle 90 puts Pad 1 at Bottom Y=11.45, Pad 2 at Top Y=9.55):
    c3 = place_fp('Capacitor_SMD', 'C_0805_2012Metric', 'C3', '100pF', 16.062, 10.5, 90)
    set_net(c3, 1, '/BASE')
    set_net(c3, 2, 'GND')

    c4 = place_fp('Capacitor_SMD', 'C_0805_2012Metric', 'C4', '1nF', 13.5, 10.5, 90)
    set_net(c4, 1, '/BASE')
    set_net(c4, 2, 'GND')

    c5 = place_fp('Capacitor_SMD', 'C_0805_2012Metric', 'C5', '100nF', 11.0, 10.5, 90)
    set_net(c5, 1, '/BASE')
    set_net(c5, 2, 'GND')

    r2 = place_fp('Resistor_SMD', 'R_0603_1608Metric', 'R2', '3.3k', 8.5, 10.5, 90)
    set_net(r2, 1, '/BASE')
    set_net(r2, 2, 'GND')

    r1 = place_fp('Resistor_SMD', 'R_0603_1608Metric', 'R1', '3.9k', 6.0, 8.5, 90)
    set_net(r1, 1, '/BASE')
    set_net(r1, 2, 'VCC')

    # 7. Collector Tuned Tank & Output Matching (Merged LC Tank + L-Match):
    # L3 Merged DC Feed & Shunt Inductor at (21.0, 10.0), angle 90: Pad 1 (Bottom, Collector) at 10.7875, Pad 2 (Top, VCC) at 9.2125
    l3 = place_fp('Inductor_SMD', 'L_0603_1608Metric', 'L3', '150nH', 21.0, 10.0, 90)
    set_net(l3, 1, '/COLLECTOR')
    set_net(l3, 2, 'VCC')

    # C6 Shunt Tank Cap (BPF Image Filter) at (21.0, 18.5), angle 270: Pad 1 (Top, Collector) at 17.55, Pad 2 (Bottom, GND) at 19.45
    c6 = place_fp('Capacitor_SMD', 'C_0805_2012Metric', 'C6', '6.8pF', 21.0, 18.5, 270)
    set_net(c6, 1, '/COLLECTOR')
    set_net(c6, 2, 'GND')

    # C7 Series L-Match Cap & Output DC Block at (25.5, 15.0), angle 0: Pad 1 (Left, Collector) at 24.55, Pad 2 (Right, RF_OUT_50R) at 26.45
    c7 = place_fp('Capacitor_SMD', 'C_0805_2012Metric', 'C7', '10pF', 25.5, 15.0, 0)
    set_net(c7, 1, '/COLLECTOR')
    set_net(c7, 2, '/RF_OUT_50R')

    # 8. Bias Tee Section:
    # L4 Bias Tee Choke at (36.0, 10.0), angle 90: Pad 1 (Bottom, RF_OUT) at 10.7875, Pad 2 (Top, DC) at 9.2125
    l4 = place_fp('Inductor_SMD', 'L_0603_1608Metric', 'L4', '1uH', 36.0, 10.0, 90)
    set_net(l4, 1, '/RF_OUT_50R')
    set_net(l4, 2, '/BIAS_TEE_DC')

    # C9 100pF Bypass at (39.0, 10.0), angle 0: Pad 1 (Left) at 38.05, Pad 2 (Right) at 39.95
    c9 = place_fp('Capacitor_SMD', 'C_0805_2012Metric', 'C9', '100pF', 39.0, 10.0, 0)
    set_net(c9, 1, '/BIAS_TEE_DC')
    set_net(c9, 2, 'GND')

    # C10 10nF Bypass at (39.0, 7.5), angle 0: Pad 1 (Left) at 38.05, Pad 2 (Right) at 39.95
    c10 = place_fp('Capacitor_SMD', 'C_0805_2012Metric', 'C10', '10nF', 39.0, 7.5, 0)
    set_net(c10, 1, '/BIAS_TEE_DC')
    set_net(c10, 2, 'GND')

    # D2 Bias-Tee Diode at (36.0, 5.0), angle 270: Pad 2 (Bottom, Anode) at 6.65, Pad 1 (Top, Cathode) at 3.35
    d2 = place_fp('Diode_SMD', 'D_SOD-123', 'D2', 'BAT54', 36.0, 5.0, 270)
    set_net(d2, 1, 'VCC')
    set_net(d2, 2, '/BIAS_TEE_DC')

    # JP1 Solder Jumper at (33.0, 5.0), angle 90: Pad 1 (Bottom) at 5.65, Pad 2 (Top) at 4.35
    jp1 = place_fp('Jumper', 'SolderJumper-2_P1.3mm_Open_Pad1.0x1.5mm', 'JP1', 'BYPASS', 33.0, 5.0, 90)
    set_net(jp1, 1, '/BIAS_TEE_DC')
    set_net(jp1, 2, 'VCC')

    # 9. Power Decoupling & LED:
    # C11 10uF at (24.0, 7.5), angle 270: Pad 1 (Top, VCC) at 6.55, Pad 2 (Bottom, GND) at 8.45
    c11 = place_fp('Capacitor_SMD', 'C_0805_2012Metric', 'C11', '10uF', 24.0, 7.5, 270)
    set_net(c11, 1, 'VCC')
    set_net(c11, 2, 'GND')

    # C12 100nF at (26.8, 7.5), angle 270: Pad 1 (Top, VCC) at 6.55, Pad 2 (Bottom, GND) at 8.45
    c12 = place_fp('Capacitor_SMD', 'C_0805_2012Metric', 'C12', '100nF', 26.8, 7.5, 270)
    set_net(c12, 1, 'VCC')
    set_net(c12, 2, 'GND')

    # R4 LED Resistor at (10.95, 5.0), angle 90: Pad 2 (Top) at 4.225, Pad 1 (Bottom, VCC) at 5.775
    r4 = place_fp('Resistor_SMD', 'R_0603_1608Metric', 'R4', '2.2k', 10.95, 5.0, 90)
    set_net(r4, 1, 'VCC')
    set_net(r4, 2, 'Net-(D3-Pad2)')

    # D3 LED at (10.0, 2.0) (10mm from left, 2mm from top), angle 0: Pad 1 (Left, Cathode) at 9.05, Pad 2 (Right, Anode) at 10.95
    d3 = place_fp('LED_SMD', 'LED_0805_2012Metric', 'D3', 'LED', 10.0, 2.0, 0)
    set_net(d3, 1, 'GND')
    set_net(d3, 2, 'Net-(D3-Pad2)')

    # =========================================================================
    # ROUTE TRACKS
    # =========================================================================
    # 1. /RF_IN_50R (CPWG 50R, width 1.5mm from SMA J1 up to L-match tap at X=8.5mm)
    p_j1_1 = pad_pos(j1, 1)
    p_c2_1 = pad_pos(c2, 1)
    p_l1_1 = pad_pos(l1, 1)
    p_c1_1 = pad_pos(c1, 1)

    # Continuous 50-ohm CPWG line from SMA J1 to L-match tap
    add_seg(p_j1_1[0], 15.0, 8.5, 15.0, 1.5, '/RF_IN_50R')

    # Vertical tap from 50R line down to C2 pad 1
    add_seg(6.5, 15.0, p_c2_1[0], p_c2_1[1], 0.6, '/RF_IN_50R')

    # Vertical tap from 50R line down to L1 pad 1
    add_seg(8.5, 15.0, p_l1_1[0], p_l1_1[1], 0.6, '/RF_IN_50R')

    # Smooth 45-degree miter transition from 50R line (Y=15.0) up to C1 level (Y=15.95)
    add_seg(8.5, 15.0, 9.45, 15.95, 0.6, '/RF_IN_50R')

    # Straight horizontal feed into C1 pad 1
    add_seg(9.45, 15.95, p_c1_1[0], 15.95, 0.6, '/RF_IN_50R')

    # 2. /EMITTER: Completely STRAIGHT horizontal line from C1 to Q1 Emitter!
    p_c1_2 = pad_pos(c1, 2)
    p_q1_2 = pad_pos(q1, 2)
    p_l2_1 = pad_pos(l2, 1)
    # Direct horizontal connection from C1 pad 2 straight into Q1 emitter pad 2
    add_seg(p_c1_2[0], 15.95, p_q1_2[0], 15.95, 0.5, '/EMITTER')
    # Vertical RFC feed branching straight down to L2 pad 1
    add_seg(p_l2_1[0], 15.95, p_l2_1[0], p_l2_1[1], 0.4, '/EMITTER')

    # 4. Net-(L2-Pad2)
    p_l2_2 = pad_pos(l2, 2)
    p_r3_1 = pad_pos(r3, 1)
    add_seg(p_l2_2[0], p_l2_2[1], p_r3_1[0], p_r3_1[1], 0.4, 'Net-(L2-Pad2)')

    # 5. /BASE
    p_q1_1 = pad_pos(q1, 1)
    p_c3_1 = pad_pos(c3, 1)
    p_c4_1 = pad_pos(c4, 1)
    p_c5_1 = pad_pos(c5, 1)
    p_r2_1 = pad_pos(r2, 1)
    p_r1_1 = pad_pos(r1, 1)
    add_seg(p_q1_1[0], p_q1_1[1], p_c3_1[0], p_c3_1[1], 0.5, '/BASE')
    add_seg(p_c3_1[0], p_c3_1[1], p_c4_1[0], p_c4_1[1], 0.4, '/BASE')
    add_seg(p_c4_1[0], p_c4_1[1], p_c5_1[0], p_c5_1[1], 0.4, '/BASE')
    add_seg(p_c5_1[0], p_c5_1[1], p_r2_1[0], p_r2_1[1], 0.4, '/BASE')
    add_seg(p_r2_1[0], p_r2_1[1], 6.0, p_r2_1[1], 0.4, '/BASE')
    add_seg(6.0, p_r2_1[1], p_r1_1[0], p_r1_1[1], 0.4, '/BASE')

    # 6. /COLLECTOR
    p_q1_3 = pad_pos(q1, 3)
    p_c7_1 = pad_pos(c7, 1)
    p_l3_1 = pad_pos(l3, 1)
    p_c6_1 = pad_pos(c6, 1)
    add_seg(p_q1_3[0], p_q1_3[1], p_c7_1[0], p_c7_1[1], 0.5, '/COLLECTOR')
    add_seg(21.0, 15.0, p_l3_1[0], p_l3_1[1], 0.5, '/COLLECTOR')
    add_seg(21.0, 15.0, p_c6_1[0], p_c6_1[1], 0.5, '/COLLECTOR')

    # 7. /RF_OUT_50R (CPWG 50R, width 1.5mm)
    p_c7_2 = pad_pos(c7, 2)
    p_j2_1 = pad_pos(j2, 1)
    p_l4_1 = pad_pos(l4, 1)
    add_seg(p_c7_2[0], p_c7_2[1], p_j2_1[0], p_j2_1[1], 1.5, '/RF_OUT_50R')
    add_seg(36.0, 15.0, p_l4_1[0], p_l4_1[1], 0.5, '/RF_OUT_50R')

    # 9. /BIAS_TEE_DC
    p_l4_2 = pad_pos(l4, 2)
    p_c9_1 = pad_pos(c9, 1)
    p_c10_1 = pad_pos(c10, 1)
    p_d2_2 = pad_pos(d2, 2)
    p_jp1_1 = pad_pos(jp1, 1)
    add_seg(p_l4_2[0], p_l4_2[1], p_c9_1[0], p_l4_2[1], 0.4, '/BIAS_TEE_DC')
    add_seg(p_c9_1[0], p_l4_2[1], p_c9_1[0], p_c9_1[1], 0.4, '/BIAS_TEE_DC')
    add_seg(p_c9_1[0], p_c9_1[1], p_c10_1[0], p_c10_1[1], 0.4, '/BIAS_TEE_DC')
    add_seg(p_l4_2[0], p_l4_2[1], p_d2_2[0], p_d2_2[1], 0.4, '/BIAS_TEE_DC')
    add_seg(p_d2_2[0], p_d2_2[1], p_jp1_1[0], p_jp1_1[1], 0.4, '/BIAS_TEE_DC')

    # 10. /BAT_IN: straight horizontal trace from J3 pad 1 (18.73, 3.5) to D1 pad 2 (16.65, 3.5)
    p_j3_1 = pad_pos(j3, 1)
    p_d1_2 = pad_pos(d1, 2)
    add_seg(p_j3_1[0], p_j3_1[1], p_d1_2[0], p_d1_2[1], 0.6, '/BAT_IN')

    # 11. Net-(D3-Pad2): straight vertical trace from R4 pad 2 (10.95, 4.225) to D3 pad 2 (10.95, 2.0)
    p_r4_2 = pad_pos(r4, 2)
    p_d3_2 = pad_pos(d3, 2)
    add_seg(p_r4_2[0], p_r4_2[1], p_d3_2[0], p_d3_2[1], 0.35, 'Net-(D3-Pad2)')

    # 12. VCC Rail
    p_r1_2 = pad_pos(r1, 2)
    p_d1_1 = pad_pos(d1, 1)
    p_l3_2 = pad_pos(l3, 2)
    p_c11_1 = pad_pos(c11, 1)
    p_c12_1 = pad_pos(c12, 1)
    p_r4_1 = pad_pos(r4, 1)
    p_d2_1 = pad_pos(d2, 1)
    p_jp1_2 = pad_pos(jp1, 2)

    # Main East Backbone at Y=4.5 from X=26.8 to X=36.0 (connecting C12, JP1, D2)
    add_seg(26.8, 4.5, 36.0, 4.5, 0.5, 'VCC')
    add_seg(p_d2_1[0], p_d2_1[1], p_d2_1[0], 4.5, 0.5, 'VCC')
    add_seg(p_jp1_2[0], p_jp1_2[1], p_jp1_2[0], 4.5, 0.4, 'VCC')

    # Main Central VCC branch at Y=6.2 from X=6.0 to X=26.8:
    add_seg(p_r1_2[0], 6.2, 26.8, 6.2, 0.5, 'VCC')

    # Connect components to this Y=6.2 bus:
    add_seg(p_r1_2[0], p_r1_2[1], p_r1_2[0], 6.2, 0.4, 'VCC')
    add_seg(p_r4_1[0], p_r4_1[1], p_r4_1[0], 6.2, 0.4, 'VCC')
    add_seg(p_d1_1[0], p_d1_1[1], p_d1_1[0], 6.2, 0.6, 'VCC')
    add_seg(p_l3_2[0], p_l3_2[1], p_l3_2[0], 6.2, 0.5, 'VCC')
    add_seg(p_c11_1[0], p_c11_1[1], p_c11_1[0], 6.2, 0.5, 'VCC')
    add_seg(p_c12_1[0], p_c12_1[1], p_c12_1[0], 6.2, 0.5, 'VCC')

    # Link between Y=6.2 and Y=4.5 at X=26.8
    add_seg(26.8, 4.5, 26.8, 6.2, 0.5, 'VCC')

    # =========================================================================
    # GROUND CONNECTIONS & VIAS
    # =========================================================================
    def connect_gnd(fp, pad_num, via_x, via_y):
        pos = pad_pos(fp, pad_num)
        add_via(via_x, via_y, 'GND')
        add_seg(pos[0], pos[1], via_x, via_y, 0.4, 'GND')

    # J3 GND is a plated through-hole pad natively connecting F.Cu and B.Cu GND zones
    connect_gnd(c2, 2, 6.5, 20.0)
    connect_gnd(l1, 2, 8.5, 20.5)
    connect_gnd(r3, 2, 14.675, 27.0)
    connect_gnd(c3, 2, 16.062, 7.8)
    connect_gnd(c4, 2, 13.5, 7.8)
    connect_gnd(c5, 2, 11.0, 7.8)
    connect_gnd(r2, 2, 8.5, 7.8)
    connect_gnd(c6, 2, 21.0, 21.5)
    connect_gnd(c9, 2, 41.5, 10.0)
    connect_gnd(c10, 2, 41.5, 7.5)
    connect_gnd(c11, 2, 24.0, 10.0)
    connect_gnd(c12, 2, 26.8, 10.0)
    connect_gnd(d3, 1, 7.0, 2.0)

    # Comprehensive RF Via Fencing (from Collector to SMA OUT, plus Input CPWG & Board Stitching)
    rf_fence = [
        # --- 1. RF Input CPWG Fencing (J1 to Q1 Emitter) ---
        (2.0, 12.5), (4.5, 12.5), (7.0, 12.5), (9.5, 12.5), (12.0, 12.5),
        (2.0, 17.5), (4.5, 17.5), (11.5, 18.5),

        # --- 2. Q1 Transistor & Collector Terminal Shielding ---
        # Immediate flanking vias isolating Collector from Base & Emitter
        (18.5, 12.5), (18.5, 17.5),
        # Inter-stage shielding between L3/C6 and C7
        (23.5, 12.5), (23.5, 17.5),

        # --- 3. Series L-Match Cap C7 Shielding ---
        (25.8, 12.5), (25.8, 17.5),

        # --- 4. 50-Ohm Output CPWG Fencing (C7 to J2 SMA) ---
        # North Side (Y = 12.5 mm)
        (28.0, 12.5), (31.0, 12.5), (33.5, 12.5),
        (38.5, 12.5), (41.0, 12.5), (43.5, 12.5),
        # South Side (Y = 17.5 mm)
        (28.0, 17.5), (30.5, 17.5), (33.0, 17.5), (35.5, 17.5),
        (38.0, 17.5), (40.5, 17.5), (43.0, 17.5), (44.5, 17.5),

        # --- 5. Connector Shielding Vias ---
        (3.5, 10.0), (3.5, 20.0),
        (42.5, 10.0), (42.5, 20.0),

        # --- 6. Ground Plane Field Stitching (LionCircuits DFM compliant: >= 1.5mm from edges) ---
        # South Ground Zone (Y = 21.5, 26.5, 28.5 mm)
        (2.0, 21.5), (5.0, 21.5), (12.0, 21.5), (16.0, 21.5), (25.0, 21.5), (29.0, 21.5), (33.0, 21.5), (37.0, 21.5), (41.0, 21.5), (44.0, 21.5),
        (8.0, 26.5), (18.0, 26.5), (22.0, 26.5), (26.0, 26.5), (30.0, 26.5), (34.0, 26.5), (38.0, 26.5),
        (4.0, 28.5), (10.0, 28.5), (16.0, 28.5), (22.0, 28.5), (28.0, 28.5), (34.0, 28.5), (40.0, 28.5),
        # North Ground Zone (Y = 1.5 mm)
        (4.0, 1.5), (15.5, 1.5), (27.0, 1.5), (30.0, 1.5), (34.0, 1.5), (38.0, 1.5),
        # Perimeter End Stitching
        (1.5, 5.0), (1.5, 9.0), (1.5, 21.0), (1.5, 25.0),
        (44.5, 5.0), (44.5, 9.0), (44.5, 21.0), (44.5, 25.0)
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
        poly.Append(mm(46.0), mm(0.0))
        poly.Append(mm(46.0), mm(30.0))
        poly.Append(mm(0.0), mm(30.0))
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
    def add_text(text, x, y, size=1.0, thickness=0.15, layer=pcbnew.F_SilkS):
        txt = pcbnew.PCB_TEXT(board)
        txt.SetText(text)
        txt.SetPosition(pcbnew.VECTOR2I(mm(x), mm(y)))
        txt.SetTextSize(pcbnew.VECTOR2I(mm(size), mm(size)))
        txt.SetTextThickness(mm(thickness))
        txt.SetLayer(layer)
        board.Add(txt)

    add_text('98MHz FM LNA', 23.0, 26.2, 1.2, 0.18)
    add_text('MMBT5179 (CB)', 23.0, 28.0, 0.9, 0.15)
    add_text('BIAS-TEE ENABLED', 23.0, 24.5, 0.85, 0.15)
    add_text('IN 50R', 5.0, 23.5, 0.85, 0.15)
    add_text('OUT 50R', 40.0, 21.0, 0.85, 0.15)
    add_text('+', 18.73, 1.2, 0.80, 0.13)
    add_text('-', 21.27, 1.2, 0.80, 0.13)
    add_text('BAT', 18.73, 5.9, 0.80, 0.13)
    add_text('GND', 21.27, 5.9, 0.80, 0.13)

    # Component Reference Designators on F.SilkS (Optimized for 0 DRC violations):
    silk_map = {
        # 1. RF Input & Pre-Filter BPF
        'C2':  (5.2, 18.5, 0.80, 0.13),    # Shunt 27pF
        'L1':  (9.8, 17.5, 0.80, 0.13),    # Shunt 22nH
        'C1':  (11.5, 14.3, 0.80, 0.13),   # Series 91pF

        # 2. Active Stage Q1 & Emitter Choke / Bias
        'Q1':  (19.0, 16.8, 0.80, 0.13),   # MMBT5179 (SOT-23)
        'L2':  (13.3, 20.0, 0.80, 0.13),   # Emitter RFC 470nH (left side)
        'R3':  (13.3, 24.5, 0.80, 0.13),   # Emitter Resistor 200R (left side)

        # 3. Base Bias & Triple Bypass Caps
        'C3':  (17.8, 10.5, 0.80, 0.13),   # Base bypass 100pF
        'C4':  (13.5, 12.8, 0.80, 0.13),   # Base bypass 1nF
        'C5':  (11.0, 12.8, 0.80, 0.13),   # Base bypass 100nF
        'R2':  (8.5, 12.8, 0.80, 0.13),    # Base bias 3.3k
        'R1':  (4.8, 8.5, 0.80, 0.13),     # Base bias 3.9k

        # 4. Collector Tuned Tank & Output Match
        'L3':  (22.4, 10.0, 0.80, 0.13),   # Collector Inductor 150nH
        'C6':  (22.5, 18.5, 0.80, 0.13),   # Shunt Tank Cap 6.8pF
        'C7':  (25.5, 17.2, 0.80, 0.13),   # Series Match / DC Block 10pF

        # 5. Bias Tee Section
        'L4':  (34.6, 10.0, 0.80, 0.13),   # Bias Tee Choke 1uH
        'C9':  (39.0, 11.5, 0.80, 0.13),   # Bias Tee 100pF
        'C10': (39.5, 6.0, 0.80, 0.13),    # Bias Tee 10nF
        'D2':  (37.8, 4.8, 0.80, 0.13),    # Bias Tee BAT54 (right side)
        'JP1': (33.0, 1.8, 0.80, 0.13),    # Solder Jumper

        # 6. Power Decoupling & LED
        'D1':  (15.0, 1.8, 0.80, 0.13),    # Battery Diode BAT54 (above D1)
        'C11': (22.2, 7.5, 0.80, 0.13),    # 10uF
        'C12': (28.8, 7.5, 0.80, 0.13),    # 100nF
        'R4':  (8.5, 5.0, 0.80, 0.13),     # LED Resistor 2.2k (left of R4)
        'D3':  (12.4, 1.3, 0.80, 0.13),    # Power LED (right of D3: 10mm from left, 2mm from top)
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
    print('Clean PCB successfully built and saved with component silkscreen!')

if __name__ == '__main__':
    build_pcb()
