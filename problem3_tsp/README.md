# Problem 3: Heuristic Algorithm — TSP using a Genetic Algorithm

Part of the **Smart Delivery Route Optimization System** (CSC2103 group project).

| | |
|---|---|
| File | `problem3_tsp_genetic.py` |
| Language | Python 3 — **zero import statements** |
| Category | Heuristic Algorithm |
| Problem | Travelling Salesman Problem |
| Method | Genetic Algorithm: population, fitness, tournament selection, Order Crossover (OX1), inversion mutation, elitism |

## How to run

```bash
python3 problem3_tsp_genetic.py
```

| Menu | Network used |
|---|---|
| 1 | Built-in sample delivery network — **the same graph as Problem 1** (Depot + 5 zones) |
| 2 | Extended delivery network — the same city plus 4 outer zones (9 stops) |
| 3 | Built-in disconnected network — **the same edge case as Problem 1** (`IsolatedZone`) |
| 4 | Custom network entered by the user |
| 5 | Sample network with your own GA settings (population, generations, mutation rate, tournament size, elitism, seed) |
| 6 | Exit |

At the stops prompt, type location names separated by spaces, or `ALL`.

## Where Problem 3 sits in the system

1. **Problem 1 — Greedy / Dijkstra:** shortest road route between *two* locations.
2. **Problem 2 — DP / 0-1 Knapsack:** *which* packages the truck carries.
3. **Problem 3 — Heuristic / GA:** the *order* the truck visits the chosen stops.

Problem 3 reuses the Problem 1 graph and calls Dijkstra internally to build a matrix
of shortest **road** distances between stops, so a tour never assumes a road that
doesn't exist. Every leg of the final route is printed with the roads actually
driven, e.g. `Mall > CityCenter > WarehouseA > Depot`.

## The five essential GA components

Each has its own commented section in the source file.

| Component | Where | What it does |
|---|---|---|
| **Population** | Section 5 | A chromosome is a permutation of the delivery stops (the depot is implicit). Generation 0 is created by a manual Fisher–Yates shuffle. |
| **Fitness** | Section 6 | `fitness = 1 / total distance`, so shorter routes score higher. Distance is kept too, since that's the number the delivery company cares about. |
| **Selection** | Section 7 | Tournament selection — a few random routes compete, the fittest becomes a parent. Always picking the single best route would make the whole population identical and stop the search early. |
| **Crossover** | Section 8 | Order Crossover (OX1). Plain single-point crossover would make a child visit some stops twice and miss others; OX1 always yields a valid route. |
| **Mutation** | Section 9 | Inversion (reverse a random segment) — the 2-opt move that un-crosses a route doubling back on itself. Crossover can only recombine what already exists; mutation is what escapes a local optimum. |

Plus **elitism** (Section 10): the best few routes are copied forward untouched, so
the answer can never get worse between generations, and **early stopping** once the
best distance stops improving.

## Why the Nearest Neighbour baseline is kept

It is worth keeping, for three reasons:

1. **A heuristic result means nothing on its own.** "The GA found a 32 km route" is
   unverifiable in isolation. The comparison table is what turns it into evidence.
2. **The brief requires showing the algorithm "may not always guarantee the optimal
   answer, but aims to find a good solution efficiently."** That claim can't be
   demonstrated with a single number — it needs a reference point.
3. **Nearest Neighbour is itself a greedy algorithm,** so the output becomes a direct
   greedy-vs-heuristic contrast, linking Problem 3 back to Problem 1's category.

On the sample network it earns its place immediately: Nearest Neighbour returns
**33 km**, the GA returns **32 km** — the greedy choice of visiting the closest stop
first is exactly the trap the GA avoids.

Brute-force verification runs automatically whenever there are 9 or fewer stops, and
proves the GA result equals the true optimum.

## Note on the sample network size

The Problem 1 graph has 5 delivery stops = only **12 distinct tours**, so the GA
solves it almost immediately and the evolution table looks flat. Menu option 2 uses
the same city extended to **9 stops = 20,160 tours**, where the population visibly
improves (66 km at generation 0 down to 56 km) — that run is the better screenshot
for the report's explanation of *why* a heuristic is needed.

## Manual implementation (no built-in algorithmic libraries)

| Needed | Built-in avoided | Written manually |
|---|---|---|
| Randomness | `random` | `SimpleRandom` — Park–Miller LCG |
| Sorting the population | `sorted()` / `.sort()` | `insertion_sort_population()` |
| Shortest road distances | any graph library | `dijkstra()` |
| Permutations (verifier only) | `itertools.permutations` | `generate_all_permutations()` |
| Shuffling | `random.shuffle` | Fisher–Yates in `create_random_route()` |

Runs are reproducible: the same seed always gives the same result, so every test case
below can be re-run and checked.

## Test cases (full transcripts in `sample_runs.txt`)

| # | Type | Input | Result |
|---|---|---|---|
| 1 | Typical | Sample network, all 5 stops | GA 32 km vs baseline 33 km; matches brute-force optimum |
| 2 | Larger | Extended network, 9 stops | 66 km → 56 km over 68 generations; matches optimum, 3,060 routes scored vs 40,320 tours |
| 3 | Edge | Disconnected network | Reports no route to `IsolatedZone`, no crash |
| 4 | Edge | Only 2 delivery stops | Single tour exists, GA skipped |
| 5 | Custom | User-entered 5-location network | Valid tour produced |
| 6 | Parameters | Population 20, 30 generations, mutation 0.5 | Still reaches 32 km with only 620 evaluations |
| 7 | Validation | Bad menu option, unknown location, depot as a stop, malformed road, negative distance | Each rejected with a message and re-prompted |