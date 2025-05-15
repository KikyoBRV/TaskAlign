from .ga_scheduler import ga_optimize
from .test_data_task1_6 import (
    get_sample_machines, get_sample_components,
    get_parallel_machines, get_parallel_components,
    get_contention_machines, get_contention_components
)

def explain_ga_schedule(schedule, components):
    comp_lookup = {c.id: c for c in components}
    component_end = {comp_id: end for comp_id, (start, end, name, m_names) in schedule.items()}
    for comp_id, (start, end, name, m_names) in sorted(schedule.items(), key=lambda x: x[1][0]):
        comp = comp_lookup[comp_id]
        prereqs = comp.prerequisites
        prereq_str = ', '.join(prereqs) if prereqs else 'No prerequisites'
        prereq_times = [component_end[pr] for pr in prereqs] if prereqs else []
        machine_str = ', '.join(m_names)
        print(f"Scheduled '{name}' on {machine_str} from {start} to {end} because:")
        if prereqs:
            print(f"  - Prerequisite(s) ({prereq_str}) completed at {[component_end[pr] for pr in prereqs]}")
        else:
            print(f"  - No prerequisites.")
        print(f"  - {machine_str} was available at {start}.")
        if prereqs:
            print(f"  - Scheduled at {start} (latest of prerequisites and machine availability).")
        else:
            print(f"  - Scheduled at {start} (machine available, no dependencies).")
        print("")

def run_and_explain(machines, components, case_name):
    print(f"\n=== {case_name} ===")
    schedule = ga_optimize(components, machines, pop_size=20, n_generations=50, mutation_rate=0.2)
    makespan = max(end for (start, end, name, m_names) in schedule.values())
    print(f"GA-Optimized total production time: {makespan} min\n")
    explain_ga_schedule(schedule, components)

if __name__ == "__main__":
    # Test Case 1
    run_and_explain(get_sample_machines(), get_sample_components(), "Test Case 1: Sample Components")
    # Test Case 2
    run_and_explain(get_parallel_machines(), get_parallel_components(), "Test Case 2: Parallelizable Tasks")
    # Test Case 3
    run_and_explain(get_contention_machines(), get_contention_components(), "Test Case 3: Resource Contention and Deep Dependencies")