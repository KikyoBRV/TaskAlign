# main.py

from .test_data import get_sample_machines, get_sample_components
from .ga_scheduler import ga_optimize
from .manual_scheduler import manual_sequential_schedule
import matplotlib.pyplot as plt

def plot_gantt(schedule, title):
    import matplotlib.pyplot as plt
    colors = ['tab:blue', 'tab:orange', 'tab:green', 'tab:red', 'tab:purple', 'tab:brown']
    fig, ax = plt.subplots(figsize=(12, 5))
    yticks = []
    yticklabels = []
    y = 0
    for i, (comp_id, (start, end, name, m_names)) in enumerate(schedule.items()):
        for m in m_names:
            ax.barh(y, end - start, left=start, color=colors[i % len(colors)], edgecolor='black')
            ax.text(start + (end - start) / 2, y, f"{name}", va='center', ha='center', color='white', fontsize=9)
            yticklabels.append(f"{name} ({m})")
            yticks.append(y)
            y += 1
    ax.set_yticks(yticks)
    ax.set_yticklabels(yticklabels)
    ax.set_xlabel("Time (min)")
    ax.set_title(title)
    # Set x-axis limits and ticks
    ax.set_xlim(0, 160)
    ax.set_xticks(list(range(0, 161, 5)))
    ax.grid(axis='x', linestyle='--', alpha=0.5)
    plt.tight_layout()
    plt.show()

def get_total_production_time(schedule):
    return max(end for (start, end, name, m_names) in schedule.values())

if __name__ == "__main__":
    machines = get_sample_machines()
    components = get_sample_components()

    # Manual (sequential) schedule
    manual_schedule = manual_sequential_schedule(components, machines)
    manual_time = get_total_production_time(manual_schedule)
    print(f"Manual (sequential) total production time: {manual_time} min")
    plot_gantt(manual_schedule, "Manual (Sequential) Production Schedule")

    # GA-optimized schedule
    best_schedule = ga_optimize(components, machines)
    ga_time = get_total_production_time(best_schedule)
    print(f"GA-Optimized total production time: {ga_time} min")
    plot_gantt(best_schedule, "GA-Optimized Production Schedule")

    print(f"\nPerformance improvement: {manual_time - ga_time} min faster using GA optimization.")