"""
CSC2103 Problem 3: Heuristic Algorithm
Smart Delivery Route Optimization System
Travelling Salesman Problem solved with a Genetic Algorithm.

Problem 3 decides the ORDER the truck visits its stops. With n stops there 
are (n-1)!/2 tours, so a heuristic is used:
it does not guarantee the shortest tour, but finds a very good one quickly.

No libraries are used - randomness, sorting, shuffling, permutations and
shortest paths are all written manually. The file has no import statements.
"""


# ===========================================================================
# SECTION 1: MANUAL HELPERS (replace random / sorted / itertools)
# ===========================================================================

class SimpleRandom:
    """Park-Miller LCG: state = (state * 48271) mod (2^31 - 1).
    Same seed always gives the same sequence, so every test run is repeatable."""

    MODULUS = 2147483647
    MULTIPLIER = 48271

    def __init__(self, seed=2103):
        self.state = seed % self.MODULUS
        if self.state <= 0:
            self.state += self.MODULUS - 1

    def _next_raw(self):
        self.state = (self.state * self.MULTIPLIER) % self.MODULUS
        return self.state

    def next_float(self):
        """Pseudo-random float in [0.0, 1.0)."""
        return (self._next_raw() - 1) / float(self.MODULUS - 1)

    def next_int(self, low, high):
        """Pseudo-random integer in the inclusive range [low, high]."""
        if low >= high:
            return low
        return low + self._next_raw() % (high - low + 1)


def insertion_sort_population(population, distances, fitnesses):
    """Sorts routes shortest-first. All three lists move together so that
    population[i], distances[i] and fitnesses[i] stay describing one route."""
    for i in range(1, len(population)):
        route, distance, fitness = population[i], distances[i], fitnesses[i]
        j = i - 1
        while j >= 0 and distances[j] > distance:
            population[j + 1], distances[j + 1], fitnesses[j + 1] = \
                population[j], distances[j], fitnesses[j]
            j -= 1
        population[j + 1], distances[j + 1], fitnesses[j + 1] = \
            route, distance, fitness


def generate_all_permutations(items):
    """Every ordering of `items`. Used only by the brute-force verifier."""
    if len(items) <= 1:
        return [list(items)]
    orders = []
    for i in range(len(items)):
        for tail in generate_all_permutations(items[:i] + items[i + 1:]):
            orders.append([items[i]] + tail)
    return orders


def factorial(n):
    result = 1
    for i in range(2, n + 1):
        result *= i
    return result


def average(values):
    return sum(values) / float(len(values)) if values else 0.0


# ===========================================================================
# SECTION 2: DELIVERY NETWORKS (same graphs as Problem 1)
# ===========================================================================

def build_sample_graph():
    """The preloaded network from Problem 1: a depot and five delivery zones."""
    graph = {
        "Depot": {}, "WarehouseA": {}, "WarehouseB": {},
        "CityCenter": {}, "Suburb": {}, "Mall": {},
    }
    edges = [
        ("Depot", "WarehouseA", 4), ("Depot", "WarehouseB", 8),
        ("WarehouseA", "CityCenter", 3), ("WarehouseB", "CityCenter", 2),
        ("WarehouseB", "Suburb", 7), ("CityCenter", "Mall", 5),
        ("CityCenter", "Suburb", 4), ("Suburb", "Mall", 6),
    ]
    for a, b, w in edges:
        graph[a][b] = w
        graph[b][a] = w
    return graph


def build_extended_sample_graph():
    """The same city plus four outer zones. Five stops give only 12 possible
    tours, so the GA solves that instantly; nine stops give 20,160 tours, which
    is large enough to show the population actually evolving."""
    graph = build_sample_graph()
    for name in ("University", "Hospital", "Airport", "Harbour"):
        graph[name] = {}
    edges = [
        ("CityCenter", "University", 6), ("Suburb", "Hospital", 5),
        ("Mall", "Airport", 9), ("University", "Hospital", 3),
        ("University", "Airport", 8), ("Airport", "Harbour", 4),
        ("Harbour", "Hospital", 7),
    ]
    for a, b, w in edges:
        graph[a][b] = w
        graph[b][a] = w
    return graph


