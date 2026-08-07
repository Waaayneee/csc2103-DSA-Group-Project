**1. Problem Description**

Part of the Smart Delivery Route Optimization System. Once the delivery packages have been chosen, the truck must visit every delivery stop and return to the depot. The program decides the ORDER in which the stops are visited so that the total distance driven is as short as possible.

This is the Travelling Salesman Problem. With n delivery stops there are (n-1)!/2 distinct tours, so checking every possible order quickly becomes impossible (5 stops is only 12 tours, but 9 stops is 20,160 and 15 stops is over 43 billion).

**1.1 Algorithm Used:**

Travelling Salesman Problem using a Genetic Algorithm (Heuristic).

A Genetic Algorithm does not guarantee the shortest possible tour. It imitates natural selection instead: a population of random candidate routes is created, each route is scored by a fitness function (fitness = 1 / distance, so shorter routes score higher), selection picks the fitter routes as parents, crossover combines two parents into a child route, and mutation randomly alters children to keep the population varied. Repeating this over many generations lets short route fragments spread through the population, so the answer improves steadily and usually reaches the optimum after scoring only a fraction of the possible tours. This is the heuristic trade-off: a good answer quickly, rather than a guaranteed best answer slowly.

The program also calls Dijkstra's algorithm (reused from Problem 1) to work out the shortest road distance between each pair of stops, because the truck drives on roads and cannot travel directly between two locations unless a road joins them.

Everything is implemented manually. There are no import statements in the file: randomness uses a hand-written Park-Miller generator instead of `random`, ranking uses a hand-written insertion sort instead of `sorted()`, shuffling uses Fisher-Yates instead of `random.shuffle`, and the verifier generates permutations recursively instead of using `itertools`.

**2. How to Run?**

Requires: Python 3.

Run this --> python3 problem3_tsp_genetic.py

On launch, you'll see a menu:

1. Run built-in sample delivery network
2. Run extended delivery network (larger search space)
3. Run built-in DISCONNECTED network (edge case test)
4. Enter a custom delivery network
5. Run sample network with your own GA settings
6. Exit

**2.1 What does it do?**

**2.1.1 Option 1:** quick demo using the same preloaded 6-location network as Problem 1.
1.1 Choose one of the sample locations as the depot IE: "Depot" (case sensitive)
1.2 Enter the delivery stops separated by spaces IE: "WarehouseA CityCenter Mall", or type "ALL" to deliver to every other location
1.3 The program prints the shortest road distance between every pair of chosen locations, shows the fittest routes of the random starting population, then prints a generation-by-generation table of the best and average distance as the population evolves. It finishes with the greedy baseline route, the final Genetic Algorithm route (with the roads driven for each leg), and a comparison table.

**2.1.2 Option 2:** the same city extended with four more delivery zones.
2.1 Same input steps as Option 1.
2.2 With only five stops in Option 1 there are just 12 possible tours, so the algorithm finds the best one almost immediately and the evolution is not visible. This network has nine stops and 20,160 possible tours, so the population visibly improves over the generations (66 km down to 56 km), which is the behaviour a heuristic is meant to demonstrate.

**2.1.3 Option 3:** tests the edge case where a delivery stop cannot be reached.
3.1 Choose "Depot" as the depot.
3.2 Enter "ALL" or include "IsolatedZone" in the delivery stops.
3.3 Since "IsolatedZone" has no roads connecting it to anything, no delivery tour covering it exists. Instead of crashing or inventing a route, the program detects this and prints a message stating that no route exists between the two locations.

**2.1.4 Option 4:** build your own network, then find a delivery tour around it.
4.1 Enter the number of locations, then name each one.
4.2 Enter the number of roads, then for each one type FromLocation ToLocation Distance (e.g. Depot WarehouseA 4).
4.3 Choose the depot and the delivery stops.
4.4 The program runs the Genetic Algorithm on the network you built and prints the same output as Option 1.

**2.1.5 Option 5:** run the sample network with your own Genetic Algorithm settings.
5.1 Enter the population size, number of generations, mutation rate, tournament size, number of elite routes, and the random seed. Press Enter at any prompt to keep the default shown in brackets.
5.2 Choose the depot and delivery stops as in Option 1.
5.3 Useful for showing how the settings affect the result. Because the same seed always produces the same output, any run can be repeated exactly.

**3. Sample Result:**
--------------------------------------------------

Generation 0: 60 random routes created. Fittest 5:

Route (delivery order)                          Distance   Fitness

WarehouseB Mall Suburb CityCenter WarehouseA        32.0    0.0312

WarehouseA CityCenter Mall Suburb WarehouseB        32.0    0.0312

CityCenter WarehouseB Suburb Mall WarehouseA        33.0    0.0303

Evolution progress

Generation     Best in Gen       Average     Best Ever

0                     32.0          38.3          32.0

20                    32.0          33.4          32.0

40                    32.0          33.3          32.0

--------------------------------------------------

FINAL DELIVERY ROUTE (Genetic Algorithm)

--------------------------------------------------

Delivery order:

  Depot -> WarehouseB -> Mall -> Suburb -> CityCenter -> WarehouseA -> Depot

Leg   From          To                km   Roads driven

1     Depot         WarehouseB         8   Depot > WarehouseB

2     WarehouseB    Mall               7   WarehouseB > CityCenter > Mall

3     Mall          Suburb             6   Mall > Suburb

4     Suburb        CityCenter         4   Suburb > CityCenter

5     CityCenter    WarehouseA         3   CityCenter > WarehouseA

6     WarehouseA    Depot              4   WarehouseA > Depot

Total distance: 32 KM

Nearest Neighbour (greedy baseline): 33 KM

Brute force (true optimal): 32 KM

Distance saved vs baseline: 1 KM (3.0%)

Verification: the GA found the TRUE OPTIMAL tour

--------------------------------------------------

**3.1 Why a baseline route is shown**

A heuristic result means nothing on its own, since "the route is 32 km" cannot be judged without something to compare against. The program therefore also prints a Nearest Neighbour route (always drive to the nearest unvisited stop), which is the obvious common-sense way a person would plan the trip. Nearest Neighbour is itself a greedy algorithm, so the comparison also shows the difference between the greedy strategy used in Problem 1 and the heuristic strategy used here.

Where there are 9 or fewer stops, the program additionally checks every possible tour by brute force to confirm how close the Genetic Algorithm came. This is how correctness was verified during testing.

**4. File Structure**

problem3_tsp_genetic/

├── problem3_tsp_genetic.py   # Main program (all logic in one file)

├── sample_runs.txt           # Recorded output of all 7 test cases

└── README.md                 # This file

**5. Known Limitations:**

1. Does not guarantee the optimal tour. This is expected for a heuristic, and the comparison table reports how far the result is from the optimum whenever the network is small enough to check.
2. Results depend on the settings used. Too small a population or too few generations can end the search before the best route is found, which Option 5 lets you demonstrate.
3. Brute-force verification is only run for 9 or fewer delivery stops, since checking every tour beyond that takes too long.
4. Requires non-negative distances, because the Dijkstra step used to build the road distance matrix does not guarantee correct results with negative weights. Negative distances are rejected during custom input.
5. Assumes roads are bidirectional (two-way), matching a typical city road network.
6. Location names are case sensitive and cannot contain spaces (use CityCenter, not City Center).
7. Does not visualize the graph; output is text-based only, as required by the assignment brief (no GUI needed).