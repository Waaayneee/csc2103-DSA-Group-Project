"""
CSC2103 Group Project - Problem 3: Heuristic Algorithm for the Travelling Salesman Problem (TSP)
Algorithm: Travelling Salesman Problem (TSP) using a Genetic Algorithm (GA)

Scenario
--------
Problem 1 (Greedy / Dijkstra) found the shortest road route between TWO
locations. Problem 2 (DP / 0-1 Knapsack) decided WHICH packages the truck
carries. Problem 3 answers the final question: given the delivery stops the
truck must visit, in WHAT ORDER should it visit them so that the total
distance driven (depot -> every stop -> back to depot) is as small as
possible?

That is the Travelling Salesman Problem. For n delivery stops there are
(n-1)!/2 distinct tours. Five stops is only 12 tours, but nine stops is
20,160 and fifteen stops is over 43 billion, so checking every possible order
becomes impossible very quickly.

Why a HEURISTIC fits this problem
---------------------------------
A Genetic Algorithm does NOT guarantee the shortest possible tour. Instead it
imitates natural selection:

    a POPULATION of candidate routes is created at random,
    each route is given a FITNESS score based on how short it is,
    SELECTION picks the fitter routes to become parents,
    CROSSOVER combines two parents into a new child route,
    MUTATION randomly alters a child to keep the population varied,

and this repeats for many generations. Short route fragments survive and
spread through the population, so the best answer improves steadily and
usually lands on (or very close to) the optimum after examining only a tiny
fraction of the possible tours. That is the defining trade-off of a
heuristic: near-optimal quality in practical time, rather than guaranteed
optimal quality in impractical time.

Manual implementation note
--------------------------
No external or built-in algorithmic libraries are used anywhere:
    randomness      -> own Linear Congruential Generator (no `random` module)
    sorting         -> own insertion sort (no sorted() / .sort())
    shortest paths  -> own Dijkstra (no graph library)
    permutations    -> own recursive generator (no itertools)
The file contains zero import statements.
"""


# ===========================================================================
# SECTION 1: MANUAL PSEUDO-RANDOM NUMBER GENERATOR
# ===========================================================================
# A Genetic Algorithm needs randomness, but Python's `random` module is a
# built-in library. To keep the whole solution hand-written (and to make every
# run reproducible when we test it) we implement the classic Lehmer /
# Park-Miller Linear Congruential Generator:
#
#       state = (state * 48271) mod (2^31 - 1)
#
# The same seed always produces the same sequence of numbers, which means the
# lecturer can re-run any of our test cases and get identical output.

class SimpleRandom:
    """Minimal reproducible pseudo-random generator (no libraries used)."""

    MODULUS = 2147483647       # 2^31 - 1, a Mersenne prime
    MULTIPLIER = 48271

    def __init__(self, seed=2103):
        self.state = seed % self.MODULUS
        if self.state <= 0:
            self.state += self.MODULUS - 1

    def _next_raw(self):
        """Advance the generator and return the raw internal state."""
        self.state = (self.state * self.MULTIPLIER) % self.MODULUS
        return self.state

    def next_float(self):
        """Return a pseudo-random float in the range [0.0, 1.0)."""
        return (self._next_raw() - 1) / float(self.MODULUS - 1)

    def next_int(self, low, high):
        """Return a pseudo-random integer in the INCLUSIVE range [low, high]."""
        if low >= high:
            return low
        return low + self._next_raw() % (high - low + 1)


# ===========================================================================
# SECTION 2: MANUAL HELPERS (sorting and permutations)
# ===========================================================================

def insertion_sort_population(population, distances, fitnesses):
    """
    Sorts the population from SHORTEST to LONGEST route using a manually
    written insertion sort, because built-in sorting is not allowed for the
    core logic. All three lists are moved together so that population[i],
    distances[i] and fitnesses[i] always describe the same route.
    """
    for i in range(1, len(population)):
        current_route = population[i]
        current_distance = distances[i]
        current_fitness = fitnesses[i]
        j = i - 1

        # Shift every longer route one slot to the right.
        while j >= 0 and distances[j] > current_distance:
            population[j + 1] = population[j]
            distances[j + 1] = distances[j]
            fitnesses[j + 1] = fitnesses[j]
            j -= 1

        population[j + 1] = current_route
        distances[j + 1] = current_distance
        fitnesses[j + 1] = current_fitness


def generate_all_permutations(items):
    """
    Recursively produces every possible ordering of `items`.
    Used ONLY by the brute-force verifier (never by the GA itself), and
    written manually instead of using itertools.permutations.
    """
    if len(items) <= 1:
        return [list(items)]

    all_orders = []
    for index in range(len(items)):
        chosen = items[index]
        remaining = items[:index] + items[index + 1:]
        for sub_order in generate_all_permutations(remaining):
            all_orders.append([chosen] + sub_order)
    return all_orders


