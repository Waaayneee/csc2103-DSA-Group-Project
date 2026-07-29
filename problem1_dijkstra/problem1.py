"""
CSC2103 Group Project - Problem 1: Greedy Algorithm
Topic: Smart Delivery Route Optimization System (Option A)
Algorithm: Dijkstra's Shortest Path Algorithm

Scenario:
A delivery company needs to find the shortest road route from the depot
to a chosen delivery destination, using a weighted graph of road
distances between city locations.

Why Greedy fits this problem:
At every step, Dijkstra's algorithm picks the unvisited location with
the smallest known tentative distance from the depot, and locks that
distance in as final. This "always pick the locally best option" choice
is the greedy strategy: it never revisits or changes a decision once a
node is finalized, because with non-negative edge weights, no shorter
path to that node can ever be found later.

Implementation note:
This program does NOT use any built-in graph or shortest-path library.
The core Dijkstra logic (finding the minimum tentative distance among
unvisited nodes, and relaxing edges) is written manually below using
plain dictionaries and lists, so every step of the greedy choice is
visible and explained.
"""

import copy


# ---------------------------------------------------------------------------
# Graph representation
# ---------------------------------------------------------------------------
# The graph is stored as an adjacency dictionary:
#   graph = {
#       "Depot": {"WarehouseA": 4, "WarehouseB": 8},
#       "WarehouseA": {"Depot": 4, "CityCenter": 3},
#       ...
#   }
# Roads are treated as two-way (bidirectional), which is typical for a
# city road network.


