"""
CSC2103 Group Project - Problem 1: Greedy Algorithm
Topic: Smart Delivery Route Optimization System (Option A)
Algorithm: Dijkstra's Shortest Path Algorithm
"""

import copy
from pathlib import Path

# Build the built-in connected sample delivery network.
def build_sample_graph():
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


# Build the built-in network with one disconnected location.
def build_disconnected_sample_graph():
    graph = {
        "Depot": {"WarehouseA": 5},
        "WarehouseA": {"Depot": 5},
        "IsolatedZone": {},  # This is the ONE disconnected location, no roads connect to this location
    }
    return graph


# Read a custom graph from user input.
def read_custom_graph():
    graph = {}

    num_locations = get_positive_int("Enter the number of delivery locations (including the depot): ")
    print("\nEnter the name of each location (e.g. Depot, WarehouseA, CityCenter):")
    for i in range(num_locations):
        name = input(f"  Location {i + 1} name: ").strip()
        if not name:
            print("    Location name cannot be empty. Try again.")
            i -= 1
            continue

        existing_key = find_graph_key(graph, name)
        if existing_key is None:
            graph[name] = {}

    num_edges = get_positive_int("\nEnter the number of roads (edges) connecting these locations: ")
    print("\nFor each road, enter: FromLocation ToLocation Distance")
    print("Example: Depot WarehouseA 4\n")

    for i in range(num_edges):
        while True:
            raw = input(f"  Road {i + 1}: ").strip()
            if not raw:
                print("    Please enter a valid road in the format: FromLocation ToLocation Distance.")
                continue

            parsed_edge = parse_custom_edge(raw, graph)
            if parsed_edge is None:
                print("    Please enter a valid road in the format: FromLocation ToLocation Distance.")
                continue

            a_key, b_key, w = parsed_edge
            if a_key is None or b_key is None:
                print("    One of those locations was not registered above. Try again.")
                continue
            if w < 0:
                print("    Distance cannot be negative (Dijkstra's algorithm requires non-negative weights). Try again.")
                continue
            graph[a_key][b_key] = w
            graph[b_key][a_key] = w
            break

    return graph


# Parse one custom road entry (edge) into two locations and a distance.
def parse_custom_edge(raw, graph):
    """Parse a road entry where location names may contain spaces."""
    parts = raw.split()
    if len(parts) < 3:
        return None

    try:
        w = float(parts[-1])
    except ValueError:
        return None

    remaining_tokens = parts[:-1]
    for split_index in range(1, len(remaining_tokens)):
        left = " ".join(remaining_tokens[:split_index]).strip()
        right = " ".join(remaining_tokens[split_index:]).strip()
        a_key = find_graph_key(graph, left)
        b_key = find_graph_key(graph, right)
        if a_key is not None and b_key is not None:
            return a_key, b_key, w

    return None, None, w


# Normalize a location name for case-insensitive matching.
def normalize_location_name(name):
    """Convert names to a comparable form so spacing and capitalization do not matter."""
    return "".join(name.split()).casefold()


# Find the exact graph key that matches a user-entered location name.
def find_graph_key(graph, name):
    """Return the exact graph key that matches the user's input name, ignoring case and spaces."""
    target = normalize_location_name(name)
    for graph_key in graph:
        if normalize_location_name(graph_key) == target:
            return graph_key
    return None


# Keep asking until the user enters a positive whole number.
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


# Load the expected shortest distances answer sheet from disk.
def load_expected_shortest_distances():
    expectedShortestDistances = {}
    answerSheetPath = Path(__file__).with_name("expected_shortest_distances.txt")

    with answerSheetPath.open("r", encoding="utf-8") as answerSheetFile:
        for rawLine in answerSheetFile:
            line = rawLine.strip()
            if not line or line.startswith("#"):
                continue

            source, destination, distanceText = line.split("\t")
            distanceValue = float(distanceText)
            if distanceValue.is_integer():
                distanceValue = int(distanceValue)
            expectedShortestDistances.setdefault(source, {})[destination] = distanceValue

    return expectedShortestDistances


# Print whether the computed shortest distance matches the answer sheet.
def print_shortest_distance_check_result(source, destination, actualDistance, expectedDistance):
    if actualDistance == expectedDistance:
        print(f"Answer sheet check for '{source}' -> '{destination}': RIGHT")
    else:
        print(
            f"Answer sheet check for '{source}' -> '{destination}': WRONG "
            f"(expected {format_distance(expectedDistance)}KM, got {format_distance(actualDistance)}KM)"
        )


# Check one computed shortest distance against the answer sheet.
def verify_shortest_distance(expectedShortestDistances, source, destination, actualDistance):
    expectedDistance = expectedShortestDistances.get(source, {}).get(destination)
    if expectedDistance is None:
        return
    # Compare the Dijkstra result with the answer sheet entry for this route.
    assert actualDistance == expectedDistance

# Run Dijkstra's algorithm and record shortest distances and predecessors.
def dijkstra_shortest_path(graph, source, show_steps=True):
    # initialize distances as infinity, except the source itself.
    distances = {node: float("inf") for node in graph}
    distances[source] = 0
    previous = {node: None for node in graph}
    visited = set()

    step_number = 1

    while len(visited) < len(graph):
        # Greedy choice: select the unvisited node with the smallest tentative distance.
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

        # relax edges: update distances to neighbors if a shorter path is found through current_node.
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