def factorial(n):
    """Small manual factorial, used to report the size of the search space."""
    result = 1
    for i in range(2, n + 1):
        result *= i
    return result


# ===========================================================================
# SECTION 3: THE DELIVERY NETWORK
# ===========================================================================
# The same graph model used in Problem 1: an adjacency dictionary where each
# key is a location and its inner dictionary holds the neighbouring locations
# and the road distance to each. Roads are two-way (bidirectional).

def build_sample_graph():
    """
    The SAME preloaded delivery network used in Problem 1, so all three
    programs in this project describe one consistent city. A depot plus five
    delivery zones.
    """
    graph = {
        "Depot": {},
        "WarehouseA": {},
        "WarehouseB": {},
        "CityCenter": {},
        "Suburb": {},
        "Mall": {},
    }
    edges = [
        ("Depot", "WarehouseA", 4),
        ("Depot", "WarehouseB", 8),
        ("WarehouseA", "CityCenter", 3),
        ("WarehouseB", "CityCenter", 2),
        ("WarehouseB", "Suburb", 7),
        ("CityCenter", "Mall", 5),
        ("CityCenter", "Suburb", 4),
        ("Suburb", "Mall", 6),
    ]
    for a, b, w in edges:
        graph[a][b] = w
        graph[b][a] = w
    return graph


def build_extended_sample_graph():
    """
    The same city as build_sample_graph(), expanded with four more delivery
    zones on the outskirts.

    Reason for including this network: with only five delivery stops there are
    just 12 possible tours, so the Genetic Algorithm finds the best one almost
    immediately and the evolution is not visible. With nine stops there are
    20,160 possible tours, which is large enough to show the population
    actually improving generation by generation - the behaviour this problem
    category is meant to demonstrate.
    """
    graph = build_sample_graph()
    for name in ("University", "Hospital", "Airport", "Harbour"):
        graph[name] = {}

    extra_edges = [
        ("CityCenter", "University", 6),
        ("Suburb", "Hospital", 5),
        ("Mall", "Airport", 9),
        ("University", "Hospital", 3),
        ("University", "Airport", 8),
        ("Airport", "Harbour", 4),
        ("Harbour", "Hospital", 7),
    ]
    for a, b, w in extra_edges:
        graph[a][b] = w
        graph[b][a] = w
    return graph


def build_disconnected_sample_graph():
    """
    The SAME edge-case network used in Problem 1: it contains a location that
    no road reaches. Used to confirm the program reports that no delivery tour
    is possible instead of crashing or inventing a route.
    """
    graph = {
        "Depot": {"WarehouseA": 5},
        "WarehouseA": {"Depot": 5},
        "IsolatedZone": {},        # no roads connect to this location
    }
    return graph


def read_custom_graph():
    """
    Builds a delivery network from user input, applying the same validation
    rules used in Problem 1: known location names only, numeric distances, and
    no negative distances.
    """
    graph = {}

    count = read_int("\nNumber of locations (including the depot): ", 2, 50)
    print("Enter the name of each location (e.g. Depot, WarehouseA, Mall):")
    for i in range(count):
        while True:
            name = input(f"  Location {i + 1} name: ").strip()
            if not name:
                print("    Name cannot be empty. Try again.")
            elif " " in name:
                print("    Name cannot contain spaces (use e.g. CityCenter). Try again.")
            elif name in graph:
                print("    That name has already been used. Try again.")
            else:
                graph[name] = {}
                break

    roads = read_int("\nNumber of roads connecting these locations: ", 1, 500)
    print("\nFor each road, enter: FromLocation ToLocation Distance")
    print("Example: Depot WarehouseA 4\n")

    for i in range(roads):
        while True:
            parts = input(f"  Road {i + 1}: ").strip().split()

            if len(parts) != 3:
                print("    Please enter exactly 3 values: FromLocation ToLocation Distance.")
                continue

            a, b, weight_text = parts

            if a not in graph or b not in graph:
                print("    One of those locations was not registered above. Try again.")
                continue
            if a == b:
                print("    A road must connect two different locations. Try again.")
                continue

            try:
                weight = float(weight_text)
            except ValueError:
                print("    Distance must be a number. Try again.")
                continue

            if weight < 0:
                print("    Distance cannot be negative. Try again.")
                continue

            graph[a][b] = weight
            graph[b][a] = weight
            break

    return graph


