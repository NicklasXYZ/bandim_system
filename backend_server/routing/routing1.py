import random
import numpy as np


# Example distance matrix
dist_matrix = np.array([
    [0, 10, 20, 30, 40, 50, 60, 70, 80],
    [10, 0, 15, 35, 25, 55, 65, 45, 50],
    [20, 15, 0, 25, 35, 40, 50, 60, 70],
    [30, 35, 25, 0, 45, 55, 65, 75, 85],
    [40, 25, 35, 45, 0, 50, 60, 70, 80],
    [50, 55, 40, 55, 50, 0, 10, 20, 30],
    [60, 65, 50, 65, 60, 10, 0, 25, 35],
    [70, 45, 60, 75, 70, 20, 25, 0, 15],
    [80, 50, 70, 85, 80, 30, 35, 15, 0],
])

n_cities = len(dist_matrix)
n_salesmen = 3
n_individuals = 50
n_generations = 1000
mutation_rate = 0.1

rng = np.random.default_rng(2023)
random.seed(2023)

def create_individual():
    cities = list(range(1, n_cities))
    rng.shuffle(cities)
    partitions = sorted(random.sample(range(1, n_cities - 1), n_salesmen - 1))
    return (cities, partitions)

def create_population():
    return [create_individual() for _ in range(n_individuals)]

def crossover(parent1, parent2):
    p1_cities, p1_partitions = parent1
    p2_cities, p2_partitions = parent2

    # One-point crossover for partitions
    crossover_point = random.randint(1, n_salesmen - 1)
    child_partitions = p1_partitions[:crossover_point] + p2_partitions[crossover_point:]

    # Edge recombination crossover for cities
    child_cities = [p1_cities[0]]
    remaining_cities = set(p1_cities + p2_cities) - set(child_cities)

    while remaining_cities:
        last_city = child_cities[-1]
        next_city = min(remaining_cities, key=lambda city: dist_matrix[last_city, city])
        child_cities.append(next_city)
        remaining_cities.remove(next_city)

    return (child_cities, child_partitions)

def mutate(individual):
    cities, partitions = individual

    if random.random() < mutation_rate:
        i, j = random.sample(range(n_cities - 1), 2)
        cities[i], cities[j] = cities[j], cities[i]

    if random.random() < mutation_rate:
        i, j = random.sample(range(1, n_salesmen), 2)
        partitions[i - 1], partitions[j - 1] = partitions[j - 1], partitions[i - 1]

    return (cities, partitions)

def fitness(individual):
    cities, partitions = individual

    start_points = [0] + partitions
    end_points = partitions + [n_cities - 1]

    total_distance = 0
    for start, end in zip(start_points, end_points):
        route = cities[start:end]
        for i in range(len(route)):
            city1 = route[i]
            city2 = route[i - 1] if i > 0 else 0
            total_distance += dist_matrix[city1, city2]
        total_distance += dist_matrix[0, route[-1]]

    return total_distance

def selection(population):
    fitnesses = [fitness(ind) for ind in population]
    total_fitness = sum(fitnesses)
    probabilities = [fit / total_fitness for fit in fitnesses]

    selected_indices = np.random.choice(range(n_individuals), size=n_individuals, p=probabilities)
    return [population[i] for i in selected_indices]

def genetic_algorithm():
    population = create_population()
    for individual in population:
        print(individual)

    # for generation in range(n_generations):
    #     # Selection
    #     selected_population = selection(population)

    #     # Crossover
    #     new_population = []
    #     for i in range(0, n_individuals, 2):
    #         parent1, parent2 = random.sample(selected_population, 2)
    #         child1 = crossover(parent1, parent2)
    #         child2 = crossover(parent2, parent1)
    #         new_population.extend([child1, child2])

    #     # Mutation
    #     population = [mutate(ind) for ind in new_population]

    # # Find the best solution
    # best_individual = min(population, key=fitness)
    # return best_individual, fitness(best_individual)

if __name__ == "__main__":
    # np.random.SeedSequence.spawn(n_children=1)
    # best_solution, best_fitness = 
    genetic_algorithm()
    # print("Best solution:", best_solution)
    # print("Fitness:", best_fitness)
