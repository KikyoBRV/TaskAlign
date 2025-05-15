def plot_gantt(schedule, title):
    import matplotlib.pyplot as plt
    import random

    # Use a large color palette for many tasks
    import matplotlib.colors as mcolors
    color_list = list(mcolors.TABLEAU_COLORS.values()) + list(mcolors.CSS4_COLORS.values())
    random.shuffle(color_list)

    fig, ax = plt.subplots(figsize=(12, 6))
    yticks = []
    yticklabels = []
    y = 0
    max_end = 0

    for i, (comp_id, (start, end, name, m_names)) in enumerate(schedule.items()):
        for m in m_names:
            color = color_list[i % len(color_list)]
            ax.barh(y, end - start, left=start, color=color, edgecolor='black')
            ax.text(start + (end - start) / 2, y, f"{name}", va='center', ha='center', color='white', fontsize=9)
            yticklabels.append(f"{name} ({m})")
            yticks.append(y)
            y += 1
            if end > max_end:
                max_end = end

    ax.set_yticks(yticks)
    ax.set_yticklabels(yticklabels)
    ax.set_xlabel("Time (min)")
    ax.set_title(title)

    # Set x-axis limits and ticks dynamically (intervals of 20)
    x_max = ((max_end // 20) + 1) * 20
    ax.set_xlim(0, x_max)
    ax.set_xticks(list(range(0, x_max + 1, 20)))
    ax.grid(axis='x', linestyle='--', alpha=0.5)
    plt.setp(ax.get_xticklabels(), rotation=30, ha='right', rotation_mode='anchor')
    plt.tight_layout()
    plt.show()