# ===========================================================================
# SECTION 4: ROAD DISTANCES BETWEEN STOPS (Dijkstra, reused from Problem 1)
# ===========================================================================
# The truck cannot travel directly between two delivery stops unless a road
# joins them. The real "distance" between stop A and stop B is therefore the
# SHORTEST ROAD DISTANCE between them, which is exactly what Dijkstra's greedy
# algorithm computes. We run Dijkstra once from every stop to build a distance
# matrix, and the Genetic Algorithm then optimises the ORDER of visits on top
# of that matrix.

def dijkstra(graph, source):
    """
    Manual Dijkstra, identical in logic to Problem 1. Used here as a SUPPORT
    routine, not as the Problem 3 algorithm. Returns the shortest distance and
    the previous-node map from `source` to every other location.
    """
    distances = {node: float("inf") for node in graph}
    previous = {node: None for node in graph}
    distances[source] = 0
    visited = set()

    while len(visited) < len(graph):
        # Greedy choice: the unvisited location with the smallest known distance.
        current = None
        smallest = float("inf")
        for node in graph:
            if node not in visited and distances[node] < smallest:
                current = node
                smallest = distances[node]

        if current is None:
            break                       # every remaining location is unreachable

        visited.add(current)

        # Relax every road leaving the location we just finalised.
        for neighbour, weight in graph[current].items():
            if neighbour in visited:
                continue
            new_distance = distances[current] + weight
            if new_distance < distances[neighbour]:
                distances[neighbour] = new_distance
                previous[neighbour] = current

    return distances, previous


def rebuild_road_path(previous, source, target):
    """Walks the `previous` map backwards to recover the roads actually driven."""
    path = []
    node = target
    while node is not None:
        path.append(node)
        node = previous[node]
    path.reverse()
    return path if path[0] == source else None


def build_distance_matrix(graph, locations):
    """
    Builds two lookup tables for the chosen delivery stops:
        distance_matrix[a][b] = shortest road distance from a to b
        road_paths[a][b]      = the list of locations driven through

    Also returns the first pair of stops with no road route between them, or
    None when every chosen stop is reachable.
    """
    distance_matrix = {}
    road_paths = {}
    unreachable_pair = None

    for origin in locations:
        distances, previous = dijkstra(graph, origin)
        distance_matrix[origin] = {}
        road_paths[origin] = {}

        for destination in locations:
            distance_matrix[origin][destination] = distances[destination]
            road_paths[origin][destination] = rebuild_road_path(
                previous, origin, destination)

            if distances[destination] == float("inf") and unreachable_pair is None:
                unreachable_pair = (origin, destination)

    return distance_matrix, road_paths, unreachable_pair


# ===========================================================================
# SECTION 5: GA PART 1 - CHROMOSOME AND POPULATION
# ===========================================================================
# CHROMOSOME: one candidate solution, stored as a list of delivery stops in
#             visiting order, for example ["Mall", "Suburb", "CityCenter"].
#             The depot is not stored because every tour starts and ends
#             there. Each stop appears exactly once, so a chromosome is a
#             permutation of the delivery stops.
#
# POPULATION: a list of many such chromosomes. Generation 0 is created purely
#             at random, so the algorithm starts with a wide spread of
#             different routes rather than one biased guess.

def create_random_route(stops, rng):
    """
    Produces one random permutation of the delivery stops using a manually
    written Fisher-Yates shuffle: walk from the last position backwards,
    swapping each item with a randomly chosen earlier item.
    """
    route = list(stops)
    for i in range(len(route) - 1, 0, -1):
        j = rng.next_int(0, i)
        route[i], route[j] = route[j], route[i]
    return route


def create_initial_population(stops, population_size, rng):
    """Generation 0: `population_size` completely random candidate routes."""
    population = []
    for _ in range(population_size):
        population.append(create_random_route(stops, rng))
    return population


# ===========================================================================
# SECTION 6: GA PART 2 - FITNESS
# ===========================================================================
# The fitness function tells the algorithm how GOOD a candidate route is.
# Here a route is good when it is short, so we first measure its total
# distance and then convert that into a fitness value where HIGHER IS BETTER:
#
#       fitness = 1 / total distance
#
# The inversion matters because selection is written to prefer higher fitness,
# which is the usual convention for genetic algorithms. Distance is kept as
# well because it is the value that is meaningful to the delivery company.

def tour_distance(route, depot, distance_matrix):
    """
    Total distance driven for one candidate route.
    The chromosome holds only the delivery stops, so the leg from the depot to
    the first stop and the leg from the last stop back to the depot are added
    here - the truck must return to base.
    """
    if not route:
        return 0.0

    total = distance_matrix[depot][route[0]]
    for i in range(len(route) - 1):
        total += distance_matrix[route[i]][route[i + 1]]
    total += distance_matrix[route[-1]][depot]
    return total


