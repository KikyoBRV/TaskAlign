# ga_scheduler.py
import random
from typing import Dict, List, Tuple, Any, Optional

from models import Machine, Mold, ProductComponent


EPS = 1e-9


def _overlaps(a_start: float, a_end: float, b_start: float, b_end: float) -> bool:
    return not (a_end <= b_start or b_end <= a_start)


def _interval_is_free(intervals: List[Tuple[float, float]], start: float, end: float) -> bool:
    for s, e in intervals:
        if _overlaps(s, e, start, end):
            return False
    return True


def _reserve_interval(intervals: List[Tuple[float, float]], start: float, end: float) -> None:
    intervals.append((start, end))


def _topological_order(components: List[ProductComponent]) -> List[ProductComponent]:
    by_id = {c.id: c for c in components}
    indeg = {c.id: 0 for c in components}
    graph = {c.id: [] for c in components}

    for c in components:
        for pr in c.prerequisites:
            if pr not in by_id:
                raise ValueError(f"Prerequisite '{pr}' not found for component '{c.id}'.")
            graph[pr].append(c.id)
            indeg[c.id] += 1

    queue = [cid for cid, d in indeg.items() if d == 0]
    out = []
    while queue:
        cid = queue.pop(0)
        out.append(by_id[cid])
        for nxt in graph[cid]:
            indeg[nxt] -= 1
            if indeg[nxt] == 0:
                queue.append(nxt)

    if len(out) != len(components):
        raise ValueError("Circular dependency detected in prerequisites.")
    return out


def _feasible_on_machine(comp: ProductComponent, machine: Machine, molds_by_id: Dict[str, Mold]) -> bool:
    mold = molds_by_id.get(comp.mold_id)
    if mold is None:
        return False
    if mold.group != machine.group:
        return False
    if mold.tonnage > machine.tonnage:
        return False
    if comp.cycle_time_sec <= 0:
        return False
    return True


def _can_start_given_prereqs(
    comp: ProductComponent,
    completion_time: Dict[str, Tuple[int, float]],
    day: int,
    start_hour: float,
) -> bool:
    for pr in comp.prerequisites:
        if pr not in completion_time:
            return False
        pr_day, pr_hour = completion_time[pr]
        if (pr_day > day) or (pr_day == day and pr_hour > start_hour + EPS):
            return False
    return True


def _piece_hours(cycle_time_sec: float) -> float:
    return float(cycle_time_sec) / 3600.0


def _next_ready_time_due_to_prereqs(
    comp: ProductComponent,
    completion_time: Dict[str, Tuple[int, float]],
    day: int,
    after_hour: float,
) -> Optional[float]:
    """
    If prereqs are not yet satisfied at (day, after_hour), return the earliest hour on this same day
    when they could become satisfied (i.e., latest prereq completion time on this day).
    If prereqs finish on future days (or missing), return None.
    """
    needed: List[float] = []
    for pr in comp.prerequisites:
        if pr not in completion_time:
            return None
        pr_day, pr_hour = completion_time[pr]
        if pr_day > day:
            return None
        if pr_day == day and pr_hour > after_hour + EPS:
            needed.append(pr_hour)
    if not needed:
        return after_hour
    return max(needed)


def _next_mold_free_time(mold_intervals: List[Tuple[float, float]], after_hour: float) -> Optional[float]:
    """
    Earliest time >= after_hour where the mold is free at an instant (tiny epsilon window).
    """
    if _interval_is_free(mold_intervals, after_hour, after_hour + 1e-6):
        return after_hour

    t = after_hour
    progressed = False
    while True:
        overlapping = [e for (s, e) in mold_intervals if _overlaps(s, e, t, t + 1e-6)]
        if not overlapping:
            return t if progressed else None
        new_t = max(overlapping)
        if new_t <= t + EPS:
            return None
        t = new_t
        progressed = True


