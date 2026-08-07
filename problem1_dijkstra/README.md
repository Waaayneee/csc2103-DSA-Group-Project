**1. Problem Description**

Part of the Smart Delivery Route Optimization System. A delivery company needs to find the shortest road route from the depot to a chosen delivery destination, given a network of roads and distances between city locations.

**1.1 Algorithm Used:**

Dijkstra's Shortest Path Algorithm (Greedy).

At every step, the algorithm picks the unvisited location with the smallest known tentative distance from the source, and finalizes it. This greedy choice is never revisited, since with non-negative edge weights, no shorter path to that location can be found later. This program implements the algorithm manually (no built-in graph or priority-queue library is used for the core logic).

**2. How to Run?**

Requires: Python 3.

Run this --> python3 problem1.py

On launch, you'll see a menu:

1. Run built-in sample delivery network
2. Run built-in DISCONNECTED network (edge case test)
3. Enter a custom delivery network
4. Exit

**2.1 What does it do?**

**2.1.1 Option 1:** quick demo using a preloaded 6-location network.
1.1 Choose one of the sample locations as source/ starting location IE: "Depot" (Not case sensitive)
1.2 Choose one of the sample locations as ending location IE: "Mall" (Not case sensitive)
1.3 The program runs Dijkstra's algorithm, printing a step-by-step table showing which location is finalized at each stage, then prints the final shortest path, total distance, average route distance, and distance saved.

**2.1.2 Option 2:** tests the edge case where no path exists between two locations.
2.1 Choose one of the sample locations as source/starting location IE: "Depot" (Not case sensitive)
2.2 Choose one of the sample locations as ending location IE: "IsolatedZone" (Not case sensitive)
2.3 The program runs Dijkstra's algorithm as normal, but since "IsolatedZone" has no roads connecting it to anything, the algorithm cannot reach it. Instead of crashing, the program detects this and prints a message stating no route exists between the two locations.

**2.1.3 Option 3:** build your own network, then find shortest path from chosen starting and ending location
3.1 Enter the number of locations, then name each one.
3.2 Enter the number of roads, then for each one type FromLocation ToLocation Distance (e.g. Depot WarehouseA 4).
3.3 Choose a source (depot) and a destination location.
3.4 The program runs Dijkstra's algorithm, printing a step-by-step table showing which location is finalized at each stage, then prints the final shortest path and several distance comparisons for the selected route.

**3. Sample Result:**
--------------------------------------------------
FINAL RESULT
--------------------------------------------------
Shortest route from 'Depot' to 'Mall':
 
  Depot -> WarehouseA -> CityCenter -> Mall
  
Total distance: 12 KM

Average distance: 14.5 KM

Distance saved: 2.5 KM

--------------------------------------------------

**4. File Structure**

problem1_dijkstra/

├── problem1.py   # Main program (all logic in one file)

└── README.md     # This file

**5. Known Limitations:**

1. Requires non-negative edge weights; the program validates and rejects negative distances during custom
2. input, since Dijkstra's algorithm does not guarantee correct results with negative weights.
3. Assumes roads are bidirectional (two-way), matching a typical city road network.
4. Does not visualize the graph; output is text-based only, as required by the assignment brief (no GUI needed).