def calculate_fitness(distance):
    """Converts a route distance into a fitness score where higher is better."""
    if distance <= 0:
        return float("inf")
    return 1.0 / distance


def evaluate_population(population, depot, distance_matrix):
    """Scores every route in the population. Returns (distances, fitnesses)."""
    distances = []
    fitnesses = []
    for route in population:
        distance = tour_distance(route, depot, distance_matrix)
        distances.append(distance)
        fitnesses.append(calculate_fitness(distance))
    return distances, fitnesses


# ===========================================================================
# SECTION 7: GA PART 3 - SELECTION
# ===========================================================================
# Selection decides which routes get to become parents. We use TOURNAMENT
# SELECTION: pick a few routes from the population at random and return the
# fittest one among them.
#
# Why not simply always pick the single best route? Because the whole
# population would quickly become copies of that one route, and the algorithm
# would stop discovering anything new (premature convergence). A tournament
# strongly favours good routes while still giving weaker ones an occasional
# chance, which keeps the population varied.

def tournament_selection(population, fitnesses, tournament_size, rng):
    """Randomly picks `tournament_size` routes and returns the fittest one."""
    best_index = rng.next_int(0, len(population) - 1)

    for _ in range(tournament_size - 1):
        challenger_index = rng.next_int(0, len(population) - 1)
        if fitnesses[challenger_index] > fitnesses[best_index]:
            best_index = challenger_index

    return population[best_index]


# ===========================================================================
# SECTION 8: GA PART 4 - CROSSOVER
# ===========================================================================
# Crossover combines two parent routes into a child route, so that good
# travel patterns from both parents can be inherited.
#
# Ordinary single-point crossover cannot be used for the TSP: cutting two
# routes and gluing the halves together would make the child visit some stops
# twice and miss others entirely, which is not a valid delivery route.
#
# ORDER CROSSOVER (OX1) solves this:
#   1. copy a random slice of parent 1 into the child at the same positions;
#   2. fill the remaining positions with the stops of parent 2, in the order
#      parent 2 lists them, skipping any stop already taken from parent 1.
# The result always visits every stop exactly once.
#
# Example:  parent1 = [A, B, C, D, E]   slice = positions 1-2  -> [_, B, C, _, _]
#           parent2 = [C, E, A, D, B]   remaining in p2 order: E, A, D
#           child   = [E, B, C, A, D]

def order_crossover(parent1, parent2, rng):
    """Order Crossover (OX1). Always returns a valid permutation of the stops."""
    size = len(parent1)
    if size < 2:
        return list(parent1)

    # Step 1: choose the random slice to inherit from parent 1.
    start = rng.next_int(0, size - 1)
    end = rng.next_int(0, size - 1)
    if start > end:
        start, end = end, start

    child = [None] * size
    taken = set()
    for i in range(start, end + 1):
        child[i] = parent1[i]
        taken.add(parent1[i])

    # Step 2: fill the empty positions using parent 2's ordering.
    fill_position = 0
    for stop in parent2:
        if stop in taken:
            continue
        while child[fill_position] is not None:
            fill_position += 1
        child[fill_position] = stop
        taken.add(stop)

    return child


# ===========================================================================
# SECTION 9: GA PART 5 - MUTATION
# ===========================================================================
# Mutation makes a small random change to a child route. It matters because
# crossover can only recombine material that already exists in the population.
# Without mutation the population runs out of new ideas and gets stuck in a
# local optimum - a route that cannot be improved by recombination alone even
# though a shorter route exists.
#
# We use INVERSION MUTATION: reverse a randomly chosen segment of the route.
# Reversing is preferred over simply swapping two stops because it is the
# classic 2-opt move, which "un-crosses" a route that doubles back on itself
# while leaving the rest of the visiting order intact. In our testing it
# reached the optimal tour far more often than plain swap mutation.
#
# Example:  [A, B, C, D, E]  reverse positions 1-3  ->  [A, D, C, B, E]

def inversion_mutation(route, mutation_rate, rng):
    """With probability `mutation_rate`, reverses a random segment of the route."""
    if len(route) >= 2 and rng.next_float() < mutation_rate:
        start = rng.next_int(0, len(route) - 1)
        end = rng.next_int(0, len(route) - 1)
        if start > end:
            start, end = end, start

        while start < end:
            route[start], route[end] = route[end], route[start]
            start += 1
            end -= 1

    return route