def _next_mold_free_time_for_window(
    mold_intervals: List[Tuple[float, float]],
    after_hour: float,
    window_hours: float,
    cap: float,
) -> Optional[float]:
    """
    Earliest t >= after_hour such that [t, t+window_hours] is fully free of mold usage,
    and t+window_hours <= cap.

    This prevents "thrashy" waits to a time where the mold becomes free for a moment but not long enough
    to complete the useful block (e.g. setup + at least 1 piece).
    """
    window_hours = float(window_hours)
    if window_hours <= 0:
        return after_hour if after_hour <= cap + EPS else None

    # If already free for the whole required window, return immediately.
    if after_hour + window_hours <= cap + EPS and _interval_is_free(mold_intervals, after_hour, after_hour + window_hours):
        return after_hour

    t = after_hour
    safety = 0
    while t + window_hours <= cap + EPS:
        safety += 1
        if safety > 10_000:
            return None

        overlaps = [(s, e) for (s, e) in mold_intervals if _overlaps(s, e, t, t + window_hours)]
        if not overlaps:
            return t

        # Jump to the latest end among all overlapping intervals, then retry
        t = max(e for (_s, e) in overlaps)

    return None


def _next_busy_start(intervals: List[Tuple[float, float]], after_hour: float) -> Optional[float]:
    starts = [s for (s, _e) in intervals if s >= after_hour + EPS]
    return min(starts) if starts else None


def _fitness_v2(
    tasks: List[Dict[str, Any]],
    unmet: Dict[str, int],
    components: List[ProductComponent],
) -> float:
    comps_by_id = {c.id: c for c in components}

    unmet_pen = sum(unmet.values()) * 1_000_000.0

    produced_total = 0
    changeover_hours = 0.0
    wait_hours = 0.0

    first_prod_day: Dict[str, int] = {}
    for t in tasks:
        if t["task_type"] == "PRODUCE":
            produced_total += int(t.get("produced_qty", 0))
            cid = t["component_id"]
            first_prod_day[cid] = min(first_prod_day.get(cid, 10**9), int(t["day"]))
        elif t["task_type"] in ("CHANGE_MOLD", "CHANGE_COLOR"):
            changeover_hours += float(t.get("used_hours", 0.0))
        elif t["task_type"] == "WAIT":
            wait_hours += float(t.get("used_hours", 0.0))

    late_start_pen = 0.0
    for cid, d in first_prod_day.items():
        c = comps_by_id[cid]
        latest_start = c.due_day - c.lead_time_days
        if latest_start < 1:
            latest_start = 1
        if d > latest_start:
            late_start_pen += (d - latest_start) * 10_000.0

    return (produced_total * 1.0) - unmet_pen - late_start_pen - (changeover_hours * 50.0) - (wait_hours * 5.0)


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
    n = len(p1)
    if n < 2:
        return p1[:]
    a, b = sorted(random.sample(range(n), 2))
    mid = p1[a:b]
    rest = [x for x in p2 if x not in mid]
    return rest[:a] + mid + rest[a:]


