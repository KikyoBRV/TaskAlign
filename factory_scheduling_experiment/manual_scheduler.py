# manual_scheduler.py

def manual_sequential_schedule(components, machines):
    # Schedule one component at a time, in the order given, even if machines are free
    machine_available = {m.name: 0 for m in machines}
    component_end = {}
    schedule = {}
    current_time = 0
    for c in components:
        prereq_end = max([component_end[pr] for pr in c.prerequisites], default=0)
        start = max(current_time, prereq_end)
        for m_name in c.required_machines:
            start = max(start, machine_available[m_name])
        end = start + c.total_time
        for m_name in c.required_machines:
            machine = next(m for m in machines if m.name == m_name)
            machine_available[m_name] = end + machine.cooldown
        component_end[c.id] = end
        schedule[c.id] = (start, end, c.name, c.required_machines)
        current_time = end  # Only one component at a time!
    return schedule