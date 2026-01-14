# ga_scheduler.py
import random
from dataclasses import dataclass
from typing import Dict, List, Tuple, Any, Optional

from factory_scheduling_experiment.models import Machine, Mold, ProductComponent


@dataclass
class DayAssignment:
    day: int
    machine_id: str
    machine_name: str
    mold_id: str
    component_id: str
    component_name: str
    color: str
    produced_qty: int
    used_hours: float
    utilization: float  # 0..1


def _machine_capacity_qty_per_day(machine: Machine, cycle_time_sec: float) -> int:
    if cycle_time_sec <= 0:
        return 0
    effective_seconds = machine.hours_per_day * 3600.0 * machine.efficiency
    return int(effective_seconds // cycle_time_sec)


def _topological_order(components: List[ProductComponent]) -> List[ProductComponent]:
    """
    Simple Kahn topological sort. Raises if circular deps.
    """
    by_id = {c.id: c for c in components}
    indeg = {c.id: 0 for c in components}
    graph = {c.id: [] for c in components}

    for c in components:
        for pr in c.prerequisites:
            if pr not in by_id:
                # allow missing prereq ids to fail early
                raise ValueError(f"Prerequisite '{pr}' not found for component '{c.id}'.")
            graph[pr].append(c.id)
            indeg[c.id] += 1

    queue = [cid for cid, d in indeg.items() if d == 0]
    order_ids = []
    while queue:
        cid = queue.pop(0)
        order_ids.append(cid)
        for nxt in graph[cid]:
            indeg[nxt] -= 1
            if indeg[nxt] == 0:
                queue.append(nxt)

    if len(order_ids) != len(components):
        raise ValueError("Circular dependency detected in prerequisites.")

    return [by_id[cid] for cid in order_ids]


def _feasible_machine_ids_for_component(
    comp: ProductComponent,
    machines: List[Machine],
    molds_by_id: Dict[str, Mold],
) -> List[str]:
    if comp.mold_id not in molds_by_id:
        return []
    mold = molds_by_id[comp.mold_id]
    feasible = []
    for m in machines:
        if m.group != mold.group:
            continue
        if mold.tonnage > m.tonnage:
            continue
        feasible.append(m.id)
    return feasible


def _decode_v2(
    genome: List[str],
    components: List[ProductComponent],
    machines: List[Machine],
    molds: List[Mold],
    month_days: int,
) -> Tuple[List[DayAssignment], Dict[str, int], Dict[str, Any]]:
    """
    Daily bucket decode with constraints:
      - mold exclusive per day
      - machine runs at most 1 component per day (simple color rule)
      - mold must match machine group, mold tonnage <= machine tonnage
      - prerequisites: component can only start after all prereqs finished (day-based)
      - due_day & lead_time_days -> latest_start_day = due_day - lead_time_days
    genome: list of component ids (order preference)
    """
    comps_by_id = {c.id: c for c in components}
    molds_by_id = {m.id: m for m in molds}
    machines_by_id = {m.id: m for m in machines}

    # Use topo order as base, then stable-sort by genome preference.
    topo = _topological_order(components)
    rank = {cid: i for i, cid in enumerate(genome)}
    ordered = sorted(topo, key=lambda c: rank.get(c.id, 10**9))

    remaining = {c.id: int(c.quantity) for c in components}
    finished_day: Dict[str, int] = {}  # component_id -> day it reached full qty

    # day -> machine_id -> assignment (one per day)
    used_machine_day = {day: set() for day in range(1, month_days + 1)}
    used_mold_day = {day: set() for day in range(1, month_days + 1)}

    assignments: List[DayAssignment] = []

    for comp in ordered:
        if comp.id not in remaining or remaining[comp.id] <= 0:
            continue

        feasible_machine_ids = _feasible_machine_ids_for_component(comp, machines, molds_by_id)
        if not feasible_machine_ids:
            # can't produce at all
            continue

        # prerequisites end day => earliest day we can start = max(finished_day[pr]) + 1
        if comp.prerequisites:
            if any(pr not in finished_day for pr in comp.prerequisites):
                # prereqs not producible/produced => can't do this comp
                continue
            earliest = max(finished_day[pr] for pr in comp.prerequisites) + 1
        else:
            earliest = 1

        latest_start = comp.due_day - comp.lead_time_days
        if latest_start < 1:
            latest_start = 1

        # We are allowed to produce before latest_start too; the "lead time" is a latest-start rule.
        # We'll try to schedule from earliest forward, but penalize if we start after latest_start.
        mold_id = comp.mold_id
        color = comp.color

        day = earliest
        while day <= month_days and remaining[comp.id] > 0:
            # pick a machine available today
            chosen_machine_id: Optional[str] = None
            for mid in feasible_machine_ids:
                if mid in used_machine_day[day]:
                    continue
                if mold_id in used_mold_day[day]:
                    continue
                chosen_machine_id = mid
                break

            if chosen_machine_id is None:
                day += 1
                continue

            machine = machines_by_id[chosen_machine_id]
            cap_qty = _machine_capacity_qty_per_day(machine, comp.cycle_time_sec)
            if cap_qty <= 0:
                break

            produce = min(remaining[comp.id], cap_qty)
            used_seconds = produce * float(comp.cycle_time_sec)
            used_hours = used_seconds / 3600.0
            util = 0.0
            denom = machine.hours_per_day * machine.efficiency
            if denom > 0:
                util = min(1.0, used_hours / denom)

            assignments.append(
                DayAssignment(
                    day=day,
                    machine_id=machine.id,
                    machine_name=machine.name,
                    mold_id=mold_id,
                    component_id=comp.id,
                    component_name=comp.name,
                    color=color,
                    produced_qty=produce,
                    used_hours=used_hours,
                    utilization=util,
                )
            )

            used_machine_day[day].add(chosen_machine_id)
            used_mold_day[day].add(mold_id)
            remaining[comp.id] -= produce

            if remaining[comp.id] <= 0:
                finished_day[comp.id] = day

            day += 1

    unmet = {cid: qty for cid, qty in remaining.items() if qty > 0}

    # diagnostics for penalties
    diag = {
        "finished_day": finished_day,
    }
    return assignments, unmet, diag


def _fitness_v2(
    assignments: List[DayAssignment],
    unmet: Dict[str, int],
    components: List[ProductComponent],
) -> float:
    """
    Higher is better.
    Penalize unmet qty heavily.
    Penalize late starts (starting after due_day - lead_time_days).
    Reward more produced & higher utilization a bit.
    """
    comps_by_id = {c.id: c for c in components}

    produced_total = sum(a.produced_qty for a in assignments)
    unmet_pen = sum(unmet.values()) * 1_000_000.0

    # compute first production day per component
    first_day: Dict[str, int] = {}
    for a in assignments:
        first_day[a.component_id] = min(first_day.get(a.component_id, 10**9), a.day)

    late_start_pen = 0.0
    for cid, fd in first_day.items():
        c = comps_by_id[cid]
        latest_start = c.due_day - c.lead_time_days
        if latest_start < 1:
            latest_start = 1
        if fd > latest_start:
            late_start_pen += (fd - latest_start) * 10_000.0

    util_reward = sum(a.utilization for a in assignments) * 10.0

    return produced_total + util_reward - unmet_pen - late_start_pen


def _random_genome(components: List[ProductComponent]) -> List[str]:
    ids = [c.id for c in components]
    random.shuffle(ids)
    return ids


def _mutate_swap(genome: List[str]) -> List[str]:
    if len(genome) < 2:
        return genome
    i, j = random.sample(range(len(genome)), 2)
    genome[i], genome[j] = genome[j], genome[i]
    return genome


def _crossover_ox(p1: List[str], p2: List[str]) -> List[str]:
    # order crossover
    n = len(p1)
    if n < 2:
        return p1[:]
    a, b = sorted(random.sample(range(n), 2))
    mid = p1[a:b]
    child = [x for x in p2 if x not in mid]
    return child[:a] + mid + child[a:]


def ga_optimize_v2(
    components: List[ProductComponent],
    machines: List[Machine],
    molds: List[Mold],
    month_days: int = 30,
    pop_size: int = 30,
    n_generations: int = 80,
    mutation_rate: float = 0.25,
) -> Dict[str, Any]:
    """
    Returns:
      {
        "assignments": [ ... ],
        "unmet": {component_id: remaining_qty, ...},
        "score": float
      }
    """
    if month_days < 1:
        raise ValueError("month_days must be >= 1")

    population = [_random_genome(components) for _ in range(pop_size)]

    best = None
    best_score = None
    best_pack = None

    for _ in range(n_generations):
        scored = []
        for g in population:
            assigns, unmet, _diag = _decode_v2(g, components, machines, molds, month_days)
            score = _fitness_v2(assigns, unmet, components)
            scored.append((score, g, assigns, unmet))

        scored.sort(key=lambda x: x[0], reverse=True)

        if best_score is None or scored[0][0] > best_score:
            best_score = scored[0][0]
            best = scored[0][1][:]
            best_pack = (scored[0][2], scored[0][3])

        # selection: top-k elitism + tournament fill
        elite_k = max(2, pop_size // 5)
        new_pop = [g[:] for (_, g, _, _) in scored[:elite_k]]

        while len(new_pop) < pop_size:
            i, j = random.sample(range(pop_size), 2)
            g1 = scored[i][1]
            g2 = scored[j][1]
            parent = g1 if scored[i][0] > scored[j][0] else g2
            new_pop.append(parent[:])

        # crossover
        children = []
        for i in range(0, pop_size, 2):
            if i + 1 >= pop_size:
                children.append(new_pop[i][:])
                break
            c1 = _crossover_ox(new_pop[i], new_pop[i + 1])
            c2 = _crossover_ox(new_pop[i + 1], new_pop[i])
            children.extend([c1, c2])

        # mutation
        for i in range(len(children)):
            if random.random() < mutation_rate:
                children[i] = _mutate_swap(children[i][:])

        population = children[:pop_size]

    final_assigns, final_unmet, _diag = _decode_v2(best, components, machines, molds, month_days)
    final_score = _fitness_v2(final_assigns, final_unmet, components)

    return {
        "assignments": [a.__dict__ for a in final_assigns],
        "unmet": final_unmet,
        "score": final_score,
    }