# ===========================================================================
# SECTION 10: THE GENETIC ALGORITHM (main heuristic loop)
# ===========================================================================
# One generation of the loop:
#
#   1. ELITISM      - copy the best few routes into the new generation
#                     unchanged, so the best answer can never get worse.
#   2. SELECTION    - run two tournaments to choose two parents.
#   3. CROSSOVER    - combine those parents into a child route.
#   4. MUTATION     - possibly alter the child.
#   5. repeat 2-4 until the new generation is full, then evaluate and sort it.
#
# The loop ends either after the requested number of generations, or early if
# the best distance has not improved for a while (the population has
# converged and further work would be wasted).

def genetic_algorithm(depot, stops, distance_matrix, settings, rng,
                      show_progress=True):
    """
    Evolves a population of delivery routes.

    Returns:
        best_route        - the shortest route found
        best_distance     - its total distance
        generations_run   - how many generations were actually completed
        evaluations       - how many candidate routes were scored in total
    """
    # Edge case: with 0, 1 or 2 stops there is only one possible tour, so
    # there is nothing to evolve.
    if len(stops) <= 2:
        route = list(stops)
        return route, tour_distance(route, depot, distance_matrix), 0, len(stops)

    population_size = settings["population_size"]
    elite_count = settings["elite_count"]

    # ----- Generation 0: a completely random population --------------------
    population = create_initial_population(stops, population_size, rng)
    distances, fitnesses = evaluate_population(population, depot, distance_matrix)
    insertion_sort_population(population, distances, fitnesses)

    if show_progress:
        print_population_sample(population, distances, fitnesses,
                                population_size)

    best_route = list(population[0])
    best_distance = distances[0]
    stagnant_generations = 0
    generation = 0

    if show_progress:
        print_progress_header()
        print_progress_row(0, distances[0], average(distances), best_distance)

    # ----- Evolution loop --------------------------------------------------
    for generation in range(1, settings["generations"] + 1):

        # 1. ELITISM: the best routes survive into the next generation
        #    untouched, guaranteeing the solution never deteriorates.
        new_population = []
        for i in range(elite_count):
            new_population.append(list(population[i]))

        # 2-4. Fill the rest of the generation by breeding.
        while len(new_population) < population_size:
            parent1 = tournament_selection(
                population, fitnesses, settings["tournament_size"], rng)
            parent2 = tournament_selection(
                population, fitnesses, settings["tournament_size"], rng)

            child = order_crossover(parent1, parent2, rng)
            child = inversion_mutation(child, settings["mutation_rate"], rng)

            new_population.append(child)

        # 5. Score and rank the new generation.
        population = new_population
        distances, fitnesses = evaluate_population(
            population, depot, distance_matrix)
        insertion_sort_population(population, distances, fitnesses)

        # Track the best route found across ALL generations so far.
        if distances[0] < best_distance:
            best_distance = distances[0]
            best_route = list(population[0])
            stagnant_generations = 0
        else:
            stagnant_generations += 1

        if show_progress and (generation % settings["report_every"] == 0):
            print_progress_row(generation, distances[0], average(distances),
                               best_distance)

        # Early stopping: the population has converged.
        if stagnant_generations >= settings["stagnation_limit"]:
            if show_progress:
                print(f"  (Converged: no improvement for "
                      f"{settings['stagnation_limit']} generations, stopping "
                      f"early at generation {generation}.)")
            break

    evaluations = population_size * (generation + 1)
    return best_route, best_distance, generation, evaluations


def average(values):
    """Plain arithmetic mean, kept separate so the GA loop stays readable."""
    if not values:
        return 0.0
    return sum(values) / float(len(values))


# ===========================================================================
# SECTION 11: BASELINE AND VERIFIER (used for testing and validation)
# ===========================================================================

def nearest_neighbour_route(depot, stops, distance_matrix):
    """
    A simple GREEDY baseline: from the current location, always drive to the
    nearest stop not yet visited.

    Why this is included: a heuristic result is meaningless on its own. Saying
    the Genetic Algorithm found a 48 km route proves nothing unless there is
    something to compare it against. Nearest Neighbour is the obvious
    "common sense" way a person would plan the trip, so it is a fair reference
    point, and because it is itself a greedy algorithm it also shows the
    difference between the greedy strategy used in Problem 1 and the heuristic
    strategy used here.
    """
    unvisited = list(stops)
    route = []
    current = depot

    while unvisited:
        nearest_index = 0
        for i in range(1, len(unvisited)):
            if distance_matrix[current][unvisited[i]] < \
               distance_matrix[current][unvisited[nearest_index]]:
                nearest_index = i

        current = unvisited[nearest_index]
        route.append(current)
        unvisited = unvisited[:nearest_index] + unvisited[nearest_index + 1:]

    return route, tour_distance(route, depot, distance_matrix)


