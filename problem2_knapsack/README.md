**1. Problem Description**

Part of the Smart Delivery Route Optimization System. Before the delivery truck leaves the depot, the company needs to decide which packages to load. Each package has a weight and a delivery priority, and the truck has a maximum weight capacity. The goal is to select the combination of packages that maximizes total delivery priority without exceeding the truck's capacity.

**1.1 Algorithm Used:**

0/1 Knapsack Problem (Dynamic Programming).

Each package can either be fully included or fully excluded, it cannot be split (hence "0/1"). The algorithm builds a table where each cell dp[i][w] represents the best total priority achievable using the first i packages within a weight limit of w. For each package, it compares including the package (its priority plus the best result for the remaining capacity) against excluding it (the best result without it), and keeps whichever is larger. This program implements the algorithm manually (no built-in optimization library is used for the core logic).

**2. How to Run?**

Requires: Python 3.

Run this --> python3 problem2.py

On launch, you'll be prompted step by step:

**2.1.1** Enter the number of delivery packages.
**2.1.2** For each package, enter its Package ID, Weight (kg), and Delivery Priority.
**2.1.3** Enter the truck's maximum capacity (kg).

**2.2 What does it do?**

**2.2.1 Builds the DP table:** the program fills a table of best-possible-priority values for every combination of package count and remaining capacity, following the 0/1 Knapsack recurrence relation.

**2.2.2** Backtracks to find the selected packages: starting from the final cell of the table, the program walks backward to determine exactly which packages were included in the optimal solution, rather than only reporting the best total.

**2.2.3** Displays the results: the program prints the full DP table, then a table of the selected packages with their weight and priority, followed by a delivery summary showing total weight used, truck capacity, total priority, and how many packages were delivered versus skipped.

**3. Sample Result:**

Input: 4 packages (P001: 2kg/priority 3, P002: 3kg/priority 4, P003: 4kg/priority 5, P004: 5kg/priority 6), truck capacity 5kg.

Selected Packages

Package Weight Priority
P001 2 3
P002 3 4
Total Weight Used : 5 kg

Truck Capacity : 5 kg

Total Priority : 7

Delivery Summary
Packages Delivered : 2

Packages Skipped : 2

Optimization Complete.

**4. File Structure**

problem2_knapsack/

├── problem2.py # Main program (all logic in one file)

└── README.md # This file

**5. Known Limitations:**

**5.1** Assumes all package weights, priorities, and truck capacity are whole numbers (integers); decimal weights are not currently supported.
**5.2** Does not currently validate against negative weights, priorities, or capacity, or reject a number of packages of 0 or less.
**5.3** A single package with a weight greater than the truck's capacity is automatically excluded, rather than flagged with a warning message.
**5.4** Does not visualize the graph; output is text-based only, as required by the assignment brief (no GUI needed).