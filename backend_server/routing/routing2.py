import numpy as np
import random

# rng = np.random.default_rng(2023)
# random.seed(2023)

# Problem Parameters

# Generate random cities and distance matrix
cities = [
    [1.00, 1.0],
    [1.25, 1.0],
    [1.50, 1.0],

    [2.00, 1.0],
    [2.25, 1.0],
    [2.50, 1.0],

    [3.00, 1.0],
    [3.25, 1.0],
    [3.50, 1.0],
]
n_cities = len(cities)
n_salesmen = 3
dist_matrix = np.array([[np.sqrt((c1[0] - c2[0]) ** 2 + (c1[1] - c2[1]) ** 2)
                         for c1 in cities] for c2 in cities])


# GA parameters
population_size = 100
generations = 1000
mutation_rate = 0.1
elitism = True



# Helper functions
def create_individual():
    route = list(range(1, n_cities))
    random.shuffle(route)
    partition_points = sorted(random.sample(route[:-1], n_salesmen - 1))
    return [route[i:j] for i, j in zip([0] + partition_points, partition_points + [None])]

def fitness(individual):
    total_distance = 0
    for route in individual:
        print(route)
        if len(route) == 0:
            distance = np.inf
        else:
            distance = dist_matrix[0][route[0]] + dist_matrix[route[-1]][0]
            for i in range(1, len(route)):
                distance += dist_matrix[route[i-1]][route[i]]
        total_distance += distance
    return -total_distance

# def order_crossover(parent1, parent2):
#     child = []
#     for p1_route, p2_route in zip(parent1, parent2):
#         start = random.randint(0, len(p1_route) - 1)
#         end = random.randint(start, len(p1_route))
#         child_route = p1_route[start:end]
#         p2_remaining = [city for city in p2_route if city not in child_route]
#         child_route = p2_remaining[:start] + child_route + p2_remaining[start:]
#         child.append(child_route)
#     return child

# def mutate(individual, mutation_rate):
#     for route in individual:
#         for i in range(len(route)):
#             if random.random() < mutation_rate:
#                 swap_index = random.randint(0, len(route) - 1)
#                 route[i], route[swap_index] = route[swap_index], route[i]
#     return individual

def selection(population, fit_scores):
    # sorted_population = sorted(population, key=lambda x: fit_scores[x], reverse=True)
    sorted_population = sorted(population, key=lambda x: x.fitness, reverse=True)
    return sorted_population[:population_size]

def main():
    # Initialize population
    population = [create_individual() for _ in range(population_size)]

    # Main loop
    for _ in range(generations):
        # Calculate the fitness of each individual in the population
        fit_scores = {i: fitness(population[i]) for i in range(len(population))}

        # Selection
        new_population = selection(population, fit_scores)
        print(new_population)
        break
        
    #     # Crossover
    #     children = []
    #     while len(children) < population_size:
    #         parent1 = random.choice(new_population)
    #         parent2 = random.choice(new_population)
    #         if parent1 != parent2:
    #             child = order_crossover(parent1, parent2)
    #             children.append(child)
        
    #     # Mutation
    #     for i in range(int(elitism), len(children)):
    #         children[i] = mutate(children[i], mutation_rate)
        
    #     population = children
        
    #     # Print best individual
    #     best_individual = max(population, key=fitness)
    #     print(f"Generation {gen + 1}: Best fitness = {-fitness(best_individual)}")


if __name__ == "__main__":
    main()
