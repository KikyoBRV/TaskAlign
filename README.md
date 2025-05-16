# TaskAlign: AI-Driven Factory Scheduling System

TaskAlign is a task scheduling system designed for conventional electronic equipment factories that rely on manual production management. The system assists factory managers and operators in designing job schedules that optimize user-specified optimization criteria, such as production time, machine utilization and workforce allocation, while taking into account constraints like machine cool-down time, energy consumption, and production dependencies. A key feature of TaskAlign is its data encoding system, which transforms user inputs (such as machine specifications, worker assignments, product requirements, and dependencies) into a representation of the factory's workflow that is suitable for job scheduling algorithms. The system then applies optimization algorithms to generate an optimal production schedule that maximizes machine utilization and efficient workforce allocation while respecting constraints like machine cool-down time and production dependencies. Users can view and interact with the resulting schedules through Gantt charts and timeline visualizations, allowing them to make manual adjustments to production plans when necessary.

---

## Features

1. **Smart Task Scheduling (Optimization-Based)**
   - Users input machine data, including:
     - Machine name
     - Machine type
     - Machine capabilities
     - Number of fixed workers assigned to operate the machine
     - Maximum operation time
     - Cooldown time
     - Defect rate
     - Production rate
     - Status of machine (Active, Maintenance, Inactive)
     - General product details (Name, Model, Description)
     - Product components:
       * ID (Might be auto generated)
       * Component name
       * Component steps: Steps in assembling this component (Additional details can be added in the "Assembly Process")
       * Total Production time per component production time
       * Required machines
       * Prerequisite components
       * Component quantity
     - Machine capabilities
     - Number of fixed workers assigned to operate the machine
     - Maximum operation time
     - Cooldown time
     - Defect rate
     - Production rate
     - Status of machine (Active, Maintenance, Inactive)
   - The system generates an optimal production schedule considering constraints like machine efficiency, energy usage, and human resource availability.

2. **Flexible Scheduling Modes**
   - Fresh Start Mode: Creates a new schedule for factories starting production from zero.
   - Production Resume Mode: Users can input completed portions, and the system will recalculate the optimal production plan to complete the remaining work.

3. **Visualized Task Planning (Gantt Chart & Timeline View)**
   - Displays a clear production roadmap, helping managers track daily tasks and machine utilization.
   - Allows users to adjust schedules manually if needed.


---

## Installation and Testing

For detailed documentation, theoretical background, and how to run the test, please visit the [Factory Scheduling Experiment Wiki](../../wiki/Factory%20Scheduling%20Experiment).


---

## Learn More

For detailed documentation, theory, and advanced usage, **visit the [Wiki](../../wiki)**.

---
