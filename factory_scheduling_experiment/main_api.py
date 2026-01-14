# main_api.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

from factory_scheduling_experiment.models import Machine, Mold, ProductComponent
from factory_scheduling_experiment.ga_scheduler import ga_optimize_v2

app = FastAPI(title="Injection Molding Monthly Planning API")


# ----------------------------
# Pydantic Schemas (Input)
# ----------------------------

class MachineIn(BaseModel):
    id: str
    name: str
    group: str = Field(..., description="small | medium | large")
    tonnage: int
    hours_per_day: float = 21.0
    efficiency: float = 0.85


class MoldIn(BaseModel):
    id: str
    name: str
    group: str = Field(..., description="small | medium | large")
    tonnage: int


class ComponentIn(BaseModel):
    id: str
    name: str
    quantity: int
    cycle_time_sec: float
    mold_id: str
    color: str
    due_day: int
    lead_time_days: int = 2
    prerequisites: List[str] = []
    status: str = "pending"


class ScheduleV2Request(BaseModel):
    month_days: int = 30
    machines: List[MachineIn]
    molds: List[MoldIn]
    components: List[ComponentIn]

    pop_size: int = 30
    n_generations: int = 80
    mutation_rate: float = 0.25


# ----------------------------
# API Endpoint
# ----------------------------

@app.post("/schedule_v2")
def schedule_v2(request: ScheduleV2Request) -> Dict[str, Any]:
    try:
        machines = [Machine(**m.model_dump()) for m in request.machines]
        molds = [Mold(**m.model_dump()) for m in request.molds]
        components = [ProductComponent(**c.model_dump()) for c in request.components]

        result = ga_optimize_v2(
            components=components,
            machines=machines,
            molds=molds,
            month_days=request.month_days,
            pop_size=request.pop_size,
            n_generations=request.n_generations,
            mutation_rate=request.mutation_rate,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))