from .ga_scheduler import ga_optimize, greedy_jobshop_scheduler
from .test_data import get_sample_machines, get_sample_components
from .manual_scheduler import manual_sequential_schedule
from .plot_gantt import plot_gantt  # <-- Import your Gantt chart function

def main():
    machines = get_sample_machines()
    components = get_sample_components()

    # Manual (sequential) schedule
    manual_sched = manual_sequential_schedule(components, machines)
    manual_makespan = max(end for (start, end, name, m_names) in manual_sched.values())
    print(f"Manual (sequential) total production time: {manual_makespan} min")
    plot_gantt(manual_sched, "Manual (Sequential) Schedule")

    # GA-optimized schedule
    ga_sched = ga_optimize(components, machines, pop_size=20, n_generations=50, mutation_rate=0.2)
    ga_makespan = max(end for (start, end, name, m_names) in ga_sched.values())
    print(f"GA-Optimized total production time: {ga_makespan} min")
    plot_gantt(ga_sched, "GA-Optimized Schedule")

    # Greedy job shop schedule
    greedy_sched = greedy_jobshop_scheduler(components, machines)
    greedy_makespan = max(end for (start, end, name, m_names) in greedy_sched.values())
    print(f"Greedy Job Shop total production time: {greedy_makespan} min")
    plot_gantt(greedy_sched, "Greedy Job Shop Schedule")

    # Print all for comparison
    print("\nSummary:")
    print(f"Manual: {manual_makespan} min")
    print(f"GA: {ga_makespan} min")
    print(f"Greedy: {greedy_makespan} min")

if __name__ == "__main__":
    main()