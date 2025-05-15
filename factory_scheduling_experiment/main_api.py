from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any
from factory_scheduling_experiment.ga_scheduler import ga_optimize
from factory_scheduling_experiment.models import Machine, ProductComponent

app = FastAPI(title="Factory Scheduling API")

# --- Pydantic Schemas for Input ---

class MachineIn(BaseModel):
    id: str
    name: str
    type: str
    capabilities: List[str]
    workers: int
    max_op_time: int
    cooldown: int
    defect_rate: float
    prod_rate: int
    status: str

class ComponentIn(BaseModel):
    id: str
    name: str
    quantity: int
    steps: int
    total_time: int
    required_machines: List[str]
    prerequisites: List[str]
    status: str

class ScheduleRequest(BaseModel):
    machines: List[MachineIn]
    components: List[ComponentIn]
    pop_size: int = 20
    n_generations: int = 50
    mutation_rate: float = 0.2

# --- API Endpoint ---

@app.post("/schedule")
def schedule(request: ScheduleRequest):
    try:
        machines = [Machine(**m.dict()) for m in request.machines]
        components = [ProductComponent(**c.dict()) for c in request.components]
        schedule = ga_optimize(
            components, machines,
            pop_size=request.pop_size,
            n_generations=request.n_generations,
            mutation_rate=request.mutation_rate
        )
        # Format output for API
        result = []
        for comp_id, (start, end, name, m_names) in schedule.items():
            result.append({
                "component_id": comp_id,
                "component_name": name,
                "start": start,
                "end": end,
                "machines": m_names
            })
        return {"schedule": result}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))