# ==============================================
# Smart Delivery Route Optimization System
# Dynamic Programming (0/1 Knapsack)
# ==============================================

def knapsack(weights, priorities, capacity):
    n = len(weights)

    # Create DP Table
    dp = [[0 for _ in range(capacity + 1)] for _ in range(n + 1)]

    # Fill DP Table
    for i in range(1, n + 1):
        for w in range(capacity + 1):

            if weights[i - 1] <= w:

                include = priorities[i - 1] + dp[i - 1][w - weights[i - 1]]
                exclude = dp[i - 1][w]

                dp[i][w] = max(include, exclude)

            else:
                dp[i][w] = dp[i - 1][w]

    # Backtracking to find selected packages
    selected = []

    w = capacity

    for i in range(n, 0, -1):

        if dp[i][w] != dp[i - 1][w]:

            selected.append(i - 1)
            w -= weights[i - 1]

    selected.reverse()

    return dp, selected


def display_dp_table(dp):

    print("\nDynamic Programming Table")

    for row in dp:
        for value in row:
            print(f"{value:4}", end="")
        print()


def main():

    print("=" * 60)
    print(" SMART DELIVERY ROUTE OPTIMIZATION SYSTEM")
    print(" Dynamic Programming (0/1 Knapsack)")
    print("=" * 60)

    n = int(input("\nEnter number of delivery packages: "))

    package_ids = []
    weights = []
    priorities = []

    for i in range(n):

        print(f"\nPackage {i + 1}")

        package_id = input("Package ID: ")
        weight = int(input("Package Weight (kg): "))
        priority = int(input("Delivery Priority: "))

        package_ids.append(package_id)
        weights.append(weight)
        priorities.append(priority)

    capacity = int(input("\nEnter Truck Maximum Capacity (kg): "))

    dp, selected = knapsack(weights, priorities, capacity)

    display_dp_table(dp)

    print("\nSelected Packages")
    print("-" * 60)

    total_weight = 0
    total_priority = 0

    print("{:<15}{:<15}{:<15}".format(
        "Package", "Weight", "Priority"))

    print("-" * 60)

    for i in selected:

        print("{:<15}{:<15}{:<15}".format(
            package_ids[i],
            weights[i],
            priorities[i]))

        total_weight += weights[i]
        total_priority += priorities[i]

    print("-" * 60)

    print(f"Total Weight Used : {total_weight} kg")
    print(f"Truck Capacity    : {capacity} kg")
    print(f"Total Priority    : {total_priority}")

    print("\nDelivery Summary")
    print("-" * 60)

    print(f"Packages Delivered : {len(selected)}")
    print(f"Packages Skipped   : {n - len(selected)}")
    print("Optimization Complete.")


if __name__ == "__main__":
    main()