def brute_force_optimal(depot, stops, distance_matrix):
    """
    Checks EVERY possible visiting order and returns the true shortest tour.
    Only usable for small inputs; it exists purely to verify how close the
    heuristic came. Returns (route, distance, tours_checked).
    """
    if len(stops) <= 1:
        route = list(stops)
        return route, tour_distance(route, depot, distance_matrix), 1

    # Fixing the first stop removes the mirror-image duplicate of each tour
    # (driving a loop clockwise or anticlockwise covers the same distance).
    fixed_stop = stops[0]
    best_route = None
    best_distance = float("inf")
    tours_checked = 0

    for tail in generate_all_permutations(stops[1:]):
        candidate = [fixed_stop] + tail
        distance = tour_distance(candidate, depot, distance_matrix)
        tours_checked += 1
        if distance < best_distance:
            best_distance = distance
            best_route = candidate

    return best_route, best_distance, tours_checked


# ===========================================================================
# SECTION 12: OUTPUT FORMATTING
# ===========================================================================

def print_header(title):
    print("\n" + "=" * 66)
    print(f" {title}")
    print("=" * 66)


def print_distance_matrix(locations, distance_matrix):
    """Shows the shortest ROAD distance between every pair of chosen stops."""
    width = 12 + 10 * len(locations)
    print("\nShortest road distance between locations (km, computed by Dijkstra):")
    print("-" * width)
    print(f"{'':<12}" + "".join(f"{name[:9]:>10}" for name in locations))
    for origin in locations:
        row = f"{origin[:11]:<12}"
        for destination in locations:
            value = distance_matrix[origin][destination]
            row += f"{('-' if value == float('inf') else value):>10}"
        print(row)
    print("-" * width)


def print_population_sample(population, distances, fitnesses, population_size,
                            show=5):
    """
    Shows the fittest few routes of the random starting population, so the
    starting point of the search is visible before evolution begins.
    """
    print(f"\nGeneration 0: {population_size} random routes created. "
          f"Fittest {show} shown below.")
    print("-" * 66)
    print(f"{'Route (delivery order)':<46}{'Distance':>10}{'Fitness':>10}")
    print("-" * 66)
    for i in range(min(show, len(population))):
        route_text = " ".join(population[i])
        if len(route_text) > 44:
            route_text = route_text[:41] + "..."
        print(f"{route_text:<46}{distances[i]:>10.1f}{fitnesses[i]:>10.4f}")
    print("-" * 66)
    print("Fitness = 1 / distance, so a shorter route scores higher.")


def print_progress_header():
    print("\nEvolution progress")
    print("-" * 66)
    print(f"{'Generation':<12}{'Best in Gen':>14}{'Average':>14}{'Best Ever':>14}")
    print("-" * 66)


def print_progress_row(generation, best_in_gen, avg, best_ever):
    print(f"{generation:<12}{best_in_gen:>14.1f}{avg:>14.1f}{best_ever:>14.1f}")


def print_route(depot, route, distance_matrix, road_paths, label):
    """Prints the delivery order, each leg's distance, and the roads driven."""
    print(f"\n{label}")
    print("-" * 66)

    full_order = [depot] + route + [depot]
    print("Delivery order : " + " -> ".join(full_order))
    print()
    print(f"{'Leg':<6}{'From':<14}{'To':<14}{'km':>6}   Roads driven")
    print("-" * 66)

    for i in range(len(full_order) - 1):
        origin = full_order[i]
        destination = full_order[i + 1]
        leg = distance_matrix[origin][destination]
        path = road_paths[origin][destination]
        via = " > ".join(path) if path else "n/a"
        print(f"{i + 1:<6}{origin[:13]:<14}{destination[:13]:<14}{leg:>6}   {via}")

    print("-" * 66)
    print(f"TOTAL DISTANCE : {tour_distance(route, depot, distance_matrix)} km")


