from .models import Machine, ProductComponent

def get_sample_machines():
    return [
        Machine(
            id="M001",
            name="SMT Line 1",
            type="Assembly",
            capabilities=["Soldering"],
            workers=2,
            max_op_time=480,
            cooldown=10,
            defect_rate=0.5,
            prod_rate=45,
            status="Active"
        ),
        Machine(
            id="M002",
            name="Testing Station",
            type="Testing",
            capabilities=["Testing"],
            workers=1,
            max_op_time=480,
            cooldown=5,
            defect_rate=0.2,
            prod_rate=60,
            status="Active"
        ),
        Machine(
            id="M003",
            name="Packaging",
            type="Packaging",
            capabilities=["Packing"],
            workers=1,
            max_op_time=480,
            cooldown=5,
            defect_rate=0.1,
            prod_rate=80,
            status="Active"
        ),
    ]

def get_sample_components():
    return [
        ProductComponent(
            id="P001",
            name="Control Board",
            quantity=1,
            steps=3,
            total_time=40,
            required_machines=["SMT Line 1", "Testing Station"],
            prerequisites=[],
            status="Active"
        ),
        ProductComponent(
            id="P002",
            name="Power Module",
            quantity=1,
            steps=2,
            total_time=30,
            required_machines=["SMT Line 1"],
            prerequisites=["P001"],
            status="Active"
        ),
        ProductComponent(
            id="P003",
            name="Display Unit",
            quantity=1,
            steps=2,
            total_time=30,
            required_machines=["Testing Station"],
            prerequisites=["P001"],
            status="Active"
        ),
        ProductComponent(
            id="P004",
            name="Final Assembly",
            quantity=1,
            steps=4,
            total_time=50,
            required_machines=["Packaging"],
            prerequisites=["P002", "P003"],
            status="Active"
        ),
    ]