def _decode_v2(
    genome: List[str],
    components: List[ProductComponent],
    machines: List[Machine],
    molds: List[Mold],
    month_days: int,
    mold_change_time_hours: float,
    color_change_time_hours: float,
) -> Tuple[List[Dict[str, Any]], Dict[str, int]]:
    molds_by_id = {m.id: m for m in molds}

    topo = _topological_order(components)
    rank = {cid: i for i, cid in enumerate(genome)}
    comp_order = sorted(topo, key=lambda c: rank.get(c.id, 10**9))

    remaining: Dict[str, int] = {c.id: int(c.quantity) for c in components}
    completion_time: Dict[str, Tuple[int, float]] = {}  # component_id -> (day, hour)

    mold_busy: Dict[int, Dict[str, List[Tuple[float, float]]]] = {
        d: {m.id: [] for m in molds} for d in range(1, month_days + 1)
    }

    # Carry-over machine state across days
    machine_state: Dict[str, Dict[str, Optional[str]]] = {
        m.id: {"mold_id": None, "color": None, "last_component_id": None} for m in machines
    }

    # Component ownership: once started, only that machine may produce it
    component_owner: Dict[str, str] = {}

    tasks: List[Dict[str, Any]] = []

    for day in range(1, month_days + 1):
        usable: Dict[str, float] = {m.id: float(m.hours_per_day) * float(m.efficiency) for m in machines}
        t: Dict[str, float] = {m.id: 0.0 for m in machines}
        seq: Dict[str, int] = {m.id: 1 for m in machines}
        done: Dict[str, bool] = {m.id: (usable[m.id] <= EPS) for m in machines}

        current_mold: Dict[str, Optional[str]] = {m.id: machine_state[m.id]["mold_id"] for m in machines}
        current_color: Dict[str, Optional[str]] = {m.id: machine_state[m.id]["color"] for m in machines}
        last_component: Dict[str, Optional[str]] = {m.id: machine_state[m.id]["last_component_id"] for m in machines}

        # Event-based within-day simulation: always schedule the machine with the earliest current time
        while True:
            active = [m for m in machines if (not done[m.id]) and (t[m.id] < usable[m.id] - EPS)]
            if not active:
                break

            # Pick next machine by earliest time (tie-break by machine list order)
            active.sort(key=lambda m: t[m.id])
            machine = active[0]
            mid = machine.id

            now = t[mid]
            cap = usable[mid]

            candidates = []
            wait_candidates_next_times: List[float] = []

            for comp in comp_order:
                if remaining[comp.id] <= 0:
                    continue

                # Ownership rule: once a component is started, only its owner can produce it
                owner = component_owner.get(comp.id)
                if owner is not None and owner != mid:
                    continue

                if not _feasible_on_machine(comp, machine, molds_by_id):
                    continue

                # Initial setup is NOT free: None -> X implies a setup
                need_mold_change = (current_mold[mid] != comp.mold_id)
                need_color_change = (current_color[mid] != comp.color)

                setup = 0.0
                if need_color_change:
                    setup += max(0.0, float(color_change_time_hours))
                if need_mold_change:
                    setup += max(0.0, float(mold_change_time_hours))

                start_after_setup = now + setup

                per_piece_h = _piece_hours(comp.cycle_time_sec)
                if per_piece_h <= 0:
                    continue

                # Allow pre-setup before prereqs are ready (but only if prereqs finish later TODAY)
                prereq_ready = _next_ready_time_due_to_prereqs(comp, completion_time, day, start_after_setup)
                if prereq_ready is None:
                    continue

                produce_start = max(start_after_setup, prereq_ready)

                if cap - produce_start < per_piece_h - EPS:
                    continue

                intervals = mold_busy[day].get(comp.mold_id)
                if intervals is None:
                    continue

                # If we will have this mold mounted (possibly while waiting for prereqs),
                # enforce mold exclusivity continuously until at least the first piece is produced.
                if need_mold_change and float(mold_change_time_hours) > 0.0:
                    mold_hold_start = now + (max(0.0, float(color_change_time_hours)) if need_color_change else 0.0)
                else:
                    mold_hold_start = now

                mold_hold_end_min = produce_start + per_piece_h

                if not _interval_is_free(intervals, mold_hold_start, mold_hold_end_min):
                    required_window = mold_hold_end_min - mold_hold_start  # setup/mount + wait + 1 piece
                    nxt = _next_mold_free_time_for_window(intervals, mold_hold_start, required_window, cap)
                    if nxt is not None and nxt > now + EPS and nxt < cap - EPS:
                        wait_candidates_next_times.append(nxt)
                    continue

                # preference (within ownership constraint)
                sticky = 1 if (last_component[mid] is not None and comp.id == last_component[mid]) else 0
                color_match = 1 if (current_color[mid] is not None and comp.color == current_color[mid]) else 0
                mold_match = 1 if (current_mold[mid] is not None and comp.mold_id == current_mold[mid]) else 0
                latest_start = comp.due_day - comp.lead_time_days

                candidates.append(
                    (sticky, color_match, mold_match, latest_start, rank.get(comp.id, 10**9), comp, need_color_change, need_mold_change)
                )

            if not candidates:
                # OPTION A WAIT
                if wait_candidates_next_times:
                    t_next = min(wait_candidates_next_times)
                    if t_next > now + EPS:
                        wait_h = t_next - now
                        tasks.append({
                            "day": day,
                            "machine_id": mid,
                            "machine_name": machine.name,
                            "sequence_in_day": seq[mid],
                            "task_type": "WAIT",
                            "used_hours": wait_h,
                            "start_hour": now,
                            "end_hour": t_next,
                            "utilization": min(1.0, wait_h / cap) if cap > EPS else 0.0,
                        })
                        t[mid] = t_next
                        seq[mid] += 1
                        continue
                done[mid] = True
                t[mid] = cap
                continue

            # stickiness first, then same color
            if last_component[mid] is not None:
                any_sticky = any(c[0] == 1 for c in candidates)
                if any_sticky:
                    candidates = [c for c in candidates if c[0] == 1]
            if current_color[mid] is not None:
                any_same_color = any(c[1] == 1 for c in candidates)
                if any_same_color:
                    candidates = [c for c in candidates if c[1] == 1]

            candidates.sort(key=lambda x: (-x[0], -x[1], -x[2], x[3], x[4]))
            chosen = candidates[0][5]
            need_color_change = candidates[0][6]
            need_mold_change = candidates[0][7]

            # CHANGE_COLOR (even if time == 0, we still update the state)
            if need_color_change:
                ch = max(0.0, float(color_change_time_hours))
                if ch > 0.0:
                    if now + ch > cap + EPS:
                        done[mid] = True
                        t[mid] = cap
                        continue
                    tasks.append({
                        "day": day,
                        "machine_id": mid,
                        "machine_name": machine.name,
                        "sequence_in_day": seq[mid],
                        "task_type": "CHANGE_COLOR",
                        "from_color": current_color[mid],
                        "to_color": chosen.color,
                        "used_hours": ch,
                        "start_hour": now,
                        "end_hour": now + ch,
                        "utilization": min(1.0, ch / cap) if cap > EPS else 0.0,
                    })
                    now += ch
                    t[mid] = now
                    seq[mid] += 1
                current_color[mid] = chosen.color

            # CHANGE_MOLD (reserve mold during change if time > 0; update state even if time == 0)
            if need_mold_change:
                mh = max(0.0, float(mold_change_time_hours))
                if mh > 0.0:
                    if now + mh > cap + EPS:
                        done[mid] = True
                        t[mid] = cap
                        continue

                    intervals = mold_busy[day][chosen.mold_id]
                    if not _interval_is_free(intervals, now, now + mh):
                        nxt = _next_mold_free_time_for_window(intervals, now, mh, cap)
                        if nxt is not None and nxt > now + EPS and nxt < cap - EPS:
                            wait_h = nxt - now
                            tasks.append({
                                "day": day,
                                "machine_id": mid,
                                "machine_name": machine.name,
                                "sequence_in_day": seq[mid],
                                "task_type": "WAIT",
                                "used_hours": wait_h,
                                "start_hour": now,
                                "end_hour": nxt,
                                "utilization": min(1.0, wait_h / cap) if cap > EPS else 0.0,
                            })
                            t[mid] = nxt
                            seq[mid] += 1
                            continue
                        done[mid] = True
                        t[mid] = cap
                        continue

                    _reserve_interval(intervals, now, now + mh)
                    tasks.append({
                        "day": day,
                        "machine_id": mid,
                        "machine_name": machine.name,
                        "sequence_in_day": seq[mid],
                        "task_type": "CHANGE_MOLD",
                        "from_mold_id": current_mold[mid],
                        "to_mold_id": chosen.mold_id,
                        "used_hours": mh,
                        "start_hour": now,
                        "end_hour": now + mh,
                        "utilization": min(1.0, mh / cap) if cap > EPS else 0.0,
                    })
                    now += mh
                    t[mid] = now
                    seq[mid] += 1

                current_mold[mid] = chosen.mold_id

            # After pre-setup, if prereqs still aren't ready, wait until they are (same-day only).
            prereq_ready_now = _next_ready_time_due_to_prereqs(chosen, completion_time, day, now)
            if prereq_ready_now is None:
                done[mid] = True
                t[mid] = cap
                continue
            if prereq_ready_now > now + EPS:
                if prereq_ready_now >= cap - EPS:
                    done[mid] = True
                    t[mid] = cap
                    continue

                # If mold is mounted, reserve it during the waiting time as well (mold exclusivity).
                if current_mold[mid] is not None:
                    intervals = mold_busy[day].get(current_mold[mid])
                    if intervals is not None:
                        if not _interval_is_free(intervals, now, prereq_ready_now):
                            wait_window = prereq_ready_now - now
                            nxt = _next_mold_free_time_for_window(intervals, now, wait_window, cap)
                            if nxt is not None and nxt > now + EPS and nxt < cap - EPS:
                                wait_h = nxt - now
                                tasks.append({
                                    "day": day,
                                    "machine_id": mid,
                                    "machine_name": machine.name,
                                    "sequence_in_day": seq[mid],
                                    "task_type": "WAIT",
                                    "used_hours": wait_h,
                                    "start_hour": now,
                                    "end_hour": nxt,
                                    "utilization": min(1.0, wait_h / cap) if cap > EPS else 0.0,
                                })
                                now = nxt
                                t[mid] = now
                                seq[mid] += 1
                                continue
                            done[mid] = True
                            t[mid] = cap
                            continue
                        _reserve_interval(intervals, now, prereq_ready_now)

                wait_h = prereq_ready_now - now
                tasks.append({
                    "day": day,
                    "machine_id": mid,
                    "machine_name": machine.name,
                    "sequence_in_day": seq[mid],
                    "task_type": "WAIT",
                    "used_hours": wait_h,
                    "start_hour": now,
                    "end_hour": prereq_ready_now,
                    "utilization": min(1.0, wait_h / cap) if cap > EPS else 0.0,
                })
                now = prereq_ready_now
                t[mid] = now
                seq[mid] += 1

            # PRODUCE (partial-window safe: stop at next mold conflict boundary)
            per_piece_h = _piece_hours(chosen.cycle_time_sec)
            if per_piece_h <= 0:
                done[mid] = True
                t[mid] = cap
                continue

            start_prod = now
            intervals = mold_busy[day][chosen.mold_id]

            nxt_busy = _next_busy_start(intervals, start_prod)
            hard_end = cap if nxt_busy is None else min(cap, nxt_busy)
            available_run_h = hard_end - start_prod

            if available_run_h < per_piece_h - EPS:
                done[mid] = True
                t[mid] = cap
                continue

            max_qty_fit = int(available_run_h // per_piece_h)
            qty = min(remaining[chosen.id], max_qty_fit)
            if qty <= 0:
                done[mid] = True
                t[mid] = cap
                continue

            used_h = qty * per_piece_h
            end_prod = start_prod + used_h

            if not _interval_is_free(intervals, start_prod, end_prod):
                # Wait until the mold is free for at least 1 piece, so we don't wake up too early.
                nxt = _next_mold_free_time_for_window(intervals, start_prod, per_piece_h, cap)
                if nxt is not None and nxt > start_prod + EPS and nxt < cap - EPS:
                    wait_h = nxt - start_prod
                    tasks.append({
                        "day": day,
                        "machine_id": mid,
                        "machine_name": machine.name,
                        "sequence_in_day": seq[mid],
                        "task_type": "WAIT",
                        "used_hours": wait_h,
                        "start_hour": start_prod,
                        "end_hour": nxt,
                        "utilization": min(1.0, wait_h / cap) if cap > EPS else 0.0,
                    })
                    t[mid] = nxt
                    seq[mid] += 1
                    continue
                done[mid] = True
                t[mid] = cap
                continue

            _reserve_interval(intervals, start_prod, end_prod)

            # Ownership is set when the component is first started (in time-ordered decode)
            if chosen.id not in component_owner:
                component_owner[chosen.id] = mid

            tasks.append({
                "day": day,
                "machine_id": mid,
                "machine_name": machine.name,
                "sequence_in_day": seq[mid],
                "task_type": "PRODUCE",
                "mold_id": chosen.mold_id,
                "component_id": chosen.id,
                "component_name": chosen.name,
                "color": chosen.color,
                "produced_qty": qty,
                "used_hours": used_h,
                "start_hour": start_prod,
                "end_hour": end_prod,
                "utilization": min(1.0, used_h / cap) if cap > EPS else 0.0,
            })

            remaining[chosen.id] -= qty
            last_component[mid] = chosen.id
            current_mold[mid] = chosen.mold_id
            current_color[mid] = chosen.color

            t[mid] = end_prod
            seq[mid] += 1

            if remaining[chosen.id] <= 0:
                completion_time[chosen.id] = (day, end_prod)

        # end of day: persist state
        for m in machines:
            machine_state[m.id]["mold_id"] = current_mold[m.id]
            machine_state[m.id]["color"] = current_color[m.id]
            machine_state[m.id]["last_component_id"] = last_component[m.id]

    unmet = {cid: qty for cid, qty in remaining.items() if qty > 0}
    return tasks, unmet


def ga_optimize_v2(
    components: List[ProductComponent],
    machines: List[Machine],
    molds: List[Mold],
    month_days: int = 30,
    mold_change_time_hours: float = 0.0,
    color_change_time_hours: float = 0.0,
    pop_size: int = 30,
    n_generations: int = 80,
    mutation_rate: float = 0.25,
) -> Dict[str, Any]:
    if month_days < 1:
        raise ValueError("month_days must be >= 1")
    if pop_size < 2:
        raise ValueError("pop_size must be >= 2")
    if n_generations < 1:
        raise ValueError("n_generations must be >= 1")
    if not (0.0 <= float(mutation_rate) <= 1.0):
        raise ValueError("mutation_rate must be between 0 and 1")

    population = [_random_genome(components) for _ in range(pop_size)]

    best_score = None
    best_genome = None

    for _ in range(n_generations):
        scored = []
        for g in population:
            tasks, unmet = _decode_v2(
                genome=g,
                components=components,
                machines=machines,
                molds=molds,
                month_days=month_days,
                mold_change_time_hours=mold_change_time_hours,
                color_change_time_hours=color_change_time_hours,
            )
            score = _fitness_v2(tasks, unmet, components)
            scored.append((score, g))

        scored.sort(key=lambda x: x[0], reverse=True)
        if best_score is None or scored[0][0] > best_score:
            best_score = scored[0][0]
            best_genome = scored[0][1][:]

        elite_k = max(2, pop_size // 5)
        new_pop = [g[:] for (_, g) in scored[:elite_k]]

        while len(new_pop) < pop_size:
            i, j = random.sample(range(pop_size), 2)
            parent = scored[i][1] if scored[i][0] > scored[j][0] else scored[j][1]
            new_pop.append(parent[:])

        children = []
        for i in range(0, pop_size, 2):
            if i + 1 >= pop_size:
                children.append(new_pop[i][:])
                break
            c1 = _crossover_ox(new_pop[i], new_pop[i + 1])
            c2 = _crossover_ox(new_pop[i + 1], new_pop[i])
            children.extend([c1, c2])

        for i in range(len(children)):
            if random.random() < mutation_rate:
                children[i] = _mutate_swap(children[i][:])

        population = children[:pop_size]

    final_tasks, final_unmet = _decode_v2(
        genome=best_genome,
        components=components,
        machines=machines,
        molds=molds,
        month_days=month_days,
        mold_change_time_hours=mold_change_time_hours,
        color_change_time_hours=color_change_time_hours,
    )
    final_score = _fitness_v2(final_tasks, final_unmet, components)

    return {
        "assignments": final_tasks,
        "unmet": final_unmet,
        "score": final_score,
    }