def build_disconnected_sample_graph():
    """Edge-case network from Problem 1: IsolatedZone has no roads at all."""
    return {
        "Depot": {"WarehouseA": 5},
        "WarehouseA": {"Depot": 5},
        "IsolatedZone": {},
    }


# ===========================================================================
# SECTION 3: ROAD DISTANCES BETWEEN STOPS (Dijkstra, reused from Problem 1)
# ===========================================================================
# The truck drives on roads, so the distance between two stops is the shortest
# ROAD distance between them. Dijkstra is run once from every stop to build a
# distance matrix; the GA then optimises the visiting order on top of it.

def dijkstra(graph, source):
    """Shortest road distance from `source` to every location (greedy)."""
    distances = {node: float("inf") for node in graph}
    previous = {node: None for node in graph}
    distances[source] = 0
    visited = set()

    while len(visited) < len(graph):
        # Greedy choice: nearest unvisited location.
        current, smallest = None, float("inf")
        for node in graph:
            if node not in visited and distances[node] < smallest:
                current, smallest = node, distances[node]
        if current is None:
            break                      # everything left is unreachable
        visited.add(current)

        for neighbour, weight in graph[current].items():   # relax edges
            if neighbour in visited:
                continue
            new_distance = distances[current] + weight
            if new_distance < distances[neighbour]:
                distances[neighbour] = new_distance
                previous[neighbour] = current

    return distances, previous


def rebuild_road_path(previous, source, target):
    """Walks `previous` backwards to recover the roads actually driven."""
    path, node = [], target
    while node is not None:
        path.append(node)
        node = previous[node]
    path.reverse()
    return path if path[0] == source else None


def build_distance_matrix(graph, locations):
    """Returns distance[a][b], roads[a][b], and the first unreachable pair."""
    distance_matrix, road_paths, unreachable = {}, {}, None

    for origin in locations:
        distances, previous = dijkstra(graph, origin)
        distance_matrix[origin], road_paths[origin] = {}, {}
        for destination in locations:
            distance_matrix[origin][destination] = distances[destination]
            road_paths[origin][destination] = rebuild_road_path(
                previous, origin, destination)
            if distances[destination] == float("inf") and unreachable is None:
                unreachable = (origin, destination)

    return distance_matrix, road_paths, unreachable


# ===========================================================================
# SECTION 4: POPULATION
# ===========================================================================
# A chromosome is one candidate route: a list of the delivery stops in visiting
# order, each appearing exactly once. The depot is not stored because every tour
# starts and ends there. Generation 0 is entirely random for a wide spread.

def create_random_route(stops, rng):
    """One random permutation of the stops (manual Fisher-Yates shuffle)."""
    route = list(stops)
    for i in range(len(route) - 1, 0, -1):
        j = rng.next_int(0, i)
        route[i], route[j] = route[j], route[i]
    return route


def create_initial_population(stops, population_size, rng):
    return [create_random_route(stops, rng) for _ in range(population_size)]


# ===========================================================================
# SECTION 5: FITNESS
# ===========================================================================
# A route is good when it is short, so fitness = 1 / distance and higher is
# better, which is the usual convention selection expects. Distance is kept too
# since it is the figure that matters to the delivery company.

def tour_distance(route, depot, distance_matrix):
    """Total km for depot -> every stop -> back to depot."""
    if not route:
        return 0.0
    total = distance_matrix[depot][route[0]]
    for i in range(len(route) - 1):
        total += distance_matrix[route[i]][route[i + 1]]
    return total + distance_matrix[route[-1]][depot]


def calculate_fitness(distance):
    return float("inf") if distance <= 0 else 1.0 / distance


