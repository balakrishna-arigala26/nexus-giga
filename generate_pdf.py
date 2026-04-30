import os
from fpdf import FPDF

# Ensure the data directory exists
os.makedirs("data", exist_ok=True)

class PDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 14)
        self.cell(0, 10, 'Nexus-Giga Heavy Industires', 0, 1, 'C')
        self.set_font('Arial', 'I', 10)
        self.cell(0, 10, 'V-101 Vacuum Gripper - Technical & Maintenance Manual', 0, 1, 'C')
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')

def create_manual():
    pdf = PDF()
    pdf.add_page()
    pdf.set_font('Arial', '', 11)

    # Document Content
    manual_content = """
1. SYSTEM OVERVIEW
The V-101 Vacuum Gripper is a heavy-duty pneumatic end-effector designed for robotic palletizing applications. it operates on a standard 80 PSI factrory air supply and utilizes vacuum generator to achieve rapid suction across its 4-pad array.

Specifications:
- Maximum Payload: 50 kg
- Operating Pressure: 80-100 PSI
- Connection Type: ISO 9409-1-50-4-M6
- Optimal Operating Temperature: 5°C to 45°C

2. DIAGNOSTIC ERROR CODES
When the V-101 contorl unit detects an anomaly, it will broadcast specific error code to the main factory telemetry system:

- ERROR-V101-01 (Low Vacuum Pressure): Indicates a leak in the pneumatic lines or a worn suction pad. If pressure dropsbelow 60 PSI, the system auto-halts.
- ERROR-V101-02 (Solenoid Valve Failure): The directional control valve is stuck. Reuires immediate manual override and replacement of the 24V DC solenoid coil.
- ERROR-V101-03 (Filter Clog): The intake particulate filter is severely restricted. Suction time will increase.

3. MAINTENANCE PROCEDURES
Routine maintenance is critical to prevent catasrophic payload drops.

Replacing Suction Pads (Monthly):
1. Power down the robotic arm and look out the pneumatic air supply.
2. Unthread the M8 retaining nut on the top of the worn suction pad.
3. Remove the pad and inspect the internal mesh screen for debris.
4. Install the new polyurethane pad and tighten the nut to 12 Nm torque.

Cleaning the Venturi Generator (Quarterly):
1. Disconnect the primary air intake hose.
2. Remove the 4 hex bolts securing the Venturi block to the main chassis.
3. Sumerge the block in indusrtial solvent for 15 minutes.
4. Blow out the internal nozzle with compressed air before reassembly.
"""

    # Write content to PDF, handling newlines
    for line in manual_content.split('\n'):
        pdf.multi_cell(0, 8, line)

    # Save the file
    file_path = os.path.join("data", "V-101_Vacuum_Gripper_Manual.pdf")
    pdf.output(file_path)
    print(f"✅ Successfully generated: {file_path}")

if __name__ == "__main__":
    create_manual()
