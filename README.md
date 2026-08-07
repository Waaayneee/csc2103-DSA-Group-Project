# CSC2103 Data Structures and Algorithms - Group Project

**1. Project Overview**

This project implements three algorithm-based solutions as required by the CSC2103 Group Project brief (April 2026 semester), covering Greedy, Dynamic Programming, and Heuristic algorithm categories.

**1.1 Topic:**

Smart Delivery Route Optimization System (Option A). A delivery company needs to plan a truck's daily route: which packages to load, and the shortest and most efficient way to deliver them.

**2. Group Members**

| Member | Role |
|---|---|
| Wayne & Natalie | Problem 1 (Greedy) |
| Zoey & Vanice | Problem 2 (Dynamic Programming) |
| Stewart | Problem 3 (Heuristic) |
| Wayne | GitHub, Integration & Report Coordinator |

Update this table with actual names before submission.

**3. Folder Structure**

csc2103-group-project/

├── problem1_dijkstra/     # Problem 1: Greedy Algorithm (Dijkstra's Shortest Path)

├── problem2_knapsack/     # Problem 2: Dynamic Programming (0/1 Knapsack)

├── problem3_tsp/          # Problem 3: Heuristic Algorithm (TSP) — not yet implemented

├── docs/                  # Report drafts, sample run screenshots, test case notes

└── README.md              # This file

**4. Requirements**

Python 3. No external libraries required, all algorithms are implemented manually with no built-in sorting, graph, or optimization libraries used for the core logic.

**5. How to Run**

**5.1 Problem 1, Greedy (Dijkstra's Shortest Path):**

Run this --> python3 problem1_dijkstra/problem1.py

Finds the shortest road route between two delivery locations. See problem1_dijkstra/README.md for the full step-by-step usage guide.

**5.2 Problem 2, Dynamic Programming (0/1 Knapsack):**

Run this --> python3 problem2_knapsack/problem2.py

Decides which packages to load onto the truck to maximize delivery priority without exceeding its weight capacity. Enter each package's ID, weight, and priority when prompted, followed by the truck's maximum capacity.

**5.3 Problem 3, Heuristic (TSP):**

Not yet implemented. This will find an efficient order to visit all delivery stops in one trip.

**6. Testing and Validation**

**6.1 Problem 1:**

problem1_dijkstra/expected_shortest_distances.txt contains every source-to-destination distance for the sample network, manually calculated by hand ahead of time. This serves as the answer sheet used to verify the program's output is correct.

**6.2 Problem 2:**

Test with a small number of packages first to manually verify the DP table and selected packages by hand, then test with a larger set and a tight capacity to confirm the algorithm still picks the optimal combination.

**6.3 Problem 3:**

To be added once implemented.

**9. Known Limitations**

1. Problem 1 requires non-negative edge weights and assumes roads are bidirectional (two-way).
2. Problem 2 assumes all package weights and capacities are whole numbers (integers).
3. Problem 3 is not yet implemented.
4. Output is text-based only, no GUI, as required by the assignment brief.

**This is just a brief summary**

Full limitations are displayed in respective problems README.md

thanks for reading this!!! :>