def evaluate_population(population, depot, distance_matrix):
    """Scores every route. Returns (distances, fitnesses)."""
    distances = [tour_distance(r, depot, distance_matrix) for r in population]
    fitnesses = [calculate_fitness(d) for d in distances]
    return distances, fitnesses


# ===========================================================================
# SECTION 6: SELECTION
# ===========================================================================

def tournament_selection(population, fitnesses, tournament_size, rng):
    """Picks `tournament_size` random routes and returns the fittest.
    Always taking the single best route instead would turn the whole population
    into copies of it and stop the search early (premature convergence)."""
    best = rng.next_int(0, len(population) - 1)
    for _ in range(tournament_size - 1):
        challenger = rng.next_int(0, len(population) - 1)
        if fitnesses[challenger] > fitnesses[best]:
            best = challenger
    return population[best]


# ===========================================================================
# SECTION 7: CROSSOVER
# ===========================================================================
# Order Crossover (OX1): copy a random slice of parent 1 into the child, then
# fill the gaps with parent 2's stops in parent 2's order, skipping duplicates.
# Plain single-point crossover cannot be used - it would make the child visit
# some stops twice and miss others, which is not a valid delivery route.
#   parent1 = [A,B,C,D,E], slice 1-2 -> [_,B,C,_,_]
#   parent2 = [C,E,A,D,B], remaining in p2 order: E,A,D -> child [E,B,C,A,D]

def order_crossover(parent1, parent2, rng):
    size = len(parent1)
    if size < 2:
        return list(parent1)

    start, end = rng.next_int(0, size - 1), rng.next_int(0, size - 1)
    if start > end:
        start, end = end, start

    child, taken = [None] * size, set()
    for i in range(start, end + 1):          # slice inherited from parent 1
        child[i] = parent1[i]
        taken.add(parent1[i])

    position = 0
    for stop in parent2:                     # gaps filled in parent 2's order
        if stop in taken:
            continue
        while child[position] is not None:
            position += 1
        child[position] = stop
        taken.add(stop)

    return child


# ===========================================================================
# SECTION 8: MUTATION
# ===========================================================================
# Inversion mutation reverses a random segment, e.g. [A,B,C,D,E] -> [A,D,C,B,E].
# Crossover can only recombine what already exists, so without mutation the
# population gets stuck in a local optimum. Reversing is preferred over swapping
# two stops because it is the 2-opt move, which un-crosses a route that doubles
# back on itself; in testing it reached the optimum far more often.

def inversion_mutation(route, mutation_rate, rng):
    if len(route) >= 2 and rng.next_float() < mutation_rate:
        start, end = rng.next_int(0, len(route) - 1), rng.next_int(0, len(route) - 1)
        if start > end:
            start, end = end, start
        while start < end:
            route[start], route[end] = route[end], route[start]
            start, end = start + 1, end - 1
    return route


# ===========================================================================
# SECTION 9: THE GENETIC ALGORITHM
# ===========================================================================
# Each generation: keep the elite unchanged, then repeatedly select two parents,
# cross them over and mutate the child until the new generation is full.