def print_comparison(ga_distance, ga_evaluations, nn_distance,
                     optimal_distance, tours_checked):
    """Side-by-side result table: the evidence for the testing section."""
    print("\nSolution quality comparison")
    print("-" * 66)
    print(f"{'Method':<36}{'Distance':>12}{'Routes checked':>18}")
    print("-" * 66)
    print(f"{'Nearest Neighbour (greedy baseline)':<36}{nn_distance:>12.1f}{1:>18}")
    print(f"{'Genetic Algorithm (heuristic)':<36}{ga_distance:>12.1f}{ga_evaluations:>18}")
    if optimal_distance is not None:
        print(f"{'Brute force (true optimal)':<36}{optimal_distance:>12.1f}{tours_checked:>18}")
    print("-" * 66)

    if nn_distance > 0:
        saving = (nn_distance - ga_distance) / nn_distance * 100
        if saving > 0:
            print(f"The GA route is {saving:.1f}% shorter than the greedy baseline.")
        else:
            print("The GA matched the greedy baseline on this network.")

    if optimal_distance is not None:
        if abs(ga_distance - optimal_distance) < 1e-9:
            print("Verification    : the GA found the TRUE OPTIMAL tour.")
        else:
            gap = (ga_distance - optimal_distance) / optimal_distance * 100
            print(f"Verification    : the GA route is {gap:.2f}% longer than the "
                  f"optimal tour.")
            print("                  This is expected - a heuristic aims for a good "
                  "solution quickly,")
            print("                  it does not guarantee the best one.")


# ===========================================================================
# SECTION 13: INPUT HANDLING AND VALIDATION
# ===========================================================================

DEFAULT_SETTINGS = {
    "population_size": 60,       # how many candidate routes per generation
    "generations": 200,          # maximum number of generations
    "mutation_rate": 0.30,       # chance that a child is mutated
    "tournament_size": 4,        # how many routes compete to become a parent
    "elite_count": 2,            # best routes copied forward unchanged
    "stagnation_limit": 50,      # stop early after this many non-improving gens
    "report_every": 20,          # how often to print a progress row
    "seed": 2103,                # same seed = same result (reproducible tests)
}


def read_int(prompt, minimum, maximum):
    """Reads a whole number inside [minimum, maximum], re-asking on bad input."""
    while True:
        raw = input(prompt).strip()
        try:
            value = int(raw)
        except ValueError:
            print(f"    Please enter a whole number between {minimum} and {maximum}.")
            continue
        if value < minimum or value > maximum:
            print(f"    Value must be between {minimum} and {maximum}.")
            continue
        return value


def ask_with_default(label, default, minimum, maximum, cast):
    """Prompt showing a default value; pressing Enter accepts that default."""
    while True:
        raw = input(f"{label} [{default}]: ").strip()
        if raw == "":
            return default
        try:
            value = cast(raw)
        except ValueError:
            print(f"    Invalid value. Enter a number between {minimum} and {maximum}.")
            continue
        if value < minimum or value > maximum:
            print(f"    Value must be between {minimum} and {maximum}.")
            continue
        return value