def build_sample_graph():
    """
    Returns a preloaded sample delivery network so the group can quickly
    demonstrate and test the program without typing input every time.
    This represents a small city with a depot and five delivery zones.
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


def build_disconnected_sample_graph():
    """
    Returns a sample graph containing a node that is NOT reachable from
    the depot at all. This is used as an edge case test to confirm the
    program correctly reports when no path exists, instead of crashing.
    """
    graph = {
        "Depot": {"WarehouseA": 5},
        "WarehouseA": {"Depot": 5},
        "IsolatedZone": {},  # no roads connect to this location
    }
    return graph


def read_custom_graph():
    """
    Prompts the user to manually build a delivery network by entering
    locations and roads (edges) one at a time. Includes input validation:
    - rejects non-numeric distances
    - rejects negative distances, since Dijkstra's algorithm requires
      non-negative edge weights to guarantee a correct greedy choice
    """
    graph = {}

    num_locations = get_positive_int("Enter the number of delivery locations (including the depot): ")
    print("\nEnter the name of each location (e.g. Depot, WarehouseA, CityCenter):")
    for i in range(num_locations):
        name = input(f"  Location {i + 1} name: ").strip()
        if name not in graph:
            graph[name] = {}

    num_edges = get_positive_int("\nEnter the number of roads (edges) connecting these locations: ")
    print("\nFor each road, enter: FromLocation ToLocation Distance")
    print("Example: Depot WarehouseA 4\n")

    for i in range(num_edges):
        while True:
            raw = input(f"  Road {i + 1}: ").strip().split()
            if len(raw) != 3:
                print("    Please enter exactly 3 values: FromLocation ToLocation Distance.")
                continue
            a, b, w_str = raw
            if a not in graph or b not in graph:
                print("    One of those locations was not registered above. Try again.")
                continue
            try:
                w = float(w_str)
            except ValueError:
                print("    Distance must be a number. Try again.")
                continue
            if w < 0:
                print("    Distance cannot be negative (Dijkstra's algorithm requires non-negative weights). Try again.")
                continue
            graph[a][b] = w
            graph[b][a] = w
            break

    return graph


def get_positive_int(prompt):
    """Repeatedly asks for input until a positive integer is given."""
    while True:
        raw = input(prompt).strip()
        try:
            value = int(raw)
            if value <= 0:
                print("    Please enter a positive whole number.")
                continue
            return value
        except ValueError:
            print("    Please enter a valid whole number.")


# ---------------------------------------------------------------------------
# Manual Dijkstra's Shortest Path Algorithm
# ---------------------------------------------------------------------------

def dijkstra_shortest_path(graph, source, show_steps=True):
    """
    Manually computes the shortest distance from 'source' to every other
    node in 'graph' using Dijkstra's greedy algorithm.

    Returns:
        distances - dict of shortest distance from source to each node
        previous  - dict used to reconstruct the shortest path later

    The greedy choice at each step:
        Among all locations not yet finalized, pick the one with the
        smallest known tentative distance, and finalize it. This choice
        is never revisited, which is what makes this a greedy algorithm
        rather than one that explores all possibilities.
    """
    # Step 0: initialize distances as infinity, except the source itself.
    distances = {node: float("inf") for node in graph}
    distances[source] = 0
    previous = {node: None for node in graph}
    visited = set()

    step_number = 1

    while len(visited) < len(graph):
        # --- Greedy choice: find the unvisited node with the smallest ---
        # --- known tentative distance. This is done manually with a  ---
        # --- simple scan, no built-in priority queue or heap library. ---
        current_node = None
        current_distance = float("inf")
        for node in graph:
            if node not in visited and distances[node] < current_distance:
                current_node = node
                current_distance = distances[node]

        # If no reachable unvisited node remains, the rest are unreachable.
        if current_node is None:
            break

        visited.add(current_node)

        # --- Relax edges: update tentative distances of neighbors ---
        for neighbor, weight in graph[current_node].items():
            if neighbor in visited:
                continue
            new_distance = distances[current_node] + weight
            if new_distance < distances[neighbor]:
                distances[neighbor] = new_distance
                previous[neighbor] = current_node

        if show_steps:
            print_step_table(step_number, current_node, distances, visited)
        step_number += 1

    return distances, previous


def reconstruct_path(previous, source, destination):
    """
    Walks backwards through the 'previous' map built during Dijkstra's
    algorithm to reconstruct the actual shortest path from source to
    destination, then reverses it into the correct order.
    """
    if previous.get(destination) is None and destination != source:
        return None  # no path exists

    path = []
    node = destination
    while node is not None:
        path.append(node)
        node = previous[node]
    path.reverse()

    if path[0] != source:
        return None
    return path


# ---------------------------------------------------------------------------
# Output formatting
# ---------------------------------------------------------------------------

def print_step_table(step_number, current_node, distances, visited):
    """
    Prints a table showing the state of the algorithm after this step,
    so the greedy choice made at each stage is clearly visible.
    """
    print(f"\n--- Step {step_number}: Finalized '{current_node}' ---")
    print(f"{'Location':<15}{'Tentative Distance':<20}{'Finalized?':<10}")
    print("-" * 45)
    for node in distances:
        dist_display = distances[node] if distances[node] != float("inf") else "Infinity"
        finalized = "Yes" if node in visited else "No"
        print(f"{node:<15}{str(dist_display):<20}{finalized:<10}")


def print_final_result(source, destination, distances, previous):
    print("\n" + "=" * 50)
    print("FINAL RESULT")
    print("=" * 50)

    if distances[destination] == float("inf"):
        print(f"No route exists from '{source}' to '{destination}'.")
        print("These two locations are not connected by any road.")
        return

    path = reconstruct_path(previous, source, destination)
    print(f"Shortest route from '{source}' to '{destination}':")
    print("  " + " -> ".join(path))
    print(f"Total distance: {distances[destination]}")
    print("=" * 50)


# ---------------------------------------------------------------------------
# Main program / menu
# ---------------------------------------------------------------------------

def choose_source_and_destination(graph):
    print("\nAvailable locations:", ", ".join(graph.keys()))
    while True:
        source = input("Enter the DEPOT / starting location: ").strip()
        if source in graph:
            break
        print("  That location does not exist in the network. Try again.")
    while True:
        destination = input("Enter the DESTINATION location: ").strip()
        if destination in graph:
            break
        print("  That location does not exist in the network. Try again.")
    return source, destination


def run_case(graph, label):
    print(f"\n{'#' * 60}\nRunning: {label}\n{'#' * 60}")
    source, destination = choose_source_and_destination(graph)
    distances, previous = dijkstra_shortest_path(graph, source)
    print_final_result(source, destination, distances, previous)


def main():
    print("=" * 60)
    print(" CSC2103 Problem 1: Greedy Algorithm")
    print(" Smart Delivery Route Optimization System")
    print(" Algorithm: Dijkstra's Shortest Path")
    print("=" * 60)

    while True:
        print("\nMenu:")
        print("  1. Run built-in sample delivery network")
        print("  2. Run built-in DISCONNECTED network (edge case test)")
        print("  3. Enter a custom delivery network")
        print("  4. Exit")
        choice = input("Select an option (1-4): ").strip()

        if choice == "1":
            graph = build_sample_graph()
            run_case(graph, "Sample Delivery Network")
        elif choice == "2":
            graph = build_disconnected_sample_graph()
            run_case(graph, "Disconnected Network (Edge Case)")
        elif choice == "3":
            graph = read_custom_graph()
            run_case(graph, "Custom Delivery Network")
        elif choice == "4":
            print("Exiting program.")
            break
        else:
            print("Invalid option, please enter 1, 2, 3, or 4.")


if __name__ == "__main__":
    main()