def genetic_algorithm(depot, stops, distance_matrix, settings, rng, show=True):
    """Returns (best_route, best_distance, generations_run, evaluations)."""
    if len(stops) <= 2:                      # only one tour is possible
        route = list(stops)
        return route, tour_distance(route, depot, distance_matrix), 0, len(stops)

    population_size = settings["population_size"]

    population = create_initial_population(stops, population_size, rng)
    distances, fitnesses = evaluate_population(population, depot, distance_matrix)
    insertion_sort_population(population, distances, fitnesses)

    if show:
        print_population_sample(population, distances, fitnesses, population_size)
        print_progress_header()
        print_progress_row(0, distances[0], average(distances), distances[0])

    best_route, best_distance = list(population[0]), distances[0]
    stagnant, generation = 0, 0

    for generation in range(1, settings["generations"] + 1):
        # Elitism: the best routes survive untouched, so the answer can never
        # get worse from one generation to the next.
        new_population = [list(population[i]) for i in range(settings["elite_count"])]

        while len(new_population) < population_size:
            parent1 = tournament_selection(population, fitnesses,
                                           settings["tournament_size"], rng)
            parent2 = tournament_selection(population, fitnesses,
                                           settings["tournament_size"], rng)
            child = order_crossover(parent1, parent2, rng)
            new_population.append(
                inversion_mutation(child, settings["mutation_rate"], rng))

        population = new_population
        distances, fitnesses = evaluate_population(population, depot, distance_matrix)
        insertion_sort_population(population, distances, fitnesses)

        if distances[0] < best_distance:     # best across ALL generations
            best_route, best_distance = list(population[0]), distances[0]
            stagnant = 0
        else:
            stagnant += 1

        if show and generation % settings["report_every"] == 0:
            print_progress_row(generation, distances[0], average(distances),
                               best_distance)

        if stagnant >= settings["stagnation_limit"]:   # converged, stop early
            if show:
                print(f"  (Converged: no improvement for "
                      f"{settings['stagnation_limit']} generations, stopped at "
                      f"generation {generation}.)")
            break

    return best_route, best_distance, generation, population_size * (generation + 1)


# ===========================================================================
# SECTION 10: BASELINE AND VERIFIER (for testing and validation)
# ===========================================================================

def nearest_neighbour_route(depot, stops, distance_matrix):
    """Greedy baseline: always drive to the nearest unvisited stop.
    Included because a heuristic result means nothing on its own - this is the
    obvious 'common sense' route to measure the GA against, and being greedy it
    also contrasts the Problem 1 strategy with the heuristic used here."""
    unvisited, route, current = list(stops), [], depot

    while unvisited:
        nearest = 0
        for i in range(1, len(unvisited)):
            if distance_matrix[current][unvisited[i]] < \
               distance_matrix[current][unvisited[nearest]]:
                nearest = i
        current = unvisited[nearest]
        route.append(current)
        unvisited = unvisited[:nearest] + unvisited[nearest + 1:]

    return route, tour_distance(route, depot, distance_matrix)


def brute_force_optimal(depot, stops, distance_matrix):
    """Checks every possible order to confirm how close the GA came.
    Only practical for small networks. Returns (route, distance, tours_checked)."""
    if len(stops) <= 1:
        route = list(stops)
        return route, tour_distance(route, depot, distance_matrix), 1

    # Fixing the first stop skips each tour's mirror image (same distance).
    best_route, best_distance, checked = None, float("inf"), 0
    for tail in generate_all_permutations(stops[1:]):
        candidate = [stops[0]] + tail
        distance = tour_distance(candidate, depot, distance_matrix)
        checked += 1
        if distance < best_distance:
            best_route, best_distance = candidate, distance

    return best_route, best_distance, checked


# ===========================================================================
# SECTION 11: OUTPUT
# ===========================================================================

def print_distance_matrix(locations, distance_matrix):
    width = 12 + 10 * len(locations)
    print("\nShortest road distance between locations (km, from Dijkstra):")
    print("-" * width)
    print(f"{'':<12}" + "".join(f"{n[:9]:>10}" for n in locations))
    for origin in locations:
        row = f"{origin[:11]:<12}"
        for destination in locations:
            value = distance_matrix[origin][destination]
            row += f"{('-' if value == float('inf') else value):>10}"
        print(row)
    print("-" * width)


