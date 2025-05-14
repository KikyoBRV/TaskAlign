# ga_scheduler.py

import random

def random_schedule(components):
    order = []
    remaining = components[:]
    while remaining:
        available = [c for c in remaining if all(pr in [o.id for o in order] for pr in c.prerequisites)]
        c = random.choice(available)
        order.append(c)
        remaining.remove(c)
    return order

def decode_schedule(component_order, machines):
    machine_available = {m.name: 0 for m in machines}
    component_end = {}
    schedule = {}
    for c in component_order:
        prereq_end = max([component_end[pr] for pr in c.prerequisites], default=0)
        start = prereq_end
        for m_name in c.required_machines:
            start = max(start, machine_available[m_name])
        end = start + c.total_time
        for m_name in c.required_machines:
            machine = next(m for m in machines if m.name == m_name)
            machine_available[m_name] = end + machine.cooldown
        component_end[c.id] = end
        schedule[c.id] = (start, end, c.name, c.required_machines)
    return schedule

def fitness(schedule):
    return -max(end for (start, end, name, machines) in schedule.values())

def crossover(parent1, parent2):
    size = len(parent1)
    a, b = sorted(random.sample(range(size), 2))
    child_p1 = parent1[a:b]
    child = []
    for c in parent2:
        if c not in child_p1:
            child.append(c)
    return child[:a] + child_p1 + child[a:]

def mutate(order, components):
    idxs = list(range(len(order)))
    i, j = random.sample(idxs, 2)
    c1, c2 = order[i], order[j]
    def is_valid_swap(o, i, j):
        c1, c2 = o[i], o[j]
        if any(pr == c1.id for pr in c2.prerequisites):
            return False
        if any(pr == c2.id for pr in c1.prerequisites):
            return False
        return True
    if is_valid_swap(order, i, j):
        order[i], order[j] = order[j], order[i]
    return order

def repair_schedule(order):
    id_to_comp = {c.id: c for c in order}
    scheduled = []
    remaining = order[:]
    while remaining:
        progress = False
        for c in remaining:
            if all(pr in [s.id for s in scheduled] for pr in c.prerequisites):
                scheduled.append(c)
                remaining.remove(c)
                progress = True
                break
        if not progress:
            raise ValueError("Cannot repair schedule: circular dependency detected.")
    return scheduled

def ga_optimize(components, machines, pop_size=20, n_generations=50, mutation_rate=0.2):
    population = [random_schedule(components) for _ in range(pop_size)]
    for gen in range(n_generations):
        decoded = [decode_schedule(ind, machines) for ind in population]
        fitnesses = [fitness(s) for s in decoded]
        # Selection (tournament)
        selected = []
        for _ in range(pop_size):
            i, j = random.sample(range(pop_size), 2)
            selected.append(population[i] if fitnesses[i] > fitnesses[j] else population[j])
        # Crossover
        children = []
        for i in range(0, pop_size, 2):
            if i+1 < pop_size:
                c1 = crossover(selected[i], selected[i+1])
                c2 = crossover(selected[i+1], selected[i])
                c1 = repair_schedule(c1)
                c2 = repair_schedule(c2)
                children.extend([c1, c2])
            else:
                c = repair_schedule(selected[i])
                children.append(c)
        # Mutation
        for i in range(pop_size):
            if random.random() < mutation_rate:
                children[i] = mutate(children[i][:], components)
                children[i] = repair_schedule(children[i])
        population = children
    decoded = [decode_schedule(ind, machines) for ind in population]
    fitnesses = [fitness(s) for s in decoded]
    best_idx = fitnesses.index(max(fitnesses))
    best_schedule = decoded[best_idx]
    return best_schedule