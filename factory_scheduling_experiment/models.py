# models.py

class Machine:
    def __init__(self, id, name, type, capabilities, workers, max_op_time, cooldown, defect_rate, prod_rate, status):
        self.id = id
        self.name = name
        self.type = type
        self.capabilities = capabilities  # list of strings
        self.workers = workers
        self.max_op_time = max_op_time
        self.cooldown = cooldown
        self.defect_rate = defect_rate
        self.prod_rate = prod_rate
        self.status = status

class ProductComponent:
    def __init__(self, id, name, quantity, steps, total_time, required_machines, prerequisites, status):
        self.id = id
        self.name = name
        self.quantity = quantity
        self.steps = steps
        self.total_time = total_time
        self.required_machines = required_machines  # list of machine names
        self.prerequisites = prerequisites  # list of component IDs
        self.status = status