def print_population_sample(population, distances, fitnesses, size, show=5):
    """Shows the fittest few of the random starting population."""
    print(f"\nGeneration 0: {size} random routes created. Fittest {show}:")
    print("-" * 66)
    print(f"{'Route (delivery order)':<46}{'Distance':>10}{'Fitness':>10}")
    print("-" * 66)
    for i in range(min(show, len(population))):
        text = " ".join(population[i])
        text = text if len(text) <= 44 else text[:41] + "..."
        print(f"{text:<46}{distances[i]:>10.1f}{fitnesses[i]:>10.4f}")
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
    """Delivery order, each leg's distance, and the roads driven for that leg."""
    print(f"\n{label}")
    print("-" * 66)
    order = [depot] + route + [depot]
    print("Delivery order : " + " -> ".join(order))
    print()
    print(f"{'Leg':<6}{'From':<14}{'To':<14}{'km':>6}   Roads driven")
    print("-" * 66)
    for i in range(len(order) - 1):
        origin, destination = order[i], order[i + 1]
        path = road_paths[origin][destination]
        print(f"{i + 1:<6}{origin[:13]:<14}{destination[:13]:<14}"
              f"{distance_matrix[origin][destination]:>6}   "
              f"{' > '.join(path) if path else 'n/a'}")
    print("-" * 66)
    print(f"TOTAL DISTANCE : {tour_distance(route, depot, distance_matrix)} km")


def print_comparison(ga_distance, evaluations, nn_distance, optimal, checked):
    print("\nSolution quality comparison")
    print("-" * 66)
    print(f"{'Method':<36}{'Distance':>12}{'Routes checked':>18}")
    print("-" * 66)
    print(f"{'Nearest Neighbour (greedy)':<36}{nn_distance:>12.1f}{1:>18}")
    print(f"{'Genetic Algorithm (heuristic)':<36}{ga_distance:>12.1f}{evaluations:>18}")
    if optimal is not None:
        print(f"{'Brute force (true optimal)':<36}{optimal:>12.1f}{checked:>18}")
    print("-" * 66)

    if nn_distance > 0:
        saving = (nn_distance - ga_distance) / nn_distance * 100
        print(f"The GA route is {saving:.1f}% shorter than the greedy baseline."
              if saving > 0 else "The GA matched the greedy baseline here.")

    if optimal is not None:
        if abs(ga_distance - optimal) < 1e-9:
            print("Verification   : the GA found the TRUE OPTIMAL tour.")
        else:
            gap = (ga_distance - optimal) / optimal * 100
            print(f"Verification   : the GA route is {gap:.2f}% longer than the "
                  f"optimal tour. This is\n                 expected - a heuristic "
                  f"aims for a good answer quickly,\n                 not a "
                  f"guaranteed best one.")


# ===========================================================================
# SECTION 12: INPUT AND VALIDATION
# ===========================================================================

DEFAULT_SETTINGS = {
    "population_size": 60,     # candidate routes per generation
    "generations": 200,        # maximum generations
    "mutation_rate": 0.30,     # chance a child is mutated
    "tournament_size": 4,      # routes competing to become a parent
    "elite_count": 2,          # best routes carried forward unchanged
    "stagnation_limit": 50,    # stop after this many non-improving generations
    "report_every": 20,        # how often to print a progress row
    "seed": 2103,              # same seed = same result
}


def read_int(prompt, minimum, maximum):
    while True:
        try:
            value = int(input(prompt).strip())
        except ValueError:
            print(f"    Please enter a whole number between {minimum} and {maximum}.")
            continue
        if minimum <= value <= maximum:
            return value
        print(f"    Value must be between {minimum} and {maximum}.")


def ask_with_default(label, default, minimum, maximum, cast):
    """Prompt showing a default; pressing Enter accepts it."""
    while True:
        raw = input(f"{label} [{default}]: ").strip()
        if raw == "":
            return default
        try:
            value = cast(raw)
        except ValueError:
            print(f"    Invalid value. Enter a number between {minimum} and {maximum}.")
            continue
        if minimum <= value <= maximum:
            return value
        print(f"    Value must be between {minimum} and {maximum}.")


