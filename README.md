# Urban Transit Route Planner

A desktop application designed for public transit route planning and multi-criteria optimization across urban networks (bus, tram, walking).

## Transit Map Visualization
<img width="952" height="656" alt="image" src="https://github.com/user-attachments/assets/6490f6d8-d7ed-4469-b4b2-f5b4d2fb6554" />


## Key Features
- **Dijkstra's Algorithm:** Calculates the fastest route (travel time), cheapest route (transit cost), and a balanced realistic score penalizing excessive transfers and long walking segments.
- **BFS (Breadth-First Search):** Finds the most direct route with the minimum number of transit stops.
- **Dynamic Scenario Simulation:** Test real-time traffic delays, fare price changes, and temporary station closures with route recalculation.
- **Interactive UI:** Metro-style interactive network map built with Tkinter Canvas featuring station hovering and visual route tracing.

## How to Run
Make sure you have Python 3 installed. Run the following command in the project directory:

```bash
python "PUBLIC TRANSPORT.py"
