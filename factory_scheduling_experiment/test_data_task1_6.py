from .models import Machine, ProductComponent

# --- Test Case 1: Sample Components (Serial & Forked Dependencies) ---
def get_sample_machines():
    return [
        Machine("M001", "SMT Line 1", "Assembly", ["Soldering"], 2, 480, 10, 0.5, 45, "Active"),
        Machine("M002", "Testing Station", "Testing", ["Testing"], 1, 480, 5, 0.2, 60, "Active"),
        Machine("M003", "Packaging", "Packaging", ["Packing"], 1, 480, 5, 0.1, 80, "Active"),
    ]

def get_sample_components():
    return [
        ProductComponent("P001", "Control Board", 1, 3, 40, ["SMT Line 1", "Testing Station"], [], "Active"),
        ProductComponent("P002", "Power Module", 1, 2, 30, ["SMT Line 1"], ["P001"], "Active"),
        ProductComponent("P003", "Display Unit", 1, 2, 30, ["Testing Station"], ["P001"], "Active"),
        ProductComponent("P004", "Final Assembly", 1, 4, 50, ["Packaging"], ["P002", "P003"], "Active"),
    ]

# --- Test Case 2: Parallelizable Tasks ---
def get_parallel_machines():
    return [
        Machine("M001", "SMT Line 1", "Assembly", ["Soldering"], 2, 480, 10, 0.5, 45, "Active"),
        Machine("M002", "SMT Line 2", "Assembly", ["Soldering"], 2, 480, 10, 0.5, 45, "Active"),
        Machine("M003", "Testing Station", "Testing", ["Testing"], 1, 480, 5, 0.2, 60, "Active"),
    ]

def get_parallel_components():
    return [
        ProductComponent("P001", "Module A", 1, 2, 30, ["SMT Line 1"], [], "Active"),
        ProductComponent("P002", "Module B", 1, 2, 30, ["SMT Line 2"], [], "Active"),
        ProductComponent("P003", "Module C", 1, 2, 30, ["SMT Line 1"], [], "Active"),
        ProductComponent("P004", "Module D", 1, 2, 30, ["SMT Line 2"], [], "Active"),
        ProductComponent("P005", "System Test", 1, 3, 40, ["Testing Station"], ["P001", "P002", "P003", "P004"], "Active"),
    ]

# --- Test Case 3: Resource Contention and Deep Dependencies ---
def get_contention_machines():
    return [
        Machine("M001", "Assembly Line", "Assembly", ["Assembly"], 2, 480, 10, 0.5, 45, "Active"),
        Machine("M002", "Testing Station", "Testing", ["Testing"], 1, 480, 5, 0.2, 60, "Active"),
    ]

def get_contention_components():
    return [
        ProductComponent("P001", "Base Frame", 1, 2, 20, ["Assembly Line"], [], "Active"),
        ProductComponent("P002", "Electronics", 1, 2, 25, ["Assembly Line"], ["P001"], "Active"),
        ProductComponent("P003", "Wiring", 1, 2, 15, ["Assembly Line"], ["P001"], "Active"),
        ProductComponent("P004", "Initial Test", 1, 2, 30, ["Testing Station"], ["P002", "P003"], "Active"),
        ProductComponent("P005", "Final Assembly", 1, 3, 40, ["Assembly Line"], ["P004"], "Active"),
        ProductComponent("P006", "Final Test", 1, 2, 20, ["Testing Station"], ["P005"], "Active"),
    ]