def ask_settings():
    s = dict(DEFAULT_SETTINGS)
    print("\nGA parameters (press Enter to keep the default):")
    s["population_size"] = ask_with_default("  Population size", s["population_size"], 4, 500, int)
    s["generations"] = ask_with_default("  Generations", s["generations"], 1, 5000, int)
    s["mutation_rate"] = ask_with_default("  Mutation rate (0.0 - 1.0)", s["mutation_rate"], 0.0, 1.0, float)
    s["tournament_size"] = ask_with_default("  Tournament size", s["tournament_size"], 2, s["population_size"], int)
    s["elite_count"] = ask_with_default("  Elite routes kept", s["elite_count"], 0, s["population_size"] - 1, int)
    s["seed"] = ask_with_default("  Random seed", s["seed"], 1, 999999, int)
    s["report_every"] = max(1, s["generations"] // 10)
    return s


def choose_depot_and_stops(graph):
    """Depot and delivery stops must exist, and the depot cannot be a stop."""
    locations = list(graph.keys())
    print("\nAvailable locations:")
    for i, name in enumerate(locations):
        print(f"  {i + 1}. {name}")

    while True:
        depot = input("\nEnter the DEPOT (starting location): ").strip()
        if depot in graph:
            break
        print("    That location does not exist in the network. Try again.")

    print("\nEnter delivery stops separated by spaces, or ALL for every location.")
    while True:
        raw = input("Delivery stops: ").strip()
        if raw.upper() == "ALL":
            return depot, [n for n in locations if n != depot]

        chosen = raw.split()
        if not chosen:
            print("    At least one delivery stop is required. Try again.")
            continue

        stops, valid = [], True
        for name in chosen:
            if name not in graph:
                print(f"    '{name}' does not exist in the network. Try again.")
                valid = False
                break
            if name == depot:
                print("    The depot cannot also be a delivery stop. Try again.")
                valid = False
                break
            if name not in stops:                # duplicates ignored
                stops.append(name)
        if valid:
            return depot, stops


def read_custom_graph():
    """Builds a network from user input, using the Problem 1 validation rules."""
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
                print("    Please enter exactly 3 values: From To Distance.")
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
# SECTION 13: RUN ONE CASE + MENU
# ===========================================================================

def run_case(graph, settings, label):
    """Choose stops -> build the distance matrix -> run the GA -> compare."""
    print("\n" + "=" * 66)
    print(f" {label}")
    print("=" * 66)

    depot, stops = choose_depot_and_stops(graph)
    locations = [depot] + stops
    distance_matrix, road_paths, unreachable = build_distance_matrix(graph, locations)

    if unreachable is not None:
        print(f"\nNo route exists between '{unreachable[0]}' and '{unreachable[1]}'.")
        print("These locations are not connected by any road, so a delivery tour")
        print("covering the selected stops is impossible.")
        return

    print_distance_matrix(locations, distance_matrix)

    if len(stops) <= 2:
        print(f"\nOnly {len(stops)} delivery stop(s), so one tour is possible "
              f"and no search is needed.")
        print_route(depot, list(stops), distance_matrix, road_paths,
                    "FINAL DELIVERY ROUTE")
        return

    nn_route, nn_distance = nearest_neighbour_route(depot, stops, distance_matrix)

    print(f"\nDelivery stops  : {len(stops)}")
    print(f"Possible tours  : {factorial(len(stops) - 1) // 2} distinct orders")
    print(f"GA settings     : population={settings['population_size']}, "
          f"generations={settings['generations']}, "
          f"mutation={settings['mutation_rate']}, seed={settings['seed']}")

    ga_route, ga_distance, generations, evaluations = genetic_algorithm(
        depot, stops, distance_matrix, settings, SimpleRandom(settings["seed"]))

    print_route(depot, nn_route, distance_matrix, road_paths,
                "BASELINE ROUTE (Nearest Neighbour, greedy)")
    print_route(depot, ga_route, distance_matrix, road_paths,
                "FINAL DELIVERY ROUTE (Genetic Algorithm)")

    optimal, checked = None, None
    if len(stops) <= 9:
        _, optimal, checked = brute_force_optimal(depot, stops, distance_matrix)
    else:
        print("\nBrute-force check skipped: too many tours with over 9 stops.")

    print_comparison(ga_distance, evaluations, nn_distance, optimal, checked)
    print(f"\nGenerations completed : {generations}")


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