# Rebuild the shortest path from the predecessor map.
def reconstruct_path(previous, source, destination):
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


# Calculate the total distance for a specific path.
def calculate_path_distance(graph, path):
    total_distance = 0
    for index in range(len(path) - 1):
        total_distance += graph[path[index]][path[index + 1]]
    return total_distance


# Find every simple path between the selected source and destination, for average distance calculation.
def find_all_simple_paths(graph, source, destination):
    allPaths = []

    # Visit neighbors recursively while avoiding repeated locations.
    def depthFirstSearch(currentNode, visited, currentPath):
        if currentNode == destination:
            allPaths.append(list(currentPath))
            return

        for neighbor in graph[currentNode]:
            if neighbor in visited:
                continue
            visited.add(neighbor)
            currentPath.append(neighbor)
            depthFirstSearch(neighbor, visited, currentPath)
            currentPath.pop()
            visited.remove(neighbor)

    depthFirstSearch(source, {source}, [source])
    return allPaths


# Compute the average distance across all simple routes between two points.
def calculate_average_route_distance(graph, source, destination):
    allPaths = find_all_simple_paths(graph, source, destination)
    if not allPaths:
        return None

    totalDistance = 0
    for path in allPaths:
        totalDistance += calculate_path_distance(graph, path)

    return totalDistance / len(allPaths)


# Format a distance value so the output stays readable. (2 decimal places)
def format_distance(distance):
    if distance == int(distance):
        return str(int(distance))
    return f"{distance:.2f}".rstrip("0").rstrip(".")

# Print the step-by-step Dijkstra table for the current run.
def print_step_table(step_number, current_node, distances, visited):
    print(f"\n--- Step {step_number}: Finalized '{current_node}' ---")
    print(f"{'Location':<15}{'Tentative Distance':<20}{'Finalized?':<10}")
    print("-" * 45)
    for node in distances:
        dist_display = distances[node] if distances[node] != float("inf") else "Infinity"
        finalized = "Yes" if node in visited else "No"
        print(f"{node:<15}{str(dist_display):<20}{finalized:<10}")


# Print the final route summary and distance results.
def print_final_result(graph, source, destination, distances, previous, expectedShortestDistances=None):
    print("\n" + "=" * 50)
    print("FINAL RESULT")
    print("=" * 50)

    if distances[destination] == float("inf"):
        print(f"No route exists from '{source}' to '{destination}'.")
        print("These two locations are not connected by any road.")
        return

    path = reconstruct_path(previous, source, destination)
    print(f"Shortest route from '{source}' to '{destination}':")
    print(" -> ".join(path))
    shortestDistance = distances[destination]
    # Checking if the Dijkstra shortest distance is correct against the answer sheet.
    if expectedShortestDistances is not None:
        verify_shortest_distance(expectedShortestDistances, source, destination, shortestDistance)
    averageDistance = calculate_average_route_distance(graph, source, destination)
    distanceSaved = averageDistance - shortestDistance

    print(f"Total distance: {format_distance(shortestDistance)} KM")
    print(f"Average distance: {format_distance(averageDistance)} KM")
    print(f"Distance saved: {format_distance(distanceSaved)} KM")
    if expectedShortestDistances is not None:
        expectedDistance = expectedShortestDistances.get(source, {}).get(destination)
        if expectedDistance is not None:
            # Show whether the Dijkstra algo shortest distance matches the answer sheet.
            print_shortest_distance_check_result(source, destination, shortestDistance, expectedDistance)
    print("=" * 50)

# Ask the user to choose a valid start and end location.
def choose_source_and_destination(graph):
    print("\nAvailable locations:", ", ".join(graph.keys()))
    while True:
        source = input("Enter the starting location, IE 'Depot': ").strip()
        source_key = find_graph_key(graph, source)
        if source_key is not None:
            break
        print("  That location does not exist in the network. Try again.")
    while True:
        destination = input("Enter the DESTINATION location, IE 'Mall': ").strip()
        destination_key = find_graph_key(graph, destination)
        if destination_key is not None:
            break
        print("  That location does not exist in the network. Try again.")
    return source_key, destination_key


# Run one selected network and print the result.
def run_case(graph, label, expectedShortestDistances=None):
    print(f"\n{'#' * 60}\nRunning: {label}\n{'#' * 60}")
    source, destination = choose_source_and_destination(graph)
    distances, previous = dijkstra_shortest_path(graph, source)
    print_final_result(graph, source, destination, distances, previous, expectedShortestDistances)


# Show the program menu and handle user choices.
def main():
    print("=" * 60)
    print(" CSC2103 Problem 1: Greedy Algorithm")
    print(" Smart Delivery Route Optimization System")
    print(" Algorithm: Dijkstra's Shortest Path")
    print("=" * 60)

    expectedShortestDistances = load_expected_shortest_distances()
    while True:
        print("\nMenu:")
        print("  1. Run built-in sample delivery network")
        print("  2. Run built-in DISCONNECTED network (edge case test)")
        print("  3. Enter a custom delivery network")
        print("  4. Exit")
        choice = input("Select an option (1-4): ").strip()

        if choice == "1":
            graph = build_sample_graph()
            run_case(graph, "Sample Delivery Network", expectedShortestDistances)
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