def ask_settings():
    """Lets the user tune the GA parameters; blank input keeps the default."""
    settings = dict(DEFAULT_SETTINGS)
    print("\nGenetic Algorithm parameters (press Enter to keep the default):")

    settings["population_size"] = ask_with_default(
        "  Population size", settings["population_size"], 4, 500, int)
    settings["generations"] = ask_with_default(
        "  Number of generations", settings["generations"], 1, 5000, int)
    settings["mutation_rate"] = ask_with_default(
        "  Mutation rate (0.0 - 1.0)", settings["mutation_rate"], 0.0, 1.0, float)
    settings["tournament_size"] = ask_with_default(
        "  Tournament size", settings["tournament_size"], 2,
        settings["population_size"], int)
    settings["elite_count"] = ask_with_default(
        "  Elite routes kept per generation", settings["elite_count"], 0,
        settings["population_size"] - 1, int)
    settings["seed"] = ask_with_default(
        "  Random seed (same seed = same result)", settings["seed"], 1, 999999, int)

    settings["report_every"] = max(1, settings["generations"] // 10)
    return settings


def choose_depot_and_stops(graph):
    """
    Asks which location is the depot and which locations must be delivered to.
    Validation: names must exist, the depot cannot also be a delivery stop,
    and at least one stop is required.
    """
    locations = list(graph.keys())

    print("\nAvailable locations:")
    for i, name in enumerate(locations):
        print(f"  {i + 1}. {name}")

    while True:
        depot = input("\nEnter the DEPOT (starting location): ").strip()
        if depot in graph:
            break
        print("    That location does not exist in the network. Try again.")

    print("\nEnter the delivery stops separated by spaces, or type ALL to")
    print("deliver to every other location.")

    while True:
        raw = input("Delivery stops: ").strip()

        if raw.upper() == "ALL":
            return depot, [name for name in locations if name != depot]

        chosen = raw.split()
        if not chosen:
            print("    At least one delivery stop is required. Try again.")
            continue

        stops = []
        valid = True
        for name in chosen:
            if name not in graph:
                print(f"    '{name}' does not exist in the network. Try again.")
                valid = False
                break
            if name == depot:
                print("    The depot cannot also be a delivery stop. Try again.")
                valid = False
                break
            if name not in stops:            # duplicates are ignored silently
                stops.append(name)

        if valid:
            return depot, stops


# ===========================================================================
# SECTION 14: RUNNING ONE COMPLETE CASE
# ===========================================================================

def run_case(graph, settings, label):
    """
    One full run of the system:
        choose stops -> build the road distance matrix -> run the GA ->
        compare the result against the greedy baseline and, where the network
        is small enough, against the true optimum.
    """
    print_header(label)
    depot, stops = choose_depot_and_stops(graph)

    # --- Step 1: shortest road distances between the chosen locations ------
    locations = [depot] + stops
    distance_matrix, road_paths, unreachable = build_distance_matrix(
        graph, locations)

    if unreachable is not None:
        print(f"\nNo route exists between '{unreachable[0]}' and "
              f"'{unreachable[1]}'.")
        print("These locations are not connected by any road, so a delivery")
        print("tour covering the selected stops is impossible.")
        return

    print_distance_matrix(locations, distance_matrix)

    # --- Edge case: only one tour is possible ------------------------------
    if len(stops) <= 2:
        route = list(stops)
        print(f"\nOnly {len(stops)} delivery stop(s) selected, so just one tour")
        print("is possible and no search is needed.")
        print_route(depot, route, distance_matrix, road_paths,
                    "FINAL DELIVERY ROUTE")
        return

    # --- Step 2: greedy baseline for comparison ----------------------------
    nn_route, nn_distance = nearest_neighbour_route(depot, stops, distance_matrix)

    # --- Step 3: run the heuristic -----------------------------------------
    print(f"\nDelivery stops  : {len(stops)}")
    print(f"Possible tours  : {factorial(len(stops) - 1) // 2} distinct visiting orders")
    print(f"GA settings     : population={settings['population_size']}, "
          f"generations={settings['generations']}, "
          f"mutation={settings['mutation_rate']}, seed={settings['seed']}")

    rng = SimpleRandom(settings["seed"])
    ga_route, ga_distance, generations_run, evaluations = genetic_algorithm(
        depot, stops, distance_matrix, settings, rng)

    # --- Step 4: results ---------------------------------------------------
    print_route(depot, nn_route, distance_matrix, road_paths,
                "BASELINE ROUTE (Nearest Neighbour, greedy)")
    print_route(depot, ga_route, distance_matrix, road_paths,
                "FINAL DELIVERY ROUTE (Genetic Algorithm)")

    # --- Step 5: verification where the network is small enough ------------
    optimal_distance = None
    tours_checked = None
    if len(stops) <= 9:
        optimal_route, optimal_distance, tours_checked = brute_force_optimal(
            depot, stops, distance_matrix)
    else:
        print("\nBrute-force verification skipped: with more than 9 stops there")
        print("are too many tours to check every one.")

    print_comparison(ga_distance, evaluations, nn_distance,
                     optimal_distance, tours_checked)
    print(f"\nGenerations completed : {generations_run}")


# ===========================================================================
# SECTION 15: MAIN PROGRAM / MENU
# ===========================================================================

def main():
    print("=" * 66)
    print(" CSC2103 Problem 3: Heuristic Algorithm")
    print(" Smart Delivery Route Optimization System")
    print(" Travelling Salesman Problem using a Genetic Algorithm")
    print("=" * 66)

    while True:
        print("\nMenu:")
        print("  1. Run built-in sample delivery network")
        print("  2. Run extended delivery network (larger search space)")
        print("  3. Run built-in DISCONNECTED network (edge case test)")
        print("  4. Enter a custom delivery network")
        print("  5. Run sample network with your own GA settings")
        print("  6. Exit")
        choice = input("Select an option (1-6): ").strip()

        if choice == "1":
            run_case(build_sample_graph(), dict(DEFAULT_SETTINGS),
                     "Sample Delivery Network")
        elif choice == "2":
            run_case(build_extended_sample_graph(), dict(DEFAULT_SETTINGS),
                     "Extended Delivery Network")
        elif choice == "3":
            run_case(build_disconnected_sample_graph(), dict(DEFAULT_SETTINGS),
                     "Disconnected Network (Edge Case)")
        elif choice == "4":
            run_case(read_custom_graph(), dict(DEFAULT_SETTINGS),
                     "Custom Delivery Network")
        elif choice == "5":
            run_case(build_sample_graph(), ask_settings(),
                     "Sample Delivery Network (Custom GA Settings)")
        elif choice == "6":
            print("Exiting program.")
            break
        else:
            print("Invalid option, please enter 1, 2, 3, 4, 5 or 6.")


if __name__ == "__main__":
    main()