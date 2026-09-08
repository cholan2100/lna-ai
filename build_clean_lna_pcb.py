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
    # 1. Edge.Cuts Outline: 34.0 mm x 29.0 mm with 4x R=3.0mm Corner Fillets
    # =========================================================================
    # Corners centered at:
    #   Top-Left:     (3.0, 3.0)
    #   Top-Right:    (31.0, 3.0)
    #   Bottom-Right: (31.0, 26.0)
    #   Bottom-Left:  (3.0, 26.0)
    #
    # Clockwise contour:
    # 1. Top straight segment: (3.0, 0.0) -> (31.0, 0.0)
    # 2. Top-Right arc: (31.0, 0.0) -> mid (31.0 + 3/sqrt2, 3.0 - 3/sqrt2) -> (34.0, 3.0)
    # 3. Right straight segment: (34.0, 3.0) -> (34.0, 26.0)
    # 4. Bottom-Right arc: (34.0, 26.0) -> mid (31.0 + 3/sqrt2, 26.0 + 3/sqrt2) -> (31.0, 29.0)
    # 5. Bottom straight segment: (31.0, 29.0) -> (3.0, 29.0)
    # 6. Bottom-Left arc: (3.0, 29.0) -> mid (3.0 - 3/sqrt2, 26.0 + 3/sqrt2) -> (0.0, 26.0)
    # 7. Left straight segment: (0.0, 26.0) -> (0.0, 3.0)
    # 8. Top-Left arc: (0.0, 3.0) -> mid (3.0 - 3/sqrt2, 3.0 - 3/sqrt2) -> (3.0, 0.0)

    def add_line(x1, y1, x2, y2):
        s = pcbnew.PCB_SHAPE(board)
        s.SetShape(pcbnew.SHAPE_T_SEGMENT)
        s.SetLayer(pcbnew.Edge_Cuts)
        s.SetStart(pcbnew.VECTOR2I(mm(x1), mm(y1)))
        s.SetEnd(pcbnew.VECTOR2I(mm(x2), mm(y2)))
        s.SetWidth(mm(0.15))
        board.Add(s)

    def add_arc(x_start, y_start, x_mid, y_mid, x_end, y_end):
        s = pcbnew.PCB_SHAPE(board)
        s.SetShape(pcbnew.SHAPE_T_ARC)
        s.SetLayer(pcbnew.Edge_Cuts)
        s.SetWidth(mm(0.15))
        s.SetArcGeometry(
            pcbnew.VECTOR2I(mm(x_start), mm(y_start)),
            pcbnew.VECTOR2I(mm(x_mid), mm(y_mid)),
            pcbnew.VECTOR2I(mm(x_end), mm(y_end))
        )
        board.Add(s)

    d = 3.0 / math.sqrt(2.0)  # ~2.12132 mm

    # 1. Top line
    add_line(3.0, 0.0, 31.0, 0.0)
    # 2. Top-Right arc
    add_arc(31.0, 0.0, 31.0 + d, 3.0 - d, 34.0, 3.0)
    # 3. Right line
    add_line(34.0, 3.0, 34.0, 26.0)
    # 4. Bottom-Right arc
    add_arc(34.0, 26.0, 31.0 + d, 26.0 + d, 31.0, 29.0)
    # 5. Bottom line
    add_line(31.0, 29.0, 3.0, 29.0)
    # 6. Bottom-Left arc
    add_arc(3.0, 29.0, 3.0 - d, 26.0 + d, 0.0, 26.0)
    # 7. Left line
    add_line(0.0, 26.0, 0.0, 3.0)
    # 8. Top-Left arc
    add_arc(0.0, 3.0, 3.0 - d, 3.0 - d, 3.0, 0.0)

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
    # 3. Mounting Holes (4x M2 plated pads at exact enclosure post centers: 3.0mm margin)
    # =========================================================================
    for i, (hx, hy) in enumerate([(3.0, 3.0), (31.0, 3.0), (3.0, 26.0), (31.0, 26.0)]):
        h = place_fp('MountingHole', 'MountingHole_2.2mm_M2_Pad', f'H{i+1}', 'M2', hx, hy)
        for p in h.Pads():
            p.SetNet(get_net('GND'))
            p.SetLocalZoneConnection(pcbnew.ZONE_CONNECTION_FULL)

    # =========================================================================
    # 4. Connectors (RF Centerline: Y = 17.00 mm - Aligned with Enclosure Cutouts)
    # =========================================================================
    # J1: SMA Input (50R) at (2.10, 17.00), angle 180 (collar flush at board edge X=0)
    j1 = place_fp('Connector_Coaxial', 'SMA_Samtec_SMA-J-P-H-ST-EM1_EdgeMount', 'J1', 'SMA_50R_IN', 2.10, 17.00, 180)
    set_net(j1, 1, '/RF_IN_50R')
    for p in j1.Pads():
        if p.GetNumber() == '2':
            p.SetNet(get_net('GND'))
            p.SetLocalZoneConnection(pcbnew.ZONE_CONNECTION_FULL)

    # J2: SMA Output + Bias Tee (50R) at (31.90, 17.00), angle 0 (collar flush at board edge X=34)
    j2 = place_fp('Connector_Coaxial', 'SMA_Samtec_SMA-J-P-H-ST-EM1_EdgeMount', 'J2', 'SMA_50R_OUT', 31.90, 17.00, 0)
    set_net(j2, 1, '/RF_OUT_50R')
    for p in j2.Pads():
        if p.GetNumber() == '2':
            p.SetNet(get_net('GND'))
            p.SetLocalZoneConnection(pcbnew.ZONE_CONNECTION_FULL)

    # J3: Battery / DC power solder pads at (18.50, 3.2), angle 90:
    # Dead center in the 7.6mm USB/DC enclosure cutout (X in [14.7, 22.3])
    j3 = place_fp('Connector_PinHeader_2.54mm', 'PinHeader_1x02_P2.54mm_Vertical', 'J3', 'BAT_PADS', 18.50, 3.2, 90)
    set_net(j3, 1, '/BAT_IN')
    set_net(j3, 2, 'GND')
    j3.FindPadByNumber('2').SetLocalZoneConnection(pcbnew.ZONE_CONNECTION_FULL)

    # D1: BAT54 Battery Protection Diode at (13.0, 3.2), angle 0: Pad 1 (Cathode, VCC) at 11.35, Pad 2 (Anode, /BAT_IN) at 14.65
    d1 = place_fp('Diode_SMD', 'D_SOD-123', 'D1', 'BAT54', 13.0, 3.2, 0)
    set_net(d1, 1, 'VCC')
    set_net(d1, 2, '/BAT_IN')

    # D3 LED at (8.0, 2.5), angle 0: Pad 1 (Cathode) at 7.05, Pad 2 (Anode) at 8.95
    d3 = place_fp('LED_SMD', 'LED_0805_2012Metric', 'D3', 'LED', 8.0, 2.5, 0)
    set_net(d3, 1, 'GND')
    set_net(d3, 2, 'Net-(D3-Pad2)')

    # R4 LED Resistor at (8.95, 5.5), angle 90: Pad 2 (Top) at 4.725, Pad 1 (Bottom, VCC) at 6.275
    r4 = place_fp('Resistor_SMD', 'R_0603_1608Metric', 'R4', '2.2k', 8.95, 5.5, 90)
    set_net(r4, 1, 'VCC')
    set_net(r4, 2, 'Net-(D3-Pad2)')

    # =========================================================================
    # 5. RF Input Matching Section (Pre-Filter BPF + 50R Match):
    # =========================================================================
    # C2 Shunt Cap (27pF, 0603) at (5.8, 20.5), angle 270 (Pad 1 at Y=19.7, Pad 2 at Y=21.3)
    c2 = place_fp('Capacitor_SMD', 'C_0603_1608Metric', 'C2', '27pF', 5.8, 20.5, 270)
    set_net(c2, 1, '/RF_IN_50R')
    set_net(c2, 2, 'GND')

    # L1 Shunt Inductor (22nH, 0603) at (7.8, 20.5), angle 270
    l1 = place_fp('Inductor_SMD', 'L_0603_1608Metric', 'L1', '22nH', 7.8, 20.5, 270)
    set_net(l1, 1, '/RF_IN_50R')
    set_net(l1, 2, 'GND')

    # C1 Series Cap (91pF, 0805) at (10.5, 17.95), angle 0 (Pad 1 at 9.55, Pad 2 at 11.45)
    c1 = place_fp('Capacitor_SMD', 'C_0805_2012Metric', 'C1', '91pF', 10.5, 17.95, 0)
    set_net(c1, 1, '/RF_IN_50R')
    set_net(c1, 2, '/EMITTER')

    # =========================================================================
    # 6. Active Stage Q1 (MMBT5179, SOT-23) at (15.5, 17.00), angle 0
    # =========================================================================
    # Pad 1 (Base): (14.55, 18.10)
    # Pad 2 (Emitter): (14.55, 15.90) -- wait! Let's check rotation:
    # If angle is 180: Pad 1 (Base) is at (16.45, 15.90), Pad 2 (Emitter) is at (16.45, 18.10), Pad 3 (Collector) at (14.55, 17.00)
    # Standard angle 0: Pad 1 (Base) is (14.55, 18.10), Pad 2 (Emitter) is (14.55, 15.90), Pad 3 is (16.45, 17.00)
    # Let's rotate Q1 by 180 degrees so Emitter faces west towards C1 at Y=17.95, or keep angle 0?
    # Let's check: in the original script:
    # q1 was at (15.5, 14.50, angle 0):
    # c1 was at (10.5, 15.45, angle 0): Pad 2 was at (11.45, 15.45)
    # q1 pad 2 (Emitter) was at (14.55, 13.40) or (14.55, 15.60)?
    # Let's check pad_pos(q1, 2) in python!
    q1 = place_fp('Package_TO_SOT_SMD', 'SOT-23', 'Q1', 'MMBT5179', 15.5, 17.00, 0)
    set_net(q1, 1, '/BASE')
    set_net(q1, 2, '/EMITTER')
    set_net(q1, 3, '/COLLECTOR')

    # Emitter RFC & Bias Resistor:
    # L2 RFC at (13.0, 22.0), angle 270: Pad 1 at Y=21.2, Pad 2 at Y=22.8
    l2 = place_fp('Inductor_SMD', 'L_0603_1608Metric', 'L2', '470nH', 13.0, 22.0, 270)
    set_net(l2, 1, '/EMITTER')
    set_net(l2, 2, 'Net-(L2-Pad2)')

    # R3 Emitter Bias Resistor at (13.0, 25.0), angle 270: Pad 1 at Y=24.2, Pad 2 at Y=25.8
    r3 = place_fp('Resistor_SMD', 'R_0603_1608Metric', 'R3', '200R', 13.0, 25.0, 270)
    set_net(r3, 1, 'Net-(L2-Pad2)')
    set_net(r3, 2, 'GND')

    # Base Bypass & Bias Network (North side: Y in [11.0, 14.0]):
    c3 = place_fp('Capacitor_SMD', 'C_0805_2012Metric', 'C3', '100pF', 14.562, 13.55, 90)
    set_net(c3, 1, '/BASE')
    set_net(c3, 2, 'GND')

    c4 = place_fp('Capacitor_SMD', 'C_0805_2012Metric', 'C4', '1nF', 12.2, 13.55, 90)
    set_net(c4, 1, '/BASE')
    set_net(c4, 2, 'GND')

    c5 = place_fp('Capacitor_SMD', 'C_0805_2012Metric', 'C5', '100nF', 9.8, 13.55, 90)
    set_net(c5, 1, '/BASE')
    set_net(c5, 2, 'GND')

    r2 = place_fp('Resistor_SMD', 'R_0603_1608Metric', 'R2', '3.3k', 7.8, 13.725, 90)
    set_net(r2, 1, '/BASE')
    set_net(r2, 2, 'GND')

    r1 = place_fp('Resistor_SMD', 'R_0603_1608Metric', 'R1', '3.9k', 6.2, 13.725, 90)
    set_net(r1, 1, '/BASE')
    set_net(r1, 2, 'VCC')

    # =========================================================================
    # 7. Collector Tuned Tank & Output Matching:
    # =========================================================================
    # L3 Collector Inductor at (19.0, 13.725), angle 90: Pad 1 at Y=14.5, Pad 2 at Y=12.95
    l3 = place_fp('Inductor_SMD', 'L_0603_1608Metric', 'L3', '150nH', 19.0, 13.725, 90)
    set_net(l3, 1, '/COLLECTOR')
    set_net(l3, 2, 'VCC')

    # C6 Collector Tuning Cap at (19.0, 20.5), angle 270: Pad 1 at Y=19.55, Pad 2 at Y=21.45
    c6 = place_fp('Capacitor_SMD', 'C_0805_2012Metric', 'C6', '6.8pF', 19.0, 20.5, 270)
    set_net(c6, 1, '/COLLECTOR')
    set_net(c6, 2, 'GND')

    # C7 Output Coupling Cap at (22.0, 17.00), angle 0 (Horizontal on RF line):
    c7 = place_fp('Capacitor_SMD', 'C_0805_2012Metric', 'C7', '10pF', 22.0, 17.00, 0)
    set_net(c7, 1, '/COLLECTOR')
    set_net(c7, 2, '/RF_OUT_50R')

    # =========================================================================
    # 8. Bias Tee Section:
    # =========================================================================
    # L4 Bias Tee Choke at (25.0, 14.00), angle 0 (Horizontal):
    l4 = place_fp('Inductor_SMD', 'L_0603_1608Metric', 'L4', '1uH', 25.0, 14.00, 0)
    set_net(l4, 1, '/RF_OUT_50R')
    set_net(l4, 2, '/BIAS_TEE_DC')

    # C10 10nF Bias Tee Low-Freq Bypass at (24.0, 11.1), angle 90:
    c10 = place_fp('Capacitor_SMD', 'C_0805_2012Metric', 'C10', '10nF', 24.0, 11.1, 90)
    set_net(c10, 1, '/BIAS_TEE_DC')
    set_net(c10, 2, 'GND')
    c10.FindPadByNumber('2').SetLocalZoneConnection(pcbnew.ZONE_CONNECTION_FULL)

    # C9 100pF Bias Tee RF Bypass at (26.5, 11.1), angle 90:
    c9 = place_fp('Capacitor_SMD', 'C_0805_2012Metric', 'C9', '100pF', 26.5, 11.1, 90)
    set_net(c9, 1, '/BIAS_TEE_DC')
    set_net(c9, 2, 'GND')
    c9.FindPadByNumber('2').SetLocalZoneConnection(pcbnew.ZONE_CONNECTION_FULL)

    # D2 BAT54 Bias Tee Isolation Diode at (26.0, 4.0), angle 0:
    d2 = place_fp('Diode_SMD', 'D_SOD-123', 'D2', 'BAT54', 26.0, 4.0, 0)
    set_net(d2, 1, 'VCC')
    set_net(d2, 2, '/BIAS_TEE_DC')

    # JP1 Solder Jumper at (26.0, 6.5), angle 180:
    jp1 = place_fp('Jumper', 'SolderJumper-2_P1.3mm_Open_RoundedPad1.0x1.5mm', 'JP1', 'SolderJumper_Open', 26.0, 6.5, 180)
    set_net(jp1, 1, '/BIAS_TEE_DC')
    set_net(jp1, 2, 'VCC')

    # =========================================================================
    # 9. Power Decoupling (VCC Bulk & High-Frequency)
    # =========================================================================
    c11 = place_fp('Capacitor_SMD', 'C_0805_2012Metric', 'C11', '10uF', 13.0, 8.5, 270)
    set_net(c11, 1, 'VCC')
    set_net(c11, 2, 'GND')

    c12 = place_fp('Capacitor_SMD', 'C_0603_1608Metric', 'C12', '100nF', 15.5, 8.5, 270)
    set_net(c12, 1, 'VCC')
    set_net(c12, 2, 'GND')

    # =========================================================================
    # COPPER TRACE ROUTING
    # =========================================================================
    # 1. /RF_IN_50R: Continuous 50-ohm CPWG line (width 1.5mm) along Y=17.00
    p_j1_1 = pad_pos(j1, 1)
    p_c2_1 = pad_pos(c2, 1)
    p_l1_1 = pad_pos(l1, 1)
    p_c1_1 = pad_pos(c1, 1)

    add_seg(p_j1_1[0], 17.00, 7.8, 17.00, 1.5, '/RF_IN_50R')
    add_seg(5.8, 17.00, p_c2_1[0], p_c2_1[1], 0.6, '/RF_IN_50R')
    add_seg(7.8, 17.00, p_l1_1[0], p_l1_1[1], 0.6, '/RF_IN_50R')
    add_seg(7.8, 17.00, 8.75, 17.95, 0.6, '/RF_IN_50R')
    add_seg(8.75, 17.95, p_c1_1[0], 17.95, 0.6, '/RF_IN_50R')

    # 2. /EMITTER: From C1 pad 2 straight into Q1 Emitter pad 2
    p_c1_2 = pad_pos(c1, 2)
    p_q1_2 = pad_pos(q1, 2)
    p_l2_1 = pad_pos(l2, 1)
    add_seg(p_c1_2[0], p_c1_2[1], p_q1_2[0], p_q1_2[1], 0.5, '/EMITTER')
    add_seg(p_c1_2[0], p_c1_2[1], p_l2_1[0], p_l2_1[1], 0.4, '/EMITTER')

    # 3. Net-(L2-Pad2): L2 to R3
    p_l2_2 = pad_pos(l2, 2)
    p_r3_1 = pad_pos(r3, 1)
    add_seg(p_l2_2[0], p_l2_2[1], p_r3_1[0], p_r3_1[1], 0.4, 'Net-(L2-Pad2)')

    # 4. /BASE: Base bus along Y=14.50 connecting Q1.1, C3, C4, C5, R2, R1
    p_q1_1 = pad_pos(q1, 1)
    p_c3_1 = pad_pos(c3, 1)
    p_c4_1 = pad_pos(c4, 1)
    p_c5_1 = pad_pos(c5, 1)
    p_r2_1 = pad_pos(r2, 1)
    p_r1_1 = pad_pos(r1, 1)
    add_seg(p_q1_1[0], p_q1_1[1], p_q1_1[0], 14.50, 0.5, '/BASE')
    add_seg(p_r1_1[0], 14.50, p_q1_1[0], 14.50, 0.4, '/BASE')

    # 5. /COLLECTOR: Resonant tank node at (19.0, 17.00)
    p_q1_3 = pad_pos(q1, 3)
    p_c7_1 = pad_pos(c7, 1)
    p_l3_1 = pad_pos(l3, 1)
    p_c6_1 = pad_pos(c6, 1)
    add_seg(p_q1_3[0], 17.00, p_c7_1[0], 17.00, 0.5, '/COLLECTOR')
    add_seg(19.0, 17.00, p_l3_1[0], p_l3_1[1], 0.5, '/COLLECTOR')
    add_seg(19.0, 17.00, p_c6_1[0], p_c6_1[1], 0.5, '/COLLECTOR')

    # 6. /RF_OUT_50R: Output 50-ohm CPWG line (width 1.5mm) along Y=17.00
    p_c7_2 = pad_pos(c7, 2)
    p_j2_1 = pad_pos(j2, 1)
    p_l4_1 = pad_pos(l4, 1)
    add_seg(p_c7_2[0], 17.00, p_j2_1[0], 17.00, 1.5, '/RF_OUT_50R')
    add_seg(p_l4_1[0], 17.00, p_l4_1[0], p_l4_1[1], 0.5, '/RF_OUT_50R')

    # 7. /BIAS_TEE_DC: L4 to C10, C9, JP1, D2
    p_l4_2 = pad_pos(l4, 2)
    p_c10_1 = pad_pos(c10, 1)
    p_c9_1 = pad_pos(c9, 1)
    p_d2_2 = pad_pos(d2, 2)
    p_jp1_1 = pad_pos(jp1, 1)
    # L4.2 (25.788, 14.0) up to horizontal bus at Y=12.05
    add_seg(p_l4_2[0], p_l4_2[1], p_l4_2[0], 12.05, 0.4, '/BIAS_TEE_DC')
    add_seg(p_c10_1[0], p_c10_1[1], p_c9_1[0], p_c9_1[1], 0.4, '/BIAS_TEE_DC')
    add_seg(p_c9_1[0], p_c9_1[1], 27.65, 12.05, 0.4, '/BIAS_TEE_DC')
    add_seg(27.65, 12.05, p_d2_2[0], p_d2_2[1], 0.4, '/BIAS_TEE_DC')
    add_seg(p_jp1_1[0], p_jp1_1[1], 27.65, p_jp1_1[1], 0.4, '/BIAS_TEE_DC')

    # 8. /BAT_IN: J3 pad 1 (17.23, 3.2) to D1 pad 2 (14.65, 3.2)
    p_j3_1 = pad_pos(j3, 1)
    p_d1_2 = pad_pos(d1, 2)
    add_seg(p_j3_1[0], p_j3_1[1], p_d1_2[0], p_d1_2[1], 0.6, '/BAT_IN')

    # 9. Net-(D3-Pad2): R4 pad 2 to D3 pad 2
    p_r4_2 = pad_pos(r4, 2)
    p_d3_2 = pad_pos(d3, 2)
    add_seg(p_r4_2[0], p_r4_2[1], p_d3_2[0], p_d3_2[1], 0.35, 'Net-(D3-Pad2)')

    # 10. VCC Rail: Main bus at Y=7.5 from X=6.2 across to X=24.35
    p_r1_2 = pad_pos(r1, 2)
    p_d1_1 = pad_pos(d1, 1)
    p_l3_2 = pad_pos(l3, 2)
    p_c11_1 = pad_pos(c11, 1)
    p_c12_1 = pad_pos(c12, 1)
    p_r4_1 = pad_pos(r4, 1)
    p_d2_1 = pad_pos(d2, 1)
    p_jp1_2 = pad_pos(jp1, 2)

    add_seg(p_r1_2[0], 7.5, 24.35, 7.5, 0.5, 'VCC')
    add_seg(p_r1_2[0], p_r1_2[1], p_r1_2[0], 7.5, 0.4, 'VCC')
    add_seg(p_r4_1[0], p_r4_1[1], p_r4_1[0], 7.5, 0.4, 'VCC')
    add_seg(p_d1_1[0], p_d1_1[1], p_d1_1[0], 7.5, 0.6, 'VCC')
    add_seg(p_c11_1[0], p_c11_1[1], p_c11_1[0], 7.5, 0.5, 'VCC')
    add_seg(p_c12_1[0], p_c12_1[1], p_c12_1[0], 7.5, 0.5, 'VCC')
    add_seg(p_l3_2[0], p_l3_2[1], p_l3_2[0], 7.5, 0.5, 'VCC')

    # Vertical VCC trace from Y=7.5 north along X=24.35 to D2.1 (24.35, 4.0) and branch to JP1.2 (25.35, 6.5)
    add_seg(24.35, 7.5, p_d2_1[0], p_d2_1[1], 0.5, 'VCC')
    add_seg(24.35, p_jp1_2[1], p_jp1_2[0], p_jp1_2[1], 0.4, 'VCC')

    # =========================================================================
    # GROUND CONNECTIONS & VIAS
    # =========================================================================
    def connect_gnd(fp, pad_num, via_x, via_y):
        pos = pad_pos(fp, pad_num)
        add_via(via_x, via_y, 'GND')
        add_seg(pos[0], pos[1], via_x, via_y, 0.4, 'GND')

    connect_gnd(c2, 2, 5.8, 23.0)
    connect_gnd(l1, 2, 7.8, 23.0)
    connect_gnd(r3, 2, 13.0, 27.2)
    connect_gnd(c3, 2, 14.562, 11.0)
    connect_gnd(c4, 2, 12.2, 11.0)
    connect_gnd(c5, 2, 9.8, 11.0)
    connect_gnd(r2, 2, 7.8, 11.0)
    connect_gnd(c6, 2, 19.0, 23.0)
    add_via(25.25, 10.15, 'GND')
    add_seg(24.0, 10.15, 26.5, 10.15, 0.4, 'GND')

    connect_gnd(c11, 2, 13.0, 11.0)
    connect_gnd(c12, 2, 15.5, 11.0)
    connect_gnd(d3, 1, 5.5, 2.5)

    # =========================================================================
    # RF VIA FENCING & BOARD STITCHING
    # =========================================================================
    rf_fence = [
        # --- 1. RF Input CPWG Fencing (J1 to Q1 Emitter) ---
        (2.0, 14.5),
        (2.0, 19.5), (4.0, 19.5), (9.8, 20.0),

        # --- 2. Q1 Stage Flanking Vias ---
        (16.5, 14.5), (16.5, 19.5),
        (21.0, 14.5), (21.0, 19.5),

        # --- 3. 50-Ohm Output CPWG Fencing (C7 to J2 SMA) ---
        # North Side (Y = 14.5 mm)
        (22.5, 14.5), (28.5, 14.5),
        # South Side (Y = 19.5 mm)
        (23.5, 19.5), (26.0, 19.5), (28.5, 19.5),

        # --- 4. Perimeter Ground Stitching ---
        # South Ground Zone (Y = 27.2 mm)
        (6.0, 27.2), (9.5, 27.2), (16.5, 27.2), (19.5, 27.2), (23.0, 27.2), (26.5, 27.2),
        # North Ground Zone (Y = 1.0 mm)
        (4.0, 1.0), (13.0, 1.0), (22.0, 1.0), (29.0, 1.0),
        # Left Edge Stitching (X = 1.5 mm)
        (1.5, 6.0), (1.5, 9.0), (1.5, 12.0), (1.5, 22.0),
        # Right Edge Stitching (X = 32.5 mm)
        (32.5, 6.0), (32.5, 9.0), (32.5, 12.0), (32.5, 22.0)
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
        # Bounded by rectangular envelope (filler will clip against Edge.Cuts)
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
    add_text('IN 50R', 4.5, 9.5, 0.80, 0.13)
    add_text('OUT 50R', 30.0, 8.0, 0.80, 0.13)

    add_text('+', 17.23, 1.2, 0.80, 0.13)
    add_text('-', 19.77, 1.2, 0.80, 0.13)
    add_text('BAT', 17.23, 5.8, 0.80, 0.13)
    add_text('GND', 19.77, 5.8, 0.80, 0.13)

    silk_map = {
        'C2':  (5.8, 24.2, 0.80, 0.13),
        'L1':  (9.2, 20.5, 0.80, 0.13),
        'C1':  (10.5, 16.5, 0.80, 0.13),
        'Q1':  (17.5, 18.5, 0.80, 0.13),
        'L2':  (11.6, 22.0, 0.80, 0.13),
        'R3':  (11.6, 25.0, 0.80, 0.13),
        'C3':  (16.0, 13.55, 0.80, 0.13),
        'C4':  (12.2, 16.3, 0.80, 0.13),
        'C5':  (9.8, 10.0, 0.80, 0.13),
        'R2':  (7.8, 16.3, 0.80, 0.13),
        'R1':  (5.0, 13.5, 0.80, 0.13),
        'L3':  (20.5, 13.7, 0.80, 0.13),
        'C6':  (20.8, 20.5, 0.80, 0.13),
        'C7':  (22.0, 18.5, 0.80, 0.13),
        'L4':  (25.0, 15.5, 0.80, 0.13),
        'C9':  (28.2, 11.1, 0.80, 0.13),
        'C10': (22.2, 11.1, 0.80, 0.13),
        'D2':  (26.0, 2.3, 0.80, 0.13),
        'JP1': (29.5, 6.5, 0.80, 0.13),
        'D1':  (13.0, 1.0, 0.80, 0.13),
        'C11': (11.4, 8.5, 0.80, 0.13),
        'C12': (17.5, 10.0, 0.80, 0.13),
        'R4':  (7.4, 5.5, 0.80, 0.13),
        'D3':  (5.8, 4.5, 0.80, 0.13),
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

    pcbnew.SaveBoard(r'd:\Workspace\rf\lna-ai\lna_fm_98mhz.kicad_pcb', board)
    print('Clean PCB successfully built and saved to lna_fm_98mhz.kicad_pcb!')

if __name__ == '__main__':
    build_pcb()
