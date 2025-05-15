from .models import Machine, ProductComponent

def get_sample_machines():
    return [
        Machine("M001", "SMT Line 1", "Assembly", ["Soldering", "Placement"], 2, 480, 30, 0.5, 45, "Active"),
        Machine("M002", "SMT Line 2", "Assembly", ["Soldering", "Placement"], 2, 480, 30, 0.4, 50, "Active"),
        Machine("M003", "Testing Station 1", "Testing", ["Electrical Test"], 1, 300, 20, 0.2, 30, "Active"),
        Machine("M004", "Testing Station 2", "Testing", ["Electrical Test"], 1, 300, 20, 0.2, 30, "Active"),
        Machine("M005", "Final Assembly 1", "Assembly", ["Screwing", "Labeling"], 1, 360, 15, 0.1, 20, "Active"),
        Machine("M006", "Final Assembly 2", "Assembly", ["Screwing", "Labeling"], 1, 360, 15, 0.1, 20, "Active"),
        Machine("M007", "Packaging 1", "Packaging", ["Boxing", "Sealing"], 1, 400, 20, 0.05, 25, "Active"),
        Machine("M008", "Packaging 2", "Packaging", ["Boxing", "Sealing"], 1, 400, 20, 0.05, 25, "Active"),
        Machine("M009", "Burn-in Station 1", "Testing", ["Burn-in"], 1, 200, 10, 0.3, 15, "Active"),
        Machine("M010", "Burn-in Station 2", "Testing", ["Burn-in"], 1, 200, 10, 0.3, 15, "Active"),
        Machine("M011", "Laser Engraver", "Marking", ["Engraving"], 1, 250, 10, 0.1, 10, "Active"),
        Machine("M012", "QC Station", "Quality Control", ["Inspection"], 1, 300, 15, 0.05, 20, "Active"),
    ]

def get_sample_components():
    return [
        ProductComponent("P001", "Control Board", 3, 5, 45, ["SMT Line 1", "Testing Station 1"], [], "Active"),
        ProductComponent("P002", "Power Module", 3, 4, 60, ["SMT Line 2", "Testing Station 2"], [], "Active"),
        ProductComponent("P003", "Display Panel", 3, 3, 40, ["SMT Line 1", "Laser Engraver"], [], "Active"),
        ProductComponent("P004", "Sensor Module", 3, 3, 50, ["SMT Line 2", "Testing Station 1"], [], "Active"),
        ProductComponent("P005", "Wireless Module", 3, 4, 55, ["SMT Line 1", "Testing Station 2"], [], "Active"),
        ProductComponent("P006", "Battery Pack", 3, 2, 35, ["SMT Line 2"], [], "Active"),
        ProductComponent("P007", "Bluetooth Module", 3, 3, 40, ["SMT Line 1", "Testing Station 2"], [], "Active"),
        ProductComponent("P008", "Antenna", 3, 2, 20, ["SMT Line 2"], [], "Active"),
        ProductComponent("P009", "Enclosure", 3, 2, 30, ["Final Assembly 1"], ["P008"], "Active"),
        ProductComponent("P010", "Main Assembly", 3, 6, 90, ["Final Assembly 1", "Final Assembly 2"], ["P001", "P002", "P003", "P004", "P005", "P006", "P007", "P009"], "Active"),
        ProductComponent("P011", "Burn-in Test", 3, 2, 30, ["Burn-in Station 1", "Burn-in Station 2"], ["P010"], "Active"),
        ProductComponent("P012", "Labeling", 3, 1, 15, ["Laser Engraver"], ["P011"], "Active"),
        ProductComponent("P013", "Packaging", 3, 2, 25, ["Packaging 1", "Packaging 2"], ["P012"], "Active"),
        ProductComponent("P014", "Final QC", 3, 2, 20, ["QC Station"], ["P013"], "Active"),
        ProductComponent("P015", "Documentation", 3, 1, 10, ["Packaging 1"], ["P014"], "Active"),
        # Cross-linked dependencies for more complexity
        ProductComponent("P016", "WiFi Module", 3, 3, 35, ["SMT Line 2", "Testing Station 1"], [], "Active"),
        ProductComponent("P017", "GPS Module", 3, 3, 38, ["SMT Line 1", "Testing Station 2"], [], "Active"),
        ProductComponent("P018", "Motherboard", 3, 5, 70, ["Final Assembly 2"], ["P016", "P017"], "Active"),
        ProductComponent("P019", "System Integration", 3, 6, 100, ["Final Assembly 1", "Final Assembly 2"], ["P018", "P010"], "Active"),
        ProductComponent("P020", "Final System Test", 3, 3, 45, ["Testing Station 1", "Testing Station 2"], ["P019"], "Active"),
        ProductComponent("P021", "Final Packaging", 3, 2, 30, ["Packaging 2"], ["P020"], "Active"),
        ProductComponent("P022", "Shipping Prep", 3, 1, 15, ["Packaging 1"], ["P021"], "Active"),
    ]