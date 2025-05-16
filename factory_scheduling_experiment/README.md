# Factory Scheduling Experiment

**Factory Scheduling Experiment** is a proof-of-concept project for AI-driven production scheduling in electronic equipment factories. It demonstrates how a Genetic Algorithm (GA) can optimize production schedules compared to manual (sequential) planning, using real-world constraints such as machine cooldowns, dependencies, and resource allocation.

---

## Features

- **Smart Task Scheduling:**  
  Uses a Genetic Algorithm and a Greedy algorithm to generate efficient production schedules, maximizing machine utilization and minimizing total production time.
- **Manual Baseline Comparison:**  
  Simulates a user-planned, sequential schedule for direct performance comparison.
- **Gantt Chart Visualization:**  
  Visualizes manual, greedy, and AI-optimized (GA) schedules for easy comparison.
- **RESTful API Service:**  
  Exposes the scheduling algorithm as a FastAPI endpoint, allowing integration with other applications or user interfaces.
- **Realistic Constraints:**  
  Models machines and product components with real-world attributes (cooldown, prerequisites, etc.).
- **Performance Metrics:**  
  Compares total production time (makespan) for all approaches.
- **Schedule Explanation:**  
  Provides a step-by-step explanation of the GA scheduling decisions.

---

## Getting Started

### Prerequisites

- Python 3.7+
- [matplotlib](https://matplotlib.org/)

### Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/KikyoBRV/TaskAlign.git
   cd factory_scheduling_experiment
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

---

## Usage

From the parent directory of `factory_scheduling_experiment`, run:

```bash
python -m factory_scheduling_experiment.main
```

This will:

- Print the total production time for both manual and GA-optimized schedules. 
- Display Gantt charts for all three schedules, using the same time scale for easy comparison.

Note:
You have to close each Gantt chart window (manual, then greedy, then GA) in order for the program to display the next one.

---

## Example Output

**Manual (Sequential) Schedule:**

![Manual Gantt Chart](image/manual2_output.png)

**GA-Optimized Schedule:**

![GA Gantt Chart](image/ga2_output.png)

**Greedy Schedule:**
![Greedy Gantt Chart](image/greedy2_output.png)

**Performance Comparison:**

```
Manual (sequential) total production time: 928 min
Greedy total production time: 638 min
GA-Optimized total production time: 680 min
```

---

## Project Structure

```
factory_scheduling_experiment/
│
├── init.py
├── models.py               # Data models for Machine and ProductComponent
├── test_data.py            # Sample data for machines and components
├── ga_scheduler.py         # Genetic Algorithm scheduling logic
├── greedy_scheduler.py     # Greedy scheduling logic
├── manual_scheduler.py     # Manual (sequential) scheduling logic
├── main.py                 # Main script: runs all schedulers and plots results
├── main_api.py             # FastAPI app: exposes scheduling as a RESTful API
├── explain_ga_schedule.py  # Script to explain GA scheduling decisions step-by-step
└── image/                  # Output images (Gantt charts, etc.)
```

---

## How It Works

1. **Data Preparation:**  
   Machines and product components are defined with realistic attributes and dependencies.
2. **Manual Scheduling:**  
   Schedules one component at a time, regardless of machine availability.
3. **GA Scheduling:**  
   Uses a genetic algorithm to find the most efficient schedule, allowing parallelism and maximizing resource use.
4. **Visualization:**  
   Both schedules are visualized as Gantt charts for direct comparison.
5. **Performance Metrics:**  
   Total production time is calculated and compared.

---

## How GA Scheduling Works

The Genetic Algorithm (GA) in this project is designed to find efficient production schedules by simulating the process of natural selection. Here’s how it works in this theory test:

1. **Population Initialization:**  
   The algorithm starts by generating a population of random, valid schedules. Each schedule is an ordering of all production tasks, ensuring that prerequisites are respected.

2. **Schedule Decoding:**  
   For each schedule, the algorithm simulates the production process:
   - Tasks are assigned to machines as soon as their prerequisites and required machines are available.
   - Machine cooldowns and other constraints are enforced.
   - The start and end times for each task are recorded.

3. **Fitness Evaluation:**  
   Each schedule is scored based on its **total production time** (makespan). Schedules that finish all tasks sooner receive higher fitness scores.

4. **Selection:**  
   The best-performing schedules are selected to form the next generation, using a tournament selection method.

5. **Crossover:**  
   Pairs of schedules are combined to create new schedules, mixing their task orders while maintaining valid dependencies.

6. **Mutation:**  
   Some schedules are randomly altered (e.g., swapping two tasks) to introduce diversity, as long as prerequisites are not violated.

7. **Repair:**  
   After crossover and mutation, a repair step ensures that all task dependencies are still respected.

8. **Iteration:**  
   Steps 2–7 are repeated for a set number of generations. Over time, the population evolves toward more efficient schedules.

9. **Best Schedule Selection:**  
   After all generations, the schedule with the shortest total production time is selected as the optimal solution.

**Result:**  
The GA finds a schedule that overlaps tasks where possible, maximizes machine utilization, and minimizes total production time often outperforming manual, sequential planning.

## Explaining GA Scheduling Decisions

To see a step-by-step explanation of how the GA makes its scheduling decisions, run:

```
python -m factory_scheduling_experiment.explain_ga_schedule
```
This script will print a detailed explanation of the GA’s decision process for a sample scenario, helping users understand how the optimized schedule is constructed.

## Run the API Service

You can also run the scheduling algorithm as a RESTful API using FastAPI:

```
uvicorn factory_scheduling_experiment.main_api:app --reload
```

The API will be available at [http://localhost:8000](http://localhost:8000).

You can access the interactive API documentation and test the `/schedule` endpoint at [http://localhost:8000/docs](http://localhost:8000/docs).

**Example:**  
Send a POST request to `/schedule` with your machines and components in JSON format to receive an optimized schedule.  
(You can copy the request body from `test_data_task1_6.py`)
